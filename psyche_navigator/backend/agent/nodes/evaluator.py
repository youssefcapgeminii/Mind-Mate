from langchain_core.prompts import ChatPromptTemplate
from agent.state import AgentState
from llm_factory import make_llm
from agent.logger import log_node_start, log_input, log_ok, log_warn, log_info, log_route

llm = make_llm(temperature=0)

prompt = ChatPromptTemplate.from_template("""
Evaluate whether these book excerpts are useful enough to give
meaningful advice for this personal situation.

User situation: {user_message}

Retrieved excerpts:
{chunks}

The excerpts come from general psychology books, not situation-specific guides.
They will rarely mention the user's exact scenario (e.g. "manager in a meeting").
Instead, look for underlying psychological principles that a skilled psychologist
could APPLY to the user's situation.

Ask yourself:
1. Do at least 2 excerpts contain a psychological concept, framework, or technique
   that can be applied to the user's situation — even if the excerpt itself
   discusses a different surface-level scenario?
2. Could a psychologist use the principles in these excerpts to give this person
   useful advice?

Applicable frameworks from these books include:
- NVC 4 steps: Observation, Feeling, Need, Request (Nonviolent Communication)
- Attachment styles: secure, anxious, avoidant, protest behavior, deactivating strategies (Attached)
- CBT tools: cognitive distortions, thought records, behavioral activation (Feeling Good)
- Transactional analysis: ego states, psychological games (Games People Play)
- Somatic responses: body-based trauma reactions (The Body Keeps the Score)
- Cognitive biases: System 1/System 2, heuristics (Thinking Fast and Slow)

If at least 2 chunks contain principles from any of the above that can be
applied to the user's situation, that is SUFFICIENT. The excerpts do NOT need
to mention the user's exact scenario — transferable principles count.

Answer with exactly one word on the first line:
SUFFICIENT or INSUFFICIENT

Then explain why in one sentence on the next line.
""")


def run(state: AgentState) -> AgentState:
    log_node_start("evaluator")
    log_input("EVALUATOR", "chunks to evaluate", str(len(state["retrieved_chunks"])))
    log_input("EVALUATOR", "for query", f'"{state["messages"][-1]["content"][:100]}..."')

    chunks_text = "\n\n".join([
        f"[{chunk['source_book']}] {chunk['text']}"
        for chunk in state["retrieved_chunks"]
    ])
    # ask the LLM: are these chunks good enough to give advice?
    response = (prompt | llm).invoke({
        "user_message": state["messages"][-1]["content"],
        "chunks":       chunks_text,
    })
    # the LLM returns two lines:
    # line 1: "SUFFICIENT" or "INSUFFICIENT"
    # line 2: the reason why
    lines = response.content.strip().split("\n")
    first_line = lines[0].strip().upper()
    reason = lines[1].strip() if len(lines) > 1 else ""

    state["is_enough"] = first_line == "SUFFICIENT"
    state["retry_reason"] = reason

    if state["is_enough"]:
        log_ok("EVALUATOR", "verdict", "SUFFICIENT")
        log_ok("EVALUATOR", "reason", reason)
        log_route("EVALUATOR", "psychologist")
    else:
        log_warn("EVALUATOR", "verdict", "INSUFFICIENT")
        log_warn("EVALUATOR", "reason", reason)
        attempts = state["retrieval_attempts"]
        if attempts >= 3:
            # all 3 retrieval attempts failed — ask the user for more details
            # instead of giving advice based on bad chunks
            state["final_response"] = (
                "I want to give you the best advice I can, but I need a bit more context. "
                "Could you share more details about your situation? For example:\n\n"
                "- Who is involved? (a manager, partner, friend, family member)\n"
                "- What specifically happened?\n"
                "- How is it making you feel?\n\n"
                "The more specific you are, the better I can help."
            )
            state["action_plan"] = []
            state["active_frameworks"] = []
            state["follow_up_question"] = None
            log_warn("EVALUATOR", "max attempts reached", f"{attempts}/3 — asking user for more details")
            log_route("EVALUATOR", "END")
        else:
            log_info("EVALUATOR", "attempts used", f"{attempts}/3 — retrying")
            log_route("EVALUATOR", "query_builder")

    return state
