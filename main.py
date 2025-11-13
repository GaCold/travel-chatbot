import os
import sys
import uvicorn
import json
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.chatbot import TravelChatbot
from src.config import Config


app = FastAPI(title="Travel Chatbot API", version="1.0.0")
# chatbot = None

# Serve static files from ui directory
ui_path = Path("ui")
if ui_path.exists():
    app.mount("/ui", StaticFiles(directory="ui"), name="ui")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        config = Config()
        global chatbot
        chatbot = TravelChatbot(
            llm_model=config.LLM_MODEL,
            embedding_model_name=config.EMBEDDING_MODEL_NAME,
            embedding_model_type=config.EMBEDDING_MODEL_TYPE,
            persist_directory=config.PERSIST_DIRECTORY,
        )
        if not os.path.exists(config.PERSIST_DIRECTORY):
            chatbot.setup_vector_store(config.DATA_DIRECTORY, config.PERSIST_DIRECTORY)
        else:
            chatbot.load_existing_vector_store()


    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

@app.get("/")
async def read_root():
    return FileResponse("ui/index.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Travel Chatbot"}

BASE_DIR = Path(__file__).resolve().parent
RATING_FILE = "data/rating.json"

@app.post("/rate")
async def rate_chatbot(request: Request):
    """Nhận đánh giá 1–5 sao từ người dùng và lưu vào file JSON"""
    try:
        data = await request.json()
        rating = int(data.get("rating", 0))
        if rating < 1 or rating > 5:
            return {"status": "error", "message": "Giá trị rating không hợp lệ"}

        # Đọc dữ liệu cũ (nếu có)
        if os.path.exists(RATING_FILE):
            with open(RATING_FILE, "r", encoding="utf-8") as f:
                try:
                    ratings = json.load(f)
                except json.JSONDecodeError:
                    ratings = []
        else:
            ratings = []

        # Thêm rating mới
        ratings.append(rating)

        # Lưu lại
        os.makedirs(os.path.dirname(RATING_FILE), exist_ok=True)
        with open(RATING_FILE, "w", encoding="utf-8") as f:
            json.dump(ratings, f, ensure_ascii=False, indent=2)

        avg = sum(ratings) / len(ratings)
        print(f"⭐ Nhận đánh giá: {rating} | Trung bình hiện tại: {avg:.2f}")

        return {"status": "success", "average": avg, "total": len(ratings)}

    except Exception as e:
        print("❌ Lỗi ghi rating:", e)
        return {"status": "error", "message": str(e)}
    
@app.get("/rate")
def get_rating():
    """Trả về điểm trung bình và tổng số lượt từ file rating.json"""
    try:
        if not os.path.exists(RATING_FILE):
            return {"average": 0, "total": 0}

        with open(RATING_FILE, "r", encoding="utf-8") as f:
            ratings = json.load(f)
            if not isinstance(ratings, list) or not ratings:
                return {"average": 0, "total": 0}

        avg = sum(ratings) / len(ratings)
        return {"average": avg, "total": len(ratings)}
    except Exception as e:
        print("❌ Lỗi đọc rating:", e)
        return {"average": 0, "total": 0}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    config = Config()
    

    while True:
        try:
            data = await websocket.receive_text()
            print(f"Received data: {data}")
            # Expect client to send JSON: {type: 'message', message: '...'}
            import json
            try:
                payload = json.loads(data)
                msg_type = payload.get('type', 'message')
                message = payload.get('message', '')
            except Exception:
                msg_type = 'message'
                message = data

            result = await chatbot.ask_question(message)
            response = {
                "type": "response",
                "message": result["answer"],
                "sources": [
                    {
                        "title": doc.get("metadata", {}).get("article_title", "N/A"),
                        "topic": doc.get("metadata", {}).get("topic", ""),
                        "location": doc.get("metadata", {}).get("location_city", ""),
                    }
                    for doc in result.get("source_documents", [])
                ],
            }
            await websocket.send_json(response)
        except Exception as e:
            await websocket.send_json({"type": "error", "message": f"Lỗi: {e}"})
    
def main():
    """Run the FastAPI server"""
    
    print("🚀 Khởi động Travel Chatbot Server...")
    print("🔧 CẤU HÌNH HỆ THỐNG:")
    config = Config()
    print(f"   LLM Model: {config.LLM_MODEL}")
    print(f"   Embedding Model: {config.EMBEDDING_MODEL_NAME}")
    print(f"   Web UI: http://localhost:8001")
    print(f"   WebSocket: ws://localhost:8001/ws")

    uvicorn.run(app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    main()
