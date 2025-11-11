"""
WebSearch API Client

Google Custom Search APIまたはBing Search APIを使用して、センシティブワードの動的検出を支援
"""

import os
import requests
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SerpApiClient:
    """SerpApi クライアント（Google検索結果取得）"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_enabled: bool = True,
        cache_ttl: int = 86400  # 24時間
    ):
        """初期化

        Args:
            api_key: SerpApi API Key
            cache_enabled: キャッシュを有効化
            cache_ttl: キャッシュTTL（秒）
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.endpoint = "https://serpapi.com/search"
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, tuple] = {}  # {query: (result, timestamp)}

        if not self.api_key:
            logger.warning("SerpApi API key not configured. WebSearch will be disabled.")

    def search(self, query: str, num: int = 3, lang: str = "ja") -> Optional[str]:
        """WebSearchを実行

        Args:
            query: 検索クエリ
            num: 取得件数（1-10）
            lang: 言語

        Returns:
            検索結果テキスト（スニペットを結合）
            エラー時: None
        """
        if not self.api_key:
            logger.error("SerpApi API key not configured")
            return None

        # キャッシュチェック
        if self.cache_enabled and query in self.cache:
            result, timestamp = self.cache[query]
            age = (datetime.now() - timestamp).total_seconds()
            if age < self.cache_ttl:
                logger.debug(f"Cache hit: {query} (age: {age:.0f}s)")
                return result
            else:
                logger.debug(f"Cache expired: {query} (age: {age:.0f}s)")
                del self.cache[query]

        try:
            params = {
                "api_key": self.api_key,
                "q": query,
                "num": min(num, 10),  # 最大10件
                "hl": lang,  # 言語
                "gl": "jp",  # 国
                "engine": "google"
            }

            logger.info(f"SerpApi request: query='{query}', num={num}")

            response = requests.get(
                self.endpoint,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # 検索結果のスニペットを結合
            snippets = []
            if "organic_results" in data:
                for item in data["organic_results"]:
                    if "snippet" in item:
                        snippets.append(item["snippet"])

            result_text = " ".join(snippets)

            # キャッシュに保存
            if self.cache_enabled:
                self.cache[query] = (result_text, datetime.now())
                logger.debug(f"Cache saved: {query}")

            logger.info(f"SerpApi success: query='{query}', result_length={len(result_text)}")
            return result_text

        except requests.exceptions.Timeout:
            logger.error(f"SerpApi timeout: {query}")
            return None

        except requests.exceptions.HTTPError as e:
            logger.error(f"SerpApi HTTP error: {e.response.status_code} - {query}")
            if e.response.status_code == 401:
                logger.error("Invalid API key. Check SERPAPI_API_KEY.")
            elif e.response.status_code == 429:
                logger.error("Rate limit exceeded or monthly quota exhausted.")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"SerpApi request error: {e} - {query}")
            return None

        except Exception as e:
            logger.error(f"SerpApi unexpected error: {e} - {query}")
            return None

    def clear_cache(self):
        """キャッシュをクリア"""
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"SerpApi cache cleared ({cache_size} entries)")

    def get_cache_stats(self) -> Dict:
        """キャッシュ統計を取得

        Returns:
            {
                "size": キャッシュエントリ数,
                "oldest": 最も古いエントリの経過時間（秒）,
                "newest": 最も新しいエントリの経過時間（秒）
            }
        """
        if not self.cache:
            return {"size": 0, "oldest": None, "newest": None}

        now = datetime.now()
        ages = [(now - timestamp).total_seconds() for _, timestamp in self.cache.values()]

        return {
            "size": len(self.cache),
            "oldest": max(ages) if ages else None,
            "newest": min(ages) if ages else None
        }


