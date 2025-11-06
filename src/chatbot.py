import os
import json
import logging
from typing import List, Dict, Any, Optional
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from .data_loader import DataLoader
from .config import Config
from .embedding_manager import EmbeddingManager
from .query_parser import QueryParser

logger = logging.getLogger(__name__)

class TravelChatbot:
    """Travel Chatbot for Can Tho tourism recommendations"""
    
    def __init__(self, 
                 llm_model="llama3.1", 
                 embedding_model_name="nomic-embed-text",
                 embedding_model_type="ollama",
                 persist_directory="./faiss_vietnamese_index"):
        
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
Bạn là trợ lý tư vấn du lịch hỗ trợ tư vấn lịch trình cũng như những địa diểm checkin nổi tiếng thuộc những địa điểm du lịch ở Việt Nam. 
HÃY TUÂN THỦ NGHIÊM NGẶT CÁC QUY TẮC SAU:

1. CHỈ trả lời câu hỏi dựa trên thông tin được cung cấp trong context bên dưới.
2. KHÔNG sử dụng kiến thức ngoài hay tự suy luận.

**QUY TẮC NGOẠI LỆ (TỔNG HỢP LỊCH TRÌNH):**
3. Nếu người dùng hỏi về "lịch trình" (ví dụ: "lịch trình 2 ngày", "kế hoạch đi chơi") VÀ context KHÔNG cung cấp lịch trình cụ thể, NHƯNG context CÓ cung cấp các địa điểm tham quan (attraction), ăn uống (food), hoặc hướng dẫn (guide) tại địa điểm đó:
    * HÃY TỰ TỔNG HỢP một lịch trình gợi ý logic (ví dụ: Ngày 1 Sáng - Chiều, Ngày 2 Sáng - Chiều).
    * Lịch trình này PHẢI CHỈ SỬ DỤNG các địa điểm, món ăn được đề cập trong context.
    * KHÔNG ĐƯỢC bịa thêm địa điểm, món ăn không có trong context.
    * Bắt đầu câu trả lời bằng: "Dạ, hiện tại tôi chưa có lịch trình cụ thể cho địa điểm này, tuy nhiên dựa trên các địa điểm tham quan và ẩm thực nổi bật, tôi có thể gợi ý cho bạn một lịch trình như sau:"

4. Nếu KHÔNG có thông tin liên quan trong context (context rỗng), hãy trả lời: "Hiện tại chưa có đủ dữ liệu về vấn đề này. Vui lòng liên hệ bộ phận hỗ trợ để được tư vấn thêm."

Trả lời với giọng điệu nhẹ nhàng, như là một tư vấn du lịch thân thiện và am hiểu về các địa điểm du lịch ở Việt Nam.

