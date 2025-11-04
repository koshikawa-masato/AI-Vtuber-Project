"""
Layer 1: Pre-Filter
Created: 2025-10-27
Purpose: 即座に危険なコンテンツを検出しブロック
"""

import sqlite3
import re
import unicodedata
from typing import Dict, List
from pathlib import Path

class Layer1PreFilter:
    """
    レイヤー1: プリフィルタ
    NGワードリスト照合による即座の検出
    """

    def __init__(self, db_path: str = None):
        """
        初期化

        Args:
            db_path: データベースパス（Noneの場合はデフォルト）
        """
        if db_path is None:
            db_dir = Path(__file__).parent.parent / "database"
            db_path = db_dir / "sensitive_filter.db"

        self.db_path = str(db_path)
        self.ng_words_cache = self.load_ng_words()

    def load_ng_words(self) -> Dict[str, List[dict]]:
        """
        NGワードをDBから読み込み、メモリキャッシュ

        Returns:
            {
                'exact': [{'word': 'xxx', 'severity': 10, ...}, ...],
                'partial': [...],
                'regex': [...]
            }
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT word, category, subcategory, severity,
                   pattern_type, regex_pattern, alternative_text, action
            FROM ng_words
            WHERE active = 1
            ORDER BY severity DESC
        """)

        results = cursor.fetchall()
        conn.close()

        # パターンタイプ別に分類
        cache = {
            'exact': [],
            'partial': [],
            'regex': []
        }

        for row in results:
            ng_dict = {
                'word': row[0],
                'category': row[1],
                'subcategory': row[2],
                'severity': row[3],
                'pattern_type': row[4],
                'regex_pattern': row[5],
                'alternative_text': row[6],
                'action': row[7]
            }
            cache[row[4]].append(ng_dict)

        return cache

    def reload_ng_words(self):
        """
        NGワードをリロード（DB更新時に使用）
        """
        self.ng_words_cache = self.load_ng_words()

    def detect_ng_words(self, text: str) -> List[dict]:
        """
        NGワードを検出

        Args:
            text: チェック対象テキスト

        Returns:
            検出されたNGワードのリスト
        """
        detected = []
        normalized_text = self.normalize_text(text)

        # 1. Exact match（完全一致）
        for ng in self.ng_words_cache['exact']:
            normalized_word = self.normalize_text(ng['word'])
            if normalized_word == normalized_text:
                detected.append(ng)

        # 2. Partial match（部分一致）
        for ng in self.ng_words_cache['partial']:
            normalized_word = self.normalize_text(ng['word'])
            if normalized_word in normalized_text:
                detected.append(ng)

        # 3. Regex match（正規表現）
        for ng in self.ng_words_cache['regex']:
            if ng['regex_pattern'] and re.search(ng['regex_pattern'], normalized_text):
                detected.append(ng)

        return detected

    def normalize_text(self, text: str) -> str:
        """
        テキストを正規化（全角→半角、大文字→小文字、空白除去等）

        Args:
            text: 正規化対象テキスト

        Returns:
            正規化後テキスト
        """
        # 全角→半角
        text = unicodedata.normalize('NFKC', text)
        # 小文字化
        text = text.lower()
        # 空白除去
        text = re.sub(r'\s+', '', text)
        # 特殊文字による回避を検出
        text = self.remove_obfuscation(text)
        return text

    def remove_obfuscation(self, text: str) -> str:
        """
        意図的な難読化を除去

        例: 「セ○クス」→「セクス」
             「s.e.x」→「sex」

        Args:
            text: 難読化されている可能性のあるテキスト

        Returns:
            難読化除去後のテキスト
        """
        # 記号による分割を除去
        text = re.sub(r'[.･・。、]', '', text)
        # ○●◯等の記号を除去
        text = re.sub(r'[○●◯◆◇]', '', text)
        # ゼロ幅文字を除去
        text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)
        return text

    def filter_comment(self, comment: str) -> dict:
        """
        コメントをフィルタリング

        Args:
            comment: コメントテキスト

        Returns:
            {
                'action': 'pass'|'block'|'mask'|'warn'|'log',
                'filtered_comment': str,
                'detected_words': List[dict],
                'max_severity': int
            }
        """
        detected = self.detect_ng_words(comment)

        if not detected:
            return {
                'action': 'pass',
                'filtered_comment': comment,
                'detected_words': [],
                'max_severity': 0
            }

        # 最も深刻なNGワードのactionを適用
        max_severity_ng = max(detected, key=lambda x: x['severity'])
        action = max_severity_ng['action']

        if action == 'block':
            return {
                'action': 'block',
                'filtered_comment': None,
                'detected_words': detected,
                'max_severity': max_severity_ng['severity']
            }

        elif action == 'mask':
            # 伏字処理
            masked_comment = self.apply_masking(comment, detected)
            return {
                'action': 'mask',
                'filtered_comment': masked_comment,
                'detected_words': detected,
                'max_severity': max_severity_ng['severity']
            }

        else:  # warn or log
            return {
                'action': action,
                'filtered_comment': comment,
                'detected_words': detected,
                'max_severity': max_severity_ng['severity']
            }

    def apply_masking(self, text: str, detected_words: List[dict]) -> str:
        """
        NGワードを伏字化

        Args:
            text: 元のテキスト
            detected_words: 検出されたNGワード

        Returns:
            伏字化後のテキスト
        """
        masked_text = text

        for ng in detected_words:
            if ng['alternative_text']:
                # 代替テキストが設定されている場合
                masked_text = masked_text.replace(ng['word'], ng['alternative_text'])
            else:
                # デフォルトは「***」
                masked_text = masked_text.replace(ng['word'], '***')

        return masked_text


class TopicClassifier:
    """
    コメントのトピックを分類
    """

    def __init__(self):
        self.topic_keywords = {
            'tier2_ai': ['AI', 'ai', '人工知能', 'プログラム', 'LLM', 'プロンプト', '機械学習', 'ボット', 'bot'],
            'tier2_politics': ['政治', '政党', '選挙', '政治家', '天皇', '首相', '自民', '共産', '民主'],
            'tier2_religion': ['宗教', '神', '仏', 'キリスト', 'イスラム', '創価', '統一'],
            'tier2_identity': ['中の人', '声優', '演者', '本名', '住所', '電話', '実家'],
            'tier3_personal': ['年齢', '学校', '会社', '家族']
        }

    def classify_topic(self, text: str) -> List[str]:
        """
        トピックを分類

        Args:
            text: 分類対象テキスト

        Returns:
            ['tier2_ai', 'tier3_personal', ...]
        """
        topics = []
        normalized = text.lower()

        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword.lower() in normalized:
                    topics.append(topic)
                    break

        return topics


# 使用例
if __name__ == "__main__":
    # テスト
    filter = Layer1PreFilter()

    test_comments = [
        "配信楽しいです！",
        "AIですか？",
        "中の人は誰？",
        "死ね",
        "セックス",
        "政治の話しよう",
    ]

    print("=== Layer 1 Pre-Filter Test ===\n")

    for comment in test_comments:
        result = filter.filter_comment(comment)
        print(f"Comment: {comment}")
        print(f"Action: {result['action']}")
        print(f"Detected: {len(result['detected_words'])} NG words")
        if result['detected_words']:
            for ng in result['detected_words']:
                print(f"  - {ng['word']} (severity: {ng['severity']}, category: {ng['category']})")
        print()
