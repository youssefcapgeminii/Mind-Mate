from langchain_core.prompts import ChatPromptTemplate
from agent.state import AgentState
from llm_factory import make_llm
from agent.logger import log_node_start, log_input, log_llm, log_ok, log_warn, log_route

llm = make_llm(temperature=0)

_OFF_TOPIC_MESSAGE = (
    "I'm here to help with personal and interpersonal challenges — "
    "things like workplace conflicts, relationship difficulties, or inner struggles.\n\n"
    "That question is a bit outside my area, but feel free to share anything "
    "personal you'd like to work through. I'm listening."
)

prompt = ChatPromptTemplate.from_template("""
You are a filter for a psychology-focused assistant.

Decide if the message is relevant to personal or interpersonal situations.
RELEVANT: conflicts with a boss, coworker, partner, or family member; personal struggles with confidence, self-esteem, emotions, or inner growth.
IRRELEVANT: sports, weather, news, politics, cooking, coding, or anything unrelated to the user's personal psychology.

User message: {user_message}

Return exactly one word: relevant or off_topic
""")

def run(state: AgentState) -> AgentState:
    """
    Classify the user's message and gate entry into the agent pipeline.

    Asks the LLM whether the message is about psychology or personal issues.
    If off-topic, sets a canned rejection response and flags is_off_topic
    so the graph stops at END. If relevant, allows the pipeline to continue
    to the retriever node.
    """
    user_message = state["messages"][-1]["content"]
    state["current_query"] = user_message
    state["retrieval_attempts"] = 0

    log_node_start("guard")
    preview = user_message[:120] + ("..." if len(user_message) > 120 else "")
    log_input("GUARD", "user message", f'"{preview}"')
    """
    LangChain pipeline using the pipe (|) operator:
    1. Takes the prompt template and plugs in the user_message.
    2. Sends the filled prompt to the LLM.
    3. .invoke() runs both steps and gives back the LLM's answer.
    """
    response = (prompt | llm).invoke({"user_message": user_message})
    classification = response.content.strip().lower()

    log_llm("GUARD", "classification", classification.upper())

    if "off_topic" in classification:
        state["is_off_topic"] = True
        state["final_response"] = _OFF_TOPIC_MESSAGE
        state["action_plan"] = []
        state["active_frameworks"] = []
        log_warn("GUARD", "verdict", "OFF-TOPIC — sending canned response")
        log_route("GUARD", "END")
    else:
        state["is_off_topic"] = False
        log_ok("GUARD", "verdict", "RELEVANT — proceeding to retriever")
        log_route("GUARD", "retriever")

    return state
