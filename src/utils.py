import os
import sys
from typing import List

def validate_data_directory(data_dir: str) -> bool:
    """Validate that data directory exists and contains JSONL files"""
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        return False
    
    jsonl_files = [f for f in os.listdir(data_dir) if f.endswith('.jsonl')]
    if not jsonl_files:
        print(f"❌ No JSONL files found in: {data_dir}")
        return False
    
    print(f"✅ Found {len(jsonl_files)} JSONL files in data directory")
    return True

def get_available_models() -> List[str]:
    """Get list of available Ollama models"""
    # This would typically call Ollama API to get available models
    return ["llama3.1", "mistral", "codellama"]

def clear_vector_store(persist_directory: str):
    """Clear existing vector store"""
    import shutil
    if os.path.exists(persist_directory):
        shutil.rmtree(persist_directory)
        print(f"✅ Vector store cleared: {persist_directory}")