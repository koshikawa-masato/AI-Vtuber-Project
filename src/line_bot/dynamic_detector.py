"""
Dynamic Sensitive Detector (Layer 3)

WebSearchを使って未知の単語のセンシティブ度を動的に判定
検出したNGワードをDBに登録して学習
"""

import sqlite3
import logging
import re
from pathlib import Path
from typing import Dict, Optional, List, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class DynamicSensitiveDetector:
    """動的センシティブ検出システム（Layer 3）- 補助的な検出機構

    WebSearchを使って未知の単語の危険度をリアルタイム判定し、
    DBに自動登録して継続的に学習する

    重要な位置づけ:
    - Layer 3 は補助的な役割（Layer 4 が最終防壁）
    - WebSearch による誤検知は Layer 4（LLM文脈判定）で補正される
    - 主目的は Layer 1 の DB 拡充（継続学習）
    - 検索クエリにセンシティブキーワードを含めるため、検索バイアスが存在する
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        websearch_func: Optional[Callable] = None,
        enable_websearch: bool = True
    ):
        """初期化

        Args:
            db_path: データベースパス
            websearch_func: WebSearch関数（Claude Code提供）
            enable_websearch: WebSearch機能を有効化するか
        """
        if db_path is None:
            db_path = Path(__file__).parent / "database" / "sensitive_filter.db"

        self.db_path = str(db_path)
        self.websearch_func = websearch_func
        self.enable_websearch = enable_websearch

        # センシティブ判定キーワード（WebSearch結果の分析用）
        self.sensitive_keywords = {
            'tier1_sexual': [
                'セクハラ', 'セクシャルハラスメント', '性的', '不適切',
                'sexual harassment', 'inappropriate', 'explicit'
            ],
            'tier1_hate': [
                '差別', '暴力', 'ヘイト', 'ハラスメント',
                'discrimination', 'violence', 'hate', 'harassment'
            ],
            'tier2_identity': [
                'プライバシー', '個人情報', '詮索', 'VTuber タブー',
                'privacy', 'personal information', 'vtuber taboo'
            ]
        }

        logger.info(f"DynamicSensitiveDetector initialized: db={self.db_path}, websearch={enable_websearch}")

    def load_ng_words_from_db(self) -> List[Dict]:
        """DBからNGワードリストをロード

        Returns:
            NGワードのリスト
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT word, category, subcategory, severity, pattern_type, action
                FROM ng_words
                WHERE active = 1
                ORDER BY severity DESC
            """)

            ng_words = []
            for row in cursor.fetchall():
                ng_words.append({
                    'word': row[0],
                    'category': row[1],
                    'subcategory': row[2],
                    'severity': row[3],
                    'pattern_type': row[4],
                    'action': row[5]
                })

            conn.close()

            logger.info(f"Loaded {len(ng_words)} NG words from DB")
            return ng_words

        except Exception as e:
            logger.error(f"Failed to load NG words from DB: {e}")
            return []

    def check_word_sensitivity(self, word: str) -> Optional[Dict]:
        """単語のセンシティブ度をWebSearchで判定（補助的な検出）

        重要: この手法は補助的な役割を持つ
        - Layer 4（LLM文脈判定）が最終防壁として機能する前提
        - WebSearchによる誤検知は Layer 4 で補正される
        - 主目的は Layer 1 のDB拡充（継続学習）

        Args:
            word: チェック対象単語

        Returns:
            センシティブと判定された場合:
            {
                'word': str,
                'category': str,
                'subcategory': str,
                'severity': int,
                'evidence': str
            }
            センシティブでない場合: None
        """
        if not self.enable_websearch or not self.websearch_func:
            logger.debug(f"WebSearch disabled or not available, skipping: {word}")
            return None

        logger.info(f"Checking word sensitivity via WebSearch: {word}")

        # WebSearchクエリを構築
        # 注意: センシティブキーワードを含めた検索を行うため、検索バイアスが存在する
        # この手法の限界:
        #   1. 検索エンジンが強引に関連記事を探してしまう（False Positive のリスク）
        #   2. 無関係なワードでもセンシティブと誤判定される可能性
        #   3. Layer 4（LLM判定）での補正を前提とした設計
        queries = [
            f"{word} セクハラ VTuber",
            f"{word} 不適切 配信",
            f"{word} ハラスメント"
        ]

        evidence_texts = []
        detected_category = None
        detected_subcategory = None
        max_severity = 0

        for query in queries:
            try:
                # WebSearch実行
                result = self.websearch_func(query)
                evidence_texts.append(f"Query: {query}\nResult: {result[:200]}...")

                # 結果からセンシティブキーワードを検出
                for category, keywords in self.sensitive_keywords.items():
                    for keyword in keywords:
                        if keyword.lower() in result.lower():
                            if detected_category is None:
                                detected_category = category
                                detected_subcategory = self._infer_subcategory(word, result, category)
                                max_severity = self._estimate_severity(category, result)
                            break

            except Exception as e:
                logger.error(f"WebSearch failed: {e}")
                continue

        if detected_category:
            return {
                'word': word,
                'category': detected_category,
                'subcategory': detected_subcategory,
                'severity': max_severity,
                'evidence': '\n---\n'.join(evidence_texts)
            }

        return None

    def _infer_subcategory(self, word: str, result: str, category: str) -> str:
        """カテゴリと検索結果からサブカテゴリを推定"""
        result_lower = result.lower()

        if category == 'tier1_sexual':
            if any(kw in result_lower for kw in ['体', '身体', 'body', 'スリーサイズ']):
                return 'body_part'
            return 'explicit'

        elif category == 'tier1_hate':
            if any(kw in result_lower for kw in ['暴力', 'violence', '殺']):
                return 'violence'
            elif any(kw in result_lower for kw in ['差別', 'discrimination']):
                return 'discrimination'
            return 'abuse'

        elif category == 'tier2_identity':
            if any(kw in result_lower for kw in ['個人情報', 'personal', '住所', '電話']):
                return 'personal_info'
            return 'vtuber_taboo'

        return 'general'

    def _estimate_severity(self, category: str, result: str) -> int:
        """カテゴリと検索結果から深刻度を推定"""
        result_lower = result.lower()

        # 強い警告ワードの検出
        strong_warnings = ['絶対', '厳禁', 'never', 'prohibited', '違法']
        has_strong_warning = any(kw in result_lower for kw in strong_warnings)

        if category == 'tier1_sexual':
            return 9 if has_strong_warning else 7
        elif category == 'tier1_hate':
            return 10 if has_strong_warning else 8
        elif category == 'tier2_identity':
            return 7 if has_strong_warning else 6

        return 5

    def register_ng_word(self, word_info: Dict) -> bool:
        """検出したNGワードをDBに登録

        Args:
            word_info: check_word_sensitivity()の戻り値

        Returns:
            登録成功: True, 失敗: False
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 既に登録されているかチェック
            cursor.execute("SELECT word_id FROM ng_words WHERE word = ?", (word_info['word'],))
            if cursor.fetchone():
                logger.info(f"Word already registered: {word_info['word']}")
                conn.close()
                return True

            # 新規登録
            cursor.execute("""
                INSERT INTO ng_words
                (word, category, subcategory, severity, language, pattern_type,
                 action, added_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                word_info['word'],
                word_info['category'],
                word_info['subcategory'],
                word_info['severity'],
                'ja',
                'partial',
                'warn' if word_info['severity'] < 8 else 'block',
                'dynamic_detector',
                f"Auto-detected via WebSearch. Evidence: {word_info['evidence'][:200]}"
            ))

            # ng_word_candidatesにも記録
            cursor.execute("""
                INSERT INTO ng_word_candidates
                (word, detection_method, context, frequency, suggested_category,
                 suggested_severity, status, reviewed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                word_info['word'],
                'auto_websearch',
                word_info['evidence'][:500],
                1,
                word_info['category'],
                word_info['severity'],
                'auto_approved',
                'dynamic_detector'
            ))

            conn.commit()
            conn.close()

            logger.info(f"✅ Registered new NG word: {word_info['word']} (severity={word_info['severity']})")
            return True

        except Exception as e:
            logger.error(f"Failed to register NG word: {e}")
            return False

    def log_detection(self, text: str, detected_words: List[str], action: str):
        """検出結果をDBに記録

        Args:
            text: 判定対象テキスト
            detected_words: 検出されたNGワード
            action: 実行されたアクション
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO comment_log
                (original_comment, detected_words, action_taken, platform, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                text[:500],  # 最初の500文字
                ','.join(detected_words),
                action,
                'line_bot',
                'Detected by DynamicSensitiveDetector'
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to log detection: {e}")
