#!/bin/bash
#
# Full Training Pipeline (Background Execution)
# Runs all steps automatically and organizes results by timestamp
#
# Usage:
#   ./scripts/run_full_training.sh [model]
#
# Example:
#   ./scripts/run_full_training.sh qwen2.5:3b
#   ./scripts/run_full_training.sh qwen2.5:72b

set -e  # Exit on error

# Configuration
MODEL="${1:-qwen2.5:3b}"  # Default to 3b for quick testing
BASE_DIR="/home/koshikawa/toExecUnit"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_DIR="$BASE_DIR/results/$TIMESTAMP"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="$BASE_DIR/logs/full_training_$TIMESTAMP.log"
mkdir -p "$BASE_DIR/logs"

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

# Create result directory structure
create_result_structure() {
    log "Creating result directory: $RESULT_DIR"
    mkdir -p "$RESULT_DIR/copy_robot"
    mkdir -p "$RESULT_DIR/snapshots"
    mkdir -p "$RESULT_DIR/logs"
    mkdir -p "$RESULT_DIR/report"
    info "Result directory created"
}

# Step 1: Create copy robot
step1_create_copy_robot() {
    log "=== Step 1/5: Creating Copy Robot ==="

    cd "$BASE_DIR"
    python3 scripts/create_copy_robot.py > "$RESULT_DIR/logs/step1_create_copy_robot.log" 2>&1

    # Find the created copy robot
    COPY_ROBOT_DB=$(ls -t copy_robots/COPY_ROBOT_*.db | head -1 | xargs basename)

    if [ -z "$COPY_ROBOT_DB" ]; then
        error "Failed to create copy robot"
    fi

    # Move to result directory
    mv "copy_robots/$COPY_ROBOT_DB" "$RESULT_DIR/copy_robot/"

    log "Copy robot created: $COPY_ROBOT_DB"
    echo "$COPY_ROBOT_DB" > "$RESULT_DIR/copy_robot_name.txt"
}

# Step 2: Before snapshot
step2_before_snapshot() {
    log "=== Step 2/5: Creating Before-Education Snapshot ==="

    cd "$BASE_DIR"
    COPY_ROBOT_DB=$(cat "$RESULT_DIR/copy_robot_name.txt")

    # Create symlink for script to access
    ln -sf "$RESULT_DIR/copy_robot/$COPY_ROBOT_DB" "copy_robots/$COPY_ROBOT_DB"

    python3 scripts/snapshot_before_education.py --db "$COPY_ROBOT_DB" > "$RESULT_DIR/logs/step2_before_snapshot.log" 2>&1

    # Find the created snapshot
    BEFORE_SNAPSHOT=$(ls -t snapshots/before_*.json | head -1 | xargs basename | sed 's/before_//' | sed 's/.json//')

    if [ -z "$BEFORE_SNAPSHOT" ]; then
        error "Failed to create before snapshot"
    fi

    # Move to result directory
    mv "snapshots/before_$BEFORE_SNAPSHOT.json" "$RESULT_DIR/snapshots/"

    log "Before snapshot created: $BEFORE_SNAPSHOT"
    echo "$BEFORE_SNAPSHOT" > "$RESULT_DIR/before_snapshot_ts.txt"
}

# Step 3: Training (main step)
step3_training() {
    log "=== Step 3/5: Training with $MODEL ==="
    log "This may take 10-20 minutes for qwen2.5:3b or 2-4 hours for qwen2.5:72b"

    cd "$BASE_DIR"
    COPY_ROBOT_DB=$(cat "$RESULT_DIR/copy_robot_name.txt")
    BEFORE_SNAPSHOT=$(cat "$RESULT_DIR/before_snapshot_ts.txt")

    START_TIME=$(date +%s)

    python3 scripts/train_sensitive_judgment.py \
        --db "$COPY_ROBOT_DB" \
        --before-snapshot "$BEFORE_SNAPSHOT" \
        --model "$MODEL" > "$RESULT_DIR/logs/step3_training.log" 2>&1

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Find training timestamp
    TRAINING_TS=$(ls -t logs/training_summary_*.json | head -1 | xargs basename | sed 's/training_summary_//' | sed 's/.json//')

    if [ -z "$TRAINING_TS" ]; then
        error "Failed to complete training"
    fi

    # Move logs to result directory
    mv "logs/training_log_$TRAINING_TS.txt" "$RESULT_DIR/logs/"
    mv "logs/training_summary_$TRAINING_TS.json" "$RESULT_DIR/logs/"

    log "Training completed in $DURATION seconds ($((DURATION/60)) minutes)"
    echo "$TRAINING_TS" > "$RESULT_DIR/training_ts.txt"
}

