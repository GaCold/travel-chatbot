# Fix SQLite version issue for Chroma (uncomment nếu dùng Chroma)
# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import json
from typing import Annotated, Literal
from typing_extensions import TypedDict

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS  # Hoặc: Chroma
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
        """Đọc và xử lý dữ liệu JSONL du lịch"""
        documents = []

        print("📂 Đang đọc file JSONL...")
        try:
            # First try with utf-8-sig to handle BOM
            with open(self.jsonl_file_path, "r", encoding="utf-8-sig") as f:
                for idx, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            doc_type = data.get("type", "unknown")
                            dest = data.get("destination_name", "Unknown")
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Error decoding JSON on line {idx}: {e}")
                            continue
        except UnicodeDecodeError:
            print("⚠️ UTF-8-sig encoding failed, trying UTF-8...")
            # Try again with regular UTF-8
            with open(self.jsonl_file_path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            doc_type = data.get("type", "unknown")
                            dest = data.get("destination_name", "Unknown")
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Error decoding JSON on line {idx}: {e}")
                            continue

                        # Xử lý theo từng loại document
                        content = ""
                        if doc_type == "overview":
                            content = f"📋 TỔNG QUAN - {dest}\n"
                            content += f"Mô tả: {data.get('description', '')}\n"
                            if "highlights" in data:
                                content += f"Điểm nổi bật: {', '.join(data['highlights'])}\n"
                            if "best_for" in data:
                                content += f"Phù hợp cho: {', '.join(data['best_for'])}"

                        elif doc_type == "best_time":
                            content = f"🌤️ THỜI GIAN ĐẾN - {dest}\n"
                            content += f"Tháng tốt nhất: {', '.join(data.get('best_months', []))}\n"
                            content += f"Mùa khô: {data.get('dry_season', '')}\n"
                            content += f"Mùa mưa: {data.get('rainy_season', '')}\n"
                            content += f"Lưu ý thời tiết: {data.get('weather_note', '')}"

                        elif doc_type == "attraction":
                            content = (
                                f"📍 ĐỊA ĐIỂM THAM QUAN - {data.get('name', '')}\n"
                            )
                            content += f"Địa điểm: {dest}\n"
                            content += f"Loại: {data.get('category', '')}\n"
                            content += f"Quận: {data.get('district', '')}\n"
                            content += f"Mô tả: {data.get('description', '')}\n"
                            content += f"Giá vé: {data.get('entry_fee', '')}\n"
                            content += f"Giờ mở cửa: {data.get('opening_hours', '')}\n"
                            content += f"Thời gian cần: {data.get('time_needed', '')}\n"
                            if "tips" in data:
                                content += f"Tips: {data['tips']}"

                        elif doc_type == "photo_spot":
                            content = f"📸 ĐIỂM CHECK-IN - {data.get('name', '')}\n"
                            content += f"Địa điểm: {dest}\n"
                            content += f"Loại: {data.get('spot_type', '')}\n"
                            content += (
                                f"Thời gian đẹp nhất: {data.get('best_time', '')}\n"
                            )
                            content += f"Góc chụp: {data.get('photo_angle', '')}\n"
                            content += f"Phong cách: {data.get('vibe', '')}\n"
                            if "tip" in data:
                                content += f"Tips: {data['tip']}"

                        elif doc_type == "food":
                            content = f"🍜 MÓN ĂN - {data.get('name', '')}\n"
                            content += f"Địa điểm: {dest}\n"
                            content += f"Mô tả: {data.get('description', '')}\n"
                            content += f"Giá: {data.get('price_range', '')}\n"
                            if "recommended_places" in data:
                                content += "Quán gợi ý:\n"
                                for place in data["recommended_places"]:
                                    content += f"- {place.get('name', '')}: {place.get('address', '')}\n"
                            if "tip" in data:
                                content += f"Tips: {data['tip']}"

                        elif doc_type == "accommodation":
                            content = f"🏨 NƠI LƯU TRÚ - {data.get('name', '')}\n"
                            content += f"Địa điểm: {dest}\n"
                            content += f"Loại: {data.get('accom_type', '')}\n"
                            content += f"Giá: {data.get('price', data.get('price_range', ''))}\n"
                            content += f"Địa chỉ: {data.get('address', '')}\n"
                            if "amenities" in data:
                                content += f"Tiện ích: {', '.join(data['amenities'])}\n"
                            if "booking" in data:
                                content += f"Đặt phòng: {data['booking']}"

                        elif doc_type == "transportation":
                            mode = data.get("mode", "unknown")
                            content = f"🚗 PHƯƠNG TIỆN - {mode.upper()}\n"
                            content += f"Địa điểm: {dest}\n"
                            for key, value in data.items():
                                if key not in [
                                    "type",
                                    "destination_name",
                                    "mode",
                                    "tags",
                                    "keywords",
                                ]:
                                    if isinstance(value, list):
                                        content += f"{key}: {', '.join(value)}\n"
                                    else:
                                        content += f"{key}: {value}\n"

                        else:
                            # Fallback cho các type khác
                            content = json.dumps(data, ensure_ascii=False, indent=2)

                        # Metadata
                        metadata = {
                            "type": doc_type,
                            "destination": dest,
                            "source": f"line_{idx}",
                        }

                        documents.append(
                            Document(page_content=content, metadata=metadata)
                        )

                        # Metadata
                        metadata = {
                            "type": doc_type,
                            "destination": dest,
                            "source": f"line_{idx}",
                        }

                        documents.append(
                            Document(page_content=content, metadata=metadata)
                        )

        print(f"✅ Đã tải {len(documents)} documents")

        # Thống kê
        type_counts = {}
        for doc in documents:
            doc_type = doc.metadata.get("type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

        print(f"\n📊 Thống kê theo loại:")
        for doc_type, count in sorted(type_counts.items()):
            print(f"   {doc_type}: {count}")

        return documents

    def create_vectorstore_and_retriever(self, documents):
        """Tạo vector store và retriever tool"""
        import os
        
        # Kiểm tra xem đã có vector store chưaaaaaa
        if os.path.exists("./faiss_index") and os.path.exists("./faiss_index/index.faiss"):
            print("📦 Tìm thấy vector store đã tồn tại, đang load...")
            try:
                embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                )
                self.vectorstore = FAISS.load_local(
                    "./faiss_index",
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                print("✅ Đã load vector store từ disk")
            except Exception as e:
                print(f"⚠️  Không thể load, sẽ tạo mới: {e}")
                self._create_new_vectorstore(documents)
        else:
            print("🔨 Đang tạo vector store mới...")
            self._create_new_vectorstore(documents)
        
        # Tạo retriever tool
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 5}
        )
        
        self.retriever_tool = create_retriever_tool(
            retriever,
            "retrieve_travel_info",
            "Tìm kiếm thông tin chi tiết về du lịch Việt Nam từ cơ sở dữ liệu."
        )
        print("✅ Retriever tool đã sẵn sàng")

    def _create_new_vectorstore(self, documents):
        """Tạo mới vector store"""
        # Chia nhỏ documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=100, separators=["\n\n", "\n", ". ", " ", ""]
        )
        splits = text_splitter.split_documents(documents)
        print(f"✅ Đã chia thành {len(splits)} chunks")

        # Tạo embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

        # Tạo vector store - KHÔNG CÓ persist_directory
        self.vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)

        # Lưu xuống disk
        try:
            self.vectorstore.save_local("./faiss_index")
            print("✅ Vector store đã được lưu tại ./faiss_index")
        except Exception as e:
            print(f"⚠️  Không thể lưu vector store: {e}")

    def build_graph(self):
        """Xây dựng LangGraph với agentic RAG"""
        print("🔧 Đang xây dựng LangGraph...")

        # Khởi tạo LLM với tools
        self.llm = ChatOllama(model=self.model_name, temperature=0.7)
        llm_with_tools = self.llm.bind_tools([self.retriever_tool])

        # Node 1: Query hoặc Respond
        def query_or_respond(state: State):
            """Agent luôn retrieve thông tin từ database"""
            messages = state["messages"]
            
            # Tạo prompt để buộc model luôn retrieve
            system_msg = """Bạn là agent du lịch. Nhiệm vụ của bạn là:
1. Đọc câu hỏi người dùng
2. TÌM KIẾM thông tin từ tool retrieve_travel_info
3. LUÔN sử dụng tool để tìm kiếm, ngay cả khi bạn có thể biết câu trả lời

Luôn gọi tool retrieve_travel_info trước khi trả lời."""

            messages_with_system = [{"role": "system", "content": system_msg}] + messages
            response = llm_with_tools.invoke(messages_with_system)
            return {"messages": [response]}

        # Node 2: Generate answer
        def generate_answer(state: State):
            """Tạo câu trả lời cuối cùng dựa trên context"""
            messages = state["messages"]

            # Lấy tool results (retrieved documents)
            tool_results = [
                msg for msg in messages 
                if hasattr(msg, "tool_call_id") and msg.type == "tool"
            ]

            # Kiểm tra xem có dữ liệu được retrieve hay không
            if not tool_results:
                # Không có dữ liệu được retrieve - từ chối trả lời
                return {
                    "messages": [
                        {"role": "assistant", "content": "❌ Xin lỗi, tôi không tìm thấy thông tin liên quan trong dữ liệu du lịch của mình. Vui lòng hỏi về các địa điểm tại TP.HCM hoặc các vùng miền khác ở Việt Nam."}
                    ]
                }

            # Nếu có dữ liệu, tạo prompt bắt buộc dùng context
            system_prompt = """Bạn là trợ lý du lịch Việt Nam thông minh và nhiệt tình. 

⚠️ HƯỚNG DẪN QUAN TRỌNG:
- BẮT BUỘC chỉ sử dụng thông tin từ tài liệu được cung cấp (tool results)
- KHÔNG ĐƯỢC dùng kiến thức bên ngoài hoặc tự sinh ra thông tin
- Nếu tài liệu không đủ chi tiết, hãy nói rõ điều đó
- Trả lời bằng tiếng Việt thân thiện và dễ hiểu
- Luôn trích dẫn nguồn thông tin từ tài liệu

Nội dung tài liệu được cung cấp:
{tool_context}"""

            # Trích xuất context từ tool results
            tool_context = "\n\n".join([
                f"[{i+1}] {msg.content}" 
                for i, msg in enumerate(tool_results)
            ])

            system_prompt = system_prompt.format(tool_context=tool_context)

            response = self.llm.invoke(
                [{"role": "system", "content": system_prompt}, *messages]
            )
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
            {"tools": "tools", END: END}
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
        result = self.graph.invoke(
            {"messages": [{"role": "user", "content": question}]}
        )

        # Lấy response cuối cùng
        final_message = result["messages"][-1]
        answer = (
            final_message.content
            if hasattr(final_message, "content")
            else str(final_message)
        )

        # Kiểm tra và làm sạch tiếng Trung
        answer = self._clean_chinese_text(answer)

        # Debug: In thông tin về retrieval
        tool_messages = [msg for msg in result["messages"] if hasattr(msg, "tool_call_id")]
        
        return {
            "answer": answer, 
            "messages": result["messages"],
            "retrieved_docs_count": len(tool_messages)
        }

    def ask_with_history(self, question, conversation_history=None):
        """Hỏi chatbot với lịch sử hội thoại"""
        if not self.graph:
            raise ValueError("Graph chưa được khởi tạo. Gọi initialize() trước.")

        # Nếu không có lịch sử, tạo mới
        if conversation_history is None:
            conversation_history = []

        # Thêm câu hỏi mới vào lịch sử
        conversation_history.append({"role": "user", "content": question})

        # Chạy graph với lịch sử
        result = self.graph.invoke({"messages": conversation_history})

        # Lấy câu trả lời
        final_message = result["messages"][-1]
        answer = (
            final_message.content
            if hasattr(final_message, "content")
            else str(final_message)
        )

        # Làm sạch tiếng Trung
        answer = self._clean_chinese_text(answer)

        # Debug: In thông tin về retrieval
        tool_messages = [msg for msg in result["messages"] if hasattr(msg, "tool_call_id")]

        return {
            "answer": answer, 
            "messages": result["messages"],
            "conversation_history": result["messages"],
            "retrieved_docs_count": len(tool_messages)
        }

    def _clean_chinese_text(self, text):
        """Loại bỏ hoặc cảnh báo nếu có tiếng Trung"""
        import re

        # Pattern để detect tiếng Trung
        chinese_pattern = re.compile(r"[\u4e00-\u9fff]+")

        if chinese_pattern.search(text):
            # Tìm thấy tiếng Trung, xử lý
            chinese_parts = chinese_pattern.findall(text)

            # Xóa phần tiếng Trung
            cleaned_text = chinese_pattern.sub("", text).strip()

            # Nếu sau khi xóa còn nội dung tiếng Việt
            if len(cleaned_text) > 20:
                return cleaned_text
            else:
                # Nếu toàn bộ là tiếng Trung, trả lời mặc định
                return "Xin lỗi, tôi không có thông tin về điều này trong dữ liệu du lịch của mình. Tôi chỉ có thông tin về các địa điểm tại: TP.HCM, Phú Quốc, Đà Nẵng, Hội An, Hà Nội, Hạ Long, Sapa và các vùng miền Việt Nam. Bạn muốn biết về địa điểm nào?"

        return text

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

                if question.lower() in ["exit", "quit", "thoát", "q"]:
                    print("\n👋 Tạm biệt!")
                    break

                if not question:
                    continue

                # Thêm vào lịch sử
                conversation_history.append({"role": "user", "content": question})

                # Hỏi chatbot
                result = self.graph.invoke({"messages": conversation_history})

                # Lấy câu trả lời
                final_message = result["messages"][-1]
                answer = (
                    final_message.content
                    if hasattr(final_message, "content")
                    else str(final_message)
                )

                # Làm sạch tiếng Trung
                answer = self._clean_chinese_text(answer)

                # Debug: Kiểm tra xem có retrieval hay không
                tool_messages = [
                    msg for msg in result["messages"] 
                    if hasattr(msg, "tool_call_id") and msg.type == "tool"
                ]

                print(f"\n🤖 Bot: {answer}\n")
                if tool_messages:
                    print(f"ℹ️  [Đã retrieve {len(tool_messages)} tài liệu]")
                else:
                    print("⚠️  [⚠️  CẢNH BÁO: Không retrieve dữ liệu từ database!]")
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
        model_name="llama3.2",  # Hoặc: mistral, gemma2, qwen2.5
    )

    # Khởi tạo hệ thống
    chatbot.initialize()

    # Ví dụ hỏi đáp
    print("📝 TEST:\n")
    result = chatbot.ask("Python là gì?")
    print(f"Trả lời: {result['answer']}\n")

    # Chế độ chat
    chatbot.chat()
