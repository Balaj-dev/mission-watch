# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

**Mission Watch** is a multi-agent anomaly triage system for spacecraft telemetry monitoring, built for hackathon deployment. The system analyzes NASA SMAP/MSL telemetry data using a parallel two-agent architecture:

- **Signal Analyst Agent**: Detects anomalies in telemetry data using machine learning (Isolation Forest, statistical methods)
- **Advisor Agent**: Generates plain-language operational briefs from detected anomalies using IBM Granite LLM via watsonx

**Tech Stack**: Python 3.11, pandas, scikit-learn, Streamlit, IBM watsonx/Granite

**Architecture Pattern**: Modular, configuration-driven design with parallel agent execution for optimal performance.

## Core Architecture Principles

### 1. Multi-Agent System Design

The project implements a **parallel agent architecture** where:
- Signal Analyst runs independently to detect anomalies quickly
- Advisor processes anomalies asynchronously to generate briefs
- Dashboard displays results as they become available (no blocking)

**Key Insight**: Agents are loosely coupled through data contracts (anomaly objects), not direct function calls. This enables independent scaling and testing.

### 2. Module Organization

```
src/
├── data/           # Data pipeline (load → preprocess → validate)
├── agents/         # Independent agent modules
│   ├── signal_analyst/  # ML-based anomaly detection
│   └── advisor/         # LLM-based brief generation
├── dashboard/      # Streamlit UI with reusable components
└── utils/          # Shared infrastructure (config, logging)
```

**Convention**: Each module is self-contained with clear input/output contracts. Cross-module dependencies flow through `utils/` or configuration.

### 3. Configuration-Driven Development

All runtime behavior is controlled via `config.yaml`:
- Model parameters (contamination, thresholds)
- API endpoints and credentials
- Data paths and processing options
- Dashboard settings

**Pattern**: Use `src/utils/config_loader.py` for all config access. Never hardcode paths, API keys, or model parameters.

## Building and Running

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys and paths
cp .env.example .env
# Edit config.yaml with your settings
```

### Running the Application
```bash
# Launch Streamlit dashboard (main entry point)
streamlit run src/dashboard/app.py

# The dashboard will:
# 1. Load telemetry data from data/raw/
# 2. Run Signal Analyst to detect anomalies
# 3. Run Advisor in parallel to generate briefs
# 4. Display results in real-time
```

### Data Preparation
```bash
# Place NASA SMAP/MSL telemetry files in:
data/raw/

# Expected format: CSV/JSON with timestamp and sensor readings
# See docs/data_schema.md for full schema specification
```

## Development Conventions

### Code Style
- **Python 3.11+** features encouraged (type hints, match statements)
- Follow PEP 8 for formatting
- Use descriptive function names that indicate purpose (e.g., `detect_anomalies`, `generate_ops_brief`)

### Agent Development Pattern

When implementing or modifying agents:

1. **Input/Output Contracts**: Define clear data structures
   ```python
   # Example: Anomaly object structure
   {
       'timestamp': datetime,
       'sensor_id': str,
       'value': float,
       'anomaly_score': float,
       'context': dict
   }
   ```

2. **Error Handling**: Agents must handle failures gracefully
   - Log errors using `src/utils/logger.py`
   - Return partial results when possible
   - Never crash the dashboard

3. **Configuration**: Read all parameters from config
   ```python
   from src.utils.config_loader import load_config
   config = load_config()
   threshold = config['signal_analyst']['anomaly_threshold']
   ```

### Logging Standards

Use centralized logging from `src/utils/logger.py`:
```python
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Starting anomaly detection")
logger.warning(f"Low confidence anomaly: {score}")
logger.error("API call failed", exc_info=True)
```

**Log Levels**:
- INFO: Normal operations, pipeline stages
- WARNING: Recoverable issues, low-confidence results
- ERROR: Failures requiring attention

### Data Processing Pipeline

Follow the three-stage pattern:
1. **Load** (`src/data/loader.py`): Read raw data, minimal transformation
2. **Preprocess** (`src/data/preprocessor.py`): Clean, engineer features, normalize
3. **Validate** (`src/data/validator.py`): Check quality, schema compliance

**Convention**: Each stage returns a pandas DataFrame with metadata dict.

### Dashboard Component Development

When creating Streamlit components in `src/dashboard/components/`:
- Keep components pure functions that take data and return rendered output
- Use Streamlit's caching (`@st.cache_data`) for expensive operations
- Follow naming: `render_<component_name>(data, **options)`

Example:
```python
import streamlit as st

