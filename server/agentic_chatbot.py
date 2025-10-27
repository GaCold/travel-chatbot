
# Fix SQLite version issue for Chroma
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import json
from typing import Annotated, Literal
from typing_extensions import TypedDict

# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.tools import create_retriever_tool

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


class State(TypedDict):
    """State của graph"""
    messages: Annotated[list, add_messages]


class AgenticRAGChatbot:
    def __init__(self, jsonl_file_path, model_name="llama3.2"):
        """
        Khởi tạo Agentic RAG Chatbot với LangGraph
        
        Args:
            jsonl_file_path: Đường dẫn file JSONL
            model_name: Model Ollama (llama3.2, mistral, gemma2, qwen2.5)
        """
        self.jsonl_file_path = jsonl_file_path
        self.model_name = model_name
        self.vectorstore = None
        self.retriever_tool = None
        self.graph = None
        self.llm = None
        
    def load_jsonl_data(self):
        """Đọc và xử lý dữ liệu JSONL du lịch, tự động nhận diện type và xây dựng nội dung phù hợp"""
        documents = []
        print("📂 Đang đọc file JSONL...")
        with open(self.jsonl_file_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, 1):
                if line.strip():
                    try:
                        data = json.loads(line)
                        doc_type = data.get('type', 'other')
                        content_parts = []
                        # Xây dựng nội dung tuỳ theo type
                        if doc_type == 'overview':
                            content_parts.append(f"📌 Tổng quan về {data.get('destination_name', '')}")
                            if 'description' in data:
                                content_parts.append(data['description'])
                            if 'highlights' in data:
                                content_parts.append(f"Nổi bật: {', '.join(data['highlights'])}")
                            if 'best_for' in data:
                                content_parts.append(f"Phù hợp: {', '.join(data['best_for'])}")
                        elif doc_type == 'best_time':
                            content_parts.append(f"🕒 Thời gian lý tưởng đi {data.get('destination_name', '')}")
                            if 'best_months' in data:
                                content_parts.append(f"Tháng đẹp: {', '.join(data['best_months'])}")
                            if 'avoid_months' in data:
                                content_parts.append(f"Tránh đi: {', '.join(data['avoid_months'])}")
                            if 'dry_season' in data:
                                content_parts.append(f"Mùa khô: {data['dry_season']}")
                            if 'rainy_season' in data:
                                content_parts.append(f"Mùa mưa: {data['rainy_season']}")
                            if 'weather_note' in data:
                                content_parts.append(f"Thời tiết: {data['weather_note']}")
                            if 'festivals' in data:
                                fest = [f"{f['name']} ({f['month']}): {f.get('note','')}" for f in data['festivals']]
                                content_parts.append(f"Lễ hội: {'; '.join(fest)}")
                        elif doc_type == 'attraction':
                            content_parts.append(f"🏞️ Địa điểm: {data.get('name','')}")
                            if 'category' in data:
                                content_parts.append(f"Loại: {data['category']}")
                            if 'district' in data:
                                content_parts.append(f"Quận: {data['district']}")
                            if 'description' in data:
                                content_parts.append(data['description'])
                            if 'entry_fee' in data:
                                content_parts.append(f"Vé vào cửa: {data['entry_fee']}")
                            if 'opening_hours' in data:
                                content_parts.append(f"Giờ mở cửa: {data['opening_hours']}")
                            if 'time_needed' in data:
                                content_parts.append(f"Thời gian tham quan: {data['time_needed']}")
                            if 'photo_spots' in data:
                                content_parts.append(f"Góc chụp đẹp: {', '.join(data['photo_spots'])}")
                            if 'tips' in data:
                                content_parts.append(f"Tips: {data['tips']}")
                        elif doc_type == 'food':
                            content_parts.append(f"🍜 Đặc sản: {data.get('name','')}")
                            if 'description' in data:
                                content_parts.append(data['description'])
                            if 'price_range' in data:
                                content_parts.append(f"Giá: {data['price_range']}")
                            if 'recommended_places' in data:
                                places = [f"{p['name']} ({p.get('address','')})" for p in data['recommended_places']]
                                content_parts.append(f"Quán nổi bật: {', '.join(places)}")
                            if 'eating_time' in data:
                                content_parts.append(f"Thời điểm ăn: {data['eating_time']}")
                            if 'tip' in data:
                                content_parts.append(f"Tips: {data['tip']}")
                        elif doc_type == 'transportation':
                            content_parts.append(f"🚗 Phương tiện: {data.get('mode','')}")
                            if 'airport' in data:
                                content_parts.append(f"Sân bay: {data['airport']}")
                            if 'station' in data:
                                content_parts.append(f"Ga: {data['station']}")
                            if 'from_hanoi' in data:
                                content_parts.append(f"Từ Hà Nội: {data['from_hanoi']}")
                            if 'from_danang' in data:
                                content_parts.append(f"Từ Đà Nẵng: {data['from_danang']}")
                            if 'bus_companies' in data:
                                content_parts.append(f"Nhà xe: {', '.join(data['bus_companies'])}")
                            if 'cost' in data:
                                content_parts.append(f"Giá: {data['cost']}")
                            if 'note' in data:
                                content_parts.append(f"Ghi chú: {data['note']}")
                            if 'tip' in data:
                                content_parts.append(f"Tips: {data['tip']}")
                        elif doc_type == 'accommodation':
                            content_parts.append(f"🏨 Lưu trú: {data.get('name','')}")
                            if 'accom_type' in data:
                                content_parts.append(f"Loại: {data['accom_type']}")
                            if 'price_range' in data:
                                content_parts.append(f"Giá: {data['price_range']}")
                            if 'address' in data:
                                content_parts.append(f"Địa chỉ: {data['address']}")
                            if 'areas' in data:
                                content_parts.append(f"Khu vực: {', '.join(data['areas'])}")
                            if 'amenities' in data:
                                content_parts.append(f"Tiện ích: {', '.join(data['amenities'])}")
                            if 'booking' in data:
                                content_parts.append(f"Đặt phòng: {data['booking']}")
                            if 'rating' in data:
                                content_parts.append(f"Đánh giá: {data['rating']}")
                            if 'benefits' in data:
                                content_parts.append(f"Lợi ích: {', '.join(data['benefits'])}")
                            if 'tip' in data:
                                content_parts.append(f"Tips: {data['tip']}")
                        elif doc_type == 'cost':
                            content_parts.append(f"💰 Chi phí du lịch {data.get('destination_name','')}")
                            if 'daily_budget' in data:
                                for k, v in data['daily_budget'].items():
                                    content_parts.append(f"{k.capitalize()}: {v['total']} - {v['breakdown']}")
                            if 'money_saving_tips' in data:
                                content_parts.append(f"Mẹo tiết kiệm: {', '.join(data['money_saving_tips'])}")
                        elif doc_type == 'itinerary':
                            content_parts.append(f"🗺️ Lịch trình: {data.get('duration','')}, loại: {data.get('itinerary_type','')}")
                            if 'day_1' in data:
                                content_parts.append(f"Ngày 1: {data['day_1']}")
                            if 'day_2' in data:
                                content_parts.append(f"Ngày 2: {data['day_2']}")
                            if 'day_3' in data:
                                content_parts.append(f"Ngày 3: {data['day_3']}")
                        elif doc_type == 'practical_info':
                            content_parts.append(f"ℹ️ Thông tin thực tế {data.get('destination_name','')}")
                            if 'language' in data:
                                content_parts.append(f"Ngôn ngữ: {data['language']}")
                            if 'currency' in data:
                                content_parts.append(f"Tiền tệ: {data['currency']}")
                            if 'atm' in data:
                                content_parts.append(f"ATM: {data['atm']}")
                            if 'credit_card' in data:
                                content_parts.append(f"Thẻ tín dụng: {data['credit_card']}")
                            if 'sim_card' in data:
                                sim = data['sim_card']
                                sim_str = f"SIM: {', '.join(sim.get('providers',[]))}, giá: {sim.get('price','')}, mua tại: {sim.get('where_to_buy','')}"
                                content_parts.append(sim_str)
                            if 'safety' in data:
                                safe = data['safety']
                                content_parts.append(f"An toàn: {safe.get('level','')}, cảnh báo: {', '.join(safe.get('warnings',[]))}")
                            if 'emergency' in data:
                                em = data['emergency']
                                em_str = f"Cấp cứu: Police {em.get('police','')}, Ambulance {em.get('ambulance','')}, Fire {em.get('fire','')}"
                                content_parts.append(em_str)
                        else:
                            # Nếu không nhận diện được type, chỉ dump toàn bộ nội dung
                            content_parts.append(json.dumps(data, ensure_ascii=False))
                        content = "\n".join(content_parts)
                        # Metadata chuẩn hóa
                        metadata = {
                            "type": doc_type,
                            "destination_name": data.get('destination_name',''),
                            "name": data.get('name',''),
                            "category": data.get('category',''),
                            "tags": ','.join(data.get('tags',[])) if isinstance(data.get('tags',[]), list) else str(data.get('tags','')),
                            "keywords": ','.join(data.get('keywords',[])) if isinstance(data.get('keywords',[]), list) else str(data.get('keywords','')),
                            "source": f"line_{idx}"
                        }
                        documents.append(Document(
                            page_content=content,
                            metadata=metadata
                        ))
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Bỏ qua dòng {idx}: {e}")
        print(f"✅ Đã tải {len(documents)} documents")
        # Thống kê theo type
        types = {}
        for doc in documents:
            t = doc.metadata.get('type', 'Không xác định')
            types[t] = types.get(t, 0) + 1
        print(f"\n📊 Thống kê dữ liệu:")
        print(f"   Loại document: {', '.join([f'{k} ({v})' for k, v in types.items()])}")
        return documents
    
    def create_vectorstore_and_retriever(self, documents):
        """Tạo vector store và retriever tool"""
        print("🔨 Đang tạo vector store...")
        
        # Chia nhỏ documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        print(f"✅ Đã chia thành {len(splits)} chunks")
        
        # Tạo embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # Tạo vector store
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        print("✅ Vector store đã sẵn sàng")
        
        # Tạo retriever tool
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 3}
        )
        
        self.retriever_tool = create_retriever_tool(
            retriever,
            "retrieve_travel_info",
            "Tìm kiếm thông tin du lịch Việt Nam bao gồm: địa điểm, phương tiện, ẩm thực, khách sạn và mẹo du lịch theo vùng miền."
        )
        print("✅ Retriever tool đã sẵn sàng")
        
    def build_graph(self):
        """Xây dựng LangGraph với agentic RAG"""
        print("🔧 Đang xây dựng LangGraph...")
        
        # Khởi tạo LLM với tools
        self.llm = ChatOllama(
            model=self.model_name,
            temperature=0.7
        )
        llm_with_tools = self.llm.bind_tools([self.retriever_tool])
        
        # Node 1: Query hoặc Respond
        def query_or_respond(state: State):
            """Agent quyết định retrieve hay trả lời trực tiếp"""
            messages = state["messages"]
            response = llm_with_tools.invoke(messages)
            return {"messages": [response]}
        
        # Node 2: Generate answer
        def generate_answer(state: State):
            """Tạo câu trả lời cuối cùng dựa trên context"""
            messages = state["messages"]
            
            # Lấy tool messages (retrieved documents)
            tool_messages = [msg for msg in messages if hasattr(msg, 'tool_calls')]
            
            # Tạo prompt với context
            system_prompt = """Bạn là trợ lý du lịch Việt Nam thông minh và nhiệt tình. 
            
Nhiệm vụ của bạn:
- Cung cấp thông tin du lịch chính xác về các vùng miền Việt Nam
- Tư vấn về địa điểm, phương tiện, ẩm thực, khách sạn
- Đưa ra các mẹo du lịch hữu ích
- Trả lời bằng tiếng Việt thân thiện và dễ hiểu

Quy tắc:
- Sử dụng thông tin từ các tài liệu được cung cấp trong cuộc trò chuyện
- Không tự suy luận hay bịa đặt thông tin
- Luôn phản hồi bằng tiếng Việt

Nếu thông tin không có trong dữ liệu thì không tự suy luận hay bịa đặt, hãy lịch sự từ chối và gợi ý người dùng tìm kiếm thông tin khác."""
            
            response = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                *messages
            ])
            return {"messages": [response]}
        
        # Xây dựng graph
        graph_builder = StateGraph(State)
        
        # Thêm nodes
        graph_builder.add_node("query_or_respond", query_or_respond)
        graph_builder.add_node("tools", ToolNode([self.retriever_tool]))
        graph_builder.add_node("generate_answer", generate_answer)
        
        # Thêm edges
        graph_builder.add_edge(START, "query_or_respond")
        graph_builder.add_conditional_edges(
            "query_or_respond",
            tools_condition,
            {
                "tools": "tools",
                END: END
            }
        )
        graph_builder.add_edge("tools", "generate_answer")
        graph_builder.add_edge("generate_answer", END)
        
        # Compile graph
        self.graph = graph_builder.compile()
        print("✅ LangGraph đã sẵn sàng")
        
    def initialize(self):
        """Khởi tạo toàn bộ hệ thống"""
        print("=" * 60)
        print("🚀 KHỞI TẠO AGENTIC RAG CHATBOT")
        print("=" * 60)
        print(f"📁 File: {self.jsonl_file_path}")
        print(f"🧠 Model: {self.model_name}\n")
        
        documents = self.load_jsonl_data()
        self.create_vectorstore_and_retriever(documents)
        self.build_graph()
        
        print("\n" + "=" * 60)
        print("✅ CHATBOT ĐÃ SẴN SÀNG!")
        print("=" * 60 + "\n")
        
    def ask(self, question):
        """Hỏi chatbot"""
        if not self.graph:
            raise ValueError("Graph chưa được khởi tạo. Gọi initialize() trước.")
        
        # Chạy graph
        result = self.graph.invoke({
            "messages": [{"role": "user", "content": question}]
        })
        
        # Lấy response cuối cùng
        final_message = result["messages"][-1]
        answer = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        return {
            "answer": answer,
            "messages": result["messages"]
        }
    
    def chat(self):
        """Chế độ chat tương tác"""
        print("💬 CHẾ ĐỘ CHAT TƯƠNG TÁC")
        print("-" * 60)
        print("Gõ câu hỏi và nhấn Enter")
        print("Gõ 'exit', 'quit' hoặc 'thoát' để kết thúc")
        print("-" * 60 + "\n")
        
        conversation_history = []
        
        while True:
            try:
                question = input("🧑 Bạn: ").strip()
                
                if question.lower() in ['exit', 'quit', 'thoát', 'q']:
                    print("\n👋 Tạm biệt!")
                    break
                
                if not question:
                    continue
                
                # Thêm vào lịch sử
                conversation_history.append({"role": "user", "content": question})
                
                # Hỏi chatbot
                result = self.graph.invoke({
                    "messages": conversation_history
                })
                
                # Lấy câu trả lời
                final_message = result["messages"][-1]
                answer = final_message.content if hasattr(final_message, 'content') else str(final_message)
                
                print(f"\n🤖 Bot: {answer}\n")
                print("-" * 60 + "\n")
                
                # Cập nhật lịch sử
                conversation_history = result["messages"]
                
            except KeyboardInterrupt:
                print("\n\n👋 Tạm biệt!")
                break
            except Exception as e:
                print(f"\n❌ Lỗi: {e}\n")


# ===== SỬ DỤNG =====
if __name__ == "__main__":
    # Khởi tạo chatbot
    chatbot = AgenticRAGChatbot(
        jsonl_file_path="data.jsonl",
        model_name="llama3.2"  # Hoặc: mistral, gemma2, qwen2.5
    )
    
    # Khởi tạo hệ thống
    chatbot.initialize()
    
    # Ví dụ hỏi đáp
    print("📝 TEST:\n")
    result = chatbot.ask("Python là gì?")
    print(f"Trả lời: {result['answer']}\n")
    
    # Chế độ chat
    chatbot.chat()