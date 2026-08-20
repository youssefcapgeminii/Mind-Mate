"""
FastAPI Application for the PsycheNavigator API.

Provides the chat endpoint (SSE streaming), database exploration endpoints
for inspecting ChromaDB contents, and health/root informational endpoints.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from groq import RateLimitError
from agent.graph import build_graph
from agent.state import AgentState
from agent.logger import log_warn
from rag.retriever import _vectorstore
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
"""
CORS middleware configuration.

Allows the React frontend (running on a different port) to call this API.
Without CORS, the browser blocks cross-origin requests for security.
"""


class Message(BaseModel):
    """Single message in the conversation with a role and content."""
    role: str
    content: str

class ChatRequest(BaseModel):
    """
    Incoming chat request payload.

    Contains the full conversation history sent with every request
    so the agent graph has context from prior turns.
    """
    messages: List[Message]

MAX_HISTORY = 10


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint that runs the LangGraph agent pipeline.

    Initializes a fully populated AgentState from the request, then streams
    state updates as Server-Sent Events (SSE). The server pushes an update
    after each node completes, allowing the frontend to show progress
    in real time.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

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

    async def stream():
        """
        Async generator that yields SSE events as each graph node completes.

        Iterates over the LangGraph async stream, serializes each node's
        state update to JSON, and emits it as an SSE data line. Sends a
        final '__end__' event to signal the frontend to stop listening.
        """
        try:
            async for graph_output in graph.astream(initial_state):
                for node_name, state_update in graph_output.items():
                    serializable_fields = {
                        key: value for key, value in state_update.items()
                        if isinstance(value, (str, int, float, bool, list, dict, type(None)))
                    }
                    yield f"data: {json.dumps({'node': node_name, 'output': serializable_fields})}\n\n"
        except RateLimitError as e:
            log_warn("STREAM", "graph execution failed", f"rate limit exceeded: {e}")
            message = "We're getting a lot of requests right now. Please wait a moment and try again."
            yield f"data: {json.dumps({'node': '__error__', 'message': message})}\n\n"
        except Exception as e:
            log_warn("STREAM", "graph execution failed", str(e))
            message = "Something went wrong while processing your request. Please try again."
            yield f"data: {json.dumps({'node': '__error__', 'message': message})}\n\n"
        yield "data: {\"node\": \"__end__\"}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/db/stats")
def db_stats():
    """
    Show how many chunks each book has in ChromaDB.

    Pulls all chunks and metadata from the vectorstore, counts chunks
    per book, grabs a text sample from each, and returns them sorted
    by chunk count (largest first) for display.
    """
    vectorstore_data = _vectorstore.get()
    metadatas = vectorstore_data.get("metadatas", [])
    documents = vectorstore_data.get("documents", [])

    book_stats = {}
    for metadata, document in zip(metadatas, documents):
        book_name = metadata.get("source", "Unknown") if metadata else "Unknown"
        if book_name not in book_stats:
            book_stats[book_name] = {"count": 0, "sample": document[:200] if document else ""}
        book_stats[book_name]["count"] += 1

    sorted_books = sorted(book_stats.items(), key=lambda item: item[1]["count"], reverse=True)

    return {
        "total": len(documents),
        "books": [
            {"book": book_name, "chunks": info["count"], "sample": info["sample"]}
            for book_name, info in sorted_books
        ],
    }


@app.get("/db/search")
def db_search(query: str = Query(..., min_length=1), top_k: int = Query(default=8, le=20)):
    """
    Test a query against ChromaDB and see which chunks it returns.

    Returns chunks ranked by similarity score, where a lower score
    indicates higher similarity to the query (better match).
    """
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
    """
    Browse chunks for a specific book with pagination.

    Filters all ChromaDB chunks to only those belonging to the requested
    book, then returns a paginated slice based on offset and limit.
    """
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


@app.get("/")
def root():
    """
    Landing page endpoint.

    Returns a quick summary when someone visits the API root URL,
    showing the API name, status, and available endpoints.
    """
    return {
        "name": "PsycheNavigator API",
        "status": "running",
        "endpoints": {"chat": "POST /chat", "health": "GET /health", "docs": "GET /docs"},
    }


@app.get("/health")
def health():
    """
    Health check endpoint.

    Deployment platforms (Docker, cloud) ping this to confirm
    the server is alive and responding.
    """
    return {"status": "ok"}
