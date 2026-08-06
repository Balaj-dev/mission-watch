"""
Telemetry Data Loader for NASA SMAP/MSL Dataset

This script provides two options:
1. Download from Kaggle (requires Kaggle API setup)
2. Generate synthetic telemetry data with labeled anomalies for demo/testing

For production use with real NASA data, follow Kaggle setup instructions.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json


def generate_synthetic_telemetry(
    channel_id: str,
    n_points: int = 10000,
    anomaly_ratio: float = 0.05
) -> pd.DataFrame:
    """
    Generate synthetic telemetry data with realistic patterns and anomalies.
    
    Args:
        channel_id: Channel identifier
        n_points: Number of data points to generate
        anomaly_ratio: Proportion of points that should be anomalies
        
    Returns:
        DataFrame with synthetic telemetry and labeled anomalies
    """
    np.random.seed(hash(channel_id) % 2**32)  # Reproducible per channel
    
    # Generate base signal with trend and seasonality
    t = np.arange(n_points)
    
    # Base trend
    trend = 0.001 * t
    
    # Seasonal component (daily cycle)
    seasonal = 5 * np.sin(2 * np.pi * t / 1440)  # 1440 minutes = 1 day
    
    # Noise
    noise = np.random.normal(0, 0.5, n_points)
    
    # Combine components
    base_value = 50 + trend + seasonal + noise
    
    # Add anomalies
    n_anomalies = int(n_points * anomaly_ratio)
    anomaly_indices = np.random.choice(n_points, n_anomalies, replace=False)
    anomaly_indices.sort()
    
    # Create anomaly labels
    is_anomaly = np.zeros(n_points, dtype=int)
    
    # Group anomalies into sequences (3-10 consecutive points)
    anomaly_sequences = []
    i = 0
    while i < len(anomaly_indices):
        seq_length = np.random.randint(3, 11)
        seq_start = anomaly_indices[i]
        seq_end = min(seq_start + seq_length, n_points)
        
        # Mark sequence as anomaly
        is_anomaly[seq_start:seq_end] = 1
        anomaly_sequences.append((seq_start, seq_end))
        
        # Skip to next non-overlapping anomaly
        i += 1
        while i < len(anomaly_indices) and anomaly_indices[i] < seq_end:
            i += 1
    
    # Apply anomalies to values
    values = base_value.copy()
    for start, end in anomaly_sequences:
        # Different anomaly types
        anomaly_type = np.random.choice(['spike', 'drop', 'shift', 'noise'])
        
        if anomaly_type == 'spike':
            values[start:end] += np.random.uniform(10, 20)
        elif anomaly_type == 'drop':
            values[start:end] -= np.random.uniform(10, 20)
        elif anomaly_type == 'shift':
            values[start:end] += np.random.uniform(-15, 15)
        else:  # noise
            values[start:end] += np.random.normal(0, 5, end - start)
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=n_points, freq='1min'),
        'sensor_id': channel_id,
        'value': values,
        'is_anomaly': is_anomaly
    })
    
    # Add metadata
    df['subsystem'] = _get_subsystem(channel_id)
    df['spacecraft'] = _get_spacecraft(channel_id)
    
    return df


def _get_subsystem(channel_id: str) -> str:
    """Map channel ID to spacecraft subsystem."""
    subsystem_map = {
        'P': 'power',
        'S': 'solar',
        'E': 'electrical',
        'A': 'attitude',
        'D': 'dynamics',
        'M': 'mechanical',
        'T': 'thermal',
        'C': 'communications'
    }
    prefix = channel_id.split('-')[0]
    return subsystem_map.get(prefix, 'unknown')


def _get_spacecraft(channel_id: str) -> str:
    """Determine spacecraft from channel ID."""
    # SMAP channels: P, S, E, T
    # MSL channels: A, D, M, C
    smap_prefixes = ['P', 'S', 'E', 'T']
    prefix = channel_id.split('-')[0]
    return 'SMAP' if prefix in smap_prefixes else 'MSL'


def load_synthetic_dataset(
    channels: List[str] = None,
    n_points_per_channel: int = 10000
) -> pd.DataFrame:
    """
    Generate synthetic NASA SMAP/MSL-like telemetry dataset.
    
    This generates realistic synthetic data for demo/testing purposes.
    For production, use load_kaggle_dataset() with real NASA data.
    
    Args:
        channels: List of channel IDs to generate
        n_points_per_channel: Number of data points per channel
        
    Returns:
        DataFrame with synthetic telemetry and anomaly labels
    """
    # Default channels with clear anomalies
    if channels is None:
        channels = [
            "P-1",   # SMAP - Power subsystem
            "S-1",   # SMAP - Solar array
            "E-1",   # SMAP - Electrical
            "E-2",   # SMAP - Electrical
            "A-1",   # MSL - Attitude control
            "D-1",   # MSL - Dynamics
            "M-1",   # MSL - Mechanical
            "T-1",   # SMAP - Thermal
        ]
    
    print(f"\n🛰️  Generating Synthetic NASA SMAP/MSL Telemetry Dataset")
    print(f"   Channels: {len(channels)}")
    print(f"   Points per channel: {n_points_per_channel:,}")
    
    dfs = []
    for channel_id in channels:
        df = generate_synthetic_telemetry(channel_id, n_points_per_channel)
        dfs.append(df)
        
        anomaly_count = df['is_anomaly'].sum()
        anomaly_pct = (anomaly_count / len(df)) * 100
        print(f"   ✓ {channel_id}: {len(df):,} points, {anomaly_count:,} anomalies ({anomaly_pct:.2f}%)")
    
    # Combine all channels
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df = combined_df.sort_values(['timestamp', 'sensor_id']).reset_index(drop=True)
    
    print(f"\n✅ Synthetic dataset generated successfully!")
    print(f"   Total records: {len(combined_df):,}")
    print(f"   Total anomalies: {combined_df['is_anomaly'].sum():,}")
    print(f"   Channels: {combined_df['sensor_id'].nunique()}")
    
    return combined_df


def load_kaggle_dataset(data_dir: str = "data/raw/telemanom") -> pd.DataFrame:
    """
    Load real NASA SMAP/MSL telemetry dataset from Kaggle.
    
    Prerequisites:
    1. Install kaggle: pip install kaggle
    2. Setup Kaggle API credentials: https://github.com/Kaggle/kaggle-api#api-credentials
    3. Run download command (see instructions below)
    
    Download Instructions:
    ```bash
    pip install kaggle
    kaggle datasets download -d patrickfleith/nasa-anomaly-detection-dataset-smap-msl
    unzip nasa-anomaly-detection-dataset-smap-msl.zip -d data/raw/telemanom
    ```
    
    Args:
        data_dir: Directory containing downloaded Kaggle data
        
    Returns:
        DataFrame with real NASA telemetry and anomaly labels
    """
    data_path = Path(data_dir)
    
    print(f"\n🛰️  Loading Real NASA SMAP/MSL Telemetry Dataset from Kaggle")
    print(f"   Data directory: {data_path}")
    
    # Check if data exists
    if not data_path.exists():
        raise FileNotFoundError(
            f"Data directory not found: {data_path}\n\n"
            "Please download the dataset from Kaggle:\n"
            "1. pip install kaggle\n"
            "2. Setup Kaggle API credentials\n"
            "3. kaggle datasets download -d patrickfleith/nasa-anomaly-detection-dataset-smap-msl\n"
            "4. unzip nasa-anomaly-detection-dataset-smap-msl.zip -d data/raw/telemanom\n\n"
            "Or use load_synthetic_dataset() for demo purposes."
        )
    
    # Load labeled anomalies
    labels_file = data_path / "labeled_anomalies.csv"
    if not labels_file.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_file}")
    
    labels_df = pd.read_csv(labels_file)
    
    # Load train and test data for each channel
    train_dir = data_path / "train"
    test_dir = data_path / "test"
    
    dfs = []
    for channel_id in labels_df['chan_id'].unique()[:10]:  # Load first 10 channels
        try:
            # Load train and test data
            train_data = np.load(train_dir / f"{channel_id}.npy")
            test_data = np.load(test_dir / f"{channel_id}.npy")
            
            # Combine
            all_data = np.concatenate([train_data, test_data])
            
            # Create DataFrame
            df = pd.DataFrame({
                'timestamp': pd.date_range(start='2024-01-01', periods=len(all_data), freq='1min'),
                'sensor_id': channel_id,
                'value': all_data.flatten() if all_data.ndim > 1 else all_data,
                'is_anomaly': 0
            })
            
            # Mark anomalies from labels
            channel_labels = labels_df[labels_df['chan_id'] == channel_id]
            for _, row in channel_labels.iterrows():
                anomaly_sequences = eval(row['anomaly_sequences'])  # Parse list
                for start, end in anomaly_sequences:
                    adjusted_start = start + len(train_data)
                    adjusted_end = end + len(train_data)
                    df.loc[adjusted_start:adjusted_end, 'is_anomaly'] = 1
            
            df['subsystem'] = _get_subsystem(channel_id)
            df['spacecraft'] = _get_spacecraft(channel_id)
            
            dfs.append(df)
            print(f"   ✓ Loaded {channel_id}")
            
        except Exception as e:
            print(f"   ✗ Failed to load {channel_id}: {e}")
    
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df = combined_df.sort_values(['timestamp', 'sensor_id']).reset_index(drop=True)
    
    print(f"\n✅ Real dataset loaded successfully!")
    print(f"   Total records: {len(combined_df):,}")
    print(f"   Total anomalies: {combined_df['is_anomaly'].sum():,}")
    
    return combined_df


def get_dataset_summary(df: pd.DataFrame) -> Dict:
    """
    Generate summary statistics for the loaded dataset.
    
    Args:
        df: Telemetry DataFrame
        
    Returns:
        Dictionary with summary statistics
    """
    summary = {
        'total_records': len(df),
        'total_anomalies': int(df['is_anomaly'].sum()),
        'anomaly_percentage': (df['is_anomaly'].sum() / len(df)) * 100,
        'num_channels': df['sensor_id'].nunique(),
        'channels': df['sensor_id'].unique().tolist(),
        'spacecraft': df['spacecraft'].unique().tolist(),
        'subsystems': df['subsystem'].unique().tolist(),
        'time_range': {
            'start': str(df['timestamp'].min()),
            'end': str(df['timestamp'].max())
        },
        'per_channel_stats': []
    }
    
    # Per-channel statistics
    for channel in df['sensor_id'].unique():
        channel_df = df[df['sensor_id'] == channel]
        summary['per_channel_stats'].append({
            'channel': channel,
            'records': len(channel_df),
            'anomalies': int(channel_df['is_anomaly'].sum()),
            'anomaly_pct': (channel_df['is_anomaly'].sum() / len(channel_df)) * 100,
            'spacecraft': channel_df['spacecraft'].iloc[0],
            'subsystem': channel_df['subsystem'].iloc[0]
        })
    
    return summary


if __name__ == "__main__":
    print("=" * 70)
    print("NASA SMAP/MSL Telemetry Dataset Loader")
    print("=" * 70)
    
    # Try to load real data, fall back to synthetic
    try:
        print("\n🔍 Checking for Kaggle dataset...")
        df = load_kaggle_dataset()
        data_source = "Kaggle (Real NASA Data)"
    except FileNotFoundError as e:
        print(f"\n⚠️  {e}")
        print("\n📊 Generating synthetic data for demo...")
        df = load_synthetic_dataset()
        data_source = "Synthetic (Demo Data)"
    
    # Display summary
    print("\n" + "=" * 70)
    print("DATASET SUMMARY")
    print("=" * 70)
    print(f"\nData Source: {data_source}")
    
    summary = get_dataset_summary(df)
    print(f"\nOverall Statistics:")
    print(f"  Total Records: {summary['total_records']:,}")
    print(f"  Total Anomalies: {summary['total_anomalies']:,} ({summary['anomaly_percentage']:.2f}%)")
    print(f"  Channels: {summary['num_channels']}")
    print(f"  Spacecraft: {', '.join(summary['spacecraft'])}")
    print(f"  Subsystems: {', '.join(summary['subsystems'])}")
    
    print(f"\nPer-Channel Statistics:")
    for stat in summary['per_channel_stats']:
        print(f"  {stat['channel']:6s} ({stat['spacecraft']:4s}/{stat['subsystem']:12s}): "
              f"{stat['records']:6,} points, {stat['anomalies']:4,} anomalies ({stat['anomaly_pct']:5.2f}%)")
    
    # Save to processed directory
    output_path = Path("data/processed/telemetry_dataset.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\n💾 Dataset saved to: {output_path}")
    
    # Save summary as JSON
    summary_path = Path("data/processed/dataset_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"💾 Summary saved to: {summary_path}")
    
    print("\n" + "=" * 70)
    print("USAGE INSTRUCTIONS")
    print("=" * 70)
    print("\nTo use this dataset in your code:")
    print("```python")
    print("from data.load_telemetry import load_synthetic_dataset")
    print("df = load_synthetic_dataset()")
    print("```")
    print("\nFor real NASA data, download from Kaggle first:")
    print("```bash")
    print("pip install kaggle")
    print("kaggle datasets download -d patrickfleith/nasa-anomaly-detection-dataset-smap-msl")
    print("unzip nasa-anomaly-detection-dataset-smap-msl.zip -d data/raw/telemanom")
    print("```")
    
    print("\n✅ Done!")