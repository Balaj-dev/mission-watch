"""
Anomaly detection orchestration module.

This module coordinates the anomaly detection pipeline by integrating
data loading, preprocessing, model training/prediction, and scoring.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logger import setup_logger
from src.utils.config_loader import load_config, get_config_value
from src.data.preprocessor import preprocess_telemetry
from src.data.validator import validate_telemetry
from src.agents.signal_analyst.models import train_model, predict_anomalies
from src.agents.signal_analyst.scorer import calculate_anomaly_scores, rank_anomalies, filter_by_threshold

logger = setup_logger(__name__)


def detect_anomalies(
    telemetry_data: pd.DataFrame,
    model_type: str = "isolation_forest",
    train_model_flag: bool = True,
    model_path: Optional[str] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Main anomaly detection workflow.
    
    This function orchestrates the complete anomaly detection process:
    1. Validates input data
    2. Trains or loads a model
    3. Predicts anomalies
    4. Calculates and ranks anomaly scores
    5. Filters results by threshold
    
    Args:
        telemetry_data: Preprocessed telemetry DataFrame
        model_type: Type of model to use ('isolation_forest', 'zscore', 'iqr', 'ensemble')
        train_model_flag: Whether to train a new model (True) or load existing (False)
        model_path: Path to saved model (required if train_model_flag=False)
        **kwargs: Additional parameters for model training/prediction
        
    Returns:
        DataFrame containing detected anomalies with scores and rankings
    """
    logger.info(f"Starting anomaly detection with model_type={model_type}")
    logger.info(f"Input data shape: {telemetry_data.shape}")
    
    # Validate input data
    validation_result = validate_telemetry(telemetry_data)
    if not validation_result['is_valid']:
        logger.error(f"Data validation failed: {validation_result['errors']}")
        raise ValueError(f"Invalid telemetry data: {validation_result['errors']}")
    
    logger.info("Data validation passed")
    
    # Train or load model
    if train_model_flag:
        logger.info("Training new model")
        model = train_model(
            telemetry_data,
            model_type=model_type,
            **kwargs
        )
        
        # Save model if path provided
        if model_path and hasattr(model, 'save'):
            model.save(model_path)
            logger.info(f"Model saved to {model_path}")
    else:
        if not model_path:
            raise ValueError("model_path required when train_model_flag=False")
        
        logger.info(f"Loading model from {model_path}")
        
        # Create model instance and load
        if model_type == "isolation_forest":
            from src.agents.signal_analyst.models import IsolationForestDetector
            model = IsolationForestDetector()
            model.load(model_path)
        else:
            raise ValueError(f"Model loading not supported for {model_type}")
    
    # Predict anomalies
    logger.info("Predicting anomalies")
    predictions_df = predict_anomalies(model, telemetry_data, return_scores=True)
    
    # Calculate anomaly scores (always, to get final_anomaly_score)
    logger.info("Calculating anomaly scores")
    predictions_df = calculate_anomaly_scores(predictions_df)
    
    # Rank anomalies
    logger.info("Ranking anomalies")
    ranked_df = rank_anomalies(predictions_df)
    
    # Filter by threshold
    threshold = kwargs.get('threshold', get_config_value('signal_analyst.anomaly_threshold', 0.7))
    logger.info(f"Filtering anomalies with threshold={threshold}")
    filtered_df = filter_by_threshold(ranked_df, threshold=threshold)
    
    num_anomalies = filtered_df['predicted_anomaly'].sum()
    logger.info(f"Detection complete: {num_anomalies:,} anomalies detected")
    
    return filtered_df


