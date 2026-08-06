"""
Report generator module for evaluation results.

This module provides functions to generate comprehensive evaluation reports
in various formats (markdown, HTML, JSON).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def generate_evaluation_report(
    evaluation_results: Dict[str, Any],
    model_name: str = "Anomaly Detection Model",
    output_path: Optional[str] = None
) -> str:
    """
    Generate comprehensive evaluation report in markdown format.
    
    Args:
        evaluation_results: Dictionary from evaluate_predictions()
        model_name: Name of the evaluated model
        output_path: Optional path to save report
        
    Returns:
        Markdown-formatted report string
    """
    logger.info(f"Generating evaluation report for {model_name}")
    
    overall = evaluation_results['overall_metrics']
    summary = evaluation_results['summary']
    cm = overall['confusion_matrix']
    
    # Build report
    report_lines = [
        f"# Evaluation Report: {model_name}",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "\n---\n",
        "## Executive Summary\n",
        f"- **Total Samples:** {summary['total_samples']:,}",
        f"- **Actual Anomalies:** {summary['actual_anomalies']:,} ({summary['actual_anomaly_rate']*100:.2f}%)",
        f"- **Predicted Anomalies:** {summary['predicted_anomalies']:,} ({summary['predicted_anomaly_rate']*100:.2f}%)",
        f"- **Overall F1 Score:** {overall['f1_score']:.4f}",
        "\n---\n",
        "## Performance Metrics\n",
        "### Classification Metrics\n",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Precision | {overall['precision']:.4f} |",
        f"| Recall | {overall['recall']:.4f} |",
        f"| F1 Score | {overall['f1_score']:.4f} |",
        f"| Accuracy | {overall['accuracy']:.4f} |",
        f"| Specificity | {overall['specificity']:.4f} |",
    ]
    
    # Add ROC AUC if available
    if 'roc_auc' in overall:
        report_lines.append(f"| ROC AUC | {overall['roc_auc']:.4f} |")
    if 'average_precision' in overall:
        report_lines.append(f"| Average Precision | {overall['average_precision']:.4f} |")
    
    # Confusion Matrix
    report_lines.extend([
        "\n### Confusion Matrix\n",
        f"| | Predicted Normal | Predicted Anomaly |",
        f"|---|---|---|",
        f"| **Actual Normal** | {cm['true_negatives']:,} (TN) | {cm['false_positives']:,} (FP) |",
        f"| **Actual Anomaly** | {cm['false_negatives']:,} (FN) | {cm['true_positives']:,} (TP) |",
    ])
    
    # Per-sensor metrics if available
    if evaluation_results.get('per_sensor_metrics') is not None:
        per_sensor = evaluation_results['per_sensor_metrics']
        
        report_lines.extend([
            "\n---\n",
            "## Per-Sensor Performance\n",
            f"\n**Number of Sensors:** {len(per_sensor)}\n",
            "\n| Sensor | Samples | Anomalies | Precision | Recall | F1 Score |",
            "|--------|---------|-----------|-----------|--------|----------|"
        ])
        
        for _, row in per_sensor.iterrows():
            report_lines.append(
                f"| {row['sensor']} | {row['samples']:,} | {row['actual_anomalies']:,} | "
                f"{row['precision']:.3f} | {row['recall']:.3f} | {row['f1_score']:.3f} |"
            )
    
    # Interpretation
    report_lines.extend([
        "\n---\n",
        "## Interpretation\n",
        _generate_interpretation(overall, summary),
        "\n---\n",
        "## Recommendations\n",
        _generate_recommendations(overall, summary)
    ])
    
    report = "\n".join(report_lines)
    
    # Save if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Report saved to {output_path}")
    
    return report


def generate_comparison_report(
    comparison_df: pd.DataFrame,
    output_path: Optional[str] = None
) -> str:
    """
    Generate model comparison report.
    
    Args:
        comparison_df: DataFrame from compare_models()
        output_path: Optional path to save report
        
    Returns:
        Markdown-formatted comparison report
    """
    logger.info("Generating model comparison report")
    
    report_lines = [
        "# Model Comparison Report",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"\n**Models Compared:** {len(comparison_df)}",
        "\n---\n",
        "## Performance Comparison\n",
        "### Overall Rankings\n",
        "\n| Rank | Model | F1 Score | Precision | Recall | Accuracy |",
        "|------|-------|----------|-----------|--------|----------|"
    ]
    
    for _, row in comparison_df.iterrows():
        report_lines.append(
            f"| {int(row['rank'])} | {row['model']} | {row['f1_score']:.4f} | "
            f"{row['precision']:.4f} | {row['recall']:.4f} | {row['accuracy']:.4f} |"
        )
    
    # Best model details
    best_model = comparison_df.iloc[0]
    
    report_lines.extend([
        "\n---\n",
        "## Best Model\n",
        f"\n**Model:** {best_model['model']}",
        f"\n**Performance:**",
        f"- F1 Score: {best_model['f1_score']:.4f}",
        f"- Precision: {best_model['precision']:.4f}",
        f"- Recall: {best_model['recall']:.4f}",
        f"- True Positives: {int(best_model['true_positives']):,}",
        f"- False Positives: {int(best_model['false_positives']):,}",
        f"- False Negatives: {int(best_model['false_negatives']):,}",
    ])
    
    # Recommendations
    report_lines.extend([
        "\n---\n",
        "## Recommendations\n",
        f"\n✅ **Recommended Model:** {best_model['model']}",
        f"\nThis model achieved the highest F1 score ({best_model['f1_score']:.4f}), "
        f"indicating the best balance between precision and recall.",
    ])
    
    report = "\n".join(report_lines)
    
    # Save if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Comparison report saved to {output_path}")
    
    return report


def export_report(
    report_data: Dict[str, Any],
    output_path: str,
    format: str = 'json'
) -> None:
    """
    Export evaluation results in various formats.
    
    Args:
        report_data: Dictionary containing evaluation results
        output_path: Path to save the report
        format: Output format ('json', 'csv', 'html')
    """
    logger.info(f"Exporting report in {format} format to {output_path}")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == 'json':
        # Convert numpy types to native Python types
        serializable_data = _make_json_serializable(report_data)
        
        with open(output_path, 'w') as f:
            json.dump(serializable_data, f, indent=2)
    
    elif format == 'csv':
        # Flatten metrics for CSV export
        if 'overall_metrics' in report_data:
            metrics = report_data['overall_metrics']
            
            # Create flat dictionary
            flat_data = {
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'f1_score': metrics['f1_score'],
                'accuracy': metrics['accuracy'],
                'true_positives': metrics['confusion_matrix']['true_positives'],
                'true_negatives': metrics['confusion_matrix']['true_negatives'],
                'false_positives': metrics['confusion_matrix']['false_positives'],
                'false_negatives': metrics['confusion_matrix']['false_negatives']
            }
            
            df = pd.DataFrame([flat_data])
            df.to_csv(output_path, index=False)
    
    elif format == 'html':
        # Generate HTML report
        html_content = _generate_html_report(report_data)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    logger.info(f"Report exported successfully to {output_path}")


def _generate_interpretation(
    metrics: Dict[str, Any],
    summary: Dict[str, Any]
) -> str:
    """Generate interpretation of metrics."""
    
    lines = []
    
    # Precision interpretation
    if metrics['precision'] >= 0.9:
        lines.append("- **Precision (Excellent):** Very few false alarms. The model is highly reliable when it predicts an anomaly.")
    elif metrics['precision'] >= 0.7:
        lines.append("- **Precision (Good):** Acceptable false alarm rate. Most predicted anomalies are genuine.")
    else:
        lines.append("- **Precision (Needs Improvement):** High false alarm rate. Many predicted anomalies are false positives.")
    
    # Recall interpretation
    if metrics['recall'] >= 0.9:
        lines.append("- **Recall (Excellent):** The model catches almost all actual anomalies.")
    elif metrics['recall'] >= 0.7:
        lines.append("- **Recall (Good):** The model catches most anomalies, but some are missed.")
    else:
        lines.append("- **Recall (Needs Improvement):** Many actual anomalies are being missed.")
    
    # F1 interpretation
    if metrics['f1_score'] >= 0.8:
        lines.append("- **F1 Score (Excellent):** Strong overall performance with good balance.")
    elif metrics['f1_score'] >= 0.6:
        lines.append("- **F1 Score (Good):** Acceptable performance, but room for improvement.")
    else:
        lines.append("- **F1 Score (Needs Improvement):** Model performance needs optimization.")
    
    return "\n".join(lines)


def _generate_recommendations(
    metrics: Dict[str, Any],
    summary: Dict[str, Any]
) -> str:
    """Generate recommendations based on metrics."""
    
    lines = []
    
    # Precision-based recommendations
    if metrics['precision'] < 0.7:
        lines.append("- **Reduce False Positives:** Consider increasing the anomaly threshold or refining feature engineering.")
    
    # Recall-based recommendations
    if metrics['recall'] < 0.7:
        lines.append("- **Reduce False Negatives:** Consider lowering the anomaly threshold or using ensemble methods.")
    
    # Balance recommendations
    if abs(metrics['precision'] - metrics['recall']) > 0.2:
        lines.append("- **Improve Balance:** Large gap between precision and recall. Adjust threshold or model parameters.")
    
    # Data recommendations
    actual_rate = summary['actual_anomaly_rate']
    if actual_rate < 0.01 or actual_rate > 0.5:
        lines.append(f"- **Data Imbalance:** Anomaly rate is {actual_rate*100:.1f}%. Consider resampling or adjusting contamination parameter.")
    
    if not lines:
        lines.append("- **Maintain Performance:** Current performance is good. Continue monitoring and periodic retraining.")
    
    return "\n".join(lines)


def _make_json_serializable(obj: Any) -> Any:
    """Convert numpy types to native Python types for JSON serialization."""
    
    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_json_serializable(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    else:
        return obj


def _generate_html_report(report_data: Dict[str, Any]) -> str:
    """Generate HTML report."""
    
    metrics = report_data.get('overall_metrics', {})
    summary = report_data.get('summary', {})
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Evaluation Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #1f77b4;
                border-bottom: 3px solid #1f77b4;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #333;
                margin-top: 30px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #1f77b4;
                color: white;
            }}
            .metric {{
                display: inline-block;
                margin: 10px;
                padding: 15px;
                background-color: #f0f0f0;
                border-radius: 5px;
                min-width: 150px;
            }}
            .metric-value {{
                font-size: 24px;
                font-weight: bold;
                color: #1f77b4;
            }}
            .metric-label {{
                font-size: 14px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Anomaly Detection Evaluation Report</h1>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            
            <h2>Summary</h2>
            <div class="metric">
                <div class="metric-label">Total Samples</div>
                <div class="metric-value">{summary.get('total_samples', 0):,}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Anomalies</div>
                <div class="metric-value">{summary.get('actual_anomalies', 0):,}</div>
            </div>
            <div class="metric">
                <div class="metric-label">F1 Score</div>
                <div class="metric-value">{metrics.get('f1_score', 0):.3f}</div>
            </div>
            
            <h2>Performance Metrics</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Precision</td>
                    <td>{metrics.get('precision', 0):.4f}</td>
                </tr>
                <tr>
                    <td>Recall</td>
                    <td>{metrics.get('recall', 0):.4f}</td>
                </tr>
                <tr>
                    <td>F1 Score</td>
                    <td>{metrics.get('f1_score', 0):.4f}</td>
                </tr>
                <tr>
                    <td>Accuracy</td>
                    <td>{metrics.get('accuracy', 0):.4f}</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """
    
    return html
