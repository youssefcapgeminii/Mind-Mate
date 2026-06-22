from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import List
from agent.state import AgentState
from llm_factory import make_llm

llm = make_llm(temperature=0.5)

# defines the exact JSON shape we want back from the LLM
class ActionPlan(BaseModel):
    steps:          List[str]
    framework_used: str
    book_source:    str
    time_horizon:   str

# forces the LLM to return JSON matching the ActionPlan structure above
# instead of free-form text
structured_llm = llm.with_structured_output(ActionPlan)

prompt = ChatPromptTemplate.from_template("""
Based on this psychological advice: {response}
And these book frameworks: {context}
Generate a concrete action plan for: {user_message}

Steps must be specific, behavioural, and immediately actionable.
Not abstract. The person should know exactly what to do tomorrow.
""")


def run(state: AgentState) -> AgentState:
    context = "\n".join([
        chunk["source_book"] + ": " + chunk["text"][:200]
        for chunk in state["retrieved_chunks"]
    ])
    try:
        # (prompt | structured_llm) is a LangChain pipeline:
        # 1. fill in the prompt template with the variables
        # 2. send the filled prompt to the LLM
        # 3. LLM returns a structured ActionPlan object
        result = (prompt | structured_llm).invoke({
            "response":     state["final_response"],
            "context":      context,
            "user_message": state["messages"][-1]["content"],
        })
        state["action_plan"] = result.steps
    except Exception:
        # if the LLM fails to return valid JSON, fall back to empty plan
        state["action_plan"] = []
    return state
