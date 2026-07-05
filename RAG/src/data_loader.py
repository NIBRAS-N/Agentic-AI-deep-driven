"""
RAG Data Loader — Documents Load ও Split করা
=============================================

## এই Module কী করে?

RAG pipeline-এর প্রথম দুই ধাপ একত্রে করে:

    RAG/data/  (pdf + csv + text_files)
        ↓  load_all_documents()
    Document objects (raw, unsplit)
        ↓  split_documents()
    Chunked Document objects   ← vectorestore.py এই chunks embed করে FAISS/Chroma-তে রাখে

## Data Directory Structure

    RAG/data/
    ├── pdf/         → PyPDFLoader  (প্রতি page = ১টা Document)
    ├── text_files/  → DirectoryLoader + TextLoader
    └── csv/         → CSVLoader   (প্রতি row = ১টা Document)
"""

from pathlib import Path

from langchain_community.document_loaders import (
    CSVLoader,
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ─────────────────────────────────────────────────────────────────
# Data directory paths — src/ থেকে এক level উপরে RAG/data/
# (vectorestore.py এখান থেকেই DATA_DIR import করে FAISS/Chroma path বানায়)
# ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdf"
TEXT_DIR = DATA_DIR / "text_files"
CSV_DIR = DATA_DIR / "csv"


def load_text_documents(text_dir: Path = TEXT_DIR) -> list[Document]:
    """text_files/ ফোল্ডারের সব .txt file DirectoryLoader দিয়ে load করে।"""
    loader = DirectoryLoader(
        path=str(text_dir),
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=False,
    )
    return loader.load()


def load_pdf_documents(pdf_dir: Path = PDF_DIR) -> list[Document]:
    """pdf/ ফোল্ডারের সব .pdf file PyPDFLoader দিয়ে load করে।"""
    loader = DirectoryLoader(
        path=str(pdf_dir),
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=False,
    )
    return loader.load()


def load_csv_documents(csv_dir: Path = CSV_DIR) -> list[Document]:
    """csv/ ফোল্ডারের সব .csv file CSVLoader দিয়ে load করে।"""
    docs: list[Document] = []
    for csv_path in sorted(csv_dir.glob("*.csv")):
        docs.extend(CSVLoader(file_path=str(csv_path)).load())
    return docs


def load_all_documents() -> list[Document]:
    """RAG/data/-এর pdf + text_files + csv — তিন source থেকে সব Document একসাথে load করে।"""
    return load_text_documents() + load_pdf_documents() + load_csv_documents()


def split_documents(
    documents: list[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 80,
) -> list[Document]:
    """RecursiveCharacterTextSplitter দিয়ে documents-কে ছোট chunk-এ ভাগ করে (metadata copy থাকে)।"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(documents)


def load_and_split(chunk_size: int = 500, chunk_overlap: int = 80) -> list[Document]:
    """Full ingestion step: load_all_documents() + split_documents() — vectorestore.py এটাই কল করে।"""
    documents = load_all_documents()
    return split_documents(documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
