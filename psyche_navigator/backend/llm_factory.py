import os
from langchain_groq import ChatGroq

MODEL = "llama-3.3-70b-versatile"


def make_llm(temperature: float = 0, model: str = MODEL):
    """
    Create a new ChatGroq LLM instance with the specified temperature.

    Temperature controls output randomness:
        - temperature=0: Deterministic output (used by guard, evaluator).
        - temperature=0.3-0.5: More creative output (used by psychologist, query_builder).

    model defaults to MODEL (llama-3.3-70b-versatile) for all app nodes; callers
    can override it (e.g. the RAGAS eval judge uses llama-3.1-8b-instant, which sits
    on a separate Groq rate-limit bucket).

    Raises:
        RuntimeError: If the GROQ_API_KEY environment variable is not set.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("No GROQ_API_KEY found in environment")
    return ChatGroq(model=model, temperature=temperature, groq_api_key=api_key)
