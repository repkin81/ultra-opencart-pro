from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SyncJob(Base):
    __tablename__ = "sync_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    connection_id: Mapped[int | None] = mapped_column(ForeignKey("open_cart_connections.id", ondelete="CASCADE"), nullable=True, index=True)
    direction: Mapped[str] = mapped_column(String(32), default="opencart_to_core")
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    requested_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    succeeded: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    items: Mapped[list["SyncItem"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class SyncItem(Base):
    __tablename__ = "sync_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("sync_jobs.id", ondelete="CASCADE"), index=True)
    connection_id: Mapped[int | None] = mapped_column(ForeignKey("open_cart_connections.id", ondelete="CASCADE"), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    external_id: Mapped[str] = mapped_column(String(128))
    operation: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    job: Mapped[SyncJob] = relationship(back_populates="items")


class SyncMapping(Base):
    __tablename__ = "sync_mappings"
    __table_args__ = (UniqueConstraint("connection_id", "entity_type", "external_id", name="uq_sync_mapping_connection_external"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    connection_id: Mapped[int | None] = mapped_column(ForeignKey("open_cart_connections.id", ondelete="CASCADE"), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    external_id: Mapped[str] = mapped_column(String(128))
    core_id: Mapped[str] = mapped_column(String(128))
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