# Step 4: After snapshot
step4_after_snapshot() {
    log "=== Step 4/5: Creating After-Education Snapshot ==="

    cd "$BASE_DIR"
    COPY_ROBOT_DB=$(cat "$RESULT_DIR/copy_robot_name.txt")
    TRAINING_TS=$(cat "$RESULT_DIR/training_ts.txt")

    python3 scripts/snapshot_after_education.py \
        --db "$COPY_ROBOT_DB" \
        --training "$TRAINING_TS" > "$RESULT_DIR/logs/step4_after_snapshot.log" 2>&1

    # Find the created snapshot
    AFTER_SNAPSHOT=$(ls -t snapshots/after_*.json | head -1 | xargs basename | sed 's/after_//' | sed 's/.json//')

    if [ -z "$AFTER_SNAPSHOT" ]; then
        error "Failed to create after snapshot"
    fi

    # Move to result directory
    mv "snapshots/after_$AFTER_SNAPSHOT.json" "$RESULT_DIR/snapshots/"

    log "After snapshot created: $AFTER_SNAPSHOT"
    echo "$AFTER_SNAPSHOT" > "$RESULT_DIR/after_snapshot_ts.txt"
}

# Step 5: Comparison report
step5_comparison_report() {
    log "=== Step 5/5: Creating Comparison Report ==="

    cd "$BASE_DIR"
    AFTER_SNAPSHOT=$(cat "$RESULT_DIR/after_snapshot_ts.txt")

    python3 scripts/compare_education_results.py \
        --after "$AFTER_SNAPSHOT" > "$RESULT_DIR/logs/step5_comparison.log" 2>&1

    # Move report to result directory
    mv "reports/education_report_$AFTER_SNAPSHOT.md" "$RESULT_DIR/report/"

    log "Comparison report created"
}

# Cleanup symlinks
cleanup() {
    log "Cleaning up temporary symlinks..."
    COPY_ROBOT_DB=$(cat "$RESULT_DIR/copy_robot_name.txt" 2>/dev/null || echo "")
    if [ -n "$COPY_ROBOT_DB" ] && [ -L "copy_robots/$COPY_ROBOT_DB" ]; then
        rm "copy_robots/$COPY_ROBOT_DB"
    fi
}

# Main execution
main() {
    echo ""
    echo "============================================================"
    echo "  Full Training Pipeline (Background Execution)"
    echo "============================================================"
    echo "Model: $MODEL"
    echo "Result Directory: $RESULT_DIR"
    echo "Log File: $LOG_FILE"
    echo "============================================================"
    echo ""

    log "Starting full training pipeline"
    log "Model: $MODEL"

    # Create result structure
    create_result_structure

    # Execute all steps
    step1_create_copy_robot
    step2_before_snapshot
    step3_training
    step4_after_snapshot
    step5_comparison_report

    # Cleanup
    cleanup

    # Final summary
    echo ""
    echo "============================================================"
    log "All steps completed successfully!"
    echo "============================================================"
    echo ""
    echo "Results saved to: $RESULT_DIR"
    echo ""
    echo "Files created:"
    echo "  - Copy Robot: $RESULT_DIR/copy_robot/"
    echo "  - Snapshots: $RESULT_DIR/snapshots/"
    echo "  - Logs: $RESULT_DIR/logs/"
    echo "  - Report: $RESULT_DIR/report/"
    echo ""
    echo "View report:"
    echo "  cat $RESULT_DIR/report/education_report_*.md"
    echo ""
    echo "============================================================"
}

# Run main function
main

exit 0
