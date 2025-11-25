# AI Autonomous Knowledge & Workflow Platform – Project Spec

> Tento dokument je zadanie pre AI developera (napr. OpenAI Codex / DevTools agenta).
> Cieľ: Vybudovať profesionálny end-to-end AI systém (backend + infra + CI/CD + testy + dokumentácia), iteratívne, s priebežnými commitmi, GitHub integráciou a aktualizáciou Notion boardu po dokončení každého kroku.

---

## 0. Všeobecné pravidlá správania (pre AI developera)

1. **Iteratívny workflow:**
   - Pracuj v malých krokoch / milestone-och.
   - Pre každý krok:
     1. Naplánuj konkrétne zmeny (krátky plán).
     2. Implementuj zmeny.
     3. Spusť testy (unit/integration).
     4. Ak testy padnú, oprav a opakuj testy.
     5. Keď testy prejdú:
        - aktualizuj dokumentáciu (ak treba),
        - sprav Git commit s rozumnou message,
        - pushni na GitHub,
        - aktualizuj Notion (odškrtnutie úlohy),
        - opýtaj sa: **„Mám pokračovať na ďalší krok?“**
   - Nikdy neskáč na ďalší milestone, kým:
     - testy neprejdú,
     - dokumentácia nie je v základnom stave,
     - commit + push nebol urobený,
     - Notion nebol aktualizovaný (ak je k dispozícii API KEY).

2. **Prostredie a nástroje:**
   - Jazyk backendu: **Python 3.11+**
   - Framework backendu: **FastAPI**
   - Frontend (ak sa robí): **Next.js + TypeScript + React**
   - Vektorová DB: **PostgreSQL + pgvector** (preferované) + prípadne **Chroma**.
   - Kontajnerizácia: **Docker** + `docker-compose`.
   - Testy:
     - Backend: `pytest` + `httpx` (test client), `pytest-asyncio`.
     - Frontend: `vitest` alebo `jest` (ak bude UI).
   - Manažment balíčkov: buď `poetry` alebo `pip` + `requirements.txt` + `venv` (vyber a buď konzistentný).
   - CI/CD: **GitHub Actions** (testy + build + lint ako minimum).

3. **Git workflow:**
   - Použi git priamo v repo.
   - Komituj často, ale logicky:
     - `feat: ...`, `fix: ...`, `chore: ...`, `docs: ...`, `test: ...`.
   - Po dokončení milestone:
     - spusti testy,
     - ak prejdú, commitni zmeny a pushni na zvolenú branch (`main` alebo `develop` – definuj na začiatku a drž sa toho).

4. **Notion integrácia:**
   - Použi Notion API (ak sú k dispozícii env premenné):
     - `NOTION_API_KEY`
     - `NOTION_DATABASE_ID` alebo `NOTION_TODO_PAGE_ID`.
   - Pre každý dokončený milestone:
     - nájdi zodpovedajúcu úlohu v Notion (napr. podľa Name/Title),
     - nastav property `Status` na `Done`/`Completed`.
   - Ak env premenné chýbajú, loguj info a Notion preskoč (nepadni na tom).

5. **Dokumentácia:**
   - Udržuj minimálne:
     - hlavný `README.md` (architektúra, spustenie, použitie),
     - `backend/README.md`,
     - `frontend/README.md` (ak existuje).
   - Aktualizuj dokumentáciu priebežne po každom väčšom kroku.

6. **Kvalita kódu:**
   - Dodržiavaj PEP8.
   - Použi typovanie (`typing`) v Pythone.
   - Pridaj unit testy pre kľúčové moduly (LLM wrapper, RAG core, agents core, API endpoints).
   - Použi linting (`ruff` alebo `flake8`) a spúšťaj ho v CI.

7. **Bezpečnosť:**
   - Žiadne hardcodované API kľúče.
   - Používaj `.env` + `dotenv` alebo `pydantic BaseSettings`.
   - Nikdy neloguj tajné údaje.
   - Ak je to rozumné, pridaj jednoduchý rate limiting.

