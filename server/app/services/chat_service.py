import logging
from typing import Any
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.utils.sanitizer import sanitize_input
from app.services.ai_service import ai_client

logger = logging.getLogger(__name__)

async def handle_chat_with_ai(
    db: Session,
    current_user: models.User,
    chat_in: schemas.ChatRequest
) -> schemas.ChatResponse:
    safe_message = sanitize_input(chat_in.message)
    if not safe_message:
        raise HTTPException(status_code=400, detail="Invalid or empty message")

    # 1. Cost Control: Check token limits and reset if needed
    now = datetime.now(timezone.utc)
    if current_user.last_token_reset.date() < now.date():
        current_user.daily_tokens_used = 0
        current_user.last_token_reset = now
        db.commit()

    if current_user.daily_tokens_used >= current_user.token_limit:
        raise HTTPException(status_code=429, detail="Bạn đã dùng hết số lượng Token hôm nay. Vui lòng quay lại vào ngày mai.")


    try:
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
                title=safe_message[:50] + "...",
                app_context=chat_in.app_context
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # Save user message
        user_msg = models.Message(
            conversation_id=conversation.id,
            role="user",
            content=safe_message
        )
        db.add(user_msg)
        db.commit()

        # Build message history for multi-turn chat
        db_messages = (
            db.query(models.Message)
            .filter(models.Message.conversation_id == conversation.id)
            .order_by(models.Message.created_at)
            .limit(20).all()
        )
        messages_payload = [
            {"role": m.role, "content": m.content} for m in db_messages
        ]

        # Call AI Engine via dedicated Service Layer
        ai_text = await ai_client.chat(
            messages_payload=messages_payload,
            app_context=chat_in.app_context,
            use_rag=True,
            user_id=current_user.id
        )

        # Save assistant message
        assistant_msg = models.Message(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_text
        )
        db.add(assistant_msg)
        
        # Calculate Token Usage (Estimate: 4 characters = 1 token)
        total_input_chars = sum(len(m["content"]) for m in messages_payload)
        total_output_chars = len(ai_text)
        estimated_tokens = (total_input_chars + total_output_chars) // 4
        
        current_user.daily_tokens_used += estimated_tokens
        
        db.commit()

        return schemas.ChatResponse(
            message=ai_text,
            conversation_id=conversation.id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Chat transaction failed: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi xử lý hội thoại")
