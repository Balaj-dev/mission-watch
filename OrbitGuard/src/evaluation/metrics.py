"""
Metrics calculation module for anomaly detection evaluation.

This module provides functions to calculate various performance metrics
including precision, recall, F1-score, and confusion matrix.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def calculate_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, int]:
    """
    Calculate confusion matrix components.
    
    Args:
        y_true: Ground truth labels (1 = anomaly, 0 = normal)
        y_pred: Predicted labels (1 = anomaly, 0 = normal)
        
    Returns:
        Dictionary with TP, TN, FP, FN counts
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    
    logger.debug(f"Confusion Matrix - TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")
    
    return {
        'true_positives': int(tp),
        'true_negatives': int(tn),
        'false_positives': int(fp),
        'false_negatives': int(fn)
    }


def calculate_precision(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Calculate precision score.
    
    Precision = TP / (TP + FP)
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
        
    Returns:
        Precision score (0.0 to 1.0)
    """
    cm = calculate_confusion_matrix(y_true, y_pred)
    tp = cm['true_positives']
    fp = cm['false_positives']
    
    if tp + fp == 0:
        logger.warning("No positive predictions - precision undefined, returning 0.0")
        return 0.0
    
    precision = tp / (tp + fp)
    logger.debug(f"Precision: {precision:.4f}")
    
    return precision


def calculate_recall(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Calculate recall score (sensitivity, true positive rate).
    
    Recall = TP / (TP + FN)
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
        
    Returns:
        Recall score (0.0 to 1.0)
    """
    cm = calculate_confusion_matrix(y_true, y_pred)
    tp = cm['true_positives']
    fn = cm['false_negatives']
    
    if tp + fn == 0:
        logger.warning("No actual positives - recall undefined, returning 0.0")
        return 0.0
    
    recall = tp / (tp + fn)
    logger.debug(f"Recall: {recall:.4f}")
    
    return recall


def calculate_f1_score(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Calculate F1 score (harmonic mean of precision and recall).
    
    F1 = 2 * (Precision * Recall) / (Precision + Recall)
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
        
    Returns:
        F1 score (0.0 to 1.0)
    """
    precision = calculate_precision(y_true, y_pred)
    recall = calculate_recall(y_true, y_pred)
    
    if precision + recall == 0:
        logger.warning("Precision and recall both zero - F1 undefined, returning 0.0")
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    logger.debug(f"F1 Score: {f1:.4f}")
    
    return f1


def calculate_accuracy(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Calculate accuracy score.
    
    Accuracy = (TP + TN) / (TP + TN + FP + FN)
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
        
    Returns:
        Accuracy score (0.0 to 1.0)
    """
    cm = calculate_confusion_matrix(y_true, y_pred)
    tp = cm['true_positives']
    tn = cm['true_negatives']
    fp = cm['false_positives']
    fn = cm['false_negatives']
    
    total = tp + tn + fp + fn
    
    if total == 0:
        logger.warning("No samples - accuracy undefined, returning 0.0")
        return 0.0
    
    accuracy = (tp + tn) / total
    logger.debug(f"Accuracy: {accuracy:.4f}")
    
    return accuracy


def calculate_specificity(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Calculate specificity (true negative rate).
    
    Specificity = TN / (TN + FP)
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
        
    Returns:
        Specificity score (0.0 to 1.0)
    """
    cm = calculate_confusion_matrix(y_true, y_pred)
    tn = cm['true_negatives']
    fp = cm['false_positives']
    
    if tn + fp == 0:
        logger.warning("No actual negatives - specificity undefined, returning 0.0")
        return 0.0
    
    specificity = tn / (tn + fp)
    logger.debug(f"Specificity: {specificity:.4f}")
    
    return specificity


def calculate_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_scores: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Calculate all evaluation metrics.
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted labels
        y_scores: Optional anomaly scores for additional metrics
        
    Returns:
        Dictionary containing all metrics
    """
    logger.info("Calculating all evaluation metrics")
    
    # Confusion matrix
    cm = calculate_confusion_matrix(y_true, y_pred)
    
    # Classification metrics
    metrics = {
        'confusion_matrix': cm,
        'precision': calculate_precision(y_true, y_pred),
        'recall': calculate_recall(y_true, y_pred),
        'f1_score': calculate_f1_score(y_true, y_pred),
        'accuracy': calculate_accuracy(y_true, y_pred),
        'specificity': calculate_specificity(y_true, y_pred)
    }
    
    # Additional metrics if scores provided
    if y_scores is not None:
        try:
            from sklearn.metrics import roc_auc_score, average_precision_score
            
            metrics['roc_auc'] = roc_auc_score(y_true, y_scores)
            metrics['average_precision'] = average_precision_score(y_true, y_scores)
            
            logger.debug(f"ROC AUC: {metrics['roc_auc']:.4f}")
            logger.debug(f"Average Precision: {metrics['average_precision']:.4f}")
        except Exception as e:
            logger.warning(f"Could not calculate ROC/AP metrics: {e}")
    
    logger.info("Metrics calculation complete")
    
    return metrics


def calculate_metrics_by_sensor(
    data: pd.DataFrame,
    true_col: str = 'is_anomaly',
    pred_col: str = 'predicted_anomaly',
    sensor_col: str = 'sensor_id'
) -> pd.DataFrame:
    """
    Calculate metrics for each sensor/channel separately.
    
    Args:
        data: DataFrame with predictions and ground truth
        true_col: Column name for ground truth
        pred_col: Column name for predictions
        sensor_col: Column name for sensor identifier
        
    Returns:
        DataFrame with metrics per sensor
    """
    logger.info("Calculating per-sensor metrics")
    
    sensors = data[sensor_col].unique()
    results = []
    
    for sensor in sensors:
        sensor_data = data[data[sensor_col] == sensor]
        
        y_true = sensor_data[true_col].values
        y_pred = sensor_data[pred_col].values
        
        metrics = calculate_all_metrics(y_true, y_pred)
        
        results.append({
            'sensor': sensor,
            'samples': len(sensor_data),
            'actual_anomalies': y_true.sum(),
            'predicted_anomalies': y_pred.sum(),
            **{k: v for k, v in metrics.items() if k != 'confusion_matrix'}
        })
    
    results_df = pd.DataFrame(results)
    logger.info(f"Calculated metrics for {len(sensors)} sensors")
    
    return results_df


def calculate_detection_latency(
    data: pd.DataFrame,
    true_col: str = 'is_anomaly',
    pred_col: str = 'predicted_anomaly',
    time_col: str = 'timestamp'
) -> Dict[str, float]:
    """
    Calculate detection latency metrics.
    
    Args:
        data: DataFrame with timestamps and predictions
        true_col: Column for ground truth
        pred_col: Column for predictions
        time_col: Column for timestamps
        
    Returns:
        Dictionary with latency statistics
    """
    logger.info("Calculating detection latency")
    
    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(data[time_col]):
        data[time_col] = pd.to_datetime(data[time_col])
    
    # Find true positives
    tp_data = data[(data[true_col] == 1) & (data[pred_col] == 1)]
    
    if tp_data.empty:
        logger.warning("No true positives found for latency calculation")
        return {
            'mean_latency_seconds': 0.0,
            'median_latency_seconds': 0.0,
            'max_latency_seconds': 0.0
        }
    
    # Calculate time differences (simplified - assumes sequential detection)
    # In production, would need more sophisticated latency tracking
    latencies = []
    
    # Group by sensor and calculate latency
    for sensor in tp_data['sensor_id'].unique() if 'sensor_id' in tp_data.columns else [None]:
        if sensor:
            sensor_tp = tp_data[tp_data['sensor_id'] == sensor].sort_values(time_col)
        else:
            sensor_tp = tp_data.sort_values(time_col)
        
        if len(sensor_tp) > 1:
            time_diffs = sensor_tp[time_col].diff().dt.total_seconds()
            latencies.extend(time_diffs.dropna().tolist())
    
    if not latencies:
        return {
            'mean_latency_seconds': 0.0,
            'median_latency_seconds': 0.0,
            'max_latency_seconds': 0.0
        }
    
    return {
        'mean_latency_seconds': float(np.mean(latencies)),
        'median_latency_seconds': float(np.median(latencies)),
        'max_latency_seconds': float(np.max(latencies))
    }
