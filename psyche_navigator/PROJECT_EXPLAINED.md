# PsycheNavigator — Full Technical Explanation

---

## Table of Contents
1. [What is this project?](#1-what-is-this-project)
2. [LangChain — The Toolkit](#2-langchain--the-toolkit)
3. [LangGraph — The Brain](#3-langgraph--the-brain)
4. [All 7 Agent Nodes — Explained](#4-all-7-agent-nodes--explained)
5. [Agentic RAG — What Makes It "Agentic"](#5-agentic-rag--what-makes-it-agentic)
6. [Classic RAG — The Retrieval Method](#6-classic-rag--the-retrieval-method)
7. [Vector Database (ChromaDB)](#7-vector-database-chromadb)
8. [Embeddings — Turning Text into Numbers](#8-embeddings--turning-text-into-numbers)
9. [Chunks — Splitting the Books](#9-chunks--splitting-the-books)
10. [The Full Pipeline — Step by Step](#10-the-full-pipeline--step-by-step)

---

## 1. What is this project?

MindMate Assistant is a psychology assistant that answers personal questions
(conflicts with managers, relationships, self-doubt, trauma, cognitive biases, etc.)
by reading real psychology books and generating evidence-based advice.

The user types a problem → the system searches relevant book excerpts → an AI
generates a warm, cited response → a structured action plan is created.

The key difference from a simple chatbot: **it does not rely on the AI's
memory**. Every response is grounded exclusively in text retrieved from 6
psychology books stored in a vector database.

```
User types a problem
        ↓
Guard checks if it's psychology-related
        ↓
LangGraph runs 7 nodes in sequence
        ↓
Reads real book excerpts (via Classic RAG — ChromaDB cosine similarity)
        ↓
Self-reflective loop evaluates chunk quality and retries if needed
        ↓
Generates response + action plan
        ↓
Streams everything live to the frontend
```

### The 6 Knowledge Base Books

| Book | Author | Focus | Chunks |
|---|---|---|---|
| Feeling Good | David D. Burns | CBT, depression, anxiety, cognitive distortions | 1,864 |
| Attached | Levine & Heller | Attachment theory, relationship styles | 622 |
| The Body Keeps the Score | Bessel van der Kolk | Trauma, nervous system, healing | 1,765 |
| Games People Play | Eric Berne | Transactional analysis, interpersonal games | 512 |
| Thinking Fast and Slow | Daniel Kahneman | Cognitive biases, decision-making | 1,834 |
| Nonviolent Communication | Marshall B. Rosenberg | Empathic communication, conflict resolution | 670 |
| **Total** | | | **7,267** |

---

## 2. LangChain — The Toolkit

LangChain is NOT the AI itself. It is a **toolkit** (a collection of ready-made
building blocks) that connects AI models, databases, and tools together.

Think of it as LEGO pieces that snap together. Without LangChain, you would need
to write custom code to connect each piece manually.

### What LangChain provides in this project:

#### A) The Pipe Operator `|`
```python
response = (prompt | llm).invoke({"user_message": "I struggle with my boss"})
```
This chains: format the prompt → send to AI → get response.
Without LangChain, this would be 15+ lines of manual API calls and string formatting.

#### B) ChatPromptTemplate — Prompt Builder
```python
prompt = ChatPromptTemplate.from_template("""
You are a filter. Is this message psychology-related?
User message: {user_message}
Return: relevant or off_topic
""")
```
LangChain handles injecting variables and formatting the system/human message
structure that AI APIs require. Every node in this project uses a prompt template.

#### C) The Retrieval Stack
LangChain wraps every retrieval component with the same `.invoke()` interface:

| Component | What it does | LangChain class |
|---|---|---|
| ChromaDB | Vector similarity search | `Chroma` |
| Sentence Transformers | Embed text into vectors | `HuggingFaceEmbeddings` |
| Retriever | Search interface | `as_retriever()` |

Because they all share the same interface, you can swap any piece without
rewriting the rest.

#### D) with_structured_output — Enforced JSON Schema
```python
class ActionPlan(BaseModel):
    steps:          List[str]
    framework_used: str
    book_source:    str
    time_horizon:   str

structured_llm = llm.with_structured_output(ActionPlan)
result = (prompt | structured_llm).invoke({...})
result.steps  # already a Python list, guaranteed valid
```
`with_structured_output()` uses Groq's native tool-calling API to enforce the
schema at the API level — the response is always valid structured data.
This replaced the older `PydanticOutputParser` which asked the LLM to return
raw JSON text and failed when the LLM returned normal text instead.

---

## 3. LangGraph — The Brain

LangGraph is a framework for building **stateful AI agents** — programs that
remember what happened in previous steps and make decisions based on that history.

### The Key Concept: AgentState

Every node reads from and writes to a shared state dictionary:

```python
class AgentState(TypedDict):
    messages:            List[dict]     # full conversation history
    current_query:       str            # what to search for (may be rewritten)
    retrieved_chunks:    List[dict]     # book excerpts found
    retrieval_attempts:  int            # how many times we tried (max 3)
    is_enough:           bool           # did evaluator approve the chunks?
    retry_reason:        str            # why evaluator said insufficient
    active_frameworks:   List[str]      # books actually cited in the response
    action_plan:         List[str]      # structured action steps
    final_response:      str            # the AI's final answer
    should_loop:         bool           # loop back for follow-up?
    turn_count:          int            # conversation turn counter
    is_off_topic:        bool           # did guard block this?
    follow_up_question:  str            # the closing follow-up question
```

This state is passed from node to node. Each node reads what it needs and
writes its output back. This is how nodes "talk" to each other without
direct coupling.

### The Graph Structure

```
                    ┌──────────┐
                    │  Guard   │  ← Entry point (off-topic detection)
                    └────┬─────┘
                         │
            ┌────────────┴────────────┐
            │ off_topic?              │ relevant?
            ▼                         ▼
           END               ┌──────────────┐
                             │   Retriever  │◄──────────┐
                             └──────┬───────┘           │
                                    │                   │ retry loop
                             ┌──────▼───────┐           │
                             │   Evaluator  │           │
                             └──────┬───────┘           │
                                    │                   │
                       ┌────────────┴────────────┐      │
                       │ insufficient            │ sufficient
                       │ (< 3 attempts)          │
                       ▼                         │
               ┌───────────────┐                 │
               │ Query Refiner │─────────────────┘
               └───────────────┘
                                    │ sufficient (or 3 attempts forced)
                                    ▼
                             ┌──────────────┐
                             │ Psychologist │  ← infers situation + responds
                             └──────┬───────┘
                                    ▼
                             ┌──────────────┐
                             │Action Planner│
                             └──────┬───────┘
                                    ▼
                             ┌──────────────┐
                             │  Follow-up   │──► END
                             └──────────────┘
```

---

## 4. All 7 Agent Nodes — Explained

### Node 1: Guard
**File:** `backend/agent/nodes/guard.py`

**What it does:** Entry point of the pipeline. Checks if the message is relevant
to personal or interpersonal psychology. If off-topic, returns a polite refusal
immediately without running retrieval. If relevant, sets up the state.

**How it works:**
- Sends the message to Groq (temperature=0 — deterministic)
- AI responds with exactly: `relevant` or `off_topic`
- If off_topic → sets `is_off_topic = True`, writes refusal to `final_response` → END
- If relevant → sets `current_query = user message`, `retrieval_attempts = 0`

**Why it saves cost:**
```
Off-topic: Guard → END                   (1 LLM call, ~0.5 seconds)
Normal:    Guard → Retriever → ... → END (4+ LLM calls, ~5 seconds)
```

---

### Node 2: Retriever
**File:** `backend/agent/nodes/retriever.py`

**What it does:** Searches all 7,267 chunks using cosine similarity and returns
the top 8 most relevant passages. Also filters out chunks containing references
to books not in the knowledge base.

**How it works:**
1. Takes `current_query` from state
2. HuggingFace embeds the query → 384-dim vector
3. ChromaDB cosine similarity search across all 6 books → top 8 chunks
4. Filters out chunks whose text mentions foreign book titles
   (e.g. chunks that contain "The Gifts of Imperfection" or "The 7 Habits"
   inside the body text — cross-references from OceanofPDF compilations)
5. Saves clean chunks to `retrieved_chunks`, increments `retrieval_attempts`

**Why filtering:** Some PDFs are compilations that contain text from multiple
books. Without filtering, the psychologist would cite hallucinated book titles
it read inside chunk body text.

---

### Node 3: Evaluator
**File:** `backend/agent/nodes/evaluator.py`

**What it does:** Quality gate. Judges whether retrieved chunks are actually
sufficient to give real, specific advice for this exact situation.

**How it works:**
- Sends user message + all chunks to Groq (temperature=0)
- AI responds: `SUFFICIENT` or `INSUFFICIENT` + one sentence explanation
- Strict criteria: requires at least 2 chunks with named, actionable frameworks
  directly relevant to the situation — not just vague emotional content

**Routing:**
```python
if is_enough:               → psychologist
if retrieval_attempts >= 3: → psychologist  (forced after max retries)
else:                       → query_builder
```

---

### Node 4: Query Refiner
**File:** `backend/agent/nodes/query_builder.py`

**What it does:** When evaluator rejects chunks, rewrites the search query
using more specific psychological terminology to find better results.

**How it works:**
- Receives: original message + previous query + evaluator's rejection reason
- Groq (temperature=0.3) generates a better, more specific search query
- Updates `current_query` in state → graph loops back to Retriever
- Maximum 3 retries before forcing the psychologist to answer

**Example:**
```
User:          "I feel invisible at work"
Previous query: "I feel invisible at work"
Retry reason:  "Chunks about general communication, not workplace recognition"
New query:     "being overlooked ignored workplace recognition acknowledgment"
```

---

### Node 5: Psychologist
**File:** `backend/agent/nodes/psychologist.py`

**What it does:** Generates the main response — warm, empathetic, evidence-based,
grounded in retrieved chunks. Also infers the situation context and enforces
strict citation rules.

**Key prompt rules:**
- Read user's message explicitly to identify who situation is about
  ("manager", "partner", "family" etc.) — never infer from chunk content
- Always cite as: `Book Name (p.X)` when referencing a framework
- Only cite books from the label at the top of each excerpt
- Skip excerpts that are clearly unrelated to the situation
- Allowed books: the 6 in the knowledge base only

**Active frameworks fix:** Only marks a book as "Used" if its name actually
appears in the generated response text — not all retrieved books:
```python
state["active_frameworks"] = [b for b in all_books if b in response.content]
```
This ensures the sidebar only shows books genuinely cited, not all retrieved.

---

### Node 6: Action Planner
**File:** `backend/agent/nodes/action_planner.py`

**What it does:** Converts the psychologist's response into a structured,
immediately actionable plan using `with_structured_output()`.

**Schema:**
```python
class ActionPlan(BaseModel):
    steps:          List[str]   # specific, behavioural steps
    framework_used: str         # e.g. "NVC — Observation vs Evaluation"
    book_source:    str         # e.g. "Nonviolent Communication"
    time_horizon:   str         # e.g. "This week"
```

**Why `with_structured_output()` instead of `PydanticOutputParser`:**
The older `PydanticOutputParser` asked the LLM to return raw JSON text and
crashed when Groq returned normal prose instead. `with_structured_output()`
uses Groq's native tool-calling API — the schema is enforced at the API level,
making failures impossible. A fallback sets `action_plan = []` if anything
still goes wrong.

---

### Node 7: Follow-up
**File:** `backend/agent/nodes/follow_up.py`

**What it does:** Generates one targeted follow-up question that deepens the
conversation, checks if advice feels realistic, or uncovers context that would
change the response.

**Rules:** Reads full conversation history to avoid repeating questions.
One question only. Sets `should_loop = False` and always routes to END via a
simple `add_edge("follow_up", END)` — there is no conditional edge here.
Context across turns is preserved because the frontend sends the full
conversation history on every new request, not by looping inside the graph.

---

## 5. Agentic RAG — What Makes It "Agentic"

**Classic RAG (retrieval only):**
```
User question → Retrieve chunks → Generate answer
```
Simple. One-shot. No checking. No adaptation.

**MindMate — Classic RAG inside an Agentic Pipeline:**
```
User question
    ↓
Guard: is this psychology-related?
    ↓ yes
Retrieve top 8 chunks from all 6 books (cosine similarity)
    ↓
EVALUATE: Are these chunks good enough? ← THE agentic part
    ↓ No                    ↓ Yes
Refine query            Psychologist infers situation + generates answer
    ↓                       ↓
Retrieve again          Action Planner structures steps
(up to 3 retries)           ↓
    ↓                   Follow-up question
Eventually answer
```

The **retry loop** (Evaluator → Query Refiner → Retriever → Evaluator) is the
key agentic behavior. The system actively improves its own retrieval quality
before generating a response, rather than blindly answering with whatever it finds.

---

## 6. Classic RAG — The Retrieval Method

### What is Classic RAG?

RAG = Retrieval Augmented Generation. Instead of answering from training memory,
the AI reads relevant passages from a knowledge base and grounds its answer there.

**Classic RAG** = single retrieval method, one search, straight to the LLM.

```
User query
    ↓
HuggingFace model embeds query → 384-number vector
    ↓
ChromaDB cosine similarity search across all 7,267 chunks
    ↓
Top 8 most similar chunks returned
    ↓
Filtered for clean content (no foreign book references)
    ↓
Injected into LLM prompt as context
    ↓
LLM generates grounded response
```

### Why Classic RAG (not Hybrid)?

An earlier version used **Hybrid RAG**: BM25 keyword search + ChromaDB dense
search merged together. This was removed because:
- BM25 was tested and removed — the self-reflective evaluator + query refiner
  loop already compensates for weak initial retrieval by rewriting and retrying
- Psychology queries are naturally semantic ("I feel numb") not keyword-based
- Simpler codebase, one less dependency (`rank-bm25` removed)
- Response quality with and without BM25 was equivalent (~8/10)

### Cosine Similarity

Both query and chunks are represented as 384-number vectors. Cosine similarity
measures the angle between them:

```
Small angle → vectors point same direction → similar meaning → relevant chunk
Large angle → vectors point different ways → different meaning → irrelevant
```

Matches meaning, not keywords:
```
Query: "I feel empty and disconnected"
Finds: "emotional numbness as avoidant response" (Attached)
       "dissociation as trauma response" (The Body Keeps the Score)
       "depressive episodes and distortions" (Feeling Good)
```

---

## 7. Vector Database (ChromaDB)

**Storage:** 7,267 book chunks stored as vectors in a local SQLite file at
`backend/chroma_db/`. Loaded once at server startup.

**Index: HNSW** — graph-based index that finds similar vectors in milliseconds
without comparing against all 7,267 chunks one by one.

**Metadata per chunk:**
```python
{
    "source": "Nonviolent Communication",  # book name → sidebar "Used" badge
    "page":   42,                          # page number → citations in response
}
```

**Why local?** ChromaDB runs entirely on disk — no external service, no API
key, no rate limits, no cost. Rebuilt by running `python rag/ingest.py` once.

---

## 8. Embeddings — Turning Text into Numbers

**Model:** `sentence-transformers/all-MiniLM-L6-v2` (runs locally on CPU)

An embedding converts the MEANING of text into a point in 384-dimensional
mathematical space. Similar meanings end up close together.

```
"I hate my boss"        → [0.23, -0.15, 0.87, ...]  (384 numbers)
"conflict with manager" → [0.21, -0.14, 0.85, ...]  (very close → similar meaning)
"I love pizza"          → [0.89,  0.67, -0.23, ...]  (far away → different meaning)
```

**Critical:** The same model must be used at both ingest time and query time.
If different models were used, vectors exist in different mathematical spaces
and cosine similarity scores mean nothing.

**Why all-MiniLM-L6-v2:**
- Fast on CPU (~50ms per query)
- 384 dimensions — good balance of quality vs speed
- Trained for semantic sentence similarity
- Open source, fully local, no API cost, no rate limits

---

## 9. Chunks — Splitting the Books

### Why chunk?

AI models have a context limit — you cannot feed a 400-page book to the LLM.
Also: embedding an entire chapter produces a vague vector. Smaller chunks
produce precise, focused vectors that match specific queries better.

### How chunks are created

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,     # max 800 characters (~130 words, ~5-8 sentences)
    chunk_overlap=120,  # 120 chars shared between consecutive chunks
)
```

**chunk_size=800:** Small enough for a focused, specific vector. Large enough
to contain a complete psychological idea or framework step.

**chunk_overlap=120:** A sentence at the boundary between two chunks appears
fully in at least one of them — nothing is cut in half.

**The splitter tries natural boundaries in order:**
```
1. Paragraph breaks (\n\n)  → preferred split point
2. Line breaks (\n)
3. Sentence endings (. )
4. Word boundaries ( )
5. Hard character cut at 800  → last resort
```

So most chunks are 400–800 characters, not exactly 800.

### PDF Quality Note

The NVC PDF was replaced during development. The original OceanofPDF version
contained private-use Unicode characters (U+E062, U+E09D) from a custom font
encoding that Python's PDF reader couldn't decode — these appeared as `≡`
symbols in responses. The replacement PDF (PDFDrive source) is fully clean.

Some OceanofPDF PDFs also contain compilation content — text from multiple books
mixed together. The retriever node filters out any chunk whose body text mentions
foreign book titles to prevent the psychologist from citing hallucinated sources.

### The Knowledge Base

| Book | Chunks |
|---|---|
| Feeling Good | 1,864 |
| Attached | 622 |
| The Body Keeps the Score | 1,765 |
| Games People Play | 512 |
| Thinking Fast and Slow | 1,834 |
| Nonviolent Communication | 670 |
| **Total** | **7,267** |

---

## 10. The Full Pipeline — Step by Step

**Query:** *"My manager keeps dismissing my ideas in meetings"*

```
STEP 1 — Frontend sends request
────────────────────────────────────────────
POST /chat
{"messages": [{"role":"user", "content":"My manager keeps dismissing my ideas..."}]}

STEP 2 — Guard Node (LLM call #1, temperature=0)
────────────────────────────────────────────
Input:  user message
Output: "relevant"
State:  is_off_topic=False, current_query=message, retrieval_attempts=0
Stream: {"node": "guard", "output": {"is_off_topic": false}}

STEP 3 — Retriever Node (no LLM — vector search only)
────────────────────────────────────────────
Action: embed query → 384-dim vector → cosine similarity across 7,267 chunks
Filter: remove any chunks referencing foreign book titles in body text
Result: top 8 clean chunks saved to retrieved_chunks, retrieval_attempts=1
Stream: {"node": "retriever", "output": {...}}

STEP 4 — Evaluator Node (LLM call #2, temperature=0)
────────────────────────────────────────────
Input:  user message + 8 chunks
Strict check: at least 2 chunks with named actionable frameworks, directly relevant
Output: "SUFFICIENT — chunks contain NVC observation/evaluation framework..."
State:  is_enough=True
Stream: {"node": "evaluator", "output": {"is_enough": true}}

  → If INSUFFICIENT: Query Refiner rewrites query → back to Retriever (max 3×)

STEP 5 — Psychologist Node (LLM call #3, temperature=0.7)
────────────────────────────────────────────
Input:  8 chunks as context + full conversation history + user message
Rule:   reads "manager" in message → frames all advice as "your manager"
Rule:   cites as "Book Name (p.X)" for every framework referenced
Output: warm, cited response grounded in NVC and Feeling Good frameworks
State:  final_response="...",
        active_frameworks=["Nonviolent Communication", "Feeling Good"]
        (only books whose names appear in the response — not all retrieved books)
Stream: {"node": "psychologist", "output": {"final_response": "..."}}

STEP 6 — Action Planner Node (LLM call #4, temperature=0.5)
────────────────────────────────────────────
Input:  psychologist's response + chunks + user message
Method: with_structured_output(ActionPlan) — Groq tool-calling enforces schema
Output: {
    steps: [
        "Identify specific instances where manager dismissed ideas",
        "Analyze the specific actions or behaviors that led to the dismissal",
        "Reframe thinking — replace 'always dismisses' with specific instances",
        "Prepare for next meeting by anticipating manager's concerns",
        "Practice active listening and ask clarifying questions"
    ],
    framework_used: "NVC — Observation vs Evaluation",
    book_source:    "Nonviolent Communication",
    time_horizon:   "This week"
}
Stream: {"node": "action_planner", "output": {"action_plan": [...]}}

STEP 7 — Follow-up Node (LLM call #5, temperature=0.6)
────────────────────────────────────────────
Input:  response + action plan + full conversation history
Rule:   reads history to avoid repeating questions
Output: "How do you feel about trying to understand your manager's perspective
         — is that something that feels manageable and authentic for you?"
Stream: {"node": "follow_up", "output": {"follow_up_question": "..."}}

STEP 8 — END
────────────────────────────────────────────
Stream: {"node": "__end__"}
Frontend assembles full response from all streamed updates.

Total: 5 LLM calls — ~4 to 6 seconds end to end
```

---

*PsycheNavigator — built with LangGraph, LangChain, Groq (Llama 3.3 70B),
ChromaDB, HuggingFace Sentence Transformers, FastAPI, and React.*
