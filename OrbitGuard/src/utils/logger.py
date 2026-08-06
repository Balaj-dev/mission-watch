"""
Centralized logging setup module.

This module configures logging for the Mission Watch application.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import sys


# Global logger cache
_loggers = {}


def setup_logger(name: str, level: str = "INFO", log_to_file: bool = True) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        log_to_file: Whether to log to file in addition to console
        
    Returns:
        Configured logger instance
    """
    # Return cached logger if exists
    if name in _loggers:
        return _loggers[name]
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        try:
            # Create logs directory if it doesn't exist
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Create log file with timestamp
            log_file = log_dir / f"mission_watch_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler: {e}")
    
    # Cache logger
    _loggers[name] = logger
    
    return logger


def log_anomaly_detection(
    anomalies: list,
    logger: Optional[logging.Logger] = None,
    channel: Optional[str] = None
) -> None:
    """
    Log anomaly detection events with metadata.
    
    Args:
        anomalies: List of detected anomalies (can be DataFrame rows or dicts)
        logger: Optional logger instance (creates default if not provided)
        channel: Optional channel identifier for context
    """
    if logger is None:
        logger = setup_logger("anomaly_detection")
    
    try:
        # Handle different input types
        if hasattr(anomalies, '__len__'):
            num_anomalies = len(anomalies)
        else:
            num_anomalies = 1
            anomalies = [anomalies]
        
        # Log summary
        if channel:
            logger.info(f"Detected {num_anomalies} anomalies in channel {channel}")
        else:
            logger.info(f"Detected {num_anomalies} anomalies")
        
        # Log details for each anomaly (limit to first 10 for brevity)
        for i, anomaly in enumerate(anomalies[:10]):
            if hasattr(anomaly, 'to_dict'):
                # DataFrame row
                anomaly_dict = anomaly.to_dict()
            elif isinstance(anomaly, dict):
                anomaly_dict = anomaly
            else:
                logger.debug(f"Anomaly {i+1}: {anomaly}")
                continue
            
            # Extract key fields
            timestamp = anomaly_dict.get('timestamp', 'N/A')
            sensor_id = anomaly_dict.get('sensor_id', 'N/A')
            value = anomaly_dict.get('value', 'N/A')
            score = anomaly_dict.get('anomaly_score', 'N/A')
            
            logger.debug(
                f"Anomaly {i+1}: timestamp={timestamp}, sensor={sensor_id}, "
                f"value={value}, score={score}"
            )
        
        if num_anomalies > 10:
            logger.debug(f"... and {num_anomalies - 10} more anomalies")
    
    except Exception as e:
        logger.error(f"Error logging anomaly detection: {e}", exc_info=True)


def log_advisor_call(
    prompt: str,
    response: str,
    logger: Optional[logging.Logger] = None,
    model: Optional[str] = None,
    duration: Optional[float] = None
) -> None:
    """
    Log LLM interactions for debugging and audit.
    
    Args:
        prompt: Input prompt sent to LLM
        response: Response received from LLM
        logger: Optional logger instance (creates default if not provided)
        model: Optional model name/identifier
        duration: Optional duration of API call in seconds
    """
    if logger is None:
        logger = setup_logger("advisor")
    
    try:
        # Log call metadata
        log_msg = "LLM API call"
        if model:
            log_msg += f" (model: {model})"
        if duration:
            log_msg += f" (duration: {duration:.2f}s)"
        
        logger.info(log_msg)
        
        # Log prompt (truncated if too long)
        max_prompt_len = 500
        if len(prompt) > max_prompt_len:
            prompt_preview = prompt[:max_prompt_len] + "..."
        else:
            prompt_preview = prompt
        
        logger.debug(f"Prompt: {prompt_preview}")
        
        # Log response (truncated if too long)
        max_response_len = 1000
        if len(response) > max_response_len:
            response_preview = response[:max_response_len] + "..."
        else:
            response_preview = response
        
        logger.debug(f"Response: {response_preview}")
        
        # Log full interaction to separate file for audit
        try:
            audit_dir = Path("logs/llm_audit")
            audit_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            audit_file = audit_dir / f"llm_call_{timestamp}.txt"
            
            with open(audit_file, 'w') as f:
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                if model:
                    f.write(f"Model: {model}\n")
                if duration:
                    f.write(f"Duration: {duration:.2f}s\n")
                f.write("\n=== PROMPT ===\n")
                f.write(prompt)
                f.write("\n\n=== RESPONSE ===\n")
                f.write(response)
        
        except Exception as e:
            logger.warning(f"Could not write LLM audit log: {e}")
    
    except Exception as e:
        logger.error(f"Error logging advisor call: {e}", exc_info=True)


def log_performance_metrics(
    metrics: dict,
    logger: Optional[logging.Logger] = None,
    context: Optional[str] = None
) -> None:
    """
    Log performance metrics (precision, recall, F1, etc.).
    
    Args:
        metrics: Dictionary of metric names and values
        logger: Optional logger instance
        context: Optional context description
    """
    if logger is None:
        logger = setup_logger("metrics")
    
    try:
        if context:
            logger.info(f"Performance metrics - {context}:")
        else:
            logger.info("Performance metrics:")
        
        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, float):
                logger.info(f"  {metric_name}: {metric_value:.4f}")
            else:
                logger.info(f"  {metric_name}: {metric_value}")
    
    except Exception as e:
        logger.error(f"Error logging performance metrics: {e}", exc_info=True)


def log_pipeline_stage(
    stage: str,
    status: str,
    logger: Optional[logging.Logger] = None,
    details: Optional[dict] = None
) -> None:
    """
    Log pipeline stage execution.
    
    Args:
        stage: Stage name (e.g., "data_loading", "preprocessing", "detection")
        status: Status ("started", "completed", "failed")
        logger: Optional logger instance
        details: Optional dictionary with additional details
    """
    if logger is None:
        logger = setup_logger("pipeline")
    
    try:
        log_level = logging.INFO if status != "failed" else logging.ERROR
        
        msg = f"Pipeline stage '{stage}' {status}"
        
        if details:
            detail_str = ", ".join([f"{k}={v}" for k, v in details.items()])
            msg += f" ({detail_str})"
        
        logger.log(log_level, msg)
    
    except Exception as e:
        logger.error(f"Error logging pipeline stage: {e}", exc_info=True)


# Convenience function to get logger with config
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with configuration from config file.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    try:
        from .config_loader import get_config_value
        
        level = get_config_value('logging.level', 'INFO')
        log_to_console = get_config_value('logging.log_to_console', True)
        
        return setup_logger(name, level, log_to_file=True)
    
    except Exception:
        # Fallback to default if config not available
        return setup_logger(name)