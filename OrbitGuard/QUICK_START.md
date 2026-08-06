# Mission Watch - Quick Start Guide

## What Was Fixed

✅ **1. demo.py Data Path**
- Changed default `--data-path` from `synthetic_telemetry.csv` to `telemetry_dataset.csv`
- Now matches the actual generated file name

✅ **2. detector.py Evaluation Fix**
- Modified `run_detection_pipeline()` to return full ranked predictions as `all_predictions`
- Previously returned only filtered anomalies, breaking precision/recall calculations
- Now `evaluate_predictions()` can compute real metrics against complete ground truth

✅ **3. Setup Automation Created**
- `setup_kaggle_data.sh` - Automated Kaggle dataset download and processing
- `test_watsonx_advisor.py` - Test script for IBM watsonx credentials
- `SETUP_INSTRUCTIONS.md` - Comprehensive setup documentation

---

## Quick Setup (5 Minutes)

### Step 1: Get Kaggle Credentials (2 min)
1. Go to https://www.kaggle.com → Account → API → Create New Token
2. Move `kaggle.json` to `~/.kaggle/` and set permissions:
   ```bash
   mkdir -p ~/.kaggle
   mv ~/Downloads/kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   ```

### Step 2: Download NASA Data (3 min)
```bash
cd /Users/balajmubeen/Desktop/Open_Sourse/IBM_Project/OrbitGuard
./setup_kaggle_data.sh
```

### Step 3: Setup IBM watsonx (Optional)
1. Get IBM Cloud API key: https://cloud.ibm.com → Manage → Access (IAM) → API keys
2. Get watsonx Project ID: https://dataplatform.cloud.ibm.com/wx/home → Your Project → Manage → General
3. Create `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and add your credentials
   ```
4. Test connection:
   ```bash
   python test_watsonx_advisor.py
   ```

---

## Run the System

### Option 1: Demo Script
```bash
python demo.py --evaluate
```

### Option 2: Interactive Dashboard
```bash
streamlit run src/dashboard/app.py
```

---

## What You Get

**With Real NASA Data:**
- ✅ Actual SMAP/MSL spacecraft telemetry
- ✅ Real anomaly labels for evaluation
- ✅ Accurate precision/recall metrics
- ✅ 10+ channels across multiple subsystems

**With IBM watsonx:**
- ✅ AI-generated operational briefs using Granite LLM
- ✅ Plain-language anomaly explanations
- ✅ Actionable recommendations for operators

**Without watsonx (Mock Mode):**
- ⚠️ System still works with template-based briefs
- ⚠️ Less sophisticated but functional for demo

---

## Files Created/Modified

### Modified Files:
1. `demo.py` - Fixed default data path
2. `src/agents/signal_analyst/detector.py` - Fixed evaluation data return

### New Files:
1. `setup_kaggle_data.sh` - Automated Kaggle setup
2. `test_watsonx_advisor.py` - watsonx credential tester
3. `SETUP_INSTRUCTIONS.md` - Detailed setup guide
4. `QUICK_START.md` - This file

---

## Troubleshooting

**"kaggle.json not found"**
→ Follow Step 1 above to get Kaggle credentials

**"telemetry_dataset.csv not found"**
→ Run `./setup_kaggle_data.sh` or `python data/load_telemetry.py`

**"Invalid API key" (watsonx)**
→ Check `.env` file has correct IBM Cloud credentials

**"Mock mode fallback"**
→ watsonx credentials not set, system uses templates instead

---

## Next Steps

1. ✅ Run `./setup_kaggle_data.sh` to get real NASA data
2. ⚠️ (Optional) Setup `.env` with IBM watsonx credentials
3. ⚠️ (Optional) Run `python test_watsonx_advisor.py` to verify
4. ✅ Run `python demo.py --evaluate` to see the system in action
5. ✅ Launch `streamlit run src/dashboard/app.py` for interactive analysis

---

**Ready to detect anomalies! 🛰️**
