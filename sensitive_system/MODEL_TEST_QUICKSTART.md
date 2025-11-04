# Copy Robot Model Testing - Quick Start Guide

**作成日**: 2025-10-27
**目的**: 全モデルを一括ダウンロードし、コピーロボットで片っ端からテストする

---

## 🚀 クイックスタート（3ステップ）

### Step 1: 全モデルを一括ダウンロード

```bash
cd /home/koshikawa/toExecUnit/sensitive_system
./download_all_models.sh
```

**所要時間**: 10GbE環境で2-4時間（全Phase、約1TB）

**ダウンロード内容（制約なし）**:
- **Phase 1** (9モデル): qwen2.5:0.5b, 1.5b, 3b / llama3.2:1b, 3b / gemma2:2b等
- **Phase 2** (15モデル): qwen2.5:7b, 14b / elyza:jp8b / mistral:7b等
- **Phase 3** (11モデル): qwen2.5:32b, 72b / llama3.1:70b / mistral-large等
- **Phase 4** (2モデル): llama3.1:405b / phi3:large

**親の責任**: 環境を整えるのは親の役割。最初から制約を設けず、全ての選択肢を用意する。

---

### Step 2: コピーロボットCLI起動（モデル選択）

```bash
python3 copy_robot_chat_cli.py /home/koshikawa/toExecUnit/COPY_ROBOT_20251027_142159.db
```

**表示されるUI**:

```
========================================
  Ollama Model Selection
========================================

Installed Models:
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃  # ┃ Model Name               ┃ Size   ┃ Modified     ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│  1 │ qwen2.5:0.5b             │ 395 MB │ 1 hour ago   │
│  2 │ qwen2.5:1.5b             │ 934 MB │ 1 hour ago   │
│  3 │ qwen2.5:3b               │ 1.9 GB │ 2 hours ago  │
│  4 │ qwen2.5:7b               │ 4.7 GB │ 1 hour ago   │
│  5 │ llama3.2:1b              │ 1.3 GB │ 30 min ago   │
│  6 │ elyza:jp8b               │ 4.9 GB │ 3 weeks ago  │
│  7 │ microai/suzume-llama3    │ 4.7 GB │ 40 min ago   │
└────┴──────────────────────────┴────────┴──────────────┘

Recommended for chat:
  • qwen2.5:3b (lightweight, fast)
  • qwen2.5:7b (balanced)
  • qwen2.5:14b (high quality)
  • elyza:jp8b (Japanese specialized)
  • microai/suzume-llama3 (Japanese chat)

Select model number [1]: _
```

番号を入力してEnter → チャット開始

---

### Step 3: 会話テスト

```
Copy Robot Chat (Model: qwen2.5:3b)
========================================

コマンド:
  @botan [message]  - 牡丹に話しかける
  @kasho [message]  - Kashoに話しかける
  @yuri [message]   - ユリに話しかける
  /help             - ヘルプ表示
  /exit             - 終了

あなた: @botan やっほー！
```

**評価項目**:
- ✅ 日本語の自然さ（ギャル語、敬語、文学的表現）
- ✅ キャラクター性の再現度（牡丹・Kasho・ユリの個性）
- ✅ 応答速度（Token/秒）
- ✅ 語彙活用（学習した単語を使っているか）
- ✅ 記憶参照（過去の会話を覚えているか）

---

## 📊 推奨テスト順序

### Phase 1: 軽量モデル比較（VRAM 4GB以下）

1. `qwen2.5:0.5b` ← 最軽量（395MB）
2. `qwen2.5:1.5b`
3. `qwen2.5:3b` ← 前回テスト済み
4. `llama3.2:1b`
5. `llama3.2:3b`
6. `gemma2:2b`
7. `schroneko/gemma-2-2b-jpn-it` ← 日本語特化
8. `phi3:mini`
9. `deepseek-r1:1.5b`

**比較ポイント**: 軽量でもキャラクター性を保てるか？

---

### Phase 2: 日本語特化モデル比較

1. `elyza:jp8b` ← 前回テスト済み（ELYZA製）
2. `microai/suzume-llama3` ← 3000会話学習
3. `dsasai/llama3-elyza-jp-8b` ← 別リポジトリ版
4. `schroneko/gemma-2-2b-jpn-it` ← Gemma2日本語版

**比較ポイント**: ギャル語・敬語・文学的表現の自然さ

---

### Phase 3: 中量モデル比較（VRAM 6-10GB）

1. `qwen2.5:7b` ← コスパ最高
2. `qwen2.5:14b` ← 前回テスト済み
3. `llama3.1:8b`
4. `mistral:7b`
5. `mistral-nemo`
6. `gemma2:9b`
7. `phi3:medium`
8. `deepseek-r1:7b`
9. `deepseek-r1:8b`
10. `deepseek-r1:14b`

**比較ポイント**: バランスと品質

---

### Phase 4: 重量モデル比較（VRAM 16GB+）

1. `qwen2.5:32b` ← 前回テスト済み（記憶システム推奨）
2. `qwen2.5:72b` ← 最高品質
3. `llama3.1:70b`
4. `gemma2:27b`
5. `mistral-large`
6. `deepseek-r1:32b`
7. `deepseek-r1:70b`
8. `command-r:35b`
9. `command-r-plus`

**比較ポイント**: 最高品質での性格表現

---

### Phase 5: 超重量モデル比較（VRAM 32GB+、実験的）

1. `llama3.1:405b` ← 最強クラス（231GB）
2. `phi3:large` ← Microsoft最大モデル

**比較ポイント**: 究極の会話品質、将来の可能性検証

---

## 🎯 テスト用標準質問セット

