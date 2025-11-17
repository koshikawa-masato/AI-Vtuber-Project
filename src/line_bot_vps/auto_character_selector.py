"""
三姉妹自動選択モジュール（親和性スコアリング）

ユーザーメッセージから最適なキャラクターを自動選択
"""

import logging
from typing import Dict, Optional
from .mysql_manager import MySQLManager

logger = logging.getLogger(__name__)


# キャラクター別キーワード辞書（親和性判定用）
CHARACTER_KEYWORDS = {
    "botan": {
        # VTuber・エンタメ
        "keywords": [
            "vtuber", "ホロライブ", "にじさんじ", "配信", "ストリーマー",
            "youtube", "twitch", "スパチャ", "切り抜き", "コラボ",
            "アイドル", "エンタメ", "芸能", "ドラマ", "映画",
            "音ゲー", "ゲーム実況", "apexlegends", "valorant", "minecraft"
        ],
        "default_score": 1
    },
    "kasho": {
        # 音楽・オーディオ
        "keywords": [
            "音楽", "ライブ", "コンサート", "フェス", "バンド",
            "アーティスト", "楽器", "ギター", "ピアノ", "ボイトレ",
            "イヤホン", "ヘッドホン", "dap", "オーディオ", "音質",
            "モニター", "宅録", "dtm", "作曲", "編曲",
            "ロック", "ポップ", "ジャズ", "クラシック", "歌"
        ],
        "default_score": 1
    },
    "yuri": {
        # サブカル・アニメ・ライトノベル
        "keywords": [
            "アニメ", "漫画", "ライトノベル", "ラノベ", "小説",
            "サブカル", "オタク", "コミケ", "同人", "二次創作",
            "異世界", "転生", "悪役令嬢", "なろう系", "ファンタジー",
            "sf", "ミステリー", "推理", "恋愛", "学園"
        ],
        "default_score": 1
    }
}


class AutoCharacterSelector:
    """三姉妹自動選択クラス"""

    def __init__(self, mysql_manager: MySQLManager):
        """初期化

        Args:
            mysql_manager: MySQLManagerインスタンス
        """
        self.mysql_manager = mysql_manager

    def calculate_affinity(self, message: str, character: str) -> int:
        """親和性スコアを計算

        Args:
            message: ユーザーメッセージ
            character: キャラクター名 ('botan', 'kasho', 'yuri')

        Returns:
            親和性スコア (1-5)
        """
        message_lower = message.lower()

        # キーワードマッチング
        keywords = CHARACTER_KEYWORDS.get(character, {}).get("keywords", [])
        match_count = sum(1 for keyword in keywords if keyword in message_lower)

        # スコア計算
        if match_count >= 3:
            return 5  # 非常に高い
        elif match_count == 2:
            return 4  # 高い
        elif match_count == 1:
            return 3  # 中程度
        else:
            # デフォルトスコア
            return CHARACTER_KEYWORDS.get(character, {}).get("default_score", 2)

    def select_best_character(self, message: str) -> Dict[str, any]:
        """最適なキャラクターを自動選択

        Args:
            message: ユーザーメッセージ

        Returns:
            {
                "character": "botan" | "kasho" | "yuri",
                "scores": {"botan": 3, "kasho": 5, "yuri": 2},
                "reason": "音楽関連のキーワードが多いため"
            }
        """
        scores = {}

        for character in ["botan", "kasho", "yuri"]:
            score = self.calculate_affinity(message, character)
            scores[character] = score

        # 最も親和性が高いキャラクターを選択
        best_character = max(scores, key=scores.get)
        best_score = scores[best_character]

        # 理由を生成
        reason = self._generate_reason(best_character, best_score)

        logger.info(f"🎯 自動選択: {best_character} (スコア: {best_score}/5)")
        logger.debug(f"   全スコア: {scores}")

        return {
            "character": best_character,
            "scores": scores,
            "reason": reason
        }

    def _generate_reason(self, character: str, score: int) -> str:
        """選択理由を生成

        Args:
            character: 選択されたキャラクター
            score: 親和性スコア

        Returns:
            理由テキスト
        """
        reasons = {
            "botan": "VTuber・エンタメ関連",
            "kasho": "音楽・オーディオ関連",
            "yuri": "サブカル・アニメ・ライトノベル関連"
        }

        base_reason = reasons.get(character, "")

        if score >= 4:
            return f"{base_reason}のキーワードが多いため"
        elif score == 3:
            return f"{base_reason}の話題と判断"
        else:
            return "デフォルト選択"
