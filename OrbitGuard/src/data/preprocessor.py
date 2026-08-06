"""
Data preprocessing module for telemetry data.

This module handles cleaning, feature extraction, and transformation of telemetry data.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import setup_logger
from src.utils.helpers import normalize_data, sliding_window

logger = setup_logger(__name__)


def clean_telemetry(
    df: pd.DataFrame,
    handle_missing: str = 'interpolate',
    remove_duplicates: bool = True
) -> pd.DataFrame:
    """
    Clean telemetry data by handling missing values and duplicates.
    
    Args:
        df: Input telemetry DataFrame
        handle_missing: Method to handle missing values ('drop', 'interpolate', 'forward_fill')
        remove_duplicates: Whether to remove duplicate timestamps
        
    Returns:
        Cleaned DataFrame
    """
    logger.info(f"Cleaning telemetry data: {len(df):,} records")
    
    df_clean = df.copy()
    
    # Remove duplicates based on timestamp and sensor_id
    if remove_duplicates and 'timestamp' in df_clean.columns and 'sensor_id' in df_clean.columns:
        before_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=['timestamp', 'sensor_id'], keep='first')
        removed = before_count - len(df_clean)
        if removed > 0:
            logger.info(f"Removed {removed:,} duplicate records")
    
    # Handle missing values in 'value' column
    if 'value' in df_clean.columns:
        missing_count = df_clean['value'].isna().sum()
        
        if missing_count > 0:
            logger.info(f"Found {missing_count:,} missing values")
            
            if handle_missing == 'drop':
                df_clean = df_clean.dropna(subset=['value'])
                logger.info(f"Dropped rows with missing values")
            
            elif handle_missing == 'interpolate':
                # Interpolate within each sensor group
                if 'sensor_id' in df_clean.columns:
                    df_clean['value'] = df_clean.groupby('sensor_id')['value'].transform(
                        lambda x: x.interpolate(method='linear', limit_direction='both')
                    )
                else:
                    df_clean['value'] = df_clean['value'].interpolate(method='linear', limit_direction='both')
                logger.info(f"Interpolated missing values")
            
            elif handle_missing == 'forward_fill':
                if 'sensor_id' in df_clean.columns:
                    df_clean['value'] = df_clean.groupby('sensor_id')['value'].transform(
                        lambda x: x.fillna(method='ffill').fillna(method='bfill')
                    )
                else:
                    df_clean['value'] = df_clean['value'].fillna(method='ffill').fillna(method='bfill')
                logger.info(f"Forward-filled missing values")
    
    logger.info(f"Cleaning complete: {len(df_clean):,} records remaining")
    
    return df_clean


def extract_features(
    df: pd.DataFrame,
    window_size: int = 10,
    include_statistical: bool = True,
    include_temporal: bool = True
) -> pd.DataFrame:
    """
    Extract features from telemetry data for anomaly detection.
    
    Args:
        df: Input telemetry DataFrame
        window_size: Size of rolling window for feature extraction
        include_statistical: Include statistical features (mean, std, etc.)
        include_temporal: Include temporal features (hour, day of week, etc.)
        
    Returns:
        DataFrame with extracted features
    """
    logger.info(f"Extracting features from {len(df):,} records")
    
    df_features = df.copy()
    
    # Ensure timestamp is datetime
    if 'timestamp' in df_features.columns:
        df_features['timestamp'] = pd.to_datetime(df_features['timestamp'])
    
    # Extract temporal features
    if include_temporal and 'timestamp' in df_features.columns:
        df_features['hour'] = df_features['timestamp'].dt.hour
        df_features['day_of_week'] = df_features['timestamp'].dt.dayofweek
        df_features['day_of_month'] = df_features['timestamp'].dt.day
        df_features['month'] = df_features['timestamp'].dt.month
        
        # Cyclical encoding for hour (24-hour cycle)
        df_features['hour_sin'] = np.sin(2 * np.pi * df_features['hour'] / 24)
        df_features['hour_cos'] = np.cos(2 * np.pi * df_features['hour'] / 24)
        
        # Cyclical encoding for day of week (7-day cycle)
        df_features['dow_sin'] = np.sin(2 * np.pi * df_features['day_of_week'] / 7)
        df_features['dow_cos'] = np.cos(2 * np.pi * df_features['day_of_week'] / 7)
        
        logger.info("Extracted temporal features")
    
    # Extract statistical features using rolling windows
    if include_statistical and 'value' in df_features.columns:
        # Group by sensor_id if present
        if 'sensor_id' in df_features.columns:
            for sensor_id in df_features['sensor_id'].unique():
                mask = df_features['sensor_id'] == sensor_id
                sensor_values = df_features.loc[mask, 'value']
                
                # Rolling statistics
                df_features.loc[mask, 'rolling_mean'] = sensor_values.rolling(
                    window=window_size, min_periods=1
                ).mean()
                
                df_features.loc[mask, 'rolling_std'] = sensor_values.rolling(
                    window=window_size, min_periods=1
                ).std()
                
                df_features.loc[mask, 'rolling_min'] = sensor_values.rolling(
                    window=window_size, min_periods=1
                ).min()
                
                df_features.loc[mask, 'rolling_max'] = sensor_values.rolling(
                    window=window_size, min_periods=1
                ).max()
                
                # Rate of change
                df_features.loc[mask, 'value_diff'] = sensor_values.diff()
                df_features.loc[mask, 'value_pct_change'] = sensor_values.pct_change()
        else:
            # No sensor grouping
            df_features['rolling_mean'] = df_features['value'].rolling(
                window=window_size, min_periods=1
            ).mean()
            
            df_features['rolling_std'] = df_features['value'].rolling(
                window=window_size, min_periods=1
            ).std()
            
            df_features['rolling_min'] = df_features['value'].rolling(
                window=window_size, min_periods=1
            ).min()
            
            df_features['rolling_max'] = df_features['value'].rolling(
                window=window_size, min_periods=1
            ).max()
            
            df_features['value_diff'] = df_features['value'].diff()
            df_features['value_pct_change'] = df_features['value'].pct_change()
        
        # Fill NaN values from rolling operations
        df_features['rolling_std'] = df_features['rolling_std'].fillna(0)
        df_features['value_diff'] = df_features['value_diff'].fillna(0)
        df_features['value_pct_change'] = df_features['value_pct_change'].fillna(0)
        
        logger.info("Extracted statistical features")
    
    logger.info(f"Feature extraction complete: {len(df_features.columns)} columns")
    
    return df_features


def normalize_timestamps(
    df: pd.DataFrame,
    freq: str = '1min',
    method: str = 'interpolate'
) -> pd.DataFrame:
    """
    Normalize timestamps to regular intervals.
    
    Args:
        df: Input telemetry DataFrame
        freq: Target frequency (e.g., '1min', '5min', '1H')
        method: Method to handle gaps ('interpolate', 'forward_fill', 'drop')
        
    Returns:
        DataFrame with normalized timestamps
    """
    if 'timestamp' not in df.columns:
        logger.warning("No timestamp column found, skipping normalization")
        return df
    
    logger.info(f"Normalizing timestamps to {freq} intervals")
    
    df_norm = df.copy()
    df_norm['timestamp'] = pd.to_datetime(df_norm['timestamp'])
    
    # Group by sensor_id if present
    if 'sensor_id' in df_norm.columns:
        normalized_dfs = []
        
        for sensor_id in df_norm['sensor_id'].unique():
            sensor_df = df_norm[df_norm['sensor_id'] == sensor_id].copy()
            
            # Set timestamp as index
            sensor_df = sensor_df.set_index('timestamp')
            
            # Resample to target frequency
            if method == 'interpolate':
                sensor_df = sensor_df.resample(freq).interpolate(method='linear')
            elif method == 'forward_fill':
                sensor_df = sensor_df.resample(freq).ffill()
            elif method == 'drop':
                sensor_df = sensor_df.resample(freq).first()
            
            # Reset index
            sensor_df = sensor_df.reset_index()
            sensor_df['sensor_id'] = sensor_id
            
            normalized_dfs.append(sensor_df)
        
        df_norm = pd.concat(normalized_dfs, ignore_index=True)
    else:
        # No sensor grouping
        df_norm = df_norm.set_index('timestamp')
        
        if method == 'interpolate':
            df_norm = df_norm.resample(freq).interpolate(method='linear')
        elif method == 'forward_fill':
            df_norm = df_norm.resample(freq).ffill()
        elif method == 'drop':
            df_norm = df_norm.resample(freq).first()
        
        df_norm = df_norm.reset_index()
    
    logger.info(f"Timestamp normalization complete: {len(df_norm):,} records")
    
    return df_norm


def create_sliding_windows(
    df: pd.DataFrame,
    window_size: int,
    step_size: int = 1,
    value_col: str = 'value'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create sliding windows from time series data.
    
    Args:
        df: Input telemetry DataFrame
        window_size: Size of each window
        step_size: Step size between windows
        value_col: Name of value column
        
    Returns:
        Tuple of (windows, labels) where windows is 2D array and labels are corresponding labels
    """
    logger.info(f"Creating sliding windows: size={window_size}, step={step_size}")
    
    if value_col not in df.columns:
        raise ValueError(f"Column '{value_col}' not found in DataFrame")
    
    # Group by sensor_id if present
    if 'sensor_id' in df.columns:
        all_windows = []
        all_labels = []
        
        for sensor_id in df['sensor_id'].unique():
            sensor_df = df[df['sensor_id'] == sensor_id].copy()
            sensor_df = sensor_df.sort_values('timestamp') if 'timestamp' in sensor_df.columns else sensor_df
            
            values = sensor_df[value_col].values
            labels = sensor_df['is_anomaly'].values if 'is_anomaly' in sensor_df.columns else np.zeros(len(values))
            
            # Create windows
            windows = sliding_window(values, window_size, step_size)
            
            # Create corresponding labels (use max label in window)
            window_labels = []
            for i in range(len(windows)):
                start_idx = i * step_size
                end_idx = start_idx + window_size
                window_label = np.max(labels[start_idx:end_idx])
                window_labels.append(window_label)
            
            all_windows.append(windows)
            all_labels.extend(window_labels)
        
        windows_array = np.vstack(all_windows)
        labels_array = np.array(all_labels)
    else:
        # No sensor grouping
        df = df.sort_values('timestamp') if 'timestamp' in df.columns else df
        
        values = df[value_col].values
        labels = df['is_anomaly'].values if 'is_anomaly' in df.columns else np.zeros(len(values))
        
        windows_array = sliding_window(values, window_size, step_size)
        
        # Create corresponding labels
        window_labels = []
        for i in range(len(windows_array)):
            start_idx = i * step_size
            end_idx = start_idx + window_size
            window_label = np.max(labels[start_idx:end_idx])
            window_labels.append(window_label)
        
        labels_array = np.array(window_labels)
    
    logger.info(f"Created {len(windows_array):,} windows")
    
    return windows_array, labels_array


