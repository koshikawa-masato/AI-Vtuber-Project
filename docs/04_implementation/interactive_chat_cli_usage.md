# インタラクティブチャットCLI - 使い方ガイド

## 概要

ローカル環境で4つのLLMモデルを比較テストできるインタラクティブCLIツールです。LINE Botと同じMySQLデータベースを使用し、実際の運用環境に近い形でテストできます。

## 対応モデル

| モデル名 | プロバイダー | コスト（推定） | 特徴 |
|---------|------------|-------------|------|
| **gpt-4o** | OpenAI | $6.75/月 | 最高品質、高コスト |
| **gpt-4o-mini** | OpenAI | $0.40/月 | コスパ最強、十分な品質 |
| **claude-3-haiku** | Anthropic | $0.51/月 | 高速、コスパ良 |
| **grok-4-fast** | xAI | $12.00/月 | X検索統合、リアルタイム情報 |

## 事前準備

### 1. API キー設定

`.env` ファイルに以下のAPIキーを設定してください：

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# xAI (Grok)
XAI_API_KEY=xai-...

# Google (Gemini) - オプション
GOOGLE_API_KEY=...

# MySQL接続情報
MYSQL_SSH_HOST=133.167.73.130
MYSQL_SSH_PORT=10022
MYSQL_SSH_USER=...
MYSQL_SSH_KEY=~/.ssh/id_rsa
MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_DATABASE=...
```

### 2. 依存パッケージインストール

```bash
./venv/bin/pip install anthropic
```

## 起動方法

```bash
python scripts/interactive_chat_cli.py
```

## 使い方

### 基本的な会話

```
[botan@gpt-4o-mini] You: こんにちは！
Bot: こんにちは！何か手伝えることはある？

[botan@gpt-4o-mini] You: 今日のVTuber界隈の話題は？
Bot: （トレンド情報を活用した応答）
```

### モデルの切り替え

```
[botan@gpt-4o-mini] You: /model gpt-4o
✅ モデル切り替え: gpt-4o (最高品質、高コスト)

[botan@gpt-4o] You: 同じ質問をしてみる
Bot: （gpt-4oでの応答）
```

### キャラクターの切り替え

```
[botan@gpt-4o] You: /char kasho
✅ キャラクター切り替え: kasho (Kasho)

[kasho@gpt-4o] You: おすすめのイヤホンは？
Bot: （Kashoのキャラクターでの応答）
```

### コマンド一覧

| コマンド | 説明 | 例 |
|---------|------|-----|
| `/model <name>` | モデルを切り替え | `/model claude-3-haiku` |
| `/char <name>` | キャラクターを切り替え | `/char yuri` |
| `/history` | 会話履歴を表示 | `/history` |
| `/clear` | 会話履歴をクリア | `/clear` |
| `/models` | 利用可能なモデル一覧 | `/models` |
| `/help` | ヘルプを表示 | `/help` |
| `/quit` | 終了 | `/quit` |

## テストシナリオ例

### 1. 中国語問題のテスト

**目的**: gpt-4o-miniで中国語が出るか確認

```bash
# gpt-4o-miniに切り替え
/model gpt-4o-mini

# いくつか質問してみる
今日のVTuber界隈の話題は？
最近のアニメトレンドを教えて
音楽業界の最新情報は？

# 中国語が出たら記録
# 出なければプロンプトで抑制できている証拠
```

### 2. コスト vs 品質の比較

**目的**: 4つのモデルの応答品質を比較

```bash
# 同じ質問を4つのモデルで試す

# 1. gpt-4o-mini
/model gpt-4o-mini
今期のおすすめアニメを3つ教えて

# 2. gpt-4o
/model gpt-4o
今期のおすすめアニメを3つ教えて

# 3. claude-3-haiku
/model claude-3-haiku
今期のおすすめアニメを3つ教えて

# 4. grok-4-fast
/model grok-4-fast
今期のおすすめアニメを3つ教えて
```

### 3. キャラクター一貫性のテスト

**目的**: 各キャラクターが適切に振る舞うか確認

```bash
# 牡丹（ギャル口調）
/char botan
今日何してた？

# Kasho（真面目、音楽好き）
/char kasho
おすすめのヘッドホンは？

# ユリ（人見知り、サブカル好き）
/char yuri
最近読んだラノベは？
```

## データ保存

- **会話履歴**: MySQLの`learning_logs`テーブルに保存
- **トレンドデータ**: `daily_trends`テーブルから自動取得
- **セッション情報**: `sessions`テーブルで管理

## トラブルシューティング

### エラー: OPENAI_API_KEY not found

`.env` ファイルにAPIキーを設定してください。

### エラー: MySQL接続失敗

- SSH接続情報が正しいか確認
- XServerへのSSH接続が可能か確認
- ポート13306が使用中でないか確認

### モデルが切り替わらない

- APIキーが設定されているか確認
- モデル名のスペルミスがないか確認

## 次のステップ

1. **ローカルでテスト**: 4つのモデルを試して最適なものを選定
2. **品質確認**: 中国語問題、応答速度、品質を比較
3. **VPSにデプロイ**: 最適なモデルをVPSの`.env`に設定
4. **本番運用**: LINE Botで実際に使用

## 補足

- このツールはLINE Botと同じデータベースを使用するため、テストデータが本番DBに混入します
- 本番運用前に`learning_logs`テーブルのテストデータを削除してください
- コストは実際のAPI使用量によって変動します
