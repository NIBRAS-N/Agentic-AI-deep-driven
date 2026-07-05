"""
RAG Embedding Model — Text-কে Vector-এ রূপান্তর
================================================

## কেন HuggingFaceEmbeddings, Anthropic নয়?

Anthropic API text **generation** দেয় — embedding endpoint দেয় না।
তাই vector conversion-এর জন্য local sentence-transformers model ব্যবহার করা হয়
(free, offline, ইন্টারনেট ছাড়াই চলে একবার download হয়ে গেলে)।
Anthropic শুধু `search.py`-তে answer generation-এর জন্য ব্যবহৃত হয়।

    text  →  HuggingFaceEmbeddings  →  384-dim vector  →  FAISS/Chroma (vectorestore.py)
"""

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    """Embedding model একবারই load করে cache করে রাখে — বারবার download/reload আটকায়।"""
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
