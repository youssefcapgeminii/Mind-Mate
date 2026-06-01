# PsycheNavigator — Complete Implementation Reference

> **This document reflects the actual built system.**
> The original planning document described OpenAI/GPT-4o, BM25 hybrid retrieval,
> a classifier node, Cohere reranking, and a different book set — none of which
> exist in the final implementation.

---

## What Was Built

A conversational AI agent that helps users navigate personal situations —
conflicts with a manager, a colleague, a partner, or internal struggles —
by drawing on a knowledge base of 6 psychology books stored in ChromaDB.

The user describes their situation. The agent retrieves the most relevant
book excerpts, evaluates whether they are good enough, retries with a
smarter query if not, and generates an empathetic, cited, actionable response.

---

## The Core Flow

```
User: "My manager keeps cutting me off in meetings"
          ↓
Guard: is this psychology-related? (if not → polite refusal → END)
          ↓
Retriever: cosine similarity search across 7,267 chunks (top 8)
          ↓
Evaluator: "are these chunks sufficient for specific advice?"
          ↓
     YES → Psychologist → Action Planner → Follow-up → END
     NO  → Query Builder rewrites query → Retriever again (max 3 retries)
```

---

## The Actual Stack

| Layer | Technology | Job |
|---|---|---|
| Agent orchestration | LangGraph | Loop, state, routing between nodes |
| LLM calls / chains | LangChain | Prompts, LLM calls, structured output |
| Vector database | ChromaDB (local) | Stores 7,267 chunks + vectors |
| Embeddings | `all-MiniLM-L6-v2` (HuggingFace, CPU) | Converts text to 384-dim vectors |
| LLM backbone | Groq — Llama 3.3 70B Versatile | All reasoning, evaluation, generation |
| Backend API | FastAPI | Streaming SSE `/chat` endpoint |
| Frontend | React + Tailwind + Vite | Chat UI with live node status |

---

## RAG Type: Classic RAG inside an Agentic Loop

- **Retrieval technique:** pure cosine similarity — `all-MiniLM-L6-v2` embeds the query → ChromaDB finds the top 8 chunks
- **No BM25, no hybrid search, no Cohere reranking** — these were evaluated and removed
- **The agentic part:** the Evaluator → Query Builder → Retriever retry loop compensates for weak initial retrieval
- Psychology queries are naturally semantic ("I feel numb"), not keyword-based, so dense-only retrieval works well

---

## The 6 Knowledge Base Books

| Book | Author | Chunks |
|---|---|---|
| Feeling Good | David D. Burns | 1,864 |
| Attached | Levine & Heller | 622 |
| The Body Keeps the Score | Bessel van der Kolk | 1,765 |
| Games People Play | Eric Berne | 512 |
| Thinking Fast and Slow | Daniel Kahneman | 1,834 |
| Nonviolent Communication | Marshall B. Rosenberg | 670 |
| **Total** | | **7,267** |

---

## AgentState — state.py

```python
from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    messages:            List[dict]      # full conversation history
    current_query:       str             # what to search (may be rewritten by query_builder)
    retrieved_chunks:    List[dict]      # [{text, source_book, page}]
    retrieval_attempts:  int             # safety counter, max 3
    is_enough:           bool            # did evaluator approve the chunks?
    retry_reason:        Optional[str]   # why evaluator said insufficient
    active_frameworks:   List[str]       # books actually cited in the response
    action_plan:         Optional[List[str]]
    final_response:      Optional[str]
    should_loop:         bool            # always False — kept for future use
    turn_count:          int
    is_off_topic:        bool            # did guard block this?
    follow_up_question:  Optional[str]
```

---

## File Structure

