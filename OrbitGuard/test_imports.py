#!/usr/bin/env python3
"""Test imports individually to find issues."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing imports individually...\n")

# Test 1
print("1. Utils config_loader...", end=" ")
try:
    from src.utils.config_loader import load_config
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 2
print("2. Utils logger...", end=" ")
try:
    from src.utils.logger import setup_logger
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 3
print("3. Utils helpers...", end=" ")
try:
    from src.utils.helpers import format_timestamp
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 4
print("4. Data loader...", end=" ")
try:
    from src.data.loader import load_telemetry_data
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 5
print("5. Data preprocessor...", end=" ")
try:
    from src.data.preprocessor import preprocess_telemetry
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 6
print("6. Data validator...", end=" ")
try:
    from src.data.validator import validate_telemetry
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 7
print("7. Signal Analyst models...", end=" ")
try:
    from src.agents.signal_analyst.models import IsolationForestDetector
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 8
print("8. Signal Analyst scorer...", end=" ")
try:
    from src.agents.signal_analyst.scorer import calculate_anomaly_scores
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 9
print("9. Signal Analyst detector...", end=" ")
try:
    from src.agents.signal_analyst.detector import detect_anomalies
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 10
print("10. Advisor watsonx_client...", end=" ")
try:
    from src.agents.advisor.watsonx_client import initialize_client
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 11
print("11. Advisor advisor...", end=" ")
try:
    from src.agents.advisor.advisor import generate_ops_brief
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 12
print("12. Dashboard app...", end=" ")
try:
    from src.dashboard import app
    print("✅")
except Exception as e:
    print(f"❌ {e}")

# Test 13
print("13. Evaluation metrics...", end=" ")
try:
    from src.evaluation.metrics import calculate_all_metrics
    print("✅")
except Exception as e:
    print(f"❌ {e}")

print("\n✅ Import test complete")
