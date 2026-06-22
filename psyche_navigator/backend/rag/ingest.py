import os
import sys
import re

# adds the parent directory to Python's import path so we can import from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb

# patterns that detect junk text inside PDFs
# some PDF pages contain ads, promotions, or website links instead of real content
# e.g. "coupon code", "save an additional 20%", "companion workbook"
# if any of these patterns match, the chunk is thrown away
_JUNK_PATTERNS = [
    r"coupon\s+code",
    r"save\s+an?\s+additional\s+\d+\s*%",
    r"companion\s+workbook",
    r"nonviolentcommunication\.com",
]

# detects index pages at the back of books
# index entries look like "motivation, 42-45" or "self-esteem, 100–103"
# if a chunk has more than 4 of these, it's an index page, not real content
_INDEX_ENTRY = re.compile(r'\b[\w\s]+,\s+\d+[–\-]\d+')


def _is_content(text: str) -> bool:
    """decides if a chunk is real book content or junk that should be skipped.
    returns False for: short text (headers/footers), promotional text, index pages."""
    if len(text.strip()) < 120:
        return False
    lower = text.lower()
    for pattern in _JUNK_PATTERNS:
        if re.search(pattern, lower):
            return False
    if len(_INDEX_ENTRY.findall(text)) > 4:
        return False
    return True


BOOKS = {
    "Feeling Good":                "books/feeling_good.pdf",
    "Attached":                    "books/attached.pdf",
    "The Body Keeps the Score":    "books/body_keeps_score.pdf",
    "Games People Play":           "books/games_people_play.pdf",
    "Thinking Fast and Slow":      "books/thinking_fast_and_slow.pdf",
    "Nonviolent Communication":    "books/nonviolent_communication.pdf",
}
def ingest():
    """reads all 6 PDF books, splits them into small text chunks,
    converts each chunk into a vector (embedding), and stores
    everything in ChromaDB so we can search by similarity later."""
    print("Loading local embedding model (all-MiniLM-L6-v2)...")
    # the embedding model converts text into numbers (vectors)
    # normalize_embeddings=True scales all vectors to the same length
    # so cosine similarity works correctly
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # splits PDF text into chunks of 800 characters
    # with 120 character overlap so sentences aren't cut in half
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    all_chunks = []

# Process each book: load PDF, split into chunks, and keep metadata (source book and page number)
    for book_name, pdf_path in BOOKS.items():
        print(f"Loading: {book_name}")
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        chunks = splitter.split_documents(pages)
        for chunk in chunks:
            chunk.metadata["source"] = book_name
        clean_chunks = [chunk for chunk in chunks if _is_content(chunk.page_content)]
        all_chunks.extend(clean_chunks)
        print(f"  -> {len(clean_chunks)}/{len(chunks)} chunks kept after filtering")

    total = len(all_chunks)
    print(f"\nTotal: {total} chunks. Storing in ChromaDB (local, no rate limits)...")

    # create a ChromaDB collection that uses cosine similarity to compare vectors
    # cosine similarity ranges from 0 (completely different) to 1 (identical meaning)
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.create_collection(
        name="langchain",
        metadata={"hnsw:space": "cosine"},
    )

    # convert all chunk text into vectors (lists of numbers)
    texts = [chunk.page_content for chunk in all_chunks]
    metadatas = [chunk.metadata for chunk in all_chunks]
    chunk_ids = [str(index) for index in range(len(all_chunks))]
    vectors = embeddings.embed_documents(texts)

    # insert 500 chunks at a time to avoid crashing memory
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
