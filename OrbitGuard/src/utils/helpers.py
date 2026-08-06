"""
Helper utility functions for Mission Watch.

This module provides common utility functions used across the application.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import json


def format_timestamp(
    timestamp: Union[str, datetime, pd.Timestamp],
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Format timestamp to string.
    
    Args:
        timestamp: Timestamp to format (string, datetime, or pandas Timestamp)
        format_str: Output format string
        
    Returns:
        Formatted timestamp string
    """
    if isinstance(timestamp, str):
        # Try to parse string to datetime
        try:
            timestamp = pd.to_datetime(timestamp)
        except Exception:
            return timestamp
    
    if isinstance(timestamp, (datetime, pd.Timestamp)):
        return timestamp.strftime(format_str)
    
    return str(timestamp)


def parse_timestamp(
    timestamp_str: str,
    format_str: Optional[str] = None
) -> pd.Timestamp:
    """
    Parse timestamp string to pandas Timestamp.
    
    Args:
        timestamp_str: Timestamp string to parse
        format_str: Optional format string (auto-detects if None)
        
    Returns:
        Pandas Timestamp object
    """
    if format_str:
        return pd.to_datetime(timestamp_str, format=format_str)
    else:
        return pd.to_datetime(timestamp_str)


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    return_dict: bool = True
) -> Union[Dict[str, float], tuple]:
    """
    Calculate classification metrics (precision, recall, F1).
    
    Args:
        y_true: Ground truth labels (0 or 1)
        y_pred: Predicted labels (0 or 1)
        return_dict: If True, return dict; if False, return tuple
        
    Returns:
        Dictionary or tuple of (precision, recall, f1, accuracy)
    """
    # Convert to numpy arrays
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    # Calculate confusion matrix components
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    
    # Calculate metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    
    if return_dict:
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'accuracy': accuracy,
            'true_positives': int(tp),
            'false_positives': int(fp),
            'true_negatives': int(tn),
            'false_negatives': int(fn)
        }
    else:
        return precision, recall, f1, accuracy


def create_directory_structure(base_dir: Union[str, Path]) -> None:
    """
    Create standard Mission Watch directory structure.
    
    Args:
        base_dir: Base directory path
    """
    base_path = Path(base_dir)
    
    directories = [
        'data/raw',
        'data/processed',
        'data/anomalies',
        'logs',
        'logs/llm_audit',
        'models',
        'reports',
        'notebooks'
    ]
    
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)


