import os
from dotenv import load_dotenv
from enum import Enum
load_dotenv()

class EmbeddingModelType(Enum):
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"


class Config:
    """Configuration class for the travel chatbot"""
    
    # Model settings
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1")  # Model cho generation
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "nomic-embed-text")  # Model cho embedding
    EMBEDDING_MODEL_TYPE = os.getenv("EMBEDDING_MODEL_TYPE", "ollama")

    # HuggingFace model names
    VIETNAMESE_EMBEDDING_MODELS = {
        "vietnamese_v2": "AITeamVN/Vietnamese_Embedding_v2",
        "vietnamese_bi_encoder": "keepitreal/vietnamese-bi-encoder",
        "sentence-transformers": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    }

    # HuggingFace settings
    HF_TOKEN = os.getenv("HF_TOKEN", "")
    
    # Path settings
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIRECTORY = os.path.join(BASE_DIR, "data")
    PERSIST_DIRECTORY = os.path.join(BASE_DIR, "faiss_index")
    LOG_DIRECTORY = os.path.join(BASE_DIR, "logs")
    
    # RAG settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    SEARCH_K = 3

    MODEL_CACHE_DIR = os.path.join(BASE_DIR, "model_cache")
    
    # Ollama settings
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    def __init__(self):
        # Create necessary directories
        os.makedirs(self.DATA_DIRECTORY, exist_ok=True)
        os.makedirs(self.LOG_DIRECTORY, exist_ok=True)