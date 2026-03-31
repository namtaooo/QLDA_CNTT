from fastapi import APIRouter
from app.routes import auth, chat, tasks, documents, office, reports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(office.router, prefix="/office", tags=["office"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
