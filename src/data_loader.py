import glob
import json
import os
from typing import List

from langchain_core.documents import Document

from src.log import logger


class DataLoader:

    def load_all_data(self, data_directory: str) -> List[Document]:
        """
        Recursively load all JSONL documents from data directory and subdirectories.

        Scans the provided directory for all .jsonl files (recursive) and loads them
        as LangChain Document objects. Each document contains both semantic content
        for embedding and metadata for filtering.

        Args:
            data_directory (str): Path to the directory containing JSONL files.
                Can have nested subdirectories (glob uses recursive=True).

        Returns:
            List[Document]: List of LangChain Document objects loaded from all JSONL files.
                Each Document has:
                - page_content: Text content for vector embedding
                - metadata: Dictionary with region, type, location, source info, etc.

        Example:
            >>> loader = DataLoader()
            >>> docs = loader.load_all_data("./data")
            >>> print(f"Loaded {len(docs)} documents")
            >>> print(docs[0].metadata['region'])
        """
        all_documents = []
        jsonl_files = glob.glob(
            os.path.join(data_directory, "**", "*.jsonl"), recursive=True
        )

        logger.info(f"📁 Found {len(jsonl_files)} JSONL files")

        for file_path in jsonl_files:
            documents = self.load_documents_from_jsonl(file_path)
            all_documents.extend(documents)
            logger.info(
                f"   📄 {os.path.basename(file_path)}: {len(documents)} documents"
            )

        logger.info(f"📊 Total documents loaded: {len(all_documents)}")
        return all_documents

    def load_documents_from_jsonl(self, file_path: str) -> List[Document]:
        """
        Load and parse documents from a JSONL file, optimized for hybrid search.

        Reads JSONL file (one JSON object per line) and converts each line into
        a LangChain Document. Separates content for embedding (semantic) from
        metadata for filtering (region, type, location, etc.).

        Structure:
        - page_content: Raw text from 'content' field (vectorized for semantic search)
        - metadata: All fields from 'metadata' object + source_jsonl filename

        Metadata is cleaned to ensure Chroma compatibility (only str, int, float, bool, None).
        Lists are joined/serialized; dicts are converted to JSON strings.

        Args:
            file_path (str): Path to JSONL file to load.

        Returns:
            List[Document]: List of LangChain Document objects from the file.
                Empty list if file doesn't exist or has errors.

        Raises:
            Logs errors for invalid JSON lines but continues processing.
            Returns partial results if some lines fail.

        Example:
            >>> loader = DataLoader()
            >>> docs = loader.load_documents_from_jsonl("./data/vnexpress.jsonl")
            >>> print(docs[0].page_content[:100])  # First 100 chars of content
            >>> print(docs[0].metadata['region'])  # Access metadata for filtering
        """
        documents = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        # 1. GET CONTENT FOR EMBEDDING
                        # This is the only text that will be vectorized.
                        # It already contains "Topic: ..." so it's very semantically rich.
                        page_content = data.get("content")

                        # 2. GET ALL METADATA FOR FILTERING
                        # This is the "brain" of Hybrid Search.
                        # Vector DB will use these keys for pre-filtering before searching.
                        metadata = data.get("metadata", {})

                        # IMPORTANT: Chroma only supports metadata types: str, int, float, bool, None
                        # Must convert list/dict to string
                        cleaned_metadata = self._clean_metadata_for_chroma(metadata)

                        # Add source JSONL filename to metadata
                        cleaned_metadata["source_jsonl"] = os.path.basename(file_path)

                        if not page_content:
                            logger.warning(
                                f"Bỏ qua dòng không có 'content' trong {file_path}"
                            )
                            continue

                        # 3. CREATE DOCUMENT
                        # page_content will be embedded.
                        # metadata will be stored for filtering.
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
        Clean and normalize metadata to be compatible with Chroma vector database.

        Chroma only supports primitive types: str, int, float, bool, None.
        This method recursively converts complex types:
        - str, int, float, bool: Kept as-is
        - list: Joined into comma-separated string if contains primitives,
                serialized to JSON string if contains complex objects
        - dict: Serialized to JSON string
        - Other types: Converted to string representation

        Special handling for list items:
        - [1, "a", 2.5] → "1, a, 2.5"
        - [{"key": "val"}] → '[{"key": "val"}]' (JSON)
        - [] → "" (empty string)

        Args:
            metadata (dict): Original metadata dictionary (may contain complex types).

        Returns:
            dict: Cleaned metadata with only Chroma-compatible types.

        Example:
            >>> loader = DataLoader()
            >>> raw = {
            ...     "region": "miền bắc",
            ...     "tags": ["hà nội", "phố cổ"],
            ...     "images": [{"src": "url1"}],
            ...     "info": None
            ... }
            >>> cleaned = loader._clean_metadata_for_chroma(raw)
            >>> # Result: {"region": "miền bắc", "tags": "hà nội, phố cổ",
            >>> #          "images": '[{"src": "url1"}]', "info": None}
        """
        cleaned = {}

        for key, value in metadata.items():
            if value is None:
                cleaned[key] = None
            elif isinstance(value, (str, int, float, bool)):
                # Preserve valid types
                cleaned[key] = value
            elif isinstance(value, list):
                if not value:
                    cleaned[key] = ""
                # Check if the list contains simple or complex values
                elif all(
                    isinstance(item, (str, int, float, bool, type(None)))
                    for item in value
                ):
                    # List of simple values (e.g., "alias": ["a", "b"])
                    str_items = [str(item) for item in value if item is not None]
                    cleaned[key] = ", ".join(str_items)
                else:
                    # List of complex values (e.g., "images": [{"src":...}])
                    # Convert the entire list to a JSON string
                    try:
                        cleaned[key] = json.dumps(value, ensure_ascii=False)
                    except TypeError:
                        # Fallback if serialization error occurs
                        cleaned[key] = str(value)
            elif isinstance(value, dict):
                # Convert dict to JSON string
                try:
                    cleaned[key] = json.dumps(value, ensure_ascii=False)
                except TypeError:
                    cleaned[key] = str(value)
            else:
                # Other types: convert to string
                cleaned[key] = str(value)

        return cleaned
