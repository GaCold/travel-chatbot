"""
Bước 1: Thu thập dữ liệu đánh giá
==================================

Script này:
1. Định nghĩa các test cases (câu hỏi)
2. Gọi chatbot để lấy câu trả lời + retrieved contexts
3. Lưu kết quả dạng RAGAS format vào file JSON

Output: evaluation/test_data.json
Format:
{
    "test_cases": [
        {
            "user_input": "Câu hỏi",
            "response": "Câu trả lời từ bot",
            "retrieved_contexts": ["Context 1", "Context 2", ...],
        },
        ...
    ]
}
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import List, Dict

# Add repo root to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.chatbot import TravelChatbot


# ============================================================================
# Test cases định sẵn
# ============================================================================

TEST_CASES = [
    # Specific locations
    {"question": "Hà Nội nên đi đâu chơi?"},
    {"question": "Hạ Long nổi tiếng cái gì?"},
    {"question": "Sapa có gì thú vị?"},
    
    # Regional queries
    {"question": "Gợi ý du lịch miền bắc"},
    {"question": "Miền trung có những địa điểm nào?"},
    {"question": "Điểm tham quan nổi tiếng ở miền nam"},
    
    # Off-topic questions (should return "no data" message)
    {"question": "Thời tiết hôm nay thế nào?"},
    {"question": "2 + 2 bằng bao nhiêu?"},
    
    # More specific location queries
    {"question": "Du lịch Huế nên tham quan những nơi nào?"},
    {"question": "Đà Nẵng có những đặc sản gì?"},
]


async def collect_test_data(output_file: str = "evaluation/test_data.json"):
    """
    Thu thập dữ liệu từ chatbot
    
    Args:
        output_file: Path để lưu JSON output
    """
    
    print("\n" + "="*70)
    print("📊 BƯỚC 1: THU THẬP DỮ LIỆU ĐÁNH GIÁ")
    print("="*70)
    
    # Khởi tạo chatbot
    print("\n🤖 Khởi tạo chatbot...")
    try:
        chatbot = TravelChatbot(
            llm_model="qwen3:0.6b",
            embedding_model_name="AITeamVN/Vietnamese_Embedding_v2",
            embedding_model_type="local",
            persist_directory="./chroma_db"
        )
        
        if not chatbot.load_existing_vector_store():
            print("❌ Không thể tải vector store")
            return False
        
        print("✅ Chatbot initialized")
    
    except Exception as e:
        print(f"❌ Error initializing chatbot: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Thu thập dữ liệu cho mỗi test case
    collected_data = []
    
    print(f"\n📝 Processing {len(TEST_CASES)} test cases...")
    print("-" * 70)
    
    for idx, test_case in enumerate(TEST_CASES, 1):
        question = test_case["question"]
        print(f"\n[{idx}/{len(TEST_CASES)}] Question: {question}")
        
        try:
            # Lấy retrieved contexts (documents)
            docs = chatbot._get_relevant_docs(question)
            retrieved_contexts = [doc.page_content for doc in docs] if docs else []
            
            print(f"  📚 Retrieved {len(retrieved_contexts)} contexts")
            
            # Lấy response từ chatbot
            qa_result = await chatbot.ask_question(question)
            response = qa_result["answer"]
            
            print(f"  ✅ Got response (length: {len(response)} chars)")
            print(f"  Response preview: {response[:100]}...")
            
            # Tạo sample cho RAGAS format
            sample = {
                "user_input": question,
                "response": response,
                "retrieved_contexts": retrieved_contexts,
            }
            
            collected_data.append(sample)
            print(f"  ✓ Data collected")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            # Skip this case nhưng tiếp tục
            continue
    
    print("\n" + "-" * 70)
    print(f"✅ Collected {len(collected_data)}/{len(TEST_CASES)} test cases")
    
    # Lưu vào file JSON
    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    output_data = {
        "test_cases": collected_data,
        "total": len(collected_data),
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Saved to: {output_path}")
        print(f"   File size: {output_path.stat().st_size} bytes")
        return True
    
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False


async def main():
    success = await collect_test_data()
    
    if success:
        print("\n" + "="*70)
        print("✅ Bước 1 hoàn thành! File test_data.json đã được tạo.")
        print("   Bước tiếp theo: python evaluation/02_run_ragas_evaluation.py")
        print("="*70 + "\n")
    else:
        print("\n❌ Bước 1 thất bại!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
