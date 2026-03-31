"""
Office Service — AI-powered Office integration helpers.
Generates Excel formulas, Word reports, and processes document content.
"""
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)
AI_URL = settings.AI_ENGINE_URL


async def _ask_llm(prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{AI_URL}/generate",
                json={"query": prompt, "context": "", "app_context": "office"},
            )
            resp.raise_for_status()
            return resp.json().get("response", "")
    except Exception as e:
        logger.error(f"Office LLM call failed: {e}")
        return f"Lỗi kết nối AI Engine: {e}"


async def generate_excel_formula(description: str, cell_context: str = "") -> dict:
    """Generate an Excel formula based on natural language description."""
    prompt = (
        "Bạn là chuyên gia Microsoft Excel. Hãy tạo công thức Excel phù hợp.\n"
        f"Yêu cầu: {description}\n"
    )
    if cell_context:
        prompt += f"Ngữ cảnh ô/dữ liệu hiện tại: {cell_context}\n"
    prompt += "Chỉ trả về công thức Excel, giải thích ngắn gọn bên dưới."

    raw = await _ask_llm(prompt)
    lines = raw.strip().splitlines()
    formula = lines[0] if lines else ""
    explanation = "\n".join(lines[1:]) if len(lines) > 1 else ""
    return {"formula": formula, "explanation": explanation}


async def generate_word_report(topic: str, data_context: str = "") -> dict:
    """Generate a Word report outline or content."""
    prompt = (
        "Bạn là trợ lý soạn thảo tài liệu Word chuyên nghiệp.\n"
        f"Hãy soạn báo cáo về chủ đề: {topic}\n"
    )
    if data_context:
        prompt += f"Dữ liệu tham khảo:\n{data_context}\n"
    prompt += "Trả về nội dung báo cáo đầy đủ có tiêu đề, mục lục, nội dung chính."

    content = await _ask_llm(prompt)
    return {"report_content": content, "topic": topic}


async def analyze_document_content(content: str, action: str) -> dict:
    """Analyze pasted document content with a specified action."""
    prompt = (
        f"Hành động yêu cầu: {action}\n\n"
        f"Nội dung tài liệu:\n{content[:3000]}\n\n"
        "Hãy thực hiện yêu cầu trên và trả lời bằng tiếng Việt."
    )
    result = await _ask_llm(prompt)
    return {"action": action, "result": result}
