"""
Configuration management module.

This module handles loading and validating configuration from config.yaml.
"""

import yaml
from pathlib import Path
from typing import Any, Optional, Dict
import os


# Global config cache
_config_cache: Optional[Dict[str, Any]] = None


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    global _config_cache
    
    # Return cached config if available
    if _config_cache is not None:
        return _config_cache
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate config
        validate_config(config)
        
        # Cache for future use
        _config_cache = config
        
        return config
    
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e}")


def get_config_value(key: str, default: Any = None, config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Safely retrieve configuration value with fallback.
    
    Supports dot notation for nested keys (e.g., 'data.raw_dir').
    
    Args:
        key: Configuration key (supports dot notation)
        default: Default value if key not found
        config: Optional config dict (loads from file if not provided)
        
    Returns:
        Configuration value or default
        
    Example:
        >>> get_config_value('signal_analyst.model_type')
        'isolation_forest'
        >>> get_config_value('nonexistent.key', 'default_value')
        'default_value'
    """
    if config is None:
        try:
            config = load_config()
        except Exception:
            return default
    
    # Handle dot notation
    keys = key.split('.')
    value = config
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration has all required fields.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    required_sections = ['data', 'signal_analyst', 'advisor', 'dashboard', 'logging']
    
    # Check required top-level sections
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: {section}")
    
    # Validate data section
    data_required = ['raw_dir', 'processed_dir', 'anomalies_dir']
    for field in data_required:
        if field not in config['data']:
            raise ValueError(f"Missing required field in data section: {field}")
    
    # Validate signal_analyst section
    analyst_required = ['model_type', 'contamination', 'anomaly_threshold']
    for field in analyst_required:
        if field not in config['signal_analyst']:
            raise ValueError(f"Missing required field in signal_analyst section: {field}")
    
    # Validate advisor section
    advisor_required = ['model_name', 'api_endpoint']
    for field in advisor_required:
        if field not in config['advisor']:
            raise ValueError(f"Missing required field in advisor section: {field}")
    
    # Validate dashboard section
    dashboard_required = ['title']
    for field in dashboard_required:
        if field not in config['dashboard']:
            raise ValueError(f"Missing required field in dashboard section: {field}")
    
    # Validate logging section
    logging_required = ['level', 'log_file']
    for field in logging_required:
        if field not in config['logging']:
            raise ValueError(f"Missing required field in logging section: {field}")
    
    # Validate value ranges
    contamination = config['signal_analyst']['contamination']
    if not (0.0 <= contamination <= 0.5):
        raise ValueError(f"contamination must be between 0.0 and 0.5, got {contamination}")
    
    threshold = config['signal_analyst']['anomaly_threshold']
    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"anomaly_threshold must be between 0.0 and 1.0, got {threshold}")
    
    return True


def reload_config() -> Dict[str, Any]:
    """
    Force reload configuration from file (clears cache).
    
    Returns:
        Reloaded configuration dictionary
    """
    global _config_cache
    _config_cache = None
    return load_config()


def get_env_or_config(env_var: str, config_key: str, default: Any = None) -> Any:
    """
    Get value from environment variable first, then config, then default.
    
    Useful for sensitive values like API keys.
    
    Args:
        env_var: Environment variable name
        config_key: Configuration key (dot notation supported)
        default: Default value if neither found
        
    Returns:
        Value from env var, config, or default
        
    Example:
        >>> get_env_or_config('IBM_CLOUD_API_KEY', 'advisor.api_key', '')
    """
    # Try environment variable first
    env_value = os.getenv(env_var)
    if env_value is not None:
        return env_value
    
    # Try config
    config_value = get_config_value(config_key)
    if config_value is not None:
        return config_value
    
    # Return default
    return default