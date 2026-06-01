from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from agent.graph import build_graph
from agent.state import AgentState
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import json

app = FastAPI(title="PsycheNavigator API")
graph = build_graph()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# shared vectorstore for the /db endpoints
_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
_vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=_embeddings)


# ── Chat receives the user message ─────────────────────────────────────────────────────────────────────

class Message(BaseModel): 
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message] # the full conversation history on every request

@app.post("/chat") 
async def chat(req: ChatRequest):
    initial_state: AgentState = { 
        "messages":           [m.dict() for m in req.messages], #sends the full conversation history on every request
        "current_query":      req.messages[-1].content,
        "retrieved_chunks":   [],
        "retrieval_attempts": 0,
        "is_enough":          False,
        "retry_reason":       None,
        "active_frameworks":  [],
        "action_plan":        None,
        "final_response":     None,
        "should_loop":        False,
        "turn_count":         0,
        "is_off_topic":       False,
        "follow_up_question": None,
    }
# runs the LangGraph and streams state updates as Server-Sent Events (SSE) server pushes an update after each node completes
    async def stream():
        async for chunk in graph.astream(initial_state):
            for node_name, state_update in chunk.items():
                safe = {k: v for k, v in state_update.items()
                        if isinstance(v, (str, int, float, bool, list, dict, type(None)))}
                yield f"data: {json.dumps({'node': node_name, 'output': safe})}\n\n"
        yield "data: {\"node\": \"__end__\"}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Database Explorer ─────────────────────────────────────────────────────────

@app.get("/db/stats")
async def db_stats():
    raw = _vectorstore.get()
    metadatas = raw.get("metadatas", [])
    documents = raw.get("documents", [])

    stats = {}
    for meta, doc in zip(metadatas, documents):
        book = meta.get("source", "Unknown") if meta else "Unknown"
        if book not in stats:
            stats[book] = {"count": 0, "sample": doc[:200] if doc else ""}
        stats[book]["count"] += 1

    return {
        "total": len(documents),
        "books": [
            {"book": book, "chunks": info["count"], "sample": info["sample"]}
            for book, info in sorted(stats.items(), key=lambda x: -x[1]["count"])
        ],
    }
# Returns the top-k chunks with their cosine similarity score.
@app.get("/db/search")
async def db_search(q: str = Query(..., min_length=1), k: int = Query(default=8, le=20)):
    results = _vectorstore.similarity_search_with_score(q, k=k)
    return {
        "query": q,
        "results": [
            {
                "text":   doc.page_content,
                "book":   doc.metadata.get("source", "Unknown"),
                "page":   doc.metadata.get("page", 0),
                "score":  round(float(score), 4),
            }
            for doc, score in results
        ],
    }

@app.get("/db/browse")
async def db_browse(book: str = Query(...), offset: int = 0, limit: int = Query(default=20, le=50)):
    raw = _vectorstore.get()
    docs = raw.get("documents", [])
    metas = raw.get("metadatas", [])
    ids = raw.get("ids", [])

    filtered = [
        {"id": i, "text": d, "page": m.get("page", 0)}
        for i, d, m in zip(ids, docs, metas)
        if m and m.get("source") == book
    ]
    return {
        "book":  book,
        "total": len(filtered),
        "chunks": filtered[offset: offset + limit],
    }


# ── Misc  ──────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "PsycheNavigator API",
        "status": "running",
        "endpoints": {"chat": "POST /chat", "health": "GET /health", "docs": "GET /docs"},
    }
#used to verify the server is alive and responsive
@app.get("/health")
async def health():
    return {"status": "ok"}