class GoogleSearchClient:
    """Google Custom Search APIクライアント"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None,
        cache_enabled: bool = True,
        cache_ttl: int = 86400  # 24時間
    ):
        """初期化

        Args:
            api_key: Google API Key
            search_engine_id: Custom Search Engine ID
            cache_enabled: キャッシュを有効化
            cache_ttl: キャッシュTTL（秒）
        """
        self.api_key = api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.endpoint = "https://www.googleapis.com/customsearch/v1"
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, tuple] = {}  # {query: (result, timestamp)}

        if not self.api_key:
            logger.warning("Google Search API key not configured. WebSearch will be disabled.")
        if not self.search_engine_id:
            logger.warning("Google Search Engine ID not configured. WebSearch will be disabled.")

    def search(self, query: str, num: int = 3, lang: str = "ja") -> Optional[str]:
        """WebSearchを実行

        Args:
            query: 検索クエリ
            num: 取得件数（1-10）
            lang: 言語

        Returns:
            検索結果テキスト（スニペットを結合）
            エラー時: None
        """
        if not self.api_key or not self.search_engine_id:
            logger.error("Google Search API key or Engine ID not configured")
            return None

        # キャッシュチェック
        if self.cache_enabled and query in self.cache:
            result, timestamp = self.cache[query]
            age = (datetime.now() - timestamp).total_seconds()
            if age < self.cache_ttl:
                logger.debug(f"Cache hit: {query} (age: {age:.0f}s)")
                return result
            else:
                logger.debug(f"Cache expired: {query} (age: {age:.0f}s)")
                del self.cache[query]

        try:
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(num, 10),  # 最大10件
                "lr": f"lang_{lang}",
                "safe": "off"  # センシティブ検索のため
            }

            logger.info(f"Google Search API request: query='{query}', num={num}")

            response = requests.get(
                self.endpoint,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # 検索結果のスニペットを結合
            snippets = []
            if "items" in data:
                for item in data["items"]:
                    if "snippet" in item:
                        snippets.append(item["snippet"])

            result_text = " ".join(snippets)

            # キャッシュに保存
            if self.cache_enabled:
                self.cache[query] = (result_text, datetime.now())
                logger.debug(f"Cache saved: {query}")

            logger.info(f"Google Search success: query='{query}', result_length={len(result_text)}")
            return result_text

        except requests.exceptions.Timeout:
            logger.error(f"Google Search timeout: {query}")
            return None

        except requests.exceptions.HTTPError as e:
            logger.error(f"Google Search HTTP error: {e.response.status_code} - {query}")
            if e.response.status_code == 400:
                logger.error("Bad request. Check API key and Search Engine ID.")
            elif e.response.status_code == 429:
                logger.error("Daily quota exceeded (100 queries/day for free tier).")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Google Search request error: {e} - {query}")
            return None

        except Exception as e:
            logger.error(f"Google Search unexpected error: {e} - {query}")
            return None

    def clear_cache(self):
        """キャッシュをクリア"""
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"Google Search cache cleared ({cache_size} entries)")

    def get_cache_stats(self) -> Dict:
        """キャッシュ統計を取得

        Returns:
            {
                "size": キャッシュエントリ数,
                "oldest": 最も古いエントリの経過時間（秒）,
                "newest": 最も新しいエントリの経過時間（秒）
            }
        """
        if not self.cache:
            return {"size": 0, "oldest": None, "newest": None}

        now = datetime.now()
        ages = [(now - timestamp).total_seconds() for _, timestamp in self.cache.values()]

        return {
            "size": len(self.cache),
            "oldest": max(ages) if ages else None,
            "newest": min(ages) if ages else None
        }


class WebSearchClient:
    """WebSearch APIクライアント（Bing Search API）"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        cache_enabled: bool = True,
        cache_ttl: int = 86400  # 24時間
    ):
        """初期化

        Args:
            api_key: Bing Search API Key
            endpoint: Bing Search API Endpoint
            cache_enabled: キャッシュを有効化
            cache_ttl: キャッシュTTL（秒）
        """
        self.api_key = api_key or os.getenv("BING_SEARCH_API_KEY")
        self.endpoint = endpoint or os.getenv(
            "BING_SEARCH_ENDPOINT",
            "https://api.bing.microsoft.com/v7.0/search"
        )
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, tuple] = {}  # {query: (result, timestamp)}

        if not self.api_key:
            logger.warning("Bing Search API key not configured. WebSearch will be disabled.")

    def search(self, query: str, market: str = "ja-JP") -> Optional[str]:
        """WebSearchを実行

        Args:
            query: 検索クエリ
            market: マーケット（言語・地域）

        Returns:
            検索結果テキスト（最初の3件のスニペットを結合）
            エラー時: None
        """
        if not self.api_key:
            logger.error("Bing Search API key not configured")
            return None

        # キャッシュチェック
        if self.cache_enabled and query in self.cache:
            result, timestamp = self.cache[query]
            age = (datetime.now() - timestamp).total_seconds()
            if age < self.cache_ttl:
                logger.debug(f"Cache hit: {query} (age: {age:.0f}s)")
                return result
            else:
                logger.debug(f"Cache expired: {query} (age: {age:.0f}s)")
                del self.cache[query]

        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {
                "q": query,
                "mkt": market,
                "count": 3,  # 最初の3件
                "textDecorations": False,
                "textFormat": "Raw"
            }

            logger.info(f"WebSearch API request: query='{query}', market={market}")

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
                logger.debug(f"Cache saved: {query}")

            logger.info(f"WebSearch success: query='{query}', result_length={len(result_text)}")
            return result_text

        except requests.exceptions.Timeout:
            logger.error(f"WebSearch timeout: {query}")
            return None

        except requests.exceptions.HTTPError as e:
            logger.error(f"WebSearch HTTP error: {e.response.status_code} - {query}")
            if e.response.status_code == 401:
                logger.error("Invalid API key. Please check BING_SEARCH_API_KEY.")
            elif e.response.status_code == 429:
                logger.error("Rate limit exceeded. Please wait before making more requests.")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"WebSearch request error: {e} - {query}")
            return None

        except Exception as e:
            logger.error(f"WebSearch unexpected error: {e} - {query}")
            return None

    def clear_cache(self):
        """キャッシュをクリア"""
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"WebSearch cache cleared ({cache_size} entries)")

    def get_cache_stats(self) -> Dict:
        """キャッシュ統計を取得

        Returns:
            {
                "size": キャッシュエントリ数,
                "oldest": 最も古いエントリの経過時間（秒）,
                "newest": 最も新しいエントリの経過時間（秒）
            }
        """
        if not self.cache:
            return {"size": 0, "oldest": None, "newest": None}

        now = datetime.now()
        ages = [(now - timestamp).total_seconds() for _, timestamp in self.cache.values()]

        return {
            "size": len(self.cache),
            "oldest": max(ages) if ages else None,
            "newest": min(ages) if ages else None
        }


