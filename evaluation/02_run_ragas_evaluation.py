"""
Step 2: Run evaluation (SIMPLIFIED - no OpenAI needed)
======================================================

Script performs:
1. Read data from test_data.json (output of step 1)
2. Run manual evaluation:
   - Faithfulness: Check if response aligns with retrieved contexts
   - AnswerRelevancy: Use similarity to verify answer relates to question
3. Save results to JSON file

Input: evaluation/test_data.json
Output: evaluation/ragas_results.json

Note: Simplified version does not require OpenAI API
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add repo root to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.config import Config
from src.embedding_manager import EmbeddingManager


def calculate_similarity(text1: str, text2: str, embeddings) -> float:
    """
    Calculate cosine similarity between two text strings using embeddings.

    Converts both texts to embedding vectors and computes cosine similarity,
    then scales result from [-1, 1] range to [0, 1] range for easier interpretation.

    Args:
        text1 (str): First text to compare.
        text2 (str): Second text to compare.
        embeddings: Embedding model (from EmbeddingManager) with embed_query() method.

    Returns:
        float: Similarity score between 0 (completely different) and 1 (identical).
               Returns 0.5 if calculation fails.

    Example:
        >>> sim = calculate_similarity("Hà Nội đẹp", "Hà Nội rất tuyệt vời", embeddings)
        >>> print(sim)  # High score (similar meaning)
        0.85
    """
    import numpy as np

    try:
        emb1 = np.array(embeddings.embed_query(text1))
        emb2 = np.array(embeddings.embed_query(text2))

        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

        # Scale from [-1, 1] to [0, 1]
        similarity = (similarity + 1) / 2
        return float(max(0, min(1, similarity)))
    except Exception as e:
        print(f"  ⚠️  Error calculating similarity: {e}")
        return 0.5


def evaluate_faithfulness(
    response: str, retrieved_contexts: List[str], embeddings
) -> float:
    """
    Evaluate Faithfulness: Does the response rely on provided context?

    Calculates average similarity between response and all retrieved contexts.
    High score (>0.7) indicates response is grounded in context.
    Low score (<0.5) suggests response may contain hallucinations.

    Args:
        response (str): Generated answer from chatbot.
        retrieved_contexts (List[str]): List of context documents used for generation.
        embeddings: Embedding model with embed_query() method.

    Returns:
        float: Faithfulness score between 0 and 1.
               Returns 0.3 if no contexts provided.

    Example:
        >>> faith = evaluate_faithfulness(
        ...     "Hà Nội có Hồ Gươm",
        ...     ["Hà Nội là thủ đô, có Hồ Gươm cổ kính"],
        ...     embeddings
        ... )
        >>> print(faith)  # High score (response faithful to context)
        0.82
    """

    if not retrieved_contexts:
        # If no contexts, response cannot be faithful
        return 0.3

    similarities = []
    for context in retrieved_contexts:
        sim = calculate_similarity(response, context, embeddings)
        similarities.append(sim)

    # Calculate average similarity
    faithfulness_score = sum(similarities) / len(similarities) if similarities else 0.5

    return float(max(0, min(1, faithfulness_score)))


def evaluate_answer_relevancy(question: str, response: str, embeddings) -> float:
    """
    Evaluate Answer Relevancy: Does response answer the question?

    Calculates similarity between question and response embeddings.
    High score (>0.6) indicates response is relevant to question.
    Low score (<0.4) suggests response is off-topic or irrelevant.

    Args:
        question (str): Original user question.
        response (str): Generated answer from chatbot.
        embeddings: Embedding model with embed_query() method.

    Returns:
        float: Relevancy score between 0 and 1.
               Returns 0.3 if question or response is empty.

    Example:
        >>> rel = evaluate_answer_relevancy(
        ...     "Hà Nội có gì chơi?",
        ...     "Hà Nội có Hồ Gươm, Lăng Bác...",
        ...     embeddings
        ... )
        >>> print(rel)  # High score (relevant answer)
        0.78
    """

    if not response or not question:
        return 0.3

    # Calculate similarity between question and response
    relevancy_score = calculate_similarity(question, response, embeddings)

    return float(max(0, min(1, relevancy_score)))


def run_evaluation(
    input_file: str = "evaluation/test_data.json",
    output_file: str = "evaluation/ragas_results.json",
) -> bool:
    """
    Run evaluation pipeline on test data and save metrics.

    Loads test cases from input file, evaluates Faithfulness and AnswerRelevancy
    for each case using embedding similarity, computes averages, and saves
    results with detailed breakdowns.

    Args:
        input_file (str): Path to test_data.json from step 1.
                         Defaults to "evaluation/test_data.json".
        output_file (str): Path to save results.
                          Defaults to "evaluation/ragas_results.json".

    Returns:
        bool: True if evaluation completes successfully, False on error.

    Side Effects:
        - Prints progress and results to console
        - Creates output JSON file with metrics
        - Logs errors if encountered

    Example:
        >>> success = run_evaluation()
        >>> # Generates evaluation/ragas_results.json
    """

    print("\n" + "=" * 70)
    print("📊 STEP 2: RUN EVALUATION (SIMPLIFIED)")
    print("=" * 70)
    print(
        f"   Embedding Model: {Config.EMBEDDING_MODEL_NAME} ({Config.EMBEDDING_MODEL_TYPE})"
    )

    # Read test_data.json
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"❌ File not found: {input_file}")
        print(f"   Run step 1 first: python evaluation/01_collect_test_data.py")
        return False

    print(f"\n📖 Reading test data from: {input_file}")
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            input_data = json.load(f)

        test_cases = input_data.get("test_cases", [])
        print(f"✅ Loaded {len(test_cases)} test cases")

    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    if not test_cases:
        print("❌ No test cases found in input file")
        return False

    # Load embeddings
    print("\n🔄 Loading embeddings for similarity calculation...")
    try:
        config = Config()
        embedding_manager = EmbeddingManager(config)
        embeddings = embedding_manager.initialize_embeddings()
        print(
            f"✅ Embeddings loaded ({Config.EMBEDDING_MODEL_NAME}, type: {Config.EMBEDDING_MODEL_TYPE})"
        )
    except Exception as e:
        print(f"❌ Error loading embeddings: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Run evaluation
    print(f"\n⏳ Evaluating {len(test_cases)} test cases...")
    print("-" * 70)

    faithfulness_scores = []
    relevancy_scores = []

    for idx, case in enumerate(test_cases, 1):
        question = case.get("user_input", "")
        response = case.get("response", "")
        contexts = case.get("retrieved_contexts", [])

        print(f"\n[{idx}/{len(test_cases)}] {question[:60]}...")

        # Calculate Faithfulness
        faithfulness = evaluate_faithfulness(response, contexts, embeddings)
        faithfulness_scores.append(faithfulness)
        print(f"  Faithfulness: {faithfulness:.1%}")

        # Calculate AnswerRelevancy
        relevancy = evaluate_answer_relevancy(question, response, embeddings)
        relevancy_scores.append(relevancy)
        print(f"  AnswerRelevancy: {relevancy:.1%}")

    print("\n" + "-" * 70)

    # Calculate averages
    avg_faithfulness = (
        sum(faithfulness_scores) / len(faithfulness_scores)
        if faithfulness_scores
        else 0
    )
    avg_relevancy = (
        sum(relevancy_scores) / len(relevancy_scores) if relevancy_scores else 0
    )

    print(f"\n✅ Evaluation Complete!")
    print(f"\n📊 Results:")
    print("-" * 70)
    print(f"  Faithfulness:     {avg_faithfulness:.1%}")
    print(f"  AnswerRelevancy:  {avg_relevancy:.1%}")
    print("-" * 70)

    overall = (avg_faithfulness + avg_relevancy) / 2
    print(f"  Overall Score:    {overall:.1%}")

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True, parents=True)

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "input_file": input_file,
        "num_test_cases": len(test_cases),
        "metrics": {
            "faithfulness": avg_faithfulness,
            "answer_relevancy": avg_relevancy,
        },
        "overall_score": overall,
        "method": "Simplified (using embedding similarity, no OpenAI needed)",
        "ragas_raw_result": {
            "faithfulness_scores": faithfulness_scores,
            "relevancy_scores": relevancy_scores,
        },
    }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Results saved to: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False


def main():
    success = run_evaluation()

    if success:
        print("\n" + "=" * 70)
        print("✅ Step 2 completed! Results have been saved.")
        print("   File: evaluation/ragas_results.json")
        print("=" * 70 + "\n")
    else:
        print("\n❌ Step 2 failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
