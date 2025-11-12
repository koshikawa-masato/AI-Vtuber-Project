# WebSearch統合 設計書

**日時**: 2025-11-11
**目的**: Layer 3拡張機能のWebSearch連携を実現するための外部API統合

---

## 📋 WebSearch APIの選択肢

### 1. SerpAPI
- **公式サイト**: https://serpapi.com/
- **料金**:
  - Free: 100 searches/month
  - Developer: $50/month (5,000 searches)
  - Production: $130/month (15,000 searches)
- **特徴**:
  - Google検索結果を取得
  - JSON形式で結果を返す
  - 日本語対応
  - レート制限: 秒間5リクエスト
- **メリット**:
  - 使いやすいAPI
  - ドキュメントが充実
  - Pythonライブラリあり
- **デメリット**:
  - コストがやや高い
  - Google検索の利用規約に注意が必要

### 2. ~~Bing Search API (Microsoft Azure)~~ ⚠️ 廃止
- **公式サイト**: ~~https://www.microsoft.com/en-us/bing/apis/bing-web-search-api~~
- **状況**: **2025年8月11日に廃止決定**
- **移行先**: Azure AI Agents（Grounding with Bing Search）
  - REST APIではなく、Azure AI Foundry SDK経由の統合が必要
  - コスト40-483%増加
  - アーキテクチャが複雑化
- **デメリット**:
  - 既に廃止が決定
  - 移行コストが非常に高い
  - 本プロジェクトには不適合

### 3. Google Custom Search API
- **公式サイト**: https://developers.google.com/custom-search/v1/overview
- **料金**:
  - Free: 100 queries/day
  - Paid: $5/1,000 queries (最大10,000 queries/day)
- **特徴**:
  - Googleの公式API
  - カスタム検索エンジン作成
  - 日本語対応
- **メリット**:
  - 最も正確な検索結果
  - 無料枠が大きい
- **デメリット**:
  - カスタム検索エンジンの設定が必要
  - 1日10,000クエリ制限

### 4. DuckDuckGo Instant Answer API
- **公式サイト**: https://duckduckgo.com/api
- **料金**: 完全無料
- **特徴**:
  - プライバシー重視
  - APIキー不要
- **メリット**:
  - 完全無料
  - 登録不要
- **デメリット**:
  - 検索結果の質が低い
  - 日本語対応が弱い
  - センシティブ判定には不向き

---

## 🎯 推奨アプローチ（2025年11月更新）

### ⚠️ 重要: Bing Search API廃止について

2025年8月11日にBing Search APIが廃止されたため、当初の推奨から変更します。

### Phase 1: MockWebSearchClient使用（短期・推奨） ⭐

**理由**:
1. **実装済み**: 追加コストなし
2. **APIキー不要**: 外部依存なし
3. **テスト済み**: 全テスト合格
4. **十分な精度**: センシティブキーワードパターンマッチングで実用的

**メリット**:
- コストゼロ
- セットアップ不要
- プライバシー保護（外部送信なし）

**制限**:
- 実際のWeb検索ではない
- 固定パターンのみ（カスタマイズ可能）

### Phase 2: Google Custom Search API（中長期）

**理由**:
1. **無料枠**: 100クエリ/日（十分な量）
2. **正確性**: Googleの検索品質
3. **REST API**: シンプルな統合
4. **日本語対応**: 優秀

**コスト**:
- 無料枠内: $0
- 超過時: $5/1,000クエリ

**想定使用量**:
- 1日10メッセージ × 2未知ワード = 20検索/日
- キャッシュ効果: 実質10検索/日
- **無料枠内で運用可能**

---

## 🔧 実装設計

### 環境変数

**Phase 1: MockWebSearchClient（推奨）**

```bash
# .env
WEBSEARCH_ENABLED=true
USE_MOCK_WEBSEARCH=true  # MockWebSearchClientを使用
WEBSEARCH_MAX_QUERIES_PER_MESSAGE=5
WEBSEARCH_CACHE_ENABLED=true
WEBSEARCH_CACHE_TTL=86400  # 24時間
```

**Phase 2: Google Custom Search API（将来）**

```bash
# .env
WEBSEARCH_ENABLED=true
USE_MOCK_WEBSEARCH=false
GOOGLE_SEARCH_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id
WEBSEARCH_MAX_QUERIES_PER_MESSAGE=5
WEBSEARCH_CACHE_ENABLED=true
WEBSEARCH_CACHE_TTL=86400  # 24時間
```

### 実装ファイル

#### 1. `src/line_bot/websearch_client.py` (新規作成)

