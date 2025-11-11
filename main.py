#!/usr/bin/env python3
"""
Main entry point for Travel Chatbot System
"""

import os
import sys
import uvicorn
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    config = Config()
    

    while True:
        try:
            data = await websocket.receive_text()
            import json
            try:
                payload = json.loads(data)
                message = payload.get('message', '')
            except Exception:
                message = data

            result = await chatbot.ask_question(message)
            response = {
                "type": "response",
                "message": result["answer"],
                "sources": result.get("source_documents", []),
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
