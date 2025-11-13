#!/bin/bash
set -e

# ========================================
# VPSデプロイスクリプト
# ========================================

echo "============================================================"
echo "🚀 VPS LINE Bot デプロイスクリプト"
echo "============================================================"

# 設定
VPS_HOST="sakura-vps"
VPS_USER="ubuntu"
VPS_DIR="/home/ubuntu/AI-Vtuber-Project"
LOCAL_DIR="/home/koshikawa/AI-Vtuber-Project"

# ========================================
# 1. コード転送
# ========================================

echo ""
echo "📦 コード転送中..."
rsync -avz --delete \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='sisters_memory.db' \
  --exclude='learning_logs.db' \
  --exclude='*.log' \
  --exclude='.vscode' \
  --exclude='.idea' \
  --exclude='node_modules' \
  --exclude='public' \
  --exclude='docs' \
  --exclude='kirinuki' \
  "${LOCAL_DIR}/" \
  "${VPS_HOST}:${VPS_DIR}/"

echo "  ✅ コード転送完了"

# ========================================
# 2. VPS上でセットアップ
# ========================================

echo ""
echo "🔧 VPS上でセットアップ実行中..."

ssh "${VPS_HOST}" << 'ENDSSH'
set -e

cd /home/ubuntu/AI-Vtuber-Project

echo ""
echo "📦 Python仮想環境セットアップ..."

# 仮想環境作成
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "  ✅ 仮想環境作成完了"
else
  echo "  ℹ️  仮想環境は既に存在します"
fi

# 依存関係インストール
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_vps.txt
echo "  ✅ 依存関係インストール完了"

# ========================================
# 3. copy_robot_memory.db 作成
# ========================================

echo ""
echo "🤖 copy_robot_memory.db 作成中..."

python3 scripts/create_copy_robot_memory.py
echo "  ✅ copy_robot_memory.db 作成完了"

# ========================================
# 4. 環境変数チェック
# ========================================

echo ""
echo "🔑 環境変数チェック..."

if [ ! -f ".env" ]; then
  echo "  ⚠️  .env ファイルが見つかりません"
  echo "  📝 .env.vps.example を参考に .env を作成してください"
  echo ""
  echo "  例:"
  echo "    cp .env.vps.example .env"
  echo "    vim .env  # API キーを設定"
  exit 1
else
  echo "  ✅ .env ファイルが存在します"
fi

# ========================================
# 5. サービス起動テスト
# ========================================

echo ""
echo "🧪 サービス起動テスト..."

# 既存のプロセスを停止
if pgrep -f "uvicorn.*webhook_server_vps" > /dev/null; then
  echo "  ℹ️  既存のプロセスを停止中..."
  pkill -f "uvicorn.*webhook_server_vps" || true
  sleep 2
fi

# バックグラウンドで起動（テスト用）
echo "  🚀 サーバー起動中..."
cd /home/ubuntu/AI-Vtuber-Project
source venv/bin/activate
nohup python3 -m uvicorn src.line_bot_vps.webhook_server_vps:app \
  --host 0.0.0.0 \
  --port 8000 \
  > /tmp/line_bot_vps.log 2>&1 &

# 起動待機
sleep 3

# ヘルスチェック
if curl -s http://localhost:8000/ | grep -q '"status":"ok"'; then
  echo "  ✅ サーバー起動成功"
else
  echo "  ❌ サーバー起動失敗"
  echo "  ログを確認してください: tail -f /tmp/line_bot_vps.log"
  exit 1
fi

echo ""
echo "============================================================"
echo "✅ デプロイ完了"
echo "============================================================"
echo ""
echo "📋 次のステップ:"
echo "  1. .env ファイルを編集してAPI キーを設定"
echo "  2. systemd サービスを設定（本番運用時）"
echo "  3. nginx リバースプロキシ設定（必要に応じて）"
echo "  4. LINE Webhook URL を設定"
echo ""
echo "🔗 Webhook URL:"
echo "  http://133.167.93.123:8000/webhook/kasho"
echo "  http://133.167.93.123:8000/webhook/botan"
echo "  http://133.167.93.123:8000/webhook/yuri"
echo ""
echo "📊 統計API:"
echo "  http://133.167.93.123:8000/api/stats"
echo ""
echo "📝 ログ確認:"
echo "  ssh sakura-vps 'tail -f /tmp/line_bot_vps.log'"
echo ""
echo "============================================================"

ENDSSH

echo ""
echo "✅ デプロイスクリプト完了"
