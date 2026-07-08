# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A LangChain agentic AI course codebase (Krish Naik). Demonstrates LangChain integrations with multiple LLM providers using Jupyter notebooks as the primary learning medium.

## Package Manager

This project uses **uv**. Do not use `pip` directly.

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package>

# Run a script
uv run python main.py

# Launch Jupyter for notebooks
uv run jupyter notebook
```

## Environment Setup

Copy API keys into a `.env` file at the project root. Required keys (based on providers used):

```
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
GROK_API_KEY=...
GOOGLE_API_KEY=...
```

Notebooks and scripts load these via `python-dotenv` (`load_dotenv()`).

**Important:** `.env` is not listed in `.gitignore` — add it before committing.

## Python Version

Python 3.13 (enforced via `.python-version`).

## Architecture

- **Notebooks** (`.ipynb`) are the main teaching artifacts — each covers a specific LangChain concept or provider integration.
- **`main.py`** is a scaffold entry point, not a runnable application.
- **`mcp/`** contains MCP (Model Context Protocol) server and client scripts — Python files, not notebooks.
- **LangChain provider packages** installed: `langchain-anthropic`, `langchain-openai`, `langchain-groq`, `langchain-google-genai`, `langchain-community`. Switch providers by swapping the chat model class and its corresponding API key.
- All LLM calls follow the standard LangChain interface: build a chain with `|` (LCEL), invoke with `.invoke()` or `.stream()`.

## Notebook Index

| # | File | Topic |
|---|---|---|
| 1 | `langchain/1-langchain-intro.ipynb` | LangChain agents intro — custom `get_weather` tool, `create_agent`, invoke |
| 2 | `langchain/2-modelintegration.ipynb` | Multi-provider LLM integration (Anthropic, OpenAI, xAI Grok, Google Gemini) + `.stream()` and `.batch()` |
| 3 | `langchain/3-tools-execution-loop.ipynb` | Manual tool-execution loop — `bind_tools`, `HumanMessage`, `ToolMessage`, parallel tool calls, unknown city handling |
| 4 | `langchain/4-Messages.ipynb` | LangChain message types — Text Prompt, SystemMessage, HumanMessage, AIMessage, ToolMessage with weather DB examples |
| 5 | `langchain/5-structured-output.ipynb` | Structured output — Pydantic (basic + nested), TypedDict, DataClass with `with_structured_output` and weather DB |
| 6 | `langchain/6-middleware.ipynb` | Middleware — `SummarizationMiddleware` (token/fraction/OR-logic triggers), `HumanInTheLoopMiddleware` (approve/reject flow) |
| 7 | `langgraph/1-basic-chatbot/1-basicChatbot.ipynb` | LangGraph basics — State/Node/Edge (Bangla), `StateGraph`, `ToolNode`, `tools_condition`, `MemorySaver`, graph visualization, weather tool, streaming |
| 8 | `langgraph/1-basic-chatbot/2-human-in-the-loop.ipynb` | HITL — `interrupt()`, `Command(resume=...)`, approve/reject/modify flows, how human decision changes tool call and LLM answer |
| 9 | `RAG/notebook/document.ipynb` | Document structure (`page_content`, `metadata`), Document Loaders — `PyPDFLoader`, `CSVLoader`, `WebBaseLoader`, `DirectoryLoader` |
| 10 | `RAG/notebook/text-splitting.ipynb` | RAG data ingestion pipeline — `RecursiveCharacterTextSplitter`, `HuggingFaceEmbeddings` (sentence-transformers), FAISS, ChromaDB, full pipeline demo |
| 11 | `vectorless-rag/vectorLess-RAG.ipynb` | Vectorless RAG (PageIndex concept) — no chunking/embeddings/vector DB; builds a hierarchical tree index from a PDF with `ChatAnthropic` + `with_structured_output`, then does LLM tree search, cited answer generation, and expert-guided retrieval |

When adding a new notebook, append a row to this table.

## MCP Scripts

Python scripts (not notebooks) under `mcp/`. Run with `uv run python <file>`.

| File | Transport | Role | Notes |
|---|---|---|---|
| `mcp/mathServer.py` | stdio | MCP server — `add`, `subtract`, `multiply`, `divide` tools | Client spawns it automatically as a subprocess |
| `mcp/weather.py` | streamable-http | MCP server — `get_weather` tool | Must be started separately before running client: `uv run python mcp/weather.py` |
| `mcp/client.py` | — | Multi-server MCP client using `MultiServerMCPClient` + LangGraph + Anthropic | Start `weather.py` first, then run this |

**Packages added for MCP:** `mcp`, `langchain-mcp-adapters`, `uvicorn`.

**Packages added for RAG:** `pypdf`, `pymupdf`, `fpdf2` (PDF generation for sample data), `beautifulsoup4` (WebBaseLoader), `sentence-transformers`, `faiss-cpu`, `chromadb`, `langchain-huggingface`, `langchain-text-splitters`.

## RAG Pipeline (`RAG/src/` + `RAG/app.py`)

A modular, linked implementation of the RAG pipeline taught in the notebooks. Each module has one responsibility and imports from the previous stage; `app.py` wires them into an interactive CLI.

| File | Role | Depends on |
|---|---|---|
| `RAG/src/data_loader.py` | Loads `RAG/data/{pdf,csv,text_files}` via `PyPDFLoader`/`CSVLoader`/`DirectoryLoader`+`TextLoader`, then splits with `RecursiveCharacterTextSplitter`. Defines `DATA_DIR`. | — |
| `RAG/src/embedding.py` | `get_embedding_model()` — cached `HuggingFaceEmbeddings` (`sentence-transformers/all-MiniLM-L6-v2`). Anthropic has no embeddings endpoint, so embeddings stay local/free. | — |
| `RAG/src/vectorestore.py` | Builds/saves/loads FAISS (`data/faiss_index/`) and Chroma (`data/chroma_db/`). `get_vector_store(store_type, rebuild)` is the smart entry point: loads an existing index if present, else ingests from `data/`. | `data_loader`, `embedding` |
| `RAG/src/search.py` | `build_rag_chain()` — LCEL retrieval chain (`RunnableParallel` of answer + source docs) using `ChatAnthropic` (`claude-haiku-4-5-20251001`) for generation. | `vectorestore` (via the `VectorStore` it's given) |
| `RAG/src/__init__.py` | Re-exports the public API of all four modules for `from src import ...`. | all of the above |
| `RAG/app.py` | Interactive CLI entry point: loads/builds the FAISS store, builds the RAG chain, loops on user questions. Run with `uv run python RAG/app.py`. | `RAG/src` package |

Explanations inside these files follow the same Bangla-annotated docstring/comment style used in `mcp/*.py`.
