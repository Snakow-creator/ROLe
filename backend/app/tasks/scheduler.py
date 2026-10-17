"""Periodic, idempotent task maintenance for the FastAPI lifespan."""

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from tasks import task_service


logger = logging.getLogger(__name__)
UPDATE_INTERVAL_SECONDS = 60


async def run_task_updates(interval: float = UPDATE_INTERVAL_SECONDS):
    # Startup performs the first update before the application accepts requests.
    while True:
        await asyncio.sleep(interval)
        try:
            await task_service.update()
        except Exception:
            logger.exception("Scheduled task update failed; retrying on the next tick")


@asynccontextmanager
async def task_update_scheduler(interval: float = UPDATE_INTERVAL_SECONDS):
    worker = asyncio.create_task(run_task_updates(interval), name="task-updates")
    try:
        yield worker
    finally:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker
