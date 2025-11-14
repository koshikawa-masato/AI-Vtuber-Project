#!/bin/bash
set -e

# ========================================
# systemdサービスインストールスクリプト
# ========================================

echo "============================================================"
echo "🔧 systemd サービスインストール"
echo "============================================================"

# VPS上で実行
if [ "$(hostname)" != "ik1-433-57699.vs.sakura.ne.jp" ] && [ "$(whoami)" != "ubuntu" ]; then
  echo "⚠️  このスクリプトはVPS上で実行してください"
  echo ""
  echo "実行方法:"
  echo "  ssh sakura-vps"
  echo "  cd /home/ubuntu/AI-Vtuber-Project"
  echo "  ./scripts/install_systemd_service.sh"
  exit 1
fi

echo ""
echo "📦 systemdサービス設定中..."

# サービスファイルをコピー
sudo cp scripts/line-bot-vps.service /etc/systemd/system/

echo "  ✅ サービスファイルをコピーしました"

# systemd再読み込み
sudo systemctl daemon-reload

echo "  ✅ systemd設定を再読み込みしました"

# サービス有効化
sudo systemctl enable line-bot-vps

echo "  ✅ サービスを有効化しました"

# 既存のプロセスを停止
if pgrep -f "uvicorn.*webhook_server_vps" > /dev/null; then
  echo ""
  echo "  ℹ️  既存のプロセスを停止中..."
  pkill -f "uvicorn.*webhook_server_vps" || true
  sleep 2
fi

# サービス起動
sudo systemctl start line-bot-vps

echo "  ✅ サービスを起動しました"

# ステータス確認
sleep 2
sudo systemctl status line-bot-vps --no-pager

echo ""
echo "============================================================"
echo "✅ systemdサービスインストール完了"
echo "============================================================"
echo ""
echo "📋 よく使うコマンド:"
echo "  サービス起動:   sudo systemctl start line-bot-vps"
echo "  サービス停止:   sudo systemctl stop line-bot-vps"
echo "  サービス再起動: sudo systemctl restart line-bot-vps"
echo "  ステータス確認: sudo systemctl status line-bot-vps"
echo "  ログ確認:       sudo journalctl -u line-bot-vps -f"
echo ""
echo "============================================================"
