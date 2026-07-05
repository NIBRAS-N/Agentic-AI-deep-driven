"""
RAG Search — Retriever + Anthropic দিয়ে Answer Generation
===========================================================

## Full Query Flow

    question
        ↓
    retriever (vector_store.as_retriever)   ← vectorestore.py
        ↓  top-k relevant chunks
    format_docs()                           → context string বানায়
        ↓
    RAG_PROMPT | ChatAnthropic | StrOutputParser   ← LCEL chain
        ↓
    answer (+ source documents, RunnableParallel দিয়ে একসাথে)

app.py এই module থেকে build_rag_chain() নিয়ে interactive query loop চালায়।
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.vectorstores import VectorStore

load_dotenv()

LLM_MODEL_NAME = "claude-haiku-4-5-20251001"

RAG_PROMPT = ChatPromptTemplate.from_template(
    """তুমি একজন সহায়ক AI assistant। নিচের context ব্যবহার করে প্রশ্নের উত্তর দাও।
যদি context-এ উত্তর না থাকে, তাহলে বলো "আমি এই বিষয়ে context পাইনি।"
উত্তর বাংলায় সংক্ষেপে দাও।

Context:
{context}

Question: {question}

Answer:"""
)


def get_llm() -> ChatAnthropic:
    """ChatAnthropic LLM তৈরি করে — generation-এর জন্য (embedding.py আলাদাভাবে vector conversion করে)।"""
    return ChatAnthropic(
        model=LLM_MODEL_NAME,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )


def get_retriever(vector_store: VectorStore, k: int = 3, search_type: str = "similarity"):
    """vector_store থেকে LangChain Runnable retriever বানায় (search_type: "similarity" বা "mmr")।"""
    return vector_store.as_retriever(search_type=search_type, search_kwargs={"k": k})


def format_docs(docs: list[Document]) -> str:
    """Retrieved chunks-কে source নাম সহ একটা single context string-এ format করে।"""
    return "\n\n".join(
        f"[Source: {Path(d.metadata.get('source', '?')).name}]\n{d.page_content}"
        for d in docs
    )


def build_rag_chain(vector_store: VectorStore, k: int = 3) -> RunnableParallel:
    """
    Full LCEL retrieval chain — answer + source documents দুটোই একসাথে রিটার্ন করে।

    Output shape: {"answer": str, "context": list[Document]}
    """
    retriever = get_retriever(vector_store, k=k)
    llm = get_llm()

    answer_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )

    return RunnableParallel(answer=answer_chain, context=retriever)


def answer_question(question: str, rag_chain: RunnableParallel) -> tuple[str, list[Document]]:
    """rag_chain invoke করে (answer, source_documents) tuple হিসেবে রিটার্ন করে।"""
    result = rag_chain.invoke(question)
    return result["answer"], result["context"]