---

## 1. Cieľ projektu

Vytvoriť **AI Autonomous Knowledge & Workflow Intelligence Platform**, ktorá:

- poskytuje RAG nad dokumentmi (PDF, DOCX, texty, obrázky cez OCR),
- má inteligentného AI agenta, ktorý:
  - dokáže riešiť multi-step úlohy,
  - dokáže volať nástroje (DB, súbory, web, email, workflow),
  - má pamäť,
- používa vektorovú DB (PostgreSQL + pgvector / Chroma),
- má MCP-like integračnú vrstvu (tool protokol / contract),
- má guardrails (validácia, bezpečnosť, JSON, obmedzenia),
- podporuje hlasový vstup a výstup (Whisper + TTS),
- môže mať web UI (chat + dokumenty + histórie),
- má CI/CD pipeline (GitHub Actions),
- má Docker infraštruktúru.

Projekt musí byť prezentovateľný na pohovoroch:
- čistá štruktúra repo,
- testy,
- dokumentácia,
- zrozumiteľná architektúra.

---

## 2. Tech Stack a štruktúra repozitára

### 2.1. Tech stack

- **Backend:**
  - Python 3.11+
  - FastAPI
  - httpx
  - pydantic
  - SQLAlchemy alebo async klient (napr. `asyncpg`) pre PostgreSQL
  - pgvector extension pre PostgreSQL
  - voliteľne ChromaDB
  - pytest, pytest-asyncio

- **AI / LLM:**
  - LLM API (min. OpenAI, abstrahuj aby šli pridať Claude/open-source)
  - Embeddings (OpenAI alebo SentenceTransformers)
  - Whisper (STT)
  - TTS (OpenAI/Azure/ElevenLabs – abstrahované)

- **Frontend (ak sa robí):**
  - Next.js + TypeScript + React

- **Infra:**
  - Docker, docker-compose
  - GitHub Actions
  - Notion API integrácia

### 2.2. Štruktúra repozitára

