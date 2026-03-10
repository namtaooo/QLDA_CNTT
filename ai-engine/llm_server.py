from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

from rag_pipeline import RAGPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Office Assistant - LLM Engine")

# Init RAG pipeline
rag = RAGPipeline()

class GenerateRequest(BaseModel):
    query: str
    context: str = ""
    app_context: str = "web"

class GenerateResponse(BaseModel):
    response: str

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": rag.is_ready()}

@app.post("/generate", response_model=GenerateResponse)
async def generate_response(req: GenerateRequest):
    try:
        # If there's document matching or general query
        answer = rag.generate_answer(req.query, req.context, req.app_context)
        return {"response": answer}
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
