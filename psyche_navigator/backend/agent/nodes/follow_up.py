from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent.state import AgentState
from llm_factory import make_llm

llm = make_llm(temperature=0.6)

_SYSTEM = """You are a compassionate psychology guide continuing an ongoing conversation.
You just gave the user advice and an action plan.

Advice: {response}
Action plan: {action_plan}

Conversation history is provided below. Read it carefully so you do NOT repeat
questions that were already asked or topics already resolved.

Ask ONE short follow-up question that either:
- Digs deeper into something not yet covered
- Checks how they feel about the action plan
- Uncovers something that would change your advice

One question only. Warm, conversational tone."""


def run(state: AgentState) -> AgentState:
    system_content = _SYSTEM.format(
        response=state["final_response"],
        action_plan="\n".join(state["action_plan"] or []),
    )
    # build conversation with full history so the LLM doesn't repeat
    # questions that were already asked in earlier turns
    conversation = [SystemMessage(content=system_content)]
    for message in state["messages"][:-1]:
        role = message.get("role", "")
        content = message.get("content", "")
        if role == "user":
            conversation.append(HumanMessage(content=content))
        elif role in ("assistant", "ai"):
            conversation.append(AIMessage(content=content))
    conversation.append(HumanMessage(content=state["messages"][-1]["content"]))

    response = llm.invoke(conversation)
    state["follow_up_question"] = response.content
    state["turn_count"] += 1
    state["should_loop"] = False
    return state
