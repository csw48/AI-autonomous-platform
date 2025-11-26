# Backend - AI Autonomous Platform

FastAPI backend for document processing, LLM chat, and vector search.

## Features

- Document upload & processing (PDF, DOCX, TXT, images)
- Text chunking & embeddings generation
- Vector storage with PostgreSQL + pgvector
- OpenAI GPT-4 chat endpoint
- Async database operations

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Testing

```bash
pytest -v --cov=app
```

Coverage: 62% (50 tests)
