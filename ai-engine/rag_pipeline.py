import logging
from embeddings import EmbeddingsManager

# In a real scenario, you'd load a local LLM via HuggingFacePipeline or use OpenAI
# For this scaffold, we're mocking the LLM inference to demonstrate the structure.
# from langchain_community.llms import HuggingFacePipeline
# from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        self.embed_manager = EmbeddingsManager()
        self.ready = True # Set to false if dynamically loading large models
        self._init_llm()

    def _init_llm(self):
        """Initialize local LLM here. Skipped in scaffold for rapid deployment."""
        pass

    def is_ready(self):
        return self.ready

    def _craft_prompt(self, query: str, context: str, retrieved_docs: list, app_context: str) -> str:
        doc_texts = "\\n".join([doc.page_content for doc in retrieved_docs])
        
        system_prompt = f"Bạn là trợ lý AI Office thông minh. Ứng dụng hiện tại: {app_context}. Hãy trả lời bằng tiếng Việt."
        if doc_texts:
            system_prompt += f"\\nDựa vào tài liệu sau:\\n{doc_texts}"
            
        full_prompt = f"{system_prompt}\\n\\nCâu hỏi của người dùng: {query}\\nNgữ cảnh đính kèm: {context}\\n\\nTrả lời:"
        return full_prompt

    def generate_answer(self, query: str, context: str = "", app_context: str = "web") -> str:
        # 1. Retrieve relevant info
        docs = self.embed_manager.similarity_search(query, k=3)
        
        # 2. Craft Prompt
        prompt = self._craft_prompt(query, context, docs, app_context)
        
        # 3. Generate (Mocked here logic)
        # return self.llm(prompt)
        
        # Mocked Response combining knowledge
        response = f"Dựa theo quy trình hệ thống, đây là giải pháp cho yêu cầu '{query}' trong ngữ cảnh {app_context}."
        if docs and docs[0].page_content != "Tài liệu giả định ban đầu":
            response += f" Tham khảo từ tài liệu: {docs[0].page_content[:50]}..."
            
        return response
