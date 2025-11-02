import os
import json
import logging
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import glob

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
                 persist_directory="./chroma_db"):
        
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
            
            # Split documents
            split_documents = self.text_splitter.split_documents(documents)
            logger.info(f"Total chunks after splitting: {len(split_documents)}")
            
            # SỬA QUAN TRỌNG: Đảm bảo embeddings được khởi tạo trước
            print(f"🔧 Đang tạo embeddings với model: {self.embedding_model_name}")
            
            # Create vector store - ĐẢM BẢO embeddings ĐÃ ĐƯỢC KHỞI TẠO
            self.vector_store = Chroma.from_documents(
                documents=split_documents,
                embedding=self.embeddings,  # Đảm bảo property này đã được khởi tạo
                persist_directory=self.persist_directory
            )
            
            # Kiểm tra ngay sau khi tạo
            doc_count = self.vector_store._collection.count()
            print(f"✅ Vector store được tạo với {doc_count} documents")
            
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
    
    def setup_vector_store2(self, data_directory: str):
        """Thiết lập vector store từ dữ liệu - SỬA THEO CÁCH CỦA DEBUG"""
        try:
            print("🔄 Starting vector store setup...")
            
            # 1. Load documents - GIỮ NGUYÊN
            documents = self.data_loader.load_all_data(data_directory)
            
            if not documents:
                raise ValueError("No documents found in the data directory")
            
            print(f"📊 Total documents loaded: {len(documents)}")
            
            # 2. Split documents - GIỮ NGUYÊN  
            split_documents = self.text_splitter.split_documents(documents)
            print(f"✂️ After splitting: {len(split_documents)} chunks")
            
            # 3. Tạo vector store - SỬA THEO DEBUG
            print("🗄️ Creating vector store...")
            
            # QUAN TRỌNG: Xóa thư mục cũ nếu tồn tại để tạo mới hoàn toàn
            if os.path.exists(self.persist_directory):
                import shutil
                print(f"🗑️ Removing existing vector store: {self.persist_directory}")
                shutil.rmtree(self.persist_directory)
            
            # SỬA: Sử dụng đúng cách như debug
            self.vector_store = Chroma.from_documents(
                documents=split_documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            # 4. Kiểm tra ngay - GIỮ NGUYÊN
            doc_count = self.vector_store._collection.count()
            print(f"✅ Vector store created with {doc_count} documents")
            
            # 5. Tạo retriever - ĐƠN GIẢN HÓA như debug
            self.retriever = self.vector_store.as_retriever(
                search_kwargs={"k": self.config.SEARCH_K}  # ĐƠN GIẢN, không cần search_type
            )
            
            # 6. Test retriever ngay - GIỮ NGUYÊN
            print("🧪 Testing retriever...")
            test_docs = self.retriever.invoke("Cần Thơ")
            print(f"   ✅ Retriever working, found {len(test_docs)} docs")
            
            # 7. Test với các câu hỏi cụ thể như debug
            print("\n🔍 Testing specific queries:")
            test_queries = [
                "Địa điểm check-in đẹp ở Cần Thơ?",
                "Cần Thơ có những món ăn ngon gì?",
                "Lịch trình 2 ngày ở Cần Thơ?"
            ]
            
            for query in test_queries:
                docs = self.retriever.invoke(query)
                print(f"   '{query}' -> {len(docs)} documents")
                for i, doc in enumerate(docs):
                    print(f"     {i+1}. {doc.metadata.get('title', 'N/A')}")
            
            # 8. Create QA chain - GIỮ NGUYÊN
            self.qa_chain = (
                {
                    "context": self.retriever, 
                    "question": RunnablePassthrough()
                }
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )
            
            print("🎉 Vector store setup completed successfully!")
            
        except Exception as e:
            logger.error(f"Error setting up vector store: {e}")
            print(f"❌ Error setting up vector store: {e}")
            import traceback
            traceback.print_exc()
            raise

    def load_existing_vector_store(self):
        """Load vector store đã tồn tại"""
        try:
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            
            # Create retriever
            self.retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={"k": self.config.SEARCH_K,"score_threshold": 0.5}
            )
            
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
            
            logger.info("Existing vector store loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading existing vector store: {e}")
            raise

    def load_existing_vector_store2(self):
        """Load vector store đã tồn tại - SỬA THEO CÁCH ĐƠN GIẢN"""
        try:
            print("📂 Loading existing vector store...")
            
            # SỬA: Khởi tạo đơn giản như debug
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            
            # Kiểm tra số lượng documents
            doc_count = self.vector_store._collection.count()
            print(f"✅ Loaded vector store with {doc_count} documents")
            
            # SỬA: Tạo retriever đơn giản
            self.retriever = self.vector_store.as_retriever(
                search_kwargs={"k": self.config.SEARCH_K}  # ĐƠN GIẢN, không cần search_type
            )
            
            # Test retriever ngay
            test_docs = self.retriever.invoke("Cần Thơ")
            print(f"🧪 Retriever test: found {len(test_docs)} documents")
            
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
            
            print("✅ Existing vector store loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading existing vector store: {e}")
            print(f"❌ Error loading vector store: {e}")
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
                print(f"   Title: {doc.metadata.get('title', 'N/A')}")
                print(f"   Type: {doc.metadata.get('type', 'N/A')}")
                print(f"   Content preview: {doc.page_content[:200]}...")
                print(f"   Similarity score: {getattr(doc, 'score', 'N/A')}")
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
            
    #         # TEST: Thử hỏi trực tiếp với context
    #         print("🧪 TEST: Thử hỏi trực tiếp với context...")
    #         context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
    #         test_prompt = f"""Dựa trên context dưới đây, hãy trả lời câu hỏi:

    # Context: {context}

    # Câu hỏi: {question}

    # Câu trả lời:"""
            
    #         test_response = self.llm.invoke(test_prompt)
    #         print(f"🧪 TEST Response: {test_response}")
            
    #         # Chạy QA chain chính thức
    #         answer = self.qa_chain.invoke(question)
            
    #         print(f"🔍 DEBUG: Câu trả lời từ chain: '{answer}'")
            
    #         # Kiểm tra xem có thông tin hữu ích không
    #         if not answer or "Hiện tại chưa có đủ dữ liệu" in answer:
    #             print("⚠️ DEBUG: Chain trả về thông báo không có dữ liệu")
    #             return {
    #                 "answer": "Hiện tại chưa có đủ dữ liệu về vấn đề này. Vui lòng liên hệ bộ phận hỗ trợ để được tư vấn thêm.",
    #                 "source_documents": []
    #             }
            
    #         logger.info("Question processed successfully")
            
    #         return {
    #             "answer": answer.strip(),
    #             "source_documents": [
    #                 {
    #                     "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
    #                     "metadata": doc.metadata
    #                 }
    #                 for doc in relevant_docs
    #             ]
    #         }
    #     except Exception as e:
    #         logger.error(f"Error processing question: {e}")
    #         print(f"❌ Lỗi chi tiết: {e}")
    #         import traceback
    #         traceback.print_exc()
    #         return {
    #             "answer": f"Có lỗi xảy ra khi xử lý câu hỏi: {str(e)}",
    #             "source_documents": []
    #         }

    def check_vector_store_status(self):
        """Kiểm tra trạng thái vector store"""
        if self.vector_store:
            try:
                doc_count = self.vector_store._collection.count()
                print(f"📊 Vector store status: {doc_count} documents")
                return doc_count
            except Exception as e:
                print(f"❌ Error checking vector store: {e}")
                return 0
        else:
            print("❌ Vector store not initialized")
            return 0