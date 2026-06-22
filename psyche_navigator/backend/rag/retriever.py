from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# initialized once at import time so we don't reload the model on every query
_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
_vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=_embeddings)

# as_retriever wraps the vectorstore into a LangChain retriever interface
# so it can be called with .invoke(query) and returns the top 8 most similar chunks
_retriever = _vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 8},
)


def build_retriever():
    return _retriever

