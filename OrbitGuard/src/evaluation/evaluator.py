"""
Evaluator module for comparing predictions against ground truth.

This module provides functions to evaluate anomaly detection models,
compare multiple models, and perform cross-validation.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import setup_logger
from src.evaluation.metrics import calculate_all_metrics, calculate_metrics_by_sensor

logger = setup_logger(__name__)


def evaluate_predictions(
    predictions: pd.DataFrame,
    ground_truth_col: str = 'is_anomaly',
    prediction_col: str = 'predicted_anomaly',
    score_col: Optional[str] = 'anomaly_score',
    sensor_col: Optional[str] = 'sensor_id'
) -> Dict[str, Any]:
    """
    Evaluate anomaly detection predictions against ground truth.
    
    Args:
        predictions: DataFrame containing predictions and ground truth
        ground_truth_col: Column name for ground truth labels
        prediction_col: Column name for predicted labels
        score_col: Optional column name for anomaly scores
        sensor_col: Optional column name for sensor grouping
        
    Returns:
        Dictionary containing evaluation results
    """
    logger.info("Evaluating predictions against ground truth")
    
    if ground_truth_col not in predictions.columns:
        raise ValueError(f"Ground truth column '{ground_truth_col}' not found in data")
    
    if prediction_col not in predictions.columns:
        raise ValueError(f"Prediction column '{prediction_col}' not found in data")
    
    # Extract arrays
    y_true = predictions[ground_truth_col].values
    y_pred = predictions[prediction_col].values
    y_scores = predictions[score_col].values if score_col and score_col in predictions.columns else None
    
    # Calculate overall metrics
    overall_metrics = calculate_all_metrics(y_true, y_pred, y_scores)
    
    # Calculate per-sensor metrics if sensor column provided
    per_sensor_metrics = None
    if sensor_col and sensor_col in predictions.columns:
        per_sensor_metrics = calculate_metrics_by_sensor(
            predictions,
            true_col=ground_truth_col,
            pred_col=prediction_col,
            sensor_col=sensor_col
        )
    
    # Summary statistics
    summary = {
        'total_samples': len(predictions),
        'actual_anomalies': int(y_true.sum()),
        'predicted_anomalies': int(y_pred.sum()),
        'actual_anomaly_rate': float(y_true.mean()),
        'predicted_anomaly_rate': float(y_pred.mean())
    }
    
    logger.info(f"Evaluation complete - F1: {overall_metrics['f1_score']:.4f}, "
               f"Precision: {overall_metrics['precision']:.4f}, "
               f"Recall: {overall_metrics['recall']:.4f}")
    
    return {
        'overall_metrics': overall_metrics,
        'per_sensor_metrics': per_sensor_metrics,
        'summary': summary
    }


def compare_models(
    predictions_list: List[pd.DataFrame],
    model_names: List[str],
    ground_truth_col: str = 'is_anomaly',
    prediction_col: str = 'predicted_anomaly',
    score_col: Optional[str] = 'anomaly_score'
) -> pd.DataFrame:
    """
    Compare performance of multiple models.
    
    Args:
        predictions_list: List of DataFrames with predictions from different models
        model_names: List of model names corresponding to predictions
        ground_truth_col: Column name for ground truth
        prediction_col: Column name for predictions
        score_col: Optional column name for scores
        
    Returns:
        DataFrame comparing model performance
    """
    logger.info(f"Comparing {len(predictions_list)} models")
    
    if len(predictions_list) != len(model_names):
        raise ValueError("Number of prediction DataFrames must match number of model names")
    
    comparison_results = []
    
    for model_name, predictions in zip(model_names, predictions_list):
        logger.debug(f"Evaluating model: {model_name}")
        
        y_true = predictions[ground_truth_col].values
        y_pred = predictions[prediction_col].values
        y_scores = predictions[score_col].values if score_col and score_col in predictions.columns else None
        
        metrics = calculate_all_metrics(y_true, y_pred, y_scores)
        
        result = {
            'model': model_name,
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'f1_score': metrics['f1_score'],
            'accuracy': metrics['accuracy'],
            'true_positives': metrics['confusion_matrix']['true_positives'],
            'false_positives': metrics['confusion_matrix']['false_positives'],
            'false_negatives': metrics['confusion_matrix']['false_negatives']
        }
        
        if 'roc_auc' in metrics:
            result['roc_auc'] = metrics['roc_auc']
        
        comparison_results.append(result)
    
    comparison_df = pd.DataFrame(comparison_results)
    
    # Rank models by F1 score
    comparison_df['rank'] = comparison_df['f1_score'].rank(ascending=False)
    comparison_df = comparison_df.sort_values('rank')
    
    logger.info("Model comparison complete")
    logger.info(f"Best model: {comparison_df.iloc[0]['model']} (F1: {comparison_df.iloc[0]['f1_score']:.4f})")
    
    return comparison_df


def cross_validate(
    data: pd.DataFrame,
    model_factory,
    n_folds: int = 5,
    ground_truth_col: str = 'is_anomaly',
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Perform k-fold cross-validation on anomaly detection model.
    
    Args:
        data: DataFrame with features and ground truth
        model_factory: Function that returns a new model instance
        n_folds: Number of cross-validation folds
        ground_truth_col: Column name for ground truth
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary with cross-validation results
    """
    logger.info(f"Performing {n_folds}-fold cross-validation")
    
    from sklearn.model_selection import KFold
    
    # Prepare data
    y = data[ground_truth_col].values
    
    # Initialize cross-validator
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    fold_results = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(data), 1):
        logger.debug(f"Processing fold {fold_idx}/{n_folds}")
        
        train_data = data.iloc[train_idx]
        test_data = data.iloc[test_idx]
        
        # Train model
        model = model_factory()
        
        try:
            if hasattr(model, 'train'):
                model.train(train_data)
            elif hasattr(model, 'fit'):
                model.fit(train_data)
            else:
                raise AttributeError("Model must have 'train' or 'fit' method")
            
            # Predict on test set
            if hasattr(model, 'predict'):
                y_pred = model.predict(test_data)
            else:
                raise AttributeError("Model must have 'predict' method")
            
            # Calculate metrics
            y_true_fold = test_data[ground_truth_col].values
            
            metrics = calculate_all_metrics(y_true_fold, y_pred)
            
            fold_results.append({
                'fold': fold_idx,
                'train_size': len(train_data),
                'test_size': len(test_data),
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'f1_score': metrics['f1_score'],
                'accuracy': metrics['accuracy']
            })
            
            logger.debug(f"Fold {fold_idx} - F1: {metrics['f1_score']:.4f}")
        
        except Exception as e:
            logger.error(f"Fold {fold_idx} failed: {str(e)}")
            fold_results.append({
                'fold': fold_idx,
                'error': str(e)
            })
    
    # Calculate aggregate statistics
    successful_folds = [r for r in fold_results if 'error' not in r]
    
    if not successful_folds:
        logger.error("All folds failed")
        return {
            'fold_results': fold_results,
            'mean_metrics': None,
            'std_metrics': None
        }
    
    fold_df = pd.DataFrame(successful_folds)
    
    mean_metrics = {
        'precision': fold_df['precision'].mean(),
        'recall': fold_df['recall'].mean(),
        'f1_score': fold_df['f1_score'].mean(),
        'accuracy': fold_df['accuracy'].mean()
    }
    
    std_metrics = {
        'precision': fold_df['precision'].std(),
        'recall': fold_df['recall'].std(),
        'f1_score': fold_df['f1_score'].std(),
        'accuracy': fold_df['accuracy'].std()
    }
    
    logger.info("Cross-validation complete")
    logger.info(f"Mean F1: {mean_metrics['f1_score']:.4f} ± {std_metrics['f1_score']:.4f}")
    
    return {
        'fold_results': fold_results,
        'mean_metrics': mean_metrics,
        'std_metrics': std_metrics,
        'n_folds': n_folds,
        'successful_folds': len(successful_folds)
    }


