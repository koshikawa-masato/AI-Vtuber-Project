#!/bin/bash
# Copy Robot Database Viewer - Startup Script
# コピーロボットDB参照WebUIの起動スクリプト

echo "========================================================================"
echo "🤖 Copy Robot Database Viewer"
echo "========================================================================"
echo ""
echo "Starting Web UI..."
echo "Database: sisters_memory_COPY_ROBOT_20251024_143000.db"
echo ""
echo "Access URL:"
echo "  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================================================"
echo ""

# 仮想環境のPythonを使用
/home/koshikawa/toExecUnit/venv_webui/bin/python /home/koshikawa/toExecUnit/copy_robot_viewer.py
