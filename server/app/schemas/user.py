from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = "user"
    is_active: Optional[bool] = True

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    full_name: str
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Properties to return to client
class User(UserInDBBase):
    pass

# Properties properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
