"""
RAG Application — Interactive CLI Entry Point
==============================================

## Full Pipeline (এক command চালিয়ে সব ধাপ)

    RAG/data/ (pdf + csv + text_files)
        ↓  src.data_loader
    Document chunks
        ↓  src.embedding
    Vectors
        ↓  src.vectorestore   → data/faiss_index/ (save/load)
    FAISS Vector Store
        ↓  src.search          → ChatAnthropic (claude-haiku-4-5)
    Interactive Q&A  ← এই file

## চালানোর নিয়ম

    uv run python RAG/app.py

প্রথমবার চালালে data/ থেকে ingest করে FAISS index বানাবে ও save করবে।
পরের বার চালালে existing index সরাসরি load করবে (দ্রুত startup)।
প্রশ্ন করতে থাকো, "exit" লিখে বের হও।
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# src/ কে package হিসেবে import করার জন্য এই file-এর নিজের directory sys.path-এ যোগ করা
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import answer_question, build_rag_chain, get_vector_store  # noqa: E402

load_dotenv()


def main() -> None:
    print("=" * 60)
    print("RAG Pipeline — FAISS + Anthropic (Claude)")
    print("=" * 60)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY পাওয়া যায়নি — .env ফাইল চেক করো।")
        return

    print("\nVector store প্রস্তুত হচ্ছে... (প্রথমবার হলে data/ থেকে ingest হবে)")
    vector_store = get_vector_store(store_type="faiss")
    print("Vector store প্রস্তুত।\n")

    rag_chain = build_rag_chain(vector_store, k=3)
    print("RAG chain প্রস্তুত। প্রশ্ন করো ('exit' লিখে বের হও)।\n")

    while True:
        question = input("প্রশ্ন: ").strip()
        if question.lower() in {"exit", "quit"}:
            print("বিদায়!")
            break
        if not question:
            continue

        answer, sources = answer_question(question, rag_chain)

        print(f"\nউত্তর: {answer}")
        src_names = sorted({Path(d.metadata.get("source", "?")).name for d in sources})
        print(f"Sources: {', '.join(src_names)}\n")


if __name__ == "__main__":
    main()
