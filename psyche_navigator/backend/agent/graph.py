from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import retriever, evaluator, query_builder, psychologist, action_planner, follow_up, guard


# ── Routing functions ─────────────────────────────────────────────────────────
# LangGraph calls these after a node finishes to decide which node runs next.
# they read a value from the state and return the name of the next node.

def route_after_guard(state: AgentState) -> str:
    """if off-topic → stop the graph. if relevant → continue to retriever."""
    return END if state.get("is_off_topic") else "retriever"


def route_after_evaluation(state: AgentState) -> str:
    """if chunks are good enough → go to psychologist.
    if we've retried 3 times and still not enough → stop and ask user for more details.
    otherwise → rephrase the query and search again."""
    if state["is_enough"]:
        return "psychologist"
    if state["retrieval_attempts"] >= 3:
        return END
    return "query_builder"


# ── Graph definition ──────────────────────────────────────────────────────────
#
# Full pipeline (edges are listed below in execution order):
#
#   guard → retriever → evaluator → psychologist → action_planner → follow_up → END
#                ↑           |
#                |           ├──→ query_builder (retry loop, up to 3 times)
#                |           |         |
#                ←───────────┘─────────┘
#                            |
#                            └──→ END  (if 3 retries failed, ask user for more details)
#

def build_graph():
    graph = StateGraph(AgentState)

    # register each node: maps a name to the function that runs it
    graph.add_node("guard",          guard.run)
    graph.add_node("retriever",      retriever.run)
    graph.add_node("evaluator",      evaluator.run)
    graph.add_node("query_builder",  query_builder.run)
    graph.add_node("psychologist",   psychologist.run)
    graph.add_node("action_planner", action_planner.run)
    graph.add_node("follow_up",      follow_up.run)

    # ── edges in execution order ──────────────────────────────────────────

    # 1. guard is the entry point (first node to run)
    graph.set_entry_point("guard")

    # 2. guard → retriever (if relevant) or → END (if off-topic)
    graph.add_conditional_edges(
        "guard",
        route_after_guard,
        {"retriever": "retriever", END: END},
    )

    # 3. retriever → evaluator (always)
    graph.add_edge("retriever", "evaluator")

    # 4. evaluator → psychologist (if chunks are good)
    #              → query_builder (if retry needed)
    #              → END (if 3 retries failed, ask user for more details)
    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {"psychologist": "psychologist", "query_builder": "query_builder", END: END},
    )

    # 4b. query_builder → retriever (retry loop: rephrase query and search again)
    graph.add_edge("query_builder", "retriever")

    # 5. psychologist → action_planner (always)
    graph.add_edge("psychologist", "action_planner")

    # 6. action_planner → follow_up (always)
    graph.add_edge("action_planner", "follow_up")

    # 7. follow_up → END (conversation turn complete)
    graph.add_edge("follow_up", END)

    # compile turns the graph definition into a runnable object
    return graph.compile()
