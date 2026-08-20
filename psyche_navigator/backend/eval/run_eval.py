"""
Runs the agent pipeline over a set of questions with known answers
(golden_set.json) and scores it with RAGAS:

    - Faithfulness:       does the response stick to what's in retrieved_chunks?
    - Answer Correctness: does the response match the ground-truth answer?
    - Context Precision:  are the chunks that contain the correct answer ranked
                          near the top of the 8 retrieved (rank-weighted)? A
                          score near 1.0 means the answer comes from the top
                          chunks and the tail is noise -- useful for deciding
                          whether k=8 could be lowered.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import pandas as pd

from agent.nodes import guard, retriever, psychologist
from llm_factory import make_llm
from rag.retriever import _embeddings

from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import faithfulness, answer_correctness, context_precision
from ragas.run_config import RunConfig

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_PATH = os.path.join(EVAL_DIR, "results.csv")


def build_initial_state(question: str) -> dict:
    """
    Build a fresh AgentState for a single-question eval run.

    Same shape api/main.py builds for a single incoming chat message,
    so the pipeline runs exactly as it would for real traffic.
    """
    return {
        "messages": [{"role": "user", "content": question}],
        "current_query": question,
        "retrieved_chunks": [],
        "retrieval_attempts": 0,
        "is_enough": False,
        "retry_reason": None,
        "active_frameworks": [],
        "action_plan": None,
        "final_response": None,
        "should_loop": False,
        "turn_count": 0,
        "is_off_topic": False,
        "follow_up_question": None,
    }


def create_evaluation_dataset(golden_set: list) -> list:
    evaluation_dataset = []

    for item in golden_set:
        question = item["question"]
        correct_answer = item["ground_truth"]

        state = build_initial_state(question)

        guard.run(state)
        if state["is_off_topic"]:
            print("  skipped (guard flagged this question off-topic)")
            continue

        retriever.run(state)
        psychologist.run(state)

        retrieved_texts = [chunk["text"] for chunk in state["retrieved_chunks"]]

        evaluation_dataset.append({
            "user_input": question,
            "response": state["final_response"],
            "retrieved_contexts": retrieved_texts,
            "reference": correct_answer,
        })

    return evaluation_dataset

def save_results(df: pd.DataFrame) -> None:
    merged = df.set_index("user_input")

    if os.path.exists(RESULTS_PATH):
        existing = pd.read_csv(RESULTS_PATH).set_index("user_input")
        merged = merged.combine_first(existing)

    merged.reset_index().to_csv(RESULTS_PATH, index=False)
    print(f"\nSaved to {RESULTS_PATH}")


def main():
    golden_set = json.load(open(os.path.join(EVAL_DIR, "golden_set.json")))

    rows = create_evaluation_dataset(golden_set)

    metrics = [answer_correctness, faithfulness, context_precision]

    result = evaluate(
        dataset=EvaluationDataset.from_list(rows),
        metrics=metrics,
        llm=LangchainLLMWrapper(make_llm(temperature=0, model="llama-3.1-8b-instant")),
        embeddings=LangchainEmbeddingsWrapper(_embeddings),
        run_config=RunConfig(max_workers=1, max_retries=15, max_wait=90, timeout=180),
    )

    df = result.to_pandas()
    metric_names = [metric.name for metric in metrics]
    print(df[["user_input", *metric_names]].to_string(index=False))
    for name in metric_names:
        print(f"mean {name}: {df[name].mean():.3f}")

    save_results(df)


if __name__ == "__main__":
    main()
