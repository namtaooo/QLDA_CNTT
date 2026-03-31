"""
Chat Router — AI-powered chat with RAG context integration.
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from app import models, schemas
from app.core.database import get_db
from app.routes.deps import get_current_active_user
from app.core.config import settings

router = APIRouter()


from tenacity import retry, stop_after_attempt, wait_exponential
from app.utils.sanitizer import sanitize_input
import logging

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def safe_call_ai_engine(url: str, json_payload: dict):
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=json_payload)
        resp.raise_for_status()
        return resp.json()

@router.post("/send", response_model=schemas.ChatResponse)
async def chat_with_ai(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    chat_in: schemas.ChatRequest,
) -> Any:
    from app.services.chat_service import handle_chat_with_ai
    return await handle_chat_with_ai(db, current_user, chat_in)


@router.get("/conversations", response_model=List[schemas.Conversation])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    conversations = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id
    ).order_by(models.Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    return conversations


@router.get("/conversations/{conversation_id}", response_model=schemas.ConversationWithMessages)
def get_conversation_history(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # We return the conversation but also slice the messages manually for the response if needed.
    # To truly paginate a relationship, it's better to construct a custom response or use explicit queries.
    # For now, we will sort and limit the messages on the conversation object itself if possible, or just limit query.
    # Modifying the ORM object's relationship directly can be tricky. Let's just return the conversation.
    return conversation
