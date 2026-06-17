# Mind-Mate

A psychology-focused AI assistant that answers questions about emotions, relationships, and mental wellbeing using evidence-based books — not generic advice.

Instead of relying on the LLM's training data, Mind-Mate retrieves real passages from 6 well-known psychology books and grounds every response in them.

---

## What it does

You describe a situation — a difficult conversation, a relationship pattern, anxiety at work — and Mind-Mate:

1. Checks if the question is psychology-related
2. Searches a local vector database of 6 psychology books for relevant passages
3. Evaluates whether the retrieved passages are actually useful, and retries with a better query if not
4. Generates a warm, cited response from a psychologist persona
5. Produces a concrete action plan with specific steps
6. Asks a follow-up question to go deeper

Every claim in the response is traceable to a specific book and page number.

---

## Knowledge base

The assistant draws from these 6 books:

| Book | Core concepts |
|---|---|
| **Feeling Good** — David D. Burns | CBT, cognitive distortions, thought records |
| **Attached** — Amir Levine & Rachel Heller | Attachment styles: secure, anxious, avoidant |
| **The Body Keeps the Score** — Bessel van der Kolk | Trauma, somatic responses |
| **Games People Play** — Eric Berne | Transactional analysis, ego states |
| **Thinking, Fast and Slow** — Daniel Kahneman | Cognitive biases, System 1 vs System 2 |
| **Nonviolent Communication** — Marshall Rosenberg | NVC 4-step framework |

---

## Architecture

```
User message
     │
     ▼
 GUARD          ── off-topic? → reject with message
     │
     ▼
 RETRIEVER      ── embeds query → cosine search in ChromaDB → top-8 chunks
     │
     ▼
 EVALUATOR      ── are chunks specific enough?
     │                    │
     │ yes                │ no (up to 3 retries)
     │                    ▼
     │           QUERY_BUILDER ── rephrases query → back to RETRIEVER
     │
     ▼
 PSYCHOLOGIST   ── generates cited response using retrieved chunks
     │
     ▼
 ACTION_PLANNER ── structured JSON action plan (Pydantic schema)
     │
     ▼
 FOLLOW_UP      ── one closing question based on conversation history
     │
     ▼
  Response streamed to frontend via SSE
```

**Stack:**
- **LLM** — Llama 3.3 70B via [Groq](https://groq.com) (free tier available)
- **Orchestration** — LangGraph (stateful agent graph)
- **Embeddings** — `sentence-transformers/all-MiniLM-L6-v2` (local, no API)
- **Vector DB** — ChromaDB (local, cosine similarity)
- **Backend** — FastAPI + Server-Sent Events (streaming)
- **Frontend** — React + Vite

---

## Project structure

```
psyche_navigator/
├── backend/
│   ├── start.py                  # entry point
│   ├── llm_factory.py            # Groq LLM setup
│   ├── api/
│   │   └── main.py               # FastAPI routes + SSE streaming
│   ├── rag/
│   │   ├── ingest.py             # one-time script: PDF → ChromaDB
│   │   └── retriever.py          # query-time vector search
│   └── agent/
│       ├── state.py              # shared AgentState TypedDict
│       ├── graph.py              # LangGraph graph definition
│       └── nodes/
│           ├── guard.py
│           ├── retriever.py
│           ├── evaluator.py
│           ├── query_builder.py
│           ├── psychologist.py
│           ├── action_planner.py
│           └── follow_up.py
└── frontend/
    └── src/
        ├── App.jsx
        └── components/
```

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- A free [Groq API key](https://console.groq.com)
- The 6 PDF books placed in `psyche_navigator/backend/books/`

### 1. Clone the repo

```bash
git clone https://github.com/youssefcapgeminii/Mind-Mate.git
cd Mind-Mate
```

### 2. Backend

```bash
cd psyche_navigator/backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:

```bash
cp .env.example .env
# then open .env and paste your Groq API key
```

Build the vector database (run once):

```bash
python rag/ingest.py
```

Start the server:

```bash
python start.py
```

Backend runs at `http://localhost:8000`.

### 3. Frontend

```bash
cd psyche_navigator/frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Main chat endpoint, streams SSE events per node |
| `GET` | `/db/search?q=<query>&k=8` | Debug: query ChromaDB directly and see scores |

### Chat request format

```json
{
  "messages": [
    { "role": "user", "content": "I feel anxious before every meeting with my manager." }
  ]
}
```

Each SSE event:

```json
{ "node": "retriever", "output": { "retrieval_attempts": 1, "retrieved_chunks": [...] } }
```

Final event: `{ "node": "__end__" }`

---

## How the retrieval works

During ingestion (`ingest.py`), every book is split into 800-character chunks with 120-character overlap, then embedded into 384-dimensional vectors using `all-MiniLM-L6-v2`. Vectors are stored in ChromaDB with cosine similarity as the distance metric.

At query time, the user's message is embedded with the same model and the 8 nearest vectors are returned. The EVALUATOR node then judges whether those chunks actually contain named frameworks relevant to the user's situation — if not, QUERY_BUILDER rephrases the search and tries again (up to 3 attempts).

---

## Environment variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key — get one free at console.groq.com |
