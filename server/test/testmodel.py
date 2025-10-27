# test_models.py
from langchain_ollama import ChatOllama

models = ["qwen2.5:7b"]
question = "Hãy giới thiệu về địa điểm Phú Quốc ngắn gọn"

for model in models:
    print(f"\n{'='*60}")
    print(f"Model: {model}")
    print('='*60)
    
    llm = ChatOllama(model=model, temperature=0.7)
    response = llm.invoke(question)
    print(response.content)