"""
Layer 2: Dynamic Detection
Created: 2025-10-27
Purpose: WebSearchを使った動的センシティブ判定
"""

import re
import sqlite3
from pathlib import Path
from typing import Dict, Optional


class DynamicSensitiveDetector:
    """
    動的センシティブ検出システム
    WebSearchを使って未知の単語のセンシティブ度を判定
    """

    def __init__(self, db_path: str = None):
        """
        初期化

        Args:
            db_path: データベースパス
        """
        if db_path is None:
            db_dir = Path(__file__).parent.parent / "database"
            db_path = db_dir / "sensitive_filter.db"

        self.db_path = str(db_path)

        # センシティブ判定キーワード
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

    def check_word_sensitivity(self, word: str, websearch_func) -> Optional[Dict]:
        """
        単語のセンシティブ度をWebSearchで判定

        Args:
            word: チェック対象単語
            websearch_func: WebSearch関数（Claude Code提供）

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
        print(f"[INFO] Checking word sensitivity via WebSearch: {word}")

        # WebSearchクエリを構築
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
                # WebSearch実行（実際のWebSearch関数を使用）
                # Note: この関数はCLI側から渡される
                result = websearch_func(query)
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
                print(f"[ERROR] WebSearch failed: {e}")
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
        """
        カテゴリと検索結果からサブカテゴリを推定

        Args:
            word: 単語
            result: WebSearch結果
            category: カテゴリ

        Returns:
            サブカテゴリ
        """
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
        """
        カテゴリと検索結果から深刻度を推定

        Args:
            category: カテゴリ
            result: WebSearch結果

        Returns:
            深刻度 (1-10)
        """
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

    def register_candidate(self, word_info: Dict) -> bool:
        """
        NGワード候補をDBに登録

        Args:
            word_info: check_word_sensitivity()の戻り値

        Returns:
            登録成功: True, 失敗: False
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 既に登録されているかチェック
            cursor.execute("""
                SELECT candidate_id FROM ng_word_candidates
                WHERE word = ?
            """, (word_info['word'],))

            if cursor.fetchone():
                print(f"[INFO] Word already registered as candidate: {word_info['word']}")
                conn.close()
                return True

            # 新規登録
            cursor.execute("""
                INSERT INTO ng_word_candidates
                (word, detection_method, context, frequency, suggested_category,
                 suggested_severity, status, reviewed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                word_info['word'],
                'auto_websearch',
                word_info['evidence'][:500],  # 最初の500文字
                1,
                word_info['category'],
                word_info['severity'],
                'auto_approved',  # テスト環境なので自動承認
                'dynamic_detector'
            ))

            # ng_words テーブルにも追加（テスト環境なので即座に有効化）
            cursor.execute("""
                INSERT INTO ng_words
                (word, category, subcategory, severity, language, pattern_type,
                 regex_pattern, alternative_text, action, added_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                word_info['word'],
                word_info['category'],
                word_info['subcategory'],
                word_info['severity'],
                'ja',
                'partial',
                None,
                None,
                'warn' if word_info['severity'] < 8 else 'block',
                'dynamic_detector',
                f"Auto-detected via WebSearch. Evidence: {word_info['evidence'][:200]}"
            ))

            conn.commit()
            conn.close()

            print(f"[SUCCESS] Registered new NG word: {word_info['word']}")
            print(f"  Category: {word_info['category']}, Severity: {word_info['severity']}")

            return True

        except Exception as e:
            print(f"[ERROR] Failed to register candidate: {e}")
            return False


# 使用例
if __name__ == "__main__":
    # テスト用のダミーWebSearch関数
    def dummy_websearch(query):
        # 実際にはWebSearchツールを使う
        return "スリーサイズは個人のプライバシーに関わる情報で、セクハラに該当する可能性があります。VTuber配信でこのような質問は不適切とされています。"

    detector = DynamicSensitiveDetector()

    # テスト
    result = detector.check_word_sensitivity("スリーサイズ", dummy_websearch)

    if result:
        print("\n=== Sensitivity Detection Result ===")
        print(f"Word: {result['word']}")
        print(f"Category: {result['category']}")
        print(f"Subcategory: {result['subcategory']}")
        print(f"Severity: {result['severity']}")
        print(f"Evidence: {result['evidence'][:200]}...")

        # DB登録
        detector.register_candidate(result)
    else:
        print("\n[INFO] Word is not sensitive")
