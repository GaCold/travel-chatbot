# RAGAS Evaluation Framework

Cách tiến hành đánh giá độ chính xác của Travel Chatbot RAG system một cách rõ ràng và theo từng bước.

## 📋 Quy trình 3 bước

### Bước 1: Thu thập dữ liệu 
**File:** `01_collect_test_data.py`

```bash
python evaluation/01_collect_test_data.py
```

**Công việc:**
- Định nghĩa test cases (các câu hỏi để test)
- Gọi chatbot → lấy câu trả lời + retrieved contexts
- Lưu vào: `evaluation/test_data.json`

**Output format:**
```json
{
    "test_cases": [
        {
            "user_input": "Hà Nội nên đi đâu chơi?",
            "response": "Câu trả lời từ bot...",
            "retrieved_contexts": ["Context 1", "Context 2", ...]
        }
    ],
    "total": 10,
    "timestamp": "2025-11-13T10:30:00"
}
```

---

### Bước 2: Chạy RAGAS evaluation
**File:** `02_run_ragas_evaluation.py`

```bash
python evaluation/02_run_ragas_evaluation.py
```

**Công việc:**
- Đọc `test_data.json` từ bước 1
- Chạy RAGAS metrics:
  - **Faithfulness**: Độ trung thành với context (bọn bịa không)
  - **Answer Relevancy**: Độ liên quan của câu trả lời
  - **Context Precision**: Độ chính xác retrieval (ít lấy rác)
  - **Context Recall**: Độ bao phủ retrieval (lấy được đủ info)
- Lưu vào: `evaluation/ragas_results.json`

**Note:** RAGAS sẽ gọi LLM nhiều lần, có thể mất vài phút ⏳

**Output format:**
```json
{
    "metrics": {
        "faithfulness": 0.85,
        "answer_relevancy": 0.78,
        "context_precision": 0.82,
        "context_recall": 0.75
    },
    "overall_score": 0.80,
    "num_test_cases": 10,
    "timestamp": "2025-11-13T10:35:00"
}
```

---

### Bước 3: Tạo báo cáo
**File:** `03_generate_report.py`

```bash
python evaluation/03_generate_report.py
```

**Công việc:**
- Đọc `ragas_results.json` từ bước 2
- Tạo báo cáo dưới các hình thức:
  - **HTML Report** (`report.html`): Dùng để xem trình duyệt, thêm vào presentation
  - **Summary JSON** (`report_summary.json`): Dùng cho automation, parsing

**Output files:**
- `evaluation/report.html` → Mở bằng browser để xem
- `evaluation/report_summary.json` → Machine-readable format

---

## 🚀 Chạy cả 3 bước liên tiếp

```bash
python evaluation/01_collect_test_data.py && \
python evaluation/02_run_ragas_evaluation.py && \
python evaluation/03_generate_report.py
```

Hoặc tạo script `run_all.sh`:
```bash
#!/bin/bash
set -e

echo "🔄 Running full evaluation pipeline..."
python evaluation/01_collect_test_data.py
python evaluation/02_run_ragas_evaluation.py
python evaluation/03_generate_report.py
echo "✅ Done! Check evaluation/report.html"
```

---

## 📊 Các Metric Giải thích

| Metric | Ý nghĩa | Giá trị tốt | Cách cải thiện |
|--------|---------|-----------|-----------------|
| **Faithfulness** | Câu trả lời không bịa, dựa trên context | > 0.8 | Tối ưu prompt, buộc bot chỉ dùng context |
| **Answer Relevancy** | Trả lời đúng câu hỏi, không lạc đề | > 0.8 | Cải thiện system prompt, instruction rõ ràng |
| **Context Precision** | Documents lấy được chủ yếu là liên quan | > 0.75 | Thêm re-ranker, giảm k |
| **Context Recall** | Lấy được đủ thông tin cần để trả lời | > 0.75 | Tăng k, dùng multi-query, cải thiện embeddings |

---

## 📂 File Structure

```
evaluation/
├── 01_collect_test_data.py       # Bước 1: Thu thập data
├── 02_run_ragas_evaluation.py    # Bước 2: Chạy evaluation
├── 03_generate_report.py         # Bước 3: Tạo báo cáo
├── README.md                     # File này
├── test_data.json                # Output bước 1
├── ragas_results.json            # Output bước 2
├── report.html                   # Output bước 3 (HTML)
└── report_summary.json           # Output bước 3 (JSON)
```

---

## 💡 Tips

### 1. Tùy chỉnh test cases
Sửa list `TEST_CASES` trong `01_collect_test_data.py`:

```python
TEST_CASES = [
    {"question": "Câu hỏi của bạn 1"},
    {"question": "Câu hỏi của bạn 2"},
    # Thêm câu hỏi khác tại đây
]
```

### 2. Chạy từng bước độc lập
Nếu bước 1 hoặc 2 thất bại, fix rồi chạy lại chỉ bước đó.
File intermediate (`test_data.json`, `ragas_results.json`) sẽ được giữ lại.

### 3. Lưu trữ kết quả
Lưu folder `evaluation/` nếu muốn so sánh với lần chạy sau:

```bash
cp -r evaluation evaluation_v1
# Sau khi cải thiện bot, chạy lại evaluation
# So sánh evaluation/report.html với evaluation_v1/report.html
```

### 4. Debugging
Mỗi script có `print()` verbose, nên có thể thấy rõ đang làm gì:
- Bước 1: Thấy câu hỏi, số contexts lấy được
- Bước 2: Thấy LLM calls (RAGAS đang chấm điểm)
- Bước 3: Thấy files được tạo

---

## ⚠️ Lưu ý

1. **Cần internet/Ollama chạy** để chạy bước 1 và 2
2. **RAGAS evaluation tốn time** vì gọi LLM nhiều lần (vài phút)
3. **Ollama phải đang chạy** `mistral` model
4. **Embeddings phải cached** sau lần đầu, lần sau nhanh hơn

---

## 🔗 Tham khảo

- RAGAS docs: https://docs.ragas.io/
- Các metrics chi tiết: https://docs.ragas.io/en/stable/concepts/metrics/

---

**Tạo bởi:** Travel Chatbot Evaluation Framework  
**Ngày:** Nov 2025
