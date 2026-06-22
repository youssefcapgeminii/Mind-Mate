import os
from langchain_groq import ChatGroq

MODEL = "llama-3.3-70b-versatile"


def make_llm(temperature: float = 0):
    """creates a new LLM instance. every node calls this with a different temperature:
    - temperature=0: deterministic output (guard, evaluator)
    - temperature=0.3-0.7: more creative output (psychologist, query_builder)"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("No GROQ_API_KEY found in environment")
    return ChatGroq(model=MODEL, temperature=temperature, groq_api_key=api_key)
