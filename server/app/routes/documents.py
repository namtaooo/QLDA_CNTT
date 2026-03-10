from typing import Any, List
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db
from app.routes.deps import get_current_user

router = APIRouter()
UPLOAD_DIR = "storage/documents"

# Ensure dir exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/", response_model=schemas.DocumentResponse)
async def upload_document(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
) -> Any:
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
    
    # Ideally trigger background task to vector index the document here
    
    return doc

@router.get("/", response_model=List[schemas.DocumentResponse])
def read_documents(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
) -> Any:
    documents = db.query(models.Document).offset(skip).limit(limit).all()
    return documents
