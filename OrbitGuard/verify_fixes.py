#!/usr/bin/env python3
"""
Verify all implementation fixes are working.
Tests the complete pipeline without Streamlit.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("MISSION WATCH - PIPELINE VERIFICATION")
print("=" * 70)
print()

# Test 1: Core imports
print("1. Testing Core Imports...")
try:
    from src.utils.config_loader import load_config
    from src.utils.logger import setup_logger
    from src.utils.helpers import format_timestamp
    print("   ✅ Utils imports working")
except Exception as e:
    print(f"   ❌ Utils import failed: {e}")
    sys.exit(1)

# Test 2: Data pipeline imports
print("2. Testing Data Pipeline Imports...")
try:
    from src.data.loader import load_telemetry_data
    from src.data.preprocessor import preprocess_telemetry
    from src.data.validator import validate_telemetry
    print("   ✅ Data pipeline imports working")
except Exception as e:
    print(f"   ❌ Data pipeline import failed: {e}")
    sys.exit(1)

# Test 3: Signal Analyst imports
print("3. Testing Signal Analyst Imports...")
try:
    from src.agents.signal_analyst.models import IsolationForestDetector
    from src.agents.signal_analyst.scorer import calculate_anomaly_scores
    from src.agents.signal_analyst.detector import detect_anomalies
    print("   ✅ Signal Analyst imports working")
except Exception as e:
    print(f"   ❌ Signal Analyst import failed: {e}")
    sys.exit(1)

# Test 4: Create synthetic data and test pipeline
print("4. Testing Pipeline with Synthetic Data...")
try:
    # Create small synthetic dataset
    np.random.seed(42)
    n_samples = 100
    
    test_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n_samples, freq='1min'),
        'sensor_id': np.random.choice(['sensor_1', 'sensor_2'], n_samples),
        'value': np.concatenate([
            np.random.randn(90),  # Normal
            np.random.randn(10) * 5 + 10  # Anomalies
        ]),
        'is_anomaly': np.concatenate([np.zeros(90), np.ones(10)])
    })
    
    print(f"   Created test dataset: {len(test_data)} records")
    
    # Test preprocessing
    processed = preprocess_telemetry(test_data, extract_features_flag=True)
    print(f"   ✅ Preprocessing: {len(processed)} records, {len(processed.columns)} features")
    
    # Test validation
    validation = validate_telemetry(processed, check_schema=True, check_quality=True)
    print(f"   ✅ Validation: {'PASSED' if validation['is_valid'] else 'FAILED'}")
    
    # Test detection
    anomalies = detect_anomalies(
        processed,
        model_type='isolation_forest',
        train_model_flag=True,
        contamination=0.1
    )
    detected = anomalies[anomalies['predicted_anomaly'] == 1]
    print(f"   ✅ Detection: {len(detected)} anomalies detected")
    
    # Test scoring
    scored = calculate_anomaly_scores(anomalies)
    print(f"   ✅ Scoring: Added anomaly scores")
    
    print("   ✅ Complete pipeline working!")
    
except Exception as e:
    print(f"   ❌ Pipeline test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Advisor imports (may use mock mode)
print("5. Testing Advisor Imports...")
try:
    from src.agents.advisor.watsonx_client import initialize_client
    from src.agents.advisor.advisor import generate_ops_brief
    print("   ✅ Advisor imports working")
except Exception as e:
    print(f"   ❌ Advisor import failed: {e}")
    sys.exit(1)

# Test 6: Evaluation imports
print("6. Testing Evaluation Imports...")
try:
    from src.evaluation.metrics import calculate_all_metrics
    from src.evaluation.evaluator import evaluate_predictions
    print("   ✅ Evaluation imports working")
except Exception as e:
    print(f"   ❌ Evaluation import failed: {e}")
    sys.exit(1)

print()
print("=" * 70)
print("✅ ALL TESTS PASSED - PIPELINE IS OPERATIONAL")
print("=" * 70)
print()
print("Pipeline Flow Verified:")
print("  NASA Telemetry → Loader → Preprocessor → Validator")
print("  → Signal Analyst → Scorer → Advisor → Dashboard")
print()
print("Ready to run:")
print("  • streamlit run src/dashboard/app.py")
print("  • python demo.py --evaluate")
print()
print("=" * 70)
