"""
Anomaly scoring and ranking module.

This module provides functions to score, rank, and filter detected anomalies.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logger import setup_logger
from src.utils.config_loader import get_config_value

logger = setup_logger(__name__)


def calculate_anomaly_score(
    df: pd.DataFrame,
    score_col: str = 'anomaly_score',
    value_col: str = 'value',
    use_context: bool = True,
    context_window: int = 10
) -> pd.DataFrame:
    """
    Calculate comprehensive anomaly scores combining multiple factors.
    
    Args:
        df: DataFrame with anomaly predictions
        score_col: Column containing base anomaly scores
        value_col: Column containing telemetry values
        use_context: Whether to incorporate contextual information
        context_window: Window size for contextual scoring
        
    Returns:
        DataFrame with enhanced anomaly scores
    """
    logger.info(f"Calculating anomaly scores for {len(df):,} records")
    
    df_scored = df.copy()
    
    # Ensure base score exists
    if score_col not in df_scored.columns:
        logger.warning(f"Score column '{score_col}' not found, using predictions")
        if 'predicted_anomaly' in df_scored.columns:
            df_scored[score_col] = df_scored['predicted_anomaly'].astype(float)
        else:
            df_scored[score_col] = 0.0
    
    # Initialize final score with base score
    df_scored['final_anomaly_score'] = df_scored[score_col]
    
    if use_context and value_col in df_scored.columns:
        # Group by sensor if available
        if 'sensor_id' in df_scored.columns:
            for sensor_id in df_scored['sensor_id'].unique():
                mask = df_scored['sensor_id'] == sensor_id
                sensor_df = df_scored[mask].copy()
                
                # Calculate contextual factors
                contextual_score = _calculate_contextual_score(
                    sensor_df[value_col].values,
                    sensor_df[score_col].values,
                    context_window
                )
                
                df_scored.loc[mask, 'contextual_score'] = contextual_score
        else:
            # No sensor grouping
            contextual_score = _calculate_contextual_score(
                df_scored[value_col].values,
                df_scored[score_col].values,
                context_window
            )
            df_scored['contextual_score'] = contextual_score
        
        # Combine base score with contextual score (weighted average)
        df_scored['final_anomaly_score'] = (
            0.7 * df_scored[score_col] + 
            0.3 * df_scored['contextual_score']
        )
    
    # Add severity level based on score
    df_scored['severity'] = pd.cut(
        df_scored['final_anomaly_score'],
        bins=[0, 0.3, 0.6, 0.8, 1.0],
        labels=['low', 'medium', 'high', 'critical'],
        include_lowest=True
    )
    
    logger.info("Anomaly scoring complete")
    
    return df_scored


def _calculate_contextual_score(
    values: np.ndarray,
    base_scores: np.ndarray,
    window_size: int
) -> np.ndarray:
    """
    Calculate contextual anomaly scores based on surrounding data.
    
    Args:
        values: Array of telemetry values
        base_scores: Array of base anomaly scores
        window_size: Size of context window
        
    Returns:
        Array of contextual scores
    """
    contextual_scores = np.zeros(len(values))
    
    for i in range(len(values)):
        # Define window bounds
        start_idx = max(0, i - window_size // 2)
        end_idx = min(len(values), i + window_size // 2 + 1)
        
        # Get window data
        window_values = values[start_idx:end_idx]
        window_scores = base_scores[start_idx:end_idx]
        
        # Calculate contextual factors
        
        # 1. Deviation from local mean
        local_mean = np.mean(window_values)
        local_std = np.std(window_values)
        if local_std > 0:
            deviation_score = abs(values[i] - local_mean) / local_std
            deviation_score = min(deviation_score / 3.0, 1.0)  # Normalize
        else:
            deviation_score = 0.0
        
        # 2. Isolation (how different from neighbors)
        if len(window_values) > 1:
            neighbor_diff = np.abs(values[i] - window_values).mean()
            max_diff = np.abs(window_values).max() - np.abs(window_values).min()
            if max_diff > 0:
                isolation_score = neighbor_diff / max_diff
            else:
                isolation_score = 0.0
        else:
            isolation_score = 0.0
        
        # 3. Persistence (nearby anomalies)
        persistence_score = np.mean(window_scores)
        
        # Combine contextual factors
        contextual_scores[i] = (
            0.4 * deviation_score +
            0.3 * isolation_score +
            0.3 * persistence_score
        )
    
    return contextual_scores


def rank_anomalies(
    df: pd.DataFrame,
    score_col: str = 'final_anomaly_score',
    top_n: Optional[int] = None,
    min_score: Optional[float] = None
) -> pd.DataFrame:
    """
    Rank anomalies by score and optionally filter.
    
    Args:
        df: DataFrame with anomaly scores
        score_col: Column to rank by
        top_n: Optional number of top anomalies to return
        min_score: Optional minimum score threshold
        
    Returns:
        DataFrame sorted by anomaly score (highest first)
    """
    logger.info(f"Ranking anomalies from {len(df):,} records")
    
    # Filter to only anomalies if prediction column exists
    if 'predicted_anomaly' in df.columns:
        df_anomalies = df[df['predicted_anomaly'] == 1].copy()
    else:
        df_anomalies = df.copy()
    
    # Apply minimum score filter if specified
    if min_score is not None:
        df_anomalies = df_anomalies[df_anomalies[score_col] >= min_score]
        logger.info(f"Filtered to {len(df_anomalies):,} anomalies with score >= {min_score}")
    
    # Sort by score (descending)
    df_ranked = df_anomalies.sort_values(score_col, ascending=False).reset_index(drop=True)
    
    # Add rank column
    df_ranked['anomaly_rank'] = range(1, len(df_ranked) + 1)
    
    # Return top N if specified
    if top_n is not None:
        df_ranked = df_ranked.head(top_n)
        logger.info(f"Returning top {top_n} anomalies")
    
    logger.info(f"Ranked {len(df_ranked):,} anomalies")
    
    return df_ranked


def filter_by_threshold(
    df: pd.DataFrame,
    threshold: float,
    score_col: str = 'final_anomaly_score'
) -> pd.DataFrame:
    """
    Filter anomalies by score threshold.
    
    Args:
        df: DataFrame with anomaly scores
        threshold: Minimum score threshold (0.0 to 1.0)
        score_col: Column containing scores
        
    Returns:
        DataFrame filtered to anomalies above threshold
    """
    logger.info(f"Filtering anomalies with threshold={threshold}")
    
    if score_col not in df.columns:
        logger.warning(f"Score column '{score_col}' not found")
        return df
    
    df_filtered = df[df[score_col] >= threshold].copy()
    
    logger.info(f"Filtered to {len(df_filtered):,} anomalies (from {len(df):,})")
    
    return df_filtered


def filter_by_severity(
    df: pd.DataFrame,
    min_severity: str = 'medium'
) -> pd.DataFrame:
    """
    Filter anomalies by severity level.
    
    Args:
        df: DataFrame with severity column
        min_severity: Minimum severity level ('low', 'medium', 'high', 'critical')
        
    Returns:
        DataFrame filtered to specified severity and above
    """
    logger.info(f"Filtering anomalies with min_severity={min_severity}")
    
    if 'severity' not in df.columns:
        logger.warning("Severity column not found")
        return df
    
    severity_order = ['low', 'medium', 'high', 'critical']
    
    if min_severity not in severity_order:
        logger.warning(f"Invalid severity level: {min_severity}")
        return df
    
    min_level = severity_order.index(min_severity)
    
    # Filter to specified severity and above
    df_filtered = df[
        df['severity'].apply(lambda x: severity_order.index(x) >= min_level)
    ].copy()
    
    logger.info(f"Filtered to {len(df_filtered):,} anomalies (from {len(df):,})")
    
    return df_filtered


def group_anomalies_by_sequence(
    df: pd.DataFrame,
    max_gap: int = 5,
    timestamp_col: str = 'timestamp'
) -> List[pd.DataFrame]:
    """
    Group consecutive anomalies into sequences.
    
    Args:
        df: DataFrame with anomalies (must be sorted by timestamp)
        max_gap: Maximum gap (in records) to consider part of same sequence
        timestamp_col: Name of timestamp column
        
    Returns:
        List of DataFrames, each representing an anomaly sequence
    """
    logger.info(f"Grouping {len(df):,} anomalies into sequences")
    
    if len(df) == 0:
        return []
    
    # Ensure sorted by timestamp
    if timestamp_col in df.columns:
        df = df.sort_values(timestamp_col).reset_index(drop=True)
    
    sequences = []
    current_sequence = [df.iloc[0]]
    
    for i in range(1, len(df)):
        # Check if this anomaly is close to previous one
        gap = i - df.index[i-1]
        
        if gap <= max_gap:
            # Part of current sequence
            current_sequence.append(df.iloc[i])
        else:
            # Start new sequence
            if current_sequence:
                sequences.append(pd.DataFrame(current_sequence))
            current_sequence = [df.iloc[i]]
    
    # Add final sequence
    if current_sequence:
        sequences.append(pd.DataFrame(current_sequence))
    
    logger.info(f"Grouped into {len(sequences)} sequences")
    
    return sequences


def summarize_anomalies(
    df: pd.DataFrame,
    group_by: Optional[str] = 'sensor_id'
) -> pd.DataFrame:
    """
    Generate summary statistics for anomalies.
    
    Args:
        df: DataFrame with anomalies
        group_by: Optional column to group by (e.g., 'sensor_id', 'severity')
        
    Returns:
        DataFrame with summary statistics
    """
    logger.info("Generating anomaly summary")
    
    if group_by and group_by in df.columns:
        # Group by specified column
        summary = df.groupby(group_by).agg({
            'final_anomaly_score': ['count', 'mean', 'max', 'min'],
            'value': ['mean', 'std', 'min', 'max']
        }).reset_index()
        
        # Flatten column names
        summary.columns = [
            group_by,
            'anomaly_count',
            'avg_score',
            'max_score',
            'min_score',
            'avg_value',
            'std_value',
            'min_value',
            'max_value'
        ]
    else:
        # Overall summary
        summary = pd.DataFrame([{
            'anomaly_count': len(df),
            'avg_score': df['final_anomaly_score'].mean() if 'final_anomaly_score' in df.columns else 0,
            'max_score': df['final_anomaly_score'].max() if 'final_anomaly_score' in df.columns else 0,
            'min_score': df['final_anomaly_score'].min() if 'final_anomaly_score' in df.columns else 0,
            'avg_value': df['value'].mean() if 'value' in df.columns else 0,
            'std_value': df['value'].std() if 'value' in df.columns else 0,
            'min_value': df['value'].min() if 'value' in df.columns else 0,
            'max_value': df['value'].max() if 'value' in df.columns else 0
        }])
    
    logger.info(f"Generated summary with {len(summary)} rows")
    
    return summary


def get_top_anomalies_per_channel(
    df: pd.DataFrame,
    n_per_channel: int = 10,
    score_col: str = 'final_anomaly_score',
    channel_col: str = 'sensor_id'
) -> pd.DataFrame:
    """
    Get top N anomalies for each channel/sensor.
    
    Args:
        df: DataFrame with anomalies
        n_per_channel: Number of top anomalies per channel
        score_col: Column to rank by
        channel_col: Column identifying channels
        
    Returns:
        DataFrame with top anomalies per channel
    """
    logger.info(f"Getting top {n_per_channel} anomalies per channel")
    
    if channel_col not in df.columns:
        logger.warning(f"Channel column '{channel_col}' not found")
        return df.head(n_per_channel)
    
    # Get top N per channel
    top_anomalies = df.groupby(channel_col).apply(
        lambda x: x.nlargest(n_per_channel, score_col)
    ).reset_index(drop=True)
    
    logger.info(f"Selected {len(top_anomalies):,} top anomalies across channels")
    
    return top_anomalies


def calculate_anomaly_statistics(
    df: pd.DataFrame,
    score_col: str = 'final_anomaly_score'
) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics for anomalies.
    
    Args:
        df: DataFrame with anomalies
        score_col: Column containing anomaly scores
        
    Returns:
        Dictionary with statistics
    """
    logger.info("Calculating anomaly statistics")
    
    stats = {
        'total_anomalies': len(df),
        'score_statistics': {}
    }
    
    if score_col in df.columns:
        scores = df[score_col]
        stats['score_statistics'] = {
            'mean': float(scores.mean()),
            'median': float(scores.median()),
            'std': float(scores.std()),
            'min': float(scores.min()),
            'max': float(scores.max()),
            'q25': float(scores.quantile(0.25)),
            'q75': float(scores.quantile(0.75))
        }
    
    # Severity distribution
    if 'severity' in df.columns:
        severity_counts = df['severity'].value_counts().to_dict()
        stats['severity_distribution'] = severity_counts
    
    # Channel distribution
    if 'sensor_id' in df.columns:
        channel_counts = df['sensor_id'].value_counts().to_dict()
        stats['channel_distribution'] = channel_counts
        stats['num_affected_channels'] = len(channel_counts)
    
    # Temporal distribution
    if 'timestamp' in df.columns:
        timestamps = pd.to_datetime(df['timestamp'])
        stats['temporal_statistics'] = {
            'start': str(timestamps.min()),
            'end': str(timestamps.max()),
            'duration': str(timestamps.max() - timestamps.min())
        }
        
        # Anomalies per hour
        df['hour'] = timestamps.dt.hour
        hourly_counts = df['hour'].value_counts().sort_index().to_dict()
        stats['hourly_distribution'] = hourly_counts
    
    logger.info("Statistics calculation complete")
    
    return stats


