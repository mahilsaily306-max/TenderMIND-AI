import asyncio
import logging

from app.core.database import async_session
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run an async coroutine in a sync Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: int, tender_id: int):
    """Parse document, generate embeddings, extract requirements."""
    from app.services.rag_service import RAGService

    async def _process():
        async with async_session() as db:
            service = RAGService(db)
            await service.parse_document(document_id)
            logger.info("Document %d parsed", document_id)
            await service.generate_embeddings(document_id)
            extraction = await service.extract_requirements(document_id, tender_id)
            logger.info(
                "Requirements extracted for tender %d: %d fields, %d compliance items",
                tender_id,
                len(extraction.get("fields", {})),
                len(extraction.get("compliance_items", [])),
            )
            return {"document_id": document_id, "tender_id": tender_id, "status": "completed"}

    try:
        return run_async(_process())
    except Exception as exc:
        logger.error("Document processing failed: %s", exc)
        raise self.retry(exc=exc) from exc
