from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import List
from agent.state import AgentState
from llm_factory import make_llm

llm = make_llm(temperature=0.5)

# Pydantic class is used to define a strict data structure for the LLM output
class ActionPlan(BaseModel):
    steps:          List[str]
    framework_used: str
    book_source:    str
    time_horizon:   str


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
        c["source_book"] + ": " + c["text"][:200]
        for c in state["retrieved_chunks"]
    ])
    try:
        result = (prompt | structured_llm).invoke({
            "response":     state["final_response"],
            "context":      context,
            "user_message": state["messages"][-1]["content"],
        })
        state["action_plan"] = result.steps
    except Exception:
        state["action_plan"] = []
    return state