def evaluate_threshold_sensitivity(
    predictions: pd.DataFrame,
    score_col: str = 'anomaly_score',
    ground_truth_col: str = 'is_anomaly',
    thresholds: Optional[List[float]] = None
) -> pd.DataFrame:
    """
    Evaluate model performance across different anomaly score thresholds.
    
    Args:
        predictions: DataFrame with scores and ground truth
        score_col: Column name for anomaly scores
        ground_truth_col: Column name for ground truth
        thresholds: List of thresholds to evaluate (auto-generated if None)
        
    Returns:
        DataFrame with metrics for each threshold
    """
    logger.info("Evaluating threshold sensitivity")
    
    if score_col not in predictions.columns:
        raise ValueError(f"Score column '{score_col}' not found")
    
    # Generate thresholds if not provided
    if thresholds is None:
        thresholds = np.linspace(0.1, 0.9, 17)  # 0.1 to 0.9 in steps of 0.05
    
    y_true = predictions[ground_truth_col].values
    scores = predictions[score_col].values
    
    results = []
    
    for threshold in thresholds:
        # Apply threshold
        y_pred = (scores >= threshold).astype(int)
        
        # Calculate metrics
        metrics = calculate_all_metrics(y_true, y_pred)
        
        results.append({
            'threshold': threshold,
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'f1_score': metrics['f1_score'],
            'accuracy': metrics['accuracy'],
            'predicted_anomalies': y_pred.sum()
        })
    
    results_df = pd.DataFrame(results)
    
    # Find optimal threshold (max F1)
    optimal_idx = results_df['f1_score'].idxmax()
    optimal_threshold = results_df.loc[optimal_idx, 'threshold']
    optimal_f1 = results_df.loc[optimal_idx, 'f1_score']
    
    logger.info(f"Optimal threshold: {optimal_threshold:.2f} (F1: {optimal_f1:.4f})")
    
    return results_df


