"""
RAG Package — Modular Data Ingestion + Retrieval + Generation
===============================================================

    data_loader.py   → RAG/data/ থেকে load + split
    embedding.py     → HuggingFaceEmbeddings (vector conversion)
    vectorestore.py  → FAISS/Chroma build/save/load (data_loader + embedding ব্যবহার করে)
    search.py        → retriever + ChatAnthropic দিয়ে RAG answer (vectorestore-এর output ব্যবহার করে)

app.py এই package-কে entry point হিসেবে ব্যবহার করে।
"""

from .data_loader import load_all_documents, load_and_split, split_documents
from .embedding import get_embedding_model
from .search import answer_question, build_rag_chain, get_llm, get_retriever
from .vectorestore import build_chroma_store, build_faiss_store, get_vector_store

__all__ = [
    "load_all_documents",
    "load_and_split",
    "split_documents",
    "get_embedding_model",
    "build_faiss_store",
    "build_chroma_store",
    "get_vector_store",
    "get_retriever",
    "build_rag_chain",
    "answer_question",
    "get_llm",
]
