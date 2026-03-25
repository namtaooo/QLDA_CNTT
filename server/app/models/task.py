from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text

from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    status = Column(String(50), nullable=False, server_default=text("'todo'"))
    due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
