# AI Autonomous Knowledge & Workflow Platform

Professional end-to-end AI system combining RAG (Retrieval-Augmented Generation), intelligent agents, and workflow automation.

## Features

- **RAG System**: Document processing (PDF, DOCX, images with OCR) with vector search
- **AI Agents**: Multi-step task execution with tool calling capabilities
- **Vector Database**: PostgreSQL + pgvector / ChromaDB integration
- **MCP Integration**: Tool protocol layer for extensible integrations
- **Guardrails**: Validation, safety, and constraint enforcement
- **Voice I/O**: Speech-to-text (Whisper) and text-to-speech support
- **Web UI**: Chat interface with document management and history
- **CI/CD**: Automated testing and deployment with GitHub Actions

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- PostgreSQL + pgvector
- SQLAlchemy
- OpenAI API (LLM & Embeddings)
- ChromaDB (optional)

### Frontend
- Next.js
- TypeScript
- React

### Infrastructure
- Docker & docker-compose
- GitHub Actions
- Notion API integration

## Project Structure

```
ai-platform/
├── backend/           # FastAPI backend application
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── core/     # Core modules (LLM, RAG, agents)
│   │   ├── db/       # Database models and connections
│   │   └── services/ # Business logic services
│   └── tests/        # Backend tests
├── frontend/         # Next.js frontend (optional)
├── infra/           # Infrastructure configs
│   ├── docker-compose.yml
│   └── github-actions/
└── scripts/         # Utility scripts
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & docker-compose (optional)
- PostgreSQL (or use Docker)
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/csw48/AI-autonomous-platform.git
cd AI-autonomous-platform
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. Install backend dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Run tests:
```bash
pytest
```

5. Start the backend:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

## Development

### Running Tests

```bash
cd backend
pytest -v --cov=app
```

### Linting

```bash
ruff check app/ tests/
```

### Docker

```bash
docker build -t ai-platform-backend ./backend
docker run -p 8000:8000 ai-platform-backend
```

## API Endpoints

### Available Now
- `GET /` - Root endpoint
- `GET /api/v1/health` - Health check
- `POST /api/v1/chat` - Simple chat with LLM

### Coming Soon
- `POST /api/v1/chat/rag` - RAG-enhanced chat
- `POST /api/v1/documents/upload` - Upload documents
- `POST /api/v1/agents/execute` - Execute agent tasks

## Configuration

See `.env.example` for all configuration options.

Key environment variables:
- `OPENAI_API_KEY` - OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string
- `NOTION_API_KEY` - Notion integration (optional)
- `NOTION_DATABASE_ID` - Notion database ID (optional)

## Contributing

This project follows an iterative development approach with:
1. Small, focused milestones
2. Test-driven development
3. Continuous integration
4. Documentation updates with each milestone

## License

MIT License

## Version

Current version: 0.1.0

## Status

🚧 **In Development**
- ✅ Milestone 1: Repository initialization + backend skeleton
- ✅ Milestone 2: LLM integration (simple chat)
- 🔄 Milestone 3: Database + vector DB setup (next)
