#!/usr/bin/env python3
"""
Pipeline Verification Script

Tests each stage of the Mission Watch pipeline and generates a status report.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Test all module imports."""
    print("=" * 70)
    print("TESTING IMPORTS")
    print("=" * 70)
    
    results = {}
    
    # Test utilities
    try:
        from src.utils.config_loader import load_config, get_config_value
        from src.utils.logger import setup_logger
        from src.utils.helpers import format_timestamp, calculate_metrics
        results['utils'] = '✅ PASS'
    except Exception as e:
        results['utils'] = f'❌ FAIL: {str(e)}'
    
    # Test data pipeline
    try:
        from src.data.loader import load_telemetry_data
        from src.data.preprocessor import preprocess_telemetry
        from src.data.validator import validate_telemetry
        results['data_pipeline'] = '✅ PASS'
    except Exception as e:
        results['data_pipeline'] = f'❌ FAIL: {str(e)}'
    
    # Test Signal Analyst
    try:
        from src.agents.signal_analyst.models import IsolationForestDetector, train_model
        from src.agents.signal_analyst.scorer import calculate_anomaly_scores
        from src.agents.signal_analyst.detector import detect_anomalies
        results['signal_analyst'] = '✅ PASS'
    except Exception as e:
        results['signal_analyst'] = f'❌ FAIL: {str(e)}'
    
    # Test Advisor
    try:
        from src.agents.advisor.watsonx_client import initialize_client
        from src.agents.advisor.prompt_templates import build_prompt
        from src.agents.advisor.advisor import generate_ops_brief
        results['advisor'] = '✅ PASS'
    except Exception as e:
        results['advisor'] = f'❌ FAIL: {str(e)}'
    
    # Test Dashboard
    try:
        from src.dashboard.components.anomaly_viewer import render_anomaly_table
        from src.dashboard.components.telemetry_charts import plot_telemetry_timeseries
        from src.dashboard.components.ops_brief_display import render_brief
        results['dashboard_components'] = '✅ PASS'
    except Exception as e:
        results['dashboard_components'] = f'❌ FAIL: {str(e)}'
    
    # Test Evaluation
    try:
        from src.evaluation.metrics import calculate_all_metrics
        from src.evaluation.evaluator import evaluate_predictions
        from src.evaluation.report_generator import generate_evaluation_report
        results['evaluation'] = '✅ PASS'
    except Exception as e:
        results['evaluation'] = f'❌ FAIL: {str(e)}'
    
    for module, status in results.items():
        print(f"{module:25s}: {status}")
    
    return all('✅' in v for v in results.values())


