import json
import logging
import os
import sys

import pysqlite3

sys.modules["sqlite3"] = pysqlite3
from typing import Any, Dict, List, Optional

from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import Config
from src.data_loader import DataLoader
from src.embedding_manager import EmbeddingManager
from src.query_parser import QueryParser

logger = logging.getLogger(__name__)


class TravelChatbot:
    """Travel Chatbot for Can Tho tourism recommendations"""

    def __init__(
        self,
        llm_model,
        embedding_model_name,
        embedding_model_type,
        persist_directory,
    ):

        self.config = Config()
        self.llm_model = llm_model
        self.embedding_model_name = embedding_model_name
        self.embedding_model_type = embedding_model_type
        self.persist_directory = persist_directory

        # Initialize embedding manager
        self.embedding_manager = EmbeddingManager(self.config)
        self.embeddings = self.embedding_manager.initialize_embeddings()

        # Initialize LLM
        self.llm = Ollama(model=llm_model, temperature=0.4)
        self.vector_store = None
        self.retriever = None
        self.qa_chain = None

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            length_function=len,
        )

        # Initialize data loader and query parser
        self.data_loader = DataLoader()
        self.query_parser = QueryParser()

        # Setup prompt template
        self.prompt_template = PromptTemplate.from_template(
            """<|start_header_id|>system<|end_header_id|>
Bạn là một hướng dẫn viên du lịch giàu kinh nghiệm tư vấn cho du khách về các điểm đến, lịch trình và đặc sản ở Việt Nam. 
HÃY TUÂN THỦ NGHIÊM NGẶT CÁC QUY TẮC SAU:

**QUY TẮC CHÍNH:**
1. CHỈ trả lời câu hỏi dựa trên thông tin được cung cấp trong context bên dưới.
2. KHÔNG sử dụng kiến thức ngoài hay tự suy luận.
3. Bắt đầu bằng một câu giới thiệu tự nhiên để mở đầu, như: "Rất vui được tư vấn cho bạn!", "Đây là những gợi ý tuyệt vời!", "Thật tuyệt vời khi bạn chọn...", v.v.
4. Trả lời một cách tự nhiên và thân thiện như một hướng dẫn viên thực tế, không vô thẳng vào nội dung.
5. Tổ chức thông tin rõ ràng, dễ đọc, sử dụng đoạn văn ngắn và danh sách gạch đầu dòng khi cần thiết.
6. Nếu KHÔNG có thông tin liên quan trong context, trả lời: "Hiện tại chưa có đủ dữ liệu về vấn đề này. Vui lòng liên hệ bộ phận hỗ trợ để được tư vấn thêm."
7. Giọng điệu nhẹ nhàng, thân thiện, nhiệt tình và am hiểu về du lịch Việt Nam.

Context: {context}
Câu hỏi: {question}
Câu trả lời:<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        )

        logger.info(
            f"TravelChatbot initialized with LLM: {llm_model}, Embedding: {embedding_model_name}"
        )

    def setup_vector_store(self, data_directory: str, persist_directory: str):
        """Thiết lập Chroma vector store từ dữ liệu với metadata filtering"""
        try:
            # Load documents
            documents = self.data_loader.load_all_data(data_directory)

            if not documents:
                raise ValueError("No documents found in the data directory")

            logger.info(f"Total documents loaded: {len(documents)}")
            documents = self.text_splitter.split_documents(documents)

            # Tạo Chroma vector store với metadata
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=self.config.CHROMA_COLLECTION_NAME,
                persist_directory=persist_directory,
                collection_metadata={
                    "hnsw:space": self.config.CHROMA_DISTANCE_FUNCTION
                },
            )

            print(f"✅ Đã tạo Chroma vector store tại: {persist_directory}")

            # Create retriever - sẽ được custom trong ask_question với filter
            self.retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": self.config.SEARCH_K,  # Số lượng doc trả về (ví dụ: 4)
                    "fetch_k": 10,  # Lấy 20 doc, sau đó MMR chọn 4 doc đa dạng nhất
                    "lambda_mult": 0.6,  # 0.5 = cân bằng, > 0.5 = ưu tiên đa dạng (diversity)
                },
            )

            # Test retriever
            print("🧪 Test retriever ngay sau khi tạo...")
            test_docs = self.retriever.invoke("Cần Thơ")
            print(f"✅ Retriever test: tìm thấy {len(test_docs)} documents")

            # Create QA chain - sẽ dùng custom retrieval trong ask_question
            self.qa_chain = (
                {
                    "context": lambda x: self._get_relevant_docs(x),
                    "question": lambda x: (
                        x if isinstance(x, str) else x.get("question", "")
                    ),
                }
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )

            logger.info("Chroma vector store setup completed successfully")

        except Exception as e:
            logger.error(f"Error setting up vector store: {e}")
            print(f"❌ Lỗi khi setup vector store: {e}")
            import traceback

            traceback.print_exc()
            raise
    
    def _get_relevant_docs(self, question: str):
        """Lấy documents liên quan với chiến lược fallback filtering."""
        if not self.vector_store:
            return []

        parsed = self.query_parser.parse_query(question)
        docs = []

        # EFFORT 1: Thử filter cụ thể (location_specific hoặc location_city)
        if parsed.get("filters"):
            filters = parsed["filters"]
            effort1_filter = None
            
            if filters.get("location_specific"):
                effort1_filter = {"location_specific": {"$eq": filters["location_specific"]}}
            elif filters.get("location_city"):
                effort1_filter = {"location_city": {"$eq": filters["location_city"]}}
            
            if effort1_filter:
                print(f"🎯 Nỗ lực 1 (Lọc location cụ thể): {effort1_filter}")
                retriever1 = self.vector_store.as_retriever(
                    search_type="mmr",
                    search_kwargs={
                        "k": self.config.SEARCH_K,
                        "fetch_k": 20,
                        "lambda_mult": 0.6,
                        "filter": effort1_filter,
                    },
                )
                docs = retriever1.invoke(question)
        
        # EFFORT 2: Nếu không tìm được location cụ thể, thử filter region
        if not docs and parsed.get("region"):
            print(f"   ...Không tìm thấy với location cụ thể. Chuyển sang Nỗ lực 2 (Lọc theo region).")
            region_filter = {"region": {"$eq": parsed["region"]}}
            print(f"🎯 Nỗ lực 2 (Lọc region): {region_filter}")
            retriever2 = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": self.config.SEARCH_K,
                    "fetch_k": 20,
                    "lambda_mult": 0.7,
                    "filter": region_filter,
                },
            )
            docs = retriever2.invoke(question)
        
        # EFFORT 3: Nếu vẫn không có, tìm kiếm không filter nhưng kiểm tra similarity score
        if not docs:
            print(f"🎯 Nỗ lực 3 (Tìm kiếm cơ bản với kiểm tra độ tương đồng).")
            # Sử dụng similarity_search_with_score để lấy kèm score
            results_with_scores = self.vector_store.similarity_search_with_score(question, k=self.config.SEARCH_K)
            
            # Lọc bỏ các kết quả có score quá cao (< 0.5) = không liên quan
            # Score nhỏ = tương đồng cao, score lớn = tương đồng thấp
            similarity_threshold = 0.5
            docs = [doc for doc, score in results_with_scores if score < similarity_threshold]
            
            if not docs:
                print(f"   ⚠️ Tất cả kết quả đều có độ tương đồng thấp (score > {similarity_threshold}). Không trả lại documents.")
            else:
                print(f"   ✅ Tìm thấy {len(docs)} documents có độ tương đồng cao (score < {similarity_threshold})")

        return docs

    async def ask_question(self, question: str) -> Dict[str, Any]:
        """Hỏi câu hỏi và nhận câu trả lời với metadata filtering"""
        if not self.vector_store:
            raise ValueError(
                "Vector store chưa được khởi tạo. Hãy gọi setup_vector_store() trước."
            )

        try:
            logger.info(f"Processing question: {question}")
            print(f"🔍 Đang tìm kiếm với câu hỏi: '{question}'")
            relevant_docs = self._get_relevant_docs(question)  # Chỉ cần truyền question
            print(f"   Found {len(relevant_docs)} relevant document(s)")
            print("📝 Relevant Documents Metadata:")
            for doc in relevant_docs:
                print(f"   - Topic: {doc.metadata.get('topic', 'N/A')}")
                print(f"     Source File: {doc.metadata.get('source_file', 'N/A')}")
            print("-----")
            # Nếu không có document liên quan
            if not relevant_docs:
                print("❌ Không tìm thấy document nào liên quan")
                return {
                    "answer": "Hiện tại chưa có đủ dữ liệu về vấn đề này. Vui lòng liên hệ bộ phận hỗ trợ để được tư vấn thêm.",
                    "source_documents": [],
                }

            # Tạo context từ relevant docs
            context = "\n\n".join([doc.page_content for doc in relevant_docs])

            # Chạy LLM với context và question
            prompt = self.prompt_template.format(context=context, question=question)
            answer = self.llm.invoke(prompt)

            # Kiểm tra xem LLM có refuse không (trả lời ko có data)
            # Chỉ override nếu LLM thực sự refuse, không phải vì câu trả lời có chứa từ khóa đó
            refused_responses = [
                "hiện tại chưa có đủ dữ liệu",
                "không có thông tin",
                "tôi không có thông tin",
                "xin lỗi, tôi không thể",
            ]
            
            is_refused = any(refused_phrase.lower() in answer.lower() for refused_phrase in refused_responses)
            
            if not answer or is_refused:
                return {
                    "answer": "Hiện tại chưa có đủ dữ liệu về vấn đề này. Vui lòng liên hệ bộ phận hỗ trợ để được tư vấn thêm.",
                    "source_documents": [],
                }

            return {
                "answer": answer.strip(),
                "source_documents": [
                    {
                        "topic": doc.metadata.get("topic", "N/A"),
                        "source_file" : doc.metadata.get("source_file", "N/A"),
                    }
                    for doc in relevant_docs
                ],
            }
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            import traceback

            traceback.print_exc()
            return {
                "answer": f"Có lỗi xảy ra khi xử lý câu hỏi: {str(e)}",
                "source_documents": [],
            }

    def load_existing_vector_store(self):
        """Tải Chroma vector store đã tồn tại"""
        try:
            persist_directory = self.config.PERSIST_DIRECTORY

            if not os.path.exists(persist_directory):
                print(f"❌ Không tìm thấy Chroma DB tại: {persist_directory}")
                return False

            print(f"🔄 Đang tải Chroma vector store từ: {persist_directory}")

            # Tải Chroma vector store
            self.vector_store = Chroma(
                collection_name=self.config.CHROMA_COLLECTION_NAME,
                embedding_function=self.embeddings,
                persist_directory=persist_directory,
            )

            # Tạo lại retriever
            self.retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": self.config.SEARCH_K,
                    "fetch_k": 20,
                    "lambda_mult": 0.6,
                },
            )

            # Tạo lại QA chain
            self.qa_chain = (
                {
                    "context": lambda x: self._get_relevant_docs(x),
                    "question": lambda x: (
                        x if isinstance(x, str) else x.get("question", "")
                    ),
                }
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )

            print("✅ Đã tải thành công Chroma vector store")
            return True

        except Exception as e:
            print(f"❌ Lỗi khi tải Chroma vector store: {e}")
            import traceback

            traceback.print_exc()
            return False

    def check_vector_store_status(self):
        """Kiểm tra trạng thái của Chroma vector store"""
        try:
            if not self.vector_store:
                print("❌ Vector store: Chưa được khởi tạo")
                return False

            persist_directory = self.config.PERSIST_DIRECTORY

            print("🔍 Kiểm tra trạng thái Chroma vector store...")

            # Kiểm tra thư mục tồn tại
            if os.path.exists(persist_directory):
                print(f"📁 Chroma DB directory: {persist_directory}")
            else:
                print(f"📁 Chroma DB: Không tồn tại tại {persist_directory}")
                return False

            # Thử tìm kiếm test để kiểm tra hoạt động
            print("🧪 Test tìm kiếm với từ khóa 'du lịch'...")
            test_results = self.vector_store.similarity_search("du lịch", k=1)

            if test_results:
                print(
                    f"✅ Vector store hoạt động tốt - Tìm thấy {len(test_results)} kết quả test"
                )
                print(f"📄 Document test: {test_results[0].page_content[:100]}...")
            else:
                print("⚠️ Vector store hoạt động nhưng không tìm thấy kết quả test")

            # Kiểm tra số lượng documents
            try:
                collection = self.vector_store._collection
                count = collection.count()
                print(f"📊 Tổng số documents trong collection: {count}")
            except:
                print("📊 Không thể đếm số documents")

            # Kiểm tra retriever
            if hasattr(self, "retriever") and self.retriever:
                retriever_test = self.retriever.invoke("test")
                print(
                    f"🔍 Retriever hoạt động - tìm thấy {len(retriever_test)} documents"
                )
            else:
                print("❌ Retriever chưa được khởi tạo")

            # Kiểm tra QA chain
            if hasattr(self, "qa_chain") and self.qa_chain:
                print("✅ QA chain đã sẵn sàng")
            else:
                print("❌ QA chain chưa được khởi tạo")

            return True

        except Exception as e:
            print(f"❌ Lỗi khi kiểm tra vector store: {e}")
            import traceback

            traceback.print_exc()
            return False

    def get_vector_store_info(self):
        """Lấy thông tin chi tiết về Chroma vector store"""
        try:
            if not self.vector_store:
                return {"status": "not_initialized"}

            persist_directory = self.config.PERSIST_DIRECTORY

            info = {
                "status": "active",
                "type": "Chroma",
                "persist_directory": persist_directory,
                "exists": os.path.exists(persist_directory),
            }

            # Đếm số documents
            try:
                collection = self.vector_store._collection
                info["document_count"] = collection.count()
            except:
                info["document_count"] = "unknown"

            # Collection info
            try:
                info["collection_name"] = self.config.CHROMA_COLLECTION_NAME
            except:
                pass

            return info

        except Exception as e:
            return {"status": f"error: {str(e)}"}