def save_json(data: Any, file_path: Union[str, Path]) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save (must be JSON serializable)
        file_path: Output file path
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_json(file_path: Union[str, Path]) -> Any:
    """
    Load data from JSON file.
    
    Args:
        file_path: Input file path
        
    Returns:
        Loaded data
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def get_time_range(
    df: pd.DataFrame,
    timestamp_col: str = 'timestamp'
) -> Dict[str, Any]:
    """
    Get time range information from DataFrame.
    
    Args:
        df: DataFrame with timestamp column
        timestamp_col: Name of timestamp column
        
    Returns:
        Dictionary with time range info
    """
    if timestamp_col not in df.columns:
        return {}
    
    timestamps = pd.to_datetime(df[timestamp_col])
    
    return {
        'start': timestamps.min(),
        'end': timestamps.max(),
        'duration': timestamps.max() - timestamps.min(),
        'num_points': len(df)
    }


def filter_by_time_range(
    df: pd.DataFrame,
    start_time: Optional[Union[str, datetime]] = None,
    end_time: Optional[Union[str, datetime]] = None,
    timestamp_col: str = 'timestamp'
) -> pd.DataFrame:
    """
    Filter DataFrame by time range.
    
    Args:
        df: DataFrame with timestamp column
        start_time: Start time (inclusive)
        end_time: End time (inclusive)
        timestamp_col: Name of timestamp column
        
    Returns:
        Filtered DataFrame
    """
    if timestamp_col not in df.columns:
        return df
    
    df = df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    
    if start_time is not None:
        start_time = pd.to_datetime(start_time)
        df = df[df[timestamp_col] >= start_time]
    
    if end_time is not None:
        end_time = pd.to_datetime(end_time)
        df = df[df[timestamp_col] <= end_time]
    
    return df


def aggregate_by_channel(
    df: pd.DataFrame,
    value_col: str = 'value',
    channel_col: str = 'sensor_id'
) -> pd.DataFrame:
    """
    Aggregate statistics by channel.
    
    Args:
        df: DataFrame with channel and value columns
        value_col: Name of value column
        channel_col: Name of channel column
        
    Returns:
        DataFrame with aggregated statistics per channel
    """
    if channel_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    
    agg_stats = df.groupby(channel_col)[value_col].agg([
        ('count', 'count'),
        ('mean', 'mean'),
        ('std', 'std'),
        ('min', 'min'),
        ('max', 'max'),
        ('median', 'median')
    ]).reset_index()
    
    return agg_stats


def detect_outliers_iqr(
    data: np.ndarray,
    multiplier: float = 1.5
) -> np.ndarray:
    """
    Detect outliers using Interquartile Range (IQR) method.
    
    Args:
        data: Input data array
        multiplier: IQR multiplier (typically 1.5 or 3.0)
        
    Returns:
        Boolean array indicating outliers (True = outlier)
    """
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr
    
    outliers = (data < lower_bound) | (data > upper_bound)
    
    return outliers


def detect_outliers_zscore(
    data: np.ndarray,
    threshold: float = 3.0
) -> np.ndarray:
    """
    Detect outliers using Z-score method.
    
    Args:
        data: Input data array
        threshold: Z-score threshold (typically 2.5 or 3.0)
        
    Returns:
        Boolean array indicating outliers (True = outlier)
    """
    mean = np.mean(data)
    std = np.std(data)
    
    if std == 0:
        return np.zeros(len(data), dtype=bool)
    
    z_scores = np.abs((data - mean) / std)
    outliers = z_scores > threshold
    
    return outliers


def sliding_window(
    data: np.ndarray,
    window_size: int,
    step_size: int = 1
) -> np.ndarray:
    """
    Create sliding windows from 1D array.
    
    Args:
        data: Input 1D array
        window_size: Size of each window
        step_size: Step size between windows
        
    Returns:
        2D array of shape (num_windows, window_size)
    """
    if len(data) < window_size:
        return np.array([])
    
    num_windows = (len(data) - window_size) // step_size + 1
    windows = np.zeros((num_windows, window_size))
    
    for i in range(num_windows):
        start_idx = i * step_size
        end_idx = start_idx + window_size
        windows[i] = data[start_idx:end_idx]
    
    return windows


def normalize_data(
    data: np.ndarray,
    method: str = 'minmax'
) -> tuple:
    """
    Normalize data using specified method.
    
    Args:
        data: Input data array
        method: Normalization method ('minmax' or 'zscore')
        
    Returns:
        Tuple of (normalized_data, normalization_params)
    """
    if method == 'minmax':
        min_val = np.min(data)
        max_val = np.max(data)
        
        if max_val - min_val == 0:
            normalized = np.zeros_like(data)
        else:
            normalized = (data - min_val) / (max_val - min_val)
        
        params = {'method': 'minmax', 'min': min_val, 'max': max_val}
    
    elif method == 'zscore':
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            normalized = np.zeros_like(data)
        else:
            normalized = (data - mean) / std
        
        params = {'method': 'zscore', 'mean': mean, 'std': std}
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    return normalized, params


def denormalize_data(
    normalized_data: np.ndarray,
    params: Dict[str, Any]
) -> np.ndarray:
    """
    Denormalize data using stored parameters.
    
    Args:
        normalized_data: Normalized data array
        params: Normalization parameters from normalize_data()
        
    Returns:
        Denormalized data array
    """
    method = params['method']
    
    if method == 'minmax':
        min_val = params['min']
        max_val = params['max']
        return normalized_data * (max_val - min_val) + min_val
    
    elif method == 'zscore':
        mean = params['mean']
        std = params['std']
        return normalized_data * std + mean
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_number(num: Union[int, float], precision: int = 2) -> str:
    """
    Format number with thousands separator.
    
    Args:
        num: Number to format
        precision: Decimal precision for floats
        
    Returns:
        Formatted number string
    """
    if isinstance(num, int):
        return f"{num:,}"
    else:
        return f"{num:,.{precision}f}"


def get_file_size(file_path: Union[str, Path]) -> str:
    """
    Get human-readable file size.
    
    Args:
        file_path: Path to file
        
    Returns:
        Formatted file size string
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return "0 B"
    
    size_bytes = file_path.stat().st_size
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if denominator is zero
        
    Returns:
        Division result or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: Input list
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]