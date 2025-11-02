#!/usr/bin/env python3
"""
Main entry point for Travel Chatbot System
"""

import os
import sys
from src.chatbot import TravelChatbot
from src.config import Config

def main():
    """Main function to run the travel chatbot"""
    config = Config()
    
    # DEBUG: Kiểm tra cấu hình
    print("🔧 CẤU HÌNH HỆ THỐNG:")
    print(f"   LLM Model: {config.LLM_MODEL}")
    print(f"   Embedding Model: {config.EMBEDDING_MODEL_NAME}")
    print(f"   Embedding Type: {config.EMBEDDING_MODEL_TYPE}")
    print(f"   Data Directory: {config.DATA_DIRECTORY}")
    print(f"   Persist Directory: {config.PERSIST_DIRECTORY}")

    # Initialize chatbot
    chatbot = TravelChatbot(
        llm_model=config.LLM_MODEL,
        embedding_model_name=config.EMBEDDING_MODEL_NAME,
        embedding_model_type=config.EMBEDDING_MODEL_TYPE,
        persist_directory=config.PERSIST_DIRECTORY
    )
    print(f"check chroma db path: {config.PERSIST_DIRECTORY} - {os.path.exists(config.PERSIST_DIRECTORY)}")
    # return
    # Setup or load vector store
    if not os.path.exists(config.PERSIST_DIRECTORY):
        print("🔄 Đang thiết lập vector store...")
        chatbot.setup_vector_store(config.DATA_DIRECTORY)
        print("✅ Thiết lập hoàn tất!")
    else:
        print("📂 Đang tải vector store có sẵn...")
        chatbot.load_existing_vector_store()
        chatbot.check_vector_store_status()
        # DEBUG: Kiểm tra vector store đã load
        try:
            doc_count = chatbot.vector_store._collection.count()
            print(f"✅ Vector store được tải với {doc_count} documents")
        except Exception as e:
            print(f"❌ Lỗi kiểm tra vector store: {e}")
    
    print("\n" + "="*50)
    print("🤖 CHATBOT TƯ VẤN DU LỊCH CẦN THƠ")
    print("="*50)
    print("Gõ 'quit', 'exit' hoặc 'thoát' để dừng chương trình")
    
    # Demo questions
    demo_questions = [
        "Cần Thơ có những địa điểm du lịch nào?",
        "Món ăn ngon ở Cần Thơ là gì?",
        "Lịch trình 2 ngày ở Cần Thơ như thế nào?",
        "Địa điểm check-in đẹp ở Cần Thơ?"
    ]
    
    print("\n💡 Câu hỏi gợi ý:")
    for i, question in enumerate(demo_questions, 1):
        print(f"  {i}. {question}")
    
    # Chat loop
    while True:
        try:
            user_input = input("\n🙋 Bạn: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'thoát']:
                print("👋 Tạm biệt! Hẹn gặp lại!")
                break
                
            if not user_input:
                continue
                
            # Get response
            result = chatbot.ask_question(user_input)
            
            # Display response
            print(f"\n🤖 Bot: {result['answer']}")
            
            # Display sources if available
            if result.get('source_documents'):
                print(f"\n📚 Tham khảo từ {len(result['source_documents'])} nguồn:")
                for i, doc in enumerate(result['source_documents'], 1):
                    source_info = f"  {i}. {doc['metadata'].get('title', 'N/A')}"
                    if doc['metadata'].get('type'):
                        source_info += f" ({doc['metadata']['type']})"
                    print(source_info)
                    
        except KeyboardInterrupt:
            print("\n👋 Tạm biệt! Hẹn gặp lại!")
            break
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")

if __name__ == "__main__":
    main()