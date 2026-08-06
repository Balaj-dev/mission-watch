# Mission Watch - Implementation Checklist

## Repository Audit Summary

**Status**: Project scaffolded, but all core modules are stubs requiring implementation.

**Completed**:
- ✅ Project structure and folder organization
- ✅ Telemetry data loader (`data/load_telemetry.py`) - FULLY FUNCTIONAL
- ✅ Configuration file (`config.yaml`)
- ✅ Requirements.txt with all dependencies
- ✅ Documentation (README, AGENTS.md, PROJECT_STRUCTURE.md)
- ✅ Virtual environment setup
- ✅ Synthetic dataset generation (80K records, 8 channels, 25% anomalies)

---

## CRITICAL (Must Have for MVP)

### 1. Core Utilities (Foundation)
**Priority**: HIGHEST - Required by all other modules

- [ ] **`src/utils/config_loader.py`**
  - Implement `load_config()` - Load YAML config
  - Implement `get_config_value()` - Dot notation access
  - Implement `validate_config()` - Required fields check
  - **Blockers**: None
  - **Estimated Time**: 30 min

- [ ] **`src/utils/logger.py`**
  - Implement `setup_logger()` - Configure logging
  - Implement `log_anomaly_detection()` - Log detection events
  - Implement `log_advisor_call()` - Log LLM interactions
  - Create logs/ directory
  - **Blockers**: None
  - **Estimated Time**: 30 min

- [ ] **`src/utils/helpers.py`**
  - Implement `format_timestamp()`
  - Implement `calculate_metrics()` - Precision, recall, F1
  - Implement `create_directory_structure()`
  - **Blockers**: None
  - **Estimated Time**: 20 min

### 2. Data Pipeline
**Priority**: HIGH - Required for Signal Analyst

- [ ] **`src/data/loader.py`**
  - Implement `load_telemetry_data()` - Load from CSV/processed
  - Implement `load_batch()` - Load multiple files
  - Implement `get_available_datasets()` - List datasets
  - **Blockers**: config_loader
  - **Estimated Time**: 45 min

- [ ] **`src/data/preprocessor.py`**
  - Implement `clean_telemetry()` - Handle missing values
  - Implement `extract_features()` - Feature engineering
  - Implement `normalize_timestamps()`
  - Implement `create_sliding_windows()`
  - **Blockers**: None
  - **Estimated Time**: 1 hour

- [ ] **`src/data/validator.py`**
  - Implement `validate_schema()`
  - Implement `check_data_quality()`
  - Implement `generate_quality_report()`
  - **Blockers**: None
  - **Estimated Time**: 30 min

### 3. Signal Analyst Agent
**Priority**: CRITICAL - Core anomaly detection

- [ ] **`src/agents/signal_analyst/models.py`**
  - Implement `IsolationForestDetector` class
    - `__init__()` - Initialize model
    - `train()` - Train on data
    - `predict()` - Predict anomalies
  - Implement `StatisticalDetector` class
    - Z-score method
    - IQR method
  - Implement `train_model()` factory function
  - Implement `predict_anomalies()` wrapper
  - **Blockers**: preprocessor
  - **Estimated Time**: 2 hours

- [ ] **`src/agents/signal_analyst/scorer.py`**
  - Implement `calculate_anomaly_score()`
  - Implement `rank_anomalies()`
  - Implement `filter_by_threshold()`
  - **Blockers**: models
  - **Estimated Time**: 45 min

- [ ] **`src/agents/signal_analyst/detector.py`**
  - Implement `detect_anomalies()` - Main workflow
  - Implement `run_detection_pipeline()` - End-to-end
  - Implement `save_anomalies()` - Persist results
  - **Blockers**: models, scorer
  - **Estimated Time**: 1 hour

### 4. Advisor Agent (IBM Granite)
**Priority**: CRITICAL - Generate operational briefs

- [ ] **`src/agents/advisor/watsonx_client.py`**
  - Implement `WatsonxClient` class
    - `__init__()` - Initialize with API key
    - `generate_text()` - Call Granite model
    - `_handle_api_errors()` - Retry logic
  - Implement `initialize_client()` factory
  - **Blockers**: config_loader, logger
  - **Estimated Time**: 1.5 hours
  - **Note**: Can use mock/stub for demo without API key

- [ ] **`src/agents/advisor/prompt_templates.py`**
  - Implement `build_prompt()` - Construct prompts
  - Implement `format_anomaly_data()` - Format for LLM
  - Define prompt templates (already defined)
  - **Blockers**: None
  - **Estimated Time**: 30 min

- [ ] **`src/agents/advisor/advisor.py`**
  - Implement `generate_ops_brief()` - Main function
  - Implement `analyze_anomaly_context()` - Enrich context
  - Implement `format_brief()` - Structure output
  - **Blockers**: watsonx_client, prompt_templates
  - **Estimated Time**: 1 hour

### 5. Streamlit Dashboard
**Priority**: CRITICAL - User interface

- [ ] **`src/dashboard/components/anomaly_viewer.py`**
  - Implement `render_anomaly_table()`
  - Implement `render_anomaly_card()`
  - Implement `add_filters()`
  - **Blockers**: None
  - **Estimated Time**: 1 hour

