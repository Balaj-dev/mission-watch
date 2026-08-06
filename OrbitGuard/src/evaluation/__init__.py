"""
Evaluation module for Mission Watch.

This module provides tools for evaluating anomaly detection performance,
calculating metrics, and generating evaluation reports.
"""

from src.evaluation.metrics import (
    calculate_precision,
    calculate_recall,
    calculate_f1_score,
    calculate_confusion_matrix,
    calculate_all_metrics
)

from src.evaluation.evaluator import (
    evaluate_predictions,
    compare_models,
    cross_validate
)

from src.evaluation.report_generator import (
    generate_evaluation_report,
    generate_comparison_report,
    export_report
)

__all__ = [
    # Metrics
    'calculate_precision',
    'calculate_recall',
    'calculate_f1_score',
    'calculate_confusion_matrix',
    'calculate_all_metrics',
    
    # Evaluator
    'evaluate_predictions',
    'compare_models',
    'cross_validate',
    
    # Report Generator
    'generate_evaluation_report',
    'generate_comparison_report',
    'export_report'
]

__version__ = '1.0.0'
