# 🤖 Chatbot Application with RAG

An intelligent chatbot application that leverages **Retrieval-Augmented Generation (RAG)** to provide contextually accurate answers based on available documents.  
This project includes a user-friendly **web interface**, built with **Python backend** and **JavaScript frontend**.

---

## 🏗 Project Structure

```
├── src/                      # Python backend source code
│   ├── __init__.py
│   ├── chatbot.py            # Main chatbot class handling conversation flow
│   ├── config.py             # Application configuration (model, paths, etc.)
│   ├── data_loader.py        # Utilities for loading and preprocessing data/documents
│   ├── embedding_manager.py  # Manages vector embeddings and vector database
│   ├── query_parser.py       # Parses and processes user queries
│   ├── log.py                # Logging utilities
│   └── utils.py              # General-purpose helper functions
├── ui/                       # Frontend directory
│   ├── img/                  # Project images and icons
│   ├── app.js                # Main frontend logic (event handling, API communication)
│   ├── index.html            # Main user interface page
│   └── styles.css            # Styling for frontend
├── evaluation/               # Evaluation framework for RAG system assessment
│   ├── 01_collect_test_data.py          # Step 1: Collect test cases and responses
│   ├── 02_run_ragas_evaluation.py       # Step 2: Calculate Faithfulness & AnswerRelevancy metrics
│   ├── 03_generate_report.py            # Step 3: Generate HTML report and JSON summary
│   ├── test_data.json                   # Generated test cases (output of step 1)
│   ├── ragas_results.json               # Evaluation metrics (output of step 2)
│   ├── report.html                      # Visual HTML report (output of step 3)
│   └── report_summary.json              # JSON summary for automation (output of step 3)
├── data/                     # Dataset and knowledge base
│   └── vnexpress.jsonl       # Travel/tourism data in JSONL format
├── model_cache/              # Cached ML models (embeddings, LLM)
├── .env                      # Environment variables (create from .env.example)
├── .env.example              # Example environment configuration
├── requirements.txt          # Python dependencies
├── main.py                   # Application entry point
├── run_qa_harness.py         # Testing harness for QA system
├── settings_gpu.sh           # GPU configuration script
└── README.md                 # This documentation file
```

---

## 🚀 Getting Started

### Prerequisites

-   Python 3.9+
-   Ollama (with llama3.1 model) - Required for LLM and embeddings
-   8GB+ RAM recommended

### 1️⃣ Install Ollama and Models

**Download Ollama:**

```bash
# macOS/Windows/Linux - Download from https://ollama.ai
# Or on Linux:
curl -fsSL https://ollama.ai/install.sh | sh
```

**Start Ollama service:**

```bash
# macOS/Windows: Start Ollama app
# Linux:
ollama serve
```

**In another terminal, pull required models:**

```bash
# Pull llama3.1 model (LLM for generation)
ollama pull llama3.1

# Pull embedding model (for vector embeddings)
ollama pull nomic-embed-text

# Verify models are running:
ollama list
```

### 2️⃣ Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env to configure model names and paths if needed
```

### 4️⃣ Run the Application

```bash
python3 main.py
```

### 5️⃣ Access the App

Open your browser and go to:

```
http://localhost:8000
```

---

## 📊 Evaluation Framework

The `evaluation/` directory contains a 3-step framework for assessing RAG system quality:

### Step 1: Collect Test Data

```bash
python evaluation/01_collect_test_data.py
```

-   Generates 90 diverse test cases (locations, regions, complex queries, off-topic)
-   Calls chatbot for each question
-   Saves responses + retrieved contexts to `test_data.json`

### Step 2: Run Evaluation

```bash
python evaluation/02_run_ragas_evaluation.py
```

-   Calculates **Faithfulness**: How well response adheres to context (0-1 score)
-   Calculates **AnswerRelevancy**: How well response answers the question (0-1 score)
-   Uses embedding similarity for evaluation (no OpenAI API needed)
-   Saves metrics to `ragas_results.json`

### Step 3: Generate Reports

```bash
python evaluation/03_generate_report.py
```

-   Generates `report.html` - Beautiful visual report for browser
-   Generates `report_summary.json` - Machine-readable results for automation
-   Prints console summary with recommendations

**Run all steps at once:**

```bash
python evaluation/01_collect_test_data.py && \
python evaluation/02_run_ragas_evaluation.py && \
python evaluation/03_generate_report.py
```

---

## 💡 Key Features

-   **Retrieval-Augmented Generation (RAG)** for enhanced context-based answers.
-   Modular backend design for scalability and maintainability.
-   Lightweight and intuitive frontend for smooth user experience.
-   Easy environment configuration and deployment.

---

## 🧰 Technologies Used

-   **Backend:** Python (FastAPI / Flask)
-   **Frontend:** HTML, CSS, JavaScript
-   **Machine Learning:** Sentence Transformers / FAISS / LangChain
-   **Deployment:** Docker, Uvicorn, Gunicorn

---

## 📄 License

This project is licensed under the **MIT License**.  
Feel free to use, modify, and distribute with proper attribution.

---

_Developed with ❤️ by the GaCold team_
