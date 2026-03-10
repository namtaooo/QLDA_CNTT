from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class DocumentBase(BaseModel):
    filename: Optional[str] = None
    file_type: Optional[str] = None
    is_indexed: Optional[bool] = False

class DocumentCreate(DocumentBase):
    filename: str
    filepath: str
    file_type: str

class DocumentUpdate(DocumentBase):
    is_indexed: Optional[bool] = None

class DocumentInDBBase(DocumentBase):
    id: int
    filepath: str
    uploader_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Properties to return to client
class DocumentResponse(DocumentInDBBase):
    pass
