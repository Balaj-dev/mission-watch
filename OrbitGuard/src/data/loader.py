"""
Data loading module for NASA SMAP/MSL telemetry datasets.

This module handles loading raw telemetry data from local storage.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import setup_logger
from src.utils.config_loader import get_config_value

logger = setup_logger(__name__)


def load_telemetry_data(file_path: str) -> pd.DataFrame:
    """
    Load raw telemetry data from CSV/JSON file.
    
    Args:
        file_path: Path to the telemetry data file
        
    Returns:
        DataFrame containing telemetry data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Telemetry data file not found: {file_path}")
    
    logger.info(f"Loading telemetry data from {file_path}")
    
    # Determine file type and load accordingly
    if file_path.suffix == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix == '.json':
        df = pd.read_json(file_path)
    elif file_path.suffix == '.parquet':
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    # Convert timestamp column to datetime if present
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    logger.info(f"Loaded {len(df):,} records from {file_path.name}")
    
    return df


def load_batch(
    data_dir: str,
    date_range: Optional[tuple] = None,
    pattern: str = "*.csv"
) -> pd.DataFrame:
    """
    Load multiple telemetry files by date range.
    
    Args:
        data_dir: Directory containing telemetry files
        date_range: Optional tuple of (start_date, end_date) as strings or datetime
        pattern: File pattern to match (default: "*.csv")
        
    Returns:
        Combined DataFrame from multiple files
        
    Raises:
        FileNotFoundError: If directory doesn't exist
        ValueError: If no files found matching pattern
    """
    data_dir = Path(data_dir)
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    logger.info(f"Loading batch data from {data_dir}")
    
    # Find all matching files
    files = list(data_dir.glob(pattern))
    
    if not files:
        raise ValueError(f"No files found matching pattern '{pattern}' in {data_dir}")
    
    logger.info(f"Found {len(files)} files matching pattern '{pattern}'")
    
    # Load all files
    dfs = []
    for file_path in files:
        try:
            df = load_telemetry_data(str(file_path))
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Failed to load {file_path.name}: {e}")
    
    if not dfs:
        raise ValueError("No files could be loaded successfully")
    
    # Combine all DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Filter by date range if provided
    if date_range is not None and 'timestamp' in combined_df.columns:
        start_date, end_date = date_range
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        combined_df = combined_df[
            (combined_df['timestamp'] >= start_date) &
            (combined_df['timestamp'] <= end_date)
        ]
        
        logger.info(f"Filtered to date range {start_date} to {end_date}")
    
    # Sort by timestamp if present
    if 'timestamp' in combined_df.columns:
        combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
    
    logger.info(f"Loaded total of {len(combined_df):,} records from {len(dfs)} files")
    
    return combined_df


def get_available_datasets(data_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List available local telemetry datasets.
    
    Args:
        data_dir: Optional directory to search (uses config if not provided)
        
    Returns:
        List of dataset metadata dictionaries
    """
    if data_dir is None:
        # Try to get from config
        data_dir = get_config_value('data.processed_dir', 'data/processed')
    
    data_dir = Path(data_dir)
    
    if not data_dir.exists():
        logger.warning(f"Data directory not found: {data_dir}")
        return []
    
    datasets = []
    
    # Search for CSV, JSON, and Parquet files
    for pattern in ['*.csv', '*.json', '*.parquet']:
        for file_path in data_dir.glob(pattern):
            try:
                # Get file metadata
                stat = file_path.stat()
                
                # Try to peek at the data
                if file_path.suffix == '.csv':
                    df_sample = pd.read_csv(file_path, nrows=5)
                elif file_path.suffix == '.json':
                    df_sample = pd.read_json(file_path, lines=True, nrows=5)
                elif file_path.suffix == '.parquet':
                    df_sample = pd.read_parquet(file_path)
                    df_sample = df_sample.head(5)
                else:
                    continue
                
                dataset_info = {
                    'name': file_path.name,
                    'path': str(file_path),
                    'size_bytes': stat.st_size,
                    'size_mb': stat.st_size / (1024 * 1024),
                    'modified': stat.st_mtime,
                    'columns': list(df_sample.columns),
                    'num_columns': len(df_sample.columns),
                    'format': file_path.suffix[1:]  # Remove leading dot
                }
                
                # Try to get row count for CSV
                if file_path.suffix == '.csv':
                    with open(file_path, 'r') as f:
                        row_count = sum(1 for _ in f) - 1  # Subtract header
                    dataset_info['num_rows'] = row_count
                
                datasets.append(dataset_info)
                
            except Exception as e:
                logger.warning(f"Could not read metadata for {file_path.name}: {e}")
    
    # Sort by modification time (newest first)
    datasets.sort(key=lambda x: x['modified'], reverse=True)
    
    logger.info(f"Found {len(datasets)} datasets in {data_dir}")
    
    return datasets


def load_processed_dataset(dataset_name: str = "telemetry_dataset.csv") -> pd.DataFrame:
    """
    Load the processed telemetry dataset.
    
    This is a convenience function that loads from the standard processed data directory.
    
    Args:
        dataset_name: Name of the dataset file
        
    Returns:
        DataFrame containing processed telemetry data
    """
    processed_dir = get_config_value('data.processed_dir', 'data/processed')
    file_path = Path(processed_dir) / dataset_name
    
    return load_telemetry_data(str(file_path))


def load_anomalies(anomaly_file: str) -> pd.DataFrame:
    """
    Load detected anomalies from file.
    
    Args:
        anomaly_file: Path to anomaly file
        
    Returns:
        DataFrame containing anomaly records
    """
    return load_telemetry_data(anomaly_file)


def save_telemetry_data(df: pd.DataFrame, file_path: str, format: str = 'csv') -> None:
    """
    Save telemetry data to file.
    
    Args:
        df: DataFrame to save
        file_path: Output file path
        format: Output format ('csv', 'json', 'parquet')
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving {len(df):,} records to {file_path}")
    
    if format == 'csv':
        df.to_csv(file_path, index=False)
    elif format == 'json':
        df.to_json(file_path, orient='records', lines=True)
    elif format == 'parquet':
        df.to_parquet(file_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    logger.info(f"Successfully saved data to {file_path}")


def get_channel_data(df: pd.DataFrame, channel_id: str) -> pd.DataFrame:
    """
    Extract data for a specific channel/sensor.
    
    Args:
        df: Telemetry DataFrame
        channel_id: Channel/sensor identifier
        
    Returns:
        DataFrame filtered to specified channel
    """
    if 'sensor_id' not in df.columns:
        logger.warning("DataFrame does not have 'sensor_id' column")
        return pd.DataFrame()
    
    channel_df = df[df['sensor_id'] == channel_id].copy()
    
    logger.info(f"Extracted {len(channel_df):,} records for channel {channel_id}")
    
    return channel_df


def get_channels_list(df: pd.DataFrame) -> List[str]:
    """
    Get list of unique channels/sensors in dataset.
    
    Args:
        df: Telemetry DataFrame
        
    Returns:
        List of channel identifiers
    """
    if 'sensor_id' not in df.columns:
        logger.warning("DataFrame does not have 'sensor_id' column")
        return []
    
    channels = df['sensor_id'].unique().tolist()
    
    logger.info(f"Found {len(channels)} unique channels")
    
    return channels