import os
from langchain_groq import ChatGroq

MODEL = "llama-3.3-70b-versatile"

#Every node that needs to call the AI model imports make_llm() from here.
def make_llm(temperature: float = 0):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("No GROQ_API_KEY found in environment")
    return ChatGroq(model=MODEL, temperature=temperature, groq_api_key=key)
