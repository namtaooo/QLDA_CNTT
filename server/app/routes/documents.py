"""
Documents Router — upload with automatic RAG indexing.
"""
from typing import Any, List
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import logging
import os
import shutil

from app import models, schemas
from app.core.database import get_db
from app.routes.deps import get_current_active_user
from app.worker import process_document_task_celery

router = APIRouter()
UPLOAD_DIR = "storage/documents"

os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

@router.post("/upload/", response_model=schemas.DocumentResponse)
async def upload_document(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    department: str = Form(""),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    # Validate file size (e.g., max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    # Validate file type
    ALLOWED_TYPES = [
        "text/plain", 
        "text/markdown", 
        "application/pdf", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ]
    if file.content_type not in ALLOWED_TYPES and not file.filename.endswith((".txt", ".md", ".pdf", ".docx", ".xlsx")):
        raise HTTPException(status_code=400, detail="Unsupported file format.")
        
    file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
    filepath = os.path.join(UPLOAD_DIR, file.filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = models.Document(
        filename=file.filename,
        filepath=filepath,
        file_type=file_type,
        uploader_id=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    metadata = {
        "filename": file.filename,
        "department": department or current_user.department or "",
        "role": current_user.role,
        "uploader": current_user.full_name,
        "user_id": current_user.id
    }
    
    # Offload processing to Celery background worker
    process_document_task_celery.delay(filepath, file_type, metadata, doc.id)

    return doc


@router.get("/", response_model=List[schemas.DocumentResponse])
def read_documents(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    documents = db.query(models.Document).offset(skip).limit(limit).all()
    return documents
