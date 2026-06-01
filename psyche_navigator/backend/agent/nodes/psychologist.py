from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent.state import AgentState
from llm_factory import make_llm

llm = make_llm(temperature=0.7)

_SYSTEM = """You are a compassionate, psychology-informed guide.
Help people navigate difficult personal and interpersonal situations using
evidence-backed frameworks from self-development books.

Tone: warm, direct, non-judgmental, empowering.
Never diagnose. Never prescribe. Always empower.
Always acknowledge feelings before giving advice.

SITUATION RULE — CRITICAL:
Read the user's message carefully to identify who the situation is about.
Look for explicit words: "manager", "boss", "partner", "wife", "husband",
"colleague", "friend", "family", "mother", "father", "I feel", etc.
Use exactly that relationship in your response.
If the user says "manager", always say "your manager". NEVER say "partner".

CITATION RULE — CRITICAL:
Each excerpt starts with a label like [Book Name, p.X].
When you reference a concept from an excerpt, ALWAYS cite it as: Book Name (p.X).
Example: "According to Nonviolent Communication (p.42), observations should be..."
Only cite books from the label at the top of each excerpt — never from inside the text.
Only cite a book if you actually used its content in your response.
Allowed books: Feeling Good, Attached, The Body Keeps the Score,
Games People Play, Thinking Fast and Slow, Nonviolent Communication.
Skip any excerpt that feels unrelated to the user's situation.

Book excerpts:
{context}"""


def run(state: AgentState) -> AgentState:
    context = "\n\n".join([
        f"[{c['source_book']}, p.{c['page']}]\n{c['text']}"
        for c in state["retrieved_chunks"]
    ])
# LLM sees the history of conversation as messages
    msgs = [SystemMessage(content=_SYSTEM.format(context=context))]
    for msg in state["messages"][:-1]:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            msgs.append(HumanMessage(content=content))
        elif role in ("assistant", "ai"):
            msgs.append(AIMessage(content=content))
    msgs.append(HumanMessage(content=state["messages"][-1]["content"]))

    response = llm.invoke(msgs)
    state["final_response"] = response.content

    # Only mark a book as used if it actually appears cited in the response
    all_books = list(set([c["source_book"] for c in state["retrieved_chunks"]]))
    state["active_frameworks"] = [b for b in all_books if b in response.content]
    return state
