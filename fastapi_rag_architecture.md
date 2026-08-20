# How FastAPI and RAG Connect in PsycheNavigator

## The two pieces

**FastAPI (`api/main.py`)** is the web server. It exposes HTTP endpoints and handles requests/responses. It does not know anything about psychology, books, or embeddings — its job is routing and streaming.

**RAG (`rag/ingest.py` + `rag/retriever.py`)** is the retrieval layer. It turns your 6 PDF books into searchable vectors stored in ChromaDB, and exposes a function to search them. It does not know anything about HTTP, requests, or the agent's reasoning steps.

They never talk to each other directly. FastAPI doesn't call RAG, and RAG doesn't call FastAPI. The connection happens through a third piece in the middle: **the LangGraph agent (`agent/`)**.

## The three-layer chain

```
FastAPI  →  Agent Graph  →  RAG
(HTTP)      (reasoning)     (search)
```

1. **FastAPI** receives the HTTP request and hands it to the agent graph.
2. **The agent graph** runs a sequence of nodes. One of those nodes (`agent/nodes/retriever.py`) is the only place that calls into RAG.
3. **RAG** runs the similarity search against ChromaDB and hands chunks of book text back up to the agent node, which passes them along to the rest of the graph.

So RAG is a tool the agent uses mid-pipeline, not something FastAPI touches directly during a chat request.

## Two different connection paths

There are actually two separate ways RAG and FastAPI meet, and it's worth keeping them distinct:

**Path 1 — the `/chat` endpoint (indirect, through the agent)**

```
POST /chat  (api/main.py)
   │
   ▼
graph.astream(initial_state)   (agent/graph.py)
   │
   ▼
guard  →  retriever  →  evaluator  →  psychologist  →  action_planner  →  follow_up
           (agent/nodes/retriever.py)
                │
                ▼
        build_retriever()   (rag/retriever.py)
                │
                ▼
        ChromaDB similarity search
```

Here, `api/main.py` never imports `rag/retriever.py` for the chat flow. It only imports `agent.graph.build_graph`. The agent node `agent/nodes/retriever.py` is the one that does `from rag.retriever import build_retriever` and calls it. FastAPI is one layer removed from RAG.

**Path 2 — the `/db/*` endpoints (direct, bypassing the agent)**

```
GET /db/stats, /db/search, /db/browse   (api/main.py)
   │
   ▼
from rag.retriever import _vectorstore
   │
   ▼
ChromaDB directly
```

For these debug/inspection endpoints, `api/main.py` imports `_vectorstore` straight from `rag/retriever.py` and queries ChromaDB itself, with no agent involved at all. This path exists purely so you can peek into what's stored (chunk counts per book, test a query, browse a book's chunks) without running the full conversational pipeline.

## Walking through a real `/chat` request

1. Frontend sends `POST /chat` with conversation history.
2. `api/main.py` builds an `AgentState` dict (the shared data structure defined in `agent/state.py`) and calls `graph.astream(initial_state)`.
3. **`guard`** node checks if the message is on-topic. If not, the graph ends immediately with a canned response — RAG is never touched.
4. **`retriever`** node (in `agent/nodes/`) calls `build_retriever()` from `rag/retriever.py`, which returns a LangChain retriever wrapping the ChromaDB collection built by `rag/ingest.py`. It runs a similarity search (top 8 chunks) using the current query, then filters out chunks that aren't from the 6 known books or that reference other books by name.
5. **`evaluator`** node asks the LLM whether those chunks are specific enough. If not, **`query_builder`** rewrites the search query and loops back to `retriever` (up to 3 attempts).
6. **`psychologist`** node takes the approved chunks and generates advice, strictly grounded in that book text.
7. **`action_planner`** and **`follow_up`** turn that advice into concrete steps and a follow-up question.
8. As each node finishes, `api/main.py`'s `stream()` generator serializes the state update and yields it as a Server-Sent Event, so the frontend sees progress node-by-node instead of waiting for the whole pipeline.

## Where the vector data actually comes from

RAG has two halves that also don't talk to each other at runtime:

- **`rag/ingest.py`** is a standalone script you run once (or whenever books change). It reads the PDFs in `backend/books/`, chunks them, embeds them with a local HuggingFace model (`all-MiniLM-L6-v2`), and writes everything into the `chroma_db/` folder on disk. It's never imported by the running server.
- **`rag/retriever.py`** is imported by both the agent node and `api/main.py`. It just opens that same `chroma_db/` folder (read-only, effectively) and wraps it as a retriever.

So the full picture is: `ingest.py` writes the data once, offline. `retriever.py` reads that data at runtime. FastAPI reaches `retriever.py` either directly (`/db/*` endpoints) or indirectly through the agent graph (`/chat` endpoint).

## One-sentence summary

FastAPI is the delivery mechanism, RAG is the knowledge source, and the LangGraph agent is the logic that decides when to call RAG, how to judge what it gets back, and how to turn book excerpts into advice — FastAPI only sees the final streamed output of that whole process (except for the `/db/*` debug routes, which skip the agent and hit RAG directly).
