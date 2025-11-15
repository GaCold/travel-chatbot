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
    "Gợi ý địa điểm du lịch ở miền nam",
    "Sapa có những điểm tham quan nào hấp dẫn?",
    "Hội An có những hoạt động gì thú vị cho du khách?",
    "Đà Nẵng nổi tiếng với những bãi biển nào?",
    "Hà giang có những trải nghiệm du lịch nào đặc sắc?",
    "Hà giang nên đi vào thời gian nào trong năm?",
    "Thời tiết ở Đà Lạt vào tháng 12 như thế nào?",
    "Hà Nội có những địa điểm checkin nào?",
    "Nên đi Hà Nội vào mùa nào trong năm?",
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
