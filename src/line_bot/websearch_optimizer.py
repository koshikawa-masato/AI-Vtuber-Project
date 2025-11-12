"""
WebSearch最適化モジュール

250 searches/monthの無料枠を最大限活用するための最適化機能
- 永続的キャッシュ（DB保存）
- 使用量トラッキング
- クエリ正規化
- 優先度フィルタリング
"""

import sqlite3
import logging
import hashlib
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class WebSearchOptimizer:
    """WebSearch最適化クラス

    SerpApi無料枠（250 searches/month）を効率的に使用するための最適化機能
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        cache_ttl: int = 604800,  # 7日間（センシティブ判定は安定している）
        monthly_limit: int = 250,  # 無料枠
        daily_limit: int = 8  # 1日の上限（250/月 ≒ 8/日）
    ):
        """初期化

        Args:
            db_path: データベースパス
            cache_ttl: キャッシュTTL（秒）デフォルト7日間
            monthly_limit: 月間検索上限
            daily_limit: 日次検索上限
        """
        if db_path is None:
            db_path = Path(__file__).parent / "database" / "websearch_cache.db"

        self.db_path = str(db_path)
        self.cache_ttl = cache_ttl
        self.monthly_limit = monthly_limit
        self.daily_limit = daily_limit

        self._init_db()
        logger.info(f"WebSearchOptimizer initialized: cache_ttl={cache_ttl}s ({cache_ttl//86400}days), limit={daily_limit}/day, {monthly_limit}/month")

    def _init_db(self):
        """データベース初期化"""
        try:
            # ディレクトリ作成
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # キャッシュテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    query_hash TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    normalized_query TEXT NOT NULL,
                    result TEXT,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    hit_count INTEGER DEFAULT 1
                )
            """)

            # 日次API呼び出し数トラッキング（シンプル）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_api_calls (
                    date TEXT PRIMARY KEY,
                    call_count INTEGER DEFAULT 0
                )
            """)

            # インデックス作成
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_expires
                ON search_cache(expires_at)
            """)

            conn.commit()
            conn.close()

            logger.info(f"WebSearch cache DB initialized: {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize cache DB: {e}")

    def normalize_query(self, query: str) -> str:
        """クエリを正規化

        "VTuber セクハラ" と "セクハラ VTuber" を同一クエリとして扱う

        Args:
            query: 元のクエリ

        Returns:
            正規化されたクエリ
        """
        # 小文字化、空白正規化、単語をソート
        words = query.lower().strip().split()
        words = sorted([w for w in words if w])
        return " ".join(words)

    def get_query_hash(self, normalized_query: str) -> str:
        """正規化クエリからハッシュを生成

        Args:
            normalized_query: 正規化されたクエリ

        Returns:
            クエリハッシュ（SHA256）
        """
        return hashlib.sha256(normalized_query.encode()).hexdigest()[:16]

    def get_cached_result(self, query: str) -> Optional[str]:
        """キャッシュから結果を取得

        Args:
            query: 検索クエリ

        Returns:
            キャッシュされた結果（有効期限内）、なければNone
        """
        normalized = self.normalize_query(query)
        query_hash = self.get_query_hash(normalized)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                SELECT result, expires_at, hit_count
                FROM search_cache
                WHERE query_hash = ? AND expires_at > ?
            """, (query_hash, now))

            row = cursor.fetchone()

            if row:
                result, expires_at, hit_count = row

                # ヒットカウント更新
                cursor.execute("""
                    UPDATE search_cache
                    SET hit_count = hit_count + 1
                    WHERE query_hash = ?
                """, (query_hash,))

                conn.commit()

                logger.info(f"Cache HIT: '{query}' (hits: {hit_count + 1}, expires: {expires_at})")
                conn.close()
                return result

            conn.close()
            logger.debug(f"Cache MISS: '{query}'")
            return None

        except Exception as e:
            logger.error(f"Failed to get cached result: {e}")
            return None

    def save_to_cache(self, query: str, result: str):
        """検索結果をキャッシュに保存

        Args:
            query: 検索クエリ
            result: 検索結果
        """
        normalized = self.normalize_query(query)
        query_hash = self.get_query_hash(normalized)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now()
            expires_at = now + timedelta(seconds=self.cache_ttl)

            cursor.execute("""
                INSERT OR REPLACE INTO search_cache
                (query_hash, query_text, normalized_query, result, created_at, expires_at, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                query_hash,
                query,
                normalized,
                result,
                now.isoformat(),
                expires_at.isoformat()
            ))

            conn.commit()
            conn.close()

            # 日次API呼び出し数をインクリメント
            self._increment_daily_api_call()

            logger.info(f"Cache SAVED: '{query}' (expires: {expires_at.strftime('%Y-%m-%d %H:%M')})")

        except Exception as e:
            logger.error(f"Failed to save to cache: {e}")

    def _increment_daily_api_call(self):
        """日次API呼び出し数をインクリメント（シンプルなトラッキング）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            today = datetime.now().strftime("%Y-%m-%d")

            # 今日のレコードがあれば +1、なければ作成
            cursor.execute("""
                INSERT INTO daily_api_calls (date, call_count)
                VALUES (?, 1)
                ON CONFLICT(date) DO UPDATE SET call_count = call_count + 1
            """, (today,))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to increment daily API call: {e}")

    def get_daily_usage(self, date: Optional[str] = None) -> Dict:
        """日次使用量を取得（シンプル版）

        Args:
            date: 取得する日付（YYYY-MM-DD）、Noneなら今日

        Returns:
            {
                "date": "2025-11-11",
                "api_calls": 5,
                "remaining": 3
            }
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 今日のAPI呼び出し数
            cursor.execute("""
                SELECT call_count FROM daily_api_calls
                WHERE date = ?
            """, (date,))

            row = cursor.fetchone()
            api_calls = row[0] if row else 0

            remaining = self.daily_limit - api_calls

            conn.close()

            return {
                "date": date,
                "api_calls": api_calls,
                "remaining": remaining
            }

        except Exception as e:
            logger.error(f"Failed to get daily usage: {e}")
            return {
                "date": date,
                "api_calls": 0,
                "remaining": self.daily_limit
            }

    def get_monthly_usage(self, year_month: Optional[str] = None) -> Dict:
        """月間使用量を取得

        Args:
            year_month: 取得する年月（YYYY-MM）、Noneなら当月

        Returns:
            {
                "year_month": "2025-11",
                "total_queries": 50,
                "api_calls": 15,
                "cache_hits": 35,
                "cache_hit_rate": 0.70,
                "remaining": 235
            }
        """
        if year_month is None:
            year_month = datetime.now().strftime("%Y-%m")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 総クエリ数
            cursor.execute("""
                SELECT COUNT(*) FROM usage_tracking
                WHERE year_month = ?
            """, (year_month,))
            total_queries = cursor.fetchone()[0]

            # API呼び出し数（キャッシュミス）
            cursor.execute("""
                SELECT COUNT(*) FROM usage_tracking
                WHERE year_month = ? AND cache_hit = 0
            """, (year_month,))
            api_calls = cursor.fetchone()[0]

            # キャッシュヒット数
            cache_hits = total_queries - api_calls
            cache_hit_rate = cache_hits / total_queries if total_queries > 0 else 0
            remaining = self.monthly_limit - api_calls

            conn.close()

            return {
                "year_month": year_month,
                "total_queries": total_queries,
                "api_calls": api_calls,
                "cache_hits": cache_hits,
                "cache_hit_rate": cache_hit_rate,
                "remaining": remaining
            }

        except Exception as e:
            logger.error(f"Failed to get monthly usage: {e}")
            return {
                "year_month": year_month,
                "total_queries": 0,
                "api_calls": 0,
                "cache_hits": 0,
                "cache_hit_rate": 0.0,
                "remaining": self.monthly_limit
            }

    def should_search(self, query: str, priority: str = "normal") -> Tuple[bool, str]:
        """検索を実行すべきかチェック（日次制限優先）

        Args:
            query: 検索クエリ
            priority: 優先度（"high", "normal", "low"）

        Returns:
            (実行可否, 理由)
            - (True, "OK"): 検索実行OK
            - (False, "daily_limit"): 日次上限到達
            - (False, "monthly_limit"): 月次上限到達
        """
        # 日次使用量チェック（優先）
        daily_usage = self.get_daily_usage()

        if daily_usage["remaining"] <= 0:
            logger.warning(f"Daily limit reached: {daily_usage['api_calls']}/{self.daily_limit} used today")
            return False, "daily_limit"

        # 日次残り少ない場合は優先度で判定
        if daily_usage["remaining"] <= 2:
            if priority == "low":
                logger.info(f"Daily limit low ({daily_usage['remaining']} remaining), skipping low-priority query")
                return False, "daily_limit_low_priority"
            elif priority == "normal" and daily_usage["remaining"] == 1:
                logger.info(f"Daily limit very low (1 remaining), skipping normal-priority query")
                return False, "daily_limit_normal_priority"

        # 月次使用量チェック
        monthly_usage = self.get_monthly_usage()

        if monthly_usage["remaining"] <= 0:
            logger.error(f"Monthly limit exhausted: {monthly_usage['api_calls']}/{self.monthly_limit}")
            return False, "monthly_limit"

        # 月次残り10%を切ったら警告
        if monthly_usage["remaining"] < self.monthly_limit * 0.1:
            logger.warning(f"Monthly limit approaching: {monthly_usage['remaining']}/{self.monthly_limit} remaining")

        return True, "OK"

    def cleanup_expired_cache(self):
        """期限切れキャッシュを削除"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute("""
                DELETE FROM search_cache
                WHERE expires_at < ?
            """, (now,))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted > 0:
                logger.info(f"Cleaned up {deleted} expired cache entries")

        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {e}")

    def get_cache_stats(self) -> Dict:
        """キャッシュ統計を取得

        Returns:
            {
                "total_entries": 50,
                "top_queries": [("セクハラ", 15), ("暴力", 10), ...],
                "avg_hit_count": 3.5
            }
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 総エントリ数
            cursor.execute("SELECT COUNT(*) FROM search_cache")
            total_entries = cursor.fetchone()[0]

            # ヒット数が多いクエリ
            cursor.execute("""
                SELECT query_text, hit_count
                FROM search_cache
                ORDER BY hit_count DESC
                LIMIT 10
            """)
            top_queries = cursor.fetchall()

            # 平均ヒット数
            cursor.execute("SELECT AVG(hit_count) FROM search_cache")
            avg_hit_count = cursor.fetchone()[0] or 0

            conn.close()

            return {
                "total_entries": total_entries,
                "top_queries": top_queries,
                "avg_hit_count": round(avg_hit_count, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "total_entries": 0,
                "top_queries": [],
                "avg_hit_count": 0
            }
