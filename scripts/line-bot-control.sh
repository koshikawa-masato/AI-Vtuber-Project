#!/bin/bash
# LINE Bot システム管理スクリプト
# Usage: ./scripts/line-bot-control.sh [start|stop|restart|status|logs]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# カラー出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

function print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

function print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

function start_services() {
    print_info "Starting LINE Bot services..."
    systemctl --user start ngrok.service
    sleep 2
    systemctl --user start line-bot.service
    print_info "Services started successfully!"
    status_services
}

function stop_services() {
    print_info "Stopping LINE Bot services..."
    systemctl --user stop line-bot.service
    systemctl --user stop ngrok.service
    print_info "Services stopped successfully!"
}

function restart_services() {
    print_info "Restarting LINE Bot services..."
    systemctl --user restart ngrok.service
    sleep 2
    systemctl --user restart line-bot.service
    print_info "Services restarted successfully!"
    status_services
}

function status_services() {
    echo ""
    print_info "=== ngrok Service Status ==="
    systemctl --user status ngrok.service --no-pager || true
    echo ""
    print_info "=== LINE Bot Service Status ==="
    systemctl --user status line-bot.service --no-pager || true
    echo ""
    print_info "=== Process Status ==="
    ps aux | grep -E "(ngrok|uvicorn)" | grep -v grep || echo "No processes found"
    echo ""
    print_info "=== API Health Check ==="
    curl -s http://localhost:8000/ | python3 -m json.tool || print_error "API is not responding"
}

function view_logs() {
    print_info "Viewing logs (Ctrl+C to exit)..."
    echo ""
    print_info "Press 'n' for ngrok logs, 'l' for LINE bot logs, or 'b' for both (default: both)"
    read -n 1 -r choice
    echo ""

    case $choice in
        n|N)
            journalctl --user -u ngrok.service -f
            ;;
        l|L)
            journalctl --user -u line-bot.service -f
            ;;
        *)
            journalctl --user -u ngrok.service -u line-bot.service -f
            ;;
    esac
}

function enable_services() {
    print_info "Enabling LINE Bot services for auto-start..."
    systemctl --user enable ngrok.service
    systemctl --user enable line-bot.service
    print_info "Services enabled successfully!"
    print_warn "Note: Services will auto-start when systemd user instance starts"
}

function disable_services() {
    print_info "Disabling LINE Bot services auto-start..."
    systemctl --user disable ngrok.service
    systemctl --user disable line-bot.service
    print_info "Services disabled successfully!"
}

# メイン処理
case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        status_services
        ;;
    logs)
        view_logs
        ;;
    enable)
        enable_services
        ;;
    disable)
        disable_services
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|enable|disable}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all LINE Bot services"
        echo "  stop     - Stop all LINE Bot services"
        echo "  restart  - Restart all LINE Bot services"
        echo "  status   - Show status of all services"
        echo "  logs     - View service logs (real-time)"
        echo "  enable   - Enable auto-start on boot"
        echo "  disable  - Disable auto-start on boot"
        exit 1
        ;;
esac
