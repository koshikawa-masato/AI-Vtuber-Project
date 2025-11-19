# LangSmith Setup Guide

LangSmithを使って三姉妹討論システムのLLM呼び出しをトレーシングする手順。

---

## 📋 前提条件

- Python 3.10以上
- LangSmith Python SDK（既にインストール済み）

---

## 🔑 Step 1: LangSmith APIキー取得

### 1.1 LangSmithアカウント作成

1. https://smith.langchain.com にアクセス
2. 「Sign Up」をクリック
3. GitHubアカウントまたはメールアドレスで登録
   - **クレジットカード不要**
   - 無料プランで月5,000トレース利用可能

### 1.2 APIキー取得

1. ログイン後、右上のユーザーアイコン → **Settings** をクリック
2. 左メニューから **API Keys** を選択
3. **Create API Key** をクリック
4. キー名を入力（例: `botan-project-key`）
5. **Create** をクリック
6. 表示されたAPIキーをコピー（`ls_...` の形式）

⚠️ **重要**: APIキーは一度しか表示されません。必ず安全な場所に保存してください。

---

## 🔧 Step 2: 環境変数設定

### 2.1 `.env`ファイルに追加

`/home/koshikawa/toExecUnit/.env` ファイルを開き、以下を追加：

```bash
# LangSmith (LLM Tracing & Observability)
LANGSMITH_API_KEY=ls_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=botan-project
```

**設定項目説明**:
- `LANGSMITH_API_KEY`: Step 1.2で取得したAPIキー
- `LANGSMITH_TRACING`: トレーシングを有効化（`true`/`false`）
- `LANGSMITH_PROJECT`: プロジェクト名（LangSmithダッシュボードで識別）

### 2.2 環境変数の読み込み確認

```bash
# .envファイルを読み込む（必要に応じて）
source .env

# 確認
echo $LANGSMITH_API_KEY
# → ls_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx と表示されればOK
```

---

## 🧪 Step 3: 動作確認

### 3.1 簡単なテスト

```bash
cd /home/koshikawa/toExecUnit
venv/bin/python src/core/llm_tracing.py
```

**期待される出力**:
```
Testing TracedLLM...

✅ Response: AI VTubers are virtual YouTubers powered by artificial intelligence...
✅ Latency: 1234.56ms
✅ Tokens: {'prompt_tokens': 12, 'completion_tokens': 20, 'total_tokens': 32}

🔍 Check LangSmith dashboard: https://smith.langchain.com
```

### 3.2 LangSmithダッシュボード確認

1. https://smith.langchain.com にアクセス
2. 左メニュー **Projects** → `botan-project` を選択
3. **Runs** タブでトレース一覧を確認

**確認項目**:
- ✅ トレースが記録されている
- ✅ Input/Outputが表示される
- ✅ Latency（レイテンシ）が記録されている
- ✅ Token使用量が記録されている

---

## 🎯 Step 4: 三姉妹討論システムで使用

### 4.1 既存コードの置き換え

**Before** (`three_sisters_council.py`):
```python
import httpx

# 直接Ollama APIを呼び出し
response = httpx.post(
    f"{ollama_url}/api/generate",
    json={"model": model, "prompt": prompt}
)
```

**After** (トレーシング付き):
```python
from src.core.llm_tracing import TracedLLM

# トレーシング付きLLM
llm = TracedLLM(provider="ollama", model="qwen2.5:14b")
result = llm.generate(
    prompt=prompt,
    metadata={"character": "botan", "topic": "VTuber"}
)
```

### 4.2 三姉妹討論の統合例

```python
from src.core.llm_tracing import ThreeSistersTracedCouncil

# 討論システムをトレーシング付きで初期化
council = ThreeSistersTracedCouncil(
    db_path="sisters_memory.db",
    model="qwen2.5:14b",
    project_name="three-sisters-council"
)

# 提案を三姉妹に相談
proposal = {
    "title": "新しいTTS音声の導入",
    "background": "より自然な音声表現を実現したい",
    "implementation": "ElevenLabs v3 APIを統合",
    "expected_effects": "感情表現が豊かになる"
}

opinions = council.consult(proposal)

# 各キャラクターの意見を確認
print(f"牡丹: {opinions['botan']['response']}")
print(f"Kasho: {opinions['kasho']['response']}")
print(f"ユリ: {opinions['yuri']['response']}")
```

---

## 📊 Step 5: ダッシュボードの活用

### 5.1 プロジェクト作成

1. LangSmith → **Projects** → **New Project**
2. プロジェクト名: `three-sisters-council`
3. **Create** をクリック

### 5.2 トレース確認のポイント

**Runs タブ**:
- 各LLM呼び出しの履歴
- Input/Outputの詳細
- Latency（応答時間）
- Token使用量

**Monitoring タブ**:
- リクエスト数の推移
- 平均レイテンシ
- エラー率

**Datasets タブ**（将来的に）:
- テストケース管理
- プロンプトのA/Bテスト

---

## 🔍 トラブルシューティング

### Q1: トレースが表示されない

**確認項目**:
1. `LANGSMITH_TRACING=true` が設定されているか
2. `LANGSMITH_API_KEY` が正しいか
3. インターネット接続があるか

**解決方法**:
```bash
# 環境変数を再確認
echo $LANGSMITH_TRACING  # → true
echo $LANGSMITH_API_KEY  # → ls_... で始まるキー

# Pythonから確認
python3 -c "import os; print(os.getenv('LANGSMITH_TRACING'))"
```

### Q2: APIキーが無効と表示される

**原因**: APIキーが間違っている、または削除された

**解決方法**:
1. LangSmith Settings → API Keys で確認
2. 新しいAPIキーを作成
3. `.env`ファイルを更新

### Q3: トレースが遅い

**原因**: トレーシングのオーバーヘッド（通常50-100ms程度）

**解決方法**:
```bash
# 必要ない時はトレーシングを無効化
LANGSMITH_TRACING=false
```

---

## 📈 コスト計算

### 無料プラン
- 月5,000トレース
- 30日データ保持
- クレジットカード不要

### 三姉妹討論システムの場合
- 1回の討論 = 3トレース（牡丹、Kasho、ユリ）
- 月間討論回数 = 5,000 / 3 = **約1,666回**
- 1日あたり = 1,666 / 30 = **約55回**

**結論**: 無料プランで十分カバー可能

---

## 🎯 次のステップ

1. ✅ LangSmithセットアップ完了
2. ⬜ 三姉妹討論システムに統合
3. ⬜ コスト・レイテンシダッシュボード確認
4. ⬜ Qiita記事執筆「LangSmithで三姉妹討論のコスト・レイテンシを可視化」

---

**作成日**: 2025-11-05
**更新日**: 2025-11-05
**対象**: LangSmith初心者、AI VTuber開発者
