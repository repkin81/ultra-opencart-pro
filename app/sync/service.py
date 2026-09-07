import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.sync.connector import OpenCartConnector
from app.sync.models import SyncItem, SyncJob, SyncMapping
from app.sync.schemas import SyncBatchIn


def canonical_checksum(payload: dict | None) -> str:
    raw = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SyncService:
    """Durable checksum-based bidirectional synchronization service."""

    def __init__(self, db: Session):
        self.db = db

    def enqueue(self, batch: SyncBatchIn, user_id: int | None = None) -> tuple[SyncJob, int, int]:
        job = SyncJob(direction=batch.direction, status="queued", requested_by=user_id, total=0)
        self.db.add(job)
        self.db.flush()
        accepted = skipped = 0
        for item in batch.items:
            checksum = canonical_checksum(item.payload)
            if batch.direction == "core_to_opencart":
                mapping = self.db.scalar(select(SyncMapping).where(
                    SyncMapping.entity_type == item.entity_type,
                    SyncMapping.core_id == item.external_id,
                ))
            else:
                mapping = self.db.scalar(select(SyncMapping).where(
                    SyncMapping.entity_type == item.entity_type,
                    SyncMapping.external_id == item.external_id,
                ))
            if mapping and mapping.checksum == checksum and item.operation == "upsert":
                skipped += 1
                continue
            self.db.add(SyncItem(
                job_id=job.id,
                entity_type=item.entity_type,
                external_id=item.external_id,
                operation=item.operation,
                payload=json.dumps(item.payload or {}, ensure_ascii=False),
                checksum=checksum,
            ))
            accepted += 1
        job.total = accepted
        self.db.commit()
        self.db.refresh(job)
        return job, accepted, skipped

    def process(self, job_id: int, connector: OpenCartConnector | None = None) -> SyncJob:
        job = self.db.get(SyncJob, job_id)
        if not job:
            raise ValueError("Sync job not found")
        if job.status == "completed":
            return job
        if job.status == "running":
            raise ValueError("Sync job is already running")
        if job.direction == "core_to_opencart" and connector is None:
            raise ValueError("OpenCart connector is required for core_to_opencart jobs")

        job.status = "running"
        job.started_at = utcnow()
        self.db.commit()
        items = self.db.scalars(select(SyncItem).where(SyncItem.job_id == job.id).order_by(SyncItem.id)).all()

        for item in items:
            if item.status == "success":
                continue
            try:
                payload = json.loads(item.payload or "{}")
                if job.direction == "opencart_to_core":
                    self._apply_to_core(item, payload)
                else:
                    self._apply_to_opencart(item, payload, connector)  # type: ignore[arg-type]
                item.status = "success"
                item.error = None
                job.succeeded += 1
            except Exception as exc:
                item.status = "failed"
                item.error = str(exc)
                job.failed += 1
            item.processed_at = utcnow()
            job.processed += 1
            self.db.commit()

        job.status = "failed" if job.failed else "completed"
        job.finished_at = utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def _apply_to_core(self, item: SyncItem, payload: dict[str, Any]) -> None:
        mapping = self.db.scalar(select(SyncMapping).where(
            SyncMapping.entity_type == item.entity_type,
            SyncMapping.external_id == item.external_id,
        ))
        if item.operation == "delete":
            if mapping:
                self._delete_core(item.entity_type, int(mapping.core_id))
                self.db.delete(mapping)
            return
        if item.entity_type == "product":
            obj = self._upsert_product(mapping, payload)
        elif item.entity_type == "category":
            obj = self._upsert_category(mapping, payload)
        else:
            raise ValueError(f"Unsupported entity type: {item.entity_type}")
        self.db.flush()
        if mapping is None:
            mapping = SyncMapping(entity_type=item.entity_type, external_id=item.external_id, core_id=str(obj.id))
            self.db.add(mapping)
        mapping.checksum = item.checksum or canonical_checksum(payload)

    def _apply_to_opencart(self, item: SyncItem, payload: dict[str, Any], connector: OpenCartConnector) -> None:
        mapping = self.db.scalar(select(SyncMapping).where(
            SyncMapping.entity_type == item.entity_type,
            SyncMapping.core_id == item.external_id,
        ))
        if item.operation == "delete":
            if mapping:
                external_id = int(mapping.external_id)
                if item.entity_type == "product":
                    connector.delete_product(external_id)
                elif item.entity_type == "category":
                    connector.delete_category(external_id)
                else:
                    raise ValueError(f"Unsupported entity type: {item.entity_type}")
                self.db.delete(mapping)
            return
        if mapping:
            remote = self._remote(connector, item.entity_type, int(mapping.external_id))
            if mapping.checksum and canonical_checksum(remote) != mapping.checksum:
                raise ValueError(f"Sync conflict for {item.entity_type} {item.external_id}: OpenCart changed since last synchronization")
        if item.entity_type == "product":
            result = connector.push_product(payload, int(mapping.external_id) if mapping else None)
        elif item.entity_type == "category":
            result = connector.push_category(payload, int(mapping.external_id) if mapping else None)
        else:
            raise ValueError(f"Unsupported entity type: {item.entity_type}")
        external_id = self._extract_id(result, item.entity_type) or (mapping.external_id if mapping else None)
        if not external_id:
            raise ValueError("OpenCart did not return an external entity id")
        if mapping is None:
            mapping = SyncMapping(entity_type=item.entity_type, external_id=str(external_id), core_id=item.external_id)
            self.db.add(mapping)
        else:
            mapping.external_id = str(external_id)
        mapping.checksum = item.checksum or canonical_checksum(payload)

    @staticmethod
    def _remote(connector: OpenCartConnector, entity_type: str, external_id: int) -> dict[str, Any]:
        if entity_type == "product":
            return connector.get_product(external_id)
        if entity_type == "category":
            return connector.get_category(external_id)
        raise ValueError(f"Unsupported entity type: {entity_type}")

    @staticmethod
    def _extract_id(result: dict[str, Any], entity_type: str) -> str | None:
        for key in (f"{entity_type}_id", "id", "insert_id"):
            value = result.get(key)
            if value is not None:
                return str(value)
        for key in (entity_type, "data"):
            nested = result.get(key)
            if isinstance(nested, dict):
                found = SyncService._extract_id(nested, entity_type)
                if found:
                    return found
        return None

    def _upsert_product(self, mapping: SyncMapping | None, payload: dict[str, Any]) -> Product:
        obj = self.db.get(Product, int(mapping.core_id)) if mapping else None
        if obj is None:
            obj = Product(model=str(payload.get("model") or payload.get("sku") or f"OC-{payload.get('product_id')}"), name=str(payload.get("name") or ""))
            self.db.add(obj)
        fields = ("model", "sku", "name", "description", "price", "quantity", "status", "meta_title", "meta_description", "seo_keyword", "image")
        for field in fields:
            if field in payload and payload[field] is not None:
                setattr(obj, field, payload[field])
        return obj

    def _upsert_category(self, mapping: SyncMapping | None, payload: dict[str, Any]) -> Category:
        obj = self.db.get(Category, int(mapping.core_id)) if mapping else None
        if obj is None:
            obj = Category(name=str(payload.get("name") or ""))
            self.db.add(obj)
        fields = ("name", "parent_id", "description", "status", "meta_title", "meta_description", "meta_keyword")
        for field in fields:
            if field in payload and payload[field] is not None:
                setattr(obj, field, payload[field])
        return obj

    def _delete_core(self, entity_type: str, core_id: int) -> None:
        model = Product if entity_type == "product" else Category if entity_type == "category" else None
        if model is None:
            raise ValueError(f"Unsupported entity type: {entity_type}")
        obj = self.db.get(model, core_id)
        if obj:
            self.db.delete(obj)

    def get(self, job_id: int) -> SyncJob | None:
        return self.db.get(SyncJob, job_id)