def prioritize_anomalies(
    df: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None
) -> pd.DataFrame:
    """
    Prioritize anomalies using weighted scoring.
    
    Args:
        df: DataFrame with anomalies
        weights: Optional dictionary of feature weights
        
    Returns:
        DataFrame with priority scores
    """
    logger.info("Prioritizing anomalies")
    
    # Default weights
    if weights is None:
        weights = {
            'anomaly_score': 0.4,
            'severity': 0.3,
            'persistence': 0.2,
            'impact': 0.1
        }
    
    df_prioritized = df.copy()
    
    # Calculate priority score
    priority_score = np.zeros(len(df))
    
    # Anomaly score component
    if 'final_anomaly_score' in df.columns:
        priority_score += weights.get('anomaly_score', 0.4) * df['final_anomaly_score']
    
    # Severity component
    if 'severity' in df.columns:
        severity_map = {'low': 0.25, 'medium': 0.5, 'high': 0.75, 'critical': 1.0}
        severity_scores = df['severity'].map(severity_map).fillna(0.5)
        priority_score += weights.get('severity', 0.3) * severity_scores
    
    # Add other components as needed
    
    df_prioritized['priority_score'] = priority_score
    df_prioritized['priority_rank'] = df_prioritized['priority_score'].rank(ascending=False, method='dense').astype(int)
    
    # Sort by priority
    df_prioritized = df_prioritized.sort_values('priority_score', ascending=False).reset_index(drop=True)
    
    logger.info(f"Prioritized {len(df_prioritized):,} anomalies")
    
    return df_prioritized


# Alias for compatibility (plural version)
def calculate_anomaly_scores(
    df: pd.DataFrame,
    score_col: str = 'anomaly_score',
    value_col: str = 'value',
    use_context: bool = True,
    context_window: int = 10
) -> pd.DataFrame:
    """
    Alias for calculate_anomaly_score (plural version for compatibility).
    
    Calculate comprehensive anomaly scores combining multiple factors.
    
    Args:
        df: DataFrame with anomaly predictions
        score_col: Column containing base anomaly scores
        value_col: Column containing telemetry values
        use_context: Whether to incorporate contextual information
        context_window: Window size for contextual scoring
        
    Returns:
        DataFrame with enhanced anomaly scores
    """
    return calculate_anomaly_score(df, score_col, value_col, use_context, context_window)