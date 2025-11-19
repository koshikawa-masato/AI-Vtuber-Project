# Google Custom Search API セットアップ手順

**日時**: 2025-11-11
**目的**: Layer 3動的検出機能でGoogle Custom Search APIを使用するためのセットアップ

---

## 📋 必要なもの

1. Googleアカウント
2. Google Cloud Platformアカウント（無料で作成可能）
3. 無料枠: 100クエリ/日

---

## 🚀 Step 1: Google Cloud Platformでプロジェクト作成

### 1-1. Google Cloud Consoleにアクセス

https://console.cloud.google.com/

### 1-2. 新しいプロジェクトを作成

1. 画面上部の「プロジェクトを選択」をクリック
2. 「新しいプロジェクト」をクリック
3. プロジェクト名: `botan-websearch`（任意）
4. 「作成」をクリック

---

## 🔑 Step 2: Custom Search API有効化とAPIキー取得

### 2-1. Custom Search APIを有効化

1. 左メニューから「APIとサービス」→「ライブラリ」を選択
2. 検索ボックスに「Custom Search API」と入力
3. 「Custom Search API」を選択
4. 「有効にする」をクリック

### 2-2. APIキーを作成

1. 左メニューから「APIとサービス」→「認証情報」を選択
2. 「認証情報を作成」→「APIキー」をクリック
3. APIキーが生成される（例: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXX`）
4. **重要**: APIキーをコピーして安全に保管

### 2-3. APIキーを制限（推奨）

1. 作成したAPIキーの「編集」ボタンをクリック
2. 「APIの制限」セクションで「キーを制限」を選択
3. 「Custom Search API」のみを選択
4. 「保存」をクリック

---

## 🔍 Step 3: Programmable Search Engine作成

### 3-1. Programmable Search Engineにアクセス

https://programmablesearchengine.google.com/

### 3-2. 新しい検索エンジンを作成

1. 「追加」または「新しい検索エンジン」をクリック
2. 設定:
   - **名前**: `Botan Sensitive Detection`（任意）
   - **検索するサイト**: `www.example.com`（後で削除）
   - **言語**: 日本語
3. 「作成」をクリック

### 3-3. Web全体を検索対象に設定

**重要**: デフォルトでは特定サイトのみが検索対象です。Web全体を検索するように変更します。

1. 作成した検索エンジンの「カスタマイズ」をクリック
2. 「検索する対象」セクション:
   - 「Web全体を検索する」を**ON**に設定
   - 「特定のサイトやページのみを検索する」を**OFF**に設定
3. 「更新」をクリック

### 3-4. Search Engine IDを取得

1. 「設定」タブをクリック
2. 「検索エンジンID」をコピー（例: `a1b2c3d4e5f6g7h8i`）

---

## ⚙️ Step 4: 環境変数設定

### 4-1. .envファイルを編集

```bash
cd /home/koshikawa/AI-Vtuber-Project
nano .env
```

### 4-2. 以下を追加/更新

```bash
# WebSearch API
WEBSEARCH_ENABLED=true
USE_MOCK_WEBSEARCH=false  # Real APIを使用
WEBSEARCH_PROVIDER=google

# Google Custom Search API
GOOGLE_SEARCH_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXX  # Step 2-2で取得
GOOGLE_SEARCH_ENGINE_ID=a1b2c3d4e5f6g7h8i  # Step 3-4で取得
```

---

## 🧪 Step 5: 動作確認テスト

### 5-1. シンプルなテスト

```bash
cd /home/koshikawa/AI-Vtuber-Project
source venv/bin/activate

# 対話的Pythonで確認
python3
```

```python
import os
os.environ["GOOGLE_SEARCH_API_KEY"] = "your_api_key_here"
os.environ["GOOGLE_SEARCH_ENGINE_ID"] = "your_engine_id_here"

from src.line_bot.websearch_client import GoogleSearchClient

client = GoogleSearchClient()
result = client.search("VTuber セクハラ")
print(result)
```

### 5-2. 期待される結果

```
Google Search API request: query='VTuber セクハラ', num=3
Google Search success: query='VTuber セクハラ', result_length=XXX
<検索結果のスニペット>
```

### 5-3. エラーが出た場合

#### エラー: "Bad request. Check API key and Search Engine ID."

- APIキーまたはSearch Engine IDが間違っている
- Custom Search APIが有効化されていない

#### エラー: "Daily quota exceeded (100 queries/day for free tier)."

- 無料枠（100クエリ/日）を超過
- 翌日まで待つか、有料プランに切り替え

#### エラー: "Google Search API key or Engine ID not configured"

- 環境変数が設定されていない
- .envファイルを確認

---

## 📊 使用量の確認

### Google Cloud Consoleで確認

1. https://console.cloud.google.com/
2. 「APIとサービス」→「ダッシュボード」
3. 「Custom Search API」をクリック
4. グラフで使用量を確認

### 無料枠の確認

- **無料枠**: 100クエリ/日
- **リセット**: 毎日午前0時（太平洋標準時）

### 有料プランへの切り替え

もし無料枠を超える場合:

1. https://console.cloud.google.com/
2. 「請求」→「請求アカウントをリンク」
3. 料金: $5/1,000クエリ（最大10,000/日）

---

## 🔐 セキュリティのベストプラクティス

### APIキーの保護

1. **.envファイルをGitignore**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **APIキーをハードコードしない**
   - 必ず環境変数から読み込む
   - コードに直接書かない

3. **APIキーを制限**
   - Custom Search APIのみに制限
   - IPアドレス制限（本番環境）

### 定期的なローテーション

- APIキーは3-6ヶ月ごとに再生成を推奨
- 古いキーは削除

---

## 📝 トラブルシューティング

### 問題: 検索結果が空

**原因**: Search Engineが「特定サイトのみ」になっている

**解決策**:
1. https://programmablesearchengine.google.com/
2. 該当の検索エンジンを選択
3. 「Web全体を検索する」をON

### 問題: 403エラー

**原因**: APIキーの権限不足

**解決策**:
1. Custom Search APIが有効化されているか確認
2. APIキーの制限設定を確認

### 問題: 日本語の検索結果が少ない

**原因**: 言語設定

**解決策**:
- Search Engineの言語を「日本語」に設定
- クエリに`lr=lang_ja`パラメータを追加（実装済み）

---

## 🎯 次のステップ

1. ✅ APIキー取得
2. ✅ Search Engine作成
3. ✅ 環境変数設定
4. ✅ 動作確認テスト
5. → **Layer 3統合テスト実行**
6. → **本番運用開始**

---

## 📚 参考リンク

- [Google Custom Search API 公式ドキュメント](https://developers.google.com/custom-search/v1/overview)
- [Programmable Search Engine](https://programmablesearchengine.google.com/)
- [API料金](https://developers.google.com/custom-search/v1/overview#pricing)
- [APIキー管理](https://console.cloud.google.com/apis/credentials)

---

**署名**:
🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
