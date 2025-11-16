"""
Bước 2: Chạy đánh giá (SIMPLIFIED - không cần OpenAI)
=======================================================

Script này:
1. Đọc dữ liệu từ test_data.json (output của bước 1)
2. Chạy evaluation thủ công:
   - Faithfulness: Kiểm tra độ tương đồng câu trả lời với retrieved contexts
   - AnswerRelevancy: Dùng similarity để check answer có liên quan đến question không
3. Lưu kết quả vào file JSON

Input: evaluation/test_data.json
Output: evaluation/ragas_results.json

Note: Phiên bản simplified không cần OpenAI API
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# Add repo root to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.embedding_manager import EmbeddingManager
from src.config import Config


def calculate_similarity(text1: str, text2: str, embeddings) -> float:
    """
    Tính độ tương đồng cosine giữa 2 text
    Trả về giá trị từ 0 (không giống) đến 1 (giống hoàn toàn)
    """
    import numpy as np
    
    try:
        emb1 = np.array(embeddings.embed_query(text1))
        emb2 = np.array(embeddings.embed_query(text2))
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        # Scale từ [-1, 1] sang [0, 1]
        similarity = (similarity + 1) / 2
        return float(max(0, min(1, similarity)))
    except Exception as e:
        print(f"  ⚠️  Error calculating similarity: {e}")
        return 0.5


def evaluate_faithfulness(
    response: str,
    retrieved_contexts: List[str],
    embeddings
) -> float:
    """
    Đánh giá Faithfulness: Câu trả lời có dựa trên context không?
    
    Phương pháp: Tính độ tương đồng trung bình giữa response và các contexts
    Giá trị cao (>0.7) = Câu trả lời dựa trên context
    Giá trị thấp (<0.5) = Câu trả lời có thể bịa
    """
    
    if not retrieved_contexts:
        # Nếu không có contexts, response không thể được faithful
        return 0.3
    
    similarities = []
    for context in retrieved_contexts:
        sim = calculate_similarity(response, context, embeddings)
        similarities.append(sim)
    
    # Lấy trung bình similarity
    faithfulness_score = sum(similarities) / len(similarities) if similarities else 0.5
    
    return float(max(0, min(1, faithfulness_score)))


def evaluate_answer_relevancy(
    question: str,
    response: str,
    embeddings
) -> float:
    """
    Đánh giá Answer Relevancy: Câu trả lời có liên quan đến câu hỏi không?
    
    Phương pháp: Tính độ tương đồng giữa question và response
    Giá trị cao (>0.6) = Câu trả lời liên quan đến câu hỏi
    Giá trị thấp (<0.4) = Câu trả lời không liên quan (off-topic)
    """
    
    if not response or not question:
        return 0.3
    
    # Tính similarity giữa question và response
    relevancy_score = calculate_similarity(question, response, embeddings)
    
    return float(max(0, min(1, relevancy_score)))


def run_evaluation(
    input_file: str = "evaluation/test_data.json",
    output_file: str = "evaluation/ragas_results.json"
) -> bool:
    """
    Chạy evaluation
    
    Args:
        input_file: Path đến test_data.json từ bước 1
        output_file: Path để lưu kết quả
    
    Returns:
        True nếu thành công, False nếu thất bại
    """
    
    print("\n" + "="*70)
    print("📊 BƯỚC 2: CHẠY EVALUATION (SIMPLIFIED)")
    print("="*70)
    print(f"   Embedding Model: {Config.EMBEDDING_MODEL_NAME} ({Config.EMBEDDING_MODEL_TYPE})")
    
    # Đọc test_data.json
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"❌ File không tìm thấy: {input_file}")
        print(f"   Hãy chạy bước 1 trước: python evaluation/01_collect_test_data.py")
        return False
    
    print(f"\n📖 Reading test data from: {input_file}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
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
        print(f"✅ Embeddings loaded ({Config.EMBEDDING_MODEL_NAME}, type: {Config.EMBEDDING_MODEL_TYPE})")
    except Exception as e:
        print(f"❌ Error loading embeddings: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Chạy evaluation
    print(f"\n⏳ Evaluating {len(test_cases)} test cases...")
    print("-" * 70)
    
    faithfulness_scores = []
    relevancy_scores = []
    
    for idx, case in enumerate(test_cases, 1):
        question = case.get("user_input", "")
        response = case.get("response", "")
        contexts = case.get("retrieved_contexts", [])
        
        print(f"\n[{idx}/{len(test_cases)}] {question[:60]}...")
        
        # Tính Faithfulness
        faithfulness = evaluate_faithfulness(response, contexts, embeddings)
        faithfulness_scores.append(faithfulness)
        print(f"  Faithfulness: {faithfulness:.1%}")
        
        # Tính AnswerRelevancy
        relevancy = evaluate_answer_relevancy(question, response, embeddings)
        relevancy_scores.append(relevancy)
        print(f"  AnswerRelevancy: {relevancy:.1%}")
    
    print("\n" + "-" * 70)
    
    # Tính trung bình
    avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0
    avg_relevancy = sum(relevancy_scores) / len(relevancy_scores) if relevancy_scores else 0
    
    print(f"\n✅ Evaluation Complete!")
    print(f"\n📊 Results:")
    print("-" * 70)
    print(f"  Faithfulness:     {avg_faithfulness:.1%}")
    print(f"  AnswerRelevancy:  {avg_relevancy:.1%}")
    print("-" * 70)
    
    overall = (avg_faithfulness + avg_relevancy) / 2
    print(f"  Overall Score:    {overall:.1%}")
    
    # Lưu vào file
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
        }
    }
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Results saved to: {output_path}")
        return True
    
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False


def main():
    success = run_evaluation()
    
    if success:
        print("\n" + "="*70)
        print("✅ Bước 2 hoàn thành! Results đã được lưu.")
        print("   File: evaluation/ragas_results.json")
        print("="*70 + "\n")
    else:
        print("\n❌ Bước 2 thất bại!")
        sys.exit(1)


if __name__ == "__main__":
    main()
