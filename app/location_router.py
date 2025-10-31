import json
import os
import re
from typing import Optional
import unicodedata

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class LocationRouter:
    def __init__(
        self,
        db_root: str = "chroma_db",
        city_map_path: str = "./app/city_map.json",
        model_name: str = "llama3",
        embed_model: str = "nomic-embed-text",
    ):
        self.db_root = db_root
        self.model_name = model_name
        self.embed_model = embed_model

        # Load danh sách city và từ khóa
        with open(city_map_path, "r", encoding="utf-8") as f:
            self.city_keywords = json.load(f)

    # ----------------------------------------------------------------------
    def remove_accents(self, text: str) -> str:
        """Loại bỏ dấu tiếng Việt và chuyển về lowercase."""
        # Normalize về dạng NFD (tách ký tự và dấu)
        nfd = unicodedata.normalize('NFD', text)
        # Loại bỏ các ký tự dấu (combining characters)
        without_accents = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
        # Xử lý các trường hợp đặc biệt của tiếng Việt
        without_accents = without_accents.replace('đ', 'd').replace('Đ', 'd')
        return without_accents.lower()

    # ----------------------------------------------------------------------
    def detect_city_from_query(self, query: str) -> Optional[str]:
        """Xác định thành phố từ câu hỏi người dùng dựa vào từ khóa."""
        query_lower = query.lower()
        query_no_accent = self.remove_accents(query)
        
        for city_slug, keywords in self.city_keywords.items():
            for kw in keywords:
                kw_lower = kw.lower()
                kw_no_accent = self.remove_accents(kw)
                
                # Check với cả có dấu và không dấu
                # Pattern 1: Khớp chính xác với từ có dấu
                if re.search(rf"\b{re.escape(kw_lower)}\b", query_lower):
                    return city_slug
                
                # Pattern 2: Khớp với từ không dấu
                if re.search(rf"\b{re.escape(kw_no_accent)}\b", query_no_accent):
                    return city_slug
                
                # Pattern 3: Khớp không dấu và không space (vd: saigon, hanoi)
                kw_no_space = kw_no_accent.replace(" ", "")
                query_no_space = query_no_accent.replace(" ", "")
                if re.search(rf"\b{re.escape(kw_no_space)}\b", query_no_space):
                    return city_slug
        
        return None

    # ----------------------------------------------------------------------
    def get_retriever_for_city(self, city_slug: str):
        """Tạo retriever tương ứng với city."""
        db_path = os.path.join(self.db_root, city_slug)
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Không tìm thấy dữ liệu vector cho '{city_slug}'")

        embeddings = OllamaEmbeddings(model=self.embed_model)
        db = Chroma(persist_directory=db_path, embedding_function=embeddings)
        return db.as_retriever(search_kwargs={"k": 4})

    # ----------------------------------------------------------------------
    def format_docs(self, docs):
        """Format documents thành string."""
        return "\n\n".join(doc.page_content for doc in docs)

    # ----------------------------------------------------------------------
    def route_and_answer(self, query: str) -> str:
        """Xử lý route → truy vấn đúng DB → trả kết quả từ Ollama."""
        city_slug = self.detect_city_from_query(query)
        if not city_slug:
            return "Xin lỗi, tôi không có thông tin về địa điểm này."

        try:
            retriever = self.get_retriever_for_city(city_slug)
        except FileNotFoundError:
            return f"Xin lỗi, dữ liệu cho địa điểm '{city_slug}' chưa được khởi tạo."

        # Sử dụng LCEL (LangChain Expression Language) thay vì RetrievalQA
        llm = OllamaLLM(model=self.model_name)
        
        # Tạo prompt template
        template = """Sử dụng thông tin sau để trả lời câu hỏi:

{context}

Câu hỏi: {question}

Trả lời:"""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # Tạo RAG chain
        rag_chain = (
            {
                "context": retriever | self.format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        # Thực thi chain
        answer = rag_chain.invoke(query)

        return f"[{city_slug.upper()}] {answer}"