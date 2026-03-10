import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Office Assistant"
    API_V1_STR: str = "/api/v1"
    
    # SECURITY
    SECRET_KEY: str = os.getenv("SECRET_KEY", "b3n91823190823091820391823019283")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # DATABASE
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ai_office_db")
    SQLALCHEMY_DATABASE_URI: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"
    
    # AI ENGINE
    AI_ENGINE_URL: str = os.getenv("AI_ENGINE_URL", "http://localhost:8001")
    
    class Config:
        case_sensitive = True

settings = Settings()
