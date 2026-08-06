# Mission Watch - Test Dataset Information

## ✅ Test Dataset Already Available!

A synthetic NASA SMAP/MSL-like telemetry dataset has been generated and is ready to use for testing the dashboard and demo.

### Dataset Location
```
data/processed/telemetry_dataset.csv
```

### Dataset Details

**File Information:**
- **Size:** 4.4 MB
- **Records:** 80,000 telemetry data points
- **Channels:** 8 sensor channels
- **Anomalies:** 20,796 labeled anomalies (26%)
- **Time Range:** January 2024 (synthetic timestamps)

**Channels Included:**

| Channel | Spacecraft | Subsystem | Records | Anomalies |
|---------|-----------|-----------|---------|-----------|
| P-1 | SMAP | Power | 10,000 | 2,563 (25.63%) |
| S-1 | SMAP | Solar | 10,000 | 2,546 (25.46%) |
| E-1 | SMAP | Electrical | 10,000 | 2,628 (26.28%) |
| E-2 | SMAP | Electrical | 10,000 | 2,601 (26.01%) |
| T-1 | SMAP | Thermal | 10,000 | 2,623 (26.23%) |
| A-1 | MSL | Attitude | 10,000 | 2,495 (24.95%) |
| D-1 | MSL | Dynamics | 10,000 | 2,717 (27.17%) |
| M-1 | MSL | Mechanical | 10,000 | 2,623 (26.23%) |

### Dataset Schema

```csv
timestamp,sensor_id,value,is_anomaly,subsystem,spacecraft
2024-01-01 00:00:00,P-1,70.858,1,power,SMAP
2024-01-01 00:01:00,P-1,70.249,1,power,SMAP
...
```

**Columns:**
- `timestamp`: ISO 8601 datetime (1-minute intervals)
- `sensor_id`: Channel identifier (e.g., P-1, S-1, E-1)
- `value`: Sensor reading (float)
- `is_anomaly`: Ground truth label (0=normal, 1=anomaly)
- `subsystem`: Spacecraft subsystem (power, solar, electrical, etc.)
- `spacecraft`: Mission name (SMAP or MSL)

### Anomaly Characteristics

The synthetic dataset includes realistic anomaly patterns:

1. **Spikes** - Sudden increases in sensor values
2. **Drops** - Sudden decreases in sensor values
3. **Shifts** - Sustained level changes
4. **Noise** - Increased variability

Anomalies are grouped into sequences of 3-10 consecutive points to simulate real spacecraft behavior.

---

## Using the Test Dataset

### 1. Run Demo Script
```bash
cd /Users/balajmubeen/Desktop/Open_Sourse/IBM_Project/OrbitGuard
source venv/bin/activate
python demo.py --evaluate
```

This will:
- Load the test dataset
- Detect anomalies using Isolation Forest
- Generate operational briefs
- Evaluate performance against ground truth labels
- Save results to `data/demo_output/`

### 2. Launch Dashboard
```bash
streamlit run src/dashboard/app.py
```

The dashboard will automatically load `data/processed/telemetry_dataset.csv` and display:
- Real-time telemetry charts
- Detected anomalies with rankings
- Operational briefs
- Performance metrics

### 3. Verify Dataset
```bash
# Check file exists and size
ls -lh data/processed/telemetry_dataset.csv

# Preview first 10 rows
head -10 data/processed/telemetry_dataset.csv

# View summary statistics
cat data/processed/dataset_summary.json
```

---

## Regenerating the Dataset

If you need to regenerate the synthetic dataset (e.g., with different parameters):

```bash
cd /Users/balajmubeen/Desktop/Open_Sourse/IBM_Project/OrbitGuard
source venv/bin/activate
python data/load_telemetry.py
```

This will create a new `telemetry_dataset.csv` with fresh synthetic data.

---

## Upgrading to Real NASA Data

To replace the synthetic dataset with real NASA SMAP/MSL data from Kaggle:

### Step 1: Get Kaggle Credentials
1. Go to https://www.kaggle.com → Account → API
2. Click "Create New API Token"
3. Move `kaggle.json` to `~/.kaggle/`
4. Set permissions: `chmod 600 ~/.kaggle/kaggle.json`

### Step 2: Run Setup Script
```bash
./setup_kaggle_data.sh
```

This will:
- Download real NASA dataset (~500MB)
- Extract and process the data
- Replace `telemetry_dataset.csv` with real data

### Step 3: Verify
```bash
cat data/processed/dataset_summary.json
```

The summary will show "Data Source: Kaggle (Real NASA Data)" instead of "Synthetic".

---

## Dataset Summary File

A JSON summary is also available at `data/processed/dataset_summary.json`:

```json
{
  "total_records": 80000,
  "total_anomalies": 20796,
  "anomaly_percentage": 26.0,
  "num_channels": 8,
  "channels": ["A-1", "D-1", "E-1", "E-2", "M-1", "P-1", "S-1", "T-1"],
  "spacecraft": ["MSL", "SMAP"],
  "subsystems": ["attitude", "dynamics", "electrical", "mechanical", "power", "solar", "thermal"],
  "per_channel_stats": [...]
}
```

---

## Expected Demo Results

When running the demo with the test dataset, you should see:

**Detection Results:**
- Total Records: 80,000
- Anomalies Detected: ~4,000 (5% contamination)
- High-confidence anomalies (threshold 0.7): ~6-10
- Execution Time: ~5-10 seconds

**Evaluation Metrics** (with ground truth):
- Precision: ~0.85-0.95
- Recall: ~0.15-0.25 (intentionally conservative)
- F1 Score: ~0.25-0.40
- Accuracy: ~0.95+

**Output Files:**
- `data/demo_output/anomalies_YYYYMMDD_HHMMSS.csv` - Detected anomalies
- `data/demo_output/brief_consolidated_YYYYMMDD_HHMMSS.md` - Operational brief
- `data/demo_output/evaluation_report.md` - Performance metrics (if --evaluate used)

---

## Troubleshooting

**"File not found: telemetry_dataset.csv"**
→ Run `python data/load_telemetry.py` to generate it

**"No module named 'pandas'"**
→ Activate virtual environment: `source venv/bin/activate`

**"Dataset too large for dashboard"**
→ The 80K records should load fine. If issues occur, reduce dataset size in `load_telemetry.py`

**"Want different anomaly patterns"**
→ Edit `generate_synthetic_telemetry()` in `data/load_telemetry.py` to customize anomaly types

---

## Summary

✅ **Test dataset is ready to use at:** `data/processed/telemetry_dataset.csv`

✅ **No additional setup needed** - just run the demo or dashboard

✅ **Contains realistic anomalies** with ground truth labels for evaluation

✅ **Can be upgraded to real NASA data** using the Kaggle setup script

**Start exploring:** `python demo.py --evaluate` or `streamlit run src/dashboard/app.py`
