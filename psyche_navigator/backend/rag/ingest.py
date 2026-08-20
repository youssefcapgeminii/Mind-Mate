import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb

from books import BOOK_TITLES

_JUNK_PATTERNS = [
    r"coupon\s+code",
    r"save\s+an?\s+additional\s+\d+\s*%",
    r"companion\s+workbook",
    r"nonviolentcommunication\.com",
]
"""
Regex patterns that detect junk text inside PDFs.

Some PDF pages contain ads, promotions, or website links instead of real content
(e.g. 'coupon code', 'save an additional 20%', 'companion workbook').
If any of these patterns match, the chunk is discarded during ingestion.
"""

_INDEX_ENTRY = re.compile(r'\b[\w\s]+,\s+\d+[–\-]\d+')
"""
Pattern to detect index pages at the back of books.

Index entries look like 'motivation, 42-45' or 'self-esteem, 100-103'.
If a chunk has more than 4 matches, it is classified as an index page
rather than real content and is discarded.
"""


def _is_content(text: str) -> bool:
    """
    Determine if a chunk is real book content or junk that should be skipped.

    Returns False for:
        - Short text under 120 characters (headers, footers, page numbers).
        - Promotional text matching any junk pattern.
        - Index pages with more than 4 index-style entries.
    """
    if len(text.strip()) < 120:
        return False
    lower = text.lower()
    for pattern in _JUNK_PATTERNS:
        if re.search(pattern, lower):
            return False
    if len(_INDEX_ENTRY.findall(text)) > 4:
        return False
    return True


_BOOK_FILES = {
    "Feeling Good":                "feeling_good.pdf",
    "Attached":                    "attached.pdf",
    "The Body Keeps the Score":    "body_keeps_score.pdf",
    "Games People Play":           "games_people_play.pdf",
    "Thinking Fast and Slow":      "thinking_fast_and_slow.pdf",
    "Nonviolent Communication":    "nonviolent_communication.pdf",
}

BOOKS = {title: f"books/{_BOOK_FILES[title]}" for title in BOOK_TITLES}


def ingest():
    """
    Run the full ingestion pipeline: PDF loading, chunking, embedding, and storage.

    Steps:
        1. Load the local embedding model (all-MiniLM-L6-v2) with normalized
           embeddings so cosine similarity works correctly.
        2. For each book: load the PDF, split into 800-character chunks with
           120-character overlap (so sentences aren't cut in half), attach
           metadata (source book and page number), and filter out junk.
        3. Create a ChromaDB collection using cosine similarity (ranges from
           0 for completely different to 1 for identical meaning).
        4. Convert all chunk text into vectors and insert in batches of 500
           to avoid memory issues.
    """
    print("Loading local embedding model (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    all_chunks = []

    for book_name, pdf_path in BOOKS.items():
        print(f"Loading: {book_name}")
        loader = PyPDFLoader(pdf_path)
        pages = loader.load() #returns documents with page_content and metadata (page number) by pypdfloader
        chunks = splitter.split_documents(pages)
        for chunk in chunks:
            chunk.metadata["source"] = book_name
        clean_chunks = [chunk for chunk in chunks if _is_content(chunk.page_content)]
        all_chunks.extend(clean_chunks)
        print(f"  -> {len(clean_chunks)}/{len(chunks)} chunks kept after filtering")

    total = len(all_chunks)
    print(f"\nTotal: {total} chunks. Storing in ChromaDB (local, no rate limits)...")

    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.create_collection(
        name="langchain",
        metadata={"hnsw:space": "cosine"},
    )

    texts = [chunk.page_content for chunk in all_chunks]
    metadatas = [chunk.metadata for chunk in all_chunks]
    chunk_ids = [str(index) for index in range(len(all_chunks))]
    vectors = embeddings.embed_documents(texts)

    batch_size = 500
    for start_index in range(0, len(texts), batch_size):
        collection.add(
            ids=chunk_ids[start_index:start_index+batch_size],
            embeddings=vectors[start_index:start_index+batch_size],
            documents=texts[start_index:start_index+batch_size],
            metadatas=metadatas[start_index:start_index+batch_size],
        )
        print(f"  stored {min(start_index+batch_size, total)}/{total}")

    print("Done. ChromaDB ready.")


if __name__ == "__main__":
    ingest()
    