def test_pipeline_stages():
    """Test each pipeline stage with synthetic data."""
    print("\n" + "=" * 70)
    print("TESTING PIPELINE STAGES")
    print("=" * 70)
    
    from src.data.preprocessor import preprocess_telemetry
    from src.agents.signal_analyst.detector import detect_anomalies
    from src.agents.advisor.advisor import generate_ops_brief
    
    # Create synthetic test data
    np.random.seed(42)
    n_samples = 1000
    
    test_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n_samples, freq='1min'),
        'sensor_id': np.random.choice(['thermal_1', 'power_1', 'comm_1'], n_samples),
        'value': np.concatenate([
            np.random.randn(950),  # Normal data
            np.random.randn(50) * 5 + 10  # Anomalies
        ]),
        'is_anomaly': np.concatenate([
            np.zeros(950),
            np.ones(50)
        ])
    })
    
    results = {}
    
    # Stage 1: Data Preprocessing
    try:
        print("\n1️⃣  Testing Data Preprocessing...")
        processed = preprocess_telemetry(test_data)
        print(f"   ✅ Preprocessed {len(processed)} records")
        print(f"   ✅ Features: {list(processed.columns)}")
        results['preprocessing'] = '✅ PASS'
    except Exception as e:
        print(f"   ❌ FAIL: {str(e)}")
        results['preprocessing'] = f'❌ FAIL: {str(e)}'
        return results
    
    # Stage 2: Anomaly Detection
    try:
        print("\n2️⃣  Testing Anomaly Detection...")
        anomalies_df = detect_anomalies(
            processed,
            model_type='isolation_forest',
            train_model_flag=True,
            contamination=0.05
        )
        detected = anomalies_df[anomalies_df['predicted_anomaly'] == 1]
        print(f"   ✅ Detected {len(detected)} anomalies")
        print(f"   ✅ Anomaly rate: {len(detected)/len(anomalies_df)*100:.2f}%")
        results['detection'] = '✅ PASS'
    except Exception as e:
        print(f"   ❌ FAIL: {str(e)}")
        results['detection'] = f'❌ FAIL: {str(e)}'
        return results
    
    # Stage 3: Evaluation
    try:
        print("\n3️⃣  Testing Evaluation...")
        from src.evaluation.evaluator import evaluate_predictions
        
        eval_results = evaluate_predictions(
            anomalies_df,
            ground_truth_col='is_anomaly',
            prediction_col='predicted_anomaly'
        )
        metrics = eval_results['overall_metrics']
        print(f"   ✅ Precision: {metrics['precision']:.3f}")
        print(f"   ✅ Recall: {metrics['recall']:.3f}")
        print(f"   ✅ F1 Score: {metrics['f1_score']:.3f}")
        results['evaluation'] = '✅ PASS'
    except Exception as e:
        print(f"   ❌ FAIL: {str(e)}")
        results['evaluation'] = f'❌ FAIL: {str(e)}'
    
    # Stage 4: Brief Generation
    try:
        print("\n4️⃣  Testing Brief Generation...")
        if not detected.empty:
            first_anomaly = detected.iloc[0].to_dict()
            brief = generate_ops_brief(first_anomaly)
            print(f"   ✅ Generated brief ({len(brief)} chars)")
            print(f"   ✅ Preview: {brief[:100]}...")
            results['brief_generation'] = '✅ PASS'
        else:
            print("   ⚠️  No anomalies to generate brief")
            results['brief_generation'] = '⚠️  SKIP'
    except Exception as e:
        print(f"   ❌ FAIL: {str(e)}")
        results['brief_generation'] = f'❌ FAIL: {str(e)}'
    
    return results


def generate_report():
    """Generate comprehensive status report."""
    print("\n" + "=" * 70)
    print("MISSION WATCH - PIPELINE STATUS REPORT")
    print("=" * 70)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test pipeline
    if imports_ok:
        pipeline_results = test_pipeline_stages()
    else:
        print("\n⚠️  Skipping pipeline tests due to import failures")
        pipeline_results = {}
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print("\n📋 Pipeline Flow:")
    print("   NASA Telemetry")
    print("        ↓")
    print("   1. Data Loader & Preprocessor")
    print("        ↓")
    print("   2. Signal Analyst (Anomaly Detection)")
    print("        ↓")
    print("   3. Evaluation (Metrics & Reports)")
    print("        ↓")
    print("   4. Advisor Agent (IBM Granite)")
    print("        ↓")
    print("   5. Streamlit Dashboard")
    
    print("\n✅ Implemented Modules:")
    print("   • Utils: config_loader, logger, helpers")
    print("   • Data: loader, preprocessor, validator")
    print("   • Signal Analyst: models, scorer, detector")
    print("   • Advisor: watsonx_client, prompt_templates, advisor")
    print("   • Dashboard: app, anomaly_viewer, telemetry_charts, ops_brief_display")
    print("   • Evaluation: metrics, evaluator, report_generator")
    print("   • Tests: integration tests, unit tests")
    print("   • Demo: command-line demo script")
    
    print("\n🎯 Key Features:")
    print("   • Multi-model detection (Isolation Forest, Z-score, IQR, Ensemble)")
    print("   • IBM Granite LLM integration with mock mode")
    print("   • Interactive Streamlit dashboard")
    print("   • Comprehensive evaluation metrics")
    print("   • Export capabilities (CSV, JSON, Markdown)")
    
    print("\n🚀 How to Run:")
    print("   Dashboard: streamlit run src/dashboard/app.py")
    print("   Demo:      python demo.py --evaluate")
    print("   Tests:     python -m pytest tests/")
    
    if imports_ok and all('✅' in v for v in pipeline_results.values()):
        print("\n✅ STATUS: ALL SYSTEMS OPERATIONAL")
    else:
        print("\n⚠️  STATUS: SOME ISSUES DETECTED (see details above)")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    generate_report()