def run_detection_pipeline(
    data_source: str,
    output_dir: Optional[str] = None,
    model_type: str = "isolation_forest",
    save_results: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute end-to-end anomaly detection pipeline.
    
    This function runs the complete pipeline from data loading to result persistence:
    1. Loads telemetry data from source
    2. Preprocesses the data
    3. Detects anomalies
    4. Saves results (if requested)
    5. Returns summary statistics
    
    Args:
        data_source: Path to data source file or directory
        output_dir: Directory to save results (uses config default if None)
        model_type: Type of model to use
        save_results: Whether to save detection results to disk
        **kwargs: Additional parameters for detection
        
    Returns:
        Dictionary containing:
            - anomalies: DataFrame of detected anomalies
            - summary: Summary statistics
            - metadata: Pipeline execution metadata
    """
    logger.info("="*60)
    logger.info("Starting anomaly detection pipeline")
    logger.info(f"Data source: {data_source}")
    logger.info(f"Model type: {model_type}")
    logger.info("="*60)
    
    pipeline_start = pd.Timestamp.now()
    
    try:
        # Step 1: Load data
        logger.info("Step 1/4: Loading telemetry data")
        from src.data.loader import load_telemetry_data
        telemetry_data, metadata = load_telemetry_data(data_source)
        logger.info(f"Loaded {len(telemetry_data):,} records")
        
        # Step 2: Preprocess data
        logger.info("Step 2/4: Preprocessing telemetry data")
        processed_data = preprocess_telemetry(telemetry_data)
        logger.info(f"Preprocessed data shape: {processed_data.shape}")
        
        # Step 3: Detect anomalies
        logger.info("Step 3/4: Detecting anomalies")
        anomalies_df = detect_anomalies(
            processed_data,
            model_type=model_type,
            **kwargs
        )
        
        # Extract only anomalies for output
        detected_anomalies = anomalies_df[anomalies_df['predicted_anomaly'] == 1].copy()
        
        # Step 4: Save results
        if save_results:
            logger.info("Step 4/4: Saving results")
            
            if output_dir is None:
                output_dir = get_config_value('paths.anomalies_dir', 'data/anomalies')
            
            output_path = Path(output_dir) / f"anomalies_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
            save_anomalies(detected_anomalies, str(output_path))
        else:
            logger.info("Step 4/4: Skipping result persistence")
        
        # Calculate summary statistics
        pipeline_end = pd.Timestamp.now()
        execution_time = (pipeline_end - pipeline_start).total_seconds()
        
        summary = {
            'total_records': len(telemetry_data),
            'processed_records': len(processed_data),
            'anomalies_detected': len(detected_anomalies),
            'anomaly_rate': len(detected_anomalies) / len(processed_data) * 100,
            'execution_time_seconds': execution_time,
            'model_type': model_type
        }
        
        # Add score statistics if available
        if 'anomaly_score' in detected_anomalies.columns:
            summary['avg_anomaly_score'] = detected_anomalies['anomaly_score'].mean()
            summary['max_anomaly_score'] = detected_anomalies['anomaly_score'].max()
            summary['min_anomaly_score'] = detected_anomalies['anomaly_score'].min()
        
        logger.info("="*60)
        logger.info("Pipeline execution complete")
        logger.info(f"Total records: {summary['total_records']:,}")
        logger.info(f"Anomalies detected: {summary['anomalies_detected']:,} ({summary['anomaly_rate']:.2f}%)")
        logger.info(f"Execution time: {execution_time:.2f}s")
        logger.info("="*60)
        
        return {
            'anomalies': detected_anomalies,
            'all_predictions': anomalies_df,
            'summary': summary,
            'metadata': {
                'pipeline_start': pipeline_start.isoformat(),
                'pipeline_end': pipeline_end.isoformat(),
                'data_source': data_source,
                'output_path': str(output_path) if save_results else None,
                **metadata
            }
        }
    
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        raise


def save_anomalies(
    anomalies: pd.DataFrame,
    output_path: str,
    format: str = 'csv',
    include_metadata: bool = True
) -> None:
    """
    Persist detected anomalies to disk.
    
    Args:
        anomalies: DataFrame containing detected anomalies
        output_path: Path to save anomalies
        format: Output format ('csv', 'json', 'parquet')
        include_metadata: Whether to include metadata in output
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving {len(anomalies):,} anomalies to {output_path}")
    
    # Prepare data for saving
    save_df = anomalies.copy()
    
    # Add metadata if requested
    if include_metadata:
        save_df['detection_timestamp'] = pd.Timestamp.now().isoformat()
    
    # Save in requested format
    if format == 'csv':
        save_df.to_csv(output_path, index=False)
    elif format == 'json':
        save_df.to_json(output_path, orient='records', indent=2)
    elif format == 'parquet':
        save_df.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    logger.info(f"Anomalies saved successfully to {output_path}")
    
    # Log summary statistics
    if 'anomaly_score' in save_df.columns:
        logger.info(f"Score statistics - Mean: {save_df['anomaly_score'].mean():.4f}, "
                   f"Max: {save_df['anomaly_score'].max():.4f}, "
                   f"Min: {save_df['anomaly_score'].min():.4f}")


def load_anomalies(filepath: str) -> pd.DataFrame:
    """
    Load previously saved anomalies from disk.
    
    Args:
        filepath: Path to anomalies file
        
    Returns:
        DataFrame containing anomalies
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Anomalies file not found: {filepath}")
    
    logger.info(f"Loading anomalies from {filepath}")
    
    # Detect format from extension
    if filepath.suffix == '.csv':
        df = pd.read_csv(filepath)
    elif filepath.suffix == '.json':
        df = pd.read_json(filepath)
    elif filepath.suffix == '.parquet':
        df = pd.read_parquet(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")
    
    logger.info(f"Loaded {len(df):,} anomalies")
    
    return df


def batch_detect_anomalies(
    data_sources: List[str],
    output_dir: str,
    model_type: str = "isolation_forest",
    parallel: bool = False,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Run anomaly detection on multiple data sources.
    
    Args:
        data_sources: List of paths to data sources
        output_dir: Directory to save all results
        model_type: Type of model to use
        parallel: Whether to process sources in parallel (future enhancement)
        **kwargs: Additional parameters for detection
        
    Returns:
        List of result dictionaries, one per data source
    """
    logger.info(f"Starting batch detection on {len(data_sources)} data sources")
    
    results = []
    
    for i, source in enumerate(data_sources, 1):
        logger.info(f"Processing source {i}/{len(data_sources)}: {source}")
        
        try:
            result = run_detection_pipeline(
                data_source=source,
                output_dir=output_dir,
                model_type=model_type,
                **kwargs
            )
            results.append(result)
            logger.info(f"Source {i} completed successfully")
        
        except Exception as e:
            logger.error(f"Source {i} failed: {str(e)}")
            results.append({
                'error': str(e),
                'data_source': source
            })
    
    # Summary
    successful = sum(1 for r in results if 'error' not in r)
    failed = len(results) - successful
    
    logger.info("="*60)
    logger.info("Batch detection complete")
    logger.info(f"Successful: {successful}/{len(data_sources)}")
    logger.info(f"Failed: {failed}/{len(data_sources)}")
    logger.info("="*60)
    
    return results