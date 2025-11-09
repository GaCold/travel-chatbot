import glob
import json
import logging
import os
from typing import List

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class DataLoader:
    """Data loader for JSONL files"""

    def load_all_data(self, data_directory: str) -> List[Document]:
        """Load tất cả dữ liệu từ thư mục data"""
        all_documents = []
        jsonl_files = glob.glob(
            os.path.join(data_directory, "**", "*.jsonl"), recursive=True
        )

        print(f"📁 Found {len(jsonl_files)} JSONL files")

        for file_path in jsonl_files:
            documents = self.load_documents_from_jsonl(file_path)
            all_documents.extend(documents)
            print(f"   📄 {os.path.basename(file_path)}: {len(documents)} documents")

        print(f"📊 Total documents loaded: {len(all_documents)}")
        return all_documents

    def load_documents_from_jsonl(self, file_path: str) -> List[Document]:
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
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        # 1. LẤY NỘI DUNG ĐỂ TẠO EMBEDDING
                        # Đây là phần text duy nhất sẽ được vector hóa.
                        # Nó đã chứa "Chủ đề: ..." nên rất giàu ngữ nghĩa.
                        page_content = data.get("content")

                        # 2. LẤY TOÀN BỘ METADATA ĐỂ LỌC (FILTERING)
                        # Đây là "bộ não" của Hybrid Search.
                        # Vector DB sẽ dùng các key này để lọc trước khi tìm kiếm.
                        metadata = data.get("metadata", {})

                        # QUAN TRỌNG: Chroma chỉ hỗ trợ metadata: str, int, float, bool, None
                        # Phải chuyển đổi list/dict thành string
                        cleaned_metadata = self._clean_metadata_for_chroma(metadata)

                        # Thêm tên file JSONL nguồn vào metadata
                        cleaned_metadata["source_jsonl"] = os.path.basename(file_path)

                        if not page_content:
                            logger.warning(
                                f"Bỏ qua dòng không có 'content' trong {file_path}"
                            )
                            continue

                        # 3. TẠO DOCUMENT
                        # page_content sẽ được embed.
                        # metadata sẽ được lưu trữ để lọc.
                        documents.append(
                            Document(
                                page_content=page_content, metadata=cleaned_metadata
                            )
                        )

                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Lỗi khi đọc một dòng trong {file_path}: {e}. Dòng: '{line.strip()}'"
                        )

        except Exception as e:
            logger.error(f"Lỗi nghiêm trọng khi tải file {file_path}: {e}")

        logger.info(f"Đã tải thành công {len(documents)} chunks từ {file_path}")
        return documents

    def _clean_metadata_for_chroma(self, metadata: dict) -> dict:
        """
        Làm sạch metadata để tương thích với Chroma.
        Chroma chỉ chấp nhận: str, int, float, bool, None

        Phiên bản này tối ưu cách xử lý list:
        - List các giá trị đơn (str, int...) sẽ được nối (join).
        - List các giá trị phức tạp (dict...) sẽ được chuyển thành chuỗi JSON.
        """
        cleaned = {}

        for key, value in metadata.items():
            if value is None:
                cleaned[key] = None
            elif isinstance(value, (str, int, float, bool)):
                # Giữ nguyên các kiểu hợp lệ
                cleaned[key] = value
            elif isinstance(value, list):
                if not value:
                    cleaned[key] = ""
                # Kiểm tra xem list này chứa giá trị đơn hay phức tạp
                elif all(
                    isinstance(item, (str, int, float, bool, type(None)))
                    for item in value
                ):
                    # List các giá trị đơn (ví dụ: "alias": ["a", "b"])
                    str_items = [str(item) for item in value if item is not None]
                    cleaned[key] = ", ".join(str_items)
                else:
                    # List các giá trị phức tạp (ví dụ: "images": [{"src":...}])
                    # Chuyển cả list thành một chuỗi JSON
                    try:
                        cleaned[key] = json.dumps(value, ensure_ascii=False)
                    except TypeError:
                        # Fallback nếu có lỗi serialization
                        cleaned[key] = str(value)
            elif isinstance(value, dict):
                # Chuyển dict thành JSON string
                try:
                    cleaned[key] = json.dumps(value, ensure_ascii=False)
                except TypeError:
                    cleaned[key] = str(value)
            else:
                # Các kiểu khác: chuyển thành string
                cleaned[key] = str(value)

        return cleaned
