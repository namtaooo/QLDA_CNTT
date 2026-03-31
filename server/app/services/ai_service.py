"""
AI Service — skill extraction, intelligent assignment, project planning.
Communicates with the AI Engine (LLM) running on port 8001.
"""
import logging
from typing import List, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, Skill, PerformanceMetric
from app.models.task import Task

logger = logging.getLogger(__name__)

AI_URL = settings.AI_ENGINE_URL  # http://localhost:8001


from tenacity import retry, stop_after_attempt, wait_exponential
import time

class AIEngineClient:
    def __init__(self, base_url: str = AI_URL):
        self.base_url = base_url

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _safe_post(self, endpoint: str, json_payload: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=json_payload)
                resp.raise_for_status()
                
                latency = time.time() - start_time
                logger.info(f"AI Engine call to {endpoint} succeeded. Latency: {latency:.2f}s")
                
                return resp.json()
        except Exception as e:
            logger.error(f"AI Engine call to {endpoint} failed: {e}")
            raise

    async def chat(self, messages_payload: list, app_context: str, use_rag: bool, user_id: int) -> str:
        payload = {
            "messages": messages_payload,
            "app_context": app_context or "web",
            "use_rag": use_rag,
            "user_id": user_id
        }
        try:
            data = await self._safe_post("/ai/chat", payload)
            return data.get("response", "Không nhận được phản hồi từ AI.")
        except Exception as e:
            logger.error(f"Chat failed after retries: {e}. Trying fallback.")
            return await self.generate(messages_payload[-1]["content"], app_context, user_id)

    async def generate(self, query: str, app_context: str = "web", user_id: int = None) -> str:
        try:
            payload = {
                "query": query,
                "context": "",
                "app_context": app_context,
                "user_id": user_id
            }
            data = await self._safe_post("/generate", payload)
            return data.get("response", "Hệ thống AI hiện đang quá tải hoặc gián đoạn. Vui lòng thử lại sau.")
        except Exception as e:
            logger.error(f"Fallback generation failed: {e}")
            return "Rất tiếc, hệ thống AI đang gặp sự cố nghiêm trọng không thể phản hồi lúc này."

    def index_document_sync(self, content: str, metadata: dict) -> dict:
        import asyncio
        payload = {"content": content, "metadata": metadata}
        # Run async function in a new sync event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._safe_post("/index-document", payload))
            return result
        finally:
            loop.close()

ai_client = AIEngineClient()

async def _ask_llm(prompt: str) -> str:
    """Send a prompt to the AI Engine and return the raw text answer."""
    return await ai_client.generate(prompt, app_context="system")


# ──────── Skill extraction ────────

async def extract_skills_from_description(description: str) -> List[str]:
    """Use the LLM to infer required skills from a task description."""
    prompt = (
        "Hãy phân tích mô tả công việc sau và liệt kê các kỹ năng cần thiết.\n"
        "Chỉ trả về danh sách kỹ năng, mỗi kỹ năng trên một dòng, "
        "không giải thích thêm.\n\n"
        f"Mô tả công việc:\n{description}"
    )
    raw = await _ask_llm(prompt)
    if not raw:
        return []
    skills = [s.strip("- •").strip() for s in raw.strip().splitlines() if s.strip()]
    return skills


# ──────── Intelligent assignment ────────

def rank_candidates(
    db: Session,
    required_skills: List[str],
    exclude_user_id: int = None,
) -> List[dict]:
    """
    Rank all active staff by:
      1. Number of matched skills (weighted by level)
      2. Past performance (productivity_score)
    Returns sorted list of dicts with user info and score.
    """
    users = db.query(User).filter(User.is_active == True, User.role.in_(["staff", "manager"])).all()
    if exclude_user_id:
        users = [u for u in users if u.id != exclude_user_id]

    required_lower = [s.lower() for s in required_skills]
    candidates = []

    for user in users:
        # Skill match
        matched = []
        skill_score = 0.0
        for skill in user.skills:
            if skill.skill_name.lower() in required_lower:
                matched.append(skill.skill_name)
                skill_score += skill.level  # higher level = more weight

        # Performance score
        perf_score = 0.0
        if user.performance:
            perf_score = user.performance.productivity_score

        # Combined score (60% skill, 40% performance, normalized)
        max_skill = len(required_skills) * 5 if required_skills else 1
        combined = (skill_score / max_skill) * 60 + (perf_score / 100) * 40

        candidates.append({
            "user_id": user.id,
            "full_name": user.full_name,
            "matched_skills": matched,
            "score": round(combined, 2),
        })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates


async def suggest_assignment(db: Session, task: Task) -> dict:
    """
    Full AI-powered assignment pipeline:
      1. Extract required skills from task description
      2. Rank candidates
      3. Return result dict
    """
    required_skills = await extract_skills_from_description(task.description or task.title)
    if not required_skills:
        required_skills = []

    candidates = rank_candidates(db, required_skills, exclude_user_id=task.creator_id)

    return {
        "task_id": task.id,
        "required_skills": required_skills,
        "candidates": candidates,
        "recommended_assignee_id": candidates[0]["user_id"] if candidates else None,
    }


# ──────── AI Project Planning ────────

async def generate_project_plan(goal: str, users_info: str = "") -> dict:
    """
    Use LLM to break a project goal into tasks with timeline.
    Returns a structured dict.
    """
    prompt = (
        "Bạn là quản lý dự án AI. Hãy lập kế hoạch cho mục tiêu dự án sau.\n"
        "Trả về danh sách task theo định dạng JSON array, mỗi task gồm:\n"
        '  {"title": "...", "description": "...", "priority": "low|medium|high|critical", '
        '"estimated_days": N}\n\n'
        f"Mục tiêu dự án:\n{goal}\n"
    )
    if users_info:
        prompt += f"\nThông tin nhân viên hiện có:\n{users_info}\n"

    raw = await _ask_llm(prompt)

    # Try to parse JSON from the response
    import json
    tasks = []
    try:
        # Attempt to extract JSON array from LLM output
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            tasks = json.loads(raw[start:end])
    except (json.JSONDecodeError, ValueError):
        # Fallback: create a single task from the goal
        tasks = [{"title": goal, "description": raw, "priority": "medium", "estimated_days": 7}]

    total_days = sum(t.get("estimated_days", 1) for t in tasks)
    return {
        "project_goal": goal,
        "tasks": tasks,
        "total_estimated_days": total_days,
    }
