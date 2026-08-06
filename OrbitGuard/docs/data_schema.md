# Telemetry Data Schema

## Overview

This document defines the expected schema for NASA SMAP/MSL telemetry data files.

## File Formats

Supported formats:
- CSV (`.csv`)
- JSON (`.json`)

## Required Columns

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `timestamp` | datetime/string | UTC timestamp of measurement | `2024-01-15 14:30:00` |
| `sensor_id` | string | Unique sensor identifier | `TEMP_001`, `PRESS_042` |
| `value` | float | Measured sensor value | `23.5`, `101.325` |

## Optional Columns

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `unit` | string | Measurement unit | `celsius`, `kPa` |
| `quality_flag` | int | Data quality indicator (0=good, 1=suspect, 2=bad) | `0` |
| `spacecraft_id` | string | Spacecraft identifier | `MSL`, `SMAP` |
| `subsystem` | string | Spacecraft subsystem | `thermal`, `power`, `comms` |

## CSV Format Example

```csv
timestamp,sensor_id,value,unit,quality_flag,subsystem
2024-01-15 14:30:00,TEMP_001,23.5,celsius,0,thermal
2024-01-15 14:30:01,TEMP_001,23.6,celsius,0,thermal
2024-01-15 14:30:02,TEMP_001,45.2,celsius,1,thermal
2024-01-15 14:30:00,PRESS_042,101.3,kPa,0,power
```

## JSON Format Example

```json
[
  {
    "timestamp": "2024-01-15T14:30:00Z",
    "sensor_id": "TEMP_001",
    "value": 23.5,
    "unit": "celsius",
    "quality_flag": 0,
    "subsystem": "thermal"
  },
  {
    "timestamp": "2024-01-15T14:30:01Z",
    "sensor_id": "TEMP_001",
    "value": 23.6,
    "unit": "celsius",
    "quality_flag": 0,
    "subsystem": "thermal"
  }
]
```

## Data Validation Rules

1. **Timestamp**: Must be valid ISO 8601 or parseable datetime string
2. **Sensor ID**: Non-empty string, alphanumeric with underscores
3. **Value**: Numeric (int or float), not NaN
4. **Quality Flag**: Integer 0-2 if present
5. **No Duplicates**: Unique (timestamp, sensor_id) combinations

## Anomaly Output Schema

Detected anomalies are saved with additional fields:

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `anomaly_score` | float | Confidence score (0.0 to 1.0) |
| `detection_method` | string | Method used (`isolation_forest`, `statistical`) |
| `severity` | string | Severity level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) |
| `detected_at` | datetime | When anomaly was detected |

## Notes

- All timestamps should be in UTC
- Missing values in optional columns are acceptable
- Files can contain multiple sensors and subsystems
- Recommended file naming: `telemetry_YYYYMMDD_HHMMSS.csv`