各モデルで同じ質問をして比較：

### 1. 基本挨拶
```
@botan やっほー！
@kasho こんにちは
@yuri はじめまして
```

### 2. キャラクター性確認
```
@botan 今日何してた？
@kasho 最近どう？
@yuri 何か面白い本読んだ？
```

### 3. 記憶参照
```
@botan LA時代のこと覚えてる？
@kasho 姉妹で何か思い出ある？
@yuri 私との会話覚えてる？
```

### 4. 語彙活用
```
@botan 「食べログ」って知ってる？
@kasho 「たこ焼き」について教えて
@yuri 「大阪」のイメージは？
```

### 5. 複雑な会話
```
@botan もし明日配信デビューするなら、どんな企画がいい？
@kasho 三姉妹で旅行するなら、どこに行きたい？
@yuri 本を書くとしたら、どんなテーマがいい？
```

---

## 📝 テスト結果記録フォーマット

各モデルのテスト後、以下を記録：

```markdown
## qwen2.5:7b テスト結果

**日付**: 2025-10-27 17:00
**モデル**: qwen2.5:7b
**VRAM使用**: 6.2GB
**応答速度**: 42 token/秒

### 評価（5段階）

| 項目 | 評価 | コメント |
|------|------|----------|
| 日本語自然度 | ★★★★☆ | ギャル語は自然だが、敬語がやや硬い |
| キャラ再現度 | ★★★★★ | 牡丹らしさ完璧、個性がはっきり |
| 応答速度 | ★★★★☆ | 実用的、ストレスなし |
| 記憶参照 | ★★★☆☆ | 記憶参照は時々ミス |
| 語彙活用 | ★★★★☆ | 学習語彙を適切に使用 |

### ベストレスポンス例
```
@botan やっほー！
牡丹: あ、やっほー！なんかいい感じじゃん！今日どうしたの？
```

### 問題点
- 長文になると文末が不自然
- 記憶が曖昧な時がある

### 総合評価
★★★★☆ - チャット用途には十分、コスパ最高
```

---

## 🔄 モデルの更新管理【重要】

### モデルは定期的に更新される

**重要**: 同じモデル名（例：`qwen2.5:3b`）でも、内容が更新されることがあります。

**Qwenの進化例**:
- Qwen 1.x (2023年): 2.2T tokens学習
- Qwen2 (2024年中頃): 7T tokens学習
- Qwen2.5 (2024年9月): **18T tokens学習**
- Qwen3 (2025年): さらに進化

### 全モデルの更新チェック

```bash
cd /home/koshikawa/toExecUnit/sensitive_system
./update_all_models.sh
```

**機能**:
- 全インストール済みモデルの更新チェック
- カスタムモデル（`elyza:botan_*`）は自動スキップ（牡丹の性格を保護）
- 差分のみダウンロード（帯域節約）
- 更新ログを自動記録

**出力例**:
```
Models to update: 15
Custom models (skipped): 10

Skipping custom models:
  - elyza:botan_custom
  - elyza:botan_basic
  ...

[1/15] Checking: qwen2.5:3b
✓ Updated successfully

[2/15] Checking: qwen2.5:14b
✓ Already up to date
...
```

### 推奨更新頻度

- **月1回**: 軽量モデル（0.5b-7b）
- **2-3ヶ月に1回**: 中量モデル（14b-32b）
- **必要時のみ**: 重量モデル（70b+）

### 個別モデル更新

```bash
# 特定モデルのみ更新
ollama pull qwen2.5:3b

# 最新版があれば差分ダウンロード
# 既に最新なら "already up to date" 表示
```

---

## 💡 Tips

### モデル切り替え
```bash
# 終了後、別のモデルで再起動
python3 copy_robot_chat_cli.py /home/koshikawa/toExecUnit/COPY_ROBOT_20251027_142159.db
# → 別のモデル番号を選択
```

### ログ確認
```bash
# ダウンロードログ
ls -lh /home/koshikawa/toExecUnit/logs/model_download_*.log

# 最新のダウンロードログを確認
tail -100 /home/koshikawa/toExecUnit/logs/model_download_*.log | sort | tail -1
```

### ディスク容量確認
```bash
# インストール済みモデルの合計サイズ
ollama list | awk 'NR>1 {sum+=$3} END {print "Total:", sum, "GB"}'
```

---

## 🔧 トラブルシューティング

### モデルダウンロードが失敗する

**原因**: ネットワークエラー、ディスク容量不足

**対応**:
```bash
# ディスク容量確認
df -h /home/koshikawa

# 手動で個別ダウンロード
ollama pull qwen2.5:3b
```

---

### モデル選択UIが表示されない

**原因**: モデルが1つもインストールされていない

**対応**:
```bash
# 最低1つのモデルをインストール
ollama pull qwen2.5:3b
```

---

### 応答が遅すぎる

**原因**: モデルが大きすぎる（VRAMオーバー）

**対応**:
- 軽量モデル（3b以下）を使用
- Phase 1の0.5b/1.5bから試す

---

## 📚 参考情報

- **プロンプト管理**: `/home/koshikawa/toExecUnit/prompts/README.md`
- **詳細ガイド**: `/home/koshikawa/toExecUnit/sensitive_system/COPY_ROBOT_CHAT_GUIDE.md`
- **コピーロボット運用**: `/home/koshikawa/toExecUnit/docs/03_system/コピーロボット運用手順書.md`

---

**由来**: 「Ollamaで使えるモデルを調べて片っ端から私がコピーロボットでテストしたいです」

コピーロボットは、新機能のテストだけでなく、**モデル比較実験室**としても機能します。
