import os
import json
import logging
from typing import List, Dict, Any
from langchain_community.llms import Ollama
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from .data_loader import DataLoader
from .config import Config
from .embedding_manager import EmbeddingManager

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
        
        # Initialize data loader
        self.data_loader = DataLoader()
        
        # Setup prompt template
        self.prompt_template = PromptTemplate.from_template(
            """<|start_header_id|>system<|end_header_id|>
Bạn là trợ lý tư vấn du lịch hỗ trợ tư vấn lịch trình cũng như những địa diểm checkin nổi tiếng thuộc những địa điểm du lịch ở Việt Nam. 
HÃY TUÂN THỦ NGHIÊM NGẶT CÁC QUY TẮC SAU:

1. CHỈ trả lời câu hỏi dựa trên thông tin được cung cấp trong context bên dưới
2. KHÔNG sử dụng kiến thức ngoài hay tự suy luận
3. Nếu KHÔNG có thông tin liên quan trong context, hãy trả lời: "Hiện tại chưa có đủ dữ liệu về vấn đề này. Vui lòng liên hệ bộ phận hỗ trợ để được tư vấn thêm."

Trả lời với giọng điệu nhẹ nhàng, như là một tư vấn du lịch thân thiện và am hiểu về các địa điểm du lịch ở Việt Nam.


Context: {context}

Câu hỏi: {question}

Câu trả lời:<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        )
        
        logger.info(f"TravelChatbot initialized with LLM: {llm_model}, Embedding: {embedding_model_name}")
    
    def setup_vector_store(self, data_directory: str):
        """Thiết lập vector store từ dữ liệu"""
        try:
            # Load documents
            documents = self.data_loader.load_all_data(data_directory)
            
            if not documents:
                raise ValueError("No documents found in the data directory")
            
            logger.info(f"Total documents loaded: {len(documents)}")

            self.vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings,
            )

            self.vector_store.save_local("./faiss_vietnamese_index")
            
            # Create retriever
            self.retriever = self.vector_store.as_retriever(
                search_type="mmr", #"mmr",
                search_kwargs={
                    "k": self.config.SEARCH_K,
                    "score_threshold": 0.5,
                    # "fetch_k": 10, 
                    # "lambda_mult": 0.7
                }
            )
            
            # Test retriever ngay
            print("🧪 Test retriever ngay sau khi tạo...")
            test_docs = self.retriever.invoke("Cần Thơ")
            print(f"✅ Retriever test: tìm thấy {len(test_docs)} documents")
            
            # Create QA chain
            self.qa_chain = (
                {
                    "context": self.retriever, 
                    "question": RunnablePassthrough()
                }
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )
            
            logger.info("Vector store setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error setting up vector store: {e}")
            print(f"❌ Lỗi khi setup vector store: {e}")
            import traceback
            traceback.print_exc()
            raise


    def ask_question(self, question: str) -> Dict[str, Any]:
        """Hỏi câu hỏi và nhận câu trả lời"""
        if not self.qa_chain:
            raise ValueError("Vector store chưa được khởi tạo. Hãy gọi setup_vector_store() trước.")
        
        try:
            logger.info(f"Processing question: {question}")
            
            # DEBUG: Kiểm tra retriever
            print(f"🔍 DEBUG: Đang tìm kiếm với câu hỏi: '{question}'")
            
            # Lấy các document liên quan
            relevant_docs = self.retriever.invoke(question)
            print(f"   Found {len(relevant_docs)} relevant document(s)")
            
            # DEBUG: Hiển thị nội dung các document tìm được
            for i, doc in enumerate(relevant_docs):
                print(f"📄 Document {i+1}:")
                print(f"   Title: {doc.metadata.get('article_title', 'N/A')}")
                print(f"   Type: {doc.metadata.get('type', 'N/A')}")
                print(f"   topic: {doc.metadata.get('topic')[:100]}")
                print()
            
            # Nếu không có document liên quan
            if not relevant_docs:
                print("❌ DEBUG: Không tìm thấy document nào liên quan")
                return {
                    "answer": "Hiện tại chưa có đủ dữ liệu về vấn đề này. Vui lòng liên hệ bộ phận hỗ trợ để được tư vấn thêm.",
                    "source_documents": []
                }
            # Chạy QA chain
            answer = self.qa_chain.invoke(question)
            
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
            return {
                "answer": f"Có lỗi xảy ra khi xử lý câu hỏi: {str(e)}",
                "source_documents": []
            }
        
    def load_existing_vector_faiss_store(self):
        """Tải vector store đã tồn tại từ FAISS index"""
        try:
            # Kiểm tra xem FAISS index có tồn tại không
            index_path = "./faiss_vietnamese_index"
            if not os.path.exists(index_path):
                print("❌ Không tìm thấy FAISS index. Cần tạo mới vector store.")
                return False
            
            # Kiểm tra các file cần thiết
            required_files = ['index.faiss', 'index.pkl']
            for file in required_files:
                if not os.path.exists(os.path.join(index_path, file)):
                    print(f"❌ Thiếu file {file} trong FAISS index")
                    return False
            
            print("🔄 Đang tải FAISS vector store từ index...")
            
            # Tải FAISS index
            self.vector_store = FAISS.load_local(
                folder_path=index_path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True  # Quan trọng với FAISS
            )
            
            # Tạo lại retriever và QA chain
            self.retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": self.config.SEARCH_K,
                    "score_threshold": 0.5,
                }
            )
            
            self.qa_chain = (
                {
                    "context": self.retriever, 
                    "question": RunnablePassthrough()
                }
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )
            
            print("✅ Đã tải thành công FAISS vector store từ index")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi tải FAISS vector store: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def check_vector_store_faiss_status(self):
            """Kiểm tra trạng thái của vector store"""
            try:
                if not self.vector_store:
                    print("❌ Vector store: Chưa được khởi tạo")
                    return False
                
                # Kiểm tra FAISS index
                index_path = "./faiss_vietnamese_index"
                
                print("🔍 Kiểm tra trạng thái vector store...")
                
                # Kiểm tra file tồn tại
                if os.path.exists(index_path):
                    faiss_files = os.listdir(index_path)
                    print(f"📁 FAISS index files: {faiss_files}")
                else:
                    print("📁 FAISS index: Không tồn tại")
                    return False
                
                # Thử tìm kiếm test để kiểm tra hoạt động
                print("🧪 Test tìm kiếm với từ khóa 'du lịch'...")
                test_results = self.vector_store.similarity_search("du lịch", k=1)
                
                if test_results:
                    print(f"✅ Vector store hoạt động tốt - Tìm thấy {len(test_results)} kết quả test")
                    print(f"📄 Document test: {test_results[0].page_content[:100]}...")
                else:
                    print("⚠️ Vector store hoạt động nhưng không tìm thấy kết quả test")
                
                # Kiểm tra số lượng documents (ước lượng)
                try:
                    # FAISS không có method count() trực tiếp, dùng ước lượng
                    test_count = self.vector_store.similarity_search("test", k=100)
                    print(f"📊 Số documents ước lượng: >={len(test_count)}")
                except:
                    print("📊 Không thể ước lượng số documents")
                
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
    
    def get_vector_store_faiss_info(self):
        """Lấy thông tin chi tiết về vector store"""
        try:
            if not self.vector_store:
                return {"status": "not_initialized"}
            
            info = {
                "status": "active",
                "type": "FAISS",
                "index_path": "./faiss_vietnamese_index",
                "index_exists": os.path.exists("./faiss_vietnamese_index")
            }
            
            # Kiểm tra files
            if info["index_exists"]:
                files = os.listdir("./faiss_vietnamese_index")
                info["files"] = files
                info["file_count"] = len(files)
            
            # Ước lượng số documents
            try:
                test_docs = self.vector_store.similarity_search("test", k=100)
                info["estimated_documents"] = f">={len(test_docs)}"
            except:
                info["estimated_documents"] = "unknown"
            
            return info
            
        except Exception as e:
            return {"status": f"error: {str(e)}"}