from agentic_chatbot import AgenticRAGChatbot

def main():
    print("=" * 70)
    print("🤖 AGENTIC RAG CHATBOT - LANGCHAIN + LANGGRAPH + OLLAMA")
    print("=" * 70 + "\n")
    
    # Cấu hình
    JSONL_FILE = "server/travel.jsonl"
    MODEL_NAME = "qwen2:7b"  # Các lựa chọn: llama3.2, mistral, gemma2, qwen2.5
    
    try:
        # Khởi tạo
        chatbot = AgenticRAGChatbot(
            jsonl_file_path=JSONL_FILE,
            model_name=MODEL_NAME
        )
        
        # Khởi tạo hệ thống
        chatbot.initialize()
        
        # Bắt đầu chat
        chatbot.chat()
        
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file: {JSONL_FILE}")
        print("Hãy đảm bảo file tồn tại trong thư mục hiện tại.")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()