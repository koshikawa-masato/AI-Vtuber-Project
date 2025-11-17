# VPS→記憶投入パイプライン

## 概要

VPS上のLINE Bot（クラウドLLM使用）のログをローカルに収集し、コピーロボット（ローカルOllama）でテスト・検証した後、本番のsisters_memory.dbに投入するパイプラインです。

## システム設計

```
┌─────────────────────────────────────────────────────────────┐
│                    VPS (さくらVPS)                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LINE Bot (webhook_server_vps)                       │   │
│  │  - LLM: OpenAI gpt-4o (クラウド)                     │   │
│  │  - ログ: systemd journal                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ SSH経由でログ収集
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              ローカル環境 (WSL2/Ubuntu)                       │
│                                                              │
│  Step 1: ログ収集 (collect_vps_logs.sh)                     │
│  ├─ logs/vps/daily/line-bot-YYYY-MM-DD.log                  │
│  └─ logs/vps/errors/errors-YYYY-MM-DD.log                   │
│                          │                                   │
│                          ▼                                   │
│  Step 2: 会話抽出 (extract_conversations_from_vps_log.py)   │
│  └─ logs/vps/conversations/conv-YYYY-MM-DD.json             │
│                          │                                   │
│                          ▼                                   │
│  Step 3: コピーロボットテスト (test_with_copy_robot.py)      │
│  ├─ LLM: Ollama (ローカル)                                  │
│  ├─ DB: copy_robot_memory.db                                │
│  └─ logs/vps/test_results/result-YYYY-MM-DD.json            │
│                          │                                   │
│                          ▼                                   │
│  Step 4: テスト結果評価                                      │
│  ├─ approved_for_production: true  → Step 5へ               │
│  └─ approved_for_production: false → スキップ                │
│                          │                                   │
│                          ▼                                   │
│  Step 5: 本番DB投入 (import_to_sisters_memory.py)           │
│  └─ sisters_memory.db (本番)                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## ワークフロー詳細

### Step 1: VPSからログ収集

**スクリプト**: `collect_vps_logs.sh`

VPS上のsystemd journalからLINE Botのログを取得。

```bash
./scripts/collect_vps_logs.sh
```

**出力**:
- `logs/vps/daily/line-bot-2025-11-13.log` - 本日のログ全体
- `logs/vps/errors/errors-2025-11-13.log` - エラーログのみ

### Step 2: 会話データ抽出

**スクリプト**: `extract_conversations_from_vps_log.py`

ログファイルから会話データ（ユーザー発言、Bot応答、キャラクター等）を抽出。

```bash
python3 ./scripts/extract_conversations_from_vps_log.py \
    logs/vps/daily/line-bot-2025-11-13.log
```

**出力**:
- `logs/vps/conversations/conv-2025-11-13.json`

**JSON形式例**:
```json
[
  {
    "timestamp": "2025-11-13 14:30:15",
    "user_id": "U123456",
    "user_message": "こんにちは",
    "character": "botan",
    "bot_response": "やっほー！元気してた？",
    "llm_model": "gpt-4o"
  }
]
```

### Step 3: コピーロボットでテスト

**スクリプト**: `test_with_copy_robot.py`

ローカルのコピーロボット環境（Ollama）で会話をテスト・検証。

```bash
python3 ./scripts/test_with_copy_robot.py \
    logs/vps/conversations/conv-2025-11-13.json
```

**検証項目**:
1. Bot応答が空でないか
2. キャラクター名が正しいか（botan/kasho/yuri）
3. センシティブなキーワードが含まれていないか
4. （将来拡張）Ollamaで再生成して品質チェック

**出力**:
- `logs/vps/test_results/result-2025-11-13.json`

**JSON形式例**:
```json
[
  {
    "timestamp": "2025-11-13 14:30:15",
    "character": "botan",
    "user_message": "こんにちは",
    "vps_response": "やっほー！元気してた？",
    "test_status": "passed",
    "test_notes": "すべてのチェックをパス",
    "approved_for_production": true
  }
]
```

### Step 4: テスト結果評価

テスト結果を確認し、`approved_for_production: true` の会話のみを次のステップへ。

### Step 5: 本番DB投入

**スクリプト**: `import_to_sisters_memory.py`

承認された会話を `sisters_memory.db` に投入。

```bash
python3 ./scripts/import_to_sisters_memory.py \
    logs/vps/test_results/result-2025-11-13.json