Context: {context}
Câu hỏi: {question}
Câu trả lời:<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        )
        
        logger.info(f"TravelChatbot initialized with LLM: {llm_model}, Embedding: {embedding_model_name}")
    
    def setup_vector_store(self, data_directory: str, persist_directory: str):
        """Thiết lập Chroma vector store từ dữ liệu với metadata filtering"""
        try:
            # Load documents
            documents = self.data_loader.load_all_data(data_directory)
            
            if not documents:
                raise ValueError("No documents found in the data directory")
            
            logger.info(f"Total documents loaded: {len(documents)}")
            
            # Tạo Chroma vector store với metadata
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=self.config.CHROMA_COLLECTION_NAME,
                persist_directory=persist_directory,
                collection_metadata={"hnsw:space": self.config.CHROMA_DISTANCE_FUNCTION}
            )
            
            print(f"✅ Đã tạo Chroma vector store tại: {persist_directory}")
            
            # Create retriever - sẽ được custom trong ask_question với filter
            self.retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": self.config.SEARCH_K, # Số lượng doc trả về (ví dụ: 4)
                    "fetch_k": 20,              # Lấy 20 doc, sau đó MMR chọn 4 doc đa dạng nhất
                    "lambda_mult": 0.6          # 0.5 = cân bằng, > 0.5 = ưu tiên đa dạng (diversity)
                }
            )
            
            # Test retriever
            print("🧪 Test retriever ngay sau khi tạo...")
            test_docs = self.retriever.invoke("Cần Thơ")
            print(f"✅ Retriever test: tìm thấy {len(test_docs)} documents")
            
            # Create QA chain - sẽ dùng custom retrieval trong ask_question
            self.qa_chain = (
                {
                    "context": lambda x: self._get_relevant_docs(x), 
                    "question": lambda x: x if isinstance(x, str) else x.get("question", "")
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
        """
        Lấy documents liên quan với CHIẾN LƯỢC LỌC DỰ PHÒNG (Fallback Filtering).
        """
        if not self.vector_store:
            return []

        parsed = self.query_parser.parse_query(question)
        docs = []

        # --- NỖ LỰC 1: LỌC CHÍNH XÁC (Địa điểm + Loại) ---
        strict_filter = self.query_parser.build_filter_dict(parsed)
        
        if strict_filter:
            print(f"🎯 Nỗ lực 1 (Lọc chính xác): {strict_filter}")
            # Dùng .as_retriever() để lọc, đây là cách chuẩn
            strict_retriever = self.vector_store.as_retriever(
                search_type="similarity", # Dùng similarity search chuẩn
                search_kwargs={
                    "k": self.config.SEARCH_K,
                    "filter": strict_filter
                }
            )
            docs = strict_retriever.invoke(question)
        
        # --- NỖ LỰC 2: LỌC DỰ PHÒNG (Chỉ lọc địa điểm, dùng MMR) ---
        # Điều kiện: (Lọc 1 không thấy) VÀ (câu hỏi có 'type' (ý định) rõ ràng, ví dụ "lịch trình", "ăn gì")
        if not docs and parsed.get("type"):
            print(f"   ...Không tìm thấy. Chuyển sang Nỗ lực 2 (Lọc dự phòng).")
            
            # Tạo bộ lọc dự phòng (chỉ giữ lại địa điểm)
            fallback_filters = parsed.get("filters", {}).copy()
            fallback_filters.pop("type", None) # Bỏ lọc 'type'
            # (Chúng ta cũng có thể bỏ các filter khác nếu muốn, ví dụ: duration)
            # fallback_filters.pop("duration", None) 

            fallback_where_clause = {}
            if fallback_filters:
                # Xây dựng lại filter CHỈ CÒN ĐỊA ĐIỂM
                temp_parsed = {"filters": fallback_filters}
                fallback_where_clause = self.query_parser.build_filter_dict(temp_parsed)

            if fallback_where_clause:
                print(f"🎯 Nỗ lực 2 (Chỉ lọc địa điểm, dùng MMR): {fallback_where_clause}")
                
                # === ĐÂY LÀ PHẦN SỬA LỖI ===
                # Lỗi TypeError là do similarity_search() không nhận 'search_type'.
                # Chúng ta PHẢI tạo một retriever mới với as_retriever()
                fallback_retriever_mmr = self.vector_store.as_retriever(
                    search_type="mmr", # Sử dụng MMR
                    search_kwargs={
                        "k": self.config.SEARCH_K,
                        "fetch_k": 20,
                        "lambda_mult": 0.7, # Ưu tiên sự đa dạng
                        "filter": fallback_where_clause # Áp dụng filter địa điểm
                    }
                )
                docs = fallback_retriever_mmr.invoke(question)
                # === KẾT THÚC SỬA LỖI ===
            else:
                # Nếu câu hỏi là "lịch trình" (ko có địa điểm) -> tìm kiếm bth
                docs = self.retriever.invoke(question) # Dùng retriever MMR mặc định (đã setup trong __init__)
        
        # Nếu không có filter nào ngay từ đầu (ví dụ: câu hỏi "chào bạn")
        elif not docs and not strict_filter:
             print(f"🎯 Nỗ lực 1 (Không có filter): Tìm kiếm cơ bản (dùng MMR).")
             docs = self.retriever.invoke(question) # Dùng retriever MMR mặc định

        return docs

    def ask_question(self, question: str) -> Dict[str, Any]:
        """Hỏi câu hỏi và nhận câu trả lời với metadata filtering"""
        if not self.vector_store:
            raise ValueError("Vector store chưa được khởi tạo. Hãy gọi setup_vector_store() trước.")
        
        try:
            logger.info(f"Processing question: {question}")
            print(f"🔍 Đang tìm kiếm với câu hỏi: '{question}'")
            
            # Parse query để detect metadata
            parsed_query = self.query_parser.parse_query(question)
            
            # === THAY ĐỔI NHỎ Ở ĐÂY (DEBUG) ===
            print(f"⚙️  Parsed query: "
                  f"region={parsed_query.get('region')}, "
                  f"type={parsed_query.get('type')}, "
                  f"city={parsed_query.get('location_city')}, "
                  f"specific={parsed_query.get('location_specific')}")
            # === KẾT THÚC THAY ĐỔI ===
            
            # Lấy các document liên quan với filter
            # Hàm _get_relevant_docs và build_filter_dict (đã sửa ở parser) sẽ tự động xử lý
            relevant_docs = self._get_relevant_docs(question) # Chỉ cần truyền question
            print(f"   Found {len(relevant_docs)} relevant document(s)")
            
            # DEBUG: Hiển thị nội dung các document tìm được
            for i, doc in enumerate(relevant_docs):
                print(f"📄 Document {i+1}:")
                print(f"   Title: {doc.metadata.get('article_title', 'N/A')}")
                print(f"   Region: {doc.metadata.get('region', 'N/A')}")
                print(f"   Type: {doc.metadata.get('type', 'N/A')}")
                # === THAY ĐỔI NHỎ Ở ĐÂY (DEBUG) ===
                print(f"   Location: {doc.metadata.get('location_city', 'N/A')} / {doc.metadata.get('location_specific', 'N/A')}")
                # === KẾT THÚC THAY ĐỔI ===
                print(f"   Topic: {doc.metadata.get('topic', 'N/A')[:100] if doc.metadata.get('topic') else 'N/A'}")
                print()
            
            # ... (Phần còn lại của hàm giữ nguyên) ...
            
            # Nếu không có document liên quan
            if not relevant_docs:
                print("❌ Không tìm thấy document nào liên quan")
                return {
                    "answer": "Hiện tại chưa có đủ dữ liệu về vấn đề này. Vui lòng liên hệ bộ phận hỗ trợ để được tư vấn thêm.",
                    "source_documents": []
                }
            
            # Tạo context từ relevant docs
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Chạy LLM với context và question
            prompt = self.prompt_template.format(context=context, question=question)
            answer = "okie" #self.llm.invoke(prompt)
            
            # Kiểm tra câu trả lời
            if not answer or "Hiện tại chưa có đủ dữ liệu" in answer:
                return {
                    "answer": "Hiện tại chưa có đủ dữ liệu về vấn đề này. Vui lòng liên hệ bộ phận hỗ trợ để được tư vấn thêm.",
                    "source_documents": []
                }
            
            return {
                "answer": answer.strip(),
                "source_documents": [
                    {
                        "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in relevant_docs
                ]
            }
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": f"Có lỗi xảy ra khi xử lý câu hỏi: {str(e)}",
                "source_documents": []
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
                persist_directory=persist_directory
            )
            
            # Tạo lại retriever
            self.retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": self.config.SEARCH_K,
                    "fetch_k": 20,
                    "lambda_mult": 0.6
                }
            )
            
            # Tạo lại QA chain
            self.qa_chain = (
                {
                    "context": lambda x: self._get_relevant_docs(x), 
                    "question": lambda x: x if isinstance(x, str) else x.get("question", "")
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
                print(f"✅ Vector store hoạt động tốt - Tìm thấy {len(test_results)} kết quả test")
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
            if hasattr(self, 'retriever') and self.retriever:
                retriever_test = self.retriever.invoke("test")
                print(f"🔍 Retriever hoạt động - tìm thấy {len(retriever_test)} documents")
            else:
                print("❌ Retriever chưa được khởi tạo")
            
            # Kiểm tra QA chain
            if hasattr(self, 'qa_chain') and self.qa_chain:
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
                "exists": os.path.exists(persist_directory)
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