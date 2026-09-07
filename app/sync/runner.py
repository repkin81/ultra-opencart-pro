from __future__ import annotations

import logging

from app.config import get_settings
from app.database import SessionLocal
from app.sync.connector import OpenCartConnector
from app.sync.scheduler import SyncScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> None:
    settings = get_settings()
    base_url = settings.sync_opencart_url
    api_key = settings.sync_opencart_api_key
    if not base_url or not api_key:
        raise RuntimeError("SYNC_OPENCART_URL and SYNC_OPENCART_API_KEY must be configured")

    while True:
        with SessionLocal() as db:
            scheduler = SyncScheduler(
                db,
                OpenCartConnector(base_url, api_key),
                interval_seconds=settings.sync_interval_seconds,
                page_size=settings.sync_page_size,
                max_retries=settings.sync_max_retries,
            )
            scheduler.run_cycle()

        # Keep the scheduler as a separate process so multiple FastAPI workers do not duplicate it.
        import time
        time.sleep(settings.sync_interval_seconds)


if __name__ == "__main__":
    main()
