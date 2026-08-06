#!/usr/bin/env python3
"""
Mission Watch - Demo Script

This script demonstrates the complete anomaly detection pipeline
without requiring the Streamlit dashboard. Useful for testing,
debugging, and batch processing.

Usage:
    python demo.py [--data-path PATH] [--model-type TYPE] [--output-dir DIR]
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.utils.config_loader import load_config
from src.agents.signal_analyst.detector import run_detection_pipeline
from src.agents.advisor.advisor import create_advisor_pipeline
from src.evaluation.evaluator import evaluate_predictions
from src.evaluation.report_generator import generate_evaluation_report

logger = setup_logger(__name__)


def main():
    """Main demo execution."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Mission Watch - Anomaly Detection Demo'
    )
    parser.add_argument(
        '--data-path',
        type=str,
        default='data/processed/synthetic_telemetry.csv',
        help='Path to telemetry data file'
    )
    parser.add_argument(
        '--model-type',
        type=str,
        default='isolation_forest',
        choices=['isolation_forest', 'zscore', 'iqr', 'ensemble'],
        help='Anomaly detection model type'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/demo_output',
        help='Directory for output files'
    )
    parser.add_argument(
        '--contamination',
        type=float,
        default=0.05,
        help='Expected proportion of anomalies'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.7,
        help='Anomaly score threshold'
    )
    parser.add_argument(
        '--brief-mode',
        type=str,
        default='consolidated',
        choices=['individual', 'consolidated'],
        help='Brief generation mode'
    )
    parser.add_argument(
        '--evaluate',
        action='store_true',
        help='Run evaluation if ground truth available'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print("=" * 70)
    print("🛰️  MISSION WATCH - ANOMALY DETECTION DEMO")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Data Path: {args.data_path}")
    print(f"  Model Type: {args.model_type}")
    print(f"  Contamination: {args.contamination}")
    print(f"  Threshold: {args.threshold}")
    print(f"  Output Directory: {args.output_dir}")
    print(f"  Brief Mode: {args.brief_mode}")
    print("\n" + "=" * 70 + "\n")
    
    try:
        # Step 1: Run Signal Analyst
        logger.info("STEP 1: Running Signal Analyst Agent")
        print("📊 STEP 1: Running Signal Analyst Agent...")
        
        detection_results = run_detection_pipeline(
            data_source=args.data_path,
            output_dir=args.output_dir,
            model_type=args.model_type,
            save_results=True,
            contamination=args.contamination,
            threshold=args.threshold
        )
        
        anomalies = detection_results['anomalies']
        summary = detection_results['summary']
        
        print(f"\n✅ Detection Complete:")
        print(f"   - Total Records: {summary['total_records']:,}")
        print(f"   - Anomalies Detected: {summary['anomalies_detected']:,}")
        print(f"   - Anomaly Rate: {summary['anomaly_rate']:.2f}%")
        print(f"   - Execution Time: {summary['execution_time_seconds']:.2f}s")
        
        # Step 2: Run Advisor Agent
        if not anomalies.empty:
            logger.info("STEP 2: Running Advisor Agent")
            print("\n💬 STEP 2: Running Advisor Agent...")
            
            # Limit to top 10 anomalies for demo
            top_anomalies = anomalies.head(10)
            
            advisor_results = create_advisor_pipeline(
                top_anomalies,
                output_dir=args.output_dir,
                mode=args.brief_mode,
                save_briefs=True
            )
            
            briefs = advisor_results['briefs']
            
            print(f"\n✅ Briefs Generated: {len(briefs)}")
            
            # Display first brief
            if briefs:
                print("\n" + "=" * 70)
                print("SAMPLE OPERATIONAL BRIEF:")
                print("=" * 70)
                print(briefs[0][:500] + "..." if len(briefs[0]) > 500 else briefs[0])
                print("=" * 70)
        else:
            print("\n✅ No anomalies detected - skipping Advisor Agent")
        
        # Step 3: Evaluation (if ground truth available)
        if args.evaluate:
            logger.info("STEP 3: Running Evaluation")
            print("\n📈 STEP 3: Running Evaluation...")
            
            all_predictions = detection_results['all_predictions']
            
            if 'is_anomaly' in all_predictions.columns:
                eval_results = evaluate_predictions(
                    all_predictions,
                    ground_truth_col='is_anomaly',
                    prediction_col='predicted_anomaly',
                    score_col='anomaly_score'
                )
                
                metrics = eval_results['overall_metrics']
                
                print(f"\n✅ Evaluation Complete:")
                print(f"   - Precision: {metrics['precision']:.4f}")
                print(f"   - Recall: {metrics['recall']:.4f}")
                print(f"   - F1 Score: {metrics['f1_score']:.4f}")
                print(f"   - Accuracy: {metrics['accuracy']:.4f}")
                
                # Generate evaluation report
                report_path = Path(args.output_dir) / 'evaluation_report.md'
                report = generate_evaluation_report(
                    eval_results,
                    model_name=args.model_type,
                    output_path=str(report_path)
                )
                
                print(f"\n📄 Evaluation report saved to: {report_path}")
            else:
                print("\n⚠️  Ground truth not available - skipping evaluation")
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ DEMO COMPLETE")
        print("=" * 70)
        print(f"\nOutput files saved to: {args.output_dir}")
        print("\nNext steps:")
        print("  1. Review anomalies in the output directory")
        print("  2. Read operational briefs")
        if args.evaluate:
            print("  3. Check evaluation report for model performance")
        print("  4. Run Streamlit dashboard for interactive analysis:")
        print("     streamlit run src/dashboard/app.py")
        print("\n" + "=" * 70 + "\n")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        print(f"\n❌ ERROR: {str(e)}")
        print("\nCheck logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
