import os
import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)

class EmbeddingsManager:
    def __init__(self, model_name="intfloat/multilingual-e5-small", index_path="vector_store"):
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self.index_path = index_path
        self.vector_store = None
        self._load_or_create_index()

    def _load_or_create_index(self):
        try:
            if os.path.exists(self.index_path) and os.path.exists(os.path.join(self.index_path, "index.faiss")):
                self.vector_store = FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
                logger.info(f"Loaded existing FAISS index from {self.index_path}")
            else:
                # Create empty index with a dummy text
                self.vector_store = FAISS.from_texts(["Tài liệu giả định ban đầu"], self.embeddings)
                self.vector_store.save_local(self.index_path)
                logger.info("Created new empty FAISS index")
        except Exception as e:
            logger.error(f"Failed to load/create index: {e}")

    def add_texts(self, texts, metadatas=None):
        if not self.vector_store:
            self._load_or_create_index()
        self.vector_store.add_texts(texts, metadatas=metadatas)
        self.vector_store.save_local(self.index_path)

    def similarity_search(self, query, k=4):
        if not self.vector_store:
            return []
        return self.vector_store.similarity_search(query, k=k)
