"""
AI Office Assistant — LLM Engine Server
Loads Qwen model from local path, serves /generate and /ai/chat endpoints.
Uses RAG pipeline for context-aware responses.
"""
import logging
from typing import List, Optional
import hashlib
from fastapi import FastAPI, HTTPException
import os
from pydantic import BaseModel
import redis

# Redis Configuration for Distributed Caching
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis cache successfully.")
except Exception as e:
    logger.warning(f"Failed to connect to Redis. Responses will not be cached: {e}")
    redis_client = None

from rag_pipeline import RAGPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Office Assistant - LLM Engine")

# Init RAG pipeline (loads model + vector store)
rag = RAGPipeline()

# Cache for responses handled by Redis now. TTL = 300s (5 mins)
CACHE_TTL = 300

import re

# Advanced Guardrails (Jailbreak / Prompt Injection Detection)
DENYLIST_REGEX = re.compile(
    r"(ignore [a-z ]+ instructions)|(system prompt)|(bypassed)|(hack)|(exploit)|(you are now)|(act as)|(đụ)|(má)", 
    re.IGNORECASE
)

def check_guardrails(text: str) -> bool:
    """Returns False if text triggers jailbreak or prompt injection detection."""
    if DENYLIST_REGEX.search(text):
        return False
    return True

def needs_rag(text: str) -> bool:
    """Fast classification: If it's a short greeting/chit-chat, skip RAG."""
    words = text.strip().split()
    if len(words) <= 3:
        chit_chat_words = {"chào", "hi", "hello", "cảm ơn", "thanks", "ok", "tạm biệt", "bye"}
        if any(w.lower() in chit_chat_words for w in words):
            return False
    return True

# ──── Request / Response Models ────

class GenerateRequest(BaseModel):
    query: str
    context: str = ""
    app_context: str = "web"
    user_id: Optional[int] = None

class GenerateResponse(BaseModel):
    response: str

class ChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    app_context: str = "web"
    use_rag: bool = True
    user_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    rag_sources: List[str] = []

# ──── Endpoints ────

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": rag.is_ready()}


@app.post("/generate", response_model=GenerateResponse)
async def generate_response(req: GenerateRequest):
    """Single-turn generation with optional RAG."""
    if not check_guardrails(req.query):
        raise HTTPException(status_code=400, detail="Query violates safety policy.")
        
    cache_key = hashlib.md5(f"{req.query}_{req.context}_{req.app_context}".encode()).hexdigest()
    if redis_client:
        cached_response = redis_client.get(cache_key)
        if cached_response:
            logger.info("Serving from Redis cache")
            return {"response": cached_response}
        
    try:
        answer = rag.generate_answer(req.query, req.context, req.app_context, req.user_id)
        if redis_client:
            redis_client.setex(cache_key, CACHE_TTL, answer)
        return {"response": answer}
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Multi-turn chat endpoint.
    Combines conversation history + RAG retrieved docs into the prompt.
    """
    try:
        # Extract the latest user message
        user_msg = ""
        for m in reversed(req.messages):
            if m.role == "user":
                user_msg = m.content
                break

        if not check_guardrails(user_msg):
            return ChatResponse(response="Tôi không thể phản hồi yêu cầu này do chính sách an toàn.")

        # Sliding Window / Token-aware trimming (Rough estimate: 4 chars ~ 1 token)
        # Keep history under 1000 tokens (~4000 characters) to save context window.
        history_str = ""
        current_chars = 0
        MAX_HISTORY_CHARS = 4000
        
        # Build from newest to oldest (excluding the current user_msg)
        for m in reversed(req.messages[:-1]): 
            line = f"[{m.role}]: {m.content}\n"
            if current_chars + len(line) > MAX_HISTORY_CHARS:
                history_str = "[Hệ thống: Lịch sử cũ quá dài đã bị cắt bớt]...\n" + history_str
                break
            history_str = line + history_str
            current_chars += len(line)
        
        history = history_str.strip()

        # RAG retrieval & Query Classification
        rag_sources = []
        rag_context = ""
        
        should_use_rag = req.use_rag and needs_rag(user_msg)
        
        if should_use_rag and user_msg:
            # Add relevance filter + user_id filter
            filter_meta = {"user_id": req.user_id} if req.user_id else None
            docs = rag.embed_manager.similarity_search(user_msg, k=3, filter_metadata=filter_meta)
            if docs:
                rag_context = "\n".join([doc.page_content for doc in docs])
                rag_sources = [doc.page_content[:80] for doc in docs
                               if doc.page_content != "Tài liệu giả định ban đầu"]
                               
        cache_key = hashlib.md5(f"chat_{user_msg}_{history}_{rag_context}_{req.app_context}".encode()).hexdigest()
        
        if redis_client:
            cached_response = redis_client.get(cache_key)
            if cached_response:
                 return ChatResponse(response=cached_response, rag_sources=rag_sources)

        # Generate
        answer = rag.generate_answer(
            query=user_msg,
            context=f"Lịch sử hội thoại:\n{history}\n\nTài liệu liên quan:\n{rag_context}",
            app_context=req.app_context,
            user_id=req.user_id,
        )
        if redis_client:
            redis_client.setex(cache_key, CACHE_TTL, answer)
            
        return ChatResponse(response=answer, rag_sources=rag_sources)

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class IndexDocumentRequest(BaseModel):
    content: str
    metadata: dict = {}

@app.post("/index-document")
async def index_document(req: IndexDocumentRequest):
    """Index a document into the FAISS vector store with metadata."""
    try:
        rag.embed_manager.add_document(req.content, req.metadata)
        return {"status": "indexed", "metadata": req.metadata}
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