def normalize_features(
    df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    method: str = 'zscore'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Normalize feature columns.
    
    Args:
        df: Input DataFrame
        feature_cols: List of columns to normalize (auto-detects if None)
        method: Normalization method ('zscore' or 'minmax')
        
    Returns:
        Tuple of (normalized_df, normalization_params)
    """
    logger.info(f"Normalizing features using {method} method")
    
    df_norm = df.copy()
    norm_params = {}
    
    # Auto-detect numeric columns if not specified
    if feature_cols is None:
        feature_cols = df_norm.select_dtypes(include=[np.number]).columns.tolist()
        # Exclude label columns
        feature_cols = [col for col in feature_cols if col not in ['is_anomaly', 'anomaly_score']]
    
    # Normalize each feature
    for col in feature_cols:
        if col in df_norm.columns:
            values = df_norm[col].values
            normalized_values, params = normalize_data(values, method=method)
            df_norm[col] = normalized_values
            norm_params[col] = params
    
    logger.info(f"Normalized {len(feature_cols)} features")
    
    return df_norm, norm_params


def prepare_for_training(
    df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    normalize: bool = True,
    handle_missing: str = 'interpolate'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Prepare telemetry data for model training.
    
    This is a convenience function that combines cleaning, feature extraction, and normalization.
    
    Args:
        df: Input telemetry DataFrame
        feature_cols: List of feature columns to use (auto-detects if None)
        normalize: Whether to normalize features
        handle_missing: Method to handle missing values
        
    Returns:
        Tuple of (prepared_df, metadata)
    """
    logger.info("Preparing data for training")
    
    # Clean data
    df_clean = clean_telemetry(df, handle_missing=handle_missing)
    
    # Extract features
    df_features = extract_features(df_clean)
    
    # Normalize if requested
    metadata = {}
    if normalize:
        df_prepared, norm_params = normalize_features(df_features, feature_cols=feature_cols)
        metadata['normalization_params'] = norm_params
    else:
        df_prepared = df_features
    
    metadata['num_records'] = len(df_prepared)
    metadata['num_features'] = len(df_prepared.columns)
    metadata['feature_columns'] = list(df_prepared.columns)
    
    logger.info(f"Data preparation complete: {len(df_prepared):,} records, {len(df_prepared.columns)} features")
    
    return df_prepared, metadata