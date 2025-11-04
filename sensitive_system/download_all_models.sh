#!/bin/bash
# ============================================================================
# Ollama Model Batch Downloader for Copy Robot Testing
# Created: 2025-10-27
# Purpose: Download all Japanese/English compatible models for testing
# ============================================================================

# Note: Do not use 'set -e' because check_installed returns 1 for not-installed models

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="/home/koshikawa/toExecUnit/logs/model_download_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "========================================" | tee -a "$LOG_FILE"
echo "Ollama Model Batch Downloader" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo ""
echo -e "${YELLOW}This script will download ALL available models${NC}" | tee -a "$LOG_FILE"
echo -e "${YELLOW}including ultra-heavy models (405B parameters)${NC}" | tee -a "$LOG_FILE"
echo ""

# Disk space check
AVAILABLE_SPACE=$(df -BG /home/koshikawa | awk 'NR==2 {print $4}' | sed 's/G//')
REQUIRED_SPACE=1000  # Estimated 1TB for all models

echo -e "${CYAN}Disk space check:${NC}" | tee -a "$LOG_FILE"
echo "  Available: ${AVAILABLE_SPACE}GB" | tee -a "$LOG_FILE"
echo "  Estimated requirement: ${REQUIRED_SPACE}GB" | tee -a "$LOG_FILE"

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    echo -e "${YELLOW}⚠ Warning: Disk space may be insufficient${NC}" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}  Some large models may fail to download${NC}" | tee -a "$LOG_FILE"
else
    echo -e "${GREEN}✓ Sufficient disk space available${NC}" | tee -a "$LOG_FILE"
fi
echo ""

# Function to check if model is already installed
check_installed() {
    local model=$1
    if ollama list | grep -q "^${model}"; then
        return 0  # Already installed
    else
        return 1  # Not installed
    fi
}

# Function to download model with progress
download_model() {
    local model=$1
    local phase=$2

    echo -e "${BLUE}⬇ Downloading $model...${NC}"
    echo "[$(date)] Downloading $model..." >> "$LOG_FILE"

    if ollama pull "$model"; then
        echo -e "${GREEN}✓ Successfully downloaded: $model${NC}"
        echo "[$(date)] Successfully downloaded: $model" >> "$LOG_FILE"
        echo ""
        return 0
    else
        echo -e "${RED}✗ Failed to download: $model${NC}"
        echo "[$(date)] Failed to download: $model" >> "$LOG_FILE"
        echo ""
        return 1
    fi
}

# Phase 1: Lightweight Models (VRAM < 4GB)
echo -e "${CYAN}=====================================${NC}"
echo -e "${CYAN}Phase 1: Lightweight Models (<4GB)${NC}"
echo -e "${CYAN}=====================================${NC}"
echo ""

PHASE1_MODELS=(
    "qwen2.5:0.5b"
    "qwen2.5:1.5b"
    "qwen2.5:3b"
    "llama3.2:1b"
    "llama3.2:3b"
    "gemma2:2b"
    "schroneko/gemma-2-2b-jpn-it"
    "phi3:mini"
    "deepseek-r1:1.5b"
)

PHASE1_SUCCESS=0
PHASE1_FAILED=0
PHASE1_SKIPPED=0

