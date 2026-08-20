# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Mind-Mate (package name "PsycheNavigator") is a psychology-focused agentic RAG assistant. It retrieves passages from 6 psychology books (Feeling Good, Attached, The Body Keeps the Score, Games People Play, Thinking Fast and Slow, Nonviolent Communication) stored in a local ChromaDB vector store, and grounds every response in cited passages rather than the LLM's training data alone.

## Commands

### Backend (`psyche_navigator/backend/`)
```bash
cd psyche_navigator/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add GROQ_API_KEY

python rag/ingest.py   # one-time: build the ChromaDB vector store from books/*.pdf
python start.py        # run the API on http://localhost:8000 (uvicorn, hot-reload)

python eval/run_eval.py   # score the pipeline with RAGAS against eval/golden_set.json
```
There is no unit-test suite or linter configured for the backend; `eval/run_eval.py` is the closest thing to a test — a RAGAS-based quality harness (see Evaluation below), not a pass/fail CI gate.

### Frontend (`psyche_navigator/frontend/`)
```bash
cd psyche_navigator/frontend
npm install
npm run dev       # http://localhost:5173
npm run build
npm run preview
```

## Architecture

### Agent pipeline (LangGraph)
The core is a LangGraph state graph (`backend/agent/graph.py`) built around a single `AgentState` TypedDict (`backend/agent/state.py`) that flows through nodes in `backend/agent/nodes/`:

```
guard → retriever → evaluator ─┬─(sufficient)→ psychologist → action_planner → follow_up → END
                                 └─(insufficient, <3 attempts)→ query_builder → retriever (loop)
                                 └─(insufficient, 3 attempts used)→ END (fallback message)
guard →(off-topic)→ END
```

- **guard**: rejects off-topic messages before any retrieval happens.
- **retriever**: embeds the current query and pulls top-8 chunks from ChromaDB.
- **evaluator**: LLM judges whether chunks contain specific, applicable psychological frameworks (not just topical overlap); decides SUFFICIENT/INSUFFICIENT.
- **query_builder**: rephrases the search query on retry (max 3 total retrieval attempts).
- **psychologist**: generates the cited response.
- **action_planner**: produces a structured action plan (Pydantic schema).
- **follow_up**: generates one closing question.

Every node has the same signature — `run(state) -> state`, mutating the `AgentState` dict in place and returning it — and logs progress through `backend/agent/logger.py`'s colored helpers (`log_node_start`, `log_input`, `log_llm`, `log_ok`, `log_warn`, `log_info`, `log_route`). Most nodes build a `ChatPromptTemplate` and call `(prompt | llm).invoke({...})` with an explicit dict of fields, not the raw state (see `guard.py`, `evaluator.py`, `query_builder.py`, `action_planner.py`). Two nodes deviate: `retriever.py` calls no LLM at all (pure vector search), and `follow_up.py` skips `ChatPromptTemplate`, instead hand-building a `SystemMessage`/`HumanMessage`/`AIMessage` list from conversation history and calling `llm.invoke(conversation)` directly. Follow whichever shape fits when adding or modifying nodes rather than introducing a new logging or prompting style.

### LLM access
All LLM calls go through `backend/llm_factory.py`'s `make_llm(temperature, model)`, which wraps `ChatGroq` (requires `GROQ_API_KEY`). `model` defaults to `llama-3.3-70b-versatile` for every app node; the only caller that overrides it is the RAGAS eval judge, which passes `llama-3.1-8b-instant` (a separate Groq rate-limit bucket). Don't instantiate `ChatGroq` directly elsewhere — use this factory so temperature conventions stay consistent (0 for guard/evaluator's deterministic judgments, 0.3–0.5 for generative nodes).

### RAG / vector store
- `backend/rag/ingest.py` is a standalone, one-time script (not imported by the API) that loads the 6 PDFs from `backend/books/`, chunks them (800 chars, 120 overlap via `RecursiveCharacterTextSplitter`), filters junk/index pages (`_is_content`), embeds with local `sentence-transformers/all-MiniLM-L6-v2`, and writes to the `chroma_db/` collection named `"langchain"` (cosine similarity). Re-run it whenever the book set or chunking strategy changes.
- `backend/rag/retriever.py` builds the query-time retriever (`k=8`) against the same persisted `chroma_db/` directory and embedding model.
- The book title list is centralized in `backend/books.py` (`BOOK_TITLES`) — the source of truth for which books are ingested.

### Evaluation (`backend/eval/`)
`eval/run_eval.py` scores retrieval + generation quality with RAGAS. It does **not** run the full LangGraph pipeline — it invokes just `guard.run → retriever.run → psychologist.run` (skipping the evaluator/query_builder retry loop and action_planner/follow_up) on each question in `golden_set.json`, building the same initial `AgentState` shape that `api/main.py` builds for real traffic. Three metrics: **answer_correctness** (response vs. `ground_truth`), **faithfulness** (response grounded in retrieved chunks), **context_precision** (are the answer-bearing chunks ranked near the top of the k=8 — a proxy for whether k could be lowered). The judge LLM is `llama-3.1-8b-instant` via `make_llm`, embeddings are reused from `rag.retriever._embeddings`. Results merge per-question into `eval/results.csv` (existing rows updated, not overwritten). Keep `golden_set.json` questions answerable from the ingested books, since off-topic ones get dropped by the guard.

### API layer
`backend/api/main.py` exposes:
- `POST /chat` — runs the LangGraph pipeline and streams one SSE event per completed node (`graph.astream()`), plus a final `{"node": "__end__"}` event. Only JSON-serializable state fields are forwarded to the client.
- `GET /db/stats`, `GET /db/search?query=...`, `GET /db/browse?book=...` — debug endpoints for inspecting ChromaDB contents directly.
- `GET /health`, `GET /` — health/info.

CORS is currently allowlisted to `localhost:3000/3001/5173` in `main.py` — update this list if the frontend origin changes.

### Frontend
React + Vite app in `psyche_navigator/frontend/src/`. `App.jsx` is the root; `components/` holds `ChatWindow.jsx` (chat UI), `MessageBubble.jsx`, `SourceChip.jsx` (citation display), `AgentPipeline.jsx` (visualizes which graph node is currently running, driven by the SSE node events), `BookSidebar.jsx`, `HomePage.jsx`, `TechStackVisualizer.jsx`. Styling via Tailwind (`tailwind.config.js`, `postcss.config.js`).

## Environment variables
`GROQ_API_KEY` (in `backend/.env`) is the only required variable — get one free at console.groq.com.
