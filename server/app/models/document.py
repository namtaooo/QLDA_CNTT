from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, text

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    file_type = Column(String(50))
    is_indexed = Column(Boolean, nullable=False, server_default=text("false"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
