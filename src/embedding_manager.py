import os
from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from .config import Config, EmbeddingModelType
import logging

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Manager for different embedding models"""
    
    def __init__(self, config: Config):
        self.config = config
        self.embeddings = None
        
    def initialize_embeddings(self):
        """Initialize embeddings based on configuration"""
        try:
            if self.config.EMBEDDING_MODEL_TYPE == "ollama":
                self.embeddings = self._setup_ollama_embeddings()
                logger.info(f"Initialized Ollama embeddings: {self.config.EMBEDDING_MODEL_NAME}")
                
            elif self.config.EMBEDDING_MODEL_TYPE == "huggingface":
                self.embeddings = self._setup_huggingface_embeddings()
                logger.info(f"Initialized HuggingFace embeddings: {self.config.EMBEDDING_MODEL_NAME}")
                
            else:
                raise ValueError(f"Unsupported embedding type: {self.config.EMBEDDING_MODEL_TYPE}")
            
            # Test embeddings
            test_embedding = self.embeddings.embed_query("test")
            print(f"✅ Embeddings initialized, dimension: {len(test_embedding)}")
                
            return self.embeddings
            
        except Exception as e:
            logger.error(f"Error initializing embeddings: {e}")
            raise
    
    def _setup_ollama_embeddings(self):
        """Setup Ollama embeddings"""
        print(f"🦙 Đang kết nối Ollama: {self.config.EMBEDDING_MODEL_NAME}")
        return OllamaEmbeddings(
            model=self.config.EMBEDDING_MODEL_NAME,
            base_url=self.config.OLLAMA_BASE_URL
        )
    
    def _setup_huggingface_embeddings(self):
        """Setup HuggingFace embeddings với model tiếng Việt"""
        model_name = self.config.VIETNAMESE_EMBEDDING_MODELS.get(
            self.config.EMBEDDING_MODEL_NAME, 
            self.config.EMBEDDING_MODEL_NAME
        )
        print(f"🤗 Loading HuggingFace model: {model_name}")
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={
                'device': 'cpu', # or 'cuda' if GPU available
                'token': self.config.HF_TOKEN
            },
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 32
            },
            cache_folder=self.config.MODEL_CACHE_DIR
        )
    
    def get_available_models(self):
        """Get list of available embedding models"""
        ollama_models = ["nomic-embed-text", "all-minilm", "bge-m3"]
        hf_models = list(self.config.VIETNAMESE_EMBEDDING_MODELS.keys())
        
        return {
            "ollama": ollama_models,
            "huggingface": hf_models
        }