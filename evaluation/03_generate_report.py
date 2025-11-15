"""
Bước 3: Tạo báo cáo từ kết quả RAGAS
======================================

Script này:
1. Đọc kết quả từ ragas_results.json (output của bước 2)
2. Tạo báo cáo dễ hiểu và chi tiết
3. Xuất dạng:
   - Console output (in ra terminal)
   - HTML report (để xem trình duyệt hoặc thêm vào presentation)
   - JSON summary (dùng cho automation)

Input: evaluation/ragas_results.json
Output: 
   - evaluation/report.html
   - evaluation/report_summary.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def load_ragas_results(result_file: str = "evaluation/ragas_results.json") -> Dict[str, Any]:
    """Đọc RAGAS results"""
    
    result_path = Path(result_file)
    
    if not result_path.exists():
        print(f"❌ File không tìm thấy: {result_file}")
        print(f"   Hãy chạy bước 2 trước: python evaluation/02_run_ragas_evaluation.py")
        return None
    
    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None


def create_html_report(results: Dict[str, Any], output_file: str = "evaluation/report.html"):
    """Tạo HTML report"""
    
    metrics = results.get("metrics", {})
    overall = results.get("overall_score", 0)
    timestamp = results.get("timestamp", "")
    num_cases = results.get("num_test_cases", 0)
    
    # Thang đánh giá màu sắc
    def get_color(score: float) -> str:
        if score >= 0.8:
            return "#4CAF50"  # Green
        elif score >= 0.6:
            return "#FFC107"  # Amber
        elif score >= 0.4:
            return "#FF9800"  # Orange
        else:
            return "#F44336"  # Red
    
    html_content = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAGAS Evaluation Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 1em;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .info-section {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #667eea;
        }}
        
        .info-item {{
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            font-size: 1em;
        }}
        
        .info-item strong {{
            color: #333;
        }}
        
        .info-item span {{
            color: #666;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .metric-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
            text-transform: capitalize;
        }}
        
        .metric-card .score {{
            font-size: 2.5em;
            font-weight: bold;
            font-family: 'Courier New', monospace;
        }}
        
        .overall-section {{
            background: linear-gradient(135deg, {get_color(overall)} 0%, {get_color(overall)}dd 100%);
            padding: 30px;
            border-radius: 8px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .overall-section .label {{
            font-size: 1.2em;
            margin-bottom: 10px;
            opacity: 0.9;
        }}
        
        .overall-section .score {{
            font-size: 3em;
            font-weight: bold;
            font-family: 'Courier New', monospace;
        }}
        
        .description {{
            background: #fafafa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            line-height: 1.6;
            color: #555;
            border-left: 4px solid #999;
        }}
        
        .description h3 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .description p {{
            margin: 8px 0;
            font-size: 0.95em;
        }}
        
        .footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 0.9em;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 RAGAS Evaluation Report</h1>
            <p>Travel Chatbot RAG System Assessment</p>
        </div>
        
        <div class="content">
            <!-- Info Section -->
            <div class="info-section">
                <div class="info-item">
                    <strong>📅 Timestamp:</strong>
                    <span>{timestamp}</span>
                </div>
                <div class="info-item">
                    <strong>🧪 Test Cases:</strong>
                    <span>{num_cases} cases</span>
                </div>
            </div>
            
            <!-- Overall Score -->
            <div class="overall-section">
                <div class="label">Overall Score</div>
                <div class="score">{overall:.1%}</div>
            </div>
            
            <!-- Metrics Grid -->
            <div class="metrics-grid">
"""
    
    # Add metric cards
    metric_info = {
        "faithfulness": ("Faithfulness", "Độ trung thành với context"),
        "answer_relevancy": ("Answer Relevancy", "Độ liên quan của câu trả lời"),
    }
    
    for metric_key, (metric_name, metric_desc) in metric_info.items():
        score = metrics.get(metric_key, 0)
        color = get_color(score)
        html_content += f"""
                <div class="metric-card" style="background: {color};">
                    <div class="label">{metric_name}</div>
                    <div style="font-size: 0.85em; margin-bottom: 8px;">{metric_desc}</div>
                    <div class="score">{score:.1%}</div>
                </div>
"""
    
    # Add descriptions
    html_content += """
            </div>
            
            <!-- Metric Explanations -->
            <div class="description">
                <h3>📖 Giải thích các Metric:</h3>
                <p>
                    <strong>Faithfulness (Độ trung thành):</strong> 
                    Mức độ câu trả lời không bịa thêm, luôn dựa trên context đã cung cấp.
                </p>
                <p>
                    <strong>Answer Relevancy (Độ liên quan):</strong> 
                    Mức độ câu trả lời trả lời đúng câu hỏi, có liên quan trực tiếp.
                </p>
                <p style="margin-top: 15px; font-size: 0.9em; color: #999; border-top: 1px solid #ddd; padding-top: 10px;">
                    <strong>Note:</strong> Context Precision & Context Recall yêu cầu ground truth reference, 
                    không được áp dụng cho hệ thống này vì KB không có Q&A pairs sẵn.
                </p>
            </div>
        </div>
        
        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
    
    # Lưu HTML
    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"💾 HTML Report: {output_path}")
    return output_path


def create_summary_json(results: Dict[str, Any], output_file: str = "evaluation/report_summary.json"):
    """Tạo summary JSON"""
    
    metrics = results.get("metrics", {})
    
    summary = {
        "timestamp": results.get("timestamp"),
        "num_test_cases": results.get("num_test_cases"),
        "scores": {
            "faithfulness": {
                "value": metrics.get("faithfulness", 0),
                "label": "Độ trung thành với context",
                "interpretation": "Cao hơn tốt hơn (tránh bịa)"
            },
            "answer_relevancy": {
                "value": metrics.get("answer_relevancy", 0),
                "label": "Độ liên quan của câu trả lời",
                "interpretation": "Cao hơn = trả lời đúng ý câu hỏi"
            },
        },
        "overall_score": results.get("overall_score"),
        "assessment": _get_assessment(results.get("overall_score", 0))
    }
    
    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Summary JSON: {output_path}")
    return output_path


def _get_assessment(score: float) -> str:
    """Đánh giá chung"""
    if score >= 0.85:
        return "Xuất sắc (Excellent) 🌟"
    elif score >= 0.75:
        return "Tốt (Good) ✅"
    elif score >= 0.65:
        return "Khá (Fair) 👍"
    elif score >= 0.5:
        return "Trung bình (Average) ⚠️"
    else:
        return "Cần cải thiện (Needs Improvement) ❌"


def print_console_report(results: Dict[str, Any]):
    """In báo cáo ra console"""
    
    metrics = results.get("metrics", {})
    overall = results.get("overall_score", 0)
    num_cases = results.get("num_test_cases", 0)
    timestamp = results.get("timestamp", "")
    
    assessment = _get_assessment(overall)
    
    print("\n" + "="*70)
    print("📊 RAGAS EVALUATION REPORT")
    print("="*70)
    
    print(f"\n📅 Timestamp: {timestamp}")
    print(f"🧪 Test Cases: {num_cases}")
    
    print(f"\n📈 Scores:")
    print("-"*70)
    print(f"  Faithfulness:        {metrics.get('faithfulness', 0):.1%}")
    print(f"  Answer Relevancy:    {metrics.get('answer_relevancy', 0):.1%}")
    print("-"*70)
    print(f"  Overall Score:       {overall:.1%}  ({assessment})")
    
    print(f"\n💡 Recommendations:")
    if metrics.get('faithfulness', 0) < 0.7:
        print(f"  • Faithfulness thấp: Cải thiện system prompt, buộc bot chỉ dùng context")
    if metrics.get('answer_relevancy', 0) < 0.7:
        print(f"  • Answer Relevancy thấp: Tối ưu prompt để trả lời chính xác hơn")
    
    print("\n" + "="*70 + "\n")


def main():
    print("\n" + "="*70)
    print("📊 BƯỚC 3: TẠO BÁOCÁO RAGAS")
    print("="*70)
    
    # Đọc results
    results = load_ragas_results()
    if not results:
        print("\n❌ Bước 3 thất bại!")
        sys.exit(1)
    
    # In console report
    print_console_report(results)
    
    # Tạo HTML report
    print("📝 Creating HTML report...")
    create_html_report(results)
    print("✅ HTML report created")
    
    # Tạo summary JSON
    print("📝 Creating summary JSON...")
    create_summary_json(results)
    print("✅ Summary JSON created")
    
    print("\n" + "="*70)
    print("✅ Bước 3 hoàn thành!")
    print("   Files:")
    print("   • evaluation/report.html (mở bằng browser)")
    print("   • evaluation/report_summary.json (dùng cho automation)")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