```
psyche_navigator/
│
├── backend/
│   ├── agent/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── logger.py           ← color-coded terminal logging
│   │   └── nodes/
│   │       ├── guard.py        ← off-topic filter (replaced classifier)
│   │       ├── retriever.py
│   │       ├── evaluator.py
│   │       ├── query_builder.py
│   │       ├── psychologist.py
│   │       ├── action_planner.py
│   │       └── follow_up.py
│   ├── rag/
│   │   ├── ingest.py           ← run once to populate ChromaDB
│   │   └── retriever.py        ← builds the LangChain retriever
│   ├── api/
│   │   └── main.py             ← FastAPI + SSE streaming + DB explorer endpoints
│   ├── llm_factory.py          ← single place to create Groq LLM instances
│   ├── books/                  ← place PDF files here
│   ├── chroma_db/              ← auto-created by ingest.py
│   ├── requirements.txt
│   └── .env
│
└── frontend/
    └── src/
        ├── components/
        └── App.jsx
```

---

## The Graph — graph.py

```python
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import retriever, evaluator, query_builder, psychologist, action_planner, follow_up, guard

# reads is_off_topic. If True, stops immediately
def route_after_guard(state: AgentState) -> str:
    return END if state.get("is_off_topic") else "retriever"

# after evaluator: sufficient → psychologist, else retry via query_builder (max 3 attempts)
def route_after_evaluation(state: AgentState) -> str:
    if state["is_enough"]:
        return "psychologist"
    if state["retrieval_attempts"] >= 3:
        return "psychologist"   # force answer after max retries
    return "query_builder"

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("guard",          guard.run)
    graph.add_node("retriever",      retriever.run)
    graph.add_node("evaluator",      evaluator.run)
    graph.add_node("query_builder",  query_builder.run)
    graph.add_node("psychologist",   psychologist.run)
    graph.add_node("action_planner", action_planner.run)
    graph.add_node("follow_up",      follow_up.run)

    graph.set_entry_point("guard")

    graph.add_conditional_edges("guard", route_after_guard,
        {"retriever": "retriever", END: END})

    graph.add_edge("retriever",      "evaluator")
    graph.add_edge("query_builder",  "retriever")
    graph.add_edge("psychologist",   "action_planner")
    graph.add_edge("action_planner", "follow_up")
    graph.add_edge("follow_up",      END)          # always ends here

    # after evaluator: go to psychologist if chunks sufficient (or max retries hit),
    # else rephrase via query_builder
    graph.add_conditional_edges("evaluator", route_after_evaluation,
        {"psychologist": "psychologist", "query_builder": "query_builder"})

    return graph.compile()
```

---

## Node 1 — guard.py

Replaced the original `classifier` node. Instead of classifying situation type,
the guard simply decides: is this psychology-related at all?

- Temperature: 0 (deterministic)
- Returns: `relevant` or `off_topic`
- If off_topic: sets `is_off_topic=True`, writes canned refusal to `final_response`, routes to END
- If relevant: sets `current_query = user message`, `retrieval_attempts = 0`, routes to retriever
- Saves 4+ LLM calls for every off-topic message

---

## Node 2 — retriever.py (node)

- Calls `_retriever.invoke(current_query)` → LangChain retriever → ChromaDB cosine search
- Returns top 8 chunks (`k=8`)
- Filters out chunks whose source is not in `_KNOWN_BOOKS`
- Filters out chunks whose body text mentions foreign book titles (cross-references from PDF compilations)
- Saves clean chunks to `retrieved_chunks`, increments `retrieval_attempts`

**No situation_type, no book filtering by category** — all 6 books are always searched.

---

## Node 3 — evaluator.py

- Temperature: 0
- Sends user message + all chunks to Groq
- Returns: `SUFFICIENT` or `INSUFFICIENT` + one sentence reason
- Strict: requires at least 2 chunks with named, actionable frameworks directly relevant to the situation
- Routes to psychologist (sufficient), query_builder (insufficient, < 3 attempts), or psychologist forced (3 attempts)

---

## Node 4 — query_builder.py

- Temperature: 0.3 (some creativity to rephrase differently)
- Receives: original message + previous query + evaluator's rejection reason
- Generates a better, more specific search query using psychological terminology
- Updates `current_query` → graph loops back to retriever

---

## Node 5 — psychologist.py