- [ ] **`src/dashboard/components/telemetry_charts.py`**
  - Implement `plot_telemetry_timeseries()`
  - Implement `plot_anomaly_distribution()`
  - Implement `plot_feature_importance()`
  - **Blockers**: None
  - **Estimated Time**: 1.5 hours

- [ ] **`src/dashboard/components/ops_brief_display.py`**
  - Implement `render_brief()`
  - Implement `render_brief_history()`
  - Implement `export_brief()`
  - **Blockers**: None
  - **Estimated Time**: 45 min

- [ ] **`src/dashboard/app.py`**
  - Implement `main()` - App entry point
  - Implement `load_data_pipeline()` - Load data
  - Implement `run_agents()` - Execute agents in parallel
  - Implement `display_results()` - Render components
  - **Blockers**: All agents, all components
  - **Estimated Time**: 2 hours

### 6. Evaluation Pipeline
**Priority**: HIGH - Measure performance

- [ ] **Create `src/evaluation/` module**
  - `__init__.py`
  - `metrics.py` - Calculate precision, recall, F1
  - `evaluator.py` - Compare predictions vs ground truth
  - `report_generator.py` - Generate evaluation reports
  - **Blockers**: detector
  - **Estimated Time**: 1.5 hours

---

## IMPORTANT (Should Have)

### 7. Integration & Testing

- [ ] **End-to-end integration test**
  - Load data → Detect anomalies → Generate briefs → Display
  - **Blockers**: All critical components
  - **Estimated Time**: 1 hour

- [ ] **Create demo script**
  - `demo.py` - Run full pipeline without dashboard
  - **Blockers**: All critical components
  - **Estimated Time**: 30 min

### 8. Documentation Updates

- [ ] **Update README.md**
  - Add actual usage examples
  - Add evaluation results
  - Add screenshots (after dashboard works)
  - **Blockers**: Working dashboard
  - **Estimated Time**: 30 min

- [ ] **Create EVALUATION.md**
  - Document model performance
  - Include metrics and charts
  - **Blockers**: Evaluation pipeline
  - **Estimated Time**: 30 min

---

## NICE-TO-HAVE (Future Enhancements)

### 9. Advanced Features

- [ ] **Model persistence**
  - Save/load trained models
  - **Estimated Time**: 30 min

- [ ] **Real-time streaming**
  - Process telemetry in real-time
  - **Estimated Time**: 2 hours

- [ ] **Multi-model ensemble**
  - Combine multiple detection methods
  - **Estimated Time**: 1 hour

- [ ] **Alert system**
  - Email/Slack notifications for critical anomalies
  - **Estimated Time**: 1 hour

- [ ] **Historical analysis**
  - Compare current vs historical patterns
  - **Estimated Time**: 1.5 hours

### 10. Production Readiness

- [ ] **Unit tests**
  - Test each module independently
  - **Estimated Time**: 3 hours

- [ ] **CI/CD pipeline**
  - GitHub Actions for testing
  - **Estimated Time**: 1 hour

- [ ] **Docker containerization**
  - Dockerfile and docker-compose
  - **Estimated Time**: 1 hour

- [ ] **API endpoint**
  - REST API for anomaly detection
  - **Estimated Time**: 2 hours

---

## Implementation Order (Recommended)

### Phase 1: Foundation (2-3 hours)
1. Utils (config_loader, logger, helpers)
2. Data pipeline (loader, preprocessor, validator)

### Phase 2: Core Agents (4-5 hours)
3. Signal Analyst (models, scorer, detector)
4. Advisor Agent (watsonx_client, prompt_templates, advisor)

### Phase 3: User Interface (3-4 hours)
5. Dashboard components (anomaly_viewer, telemetry_charts, ops_brief_display)
6. Dashboard app (main integration)

### Phase 4: Evaluation (1-2 hours)
7. Evaluation pipeline (metrics, evaluator, report_generator)

### Phase 5: Polish (1-2 hours)
8. Integration testing
9. Documentation updates
10. Demo script

**Total Estimated Time**: 11-16 hours for MVP

---

## Current Blockers

1. **No API key for IBM watsonx** - Can implement with mock responses for demo
2. **All src/ modules are stubs** - Need to implement from scratch

---

## Next Steps

1. ✅ Complete repository audit
2. ✅ Create prioritized checklist
3. ⏭️ Start implementing Phase 1 (Foundation)
4. ⏭️ Continue with Phase 2 (Core Agents)
5. ⏭️ Build Phase 3 (Dashboard)
6. ⏭️ Add Phase 4 (Evaluation)
7. ⏭️ Polish Phase 5 (Testing & Docs)

---

## Notes

- **Data is ready**: Synthetic dataset with 80K records and labeled anomalies
- **Structure is solid**: Well-organized, modular architecture
- **Dependencies installed**: All packages available in venv
- **Documentation complete**: Clear guidelines in AGENTS.md and PROJECT_STRUCTURE.md
- **Focus on MVP**: Get working end-to-end demo first, then enhance
