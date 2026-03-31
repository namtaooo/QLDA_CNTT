"""
RAG Pipeline — Loads local Qwen model and provides generation with RAG context.
"""
import os
import logging

from embeddings import EmbeddingsManager

logger = logging.getLogger(__name__)

# Model configuration
MODEL_PATH = os.getenv("MODEL_PATH", "./models/qwen")


class RAGPipeline:
    def __init__(self):
        self.embed_manager = EmbeddingsManager()
        self.tokenizer = None
        self.model = None
        self.ready = False
        self._init_llm()

    def _init_llm(self):
        """Load local Qwen model from disk."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            if os.path.exists(MODEL_PATH):
                logger.info(f"Loading Qwen model from {MODEL_PATH}...")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    MODEL_PATH, trust_remote_code=True
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    MODEL_PATH, trust_remote_code=True, device_map="auto"
                )
                self.ready = True
                logger.info("Qwen model loaded successfully.")
            else:
                logger.warning(
                    f"Model path {MODEL_PATH} not found. "
                    "Running in mock mode. Download model first."
                )
                self.ready = False
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}. Running in mock mode.")
            self.ready = False

    def is_ready(self):
        return self.ready

    def _craft_prompt(self, query: str, context: str,
                      retrieved_docs: list, app_context: str) -> str:
        doc_texts = "\n".join([doc.page_content for doc in retrieved_docs])
        # Context limit: keep max 4000 characters
        if len(doc_texts) > 4000:
            doc_texts = doc_texts[:4000] + "\n...(Bị cắt ngắn do độ dài)"

        system_prompt = (
            f"Bạn là trợ lý AI Office thông minh. "
            f"Ứng dụng hiện tại: {app_context}. Hãy trả lời bằng tiếng Việt."
        )
        if doc_texts:
            system_prompt += f"\nDựa vào tài liệu sau:\n{doc_texts}"

        full_prompt = (
            f"{system_prompt}\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi của người dùng: {query}\n\n"
            f"Trả lời:"
        )
        return full_prompt

    def generate_answer(self, query: str, context: str = "",
                        app_context: str = "web", user_id: int = None) -> str:
        # 1. Retrieve relevant docs
        filter_meta = {"user_id": user_id} if user_id else None
        docs = self.embed_manager.similarity_search(query, k=3, filter_metadata=filter_meta)

        # 2. Craft prompt
        prompt = self._craft_prompt(query, context, docs, app_context)

        # 3. Generate with real model if available, else mock
        if self.ready and self.model and self.tokenizer:
            try:
                inputs = self.tokenizer(prompt, return_tensors="pt").to(
                    self.model.device
                )
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                )
                response = self.tokenizer.decode(
                    outputs[0][inputs["input_ids"].shape[-1]:],
                    skip_special_tokens=True,
                )
                return response.strip()
            except Exception as e:
                logger.error(f"Generation error: {e}")
                return f"Lỗi khi sinh phản hồi: {e}"
        else:
            # Mock response
            response = (
                f"[Mock] Dựa theo quy trình hệ thống, đây là giải pháp cho "
                f"yêu cầu '{query}' trong ngữ cảnh {app_context}."
            )
            if docs and docs[0].page_content != "Tài liệu giả định ban đầu":
                response += f" Tham khảo: {docs[0].page_content[:80]}..."
            return response
