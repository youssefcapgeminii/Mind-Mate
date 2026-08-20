from rag.retriever import build_retriever
from agent.state import AgentState
from agent.logger import log_node_start, log_input, log_info, log_ok
from books import BOOK_TITLES

_retriever = build_retriever()

_KNOWN_BOOKS = set(BOOK_TITLES)

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
"""
Foreign book titles that appear inside PDF text as cross-references.
Chunks mentioning these are filtered out to prevent citation confusion.
"""


def _has_foreign_reference(text: str) -> bool:
    """
    Check if chunk text mentions any book title from the foreign markers list.

    Returns True if a foreign book is found, meaning this chunk should be rejected.
    """
    for marker in _FOREIGN_MARKERS:
        if marker and marker in text:
            return True
    return False


def _filter_chunks(results):
    """
    Filter raw ChromaDB results to remove unreliable chunks.

    Applies two filters:
        1. Reject if the chunk's source label is not one of the 6 known books.
        2. Reject if the chunk text mentions a foreign book title.

    Returns a tuple of (clean_chunks, filtered_out_count).
    """
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


def run(state: AgentState) -> AgentState:
    """
    Execute a similarity search against ChromaDB and filter the results.

    Queries the vectorstore with the current search query, filters out
    chunks from unknown sources or containing foreign book references,
    and updates the state with clean chunks. Increments the retrieval
    attempt counter.
    """
    log_node_start("retriever")
    attempt_num = state["retrieval_attempts"] + 1
    log_input("RETRIEVER", "query", f'"{state["current_query"]}"')
    log_info("RETRIEVER", "attempt", f"{attempt_num}/3")
# converts input message into a vector and retrieves the most similar chunks from ChromaDB
    results = _retriever.invoke(state["current_query"])
    log_info("RETRIEVER", "raw hits from ChromaDB", str(len(results)))

    chunks, filtered_out = _filter_chunks(results)

    log_info("RETRIEVER", "filtered out (unknown source / foreign marker)", str(filtered_out))
    log_ok("RETRIEVER", "clean chunks kept", str(len(chunks)))
    for index, chunk in enumerate(chunks, 1):
        preview = chunk["text"][:90].replace("\n", " ")
        log_info("RETRIEVER", f"  chunk {index}", f'[{chunk["source_book"]}, p.{chunk["page"]}] "{preview}..."')
# Stores the clean chunks in the shared state
    state["retrieved_chunks"] = chunks
    state["retrieval_attempts"] += 1
    return state