def calculate_error_analysis(
    predictions: pd.DataFrame,
    ground_truth_col: str = 'is_anomaly',
    prediction_col: str = 'predicted_anomaly',
    sensor_col: Optional[str] = 'sensor_id',
    value_col: Optional[str] = 'value'
) -> Dict[str, Any]:
    """
    Perform detailed error analysis on predictions.
    
    Args:
        predictions: DataFrame with predictions and ground truth
        ground_truth_col: Column for ground truth
        prediction_col: Column for predictions
        sensor_col: Optional sensor identifier column
        value_col: Optional value column for analysis
        
    Returns:
        Dictionary with error analysis results
    """
    logger.info("Performing error analysis")
    
    # Identify error types
    false_positives = predictions[
        (predictions[ground_truth_col] == 0) & 
        (predictions[prediction_col] == 1)
    ].copy()
    
    false_negatives = predictions[
        (predictions[ground_truth_col] == 1) & 
        (predictions[prediction_col] == 0)
    ].copy()
    
    analysis = {
        'false_positives': {
            'count': len(false_positives),
            'rate': len(false_positives) / len(predictions)
        },
        'false_negatives': {
            'count': len(false_negatives),
            'rate': len(false_negatives) / len(predictions)
        }
    }
    
    # Analyze by sensor if available
    if sensor_col and sensor_col in predictions.columns:
        fp_by_sensor = false_positives[sensor_col].value_counts().to_dict()
        fn_by_sensor = false_negatives[sensor_col].value_counts().to_dict()
        
        analysis['false_positives']['by_sensor'] = fp_by_sensor
        analysis['false_negatives']['by_sensor'] = fn_by_sensor
    
    # Analyze value distributions if available
    if value_col and value_col in predictions.columns:
        analysis['false_positives']['value_stats'] = {
            'mean': float(false_positives[value_col].mean()) if len(false_positives) > 0 else 0.0,
            'std': float(false_positives[value_col].std()) if len(false_positives) > 0 else 0.0
        }
        
        analysis['false_negatives']['value_stats'] = {
            'mean': float(false_negatives[value_col].mean()) if len(false_negatives) > 0 else 0.0,
            'std': float(false_negatives[value_col].std()) if len(false_negatives) > 0 else 0.0
        }
    
    logger.info(f"Error analysis complete - FP: {analysis['false_positives']['count']}, "
               f"FN: {analysis['false_negatives']['count']}")
    
    return analysis
