"""
Reports Router — dashboard and per-user KPI reports.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.core.database import get_db
from app.routes.deps import get_current_active_user
from app import models
from app.services import report_service

router = APIRouter()


@router.get("/dashboard", response_model=schemas.DashboardReport)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """System-wide dashboard metrics. Accessible to managers and admins."""
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Only managers/admins can view dashboard")
    return report_service.get_dashboard(db)


@router.get("/user/{user_id}", response_model=schemas.UserReport)
def get_user_report(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """Per-user KPI report. Users can view their own; managers can view any."""
    if current_user.role not in ("admin", "manager") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    result = report_service.get_user_report(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result
