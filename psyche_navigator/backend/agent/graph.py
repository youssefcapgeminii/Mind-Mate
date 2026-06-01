from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import retriever, evaluator, query_builder, psychologist, action_planner, follow_up, guard

# reads is_off_topic. If True, stops immediately
def route_after_guard(state: AgentState) -> str:
    return END if state.get("is_off_topic") else "retriever"

# If chunks are good → psychologist
def route_after_evaluation(state: AgentState) -> str:
    if state["is_enough"]:
        return "psychologist"
    if state["retrieval_attempts"] >= 3:
        return "psychologist"
    return "query_builder"



# when you reach the node named '', call the function ''.run
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("guard",          guard.run)
    graph.add_node("retriever",      retriever.run)
    graph.add_node("evaluator",      evaluator.run)
    graph.add_node("query_builder",  query_builder.run)
    graph.add_node("psychologist",   psychologist.run)
    graph.add_node("action_planner", action_planner.run)
    graph.add_node("follow_up",      follow_up.run)
# starting point
    graph.set_entry_point("guard")

    graph.add_conditional_edges(
        "guard",
        route_after_guard,
        {"retriever": "retriever", END: END},
    )
    # always goes to the same next node
    graph.add_edge("retriever",      "evaluator")
    graph.add_edge("query_builder",  "retriever")
    graph.add_edge("psychologist",   "action_planner")
    graph.add_edge("action_planner", "follow_up")

    # after evaluator: go to psychologist if chunks are sufficient (or max retries hit), else rephrase via query_builder
    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {"psychologist": "psychologist", "query_builder": "query_builder"},
    )

    graph.add_edge("follow_up", END)

    return graph.compile()
