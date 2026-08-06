"""
Data validation module for telemetry datasets.

This module validates data quality, schema compliance, and generates quality reports.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import setup_logger
from src.utils.helpers import calculate_metrics

logger = setup_logger(__name__)


def validate_telemetry(
    df: pd.DataFrame,
    check_schema: bool = True,
    check_quality: bool = True,
    generate_report: bool = False
) -> Dict[str, Any]:
    """
    Main validation function for telemetry data.
    
    This is the primary entry point for validation that orchestrates
    schema validation, quality checks, and optional report generation.
    
    Args:
        df: DataFrame to validate
        check_schema: Whether to validate schema
        check_quality: Whether to check data quality
        generate_report: Whether to generate detailed report
        
    Returns:
        Dictionary containing validation results
    """
    logger.info(f"Validating telemetry data: {len(df):,} records")
    
    results = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Schema validation
    if check_schema:
        is_valid, errors = validate_schema(df)
        results['schema_valid'] = is_valid
        if not is_valid:
            results['is_valid'] = False
            results['errors'].extend(errors)
    
    # Quality checks
    if check_quality:
        quality_metrics = check_data_quality(df)
        results['quality_metrics'] = quality_metrics
        
        # Add quality issues as warnings
        if quality_metrics.get('issues'):
            results['warnings'].extend(quality_metrics['issues'])
        
        # Mark as invalid if quality is poor
        if quality_metrics.get('quality_score') == 'POOR':
            results['is_valid'] = False
            results['errors'].append("Data quality is POOR")
    
    # Generate report if requested
    if generate_report:
        report = generate_quality_report(df)
        results['report'] = report
    
    if results['is_valid']:
        logger.info("Telemetry validation passed")
    else:
        logger.warning(f"Telemetry validation failed: {len(results['errors'])} errors")
    
    return results


def validate_schema(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None,
    expected_types: Optional[Dict[str, str]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate DataFrame schema against expected structure.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        expected_types: Dictionary mapping column names to expected types
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Default required columns for telemetry data
    if required_columns is None:
        required_columns = ['timestamp', 'sensor_id', 'value']
    
    # Check required columns
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Check data types if specified
    if expected_types:
        for col, expected_type in expected_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                
                # Flexible type matching
                type_matches = False
                if expected_type == 'datetime' and 'datetime' in actual_type:
                    type_matches = True
                elif expected_type == 'numeric' and df[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
                    type_matches = True
                elif expected_type == 'string' and df[col].dtype == 'object':
                    type_matches = True
                elif expected_type in actual_type:
                    type_matches = True
                
                if not type_matches:
                    errors.append(f"Column '{col}' has type '{actual_type}', expected '{expected_type}'")
    
    is_valid = len(errors) == 0
    
    if is_valid:
        logger.info("Schema validation passed")
    else:
        logger.warning(f"Schema validation failed with {len(errors)} errors")
        for error in errors:
            logger.warning(f"  - {error}")
    
    return is_valid, errors


def check_data_quality(
    df: pd.DataFrame,
    value_col: str = 'value',
    timestamp_col: str = 'timestamp'
) -> Dict[str, Any]:
    """
    Check data quality metrics.
    
    Args:
        df: DataFrame to check
        value_col: Name of value column
        timestamp_col: Name of timestamp column
        
    Returns:
        Dictionary with quality metrics
    """
    logger.info("Checking data quality")
    
    quality_metrics = {
        'total_records': len(df),
        'columns': list(df.columns),
        'issues': []
    }
    
    # Check for missing values
    missing_counts = df.isnull().sum()
    if missing_counts.sum() > 0:
        quality_metrics['missing_values'] = missing_counts[missing_counts > 0].to_dict()
        quality_metrics['missing_percentage'] = (missing_counts.sum() / len(df)) * 100
        quality_metrics['issues'].append(f"Found {missing_counts.sum()} missing values")
    else:
        quality_metrics['missing_values'] = {}
        quality_metrics['missing_percentage'] = 0.0
    
    # Check for duplicates
    if timestamp_col in df.columns and 'sensor_id' in df.columns:
        duplicate_count = df.duplicated(subset=[timestamp_col, 'sensor_id']).sum()
        quality_metrics['duplicate_records'] = int(duplicate_count)
        if duplicate_count > 0:
            quality_metrics['issues'].append(f"Found {duplicate_count} duplicate records")
    
    # Check value column statistics
    if value_col in df.columns:
        values = df[value_col].dropna()
        
        quality_metrics['value_stats'] = {
            'count': int(len(values)),
            'mean': float(values.mean()),
            'std': float(values.std()),
            'min': float(values.min()),
            'max': float(values.max()),
            'median': float(values.median()),
            'q25': float(values.quantile(0.25)),
            'q75': float(values.quantile(0.75))
        }
        
        # Check for infinite values
        inf_count = np.isinf(values).sum()
        if inf_count > 0:
            quality_metrics['infinite_values'] = int(inf_count)
            quality_metrics['issues'].append(f"Found {inf_count} infinite values")
        
        # Check for constant values (no variation)
        if values.std() == 0:
            quality_metrics['issues'].append("Value column has no variation (constant)")
    
    # Check timestamp continuity
    if timestamp_col in df.columns:
        df_sorted = df.sort_values(timestamp_col)
        timestamps = pd.to_datetime(df_sorted[timestamp_col])
        
        # Calculate time gaps
        time_diffs = timestamps.diff()
        
        quality_metrics['timestamp_stats'] = {
            'start': str(timestamps.min()),
            'end': str(timestamps.max()),
            'duration': str(timestamps.max() - timestamps.min()),
            'median_gap': str(time_diffs.median()),
            'max_gap': str(time_diffs.max())
        }
        
        # Check for large gaps (more than 10x median)
        median_gap = time_diffs.median()
        large_gaps = time_diffs > (median_gap * 10)
        if large_gaps.sum() > 0:
            quality_metrics['large_time_gaps'] = int(large_gaps.sum())
            quality_metrics['issues'].append(f"Found {large_gaps.sum()} large time gaps")
    
    # Check sensor distribution
    if 'sensor_id' in df.columns:
        sensor_counts = df['sensor_id'].value_counts()
        quality_metrics['sensor_stats'] = {
            'num_sensors': len(sensor_counts),
            'records_per_sensor': sensor_counts.to_dict(),
            'min_records': int(sensor_counts.min()),
            'max_records': int(sensor_counts.max()),
            'mean_records': float(sensor_counts.mean())
        }
        
        # Check for imbalanced sensors
        if sensor_counts.max() > sensor_counts.min() * 10:
            quality_metrics['issues'].append("Highly imbalanced sensor distribution")
    
    # Check anomaly labels if present
    if 'is_anomaly' in df.columns:
        anomaly_count = df['is_anomaly'].sum()
        anomaly_pct = (anomaly_count / len(df)) * 100
        
        quality_metrics['anomaly_stats'] = {
            'total_anomalies': int(anomaly_count),
            'anomaly_percentage': float(anomaly_pct),
            'normal_records': int(len(df) - anomaly_count)
        }
        
        # Check for class imbalance
        if anomaly_pct < 1.0:
            quality_metrics['issues'].append(f"Low anomaly rate: {anomaly_pct:.2f}%")
        elif anomaly_pct > 50.0:
            quality_metrics['issues'].append(f"High anomaly rate: {anomaly_pct:.2f}%")
    
    # Overall quality score
    num_issues = len(quality_metrics['issues'])
    if num_issues == 0:
        quality_metrics['quality_score'] = 'EXCELLENT'
    elif num_issues <= 2:
        quality_metrics['quality_score'] = 'GOOD'
    elif num_issues <= 4:
        quality_metrics['quality_score'] = 'FAIR'
    else:
        quality_metrics['quality_score'] = 'POOR'
    
    logger.info(f"Data quality check complete: {quality_metrics['quality_score']} ({num_issues} issues)")
    
    return quality_metrics


def generate_quality_report(
    df: pd.DataFrame,
    output_path: Optional[str] = None
) -> str:
    """
    Generate comprehensive data quality report.
    
    Args:
        df: DataFrame to analyze
        output_path: Optional path to save report (as text file)
        
    Returns:
        Report as formatted string
    """
    logger.info("Generating data quality report")
    
    # Validate schema
    is_valid, schema_errors = validate_schema(df)
    
    # Check quality
    quality_metrics = check_data_quality(df)
    
    # Build report
    report_lines = [
        "=" * 80,
        "DATA QUALITY REPORT",
        "=" * 80,
        "",
        f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Dataset: {len(df):,} records, {len(df.columns)} columns",
        "",
        "=" * 80,
        "SCHEMA VALIDATION",
        "=" * 80,
        "",
        f"Status: {'✓ PASSED' if is_valid else '✗ FAILED'}",
        ""
    ]
    
    if schema_errors:
        report_lines.append("Errors:")
        for error in schema_errors:
            report_lines.append(f"  - {error}")
        report_lines.append("")
    
    report_lines.extend([
        "Columns:",
        f"  {', '.join(df.columns)}",
        "",
        "=" * 80,
        "DATA QUALITY METRICS",
        "=" * 80,
        "",
        f"Overall Quality Score: {quality_metrics['quality_score']}",
        f"Total Records: {quality_metrics['total_records']:,}",
        ""
    ])
    
    # Missing values
    if quality_metrics['missing_values']:
        report_lines.append("Missing Values:")
        for col, count in quality_metrics['missing_values'].items():
            pct = (count / quality_metrics['total_records']) * 100
            report_lines.append(f"  - {col}: {count:,} ({pct:.2f}%)")
        report_lines.append("")
    else:
        report_lines.append("Missing Values: None ✓")
        report_lines.append("")
    
    # Duplicates
    if 'duplicate_records' in quality_metrics:
        dup_count = quality_metrics['duplicate_records']
        if dup_count > 0:
            report_lines.append(f"Duplicate Records: {dup_count:,}")
        else:
            report_lines.append("Duplicate Records: None ✓")
        report_lines.append("")
    
    # Value statistics
    if 'value_stats' in quality_metrics:
        report_lines.append("Value Statistics:")
        stats = quality_metrics['value_stats']
        report_lines.append(f"  Count: {stats['count']:,}")
        report_lines.append(f"  Mean: {stats['mean']:.4f}")
        report_lines.append(f"  Std Dev: {stats['std']:.4f}")
        report_lines.append(f"  Min: {stats['min']:.4f}")
        report_lines.append(f"  Q25: {stats['q25']:.4f}")
        report_lines.append(f"  Median: {stats['median']:.4f}")
        report_lines.append(f"  Q75: {stats['q75']:.4f}")
        report_lines.append(f"  Max: {stats['max']:.4f}")
        report_lines.append("")
    
    # Timestamp statistics
    if 'timestamp_stats' in quality_metrics:
        report_lines.append("Timestamp Statistics:")
        stats = quality_metrics['timestamp_stats']
        report_lines.append(f"  Start: {stats['start']}")
        report_lines.append(f"  End: {stats['end']}")
        report_lines.append(f"  Duration: {stats['duration']}")
        report_lines.append(f"  Median Gap: {stats['median_gap']}")
        report_lines.append(f"  Max Gap: {stats['max_gap']}")
        report_lines.append("")
    
    # Sensor statistics
    if 'sensor_stats' in quality_metrics:
        report_lines.append("Sensor Statistics:")
        stats = quality_metrics['sensor_stats']
        report_lines.append(f"  Number of Sensors: {stats['num_sensors']}")
        report_lines.append(f"  Records per Sensor (min/mean/max): {stats['min_records']}/{stats['mean_records']:.0f}/{stats['max_records']}")
        report_lines.append("")
    
    # Anomaly statistics
    if 'anomaly_stats' in quality_metrics:
        report_lines.append("Anomaly Statistics:")
        stats = quality_metrics['anomaly_stats']
        report_lines.append(f"  Total Anomalies: {stats['total_anomalies']:,} ({stats['anomaly_percentage']:.2f}%)")
        report_lines.append(f"  Normal Records: {stats['normal_records']:,}")
        report_lines.append("")
    
    # Issues
    if quality_metrics['issues']:
        report_lines.append("=" * 80)
        report_lines.append("ISSUES DETECTED")
        report_lines.append("=" * 80)
        report_lines.append("")
        for i, issue in enumerate(quality_metrics['issues'], 1):
            report_lines.append(f"{i}. {issue}")
        report_lines.append("")
    
    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)
    
    report = "\n".join(report_lines)
    
    # Save to file if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Quality report saved to {output_path}")
    
    return report


def validate_for_training(
    df: pd.DataFrame,
    min_records: int = 1000,
    min_anomaly_rate: float = 0.01,
    max_missing_rate: float = 0.1
) -> Tuple[bool, List[str]]:
    """
    Validate that dataset is suitable for model training.
    
    Args:
        df: DataFrame to validate
        min_records: Minimum number of records required
        min_anomaly_rate: Minimum anomaly rate (as fraction)
        max_missing_rate: Maximum allowed missing value rate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    logger.info("Validating dataset for training")
    
    errors = []
    
    # Check minimum records
    if len(df) < min_records:
        errors.append(f"Insufficient records: {len(df)} < {min_records}")
    
    # Check for required columns
    required_cols = ['value', 'sensor_id']
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
    
    # Check missing value rate
    missing_rate = df.isnull().sum().sum() / (len(df) * len(df.columns))
    if missing_rate > max_missing_rate:
        errors.append(f"Too many missing values: {missing_rate:.2%} > {max_missing_rate:.2%}")
    
    # Check anomaly labels if present
    if 'is_anomaly' in df.columns:
        anomaly_rate = df['is_anomaly'].sum() / len(df)
        if anomaly_rate < min_anomaly_rate:
            errors.append(f"Anomaly rate too low: {anomaly_rate:.2%} < {min_anomaly_rate:.2%}")
    else:
        errors.append("Missing 'is_anomaly' column for supervised training")
    
    is_valid = len(errors) == 0
    
    if is_valid:
        logger.info("Dataset validation passed - ready for training")
    else:
        logger.warning(f"Dataset validation failed with {len(errors)} errors")
        for error in errors:
            logger.warning(f"  - {error}")
    
    return is_valid, errors