from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from app import models, schemas
from app.core.database import get_db
from app.routes.deps import get_current_user
from app.core.config import settings

router = APIRouter()

@router.post("/send", response_model=schemas.ChatResponse)
async def chat_with_ai(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    chat_in: schemas.ChatRequest,
) -> Any:
    # Get or create conversation
    if chat_in.conversation_id:
        conversation = db.query(models.Conversation).filter(
            models.Conversation.id == chat_in.conversation_id,
            models.Conversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = models.Conversation(
            user_id=current_user.id,
            title=chat_in.message[:50] + "...",
            app_context=chat_in.app_context
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Save user message
    user_msg = models.Message(
        conversation_id=conversation.id,
        role="user",
        content=chat_in.message
    )
    db.add(user_msg)
    db.commit()

    # Call AI Engine (mocked for now, will implement actual call in services later)
    # This is where we'd call the LLM service
    try:
        async with httpx.AsyncClient() as client:
            # Using placeholder URL since ai_service is not fully implemented here
            # ai_resp = await client.post(f"{settings.AI_ENGINE_URL}/generate", json={"query": chat_in.message})
            # ai_text = ai_resp.json().get("response", "Error from AI Engine")
            ai_text = "Đây là phản hồi giả lập từ AI Assistant. Hệ thống AI Engine chưa được kết nối."
    except Exception as e:
        ai_text = f"Lỗi kết nối tới AI Engine: {str(e)}"

    # Save assistant message
    assistant_msg = models.Message(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_text
    )
    db.add(assistant_msg)
    db.commit()

    return schemas.ChatResponse(
        message=ai_text,
        conversation_id=conversation.id
    )

@router.get("/conversations", response_model=List[schemas.Conversation])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    conversations = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return conversations

@router.get("/conversations/{conversation_id}", response_model=schemas.ConversationWithMessages)
def get_conversation_history(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> Any:
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
