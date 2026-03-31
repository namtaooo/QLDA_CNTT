"""
Embeddings Manager — FAISS vector store with document chunking and metadata.
"""
import os
import logging
from typing import List, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    def __init__(self, model_name="intfloat/multilingual-e5-small",
                 index_path="vector_store"):
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self.index_path = index_path
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._load_or_create_index()

    def _load_or_create_index(self):
        try:
            if (os.path.exists(self.index_path) and
                    os.path.exists(os.path.join(self.index_path, "index.faiss"))):
                self.vector_store = FAISS.load_local(
                    self.index_path, self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info(f"Loaded existing FAISS index from {self.index_path}")
            else:
                self.vector_store = FAISS.from_texts(
                    ["Tài liệu giả định ban đầu"], self.embeddings
                )
                self.vector_store.save_local(self.index_path)
                logger.info("Created new empty FAISS index")
        except Exception as e:
            logger.error(f"Failed to load/create index: {e}")

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None):
        """Add raw texts directly (no chunking)."""
        if not self.vector_store:
            self._load_or_create_index()
        self.vector_store.add_texts(texts, metadatas=metadatas)
        self.vector_store.save_local(self.index_path)

    def add_document(self, content: str, metadata: dict = None):
        """
        Chunk a document and add all chunks to the vector store.
        metadata example: {"department": "IT", "role": "manager", "filename": "..."}
        """
        chunks = self.text_splitter.split_text(content)
        if not chunks:
            return

        chunk_metadatas = None
        if metadata:
            chunk_metadatas = [metadata.copy() for _ in chunks]
            for i, m in enumerate(chunk_metadatas):
                m["chunk_index"] = i

        self.add_texts(chunks, metadatas=chunk_metadatas)
        logger.info(f"Indexed {len(chunks)} chunks with metadata {metadata}")

    def similarity_search(self, query: str, k: int = 4,
                          filter_metadata: dict = None):
        """Search for similar documents, optionally filtered by metadata and threshold."""
        if not self.vector_store:
            return []
            
        # Retrieve more candidates first to allow client-side filtering and re-ranking
        results_with_score = self.vector_store.similarity_search_with_score(query, k=k*3)

        # FAISS returns L2 distance (lower is better) or inner product depending on metric.
        # Assuming HuggingFaceEmbeddings default to L2 distance.
        DISTANCE_THRESHOLD = 1.5

        filtered = []
        for doc, score in results_with_score:
            # 1. Distance Threshold Filter
            if score > DISTANCE_THRESHOLD:
                continue
                
            # 2. Client-side metadata filtering (FAISS doesn't support server-side metadata easily)
            if filter_metadata:
                match = all(
                    doc.metadata.get(key) == value
                    for key, value in filter_metadata.items()
                )
                if not match:
                    continue
                    
            filtered.append((doc, score))

        # 3. Simple Keyword Re-ranking (TF-style boosting) & Duplicate Removal
        # Boost items that have exact keyword matches of the query in their content.
        query_terms = set(query.lower().split())
        ranked_results = []
        seen_texts = set()
        
        for doc, score in filtered:
            # Duplicate Chunk Removal
            content_lower = doc.page_content.lower()
            if content_lower in seen_texts:
                continue
            seen_texts.add(content_lower)
            
            keyword_matches = sum(1 for term in query_terms if term in content_lower)
            
            # Boost score: Lower distance is better, so we subtract a boost value
            boosted_score = score - (keyword_matches * 0.1)
            ranked_results.append((doc, boosted_score))

        # Re-sort by boosted score
        ranked_results.sort(key=lambda x: x[1])
        
        # Return top-K documents
        final_docs = [doc for doc, _score in ranked_results[:k]]
        return final_docs
