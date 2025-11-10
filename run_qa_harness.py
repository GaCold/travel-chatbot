"""
QA harness to run a list of user questions through TravelChatbot.ask_question
and save the results for manual review.

Usage:
  python -m src.test.run_qa_harness
or
  python src/test/run_qa_harness.py

Notes:
- Requires an existing Chroma vector store (persist directory) created by the app.
- If not found, the script will print instructions and exit.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

repo_root = os.path.abspath(os.path.dirname(__file__))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
from src.config import Config
from src.chatbot import TravelChatbot

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'tests')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Edit this list to include the questions you want to evaluate
QUESTIONS = [
    "Gợi ý cho tôi các địa điểm du lịch nổi bật ở miền Bắc Việt Nam",
    "Gợi ý địa điểm du lịch miền Trung phù hợp cho gia đình",
    "Những điểm du lịch nổi tiếng ở miền Nam Việt Nam là gì",
    "Sapa có gì chơi, ăn gì, đi đâu, ở đâu?",
    "Nên đi Sapa vào thời gian nào trong năm?",
    "Gợi ý lịch trình 3 ngày 2 đêm ở Sapa",
    "Hà Giang có gì đặc sắc để du lịch?",
    "Nên đi Hà Giang tháng mấy là đẹp nhất?",
    "Các điểm check-in nổi tiếng ở Hà Giang là gì?",
    "Du lịch Mộc Châu nên đi đâu, ăn gì?",
    "Gợi ý lịch trình 2 ngày 1 đêm khám phá Mộc Châu",
    "Tam Đảo có gì chơi, nên ở khu nào?",
    "Du lịch Ninh Bình có những điểm tham quan nổi bật nào?",
    "Tràng An, Bái Đính, Tam Cốc có gì khác nhau?",
    "Hạ Long có gì thú vị ngoài đi tàu tham quan vịnh?",
    "Gợi ý lịch trình 2 ngày du lịch Hạ Long",
    "Nên đi Cát Bà hay Hạ Long nếu chỉ có 2 ngày?",
    "Du lịch Hà Nội có những điểm đáng đi nhất?",
    "Gợi ý một ngày khám phá Hà Nội cho du khách mới",
    "Ở Hà Nội nên thử món ăn đặc sản nào?",
    "Đà Nẵng có gì chơi, ăn gì, đi đâu, ở đâu?",
    "Nên đi Đà Nẵng vào thời điểm nào trong năm?",
    "Lịch trình 3 ngày 2 đêm khám phá Đà Nẵng",
    "Bà Nà Hills có gì nổi bật để tham quan?",
    "Hội An có gì đặc sắc ngoài phố cổ?",
    "Gợi ý lịch trình tham quan Hội An trong 1 ngày",
    "Huế có gì chơi, nên ở khu vực nào khi du lịch?",
    "Nên đi Huế mùa nào đẹp nhất?",
    "Địa điểm du lịch nổi bật ở Quy Nhơn là gì?",
    "Phú Yên có gì hấp dẫn du khách?",
    "Gợi ý lịch trình 3 ngày 2 đêm ở Nha Trang",
    "Ở Nha Trang nên ăn gì và chơi gì buổi tối?",
    "Đà Lạt có gì hấp dẫn vào mùa đông?",
    "Gợi ý các quán cà phê đẹp ở Đà Lạt",
    "Nên đi Đà Lạt vào tháng mấy là nhiều hoa?",
    "Du lịch Buôn Ma Thuột có gì đặc sắc?",
    "Phú Quốc có gì chơi, ăn gì, đi đâu, ở đâu?",
    "Nên đi Phú Quốc mùa nào đẹp và ít mưa?",
    "Gợi ý lịch trình 4 ngày du lịch Phú Quốc",
    "Côn Đảo có gì đặc biệt và nên đi vào thời gian nào?",
    "Du lịch Vũng Tàu có những điểm tham quan nổi bật nào?",
    "Ở Vũng Tàu nên ăn gì, chơi gì buổi tối?",
    "Cần Thơ có gì chơi ngoài chợ nổi Cái Răng?",
    "Gợi ý lịch trình du lịch miền Tây 3 ngày",
    "Những điểm du lịch biển đẹp nhất Việt Nam là gì?",
    "Gợi ý địa điểm du lịch cho cặp đôi ở Việt Nam",
    "Các điểm du lịch phù hợp với gia đình có trẻ nhỏ",
    "Những địa điểm du lịch yên tĩnh để nghỉ dưỡng ở Việt Nam",
    "Các lễ hội du lịch lớn diễn ra trong năm ở Việt Nam",
    "Gợi ý 5 điểm đến du lịch Việt Nam nổi bật trong năm nay"
]



async def run_harness(questions):
    cfg = Config()
    bot = TravelChatbot(
        llm_model=cfg.LLM_MODEL,
        embedding_model_name=cfg.EMBEDDING_MODEL_NAME,
        embedding_model_type=cfg.EMBEDDING_MODEL_TYPE,
        persist_directory=cfg.PERSIST_DIRECTORY,
    )

    print("Checking for vector store...")
    if not bot.load_existing_vector_store():
        print("\nVector store not found. Please create it before running this harness.")
        print("You can run the main app (python main.py) which will create the Chroma DB, or call setup_vector_store() manually from a small script.")
        return 2

    results = []
    for q in questions:
        print(f"\nAsking: {q}")
        try:
            # time the call to ask_question
            t0 = time.perf_counter()
            res = await bot.ask_question(q)
            t1 = time.perf_counter()
            elapsed = t1 - t0

            answer = res.get('answer') if isinstance(res, dict) else str(res)
            sources = res.get('source_documents', []) if isinstance(res, dict) else []
            print(f"(took {elapsed:.2f}s)")
            results.append({'question': q, 'answer': answer, 'sources': sources, 'duration_seconds': round(elapsed, 3)})
        except Exception as e:
            results.append({'question': q, 'error': str(e)})

    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    out_path = os.path.join(OUTPUT_DIR, f'qa_results_{ts}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSaved results to: {out_path}")
    return 0


if __name__ == '__main__':
    code = asyncio.run(run_harness(QUESTIONS))
    sys.exit(code)
