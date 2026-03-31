"""
Auth Router — login, register, test-token, and skill management.
"""
from datetime import timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.routes.deps import get_current_user, get_current_active_user

router = APIRouter()


@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "refresh_token": security.create_refresh_token(
            user.id, expires_delta=refresh_token_expires
        ),
        "token_type": "bearer",
    }

class RefreshTokenRequest(schemas.TokenPayload):
    refresh_token: str

@router.post("/refresh-token", response_model=schemas.Token)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> Any:
    from jose import jwt, JWTError
    from pydantic import ValidationError
    try:
        payload = jwt.decode(
            request.refresh_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
        if token_data.type != "refresh":
            raise HTTPException(status_code=403, detail="Invalid token type")
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
    user = db.query(models.User).filter(models.User.id == token_data.sub).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found or inactive")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "refresh_token": request.refresh_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=schemas.User)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
) -> Any:
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user_obj = models.User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        department=user_in.department,
        role=user_in.role or "staff",
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj


@router.post("/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(get_current_active_user)) -> Any:
    return current_user


@router.get("/me", response_model=schemas.UserWithDetails)
def get_current_user_details(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """Get current user with skills and performance metrics."""
    return current_user


# ──── Skill management ────

@router.post("/me/skills", response_model=schemas.Skill)
def add_skill(
    *,
    db: Session = Depends(get_db),
    skill_in: schemas.SkillCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    skill = models.Skill(
        user_id=current_user.id,
        skill_name=skill_in.skill_name,
        level=skill_in.level,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.get("/me/skills", response_model=List[schemas.Skill])
def get_my_skills(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    return db.query(models.Skill).filter(models.Skill.user_id == current_user.id).all()


@router.delete("/me/skills/{skill_id}")
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    skill = db.query(models.Skill).filter(
        models.Skill.id == skill_id,
        models.Skill.user_id == current_user.id,
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    db.delete(skill)
    db.commit()
    return {"detail": "Skill deleted"}
