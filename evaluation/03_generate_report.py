"""
Step 3: Generate reports from RAGAS results
=============================================

Script performs:
1. Read results from ragas_results.json (output of step 2)
2. Create easy-to-understand detailed reports
3. Export in formats:
   - Console output (print to terminal)
   - HTML report (view in browser or add to presentation)
   - JSON summary (for automation)

Input: evaluation/ragas_results.json
Output:
   - evaluation/report.html
   - evaluation/report_summary.json
"""

import json

# Add repo root to path
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.config import Config


def load_ragas_results(
    result_file: str = "evaluation/ragas_results.json",
) -> Dict[str, Any]:
    """
    Load RAGAS evaluation results from JSON file.

    Args:
        result_file (str): Path to ragas_results.json file.

    Returns:
        Dict[str, Any]: Parsed results dictionary or None if file not found/readable.
    """

    result_path = Path(result_file)

    if not result_path.exists():
        print(f"❌ File not found: {result_file}")
        print(f"   Run step 2 first: python evaluation/02_run_ragas_evaluation.py")
        return None

    try:
        with open(result_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None


def create_html_report(
    results: Dict[str, Any], output_file: str = "evaluation/report.html"
):
    """
    Generate HTML report from evaluation results.

    Creates professional, visually appealing HTML report with:
    - Header with title and timestamp
    - Score cards with color coding
    - Overall assessment banner
    - Metric explanations
    - Responsive design for browser viewing

    Args:
        results (Dict[str, Any]): Results dictionary from load_ragas_results().
        output_file (str): Path to save HTML report.

    Returns:
        Path: Path object to created HTML file.
    """

    metrics = results.get("metrics", {})
    overall = results.get("overall_score", 0)
    timestamp = results.get("timestamp", "")
    num_cases = results.get("num_test_cases", 0)

    # Color scale for scores
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
                <h3>📖 Metric Explanations:</h3>
                <p>
                    <strong>Faithfulness:</strong> 
                    How well response stays grounded in provided context, avoiding hallucinations.
                </p>
                <p>
                    <strong>Answer Relevancy:</strong> 
                    How well response directly answers the user's question.
                </p>
                <p style="margin-top: 15px; font-size: 0.9em; color: #999; border-top: 1px solid #ddd; padding-top: 10px;">
                    <strong>Note:</strong> Context Precision & Context Recall require ground truth references,
                    not applicable for this system as KB has no pre-made Q&A pairs.
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

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"💾 HTML Report: {output_path}")
    return output_path


def create_summary_json(
    results: Dict[str, Any], output_file: str = "evaluation/report_summary.json"
):
    """
    Generate summary JSON from evaluation results.

    Creates machine-readable summary with metric values, labels, and
    interpretation guidance. Useful for automation and integration.

    Args:
        results (Dict[str, Any]): Results dictionary from load_ragas_results().
        output_file (str): Path to save JSON summary.

    Returns:
        Path: Path object to created JSON file.
    """

    metrics = results.get("metrics", {})

    summary = {
        "timestamp": results.get("timestamp"),
        "num_test_cases": results.get("num_test_cases"),
        "scores": {
            "faithfulness": {
                "value": metrics.get("faithfulness", 0),
                "label": "Response alignment with context",
                "interpretation": "Higher is better (avoid hallucinations)",
            },
            "answer_relevancy": {
                "value": metrics.get("answer_relevancy", 0),
                "label": "Answer relevance to question",
                "interpretation": "Higher = answers question correctly",
            },
        },
        "overall_score": results.get("overall_score"),
        "assessment": _get_assessment(results.get("overall_score", 0)),
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True, parents=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"💾 Summary JSON: {output_path}")
    return output_path


def _get_assessment(score: float) -> str:
    """
    Generate human-readable assessment based on overall score.

    Args:
        score (float): Overall evaluation score between 0 and 1.

    Returns:
        str: Assessment label with emoji (e.g., "Excellent 🌟").
    """
    if score >= 0.85:
        return "Excellent"
    elif score >= 0.75:
        return "Good"
    elif score >= 0.65:
        return "Fair"
    elif score >= 0.55:
        return "Average"
    else:
        return "Needs Improvement"


def print_console_report(results: Dict[str, Any]):
    """
    Print formatted evaluation report to console.

    Displays all evaluation metrics and configuration in human-readable format
    with ASCII formatting for easy terminal viewing.

    Args:
        results (Dict[str, Any]): Results dictionary from load_ragas_results().

    Returns:
        None
    """

    metrics = results.get("metrics", {})
    overall = results.get("overall_score", 0)
    num_cases = results.get("num_test_cases", 0)
    timestamp = results.get("timestamp", "")

    assessment = _get_assessment(overall)
    config = Config()

    print("\n" + "=" * 70)
    print("📊 RAGAS EVALUATION REPORT")
    print("=" * 70)

    # Display configuration
    print(f"\n⚙️  Configuration:")
    print(f"  LLM Model: {config.LLM_MODEL}")
    print(
        f"  Embedding Model: {config.EMBEDDING_MODEL_NAME} (type: {config.EMBEDDING_MODEL_TYPE})"
    )

    print(f"\n📅 Timestamp: {timestamp}")
    print(f"🧪 Test Cases: {num_cases}")

    print(f"\n📈 Scores:")
    print("-" * 70)
    print(f"  Faithfulness:        {metrics.get('faithfulness', 0):.1%}")
    print(f"  Answer Relevancy:    {metrics.get('answer_relevancy', 0):.1%}")
    print("-" * 70)
    print(f"  Overall Score:       {overall:.1%}  ({assessment})")

    print(f"\n💡 Recommendations:")
    if metrics.get("faithfulness", 0) < 0.7:
        print(
            f"  • Faithfulness is low: Improve system prompt, enforce context-only responses"
        )
    if metrics.get("answer_relevancy", 0) < 0.7:
        print(f"  • Answer Relevancy is low: Optimize prompt for more accurate answers")

    print("\n" + "=" * 70 + "\n")


def main():
    """
    Main entry point for report generation.

    Loads evaluation results and generates HTML report, JSON summary,
    and console output.
    """
    print("\n" + "=" * 70)
    print("📊 STEP 3: GENERATE RAGAS REPORT")
    print("=" * 70)

    # Load results
    results = load_ragas_results()
    if not results:
        print("\n❌ Step 3 failed!")
        sys.exit(1)

    # Print console report
    print_console_report(results)

    # Create HTML report
    print("📝 Creating HTML report...")
    create_html_report(results)
    print("✅ HTML report created")

    # Create summary JSON
    print("📝 Creating summary JSON...")
    create_summary_json(results)
    print("✅ Summary JSON created")

    print("\n" + "=" * 70)
    print("✅ Step 3 completed!")
    print("   Files:")
    print("   • evaluation/report.html (open with browser)")
    print("   • evaluation/report_summary.json (for automation)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
