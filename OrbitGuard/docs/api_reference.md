# API Reference

## Data Module (`src.data`)

### loader.py

#### `load_telemetry_data(file_path: str) -> pd.DataFrame`
Load raw telemetry data from CSV/JSON file.

**Parameters:**
- `file_path` (str): Path to the telemetry data file

**Returns:**
- `pd.DataFrame`: DataFrame containing telemetry data

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file format is invalid

---

#### `load_batch(data_dir: str, date_range: Optional[tuple] = None) -> pd.DataFrame`
Load multiple telemetry files by date range.

**Parameters:**
- `data_dir` (str): Directory containing telemetry files
- `date_range` (Optional[tuple]): Tuple of (start_date, end_date)

**Returns:**
- `pd.DataFrame`: Combined DataFrame from multiple files

---

### preprocessor.py

#### `clean_telemetry(df: pd.DataFrame) -> pd.DataFrame`
Clean telemetry data by handling missing values and outliers.

**Parameters:**
- `df` (pd.DataFrame): Raw telemetry DataFrame

**Returns:**
- `pd.DataFrame`: Cleaned DataFrame

---

#### `extract_features(df: pd.DataFrame) -> pd.DataFrame`
Engineer features for ML models from raw telemetry.

**Parameters:**
- `df` (pd.DataFrame): Cleaned telemetry DataFrame

**Returns:**
- `pd.DataFrame`: DataFrame with engineered features

---

## Signal Analyst Module (`src.agents.signal_analyst`)

### detector.py

#### `detect_anomalies(telemetry_data: pd.DataFrame) -> pd.DataFrame`
Main anomaly detection workflow.

**Parameters:**
- `telemetry_data` (pd.DataFrame): Preprocessed telemetry DataFrame

**Returns:**
- `pd.DataFrame`: DataFrame containing detected anomalies with scores

---

### models.py

#### `class IsolationForestDetector`
Isolation Forest-based anomaly detector.

**Methods:**
- `__init__(contamination: float = 0.05, n_estimators: int = 100)`
- `train(data: pd.DataFrame) -> None`
- `predict(data: pd.DataFrame) -> np.ndarray`

---

#### `class StatisticalDetector`
Statistical methods for anomaly detection.

**Methods:**
- `__init__(method: str = "zscore", threshold: float = 3.0)`
- `detect(data: pd.DataFrame) -> np.ndarray`

---

### scorer.py

#### `calculate_anomaly_score(anomaly: Dict[str, Any]) -> float`
Calculate severity score for a single anomaly.

**Parameters:**
- `anomaly` (Dict[str, Any]): Dictionary containing anomaly data

**Returns:**
- `float`: Severity score (0.0 to 1.0)

---

## Advisor Module (`src.agents.advisor`)

### advisor.py

#### `generate_ops_brief(anomaly_data: Dict[str, Any]) -> str`
Generate operational brief from anomaly data.

**Parameters:**
- `anomaly_data` (Dict[str, Any]): Dictionary containing anomaly information

**Returns:**
- `str`: Plain-language operational brief text

---

### watsonx_client.py

#### `class WatsonxClient`
Client for IBM watsonx/Granite API.

**Methods:**
- `__init__(api_key: str, endpoint: str, model_name: str)`
- `generate_text(prompt: str, **model_params) -> str`

---

## Dashboard Module (`src.dashboard`)

### app.py

#### `main() -> None`
Main application entry point. Initializes dashboard and runs agents.

---

#### `load_data_pipeline() -> pd.DataFrame`
Load and preprocess telemetry data.

**Returns:**
- `pd.DataFrame`: Preprocessed telemetry DataFrame

---

#### `run_agents(telemetry_data: pd.DataFrame) -> Dict[str, Any]`
Execute Signal Analyst and Advisor agents in parallel.

**Parameters:**
- `telemetry_data` (pd.DataFrame): Preprocessed telemetry data

**Returns:**
- `Dict[str, Any]`: Dictionary containing agent results

---

## Utilities Module (`src.utils`)

### config_loader.py

#### `load_config(config_path: str = "config.yaml") -> Dict[str, Any]`
Load configuration from YAML file.

**Parameters:**
- `config_path` (str): Path to configuration file

**Returns:**
- `Dict[str, Any]`: Dictionary containing configuration

---

### logger.py

#### `setup_logger(name: str, level: str = "INFO") -> logging.Logger`
Configure and return a logger instance.

**Parameters:**
- `name` (str): Logger name (typically `__name__`)
- `level` (str): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')

**Returns:**
- `logging.Logger`: Configured logger instance

---

## Usage Examples

### Loading Data
```python
from src.data.loader import load_telemetry_data
from src.data.preprocessor import clean_telemetry

# Load raw data
df = load_telemetry_data("data/raw/telemetry_20240115.csv")

# Clean data
clean_df = clean_telemetry(df)
```

### Detecting Anomalies
```python
from src.agents.signal_analyst.detector import detect_anomalies

# Detect anomalies
anomalies = detect_anomalies(clean_df)
```

### Generating Briefs
```python
from src.agents.advisor.advisor import generate_ops_brief

# Generate brief for first anomaly
anomaly_data = anomalies.iloc[0].to_dict()
brief = generate_ops_brief(anomaly_data)
print(brief)
```
