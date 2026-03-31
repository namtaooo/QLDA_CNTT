from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr


# ──── Skill ────
class SkillBase(BaseModel):
    skill_name: str
    level: int = 1

class SkillCreate(SkillBase):
    pass

class Skill(SkillBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# ──── Performance Metric ────
class PerformanceMetricOut(BaseModel):
    tasks_completed: int = 0
    overdue_rate: float = 0.0
    avg_completion_time: float = 0.0
    productivity_score: float = 0.0
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ──── User ────
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = "staff"
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    email: EmailStr
    full_name: str
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserWithDetails(UserInDBBase):
    skills: List[Skill] = []
    performance: Optional[PerformanceMetricOut] = None

class UserInDB(UserInDBBase):
    hashed_password: str


# ──── Auth Tokens ────
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None
