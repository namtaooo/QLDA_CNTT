from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    title: Optional[str] = None
    app_context: Optional[str] = None

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationWithMessages(Conversation):
    messages: List[Message] = []

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    app_context: Optional[str] = "web" # 'web', 'word', 'excel', 'powerpoint'

class ChatResponse(BaseModel):
    message: str
    conversation_id: int
