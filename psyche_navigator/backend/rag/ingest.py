import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb


BOOKS = {
    "Feeling Good":                "books/feeling_good.pdf",
    "Attached":                    "books/attached.pdf",
    "The Body Keeps the Score":    "books/body_keeps_score.pdf",
    "Games People Play":           "books/games_people_play.pdf",
    "Thinking Fast and Slow":      "books/thinking_fast_and_slow.pdf",
    "Nonviolent Communication":    "books/nonviolent_communication.pdf",
}
# normalize_embeddings: True means all vectors are scaled to the same length
def ingest():
    print("Loading local embedding model (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

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
        all_chunks.extend(chunks)
        print(f"  -> {len(chunks)} chunks")

    total = len(all_chunks)
    print(f"\nTotal: {total} chunks. Storing in ChromaDB (local, no rate limits)...")

# Initialize ChromaDB client and create a collection with cosine similarity
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.create_collection(
        name="langchain",
        metadata={"hnsw:space": "cosine"},
    )
# runs all chunks through the embedding model then stores everything in ChromaDB
    texts = [c.page_content for c in all_chunks]
    metadatas = [c.metadata for c in all_chunks]
    ids = [str(i) for i in range(len(all_chunks))]
    vectors = embeddings.embed_documents(texts)
    
# it inserts 500 chunks at a time , instead of inserting all chunks at once (could crash memory)
    batch = 500
    for i in range(0, len(texts), batch):
        collection.add(
            ids=ids[i:i+batch],
            embeddings=vectors[i:i+batch],
            documents=texts[i:i+batch],
            metadatas=metadatas[i:i+batch],
        )
        print(f"  stored {min(i+batch, total)}/{total}")

    print("Done. ChromaDB ready.")


if __name__ == "__main__":
    ingest()
