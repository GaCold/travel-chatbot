import os
import json
import glob
from typing import List
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    """Data loader for JSONL files"""
    
    def load_documents_from_jsonl(self, file_path: str) -> List[Document]:
        """Load documents từ file JSONL"""
        documents = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    content = f"Title: {data.get('title', '')}\nContent: {data.get('content', '')}"
                    metadata = {
                        "id": data.get("id", ""),
                        "type": data.get("type", ""),
                        "title": data.get("title", "")
                    }
                    documents.append(Document(page_content=content, metadata=metadata))
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
        return documents
    
    def load_documents_from_jsonl_V2(self, file_path: str) -> List[Document]:
        """Load documents từ file JSONL - TỐI ƯU CHO SEMANTIC SEARCH"""
        documents = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    
                    content = f"""
TITLE: {data.get('title', '')}
DESTINATION: {data.get('destination_name', '')}
DESCRIPTION: {data.get('description', '')}
REGION: {data.get('region', '')}
CONTENT: {data.get('content', '')}
SOURCE: {data.get('source', '')}
"""

                    
                    metadata = {
                        "id": data.get("id", ""),
                        "type": data.get("type", ""),
                        "title": data.get("title", ""),
                        "destination": data.get("destination_name", ""),
                        "source": data.get("source", ""),
                        "region": data.get("region", ""),
                        "file": os.path.basename(file_path)
                    }
                    
                    documents.append(Document(page_content=content, metadata=metadata))
                        
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
        return documents
    
    def load_all_data(self, data_directory: str) -> List[Document]:
        """Load tất cả dữ liệu từ thư mục data"""
        all_documents = []
        jsonl_files = glob.glob(os.path.join(data_directory, "**", "*.jsonl"), recursive=True)
        
        print(f"📁 Found {len(jsonl_files)} JSONL files")
        
        for file_path in jsonl_files:
            documents = self.load_documents_from_jsonl_updated(file_path)
            all_documents.extend(documents)
            print(f"   📄 {os.path.basename(file_path)}: {len(documents)} documents")
        
        print(f"📊 Total documents loaded: {len(all_documents)}")
        return all_documents
    

    def load_documents_from_jsonl_updated(self, file_path: str) -> List[Document]:
        """
        Load documents từ file JSONL đã crawl (chatbot_data.jsonl).
        Tối ưu cho "TÌM KIẾM LAI" (Hybrid Search).
        
        - page_content: Chỉ chứa nội dung text thuần túy (data['content']) 
                        để tạo vector ngữ nghĩa.
        - metadata:     Chứa TOÀN BỘ thông tin lọc (data['metadata'])
                        như region, type, location, images, v.v.
        """
        documents = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        
                        # 1. LẤY NỘI DUNG ĐỂ TẠO EMBEDDING
                        # Đây là phần text duy nhất sẽ được vector hóa.
                        # Nó đã chứa "Chủ đề: ..." nên rất giàu ngữ nghĩa.
                        page_content = data.get('content')
                        
                        # 2. LẤY TOÀN BỘ METADATA ĐỂ LỌC (FILTERING)
                        # Đây là "bộ não" của Hybrid Search.
                        # Vector DB sẽ dùng các key này để lọc trước khi tìm kiếm.
                        metadata = data.get('metadata', {})
                        
                        # (Tùy chọn) Thêm tên file JSONL nguồn vào metadata nếu cần
                        metadata['source_jsonl'] = os.path.basename(file_path)

                        if not page_content:
                            logger.warning(f"Bỏ qua dòng không có 'content' trong {file_path}")
                            continue
                            
                        # 3. TẠO DOCUMENT
                        # page_content sẽ được embed.
                        # metadata sẽ được lưu trữ để lọc.
                        documents.append(Document(page_content=page_content, metadata=metadata))
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Lỗi khi đọc một dòng trong {file_path}: {e}. Dòng: '{line.strip()}'")
                            
        except Exception as e:
            logger.error(f"Lỗi nghiêm trọng khi tải file {file_path}: {e}")
            
        logger.info(f"Đã tải thành công {len(documents)} chunks từ {file_path}")
        return documents