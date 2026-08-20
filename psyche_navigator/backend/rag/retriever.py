from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

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


def build_retriever():
    """
    Return the pre-initialized LangChain retriever instance.

    The retriever uses the as_retriever wrapper around ChromaDB, configured
    for similarity search returning the top 8 most similar chunks.
    """
    return _retriever