```python
import os
import requests
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WebSearchClient:
    """WebSearch APIクライアント"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        cache_enabled: bool = True,
        cache_ttl: int = 86400
    ):
        self.api_key = api_key or os.getenv("BING_SEARCH_API_KEY")
        self.endpoint = endpoint or os.getenv("BING_SEARCH_ENDPOINT",
                                               "https://api.bing.microsoft.com/v7.0/search")
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, tuple] = {}  # {query: (result, timestamp)}

    def search(self, query: str, market: str = "ja-JP") -> Optional[str]:
        """WebSearchを実行

        Args:
            query: 検索クエリ
            market: マーケット（言語・地域）

        Returns:
            検索結果テキスト（最初の3件のスニペットを結合）
        """
        if not self.api_key:
            logger.error("Bing Search API key not configured")
            return None

        # キャッシュチェック
        if self.cache_enabled and query in self.cache:
            result, timestamp = self.cache[query]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                logger.debug(f"Cache hit: {query}")
                return result

        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {
                "q": query,
                "mkt": market,
                "count": 3,  # 最初の3件
                "textDecorations": False,
                "textFormat": "Raw"
            }

            response = requests.get(
                self.endpoint,
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # 検索結果のスニペットを結合
            snippets = []
            if "webPages" in data and "value" in data["webPages"]:
                for item in data["webPages"]["value"]:
                    if "snippet" in item:
                        snippets.append(item["snippet"])

            result_text = " ".join(snippets)

            # キャッシュに保存
            if self.cache_enabled:
                self.cache[query] = (result_text, datetime.now())

            logger.info(f"WebSearch success: {query} -> {len(result_text)} chars")
            return result_text

        except requests.exceptions.RequestException as e:
            logger.error(f"WebSearch API error: {e}")
            return None

    def clear_cache(self):
        """キャッシュをクリア"""
        self.cache.clear()
        logger.info("WebSearch cache cleared")
```

#### 2. `webhook_server.py` の更新

```python
# WebSearch統合
WEBSEARCH_ENABLED = os.getenv("WEBSEARCH_ENABLED", "false").lower() == "true"

if WEBSEARCH_ENABLED:
    from .websearch_client import WebSearchClient
    websearch_client = WebSearchClient()
    websearch_func = websearch_client.search
    logger.info("WebSearch統合: 有効（Bing Search API）")
else:
    websearch_func = None
    logger.info("WebSearch統合: 無効")

# SensitiveHandler初期化
if USE_SENSITIVE_CHECK:
    sensitive_handler = SensitiveHandler(
        mode=SENSITIVE_CHECK_MODE,
        judge_provider=SENSITIVE_JUDGE_PROVIDER,
        judge_model=SENSITIVE_JUDGE_MODEL,
        enable_layer3=ENABLE_LAYER3,
        websearch_func=websearch_func  # WebSearch関数を注入
    )
```

---

## 📊 レート制限・コスト管理

### 実装する制限

1. **メッセージあたりの検索数制限**: 最大5ワード
2. **キャッシュ**: 同じクエリは24時間キャッシュ
3. **頻度制限**: ユーザーあたり1分間に10検索まで
4. **コスト監視**: 月間使用量をログに記録

### コスト試算

| ケース | 検索数/月 | コスト（Bing API） |
|--------|----------|------------------|
| 軽量（10メッセージ/日） | 1,500 | $0.50 |
| 通常（50メッセージ/日） | 7,500 | $2.50 |
| 高負荷（200メッセージ/日） | 30,000 | $10.00 |

**結論**: 月額$5以下で運用可能（通常使用）

---

## 🧪 テスト計画

### テストケース

1. **正常系**:
   - センシティブなワードの検索（"セクハラ"、"暴力"等）
   - 検索結果からのセンシティブ判定
   - DB登録とリロード

2. **異常系**:
   - APIキーが無効
   - ネットワークエラー
   - タイムアウト
   - レート制限超過

3. **キャッシュ**:
   - 同じクエリの2回目検索（キャッシュヒット）
   - キャッシュTTL超過後の再検索

### モックテスト

APIキーなしでもテスト可能なモック実装:

```python
class MockWebSearchClient:
    """テスト用モックWebSearchクライアント"""

    def search(self, query: str) -> str:
        # センシティブキーワードを含む場合、それらしい結果を返す
        sensitive_keywords = ["セクハラ", "暴力", "差別", "ヘイト"]
        if any(kw in query for kw in sensitive_keywords):
            return f"「{query}」は不適切な表現として認識されており、VTuber配信では避けるべきです。"
        return f"「{query}」は一般的な単語です。"
```

---

## 🚀 実装ステップ

### Phase 1: 基本実装（今回）
- [x] 設計書作成
- [ ] WebSearchClient実装
- [ ] webhook_serverへの統合
- [ ] 基本テスト

### Phase 2: 最適化
- [ ] キャッシュ機能の実装
- [ ] レート制限の実装
- [ ] エラーハンドリングの強化

### Phase 3: 運用
- [ ] コスト監視ダッシュボード
- [ ] アラート設定
- [ ] 定期レビュー

---

## ⚠️ 注意事項

### セキュリティ

1. **APIキーの管理**:
   - 環境変数で管理（.envファイル）
   - Gitにコミットしない（.gitignoreに追加）
   - 本番環境では環境変数または秘密管理サービス使用

2. **検索クエリのサニタイズ**:
   - 個人情報を含まないよう注意
   - ログに検索クエリを記録する場合は匿名化

### プライバシー

1. **ユーザーメッセージの取り扱い**:
   - WebSearchに送信する前にキーワード抽出のみ
   - フルメッセージは送信しない
   - 検索結果はログに記録しない（またはハッシュ化）

---

## 📝 代替案: Claude Code WebSearch Tool

**現在検討中**: Claude Code自体が提供するWebSearch toolを活用する方法

**メリット**:
- 外部API不要
- コストなし
- 実装が簡単

**デメリット**:
- リアルタイム性が低い可能性
- Claude Codeのコンテキストを消費
- プログラムからの直接呼び出しが困難

**結論**: まずはBing Search API統合を進め、将来的にClaude Code toolとの連携を検討

---

**署名**:
🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
