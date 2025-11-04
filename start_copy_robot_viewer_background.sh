#!/bin/bash
# Copy Robot Database Viewer - Background Startup Script
# バックグラウンドで起動するスクリプト

echo "========================================================================"
echo "🤖 Copy Robot Database Viewer - Background Mode"
echo "========================================================================"
echo ""

# 既存のプロセスをチェック
if pgrep -f "copy_robot_viewer.py" > /dev/null; then
    echo "⚠️  WebUI is already running!"
    echo ""
    echo "To stop: pkill -f copy_robot_viewer.py"
    echo "To view logs: tail -f copy_robot_viewer.log"
    echo ""
    exit 1
fi

echo "Starting Web UI in background..."
echo "Database: sisters_memory_COPY_ROBOT_20251024_143000.db"
echo ""

# バックグラウンドで起動 (Simple版を使用)
nohup /home/koshikawa/toExecUnit/venv_webui/bin/python /home/koshikawa/toExecUnit/copy_robot_viewer_simple.py > copy_robot_viewer.log 2>&1 &

# 起動確認
sleep 2

if pgrep -f "copy_robot_viewer.py" > /dev/null; then
    PID=$(pgrep -f "copy_robot_viewer.py")
    echo "✅ WebUI started successfully! (PID: $PID)"
    echo ""
    echo "Access URL:"
    echo "  http://localhost:5000"
    echo ""
    echo "Commands:"
    echo "  View logs: tail -f copy_robot_viewer.log"
    echo "  Stop: pkill -f copy_robot_viewer.py"
    echo ""
else
    echo "❌ Failed to start WebUI"
    echo "Check copy_robot_viewer.log for errors"
    exit 1
fi

echo "========================================================================"
