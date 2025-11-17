# ChatGPT Bridge 使い方ガイド

> クロコ（Claude Code）とチャッピー（ChatGPT GPT-5.1）の自動協働システム

---

## 概要

`chatgpt_bridge.py` を使うと、以下が自動化されます:

1. `to_chatgpt.md` から質問を読み込み
2. GPT-5.1 に質問を送信
3. 回答を `from_chatgpt.md` に保存
4. 履歴を `collaboration_log.md` に追記

---

## セットアップ（初回のみ）

### 1. 依存パッケージのインストール

```bash
pip install openai python-dotenv
```

### 2. API キーの確認

`.env` ファイルに `OPENAI_API_KEY` が設定されているか確認:

```bash
grep OPENAI_API_KEY .env
```

✅ すでに設定済みです

---

## 使い方

### Step 1: クロコが質問を書き込む

クロコが `docs/ai_collaboration/to_chatgpt.md` の「最新の質問」セクションを更新します。

**例**:
```markdown
## 最新の質問

[クロコからチャッピーへ] (2025-11-14)

感情・論理モードの実装について、
MVP範囲で「モード判定の軽量版」を実装する場合、
どのようなトリガー検出が最小限必要でしょうか？
```

### Step 2: スクリプトを実行

```bash
python scripts/chatgpt_bridge.py
```

### Step 3: 結果を確認

自動的に以下が更新されます:

- ✅ `docs/ai_collaboration/from_chatgpt.md` - チャッピーの回答
- ✅ `docs/ai_collaboration/collaboration_log.md` - やり取りの履歴

### Step 4: クロコが回答を読み込んで続きを考える

クロコが `from_chatgpt.md` を読んで、統合設計を進めます。

---

## 実行例

```bash
$ python scripts/chatgpt_bridge.py

============================================================
🤖 ChatGPT Bridge - クロコ ↔ チャッピー
============================================================

📝 質問内容:
------------------------------------------------------------
[クロコからチャッピーへ] (2025-11-14)

感情・論理モードの実装について...
------------------------------------------------------------

📡 GPT-5.1 に質問を送信中...

✅ チャッピーから回答を受信しました

✅ 回答を保存しました: docs/ai_collaboration/from_chatgpt.md
✅ 履歴を更新しました: docs/ai_collaboration/collaboration_log.md

============================================================
🎉 完了！
============================================================

回答を確認してください: docs/ai_collaboration/from_chatgpt.md
```

---

## トラブルシューティング

### Q1: `OPENAI_API_KEY が設定されていません` エラー

**原因**: `.env` に API キーがない

**解決策**:
```bash
echo "OPENAI_API_KEY=your-api-key-here" >> .env
```

API キーは以下から取得:
https://platform.openai.com/api-keys

---

### Q2: `質問が見つかりません` エラー

**原因**: `to_chatgpt.md` の「最新の質問」セクションが空

**解決策**:
1. `docs/ai_collaboration/to_chatgpt.md` を開く
2. 「## 最新の質問」セクションに質問を書き込む
3. 再度スクリプトを実行

---

### Q3: `openai パッケージがインストールされていません` エラー

**解決策**:
```bash
pip install openai
```

または、venv を使っている場合:
```bash
./venv/bin/pip install openai
```

---

## 料金について

GPT-5.1 の使用料金は OpenAI の料金体系に従います。

- Input tokens: 価格は OpenAI のドキュメント参照
- Output tokens: 価格は OpenAI のドキュメント参照

参考: https://openai.com/pricing

**注意**: API を使用するごとに課金されます。

---

## ファイル構成

```
docs/ai_collaboration/
├── README.md              # システム概要
├── USAGE.md              # このファイル
├── to_chatgpt.md         # クロコ → チャッピー（質問）
├── from_chatgpt.md       # チャッピー → クロコ（回答）
└── collaboration_log.md  # やり取りの履歴
```

---

## よくある質問

### Q: GPT-5.1 ではなく GPT-4 を使いたい

`scripts/chatgpt_bridge.py` の以下の行を変更:

```python
# 変更前
model="gpt-5.1",

# 変更後
model="gpt-4",
```

### Q: システムプロンプトをカスタマイズしたい

`scripts/chatgpt_bridge.py` の `ask_chatgpt()` 関数内の `system` メッセージを編集してください。

### Q: 複数の質問を一度に投げたい

現在は「最新の質問」のみを処理します。複数の質問がある場合は、1つずつ実行してください。

---

**🤖 Generated with Claude Code (クロコ)**
**作成日**: 2025-11-14
