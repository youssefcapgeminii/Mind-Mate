from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import retriever, evaluator, query_builder, psychologist, action_planner, follow_up, guard


def route_after_guard(state: AgentState) -> str:
    """
    Determine the next node after the guard node.

    If the message is off-topic, stop the graph.
    If the message is relevant, continue to the retriever node.
    """
    return END if state.get("is_off_topic") else "retriever"


def route_after_evaluation(state: AgentState) -> str:
    """
    Determine the next node after the evaluator node.

    If chunks are good enough, proceed to the psychologist node.
    If 3 retrieval attempts have been exhausted, stop and ask the user for more details.
    Otherwise, rephrase the query via query_builder and search again.
    """
    if state["is_enough"]:
        return "psychologist"
    if state["retrieval_attempts"] >= 3:
        return END
    return "query_builder"


def build_graph():
    """
    Construct and compile the LangGraph state graph.

    Registers each node and wires up edges in execution order:
    1. Guard is the entry point (first node to run).
    2. Guard routes to retriever (if relevant) or END (if off-topic).
    3. Retriever always passes to evaluator.
    4. Evaluator routes to psychologist, query_builder (retry), or END.
    5. Query_builder loops back to retriever for another attempt.
    6. Psychologist passes to action_planner.
    7. Action_planner passes to follow_up.
    8. Follow_up ends the conversation turn.
    """
    graph = StateGraph(AgentState)

    graph.add_node("guard",          guard.run)
    graph.add_node("retriever",      retriever.run)
    graph.add_node("evaluator",      evaluator.run)
    graph.add_node("query_builder",  query_builder.run)
    graph.add_node("psychologist",   psychologist.run)
    graph.add_node("action_planner", action_planner.run)
    graph.add_node("follow_up",      follow_up.run)

    graph.set_entry_point("guard")

    graph.add_conditional_edges(
        "guard",
        route_after_guard,
        {"retriever": "retriever", END: END},
    )

    graph.add_edge("retriever", "evaluator")

    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {"psychologist": "psychologist", "query_builder": "query_builder", END: END},
    )

    graph.add_edge("query_builder", "retriever")

    graph.add_edge("psychologist", "action_planner")

    graph.add_edge("action_planner", "follow_up")

    graph.add_edge("follow_up", END)

    return graph.compile()