- Temperature: 0.7
- Reads **full conversation history** — the only node that does this besides follow_up
- Formats chunks as `[Book Name, p.X]\n{text}` in the system prompt
- Strict prompt rules: use person's exact relationship word ("manager", "partner"), cite as `Book Name (p.X)`
- `active_frameworks`: only marks books as used if their name appears in the response text

```python
state["active_frameworks"] = [b for b in all_books if b in response.content]
```

---

## Node 6 — action_planner.py

- Temperature: 0.5
- Uses `with_structured_output(ActionPlan)` — Groq's native tool-calling enforces the schema
- **Not** `PydanticOutputParser` — that was replaced because it crashed when Groq returned prose instead of JSON

```python
class ActionPlan(BaseModel):
    steps:          List[str]
    framework_used: str
    book_source:    str
    time_horizon:   str
```

Fallback: `action_plan = []` if structured output still fails.

---

## Node 7 — follow_up.py

- Temperature: 0.6
- Reads **full conversation history** to avoid repeating questions already asked
- Generates one follow-up question
- Sets `should_loop = False` always — routes to END via simple edge
- Context across turns is preserved because the **frontend sends full history** on every `/chat` request

---

## RAG Ingestion — rag/ingest.py

Run once before starting the server.

```
Books → PyPDFLoader → RecursiveCharacterTextSplitter (800 chars, 120 overlap)
     → all-MiniLM-L6-v2 embeds each chunk → ChromaDB PersistentClient
     → stored at ./chroma_db with cosine distance metric
```

Batch size 500 to avoid memory issues. Total: 7,267 chunks across 6 books.

---

## Retriever — rag/retriever.py

```python
_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
_vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=_embeddings)
_retriever = _vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 8},
)
```

Loaded once at module import. Reused for every request.

---

## LLM Factory — llm_factory.py

Single place where all nodes create their LLM instance.

```python
MODEL = "llama-3.3-70b-versatile"

def make_llm(temperature: float = 0):
    key = os.getenv("GROQ_API_KEY")
    return ChatGroq(model=MODEL, temperature=temperature, groq_api_key=key)
```

---

## FastAPI Backend — api/main.py

- `POST /chat` — runs the LangGraph and streams state updates as SSE
- `GET /db/stats` — returns chunk count per book
- `GET /db/search?q=...&k=8` — cosine similarity search with scores
- `GET /db/browse?book=...` — paginated chunk browser per book
- `GET /health` — server alive check

Streaming:
```python
async for chunk in graph.astream(initial_state):
    for node_name, state_update in chunk.items():
        yield f"data: {json.dumps({'node': node_name, 'output': safe})}\n\n"
yield "data: {\"node\": \"__end__\"}\n\n"
```

---

## Logger — agent/logger.py

Color-coded terminal output. All nodes use it for structured debugging.

| Function | Color | Meaning |
|---|---|---|
| `log_node_start` | Cyan box | Node banner |
| `log_input` | Yellow | Data entering the node |
| `log_llm` | Magenta | Raw LLM output |
| `log_ok` | Green ✓ | Success / positive outcome |
| `log_warn` | Red ✗ | Failure / rejection / fallback |
| `log_info` | Cyan | Neutral detail |
| `log_route` | Blue → | Next node destination |

Nodes with no logging: `psychologist`, `action_planner`, `follow_up`.

---

## .env

```
GROQ_API_KEY=gsk_...
```

---

## Build Order

1. `backend/agent/state.py`
2. `backend/llm_factory.py`
3. `backend/agent/logger.py`
4. `backend/agent/nodes/guard.py`
5. `backend/agent/nodes/retriever.py`
6. `backend/agent/nodes/evaluator.py`
7. `backend/agent/nodes/query_builder.py`
8. `backend/agent/nodes/psychologist.py`
9. `backend/agent/nodes/action_planner.py`
10. `backend/agent/nodes/follow_up.py`
11. `backend/agent/graph.py`
12. `backend/rag/ingest.py`
13. `backend/rag/retriever.py`
14. `backend/api/main.py`
15. `backend/start.py`
16. Frontend components
