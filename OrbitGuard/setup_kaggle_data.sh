#!/bin/bash

# Mission Watch - Kaggle Dataset Setup Script
# This script automates the download and setup of NASA SMAP/MSL telemetry data

set -e  # Exit on error

echo "=========================================="
echo "🛰️  Mission Watch - Kaggle Data Setup"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}Project root: $PROJECT_ROOT${NC}"
echo ""

# Step 1: Check for Kaggle credentials
echo "=========================================="
echo "Step 1: Checking Kaggle API Credentials"
echo "=========================================="
echo ""

KAGGLE_CONFIG_DIR="$HOME/.kaggle"
KAGGLE_JSON="$KAGGLE_CONFIG_DIR/kaggle.json"

if [ ! -f "$KAGGLE_JSON" ]; then
    echo -e "${RED}❌ Kaggle credentials not found!${NC}"
    echo ""
    echo "Please follow these steps to get your Kaggle API credentials:"
    echo ""
    echo "1. Go to https://www.kaggle.com and sign in"
    echo "2. Click on your profile picture → Account"
    echo "3. Scroll to 'API' section → Click 'Create New API Token'"
    echo "4. This will download 'kaggle.json' to your Downloads folder"
    echo ""
    echo "5. Move the file to the correct location:"
    echo "   mkdir -p ~/.kaggle"
    echo "   mv ~/Downloads/kaggle.json ~/.kaggle/"
    echo "   chmod 600 ~/.kaggle/kaggle.json"
    echo ""
    echo "6. Run this script again after setting up credentials"
    echo ""
    exit 1
else
    echo -e "${GREEN}✅ Kaggle credentials found at: $KAGGLE_JSON${NC}"
    
    # Check permissions
    PERMS=$(stat -f "%A" "$KAGGLE_JSON" 2>/dev/null || stat -c "%a" "$KAGGLE_JSON" 2>/dev/null)
    if [ "$PERMS" != "600" ]; then
        echo -e "${YELLOW}⚠️  Fixing file permissions...${NC}"
        chmod 600 "$KAGGLE_JSON"
        echo -e "${GREEN}✅ Permissions set to 600${NC}"
    fi
fi
echo ""

# Step 2: Install Kaggle package
echo "=========================================="
echo "Step 2: Installing Kaggle Package"
echo "=========================================="
echo ""

if python3 -c "import kaggle" 2>/dev/null; then
    echo -e "${GREEN}✅ Kaggle package already installed${NC}"
else
    echo -e "${YELLOW}📦 Installing kaggle package...${NC}"
    pip install kaggle
    echo -e "${GREEN}✅ Kaggle package installed${NC}"
fi
echo ""

# Step 3: Create data directories
echo "=========================================="
echo "Step 3: Creating Data Directories"
echo "=========================================="
echo ""

mkdir -p data/raw/telemanom
mkdir -p data/processed
mkdir -p data/anomalies

echo -e "${GREEN}✅ Data directories created${NC}"
echo ""

# Step 4: Download dataset from Kaggle
echo "=========================================="
echo "Step 4: Downloading NASA SMAP/MSL Dataset"
echo "=========================================="
echo ""

DATASET_ZIP="nasa-anomaly-detection-dataset-smap-msl.zip"

if [ -f "$DATASET_ZIP" ]; then
    echo -e "${YELLOW}⚠️  Dataset zip already exists, skipping download${NC}"
else
    echo -e "${BLUE}📥 Downloading dataset from Kaggle...${NC}"
    echo "   This may take a few minutes depending on your connection"
    echo ""
    
    kaggle datasets download -d patrickfleith/nasa-anomaly-detection-dataset-smap-msl
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Dataset downloaded successfully${NC}"
    else
        echo -e "${RED}❌ Failed to download dataset${NC}"
        echo "   Please check your Kaggle credentials and internet connection"
        exit 1
    fi
fi
echo ""

# Step 5: Unzip dataset
echo "=========================================="
echo "Step 5: Extracting Dataset"
echo "=========================================="
echo ""

if [ -d "data/raw/telemanom/train" ] && [ -d "data/raw/telemanom/test" ]; then
    echo -e "${YELLOW}⚠️  Dataset already extracted, skipping${NC}"
else
    echo -e "${BLUE}📂 Extracting dataset...${NC}"
    
    unzip -q "$DATASET_ZIP" -d data/raw/telemanom
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Dataset extracted successfully${NC}"
    else
        echo -e "${RED}❌ Failed to extract dataset${NC}"
        exit 1
    fi
fi
echo ""

# Step 6: Process dataset
echo "=========================================="
echo "Step 6: Processing Telemetry Data"
echo "=========================================="
echo ""

echo -e "${BLUE}🔄 Running data loader to process telemetry...${NC}"
echo ""

python3 data/load_telemetry.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Data processing complete${NC}"
else
    echo ""
    echo -e "${RED}❌ Data processing failed${NC}"
    exit 1
fi
echo ""

# Step 7: Verify output
echo "=========================================="
echo "Step 7: Verifying Output"
echo "=========================================="
echo ""

TELEMETRY_FILE="data/processed/telemetry_dataset.csv"
SUMMARY_FILE="data/processed/dataset_summary.json"

if [ -f "$TELEMETRY_FILE" ]; then
    FILE_SIZE=$(du -h "$TELEMETRY_FILE" | cut -f1)
    LINE_COUNT=$(wc -l < "$TELEMETRY_FILE")
    echo -e "${GREEN}✅ Telemetry dataset created${NC}"
    echo "   File: $TELEMETRY_FILE"
    echo "   Size: $FILE_SIZE"
    echo "   Lines: $LINE_COUNT"
else
    echo -e "${RED}❌ Telemetry dataset not found${NC}"
    exit 1
fi
echo ""

if [ -f "$SUMMARY_FILE" ]; then
    echo -e "${GREEN}✅ Dataset summary created${NC}"
    echo "   File: $SUMMARY_FILE"
else
    echo -e "${YELLOW}⚠️  Dataset summary not found${NC}"
fi
echo ""

# Cleanup
echo "=========================================="
echo "Step 8: Cleanup"
echo "=========================================="
echo ""

if [ -f "$DATASET_ZIP" ]; then
    echo -e "${BLUE}🗑️  Removing downloaded zip file...${NC}"
    rm "$DATASET_ZIP"
    echo -e "${GREEN}✅ Cleanup complete${NC}"
fi
echo ""

# Final summary
echo "=========================================="
echo "✅ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Your NASA SMAP/MSL telemetry dataset is ready to use!"
echo ""
echo "Next steps:"
echo "  1. Run the demo script:"
echo "     python demo.py"
echo ""
echo "  2. Or launch the Streamlit dashboard:"
echo "     streamlit run src/dashboard/app.py"
echo ""
echo "  3. Check the processed data:"
echo "     cat data/processed/dataset_summary.json"
echo ""
echo "=========================================="
