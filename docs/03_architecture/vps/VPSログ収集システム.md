# VPSログ収集・解析システム

## 概要

さくらVPS上で動作するLINE Botのログをローカルに定期収集し、解析するシステムです。

## システム構成

```
ローカル環境
├── scripts/
│   ├── collect_vps_logs.sh          # ログ収集スクリプト
│   ├── analyze_vps_logs.py          # ログ解析スクリプト
│   ├── auto_collect_and_analyze.sh  # 自動実行スクリプト
│   └── crontab_example.txt          # cron設定例
└── logs/vps/
    ├── daily/                       # 日次ログ
    ├── errors/                      # エラーログ
    ├── stats/                       # 統計情報
    ├── latest_100.log               # 最新100行
    ├── service_status_*.log         # サービス状態
    └── process_info_*.log           # プロセス情報
```

## スクリプト詳細

### 1. collect_vps_logs.sh

VPSからログを収集するメインスクリプト。

**収集内容**:
- 本日のログ全体
- 最新100行のログ
- エラーログ（ERROR/CRITICAL/Exception）
- サービスステータス
- プロセス情報

**使い方**:
```bash
./scripts/collect_vps_logs.sh
```

**出力先**:
- `logs/vps/daily/line-bot-YYYY-MM-DD.log` - 本日のログ
- `logs/vps/errors/errors-YYYY-MM-DD.log` - エラーログ
- `logs/vps/stats/stats-YYYY-MM-DD.txt` - 統計情報

### 2. analyze_vps_logs.py

収集したログを解析するPythonスクリプト。

**解析内容**:
- エラー統計（ERROR/CRITICAL/Exception）
- 警告統計（WARNING）
- キャラクター別会話数
- LLM呼び出し回数
- レスポンス時間（平均・最大）

**使い方**:
```bash
python3 ./scripts/analyze_vps_logs.py logs/vps/daily/line-bot-2025-11-13.log
```

**出力**:
- コンソールにレポート表示
- `logs/vps/daily/analysis_*.json` - 詳細レポート（JSON形式）

### 3. auto_collect_and_analyze.sh

ログ収集と解析を自動実行するスクリプト。cronから呼ばれる。

**処理内容**:
1. `collect_vps_logs.sh` を実行
2. 本日のログファイルを `analyze_vps_logs.py` で解析
3. 結果を `logs/vps/auto_collect.log` に記録

**使い方**:
```bash
./scripts/auto_collect_and_analyze.sh
```

## 自動実行の設定

### 方法1: cron（推奨）

```bash
# crontabを編集
crontab -e

# 以下を追加（毎時0分に実行）
0 * * * * /home/koshikawa/AI-Vtuber-Project/scripts/auto_collect_and_analyze.sh
```

**実行頻度の例**:
- 毎時: `0 * * * *`
- 6時間ごと: `0 */6 * * *`
- 毎日0時: `0 0 * * *`
- 毎日12時: `0 12 * * *`

### 方法2: 手動実行

```bash
cd /home/koshikawa/AI-Vtuber-Project
./scripts/auto_collect_and_analyze.sh
```

## ログの見方

### 本日のログ

```bash
cat logs/vps/daily/line-bot-2025-11-13.log
```

### エラーログのみ

```bash
cat logs/vps/errors/errors-2025-11-13.log
```

### 統計情報

```bash
cat logs/vps/stats/stats-2025-11-13.txt
```

### 解析レポート（JSON）

```bash
cat logs/vps/daily/analysis_line-bot-2025-11-13.json | jq .
```

## ログ収集の仕組み

1. **SSH接続**: ローカルからVPSにSSH接続（鍵認証）
2. **journalctl**: systemd journalからログ取得
3. **フィルタリング**: 日付、サービス名でフィルタ
4. **ローカル保存**: ログをローカルファイルシステムに保存
5. **解析**: Pythonスクリプトでログを解析
6. **レポート生成**: 統計情報とエラーサマリーを生成

## トラブルシューティング

### SSH接続エラー

```bash
# SSH接続確認
ssh sakura-vps "echo OK"

# SSH設定確認
cat ~/.ssh/config | grep -A 5 sakura-vps
```

### ログが空

```bash
# VPS側で直接確認
ssh sakura-vps "sudo journalctl -u line-bot-vps.service -n 10"
```

### 権限エラー

```bash
# ログディレクトリの権限確認
ls -la logs/vps/

# 必要に応じて権限修正
chmod 755 logs/vps/
```

## カスタマイズ

### 収集頻度を変更

`scripts/crontab_example.txt` を参考にcronの設定を変更。

### 解析項目を追加

`scripts/analyze_vps_logs.py` の `_parse_line()` メソッドを編集。

例: 特定のキーワードをカウント
```python
if 'キーワード' in line:
    self.keyword_count += 1
```

### 保存期間の設定

古いログを自動削除するスクリプトを追加：

```bash
# 30日以前のログを削除
find logs/vps/daily -name "*.log" -mtime +30 -delete
```

## ログの活用例

### 1. エラー監視

```bash
# 今日のエラー数をチェック
wc -l logs/vps/errors/errors-$(date +%Y-%m-%d).log
```

### 2. キャラクター別人気度

```bash
# 解析レポートからキャラクター別会話数を抽出
cat logs/vps/daily/analysis_*.json | jq '.summary.character_stats'
```

### 3. パフォーマンス監視

```bash
# レスポンス時間の推移を確認
cat logs/vps/daily/analysis_*.json | jq '.summary.avg_response_time'
```

### 4. LLM使用量の追跡

```bash
# LLM呼び出し回数の推移
cat logs/vps/daily/analysis_*.json | jq '.summary.llm_calls'
```

## セキュリティ注意事項

- SSH鍵は適切に管理（`~/.ssh/sakura-vps`）
- sudoパスワードはスクリプトにハードコード（セキュリティリスク）
- 本番環境では、sudoersでNOPASSWD設定を推奨

### sudoパスワードなし設定（オプション）

VPS側で設定：

```bash
# visudoで編集
sudo visudo

# 以下を追加
ubuntu ALL=(ALL) NOPASSWD: /bin/journalctl, /bin/systemctl
```

その後、スクリプトから `echo 'cha1me2983' | sudo -S` を削除。

## まとめ

- **自動収集**: cronで定期的にVPSログを収集
- **自動解析**: 収集したログを自動解析
- **エラー監視**: エラーログを自動抽出
- **統計情報**: 日次レポートを自動生成

これにより、VPS上のLINE Botの動作を常に監視し、問題を早期発見できます。

---

作成日: 2025-11-13
作成者: 越川将人 & Claude Code
