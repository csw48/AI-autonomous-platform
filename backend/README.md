# Backend - AI Autonomous Platform

FastAPI-based backend for the AI Autonomous Knowledge & Workflow Platform.

## Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── health.py       # Health check endpoint
│   ├── core/
│   │   ├── config.py          # Application configuration
│   │   ├── notion.py          # Notion API integration
│   │   ├── llm.py             # LLM wrapper (coming soon)
│   │   ├── embeddings.py      # Embeddings (coming soon)
│   │   ├── rag.py             # RAG core (coming soon)
│   │   ├── agents.py          # Agent system (coming soon)
│   │   ├── guardrails.py      # Validation & safety (coming soon)
│   │   ├── tools/             # Agent tools (coming soon)
│   │   └── mcpx/              # MCP protocol (coming soon)
│   ├── db/
│   │   ├── models.py          # Database models (coming soon)
│   │   └── session.py         # DB session management (coming soon)
│   ├── services/
│   │   ├── documents_service.py   # Document processing (coming soon)
│   │   ├── indexing_service.py    # Indexing (coming soon)
│   │   └── search_service.py      # Search service (coming soon)
│   └── main.py                # Application entry point
├── tests/
│   ├── conftest.py            # Pytest configuration
│   ├── test_health.py         # Health endpoint tests
│   ├── test_config.py         # Configuration tests
│   └── test_notion.py         # Notion integration tests
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Pytest configuration
└── Dockerfile                 # Docker image definition
```

## Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py -v
```

### Linting

```bash
# Check code quality
ruff check app/ tests/

# Auto-fix issues
ruff check app/ tests/ --fix
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

Configuration is managed through environment variables using `pydantic-settings`.

See `.env.example` in the root directory for all available options.

## Current Endpoints

### Health Check
```http
GET /api/v1/health

Response:
{
  "status": "ok",
  "version": "0.1.0",
  "app_name": "AI Autonomous Platform",
  "services": {
    "notion": true
  }
}
```

### Chat (LLM)
```http
POST /api/v1/chat

Request:
{
  "message": "Hello, how are you?",
  "system_prompt": "You are a helpful assistant",  // optional
  "temperature": 0.7,  // optional, default 0.7
  "max_tokens": 1000   // optional
}

Response:
{
  "answer": "I'm doing well, thank you for asking!",
  "tokens_used": 12
}
```

## Notion Integration

The backend includes Notion API integration for task tracking:

```python
from app.core.notion import notion

# Update task status
notion.update_task_status("Milestone 1", "Done")

# Log milestone completion
notion.log_milestone("Milestone 1", {"details": "..."})
```

Notion integration is automatically disabled if `NOTION_API_KEY` or `NOTION_DATABASE_ID` are not set.

## Testing

Tests are written using pytest and include:
- Unit tests for core modules
- Integration tests for API endpoints
- Mock-based tests for external services

Test coverage target: >80%

## Docker

```bash
# Build image
docker build -t ai-platform-backend .

# Run container
docker run -p 8000:8000 --env-file ../.env ai-platform-backend
```

## Completed Milestones

- [x] Milestone 1: Repository initialization + backend skeleton
- [x] Milestone 2: LLM integration (simple chat)

## Next Steps

- [ ] Database setup (Milestone 3)
- [ ] Document upload & indexing (Milestone 4)
- [ ] RAG implementation (Milestone 5)
- [ ] AI Agent system (Milestone 6)

## LLM Integration

The backend supports multiple LLM providers through an abstract interface:

```python
from app.core.llm import llm_manager

# Generate text
response = await llm_manager.generate(
    prompt="What is AI?",
    system_prompt="You are a helpful assistant",
    temperature=0.7
)

# Count tokens
tokens = llm_manager.count_tokens("Some text")
```

Currently supported providers:
- OpenAI (GPT-4, GPT-3.5-turbo)
