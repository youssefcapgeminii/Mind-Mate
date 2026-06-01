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

# Foreign book titles that appear inside PDF text as cross-references
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

# Loops through every foreign book title in FM 
def _is_clean(text: str) -> bool:
    for marker in _FOREIGN_MARKERS:
        if marker and marker in text:
            return False 
    return True #clean


def run(state: AgentState) -> AgentState:
    log_node_start("retriever")
    attempt_num = state["retrieval_attempts"] + 1
    log_input("RETRIEVER", "query", f'"{state["current_query"]}"')
    log_info("RETRIEVER", "attempt", f"{attempt_num}/3")

    results = _retriever.invoke(state["current_query"])
    log_info("RETRIEVER", "raw hits from ChromaDB", str(len(results)))

    chunks = []
    filtered_out = 0
    for doc in results:
        source = doc.metadata.get("source", "Unknown")
        if source not in _KNOWN_BOOKS:
            filtered_out += 1
            continue
        if not _is_clean(doc.page_content):
            filtered_out += 1
            continue
        chunks.append({
            "text":        doc.page_content,
            "source_book": source,
            "page":        doc.metadata.get("page", 0),
        })

    log_info("RETRIEVER", "filtered out (unknown source / foreign marker)", str(filtered_out))
    log_ok("RETRIEVER", "clean chunks kept", str(len(chunks)))
    for i, c in enumerate(chunks, 1):
        preview = c["text"][:90].replace("\n", " ")
        log_info("RETRIEVER", f"  chunk {i}", f'[{c["source_book"]}, p.{c["page"]}] "{preview}..."')

    state["retrieved_chunks"] = chunks
    state["retrieval_attempts"] += 1
    return state
