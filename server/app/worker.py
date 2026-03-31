import os
import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "aioffice_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
)

@celery_app.task(name="process_document_task_celery", bind=True, max_retries=3)
def process_document_task_celery(self, filepath: str, file_type: str, metadata: dict, doc_id: int):
    """
    Celery task to parse a document and index it in the AI Engine vector store.
    """
    from app.services import document_service
    from app.core.database import SessionLocal
    from app import models
    from app.services.ai_service import ai_client

    logger.info(f"Starting document processing for doc_id={doc_id}")
    
    try:
        content = document_service.extract_text(filepath, file_type)
        if content:
            # Call AI engine syncly since Celery workers are synchronous
            logger.info("Content extracted. Sending to AI Engine for indexing...")
            ai_client.index_document_sync(content, metadata)
            
            # Mark document as indexed in DB
            db = SessionLocal()
            try:
                doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
                if doc:
                    doc.is_indexed = True
                    db.commit()
                    logger.info(f"Document {doc_id} successfully indexed.")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to update document indexed status: {e}")
            finally:
                db.close()
        else:
            logger.warning(f"No content extracted from doc_id={doc_id}")
            
    except Exception as exc:
        logger.error(f"Error in process_document_task_celery: {exc}")
        # Exponential backoff for retries: 2^retry_count * 5 seconds (5, 10, 20s...)
        retry_countdown = (2 ** self.request.retries) * 5
        raise self.retry(exc=exc, countdown=retry_countdown)
