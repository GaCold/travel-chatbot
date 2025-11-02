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
            documents = self.load_documents_from_jsonl(file_path)
            all_documents.extend(documents)
            print(f"   📄 {os.path.basename(file_path)}: {len(documents)} documents")
        
        print(f"📊 Total documents loaded: {len(all_documents)}")
        return all_documents