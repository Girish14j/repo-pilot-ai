# RepoPilot AI

An AI-powered GitHub repository analyzer that runs a multi-agent pipeline to review code architecture, security, documentation, and performance — then generates career content like resume bullets, interview questions, and LinkedIn posts. Includes a live streaming UI and a context-aware chat assistant.

---

## Features

- **Multi-agent pipeline** — 8 specialized LangGraph agents run in parallel (architecture, documentation, security, performance, interview, resume, refactoring, final report)
- **Live streaming** — SSE endpoint streams each agent's result to the frontend as it completes
- **RAG-enhanced analysis** — Architecture, security, and documentation agents retrieve knowledge from a local ChromaDB vector store (SOLID principles, OWASP Top 10, README best practices)
- **Career content generation** — ATS-optimized resume bullets, LinkedIn posts, interview questions, and system design questions tailored to the repo
- **Context-aware chat** — After analysis, chat with an AI assistant that has full knowledge of the analyzed repository using LangGraph memory
- **Free tier only** — Uses OpenRouter free models with a 9-model fallback loop to handle rate limits

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Python 3.11 |
| AI Orchestration | LangGraph, LangChain |
| LLM Provider | OpenRouter (free tier) |
| Vector Store | ChromaDB (local, persisted to disk) |
| Embeddings | OpenAI-compatible via OpenRouter |

---

## Project Structure

```
repo-pilot-ai/
├── backend/
│   ├── app/
│   │   ├── graph/
│   │   │   ├── agents/          # 8 individual agent files
│   │   │   ├── graph.py         # Parallel pipeline with ThreadPoolExecutor
│   │   │   ├── chat_graph.py    # Conversational graph with MemorySaver
│   │   │   ├── state.py         # RepoState TypedDict
│   │   │   └── chat_state.py    # ChatState TypedDict
│   │   ├── models/              # Pydantic request/response models
│   │   ├── rag/
│   │   │   ├── embeddings.py    # ChromaDB vector store setup
│   │   │   ├── retriever.py     # RAG retrieval function
│   │   │   └── knowledge_base.py # Knowledge ingestion
│   │   ├── routers/
│   │   │   └── github.py        # All API endpoints
│   │   ├── services/            # GitHub, AI, and assistant services
│   │   └── main.py
│   ├── chroma_db/               # Persisted vector store (auto-created)
│   ├── .env.example
│   └── requirements.txt
└── frontend/
    ├── app/
    │   ├── page.tsx             # Main page with streaming UI
    │   └── globals.css          # Dark theme + animations
    ├── components/
    │   ├── chat/                # ChatWindow, ChatMessage, ChatInput
    │   ├── report/              # ReportTabs, AnalysisTab, SecurityTab, CareerTab
    │   └── ui/                  # shadcn/ui primitives
    └── lib/
        ├── api.ts               # streamGraphAnalysis SSE consumer
        └── types.ts             # FullReport TypeScript types
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A free [OpenRouter](https://openrouter.ai) account
- A [GitHub Personal Access Token](https://github.com/settings/tokens) (read-only, public repos)

### 1. Clone the repo

```bash
git clone https://github.com/your-username/repo-pilot-ai.git
cd repo-pilot-ai
```

### 2. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env`:

```env
GITHUB_TOKEN=your_github_pat_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

```bash
# Start the backend
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 3. Frontend setup

```bash
cd frontend

npm install
npm run dev
```

Frontend runs at `http://localhost:3000`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/github/graph-stream` | SSE stream — yields agent results as they complete |
| `POST` | `/api/github/graph-analyze` | Batch — runs full pipeline, returns final report |
| `POST` | `/api/github/chat/start` | Initialize chat session with repo context |
| `POST` | `/api/github/chat/message` | Send a message, get AI response |
| `POST` | `/api/github/review` | Legacy single-chain analysis |
| `POST` | `/api/github/assistant` | Legacy career content generation |
| `GET` | `/health` | Health check |

All `POST` endpoints accept `{ "url": "https://github.com/owner/repo" }`.

---

## Agent Pipeline

```
Step 1 (sequential):   repository_agent        — fetches GitHub data
                              │
Step 2 (parallel):    ┌──────┴──────┐
               architecture  documentation  security  performance
                              │
Step 3 (parallel):    ┌──────┴──────┐
               interview_agent  resume_agent  [refactoring_agent if arch < 7]
                              │
Step 4 (sequential):   final_report_agent      — assembles everything
```

Each agent has a 9-model fallback loop. If a model returns a rate limit, connection error, or status error, the next model is tried automatically.

### Free models used (in fallback order)

1. `meta-llama/llama-3.3-70b-instruct:free`
2. `nousresearch/hermes-3-llama-3.1-405b:free`
3. `nvidia/nemotron-3-ultra-550b-a55b:free`
4. `nvidia/nemotron-3-super-120b-a12b:free`
5. `openai/gpt-oss-120b:free`
6. `openai/gpt-oss-20b:free`
7. `qwen/qwen3-coder:free`
8. `google/gemma-4-31b-it:free`
9. `meta-llama/llama-3.2-3b-instruct:free`

---

## RAG Knowledge Base

The vector store is pre-populated with:

- **SOLID principles** — used by architecture and refactoring agents
- **Clean Architecture patterns** — used by architecture agent
- **OWASP Top 10** — used by security agent
- **README best practices** — used by documentation agent

ChromaDB persists to `backend/chroma_db/` on first run. Subsequent runs load from disk.

---

## Environment Variables

| Variable | Description |
|---|---|
| `GITHUB_TOKEN` | GitHub PAT for API access (avoids 60 req/hr unauthenticated limit) |
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM access |

---

## Known Limitations

- **Rate limits** — OpenRouter free models share a rate limit (~20 req/min). The 9-model fallback handles this but analysis can take 2–5 minutes for large repos.
- **Analysis time** — Parallel execution reduces time ~3×, but each LLM call still takes 10–30s.
- **Context window** — File trees are truncated to 150 files and READMEs to 3000 characters to stay within model limits.
- **Chat memory** — Chat sessions are stored in-memory (MemorySaver). Sessions are lost on server restart.

---

## License

MIT
