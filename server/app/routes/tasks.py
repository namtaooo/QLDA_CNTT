from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db
from app.routes.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.Task)
def create_task(
    *,
    db: Session = Depends(get_db),
    task_in: schemas.TaskCreate,
    current_user: models.User = Depends(get_current_user),
) -> Any:
    task = models.Task(
        **task_in.model_dump(),
        creator_id=current_user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/", response_model=List[schemas.Task])
def read_tasks(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
) -> Any:
    if current_user.role == "admin":
        tasks = db.query(models.Task).offset(skip).limit(limit).all()
    else:
        tasks = db.query(models.Task).filter(
            (models.Task.creator_id == current_user.id) | 
            (models.Task.assignee_id == current_user.id)
        ).offset(skip).limit(limit).all()
    return tasks

@router.get("/{id}", response_model=schemas.Task)
def read_task(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: models.User = Depends(get_current_user),
) -> Any:
    task = db.query(models.Task).filter(models.Task.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role != "admin" and task.creator_id != current_user.id and task.assignee_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return task
