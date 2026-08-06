#!/usr/bin/env python3
"""
Quick status check for Mission Watch implementation.
Tests imports and provides implementation report.
"""

import sys
from pathlib import Path

def check_module(module_path, description):
    """Test if a module can be imported."""
    try:
        exec(f"import {module_path}")
        return "✅ IMPLEMENTED"
    except ImportError as e:
        return f"❌ MISSING: {str(e)}"
    except Exception as e:
        return f"⚠️  ERROR: {str(e)}"

def main():
    print("=" * 70)
    print("MISSION WATCH - IMPLEMENTATION STATUS REPORT")
    print("=" * 70)
    
    # Add project to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    modules = {
        "Utils": [
            ("src.utils.config_loader", "Configuration management"),
            ("src.utils.logger", "Logging system"),
            ("src.utils.helpers", "Helper utilities"),
        ],
        "Data Pipeline": [
            ("src.data.loader", "Data loading"),
            ("src.data.preprocessor", "Data preprocessing"),
            ("src.data.validator", "Data validation"),
        ],
        "Signal Analyst": [
            ("src.agents.signal_analyst.models", "ML models"),
            ("src.agents.signal_analyst.scorer", "Anomaly scoring"),
            ("src.agents.signal_analyst.detector", "Detection orchestration"),
        ],
        "Advisor Agent": [
            ("src.agents.advisor.watsonx_client", "IBM watsonx client"),
            ("src.agents.advisor.prompt_templates", "Prompt templates"),
            ("src.agents.advisor.advisor", "Brief generation"),
        ],
        "Dashboard": [
            ("src.dashboard.components.anomaly_viewer", "Anomaly viewer"),
            ("src.dashboard.components.telemetry_charts", "Charts"),
            ("src.dashboard.components.ops_brief_display", "Brief display"),
            ("src.dashboard.app", "Main application"),
        ],
        "Evaluation": [
            ("src.evaluation.metrics", "Performance metrics"),
            ("src.evaluation.evaluator", "Model evaluation"),
            ("src.evaluation.report_generator", "Report generation"),
        ],
    }
    
    all_ok = True
    
    for category, module_list in modules.items():
        print(f"\n{category}:")
        print("-" * 70)
        for module_path, description in module_list:
            status = check_module(module_path, description)
            print(f"  {description:30s}: {status}")
            if "❌" in status or "⚠️" in status:
                all_ok = False
    
    print("\n" + "=" * 70)
    print("PIPELINE FLOW:")
    print("=" * 70)
    print("""
    NASA Telemetry Data
          ↓
    1. Data Loader (src.data.loader)
          ↓
    2. Preprocessor (src.data.preprocessor)
          ↓
    3. Validator (src.data.validator)
          ↓
    4. Signal Analyst (src.agents.signal_analyst.detector)
          ├─ Models (isolation_forest, zscore, iqr, ensemble)
          ├─ Scorer (anomaly scoring & ranking)
          └─ Detector (orchestration)
          ↓
    5. Evaluation (src.evaluation.evaluator)
          ├─ Metrics (precision, recall, F1)
          └─ Reports (MD, HTML, JSON)
          ↓
    6. Advisor Agent (src.agents.advisor.advisor)
          ├─ watsonx Client (IBM Granite LLM)
          ├─ Prompt Templates
          └─ Brief Generation
          ↓
    7. Streamlit Dashboard (src.dashboard.app)
          ├─ Anomaly Viewer
          ├─ Telemetry Charts
          └─ Ops Brief Display
    """)
    
    print("=" * 70)
    print("KEY FEATURES:")
    print("=" * 70)
    print("""
    ✅ Multi-model detection (Isolation Forest, Z-score, IQR, Ensemble)
    ✅ IBM Granite LLM integration with mock mode fallback
    ✅ Interactive Streamlit dashboard with real-time updates
    ✅ Comprehensive evaluation metrics and reports
    ✅ Export capabilities (CSV, JSON, Markdown, HTML)
    ✅ Modular architecture for easy extension
    ✅ Centralized logging and configuration
    ✅ Error handling throughout pipeline
    """)
    
    print("=" * 70)
    print("HOW TO RUN:")
    print("=" * 70)
    print("""
    1. Dashboard (Interactive UI):
       streamlit run src/dashboard/app.py
    
    2. Demo Script (Command-line):
       python demo.py --evaluate
    
    3. Tests:
       python -m pytest tests/
    
    4. Generate Synthetic Data:
       python data/load_telemetry.py
    """)
    
    print("=" * 70)
    print("CONFIGURATION:")
    print("=" * 70)
    print("""
    - Edit config.yaml for all settings
    - Set IBM_CLOUD_API_KEY in .env for watsonx
    - Mock mode enabled by default (no API key needed)
    - Data paths: data/raw/, data/processed/, data/anomalies/
    """)
    
    print("=" * 70)
    if all_ok:
        print("STATUS: ✅ ALL MODULES IMPLEMENTED AND READY")
    else:
        print("STATUS: ⚠️  SOME MODULES HAVE ISSUES (see details above)")
    print("=" * 70)

if __name__ == "__main__":
    main()
