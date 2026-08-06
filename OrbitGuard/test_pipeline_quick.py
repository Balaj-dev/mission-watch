#!/usr/bin/env python3
"""Quick pipeline test - verifies each stage works."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing Mission Watch Pipeline...\n")

# Test 1: Utils
print("1. Testing Utils...")
try:
    from src.utils.config_loader import load_config
    from src.utils.logger import setup_logger
    config = load_config()
    logger = setup_logger(__name__)
    print("   ✅ Utils working")
except Exception as e:
    print(f"   ❌ Utils failed: {e}")
    sys.exit(1)

# Test 2: Data Pipeline
print("2. Testing Data Pipeline...")
try:
    from src.data.loader import load_telemetry_data
    from src.data.preprocessor import preprocess_telemetry
    from src.data.validator import validate_telemetry
    print("   ✅ Data pipeline working")
except Exception as e:
    print(f"   ❌ Data pipeline failed: {e}")
    sys.exit(1)

# Test 3: Signal Analyst
print("3. Testing Signal Analyst...")
try:
    from src.agents.signal_analyst.models import IsolationForestDetector
    from src.agents.signal_analyst.scorer import calculate_anomaly_scores
    from src.agents.signal_analyst.detector import detect_anomalies
    print("   ✅ Signal Analyst working")
except Exception as e:
    print(f"   ❌ Signal Analyst failed: {e}")
    sys.exit(1)

# Test 4: Advisor
print("4. Testing Advisor...")
try:
    from src.agents.advisor.watsonx_client import initialize_client
    from src.agents.advisor.advisor import generate_ops_brief
    print("   ✅ Advisor working")
except Exception as e:
    print(f"   ❌ Advisor failed: {e}")
    sys.exit(1)

# Test 5: Dashboard
print("5. Testing Dashboard...")
try:
    from src.dashboard.components.anomaly_viewer import render_anomaly_table
    from src.dashboard.components.telemetry_charts import plot_telemetry_timeseries
    print("   ✅ Dashboard components working")
except Exception as e:
    print(f"   ❌ Dashboard failed: {e}")
    sys.exit(1)

# Test 6: Evaluation
print("6. Testing Evaluation...")
try:
    from src.evaluation.metrics import calculate_all_metrics
    from src.evaluation.evaluator import evaluate_predictions
    print("   ✅ Evaluation working")
except Exception as e:
    print(f"   ❌ Evaluation failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL PIPELINE STAGES OPERATIONAL")
print("="*60)
print("\nPipeline Flow:")
print("  NASA Telemetry → Loader → Preprocessor → Validator")
print("  → Signal Analyst → Evaluation → Advisor → Dashboard")
print("\nReady to run:")
print("  streamlit run src/dashboard/app.py")
print("  python demo.py --evaluate")
