from langchain_core.prompts import ChatPromptTemplate
from agent.state import AgentState
from llm_factory import make_llm
from agent.logger import log_node_start, log_input, log_llm, log_ok, log_warn, log_info, log_route

llm = make_llm(temperature=0)

prompt = ChatPromptTemplate.from_template("""
Evaluate whether these book excerpts are sufficient to give
concrete, specific advice for this personal situation.

User situation: {user_message}

Retrieved excerpts:
{chunks}

Ask yourself:
1. Do at least 2 excerpts contain a real, actionable framework directly
   relevant to THIS situation — not just vaguely related emotional content?
2. Would a psychologist actually use these specific excerpts to help this person?
3. Are the excerpts about the right topic (e.g. if user mentions a manager,
   are the chunks about workplace dynamics or communication — not about dates,
   daydreaming, or unrelated personal struggles)?

Be strict. Vague emotional content that could apply to any situation is NOT sufficient.
Generic advice without a named framework is NOT sufficient.

Named frameworks from these books include:
- NVC 4 steps: Observation, Feeling, Need, Request (Nonviolent Communication)
- Attachment styles: secure, anxious, avoidant, protest behavior, deactivating strategies (Attached)
- CBT tools: cognitive distortions, thought records, behavioral activation (Feeling Good)
- Transactional analysis: ego states, psychological games (Games People Play)
- Somatic responses: body-based trauma reactions (The Body Keeps the Score)
- Cognitive biases: System 1/System 2, heuristics (Thinking Fast and Slow)

If at least 2 chunks reference or apply any of the above AND are directly relevant
to the user's specific situation, that is SUFFICIENT.

Answer with exactly one word on the first line:
SUFFICIENT or INSUFFICIENT

Then explain why in one sentence on the next line.
""")


def run(state: AgentState) -> AgentState:
    log_node_start("evaluator")
    log_input("EVALUATOR", "chunks to evaluate", str(len(state["retrieved_chunks"])))
    log_input("EVALUATOR", "for query", f'"{state["messages"][-1]["content"][:100]}..."')

    chunks_text = "\n\n".join([
        f"[{c['source_book']}] {c['text']}"
        for c in state["retrieved_chunks"]
    ])
    response = (prompt | llm).invoke({
        "user_message": state["messages"][-1]["content"],
        "chunks":       chunks_text,
    })
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
            log_warn("EVALUATOR", "max attempts reached", f"{attempts}/3 — forcing route to psychologist")
            log_route("EVALUATOR", "psychologist (forced)")
        else:
            log_info("EVALUATOR", "attempts used", f"{attempts}/3 — retrying")
            log_route("EVALUATOR", "query_builder")

    return state
