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
from src.config import Config


# ===========================================================================#
#                           Test cases định sẵn                              #
# ===========================================================================#

TEST_CASES = [
    # -------------------------
    # Specific locations (50)
    # -------------------------
    {"question": "Hà Nội có gì chơi?"},
    {"question": "Ăn phở ở đâu ngon tại Hà Nội?"},
    {"question": "Giá vé xe buýt hai tầng Hà Nội bao nhiêu?"},
    {"question": "Vịnh Hạ Long nổi tiếng với gì?"},
    {"question": "Đi thủy phi cơ ngắm Vịnh Hạ Long giá bao nhiêu?"},
    {"question": "Hòn Trống Mái ở đâu?"},
    {"question": "Đà Nẵng có những cây cầu nổi tiếng nào?"},
    {"question": "Ăn gì ngon ở Đà Nẵng?"},
    {"question": "Cầu Vàng nằm ở đâu?"},
    {"question": "Giá vé cáp treo Bà Nà Hills bao nhiêu?"},
    {"question": "Phố cổ Hội An có gì chơi?"},
    {"question": "Đặc sản Hội An là gì?"},
    {"question": "Nên đi Lý Sơn vào tháng mấy?"},
    {"question": "Đi Cù Lao Chàm bằng cách nào?"},
    {"question": "Đặc sản Phú Quốc là gì?"},
    {"question": "Mũi Né có gì chơi?"},
    {"question": "Vịnh Vĩnh Hy ở đâu?"},
    {"question": "Thác Chiềng Khoa ở đâu?"},
    {"question": "Bản Cát Cát ở đâu?"},
    {"question": "Đi Y Tý mùa nào đẹp nhất?"},
    {"question": "Điểm tham quan nổi tiếng ở Mộc Châu?"},
    {"question": "Ăn gì đặc sản ở Sa Pa?"},
    {"question": "Chợ tình Khâu Vai họp khi nào?"},
    {"question": "Giá vé tham quan Tràng An tuyến 1 là bao nhiêu?"},
    {"question": "Leo Hang Múa có bao nhiêu bậc thang?"},
    {"question": "Vườn quốc gia Cúc Phương thuộc tỉnh nào?"},
    {"question": "Hồ Tà Đùng ở đâu?"},
    {"question": "Bảo tàng Thế giới Cà phê ở đâu?"},
    {"question": "Nên đi Nghệ An mùa nào?"},
    {"question": "Vườn quốc gia Pù Mát có gì?"},
    {"question": "Đặc sản Ninh Thuận là gì?"},
    {"question": "Đặc sản Ninh Bình là gì?"},
    {"question": "Làm thế nào để đến Eo Gió?"},
    {"question": "Điện Biên có gì chơi?"},
    {"question": "Đèo Mã Pì Lèng thuộc tỉnh nào?"},
    {"question": "Đi thuyền trên sông Nho Quế giá bao nhiêu?"},
    {"question": "Cầu Hiền Lương bắc qua sông nào?"},
    {"question": "Địa đạo Vịnh Mốc ở đâu?"},
    {"question": "Nhà tù Côn Đảo ở đâu?"},
    {"question": "Vườn quốc gia Bù Gia Mập ở đâu?"},
    {"question": "Chợ nổi Cái Răng họp lúc mấy giờ?"},
    {"question": "Miếu Bà Chúa Xứ núi Sam ở đâu?"},
    {"question": "Khu du lịch Đại Nam ở đâu?"},
    {"question": "Thác Datanla ở đâu?"},
    {"question": "Nhà thờ gỗ Kon Tum có gì đặc biệt?"},
    {"question": "Ăn gì đặc sản ở Đà Lạt?"},
    {"question": "Chợ Bến Thành ở đâu?"},
    {"question": "Đặc sản Châu Đốc là gì?"},
    {"question": "Đi Cần Giờ bằng cách nào?"},
    {"question": "Nhà cổ Bình Thủy ở đâu?"},

    # -------------------------
    # Regional queries (15)
    # -------------------------
    {"question": "Gợi ý du lịch miền bắc"},
    {"question": "Miền trung có những địa điểm nào?"},
    {"question": "Điểm tham quan nổi tiếng ở miền nam"},
    {"question": "Gợi ý quà đặc sản miền Tây"},
    {"question": "Đặc sản miền Trung là gì?"},
    {"question": "Các bãi biển đẹp ở miền Trung?"},
    {"question": "Tây Nguyên có gì chơi?"},
    {"question": "Các tỉnh miền Đông Nam Bộ có gì đặc biệt?"},
    {"question": "Địa điểm check-in đẹp ở miền Bắc"},
    {"question": "Miền Tây nên đi đâu vào mùa nước nổi?"},
    {"question": "Miền Trung tháng 3 có gì đẹp?"},
    {"question": "Các địa điểm du lịch lễ hội miền Bắc?"},
    {"question": "Vùng núi Tây Bắc nên đi đâu?"},
    {"question": "Du lịch miền Nam vào tháng 12 có gì?"},
    {"question": "Miền Bắc có món ăn gì ngon?"},

    # -------------------------
    # Complex queries (10)
    # -------------------------
    {"question": "Nên đi Mù Cang Chải hay Sa Pa vào tháng 9?"},
    {"question": "So sánh Vịnh Hạ Long và Vịnh Vĩnh Hy?"},
    {"question": "So sánh đặc sản Ninh Bình và Thanh Hóa."},
    {"question": "Đà Nẵng hay Nha Trang đáng đi hơn?"},
    {"question": "Cần Thơ và Cà Mau nên đi nơi nào trước?"},
    {"question": "So sánh phở Hà Nội và phở hai tô Gia Lai"},
    {"question": "Chợ nổi Cái Răng và Trà Sư, nên đi đâu trước?"},
    {"question": "Huế hay Hội An phù hợp cho nghỉ dưỡng dài ngày?"},
    {"question": "Bãi biển nào đẹp nhất miền Trung?"},
    {"question": "Phú Quốc hay Côn Đảo đẹp hơn?"},

    # -------------------------
    # Off-topic (15)
    # -------------------------
    {"question": "Thời tiết hôm nay thế nào?"},
    {"question": "Giá vàng hôm nay bao nhiêu?"},
    {"question": "Viết cho tôi một bài thơ về biển Cửa Lò."},
    {"question": "Tổng thống Mỹ là ai?"},
    {"question": "Làm thế nào để đặt vé máy bay đi Phú Quốc?"},
    {"question": "Công thức nấu món bún bò Huế?"},
    {"question": "Thủ đô của nước Pháp là gì?"},
    {"question": "Tôi bị đau bụng nên uống thuốc gì?"},
    {"question": "Kể cho tôi một câu chuyện cười."},
    {"question": "Tại sao mặt trời mọc ở hướng Đông?"},
    {"question": "Covid-19 là gì?"},
    {"question": "Giải phương trình x^2 + 2x - 3 = 0"},
    {"question": "Làm sao để viết một bài luận?"},
    {"question": "Tắt thông báo email trên iPhone?"},
    {"question": "Có bao nhiêu hành tinh trong hệ mặt trời?"},

    # -------------------------
    # Itinerary / Synthesis (10)
    # -------------------------
    {"question": "Gợi ý lịch trình 3 ngày ở Huế và Đà Nẵng."},
    {"question": "Đi Đà Lạt 2 ngày nên đi đâu?"},
    {"question": "Lịch trình 4 ngày ở miền Tây nên đi tỉnh nào?"},
    {"question": "Gợi ý tour 5 ngày ở Tây Nguyên."},
    {"question": "Du lịch miền Trung 3 ngày nên đi Đà Nẵng hay Huế?"},
    {"question": "Lịch trình phượt xe máy từ Hà Nội đi Hà Giang."},
    {"question": "Làm gì trong 1 ngày ở Cần Thơ?"},
    {"question": "Lịch trình 2 ngày ở Ninh Bình."},
    {"question": "Hà Nội – Sa Pa 2 ngày nên đi đâu?"},
    {"question": "Du lịch tự túc Quảng Bình 3 ngày đi đâu?"}
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
    print(f"   LLM Model: {Config.LLM_MODEL}")
    print(f"   Embedding Model: {Config.EMBEDDING_MODEL_NAME} ({Config.EMBEDDING_MODEL_TYPE})")
    print(f"   Persist Directory: {Config.PERSIST_DIRECTORY}")
    try:
        config = Config()
        chatbot = TravelChatbot(
            llm_model=config.LLM_MODEL,
            embedding_model_name=config.EMBEDDING_MODEL_NAME,
            embedding_model_type=config.EMBEDDING_MODEL_TYPE,
            persist_directory=config.PERSIST_DIRECTORY
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
