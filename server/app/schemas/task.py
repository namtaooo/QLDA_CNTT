from typing import Optional
from datetime import datetime
from pydantic import BaseModel

# Shared properties
class TaskBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "todo"
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None

# Properties to receive on task creation
class TaskCreate(TaskBase):
    title: str

# Properties to receive on task update
class TaskUpdate(TaskBase):
    pass

# Properties shared by models stored in DB
class TaskInDBBase(TaskBase):
    id: int
    creator_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Properties to return to client
class Task(TaskInDBBase):
    pass
