#!/bin/bash
# ============================================================================
# Ollama Model Updater for Copy Robot Testing
# Created: 2025-10-27
# Purpose: Check and update all installed models to latest versions
# ============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="/home/koshikawa/toExecUnit/logs/model_update_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "========================================" | tee -a "$LOG_FILE"
echo "Ollama Model Updater" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo ""

# Get list of installed models (exclude custom models)
echo -e "${CYAN}Checking installed models...${NC}" | tee -a "$LOG_FILE"
echo ""

# Custom model patterns to exclude (牡丹専用モデルは更新しない)
EXCLUDE_PATTERNS=(
    "elyza:botan_"
    "elyza:botan"
    ":custom"
    ":test"
)

# Get all models
ALL_MODELS=$(ollama list | tail -n +2 | awk '{print $1}')

# Filter out custom models
MODELS_TO_UPDATE=()
CUSTOM_MODELS=()

while IFS= read -r model; do
    is_custom=false

    # Check if model matches any exclude pattern
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        if [[ "$model" == *"$pattern"* ]]; then
            is_custom=true
            CUSTOM_MODELS+=("$model")
            break
        fi
    done

    if [ "$is_custom" = false ]; then
        MODELS_TO_UPDATE+=("$model")
    fi
done <<< "$ALL_MODELS"

# Display summary
echo -e "${GREEN}Models to update: ${#MODELS_TO_UPDATE[@]}${NC}" | tee -a "$LOG_FILE"
echo -e "${YELLOW}Custom models (skipped): ${#CUSTOM_MODELS[@]}${NC}" | tee -a "$LOG_FILE"
echo ""

# Show custom models being skipped
if [ ${#CUSTOM_MODELS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Skipping custom models:${NC}" | tee -a "$LOG_FILE"
    for model in "${CUSTOM_MODELS[@]}"; do
        echo "  - $model" | tee -a "$LOG_FILE"
    done
    echo ""
fi

# Show models to be updated
echo -e "${CYAN}Models to check for updates:${NC}" | tee -a "$LOG_FILE"
for model in "${MODELS_TO_UPDATE[@]}"; do
    echo "  - $model" | tee -a "$LOG_FILE"
done
echo ""

# Confirm before proceeding
read -p "Proceed with update check? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Update cancelled." | tee -a "$LOG_FILE"
    exit 0
fi

echo ""
echo "========================================" | tee -a "$LOG_FILE"
echo "Starting update process..." | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo ""

# Update counters
UPDATED_COUNT=0
ALREADY_UPDATED_COUNT=0
FAILED_COUNT=0

# Update each model
for i in "${!MODELS_TO_UPDATE[@]}"; do
    model="${MODELS_TO_UPDATE[$i]}"
    model_num=$((i + 1))
    total_models=${#MODELS_TO_UPDATE[@]}

    echo -e "${CYAN}[$model_num/$total_models]${NC} Checking: ${YELLOW}$model${NC}" | tee -a "$LOG_FILE"

    # Capture ollama pull output
    PULL_OUTPUT=$(ollama pull "$model" 2>&1)
    PULL_EXIT_CODE=$?

    if [ $PULL_EXIT_CODE -eq 0 ]; then
        # Check if model was updated or already up-to-date
        if echo "$PULL_OUTPUT" | grep -q "already up to date"; then
            echo -e "${GREEN}✓ Already up to date${NC}" | tee -a "$LOG_FILE"
            ((ALREADY_UPDATED_COUNT++))
        else
            echo -e "${GREEN}✓ Updated successfully${NC}" | tee -a "$LOG_FILE"
            ((UPDATED_COUNT++))
        fi
    else
        echo -e "${RED}✗ Update failed${NC}" | tee -a "$LOG_FILE"
        echo "$PULL_OUTPUT" >> "$LOG_FILE"
        ((FAILED_COUNT++))
    fi

    echo ""
done

# Final summary
echo ""
echo "========================================" | tee -a "$LOG_FILE"
echo "Update Complete!" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo ""
echo -e "${GREEN}Updated: $UPDATED_COUNT${NC}" | tee -a "$LOG_FILE"
echo -e "${YELLOW}Already up to date: $ALREADY_UPDATED_COUNT${NC}" | tee -a "$LOG_FILE"
echo -e "${RED}Failed: $FAILED_COUNT${NC}" | tee -a "$LOG_FILE"
echo -e "${CYAN}Custom models skipped: ${#CUSTOM_MODELS[@]}${NC}" | tee -a "$LOG_FILE"
echo ""
echo "Finished: $(date)" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo ""

# List all installed models with updated timestamps
echo "========================================" | tee -a "$LOG_FILE"
echo "Currently Installed Models:" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
ollama list | tee -a "$LOG_FILE"