for i in "${!PHASE1_MODELS[@]}"; do
    model="${PHASE1_MODELS[$i]}"
    model_num=$((i + 1))
    total_models=${#PHASE1_MODELS[@]}

    echo -e "${CYAN}[Phase 1: $model_num/$total_models]${NC} Checking: ${YELLOW}$model${NC}" | tee -a "$LOG_FILE"

    if check_installed "$model"; then
        ((PHASE1_SKIPPED++))
        echo -e "${GREEN}✓ Already installed, skipping${NC}" | tee -a "$LOG_FILE"
        echo ""
    else
        if download_model "$model" "1"; then
            ((PHASE1_SUCCESS++))
        else
            ((PHASE1_FAILED++))
        fi
    fi
done

echo -e "${CYAN}Phase 1 Summary: ${GREEN}$PHASE1_SUCCESS downloaded${NC}, ${YELLOW}$PHASE1_SKIPPED skipped${NC}, ${RED}$PHASE1_FAILED failed${NC}"
echo ""

# Phase 2: Medium Models (VRAM 6-10GB)
echo -e "${CYAN}=====================================${NC}"
echo -e "${CYAN}Phase 2: Medium Models (6-10GB)${NC}"
echo -e "${CYAN}=====================================${NC}"
echo ""

PHASE2_MODELS=(
    "qwen2.5:7b"
    "qwen2.5:14b"
    "llama3.1:8b"
    "llama3:8b"
    "elyza:jp8b"
    "microai/suzume-llama3"
    "dsasai/llama3-elyza-jp-8b"
    "gemma2:9b"
    "mistral:7b"
    "mistral-nemo"
    "phi3:medium"
    "deepseek-r1:7b"
    "deepseek-r1:8b"
    "deepseek-r1:14b"
    "qwen2.5-coder:7b"
)

PHASE2_SUCCESS=0
PHASE2_FAILED=0
PHASE2_SKIPPED=0

for i in "${!PHASE2_MODELS[@]}"; do
    model="${PHASE2_MODELS[$i]}"
    model_num=$((i + 1))
    total_models=${#PHASE2_MODELS[@]}

    echo -e "${CYAN}[Phase 2: $model_num/$total_models]${NC} Checking: ${YELLOW}$model${NC}" | tee -a "$LOG_FILE"

    if check_installed "$model"; then
        ((PHASE2_SKIPPED++))
        echo -e "${GREEN}✓ Already installed, skipping${NC}" | tee -a "$LOG_FILE"
        echo ""
    else
        if download_model "$model" "2"; then
            ((PHASE2_SUCCESS++))
        else
            ((PHASE2_FAILED++))
        fi
    fi
done

echo -e "${CYAN}Phase 2 Summary: ${GREEN}$PHASE2_SUCCESS downloaded${NC}, ${YELLOW}$PHASE2_SKIPPED skipped${NC}, ${RED}$PHASE2_FAILED failed${NC}"
echo ""

# Phase 3: Heavy Models (VRAM 16GB+)
echo -e "${CYAN}=====================================${NC}"
echo -e "${CYAN}Phase 3: Heavy Models (16GB+)${NC}"
echo -e "${CYAN}=====================================${NC}"
echo ""

PHASE3_MODELS=(
    "qwen2.5:32b"
    "qwen2.5:72b"
    "llama3.1:70b"
    "llama3:70b"
    "gemma2:27b"
    "mistral-large"
    "command-r:35b"
    "command-r-plus"
    "deepseek-r1:32b"
    "deepseek-r1:70b"
    "qwen2.5-coder:32b"
)

PHASE3_SUCCESS=0
PHASE3_FAILED=0
PHASE3_SKIPPED=0

for i in "${!PHASE3_MODELS[@]}"; do
    model="${PHASE3_MODELS[$i]}"
    model_num=$((i + 1))
    total_models=${#PHASE3_MODELS[@]}

    echo -e "${CYAN}[Phase 3: $model_num/$total_models]${NC} Checking: ${YELLOW}$model${NC}" | tee -a "$LOG_FILE"

    if check_installed "$model"; then
        ((PHASE3_SKIPPED++))
        echo -e "${GREEN}✓ Already installed, skipping${NC}" | tee -a "$LOG_FILE"
        echo ""
    else
        if download_model "$model" "3"; then
            ((PHASE3_SUCCESS++))
        else
            ((PHASE3_FAILED++))
        fi
    fi
done

echo -e "${CYAN}Phase 3 Summary: ${GREEN}$PHASE3_SUCCESS downloaded${NC}, ${YELLOW}$PHASE3_SKIPPED skipped${NC}, ${RED}$PHASE3_FAILED failed${NC}"
echo ""

# Phase 4: Ultra-Heavy Models (VRAM 32GB+, Experimental)
echo -e "${CYAN}=====================================${NC}"
echo -e "${CYAN}Phase 4: Ultra-Heavy Models (32GB+)${NC}"
echo -e "${CYAN}=====================================${NC}"
echo ""

PHASE4_MODELS=(
    "llama3.1:405b"
    "phi3:large"
)

PHASE4_SUCCESS=0
PHASE4_FAILED=0
PHASE4_SKIPPED=0

for i in "${!PHASE4_MODELS[@]}"; do
    model="${PHASE4_MODELS[$i]}"
    model_num=$((i + 1))
    total_models=${#PHASE4_MODELS[@]}

    echo -e "${CYAN}[Phase 4: $model_num/$total_models]${NC} Checking: ${YELLOW}$model${NC}" | tee -a "$LOG_FILE"

    if check_installed "$model"; then
        ((PHASE4_SKIPPED++))
        echo -e "${GREEN}✓ Already installed, skipping${NC}" | tee -a "$LOG_FILE"
        echo ""
    else
        if download_model "$model" "4"; then
            ((PHASE4_SUCCESS++))
        else
            ((PHASE4_FAILED++))
        fi
    fi
done

echo -e "${CYAN}Phase 4 Summary: ${GREEN}$PHASE4_SUCCESS downloaded${NC}, ${YELLOW}$PHASE4_SKIPPED skipped${NC}, ${RED}$PHASE4_FAILED failed${NC}"
echo ""

# Final Summary
echo ""
echo "========================================" | tee -a "$LOG_FILE"
echo "Download Complete!" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo ""
echo -e "${CYAN}Phase 1 (Lightweight):${NC} ${GREEN}$PHASE1_SUCCESS downloaded${NC}, ${YELLOW}$PHASE1_SKIPPED skipped${NC}, ${RED}$PHASE1_FAILED failed${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}Phase 2 (Medium):${NC} ${GREEN}$PHASE2_SUCCESS downloaded${NC}, ${YELLOW}$PHASE2_SKIPPED skipped${NC}, ${RED}$PHASE2_FAILED failed${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}Phase 3 (Heavy):${NC} ${GREEN}$PHASE3_SUCCESS downloaded${NC}, ${YELLOW}$PHASE3_SKIPPED skipped${NC}, ${RED}$PHASE3_FAILED failed${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}Phase 4 (Ultra-Heavy):${NC} ${GREEN}$PHASE4_SUCCESS downloaded${NC}, ${YELLOW}$PHASE4_SKIPPED skipped${NC}, ${RED}$PHASE4_FAILED failed${NC}" | tee -a "$LOG_FILE"
echo ""

TOTAL_SUCCESS=$((PHASE1_SUCCESS + PHASE2_SUCCESS + PHASE3_SUCCESS + PHASE4_SUCCESS))
TOTAL_FAILED=$((PHASE1_FAILED + PHASE2_FAILED + PHASE3_FAILED + PHASE4_FAILED))
TOTAL_SKIPPED=$((PHASE1_SKIPPED + PHASE2_SKIPPED + PHASE3_SKIPPED + PHASE4_SKIPPED))

echo -e "${GREEN}Total Downloaded: $TOTAL_SUCCESS${NC}" | tee -a "$LOG_FILE"
echo -e "${YELLOW}Total Skipped: $TOTAL_SKIPPED${NC}" | tee -a "$LOG_FILE"
echo -e "${RED}Total Failed: $TOTAL_FAILED${NC}" | tee -a "$LOG_FILE"
echo ""
echo "Finished: $(date)" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo ""

# List all installed models
echo "========================================" | tee -a "$LOG_FILE"
echo "Currently Installed Models:" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
ollama list | tee -a "$LOG_FILE"
