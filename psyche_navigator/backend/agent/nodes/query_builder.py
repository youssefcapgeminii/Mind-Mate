from langchain_core.prompts import ChatPromptTemplate
from agent.state import AgentState
from llm_factory import make_llm
from agent.logger import log_node_start, log_input, log_llm, log_warn, log_route

llm = make_llm(temperature=0.3) # Some creativity is needed to rephrase differently

prompt = ChatPromptTemplate.from_template("""
You tried to help with: {user_message}
You searched for: {previous_query}
The chunks were insufficient because: {retry_reason}

Write a better, more specific search query to find
concrete frameworks and actionable advice.
Think: specific psychological concepts, named frameworks,
interpersonal dynamics relevant to this situation.

Return only the search query, nothing else.
""")


def run(state: AgentState) -> AgentState:
    log_node_start("query_builder")
    log_warn("QUERY_BUILDER", "retry triggered", f'attempt {state["retrieval_attempts"]}/3 failed')
    log_input("QUERY_BUILDER", "failed query", f'"{state["current_query"]}"')
    log_input("QUERY_BUILDER", "reason chunks failed", state["retry_reason"])

    new_query = (prompt | llm).invoke({
        "user_message":   state["messages"][-1]["content"],
        "previous_query": state["current_query"],
        "retry_reason":   state["retry_reason"],
    })
    state["current_query"] = new_query.content.strip()

    log_llm("QUERY_BUILDER", "new rephrased query", f'"{state["current_query"]}"')
    log_route("QUERY_BUILDER", "retriever (retry)")
    return state
