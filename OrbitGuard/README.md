# Mission Watch 🛰️

Multi-agent anomaly triage system for spacecraft telemetry monitoring.

## Overview

Mission Watch analyzes NASA SMAP/MSL telemetry data using a two-agent system:
- **Signal Analyst**: Detects anomalies using machine learning (Isolation Forest, statistical methods)
- **Advisor**: Generates plain-language operational briefs using IBM Granite LLM

## Features

- 🔍 Real-time anomaly detection in spacecraft telemetry
- 🤖 AI-powered operational briefs for mission control
- 📊 Interactive Streamlit dashboard
- ⚡ Parallel agent architecture for fast processing

## Tech Stack

- **Python 3.11+**
- **Data & ML**: pandas, scikit-learn
- **LLM**: IBM watsonx/Granite
- **Dashboard**: Streamlit, Plotly

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd OrbitGuard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**
   ```bash
   cp .env.example .env
   # Edit .env with your IBM Cloud API key
   ```

4. **Configure settings**
   ```bash
   # Edit config.yaml to customize:
   # - Detection model parameters
   # - IBM watsonx API settings
   # - Dashboard preferences
   ```

5. **Place NASA telemetry data**
   ```bash
   # Add your SMAP/MSL telemetry files to:
   data/raw/
   ```

## Usage

Run the dashboard:
```bash
streamlit run src/dashboard/app.py
```

The dashboard will:
1. Load telemetry data from `data/raw/`
2. Run Signal Analyst to detect anomalies
3. Run Advisor in parallel to generate briefs
4. Display results in real-time

## Project Structure

```
OrbitGuard/
├── src/
│   ├── data/              # Data loading and preprocessing
│   ├── agents/
│   │   ├── signal_analyst/  # ML-based anomaly detection
│   │   └── advisor/         # LLM-based brief generation
│   ├── dashboard/         # Streamlit UI
│   └── utils/             # Configuration, logging, helpers
├── data/                  # Telemetry data storage
├── config.yaml            # Application configuration
└── requirements.txt       # Python dependencies
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed architecture.

## Configuration

Edit `config.yaml` to customize:

- **Signal Analyst**: Model type, contamination rate, thresholds
- **Advisor**: Model name, API endpoint, generation parameters
- **Dashboard**: Title, refresh interval, display limits

## Data Format

Expected telemetry data format:
- CSV or JSON files
- Required columns: timestamp, sensor_id, value
- See `docs/data_schema.md` for full schema specification

## Development

For development guidelines and conventions, see [AGENTS.md](AGENTS.md).

### Adding New Features

- **New detection model**: Add to `src/agents/signal_analyst/models.py`
- **Custom prompts**: Edit `src/agents/advisor/prompt_templates.py`
- **Dashboard components**: Create in `src/dashboard/components/`

## License

[Your License Here]

## Hackathon

Built for [Hackathon Name] - [Date]

## Contributors

[Your Name/Team]

## Acknowledgments

- NASA for SMAP/MSL telemetry datasets
- IBM for watsonx/Granite LLM platform
