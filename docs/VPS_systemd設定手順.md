# VPS LINE Bot systemd設定手順

## 概要

さくらVPS上でLINE Botをsystemdサービスとして自動起動する設定を行いました。

## 設定内容

### サービスファイル

ファイル: `/etc/systemd/system/line-bot-vps.service`

```ini
[Unit]
Description=LINE Bot VPS Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/AI-Vtuber-Project
Environment="PATH=/home/ubuntu/AI-Vtuber-Project/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=/home/ubuntu/AI-Vtuber-Project/.env
ExecStart=/home/ubuntu/AI-Vtuber-Project/venv/bin/python -m uvicorn src.line_bot_vps.webhook_server_vps:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 設定完了日時

2025-11-13 13:21:20 JST

### LLM設定

- プロバイダー: OpenAI
- モデル: gpt-4o

## systemdコマンド

### サービスの状態確認

```bash
sudo systemctl status line-bot-vps.service
```

### サービスの起動

```bash
sudo systemctl start line-bot-vps.service
```

### サービスの停止

```bash
sudo systemctl stop line-bot-vps.service
```

### サービスの再起動

```bash
sudo systemctl restart line-bot-vps.service
```

### ログの確認

```bash
# リアルタイムログ
sudo journalctl -u line-bot-vps.service -f

# 最新100行
sudo journalctl -u line-bot-vps.service -n 100

# 特定時刻以降のログ
sudo journalctl -u line-bot-vps.service --since "2025-11-13 13:00:00"
```

### 自動起動の確認

```bash
sudo systemctl is-enabled line-bot-vps.service
```

出力が `enabled` であればOK

## 動作確認

### プロセス確認

```bash
ps aux | grep uvicorn
```

### 起動ログの確認例

```
✅ OpenAI初期化完了: gpt-4o
✅ CloudLLMProvider初期化完了（openai: gpt-4o）
✅ 学習ログシステム初期化: ./learning_logs.db
✅ LearningLogSystem初期化完了
SessionManager initialized (in-memory)
✅ SessionManager初期化完了
PromptManager初期化完了: /home/ubuntu/AI-Vtuber-Project/prompts
世界観ルール読み込み完了: 1537 文字
✅ PromptManager初期化完了
============================================================
🚀 VPS LINE Bot起動
   LLM: openai/gpt-4o
   学習ログDB: ./learning_logs.db
   キャラクター: kasho, botan, yuri
============================================================
Uvicorn running on http://0.0.0.0:8000
```

## トラブルシューティング

### サービスが起動しない場合

```bash
# 詳細なログを確認
sudo journalctl -u line-bot-vps.service -xe

# 設定ファイルの再読み込み
sudo systemctl daemon-reload

# 再起動
sudo systemctl restart line-bot-vps.service
```

### 環境変数が読み込まれない場合

`/home/ubuntu/AI-Vtuber-Project/.env` ファイルを確認：

```bash
cat /home/ubuntu/AI-Vtuber-Project/.env
```

### 手動で起動して確認

```bash
cd /home/ubuntu/AI-Vtuber-Project
source venv/bin/activate
python -m uvicorn src.line_bot_vps.webhook_server_vps:app --host 0.0.0.0 --port 8000
```

## メリット

1. **自動起動**: サーバー再起動時に自動的にLINE Botが起動
2. **自動復旧**: プロセスがクラッシュしても10秒後に自動再起動
3. **ログ管理**: systemd journalで一元管理
4. **管理しやすさ**: systemctlコマンドで統一的に管理

## 注意事項

- サービスの変更後は必ず `sudo systemctl daemon-reload` を実行
- `.env` ファイルの変更後はサービスの再起動が必要
- ログはjournaldで管理されるため、disk使用量に注意

---

作成日: 2025-11-13
作成者: 越川将人 & Claude Code