@st.cache_data
def render_anomaly_table(anomalies: pd.DataFrame, max_rows: int = 50):
    """Display anomalies in interactive table."""
    st.dataframe(anomalies.head(max_rows))
```

## IBM watsonx/Granite Integration

### API Client Pattern
The Advisor agent uses `src/agents/advisor/watsonx_client.py` for all LLM interactions:
- Initialize once with credentials from config
- Implement retry logic with exponential backoff
- Handle rate limits gracefully
- Log all prompts and responses for debugging

### Prompt Engineering
Prompts are managed in `src/agents/advisor/prompt_templates.py`:
- Use template strings or Jinja2 for dynamic content
- Include clear instructions and context
- Specify output format (e.g., "Generate a 3-paragraph brief...")
- Version prompts when making significant changes

## Testing Strategy (Future)

While MVP skips formal testing for speed, the architecture supports:
- **Unit tests**: Test individual functions in isolation
- **Integration tests**: Test agent pipelines end-to-end
- **Mock data**: Use synthetic telemetry for reproducible tests

When adding tests later, place them in `tests/` mirroring `src/` structure.

## Key Files Reference

For detailed module responsibilities and function signatures, see:
- **PROJECT_STRUCTURE.md**: Complete architecture and file-by-file documentation
- **config.yaml**: All configurable parameters
- **docs/architecture.md**: System design and data flow diagrams
- **docs/data_schema.md**: Telemetry data format specification

## Common Development Tasks

### Adding a New Detection Model
1. Create model class in `src/agents/signal_analyst/models.py`
2. Implement `train_model()` and `predict_anomalies()` methods
3. Add model type to `config.yaml` under `signal_analyst.model_type`
4. Update `detector.py` to instantiate new model

### Modifying Advisor Prompts
1. Edit templates in `src/agents/advisor/prompt_templates.py`
2. Test with sample anomalies
3. Update `config.yaml` if new parameters needed (e.g., temperature)

### Adding Dashboard Visualizations
1. Create component in `src/dashboard/components/`
2. Import and call from `src/dashboard/app.py`
3. Use Streamlit's layout functions (columns, tabs, expander)

## Performance Considerations

- **Data Loading**: Use chunked reading for large telemetry files
- **ML Models**: Cache trained models to avoid retraining
- **LLM Calls**: Batch anomalies when possible to reduce API calls
- **Dashboard**: Use Streamlit's caching aggressively for data processing

## Security Notes

- **API Keys**: Never commit to git. Use `.env` file (gitignored)
- **Data Privacy**: Telemetry data may be sensitive. Follow data handling policies
- **LLM Outputs**: Validate and sanitize before displaying in dashboard

## Hackathon-Specific Notes

This project is optimized for rapid development and demo:
- **MVP Focus**: Core functionality over polish
- **No Tests**: Speed over test coverage (add later)
- **Local Data**: No cloud storage or databases
- **Single Config**: No dev/prod environments

When transitioning to production, consider:
- Adding comprehensive test suite
- Implementing proper error recovery
- Setting up CI/CD pipeline
- Adding authentication/authorization
- Scaling to cloud infrastructure

## Getting Help

- Review **PROJECT_STRUCTURE.md** for detailed module documentation
- Check `config.yaml` for available configuration options
- Examine existing code patterns before implementing new features
- Use logging extensively for debugging agent behavior
