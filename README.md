# 🤖 Chatbot Application with RAG

An intelligent chatbot application that leverages **Retrieval-Augmented Generation (RAG)** to provide contextually accurate answers based on available documents.  
This project includes a user-friendly **web interface**, built with **Python backend** and **JavaScript frontend**.

---

## 🏗 Project Structure
```
├── src/                    # Python backend source code
│   ├── __init__.py
│   ├── chatbot.py          # Main chatbot class handling conversation flow
│   ├── config.py           # Application configuration (model, paths, etc.)
│   ├── data_loader.py      # Utilities for loading and preprocessing data/documents
│   ├── embedding_manager.py# Manages vector embeddings and vector database
│   ├── query_parser.py     # Parses and processes user queries
│   └── utils.py            # General-purpose helper functions
├── ui/                     # Frontend directory
│   ├── img/                # Project images and icons
│   ├── app.js              # Main frontend logic (event handling, API communication)
│   ├── index.html          # Main user interface page
└── README.md               # This documentation file
```

---

## 🚀 Getting Started

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Set Up Environment Variables
```bash
cp .env.example .env
```

### 3️⃣ Run the Application
```bash
python3 main.py
```

### 4️⃣ Access the App
Open your browser and go to:
```
http://localhost:8001
```

---

## 💡 Key Features
- **Retrieval-Augmented Generation (RAG)** for enhanced context-based answers.
- Modular backend design for scalability and maintainability.
- Lightweight and intuitive frontend for smooth user experience.
- Easy environment configuration and deployment.

---

## 🧰 Technologies Used
- **Backend:** Python (FastAPI / Flask)
- **Frontend:** HTML, CSS, JavaScript
- **Machine Learning:** Sentence Transformers / FAISS / LangChain
- **Deployment:** Docker, Uvicorn, Gunicorn

---

## 📄 License
This project is licensed under the **MIT License**.  
Feel free to use, modify, and distribute with proper attribution.

---

_Developed with ❤️ by the GaCold team_