```bash
ai-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── chat.py
│   │   │   │   ├── documents.py
│   │   │   │   ├── agents.py
│   │   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── llm.py
│   │   │   ├── embeddings.py
│   │   │   ├── rag.py
│   │   │   ├── agents.py
│   │   │   ├── tools/
│   │   │   │   ├── base.py
│   │   │   │   ├── file_tool.py
│   │   │   │   ├── web_tool.py
│   │   │   │   ├── sql_tool.py
│   │   │   │   ├── email_tool.py
│   │   │   │   └── workflow_tool.py
│   │   │   ├── guardrails.py
│   │   │   ├── mcpx/
│   │   │   │   ├── server.py
│   │   │   │   └── protocol.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── models.py
│   │   │   ├── session.py
│   │   ├── services/
│   │   │   ├── documents_service.py
│   │   │   ├── indexing_service.py
│   │   │   ├── search_service.py
│   │   ├── main.py
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_health.py
│   │   ├── test_llm.py
│   │   ├── test_rag.py
│   │   ├── test_agents.py
│   │   └── ...
│   ├── pyproject.toml alebo requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── frontend/  # ak implementuješ UI
│   ├── package.json
│   ├── next.config.js
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.tsx
│   │   │   └── ...
│   │   ├── components/
│   │   └── ...
│   ├── Dockerfile
│   └── README.md
│
├── infra/
│   ├── docker-compose.yml
│   ├── github-actions/
│   │   ├── ci.yml
│   └── diagrams/
│       ├── architecture.md
│       └── ...
│
├── scripts/
│   ├── init_db.sql
│   ├── dev_setup.sh
│   └── ...
│
├── .env.example
├── .gitignore
├── README.md
└── PROJECT_PLAN.md
3. Funkčné moduly
3.1. Healthcheck API
GET /api/v1/health

Vráti:

status: "ok"

verziu aplikácie

stav DB / vector DB (ak implementované)

3.2. Základný Chat endpoint
POST /api/v1/chat

Request: { "message": "..." }

Response: { "answer": "..." }

Používa core.llm.generate_answer(prompt).

3.3. Upload dokumentov + indexovanie
POST /api/v1/documents/upload

multipart upload

meta (tagy, názov, typ, jazyk)

Funkcie:

extrakcia textu (PDF, DOCX),

OCR pre obrázky (Tesseract / Vision API),

chunkovanie textu,

embeddings,

uloženie do vector DB + metadáta do SQL.

3.4. RAG vyhľadávanie
POST /api/v1/chat/rag

Request: { "query": "otázka", "top_k": 5 }

Workflow:

retrieval (vector + keyword),

re-ranking (ak implementuješ),

prompt construction z query + contextu,

LLM odpoveď + referencie (IDs chunkov, dokumenty).

3.5. AI Agent
core/agents.py:

agent s tools (SQL, file, web, email, workflow),

ReAct / Planner-Executor štýl.

Endpoint: POST /api/v1/agents/execute

Request: { "goal": "...", "context": {...} }

Response: finálny výsledok + log krokov.

3.6. MCP-like vrstva
core/mcpx/protocol.py, core/mcpx/server.py

Jednoduchý protokol pre nástroje:

name, args, result.

Endpointy pre volanie nástrojov cez konzistentný contract.

3.7. Guardrails
core/guardrails.py:

JSON schema validation,

obmedzenia dĺžky odpovede,

základny obsahový filter,

fallback stratégie (retry, inštrukcie).

3.8. Hlasový vstup / výstup
POST /api/v1/voice/query

vstup: audio alebo URL

STT → text → chat/agent → odpoveď → TTS (audio).

core/voice.py – wrapper pre STT + TTS.

3.9. Frontend (ak sa robí)
Chat UI (simple / RAG / Agent mód)

Upload dokumentov

Zobrazenie histórie / workflow

4. Env premenné
Použi .env + .env.example:

OPENAI_API_KEY

LLM_PROVIDER

DATABASE_URL

VECTOR_DB_URL alebo info pre pgvector

NOTION_API_KEY

NOTION_DATABASE_ID alebo NOTION_TODO_PAGE_ID

LOG_LEVEL

5. CI/CD – GitHub Actions
Workflow (.github/workflows/ci.yml):

spúšťa sa na push a pull_request,

setup Python 3.11,

inštalácia závislostí,

lint (ruff alebo flake8),

testy (pytest),

voliteľne build Docker images.

6. Notion integrácia
Modul backend/app/core/notion.py:

funkcie:

update_task_status(task_name: str, status: str) -> None

log_milestone(milestone_name: str, details: dict) -> None

používa Notion API (/databases/{id}/query, /pages).

ak chýba NOTION_API_KEY alebo NOTION_DATABASE_ID, funkcie sú no-op + warning log.

Po každom dokončenom milestoni:

Aktualizuj zodpovedajúcu Notion úlohu na Done.

Potom sa pýtaj používateľa:

„Milestone X dokončený, Notion aktualizovaný. Mám pokračovať na ďalší krok?“

7. Milestones (poradie)
Inicializácia repozitára + backend skeleton.

LLM integrácia (simple chat) + testy + CI.

DB + vector DB + modely + docker-compose.

Upload dokumentov + indexovanie + testy.

RAG vyhľadávanie + testy.

AI Agent (tools + multi-step) + testy.

MCP-like integračná vrstva + testy.

Guardrails + testy.

Voice + multimodálne vstupy + testy.

Frontend (UI) + testy.

Finálny polish, dokumentácia, kontrola CI.

8. Interakčný protokol s človekom
Po každom milestoni AI developer:

Zhrnie, čo urobil.

Uvedie stav testov.

Potvrdí, že dokumentácia je aktualizovaná.

Potvrdí, že commit + push + Notion update sú hotové (ak API kľúče existujú).

Spýta sa:

„Mám pokračovať na ďalší krok? Ak áno, ktorý milestone mám riešiť ďalej, alebo mám pokračovať podľa plánu?“