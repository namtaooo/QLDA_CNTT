from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# ──── Task Log ────
class TaskLogOut(BaseModel):
    id: int
    task_id: int
    user_id: Optional[int] = None
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ──── Task ────
class TaskBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "CREATED"
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None

class TaskCreate(TaskBase):
    title: str

class TaskUpdate(TaskBase):
    pass

class TaskInDBBase(TaskBase):
    id: int
    creator_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Task(TaskInDBBase):
    pass

class TaskWithLogs(TaskInDBBase):
    logs: List[TaskLogOut] = []


# ──── Assign / Status payloads ────
class TaskAssign(BaseModel):
    assignee_id: int
    note: Optional[str] = None

class TaskStatusUpdate(BaseModel):
    status: str  # CREATED, ASSIGNED, IN_PROGRESS, REVIEW, DONE
    note: Optional[str] = None


# ──── AI Assignment response ────
class CandidateScore(BaseModel):
    user_id: int
    full_name: str
    score: float
    matched_skills: List[str] = []

class AIAssignmentResult(BaseModel):
    task_id: int
    required_skills: List[str]
    candidates: List[CandidateScore]
    recommended_assignee_id: Optional[int] = None


# ──── AI Planning response ────
class PlannedTask(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    suggested_assignee: Optional[str] = None
    estimated_days: int = 1

class ProjectPlan(BaseModel):
    project_goal: str
    tasks: List[PlannedTask]
    total_estimated_days: int