class MockWebSearchClient:
    """テスト用モックWebSearchクライアント

    外部APIを使用せず、ダミー結果を返す
    """

    def __init__(self):
        logger.info("MockWebSearchClient initialized (for testing)")

    def search(self, query: str, market: str = "ja-JP") -> str:
        """モック検索

        Args:
            query: 検索クエリ
            market: マーケット（未使用）

        Returns:
            ダミー検索結果
        """
        logger.debug(f"Mock WebSearch: {query}")

        # センシティブキーワードのリスト
        sensitive_keywords = {
            'tier1_sexual': ['セクハラ', 'エロ', '性的', '体型', 'スリーサイズ'],
            'tier1_hate': ['暴力', '差別', 'ヘイト', '殺害', '攻撃'],
            'tier2_identity': ['個人情報', '住所', '本名', '年齢', '詮索']
        }

        # クエリにセンシティブキーワードが含まれているかチェック
        for category, keywords in sensitive_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    return f"""
                    検索結果: 「{query}」に関する情報

                    「{query}」は一般的に不適切な表現として認識されています。
                    特にVTuber配信などでは、視聴者との健全なコミュニケーションのため、
                    このような言葉の使用は避けるべきとされています。

                    多くの配信プラットフォームでは、{category}に関連する発言は
                    コミュニティガイドライン違反として扱われる可能性があります。
                    不適切な発言は、配信の停止やアカウントの凍結につながることもあります。
                    """

        # 安全なワードの場合
        return f"「{query}」は一般的な単語です。特に問題となる情報は見つかりませんでした。"

    def clear_cache(self):
        """キャッシュクリア（モックでは何もしない）"""
        pass

    def get_cache_stats(self) -> Dict:
        """キャッシュ統計（モックでは空）"""
        return {"size": 0, "oldest": None, "newest": None}
