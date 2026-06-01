from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

#Load the embedding model and vectorstore once, then reuse for every query 
_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
_vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=_embeddings)
_retriever = _vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 8}, # return top 8 chunks per query
)


def build_retriever():
    return _retriever

