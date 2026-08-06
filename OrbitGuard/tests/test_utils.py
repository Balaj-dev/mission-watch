"""
Unit tests for utility modules.

Tests configuration loading, logging, and helper functions.
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config_loader import load_config, get_config_value
from src.utils.logger import setup_logger
from src.utils.helpers import format_timestamp, calculate_metrics


class TestConfigLoader(unittest.TestCase):
    """Tests for configuration loader."""
    
    def test_load_config(self):
        """Test loading configuration file."""
        config = load_config()
        self.assertIsInstance(config, dict)
        self.assertIn('signal_analyst', config)
        self.assertIn('advisor', config)
    
    def test_get_config_value(self):
        """Test getting configuration values."""
        value = get_config_value('signal_analyst.contamination', default=0.05)
        self.assertIsInstance(value, (int, float))


class TestLogger(unittest.TestCase):
    """Tests for logging utilities."""
    
    def test_setup_logger(self):
        """Test logger setup."""
        logger = setup_logger('test_logger')
        self.assertIsNotNone(logger)
        
        # Test logging
        logger.info("Test log message")
        logger.debug("Test debug message")


class TestHelpers(unittest.TestCase):
    """Tests for helper functions."""
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        timestamp = pd.Timestamp('2024-01-01 12:00:00')
        formatted = format_timestamp(timestamp)
        self.assertIsInstance(formatted, str)
    
    def test_calculate_metrics(self):
        """Test metrics calculation."""
        y_true = np.array([1, 0, 1, 1, 0])
        y_pred = np.array([1, 0, 1, 0, 0])
        
        metrics = calculate_metrics(y_true, y_pred)
        
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1_score', metrics)


if __name__ == '__main__':
    unittest.main()
