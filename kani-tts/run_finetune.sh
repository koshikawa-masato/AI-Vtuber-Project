#!/bin/bash
#
# KaniTTS Fine-tuning Background Execution Script
# Usage: ./run_finetune.sh [options]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
LOG_DIR="${SCRIPT_DIR}/logs"
PID_FILE="${SCRIPT_DIR}/finetune.pid"
LOG_FILE="${LOG_DIR}/finetune_$(date +%Y%m%d_%H%M%S).log"

# Default values
CONFIG_FILE="${SCRIPT_DIR}/train_config.yaml"
PREPARE_DATA=false
RESUME=false
BACKGROUND=false

# Create log directory
mkdir -p "${LOG_DIR}"

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if training is running
is_training_running() {
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if ps -p ${PID} > /dev/null 2>&1; then
            return 0
        else
            rm -f "${PID_FILE}"
            return 1
        fi
    fi
    return 1
}

# Function to show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -c, --config FILE       Configuration file (default: train_config.yaml)
    -p, --prepare-data      Prepare data manifest before training
    -a, --audio-dir DIR     Audio directory (with --prepare-data)
    -t, --text-file FILE    Text file (with --prepare-data)
    -r, --resume            Resume from last checkpoint
    -b, --background        Run in background
    -s, --status            Check training status
    -k, --kill              Kill running training
    -l, --logs              Show recent logs
    -h, --help              Show this help

Examples:
    # Prepare data
    $0 --prepare-data --audio-dir ./audio --text-file ./text.txt

    # Start training in background
    $0 --background

    # Resume training in background
    $0 --resume --background

    # Check status
    $0 --status

    # View logs
    $0 --logs

    # Kill training
    $0 --kill

EOF
    exit 1
}

# Parse arguments
AUDIO_DIR=""
TEXT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -p|--prepare-data)
            PREPARE_DATA=true
            shift
            ;;
        -a|--audio-dir)
            AUDIO_DIR="$2"
            shift 2
            ;;
        -t|--text-file)
            TEXT_FILE="$2"
            shift 2
            ;;
        -r|--resume)
            RESUME=true
            shift
            ;;
        -b|--background)
            BACKGROUND=true
            shift
            ;;
        -s|--status)
            if is_training_running; then
                PID=$(cat "${PID_FILE}")
                print_info "Training is running (PID: ${PID})"
                print_info "Log file: $(ls -t ${LOG_DIR}/finetune_*.log | head -1)"
                exit 0
            else
                print_info "No training process running"
                exit 0
            fi
            ;;
        -k|--kill)
            if is_training_running; then
                PID=$(cat "${PID_FILE}")
                print_warn "Killing training process (PID: ${PID})..."
                kill ${PID}
                rm -f "${PID_FILE}"
                print_info "Training stopped"
            else
                print_info "No training process running"
            fi
            exit 0
            ;;
        -l|--logs)
            LATEST_LOG=$(ls -t ${LOG_DIR}/finetune_*.log 2>/dev/null | head -1)
            if [ -n "${LATEST_LOG}" ]; then
                print_info "Showing logs from: ${LATEST_LOG}"
                tail -f "${LATEST_LOG}"
            else
                print_error "No log files found"
                exit 1
            fi
            ;;
        -h|--help)
            usage
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Check if training is already running
if is_training_running && ! ${PREPARE_DATA}; then
    PID=$(cat "${PID_FILE}")
    print_error "Training is already running (PID: ${PID})"
    print_info "Use '$0 --status' to check status"
    print_info "Use '$0 --kill' to stop training"
    exit 1
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

# Check GPU
print_info "Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    print_warn "nvidia-smi not found. Training will use CPU (very slow)"
fi

# Build command
CMD="python finetune.py --config ${CONFIG_FILE}"

if ${PREPARE_DATA}; then
    if [ -z "${AUDIO_DIR}" ] || [ -z "${TEXT_FILE}" ]; then
        print_error "--audio-dir and --text-file required with --prepare-data"
        exit 1
    fi
    CMD="${CMD} --prepare-data --audio-dir ${AUDIO_DIR} --text-file ${TEXT_FILE}"
    print_info "Preparing data manifest..."
fi

if ${RESUME}; then
    CMD="${CMD} --resume"
    print_info "Resuming from checkpoint..."
fi

# Execute
if ${BACKGROUND}; then
    print_info "Starting training in background..."
    print_info "Log file: ${LOG_FILE}"
    print_info "PID file: ${PID_FILE}"

    nohup ${CMD} > "${LOG_FILE}" 2>&1 &
    PID=$!
    echo ${PID} > "${PID_FILE}"

    print_info "Training started (PID: ${PID})"
    print_info ""
    print_info "Commands:"
    print_info "  Check status: $0 --status"
    print_info "  View logs:    $0 --logs"
    print_info "  Stop:         $0 --kill"

    # Show initial logs
    sleep 2
    if [ -f "${LOG_FILE}" ]; then
        print_info ""
        print_info "Initial logs:"
        echo "----------------------------------------"
        head -20 "${LOG_FILE}"
        echo "----------------------------------------"
    fi
else
    print_info "Starting training in foreground..."
    ${CMD} 2>&1 | tee "${LOG_FILE}"
fi
