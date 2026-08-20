from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import List
from agent.state import AgentState
from llm_factory import make_llm
from agent.logger import log_node_start, log_ok, log_warn

llm = make_llm(temperature=0.5)


class ActionPlan(BaseModel):
    """
    Structured JSON schema for the LLM's action plan response.

    Forces the LLM to return JSON matching this structure
    instead of free-form text.
    """
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
    """
    Generate a structured action plan from the psychologist's advice.

    Builds context from retrieved book chunks, then invokes a LangChain pipeline
    (prompt | structured_llm) that fills in the prompt template, sends it to the LLM,
    and parses the response into a structured ActionPlan object.
    Falls back to an empty plan if the LLM fails to return valid JSON.
    """
    log_node_start("action_planner")
    context = "\n".join([
        chunk["source_book"] + ": " + chunk["text"][:200]
        for chunk in state["retrieved_chunks"]
    ])
    try:
        result = (prompt | structured_llm).invoke({
            "response":     state["final_response"],
            "context":      context,
            "user_message": state["messages"][-1]["content"],
        })
        state["action_plan"] = result.steps
        log_ok("ACTION_PLANNER", "steps generated", str(len(result.steps)))
    except Exception as e:
        log_warn("ACTION_PLANNER", "generation failed", str(e))
        state["action_plan"] = []
    return state
