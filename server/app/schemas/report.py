from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# ──── Dashboard ────
class UserKPI(BaseModel):
    user_id: int
    full_name: str
    department: Optional[str] = None
    tasks_completed: int = 0
    overdue_rate: float = 0.0
    avg_completion_time: float = 0.0
    productivity_score: float = 0.0

class DashboardReport(BaseModel):
    total_tasks: int = 0
    tasks_by_status: dict = {}
    total_users: int = 0
    top_performers: List[UserKPI] = []
    overall_completion_rate: float = 0.0
    generated_at: datetime


# ──── User Report ────
class TaskSummaryItem(BaseModel):
    task_id: int
    title: str
    status: str
    due_date: Optional[datetime] = None
    created_at: datetime

class UserReport(BaseModel):
    user_id: int
    full_name: str
    department: Optional[str] = None
    kpi: UserKPI
    recent_tasks: List[TaskSummaryItem] = []
    generated_at: datetime
