"""
Tasks Router — CRUD + assign + status + AI suggestion + planning.
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db
from app.routes.deps import get_current_active_user
from app.services import task_service, ai_service

router = APIRouter()


# ──── Create ────
@router.post("/", response_model=schemas.Task)
def create_task(
    *,
    db: Session = Depends(get_db),
    task_in: schemas.TaskCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    task = task_service.create_task(
        db,
        title=task_in.title,
        description=task_in.description,
        creator_id=current_user.id,
        priority=task_in.priority or "medium",
        due_date=task_in.due_date,
        assignee_id=task_in.assignee_id,
    )
    return task


# ──── List (all or filtered) ────
@router.get("/", response_model=List[schemas.Task])
def read_tasks(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    if current_user.role in ("admin", "manager"):
        tasks = db.query(models.Task).offset(skip).limit(limit).all()
    else:
        tasks = task_service.get_tasks_by_user(db, current_user.id, skip, limit)
    return tasks


# ──── Get single task (with logs) ────
@router.get("/{id}", response_model=schemas.TaskWithLogs)
def read_task(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    task = db.query(models.Task).filter(models.Task.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if (
        current_user.role not in ("admin", "manager")
        and task.creator_id != current_user.id
        and task.assignee_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return task


# ──── Get tasks by user ────
@router.get("/user/{user_id}", response_model=List[schemas.Task])
def read_tasks_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    if current_user.role not in ("admin", "manager") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return task_service.get_tasks_by_user(db, user_id, skip, limit)


# ──── Assign task ────
@router.post("/{id}/assign", response_model=schemas.Task)
def assign_task(
    *,
    db: Session = Depends(get_db),
    id: int,
    payload: schemas.TaskAssign,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    task = db.query(models.Task).filter(models.Task.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role not in ("admin", "manager") and task.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only managers or task creator can assign")
    # Verify assignee exists
    assignee = db.query(models.User).filter(models.User.id == payload.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee user not found")
    return task_service.assign_task(db, task, payload.assignee_id, current_user.id, payload.note)


# ──── Update status ────
@router.put("/{id}/status", response_model=schemas.Task)
def update_task_status(
    *,
    db: Session = Depends(get_db),
    id: int,
    payload: schemas.TaskStatusUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    task = db.query(models.Task).filter(models.Task.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        return task_service.update_status(db, task, payload.status, current_user.id, payload.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ──── AI: suggest best assignee ────
@router.get("/{id}/suggest-assignee", response_model=schemas.AIAssignmentResult)
async def suggest_assignee(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    task = db.query(models.Task).filter(models.Task.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    result = await ai_service.suggest_assignment(db, task)
    return result


# ──── AI: project planning ────
class ProjectGoalInput(BaseModel):
    goal: str

@router.post("/ai/plan-project", response_model=schemas.ProjectPlan)
async def plan_project(
    *,
    db: Session = Depends(get_db),
    payload: ProjectGoalInput,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    # Gather user info for context
    users = db.query(models.User).filter(models.User.is_active == True).all()
    users_info = "\n".join([
        f"- {u.full_name} ({u.department or 'N/A'}): "
        + ", ".join([s.skill_name for s in u.skills]) if u.skills else f"- {u.full_name}"
        for u in users
    ])
    result = await ai_service.generate_project_plan(payload.goal, users_info)
    return result
