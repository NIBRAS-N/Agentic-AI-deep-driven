"""
RAG Vector Store — FAISS ও ChromaDB Build/Load/Save
====================================================

## Pipeline Position

    data_loader.load_and_split()     →  chunks
    embedding.get_embedding_model()  →  embeddings
                    ↓
              vectorestore.py   ← (এই file)
                    ↓
        FAISS (data/faiss_index/)  অথবা  Chroma (data/chroma_db/)
                    ↓
              search.py  (retriever + RAG chain)

## FAISS vs Chroma

| | FAISS | Chroma |
|---|---|---|
| Storage | in-memory, `save_local()` দরকার | disk-persistent, automatic |
| ব্যবহার | দ্রুত prototyping | persistent, production-like store |

## get_vector_store() — Smart Loader

ইতিমধ্যে index/collection disk-এ থাকলে সরাসরি load করে; না থাকলে (বা
`rebuild=True` দিলে) data_loader দিয়ে documents load+split করে নতুন
index তৈরি করে save করে।
"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from .data_loader import DATA_DIR, load_and_split
from .embedding import get_embedding_model

FAISS_INDEX_DIR = DATA_DIR / "faiss_index"
CHROMA_DIR = DATA_DIR / "chroma_db"
CHROMA_COLLECTION = "rag_documents"


def build_faiss_store(chunks: list[Document], save_path: Path = FAISS_INDEX_DIR) -> FAISS:
    """Chunks থেকে নতুন FAISS index বানিয়ে disk-এ save করে।"""
    embeddings = get_embedding_model()
    store = FAISS.from_documents(documents=chunks, embedding=embeddings)
    save_path.mkdir(parents=True, exist_ok=True)
    store.save_local(str(save_path))
    return store


def load_faiss_store(load_path: Path = FAISS_INDEX_DIR) -> FAISS:
    """আগে থেকে save করা FAISS index disk থেকে load করে।"""
    embeddings = get_embedding_model()
    return FAISS.load_local(
        folder_path=str(load_path),
        embeddings=embeddings,
        allow_dangerous_deserialization=True,  # locally save করা নিজেদের index-এর জন্য নিরাপদ
    )


def build_chroma_store(chunks: list[Document], persist_dir: Path = CHROMA_DIR) -> Chroma:
    """Chunks থেকে নতুন Chroma collection বানায় — automatically disk-এ persist হয়।"""
    embeddings = get_embedding_model()
    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(persist_dir),
        collection_name=CHROMA_COLLECTION,
    )


def load_chroma_store(persist_dir: Path = CHROMA_DIR) -> Chroma:
    """আগে থেকে persist করা Chroma collection load করে।"""
    embeddings = get_embedding_model()
    return Chroma(
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
        collection_name=CHROMA_COLLECTION,
    )


def get_vector_store(store_type: str = "faiss", rebuild: bool = False) -> VectorStore:
    """
    Vector store পাওয়ার single entry point — app.py এটাই কল করে।

    - store_type: "faiss" অথবা "chroma"
    - rebuild=True দিলে data/ থেকে নতুন করে ingest করে; নাহলে existing
      index/collection load করে (না পেলে automatically build করে)
    """
    if store_type == "faiss":
        index_file = FAISS_INDEX_DIR / "index.faiss"
        if not rebuild and index_file.exists():
            return load_faiss_store()
        chunks = load_and_split()
        return build_faiss_store(chunks)

    if store_type == "chroma":
        sqlite_file = CHROMA_DIR / "chroma.sqlite3"
        if not rebuild and sqlite_file.exists():
            return load_chroma_store()
        chunks = load_and_split()
        return build_chroma_store(chunks)

    raise ValueError(f"Unknown store_type: {store_type!r} — 'faiss' বা 'chroma' দাও")
