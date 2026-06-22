from rag.retriever import build_retriever
from agent.state import AgentState
from agent.logger import log_node_start, log_input, log_info, log_ok

_retriever = build_retriever()

_KNOWN_BOOKS = {
    "Feeling Good",
    "Attached",
    "The Body Keeps the Score",
    "Games People Play",
    "Thinking Fast and Slow",
    "Nonviolent Communication",
}

# foreign book titles that appear inside PDF text as cross-references
_FOREIGN_MARKERS = [
    "The Gifts of Imperfection",
    "The 7 Habits",
    "Seven Habits",
    "Crucial Conversations",
    "Never Split the Difference",
    "Radical Acceptance",
    "The Like Switch",
    "The Empathy Factor",
    "Daring Greatly",
    "Rising Strong",
]


# ── Filtering helpers ─────────────────────────────────────────────────────────

def _has_foreign_reference(text: str) -> bool:
    """checks if the chunk text mentions any book title from _FOREIGN_MARKERS.
    returns True if a foreign book is found (meaning this chunk should be rejected)."""
    for marker in _FOREIGN_MARKERS:
        if marker and marker in text:
            return True
    return False


def _filter_chunks(results):
    """takes raw ChromaDB results and removes bad chunks.
    filter 1: reject if the chunk's source label is not one of our 6 books.
    filter 2: reject if the chunk text mentions a foreign book title."""
    chunks = []
    filtered_out = 0
    for doc in results:
        source = doc.metadata.get("source", "Unknown")
        if source not in _KNOWN_BOOKS:
            filtered_out += 1
            continue
        if _has_foreign_reference(doc.page_content):
            filtered_out += 1
            continue
        chunks.append({
            "text":        doc.page_content,
            "source_book": source,
            "page":        doc.metadata.get("page", 0),
        })
    return chunks, filtered_out


# ── Node entry point ──────────────────────────────────────────────────────────

def run(state: AgentState) -> AgentState:
    log_node_start("retriever")
    attempt_num = state["retrieval_attempts"] + 1
    log_input("RETRIEVER", "query", f'"{state["current_query"]}"')
    log_info("RETRIEVER", "attempt", f"{attempt_num}/3")

    results = _retriever.invoke(state["current_query"])
    log_info("RETRIEVER", "raw hits from ChromaDB", str(len(results)))

    chunks, filtered_out = _filter_chunks(results)

    log_info("RETRIEVER", "filtered out (unknown source / foreign marker)", str(filtered_out))
    log_ok("RETRIEVER", "clean chunks kept", str(len(chunks)))
    for index, chunk in enumerate(chunks, 1):
        preview = chunk["text"][:90].replace("\n", " ")
        log_info("RETRIEVER", f"  chunk {index}", f'[{chunk["source_book"]}, p.{chunk["page"]}] "{preview}..."')

    state["retrieved_chunks"] = chunks
    state["retrieval_attempts"] += 1
    return state
