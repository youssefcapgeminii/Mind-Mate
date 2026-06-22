from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from agent.graph import build_graph
from agent.state import AgentState
from rag.retriever import _vectorstore
import json

app = FastAPI(title="PsycheNavigator API")
graph = build_graph()

# CORS: allows the React frontend (running on a different port) to call this API
# without CORS, the browser blocks cross-origin requests for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Chat receives the user message ─────────────────────────────────────────────────────────────────────

class Message(BaseModel): 
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message] # the full conversation history on every request

MAX_HISTORY = 10

@app.post("/chat")
async def chat(request: ChatRequest):
    recent_messages = request.messages[-MAX_HISTORY:]
    initial_state: AgentState = {
        "messages":           [message.model_dump() for message in recent_messages],
        "current_query":      recent_messages[-1].content,
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
    # streams results to the frontend as each node finishes (SSE)
    async def stream():
        # wait for each node to complete one by one
        async for graph_output in graph.astream(initial_state):
            for node_name, state_update in graph_output.items():
                # remove any values that can't be converted to JSON
                serializable_fields = {
                    key: value for key, value in state_update.items()
                    if isinstance(value, (str, int, float, bool, list, dict, type(None)))
                }
                yield f"data: {json.dumps({'node': node_name, 'output': serializable_fields})}\n\n"
        yield "data: {\"node\": \"__end__\"}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Database Explorer ─────────────────────────────────────────────────────────

@app.get("/db/stats")
def db_stats():
    vectorstore_data = _vectorstore.get()
    metadatas = vectorstore_data.get("metadatas", [])
    documents = vectorstore_data.get("documents", [])

    book_stats = {}
    for metadata, document in zip(metadatas, documents):
        book_name = metadata.get("source", "Unknown") if metadata else "Unknown"
        if book_name not in book_stats:
            book_stats[book_name] = {"count": 0, "sample": document[:200] if document else ""}
        book_stats[book_name]["count"] += 1

    # sort books by chunk number from largest to smallest for display
    sorted_books = sorted(book_stats.items(), key=lambda item: item[1]["count"], reverse=True)

    return {
        "total": len(documents),
        "books": [
            {"book": book_name, "chunks": info["count"], "sample": info["sample"]}
            for book_name, info in sorted_books
        ],
    }
# Returns the top-k chunks with their cosine similarity score.
@app.get("/db/search")
def db_search(query: str = Query(..., min_length=1), top_k: int = Query(default=8, le=20)):
    # returns chunks ranked by how similar they are to the query (lower score = more similar)
    results = _vectorstore.similarity_search_with_score(query, k=top_k)
    return {
        "query": query,
        "results": [
            {
                "text":   document.page_content,
                "book":   document.metadata.get("source", "Unknown"),
                "page":   document.metadata.get("page", 0),
                "score":  round(float(similarity_score), 4),
            }
            for document, similarity_score in results
        ],
    }

@app.get("/db/browse")
def db_browse(book: str = Query(...), offset: int = 0, limit: int = Query(default=20, le=50)):
    vectorstore_data = _vectorstore.get()
    documents = vectorstore_data.get("documents", [])
    metadatas = vectorstore_data.get("metadatas", [])
    chunk_ids = vectorstore_data.get("ids", [])

    filtered_chunks = [
        {"id": chunk_id, "text": document, "page": metadata.get("page", 0)}
        for chunk_id, document, metadata in zip(chunk_ids, documents, metadatas)
        if metadata and metadata.get("source") == book
    ]
    return {
        "book":  book,
        "total": len(filtered_chunks),
        "chunks": filtered_chunks[offset: offset + limit],
    }


# ── Misc  ──────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "PsycheNavigator API",
        "status": "running",
        "endpoints": {"chat": "POST /chat", "health": "GET /health", "docs": "GET /docs"},
    }
#used to verify the server is alive and responsive
@app.get("/health")
def health():
    return {"status": "ok"}
