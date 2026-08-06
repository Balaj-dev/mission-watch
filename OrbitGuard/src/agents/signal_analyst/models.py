"""
Machine learning models for anomaly detection.

This module implements various anomaly detection algorithms including
Isolation Forest, statistical methods, and ensemble approaches.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Any, Optional, Dict, Tuple
from pathlib import Path
import pickle
import sys

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logger import setup_logger
from src.utils.config_loader import get_config_value

logger = setup_logger(__name__)


class IsolationForestDetector:
    """Isolation Forest-based anomaly detector."""
    
    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 100,
        max_samples: str = 'auto',
        random_state: int = 42
    ):
        """
        Initialize Isolation Forest detector.
        
        Args:
            contamination: Expected proportion of anomalies in the dataset
            n_estimators: Number of trees in the forest
            max_samples: Number of samples to draw for each tree
            random_state: Random seed for reproducibility
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.random_state = random_state
        
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            max_samples=max_samples,
            random_state=random_state,
            n_jobs=-1  # Use all CPU cores
        )
        
        self.scaler = StandardScaler()
        self.is_trained = False
        
        logger.info(f"Initialized IsolationForest with contamination={contamination}, n_estimators={n_estimators}")
    
    def train(self, data: pd.DataFrame, feature_cols: Optional[list] = None) -> None:
        """
        Train the model on telemetry data.
        
        Args:
            data: Training data DataFrame
            feature_cols: List of feature columns to use (auto-detects if None)
        """
        logger.info(f"Training IsolationForest on {len(data):,} samples")
        
        # Auto-detect feature columns if not provided
        if feature_cols is None:
            # Use numeric columns, exclude labels and identifiers
            feature_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            exclude_cols = ['is_anomaly', 'anomaly_score', 'sensor_id']
            feature_cols = [col for col in feature_cols if col not in exclude_cols]
        
        self.feature_cols = feature_cols
        logger.info(f"Using {len(feature_cols)} features: {feature_cols}")
        
        # Extract features
        X = data[feature_cols].values
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled)
        self.is_trained = True
        
        logger.info("IsolationForest training complete")
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """
        Predict anomalies in new data.
        
        Args:
            data: Data to predict on
            
        Returns:
            Array of predictions (1 = anomaly, 0 = normal)
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")
        
        # Extract features
        X = data[self.feature_cols].values
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Normalize features
        X_scaled = self.scaler.transform(X)
        
        # Predict (-1 = anomaly, 1 = normal)
        predictions = self.model.predict(X_scaled)
        
        # Convert to binary (1 = anomaly, 0 = normal)
        binary_predictions = (predictions == -1).astype(int)
        
        logger.info(f"Predicted {binary_predictions.sum():,} anomalies out of {len(data):,} samples")
        
        return binary_predictions
    
    def score(self, data: pd.DataFrame) -> np.ndarray:
        """
        Get anomaly scores for data.
        
        Args:
            data: Data to score
            
        Returns:
            Array of anomaly scores (lower = more anomalous)
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before scoring")
        
        # Extract features
        X = data[self.feature_cols].values
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Normalize features
        X_scaled = self.scaler.transform(X)
        
        # Get anomaly scores (lower = more anomalous)
        scores = self.model.score_samples(X_scaled)
        
        # Normalize scores to [0, 1] range (higher = more anomalous)
        # Invert so that higher scores indicate anomalies
        normalized_scores = 1 / (1 + np.exp(scores))  # Sigmoid transformation
        
        return normalized_scores
    
    def save(self, filepath: str) -> None:
        """Save trained model to file."""
        if not self.is_trained:
            raise RuntimeError("Cannot save untrained model")
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_cols': self.feature_cols,
            'contamination': self.contamination,
            'n_estimators': self.n_estimators
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath: str) -> None:
        """Load trained model from file."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_cols = model_data['feature_cols']
        self.contamination = model_data['contamination']
        self.n_estimators = model_data['n_estimators']
        self.is_trained = True
        
        logger.info(f"Model loaded from {filepath}")


class StatisticalDetector:
    """Statistical methods for anomaly detection (Z-score, IQR)."""
    
    def __init__(self, method: str = "zscore", threshold: float = 3.0):
        """
        Initialize statistical detector.
        
        Args:
            method: Detection method ('zscore' or 'iqr')
            threshold: Threshold for anomaly classification
                      - For zscore: number of standard deviations (typically 2.5-3.0)
                      - For iqr: IQR multiplier (typically 1.5-3.0)
        """
        if method not in ['zscore', 'iqr']:
            raise ValueError(f"Unknown method: {method}. Use 'zscore' or 'iqr'")
        
        self.method = method
        self.threshold = threshold
        self.stats = {}
        
        logger.info(f"Initialized StatisticalDetector with method={method}, threshold={threshold}")
    
    def fit(self, data: pd.DataFrame, value_col: str = 'value') -> None:
        """
        Fit statistical parameters on training data.
        
        Args:
            data: Training data
            value_col: Column containing values to analyze
        """
        values = data[value_col].values
        
        if self.method == 'zscore':
            self.stats['mean'] = np.mean(values)
            self.stats['std'] = np.std(values)
            logger.info(f"Fitted Z-score: mean={self.stats['mean']:.4f}, std={self.stats['std']:.4f}")
        
        elif self.method == 'iqr':
            self.stats['q25'] = np.percentile(values, 25)
            self.stats['q75'] = np.percentile(values, 75)
            self.stats['iqr'] = self.stats['q75'] - self.stats['q25']
            logger.info(f"Fitted IQR: Q25={self.stats['q25']:.4f}, Q75={self.stats['q75']:.4f}, IQR={self.stats['iqr']:.4f}")
    
    def detect(self, data: pd.DataFrame, value_col: str = 'value') -> np.ndarray:
        """
        Detect anomalies using statistical methods.
        
        Args:
            data: Data to analyze
            value_col: Column containing values to analyze
            
        Returns:
            Array of predictions (1 = anomaly, 0 = normal)
        """
        values = data[value_col].values
        
        if self.method == 'zscore':
            if 'mean' not in self.stats:
                # Fit on the fly if not already fitted
                self.fit(data, value_col)
            
            mean = self.stats['mean']
            std = self.stats['std']
            
            if std == 0:
                # No variation - no anomalies
                return np.zeros(len(values), dtype=int)
            
            z_scores = np.abs((values - mean) / std)
            anomalies = (z_scores > self.threshold).astype(int)
        
        elif self.method == 'iqr':
            if 'iqr' not in self.stats:
                # Fit on the fly if not already fitted
                self.fit(data, value_col)
            
            q25 = self.stats['q25']
            q75 = self.stats['q75']
            iqr = self.stats['iqr']
            
            lower_bound = q25 - self.threshold * iqr
            upper_bound = q75 + self.threshold * iqr
            
            anomalies = ((values < lower_bound) | (values > upper_bound)).astype(int)
        
        logger.info(f"Detected {anomalies.sum():,} anomalies using {self.method} method")
        
        return anomalies
    
    def score(self, data: pd.DataFrame, value_col: str = 'value') -> np.ndarray:
        """
        Get anomaly scores.
        
        Args:
            data: Data to score
            value_col: Column containing values
            
        Returns:
            Array of anomaly scores (higher = more anomalous)
        """
        values = data[value_col].values
        
        if self.method == 'zscore':
            if 'mean' not in self.stats:
                self.fit(data, value_col)
            
            mean = self.stats['mean']
            std = self.stats['std']
            
            if std == 0:
                return np.zeros(len(values))
            
            # Absolute z-scores as anomaly scores
            scores = np.abs((values - mean) / std)
        
        elif self.method == 'iqr':
            if 'iqr' not in self.stats:
                self.fit(data, value_col)
            
            q25 = self.stats['q25']
            q75 = self.stats['q75']
            iqr = self.stats['iqr']
            
            # Distance from IQR bounds
            lower_bound = q25 - self.threshold * iqr
            upper_bound = q75 + self.threshold * iqr
            
            # Score based on distance from bounds
            scores = np.maximum(
                (lower_bound - values) / iqr,
                (values - upper_bound) / iqr
            )
            scores = np.maximum(scores, 0)  # Clip negative scores
        
        # Normalize to [0, 1]
        if scores.max() > 0:
            scores = scores / scores.max()
        
        return scores


class EnsembleDetector:
    """Ensemble of multiple detection methods."""
    
    def __init__(self, detectors: list, voting: str = 'soft'):
        """
        Initialize ensemble detector.
        
        Args:
            detectors: List of detector instances
            voting: Voting method ('hard' = majority vote, 'soft' = average scores)
        """
        if not detectors:
            raise ValueError("At least one detector required")
        
        self.detectors = detectors
        self.voting = voting
        
        logger.info(f"Initialized EnsembleDetector with {len(detectors)} detectors, voting={voting}")
    
    def train(self, data: pd.DataFrame, **kwargs) -> None:
        """Train all detectors in the ensemble."""
        logger.info("Training ensemble detectors")
        
        for i, detector in enumerate(self.detectors):
            if hasattr(detector, 'train'):
                detector.train(data, **kwargs)
            elif hasattr(detector, 'fit'):
                detector.fit(data, **kwargs)
            
            logger.info(f"Trained detector {i+1}/{len(self.detectors)}")
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """
        Combine predictions from multiple detectors.
        
        Args:
            data: Data to predict on
            
        Returns:
            Array of ensemble predictions
        """
        if self.voting == 'hard':
            # Majority voting
            predictions = []
            for detector in self.detectors:
                pred = detector.predict(data)
                predictions.append(pred)
            
            predictions = np.array(predictions)
            # Anomaly if majority of detectors agree
            ensemble_pred = (predictions.sum(axis=0) > len(self.detectors) / 2).astype(int)
        
        elif self.voting == 'soft':
            # Average scores and threshold
            scores = []
            for detector in self.detectors:
                if hasattr(detector, 'score'):
                    score = detector.score(data)
                else:
                    # Use predictions as scores
                    score = detector.predict(data).astype(float)
                scores.append(score)
            
            scores = np.array(scores)
            avg_scores = scores.mean(axis=0)
            
            # Threshold at 0.5
            ensemble_pred = (avg_scores > 0.5).astype(int)
        
        logger.info(f"Ensemble predicted {ensemble_pred.sum():,} anomalies")
        
        return ensemble_pred
    
    def score(self, data: pd.DataFrame) -> np.ndarray:
        """Get ensemble anomaly scores."""
        scores = []
        
        for detector in self.detectors:
            if hasattr(detector, 'score'):
                score = detector.score(data)
            else:
                # Use predictions as scores
                score = detector.predict(data).astype(float)
            scores.append(score)
        
        scores = np.array(scores)
        ensemble_scores = scores.mean(axis=0)
        
        return ensemble_scores


def train_model(
    data: pd.DataFrame,
    model_type: str = "isolation_forest",
    **kwargs
) -> Any:
    """
    Train an anomaly detection model.
    
    Args:
        data: Training data
        model_type: Type of model to train ('isolation_forest', 'zscore', 'iqr', 'ensemble')
        **kwargs: Model-specific parameters
        
    Returns:
        Trained model instance
    """
    logger.info(f"Training {model_type} model")
    
    if model_type == "isolation_forest":
        contamination = kwargs.get('contamination', get_config_value('signal_analyst.contamination', 0.05))
        n_estimators = kwargs.get('n_estimators', 100)
        
        model = IsolationForestDetector(
            contamination=contamination,
            n_estimators=n_estimators
        )
        model.train(data, feature_cols=kwargs.get('feature_cols'))
    
    elif model_type == "zscore":
        threshold = kwargs.get('threshold', 3.0)
        model = StatisticalDetector(method='zscore', threshold=threshold)
        model.fit(data, value_col=kwargs.get('value_col', 'value'))
    
    elif model_type == "iqr":
        threshold = kwargs.get('threshold', 1.5)
        model = StatisticalDetector(method='iqr', threshold=threshold)
        model.fit(data, value_col=kwargs.get('value_col', 'value'))
    
    elif model_type == "ensemble":
        # Create ensemble of multiple detectors
        detectors = [
            IsolationForestDetector(contamination=0.05),
            StatisticalDetector(method='zscore', threshold=3.0),
            StatisticalDetector(method='iqr', threshold=1.5)
        ]
        
        model = EnsembleDetector(detectors, voting=kwargs.get('voting', 'soft'))
        model.train(data, feature_cols=kwargs.get('feature_cols'))
    
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    return model


def predict_anomalies(
    model: Any,
    data: pd.DataFrame,
    return_scores: bool = True
) -> pd.DataFrame:
    """
    Use trained model to predict anomalies.
    
    Args:
        model: Trained model instance
        data: Data to predict on
        return_scores: Whether to include anomaly scores
        
    Returns:
        DataFrame with anomaly predictions and scores
    """
    logger.info(f"Predicting anomalies on {len(data):,} samples")
    
    result_df = data.copy()
    
    # Get predictions
    predictions = model.predict(data)
    result_df['predicted_anomaly'] = predictions
    
    # Get scores if requested
    if return_scores and hasattr(model, 'score'):
        scores = model.score(data)
        result_df['anomaly_score'] = scores
    
    num_anomalies = predictions.sum()
    logger.info(f"Predicted {num_anomalies:,} anomalies ({num_anomalies/len(data)*100:.2f}%)")
    
    return result_df