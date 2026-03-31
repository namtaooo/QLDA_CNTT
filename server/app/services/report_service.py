"""
Report Service — dashboard and per-user KPI reporting.
"""
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func as sqla_func

from app.models.task import Task, TaskStatus
from app.models.user import User, PerformanceMetric


def get_dashboard(db: Session) -> dict:
    """Aggregate system-wide metrics for the dashboard."""
    total_tasks = db.query(Task).count()
    total_users = db.query(User).filter(User.is_active == True).count()

    # Tasks grouped by status
    status_rows = (
        db.query(Task.status, sqla_func.count(Task.id))
        .group_by(Task.status).all()
    )
    tasks_by_status = {row[0]: row[1] for row in status_rows}

    done_count = tasks_by_status.get(TaskStatus.DONE, 0)
    completion_rate = (done_count / total_tasks * 100) if total_tasks else 0.0

    # Top performers
    top = (
        db.query(PerformanceMetric)
        .order_by(PerformanceMetric.productivity_score.desc())
        .limit(10).all()
    )
    top_performers = []
    for pm in top:
        user = db.query(User).filter(User.id == pm.user_id).first()
        if user:
            top_performers.append({
                "user_id": user.id,
                "full_name": user.full_name,
                "department": user.department,
                "tasks_completed": pm.tasks_completed,
                "overdue_rate": pm.overdue_rate,
                "avg_completion_time": pm.avg_completion_time,
                "productivity_score": pm.productivity_score,
            })

    return {
        "total_tasks": total_tasks,
        "tasks_by_status": tasks_by_status,
        "total_users": total_users,
        "top_performers": top_performers,
        "overall_completion_rate": round(completion_rate, 2),
        "generated_at": datetime.now(timezone.utc),
    }


def get_user_report(db: Session, user_id: int) -> dict:
    """Generate a KPI report for a specific user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    pm = db.query(PerformanceMetric).filter(
        PerformanceMetric.user_id == user_id
    ).first()

    kpi = {
        "user_id": user.id,
        "full_name": user.full_name,
        "department": user.department,
        "tasks_completed": pm.tasks_completed if pm else 0,
        "overdue_rate": pm.overdue_rate if pm else 0.0,
        "avg_completion_time": pm.avg_completion_time if pm else 0.0,
        "productivity_score": pm.productivity_score if pm else 0.0,
    }

    recent = (
        db.query(Task)
        .filter((Task.assignee_id == user_id) | (Task.creator_id == user_id))
        .order_by(Task.updated_at.desc())
        .limit(20).all()
    )
    recent_tasks = [
        {
            "task_id": t.id,
            "title": t.title,
            "status": t.status,
            "due_date": t.due_date,
            "created_at": t.created_at,
        }
        for t in recent
    ]

    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "department": user.department,
        "kpi": kpi,
        "recent_tasks": recent_tasks,
        "generated_at": datetime.now(timezone.utc),
    }
