# Mission Watch - Setup Instructions

This guide will help you set up the complete Mission Watch system with real NASA data and IBM watsonx integration.

## Quick Start

We've created automated setup scripts to make this process easier. Follow the steps below:

---

## Part 1: Kaggle Dataset Setup (Real NASA SMAP/MSL Data)

### Prerequisites
1. A Kaggle account (free): https://www.kaggle.com
2. Python 3.11+ installed
3. Internet connection for downloading ~500MB dataset

### Step-by-Step Instructions

#### 1. Get Kaggle API Credentials

1. Go to https://www.kaggle.com and sign in (create account if needed)
2. Click on your profile picture → **Account**
3. Scroll to **API** section → Click **"Create New API Token"**
4. This downloads a `kaggle.json` file to your Downloads folder

#### 2. Install Kaggle Credentials

**macOS/Linux:**
```bash
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

**Windows:**
```powershell
mkdir $env:USERPROFILE\.kaggle
move $env:USERPROFILE\Downloads\kaggle.json $env:USERPROFILE\.kaggle\
```

#### 3. Run Automated Setup Script

**macOS/Linux:**
```bash
cd /Users/balajmubeen/Desktop/Open_Sourse/IBM_Project/OrbitGuard
./setup_kaggle_data.sh
```

**Windows:**
```powershell
cd C:\path\to\OrbitGuard
python data/load_telemetry.py
```

The script will:
- ✅ Verify Kaggle credentials
- ✅ Install kaggle package
- ✅ Download NASA SMAP/MSL dataset (~500MB)
- ✅ Extract and process telemetry data
- ✅ Generate `data/processed/telemetry_dataset.csv`

#### 4. Verify Setup

Check that the dataset was created:
```bash
ls -lh data/processed/telemetry_dataset.csv
cat data/processed/dataset_summary.json
```

---

## Part 2: IBM watsonx Setup (AI-Powered Operational Briefs)

### Prerequisites
1. IBM Cloud account (free tier available): https://cloud.ibm.com
2. watsonx.ai project created

### Step-by-Step Instructions

#### 1. Get IBM Cloud API Key

1. Go to https://cloud.ibm.com
2. Click **Manage** → **Access (IAM)** → **API keys**
3. Click **Create an IBM Cloud API key**
4. Give it a name (e.g., "Mission Watch")
5. Click **Create** and **Download** the key

#### 2. Get watsonx Project ID

1. Go to https://dataplatform.cloud.ibm.com/wx/home
2. Click on your project (or create a new one)
3. Click **Manage** tab → **General**
4. Copy the **Project ID**

#### 3. Create .env File

Create a `.env` file in the OrbitGuard directory:

```bash
cd /Users/balajmubeen/Desktop/Open_Sourse/IBM_Project/OrbitGuard
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
# IBM watsonx API credentials
IBM_CLOUD_API_KEY=your_actual_api_key_here
WATSONX_ENDPOINT=https://us-south.ml.cloud.ibm.com
WATSONX_PROJECT_ID=your_actual_project_id_here

# Optional: Additional configuration
LOG_LEVEL=INFO
```

**Important:** Never commit `.env` to git! It's already in `.gitignore`.

#### 4. Test watsonx Connection

Run this test script to verify your credentials work:

```bash
python -c "
from src.agents.advisor.watsonx_client import WatsonxClient
from src.utils.config_loader import load_config
import os
from dotenv import load_dotenv

load_dotenv()
config = load_config()

client = WatsonxClient(
    api_key=os.getenv('IBM_CLOUD_API_KEY'),
    project_id=os.getenv('WATSONX_PROJECT_ID'),
    endpoint=os.getenv('WATSONX_ENDPOINT')
)

# Test with a simple prompt
response = client.generate_text('Say hello')
print('✅ watsonx connection successful!')
print(f'Response: {response[:100]}...')
"
```

---

## Part 3: Run the Complete System

### Option 1: Demo Script (Command Line)

Run the complete pipeline with real data:

```bash
python demo.py --evaluate
```

This will:
1. Load real NASA telemetry from `data/processed/telemetry_dataset.csv`
2. Detect anomalies using Isolation Forest
3. Generate operational briefs using IBM Granite LLM
4. Evaluate performance against ground truth
5. Save results to `data/demo_output/`

### Option 2: Streamlit Dashboard (Interactive)

Launch the interactive web dashboard:

```bash
streamlit run src/dashboard/app.py
```

Then open your browser to http://localhost:8501

---

## Troubleshooting

### Kaggle Issues

**Problem:** `kaggle: command not found`
```bash
pip install kaggle
```

**Problem:** `401 Unauthorized`
- Check that `~/.kaggle/kaggle.json` exists and has correct permissions (600)
- Verify your Kaggle API credentials are valid

**Problem:** Dataset download fails
- Check your internet connection
- Try downloading manually from: https://www.kaggle.com/datasets/patrickfleith/nasa-anomaly-detection-dataset-smap-msl

### watsonx Issues

**Problem:** `Invalid API key`
- Verify your IBM Cloud API key is correct in `.env`
- Make sure the key has access to watsonx.ai

**Problem:** `Project not found`
- Verify your watsonx project ID is correct
- Make sure the project exists in your IBM Cloud account

**Problem:** Mock mode fallback
- Check that `.env` file exists and is loaded
- Verify all three credentials are set: API_KEY, PROJECT_ID, ENDPOINT

### Data Issues

**Problem:** `telemetry_dataset.csv not found`
- Run `./setup_kaggle_data.sh` to download and process data
- Or run `python data/load_telemetry.py` to generate synthetic data

**Problem:** Import errors
- Make sure you're in the project root directory
- Activate your virtual environment if using one
- Install requirements: `pip install -r requirements.txt`

---

## Alternative: Use Synthetic Data

If you can't access Kaggle or want to test quickly, generate synthetic data:

```bash
python data/load_telemetry.py
```

This creates realistic synthetic NASA-like telemetry with labeled anomalies for testing.

---

## Verification Checklist

Before running the full system, verify:

- [ ] Kaggle credentials set up (`~/.kaggle/kaggle.json` exists)
- [ ] Dataset downloaded and processed (`data/processed/telemetry_dataset.csv` exists)
- [ ] IBM watsonx credentials in `.env` file
- [ ] watsonx connection test passes
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Can run demo script without errors

---

## Next Steps

Once setup is complete:

1. **Explore the data:**
   ```bash
   python -c "import pandas as pd; df = pd.read_csv('data/processed/telemetry_dataset.csv'); print(df.info()); print(df.head())"
   ```

2. **Run anomaly detection:**
   ```bash
   python demo.py --model-type isolation_forest --threshold 0.7
   ```

3. **Launch dashboard:**
   ```bash
   streamlit run src/dashboard/app.py
   ```

4. **Review results:**
   - Check `data/demo_output/` for anomaly reports
   - Read operational briefs generated by Granite LLM
   - Review evaluation metrics if ground truth available

---

## Support

For issues or questions:
- Check the troubleshooting section above
- Review `AGENTS.md` for architecture details
- Check `PROJECT_STRUCTURE.md` for code organization
- Review logs in `logs/` directory

---

**Happy anomaly hunting! 🛰️**