```

**DB構造** (簡易版):
```sql
CREATE TABLE short_term_memories (
    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    character TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    memory_type TEXT DEFAULT 'conversation',
    importance INTEGER DEFAULT 5,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 統合パイプラインの実行

### 全ステップを自動実行

```bash
./scripts/vps_to_memory_pipeline.sh
```

このスクリプトは以下を順次実行：
1. VPSからログ収集
2. 会話データ抽出
3. コピーロボットでテスト
4. テスト結果確認
5. 本番DBへ投入（承認済みのみ）

### 手動実行（ステップごと）

```bash
# Step 1: ログ収集
./scripts/collect_vps_logs.sh

# Step 2: 会話抽出
python3 ./scripts/extract_conversations_from_vps_log.py \
    logs/vps/daily/line-bot-2025-11-13.log

# Step 3: テスト
python3 ./scripts/test_with_copy_robot.py \
    logs/vps/conversations/conv-2025-11-13.json

# Step 4: 結果確認
cat logs/vps/test_results/result-2025-11-13.json | jq '.[] | select(.approved_for_production == true)'

# Step 5: 投入
python3 ./scripts/import_to_sisters_memory.py \
    logs/vps/test_results/result-2025-11-13.json
```

## 自動化（cron設定）

### 毎日0時にパイプラインを実行

```bash
crontab -e

# 以下を追加
0 0 * * * /home/koshikawa/AI-Vtuber-Project/scripts/vps_to_memory_pipeline.sh >> /home/koshikawa/AI-Vtuber-Project/logs/vps/pipeline.log 2>&1
```

## ディレクトリ構造

```
logs/vps/
├── daily/                          # VPSログ
│   ├── line-bot-2025-11-13.log
│   └── analysis_*.json
├── errors/                         # エラーログ
│   └── errors-2025-11-13.log
├── conversations/                  # 抽出した会話データ
│   └── conv-2025-11-13.json
├── test_results/                   # テスト結果
│   └── result-2025-11-13.json
├── stats/                          # 統計情報
│   └── stats-2025-11-13.txt
└── pipeline.log                    # パイプライン実行ログ
```

## メリット

### 1. クラウドLLMの活用
- VPS環境でOpenAI gpt-4oを使用
- 高品質な会話を生成

### 2. ローカルでの安全な検証
- コピーロボット（Ollama）でテスト
- 本番環境に影響を与えない

### 3. 段階的な品質管理
- 自動テストでエラー検出
- 承認済みのみ本番投入

### 4. コスト最適化
- クラウドLLM: 本番会話のみ
- ローカルLLM: テスト・検証用

## トラブルシューティング

### 会話データが抽出されない

**原因**: ログフォーマットが想定と異なる

**対策**:
```bash
# ログの内容を確認
cat logs/vps/daily/line-bot-2025-11-13.log | head -50

# extract_conversations_from_vps_log.py の正規表現を調整
```

### テストが全件失敗

**原因**: コピーロボットDBが存在しない

**対策**:
```bash
# copy_robot_memory.db を作成
python3 ./scripts/create_copy_robot_memory.py
```

### 本番DBへの投入が失敗

**原因**: sisters_memory.db のスキーマが異なる

**対策**:
```bash
# DBスキーマを確認
sqlite3 sisters_memory.db ".schema"

# import_to_sisters_memory.py のSQL文を調整
```

## 拡張案

### Phase 1: 基本パイプライン（現在）
- ✅ ログ収集
- ✅ 会話抽出
- ✅ 簡易テスト
- ✅ DB投入

### Phase 2: 高度なテスト
- [ ] Ollamaで会話を再生成
- [ ] VPS応答とOllama応答を比較
- [ ] 品質スコアを算出

### Phase 3: 自動学習
- [ ] テスト結果から学習
- [ ] プロンプト最適化
- [ ] センシティブ判定の強化

### Phase 4: リアルタイム同期
- [ ] VPS→ローカルのリアルタイムログ転送
- [ ] 即座にテスト・投入

## セキュリティ注意事項

1. **ログの取り扱い**
   - ユーザーのプライバシー情報を含む可能性
   - ログファイルの権限管理を厳格に

2. **SSH認証**
   - 鍵認証を使用
   - パスワード認証は避ける

3. **本番DB投入**
   - 必ず承認プロセスを経る
   - バックアップを取る

## まとめ

このパイプラインにより、以下が実現：

1. **VPS環境**でクラウドLLM（gpt-4o）を使用した高品質な会話生成
2. **ローカル環境**でコピーロボット（Ollama）による安全な検証
3. **段階的な品質管理**で本番DBの信頼性を確保
4. **自動化**による運用負荷の軽減

---

作成日: 2025-11-13
作成者: 越川将人 & Claude Code
