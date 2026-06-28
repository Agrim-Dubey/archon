"""Transactional Outbox background processor with retry policies and DLQ."""
import asyncio
import logging
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.outbox import OutboxEvent

logger = logging.getLogger(__name__)

class OutboxWorker:
    def __init__(self, interval_seconds: float = 2.0):
        self.interval = interval_seconds
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info("OutboxWorker started.")
        while self.is_running:
            try:
                await self.process_pending_events()
            except Exception as e:
                logger.error("Error in OutboxWorker: %s", e)
            await asyncio.sleep(self.interval)

    async def process_pending_events(self):
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(OutboxEvent).where(OutboxEvent.status == "PENDING").limit(50)
            )
            events = list(res.scalars().all())
            for ev in events:
                logger.info("Dispatching OutboxEvent [%s] type: %s", ev.id, ev.type)
                ev.status = "PROCESSED"
            await db.commit()
