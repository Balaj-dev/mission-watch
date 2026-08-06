"""
Integration tests for Mission Watch.

Tests the complete pipeline from data loading to brief generation.
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.data.loader import load_telemetry_data
from src.data.preprocessor import preprocess_telemetry
from src.agents.signal_analyst.detector import detect_anomalies
from src.agents.advisor.advisor import generate_ops_brief
from src.evaluation.evaluator import evaluate_predictions


class TestIntegration(unittest.TestCase):
    """Integration tests for end-to-end pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Create synthetic test data
        np.random.seed(42)
        n_samples = 1000
        
        cls.test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=n_samples, freq='1min'),
            'sensor_id': np.random.choice(['sensor_1', 'sensor_2'], n_samples),
            'value': np.random.randn(n_samples),
            'is_anomaly': np.random.choice([0, 1], n_samples, p=[0.95, 0.05])
        })
    
    def test_data_loading_and_preprocessing(self):
        """Test data loading and preprocessing pipeline."""
        # This would normally load from file, but we'll use our test data
        processed = preprocess_telemetry(self.test_data)
        
        self.assertIsInstance(processed, pd.DataFrame)
        self.assertGreater(len(processed), 0)
        self.assertIn('timestamp', processed.columns)
    
    def test_anomaly_detection_pipeline(self):
        """Test anomaly detection pipeline."""
        processed = preprocess_telemetry(self.test_data)
        
        results = detect_anomalies(
            processed,
            model_type='isolation_forest',
            train_model_flag=True,
            contamination=0.05
        )
        
        self.assertIsInstance(results, pd.DataFrame)
        self.assertIn('predicted_anomaly', results.columns)
        self.assertIn('anomaly_score', results.columns)
    
    def test_evaluation_pipeline(self):
        """Test evaluation with ground truth."""
        processed = preprocess_telemetry(self.test_data)
        
        results = detect_anomalies(
            processed,
            model_type='isolation_forest',
            train_model_flag=True
        )
        
        if 'is_anomaly' in results.columns:
            eval_results = evaluate_predictions(
                results,
                ground_truth_col='is_anomaly',
                prediction_col='predicted_anomaly'
            )
            
            self.assertIn('overall_metrics', eval_results)
            self.assertIn('f1_score', eval_results['overall_metrics'])
    
    def test_end_to_end_pipeline(self):
        """Test complete end-to-end pipeline."""
        # 1. Preprocess
        processed = preprocess_telemetry(self.test_data)
        
        # 2. Detect anomalies
        results = detect_anomalies(
            processed,
            model_type='isolation_forest',
            train_model_flag=True
        )
        
        # 3. Generate brief for first anomaly
        anomalies = results[results['predicted_anomaly'] == 1]
        
        if not anomalies.empty:
            first_anomaly = anomalies.iloc[0].to_dict()
            brief = generate_ops_brief(first_anomaly)
            
            self.assertIsInstance(brief, str)
            self.assertGreater(len(brief), 0)


if __name__ == '__main__':
    unittest.main()
