from typing import TypedDict, List, Optional

# Without AgentState(memory), no node could communicate with any other node.

class AgentState(TypedDict):
    messages:            List[dict]      #  full conversation history
    current_query:       str             # the latest user message we're trying to answer
    retrieved_chunks:    List[dict]      # chunks returned from chromadb after filtering
    retrieval_attempts:  int             # safety counter, max 3
    is_enough:           bool
    retry_reason:        Optional[str]   # why evaluator said insufficient
    active_frameworks:   List[str] 
    action_plan:         Optional[List[str]]
    final_response:      Optional[str]
    should_loop:         bool
    turn_count:          int
    is_off_topic:        bool
    follow_up_question:  Optional[str]
