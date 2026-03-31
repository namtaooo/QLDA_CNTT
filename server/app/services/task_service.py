"""
Task Service — business logic for task management, workflow, KPI calculation.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func as sqla_func

from app.models.task import Task, TaskLog, TaskStatus
from app.models.user import User, PerformanceMetric


# ──────── Valid workflow transitions ────────
VALID_TRANSITIONS = {
    TaskStatus.CREATED:     [TaskStatus.ASSIGNED],
    TaskStatus.ASSIGNED:    [TaskStatus.IN_PROGRESS, TaskStatus.CREATED],
    TaskStatus.IN_PROGRESS: [TaskStatus.REVIEW, TaskStatus.ASSIGNED],
    TaskStatus.REVIEW:      [TaskStatus.DONE, TaskStatus.IN_PROGRESS],
    TaskStatus.DONE:        [],  # terminal state
}


def _log(db: Session, task_id: int, user_id: int, action: str,
         old: str = None, new: str = None, note: str = None):
    """Write a single task log entry."""
    entry = TaskLog(
        task_id=task_id, user_id=user_id,
        action=action, old_value=old, new_value=new, note=note,
    )
    db.add(entry)


# ──────── Task CRUD ────────

def create_task(db: Session, title: str, description: str,
                creator_id: int, priority: str = "medium",
                due_date=None, assignee_id: int = None) -> Task:
    task = Task(
        title=title, description=description,
        creator_id=creator_id, priority=priority,
        due_date=due_date, assignee_id=assignee_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    _log(db, task.id, creator_id, "task_created", new=task.title)
    db.commit()
    return task


def assign_task(db: Session, task: Task, assignee_id: int,
                actor_id: int, note: str = None) -> Task:
    old_assignee = str(task.assignee_id) if task.assignee_id else None
    task.assignee_id = assignee_id
    if task.status == TaskStatus.CREATED:
        task.status = TaskStatus.ASSIGNED
    _log(db, task.id, actor_id, "assigned",
         old=old_assignee, new=str(assignee_id), note=note)
    db.commit()
    db.refresh(task)
    return task


def update_status(db: Session, task: Task, new_status: str,
                  actor_id: int, note: str = None) -> Task:
    old = task.status
    new_enum = TaskStatus(new_status)

    allowed = VALID_TRANSITIONS.get(TaskStatus(old), [])
    if new_enum not in allowed:
        raise ValueError(
            f"Không thể chuyển trạng thái từ {old} → {new_status}. "
            f"Cho phép: {[s.value for s in allowed]}"
        )

    task.status = new_enum.value
    _log(db, task.id, actor_id, "status_changed",
         old=old, new=new_status, note=note)
    db.commit()
    db.refresh(task)

    # If task completed → recalculate KPIs for assignee
    if new_enum == TaskStatus.DONE and task.assignee_id:
        recalculate_kpi(db, task.assignee_id)

    return task


def get_tasks_by_user(db: Session, user_id: int,
                      skip: int = 0, limit: int = 100) -> List[Task]:
    return (
        db.query(Task)
        .filter((Task.assignee_id == user_id) | (Task.creator_id == user_id))
        .order_by(Task.updated_at.desc())
        .offset(skip).limit(limit).all()
    )


# ──────── KPI Recalculation ────────

def recalculate_kpi(db: Session, user_id: int):
    """Recompute KPI metrics for a single user and persist."""
    completed = db.query(Task).filter(
        Task.assignee_id == user_id, Task.status == TaskStatus.DONE
    ).all()
    tasks_completed = len(completed)

    total_assigned = db.query(Task).filter(Task.assignee_id == user_id).count()

    # Overdue = completed after due_date OR still open past due_date
    now = datetime.now(timezone.utc)
    overdue_count = db.query(Task).filter(
        Task.assignee_id == user_id,
        Task.due_date != None,
        (
            ((Task.status == TaskStatus.DONE) & (Task.updated_at > Task.due_date)) |
            ((Task.status != TaskStatus.DONE) & (Task.due_date < now))
        )
    ).count()
    overdue_rate = (overdue_count / total_assigned * 100) if total_assigned else 0.0

    # Avg completion time (hours) — from created_at to updated_at of DONE tasks
    avg_hours = 0.0
    if completed:
        deltas = [(t.updated_at - t.created_at).total_seconds() / 3600 for t in completed]
        avg_hours = sum(deltas) / len(deltas)

    # Simple productivity score: completed weight − overdue penalty
    productivity = min(100.0, max(0.0,
        tasks_completed * 10 - overdue_rate * 0.5
    ))

    metric = db.query(PerformanceMetric).filter(
        PerformanceMetric.user_id == user_id
    ).first()
    if not metric:
        metric = PerformanceMetric(user_id=user_id)
        db.add(metric)

    metric.tasks_completed = tasks_completed
    metric.overdue_rate = round(overdue_rate, 2)
    metric.avg_completion_time = round(avg_hours, 2)
    metric.productivity_score = round(productivity, 2)
    db.commit()
