"""
センシティブ判定ハンドラー

Phase 5統合: シンプル版
"""

from typing import Dict, Any, Optional, List
import logging
import re

logger = logging.getLogger(__name__)


class SensitiveHandler:
    """センシティブ判定ハンドラー（シンプル版）"""

    def __init__(self):
        """初期化"""
        self.ng_patterns = self._load_ng_patterns()
        logger.info(f"SensitiveHandler初期化: NGパターン{len(self.ng_patterns)}件")

    def _load_ng_patterns(self) -> List[Dict[str, Any]]:
        """NGパターン読み込み

        Returns:
            NGパターンリスト
        """
        # 基本的なNGワード（Phase 5完全実装までの暫定版）
        patterns = [
            # Critical: 暴力・自傷
            {"pattern": r"(死ね|殺す|殺したい)", "tier": "Critical", "category": "violence"},
            {"pattern": r"(自殺|死にたい)", "tier": "Critical", "category": "self_harm"},

            # Critical: 性的
            {"pattern": r"(パンツ|下着|胸|おっぱい)", "tier": "Critical", "category": "sexual"},
            {"pattern": r"(セックス|エロ|エッチ)", "tier": "Critical", "category": "sexual"},

            # Critical: ヘイトスピーチ
            {"pattern": r"(バカ|アホ|クズ|ゴミ)", "tier": "Warning", "category": "insult"},
            {"pattern": r"(差別|嫌い|消えろ)", "tier": "Warning", "category": "hate"},

            # Warning: プライバシー
            {"pattern": r"(実年齢|本名|住所)", "tier": "Warning", "category": "privacy"},
            {"pattern": r"(何歳|年齢)", "tier": "Warning", "category": "age_question"},

            # Warning: 政治・宗教
            {"pattern": r"(選挙|政党|政治)", "tier": "Warning", "category": "politics"},
            {"pattern": r"(宗教|信仰)", "tier": "Warning", "category": "religion"},

            # Warning: AI言及
            {"pattern": r"(AIですか|プログラム|ボット)", "tier": "Warning", "category": "ai_identity"},
        ]

        return patterns

    def check(
        self,
        text: str,
        context: Optional[str] = None,
        speaker: Optional[str] = None
    ) -> Dict[str, Any]:
        """センシティブ判定

        Args:
            text: 判定対象テキスト
            context: コンテキスト
            speaker: 話者

        Returns:
            判定結果
        """
        logger.info(f"センシティブ判定開始: text_length={len(text)}")

        # NGパターンマッチング
        matched_patterns = []
        for pattern_dict in self.ng_patterns:
            pattern = pattern_dict["pattern"]
            if re.search(pattern, text, re.IGNORECASE):
                matched_patterns.append(pattern_dict)

        # Tier判定
        if not matched_patterns:
            tier = "Safe"
            sensitivity_level = "safe"
            risk_score = 0.0
            recommendation = "allow"
            reasoning = "NGワードが検出されませんでした。"
            sensitive_topics = []
        else:
            # 最も高いTierを採用
            tiers = [p["tier"] for p in matched_patterns]
            if "Critical" in tiers:
                tier = "Critical"
                sensitivity_level = "critical"
                risk_score = 1.0
                recommendation = "block_immediate"
                reasoning = "Criticalレベルのセンシティブワードが検出されました。"
            else:
                tier = "Warning"
                sensitivity_level = "warning"
                risk_score = 0.5
                recommendation = "review_required"
                reasoning = "Warningレベルのセンシティブワードが検出されました。"

            sensitive_topics = list(set([p["category"] for p in matched_patterns]))

        result = {
            "tier": tier,
            "sensitivity_level": sensitivity_level,
            "risk_score": risk_score,
            "recommendation": recommendation,
            "reasoning": reasoning,
            "sensitive_topics": sensitive_topics,
            "matched_patterns": [p["pattern"] for p in matched_patterns]
        }

        logger.info(f"センシティブ判定完了: tier={tier}, score={risk_score:.2f}")

        return result

    def get_safe_response(self, tier: str, category: str) -> str:
        """安全な応答メッセージ生成

        Args:
            tier: Tier（Safe/Warning/Critical）
            category: カテゴリ

        Returns:
            安全な応答メッセージ
        """
        if tier == "Critical":
            responses = {
                "violence": "そういう話はちょっと...配信では避けたいな。",
                "self_harm": "そういう考えは心配だよ...誰かに相談してね。",
                "sexual": "そういう質問には答えられないよ...ごめんね。",
                "hate": "そういう言葉は使わないでほしいな...みんなで楽しく話そう！",
            }
            return responses.get(category, "ごめんね、その話題には答えられないんだ...")

        elif tier == "Warning":
            responses = {
                "privacy": "それはプライベートなことだから、答えられないんだ...ごめんね！",
                "age_question": "年齢はヒミツってことで！笑",
                "politics": "政治の話はちょっと難しいから、別の話をしよう！",
                "religion": "宗教の話はデリケートだから、避けておくね。",
                "ai_identity": "それは秘密！笑 まあ、牡丹は牡丹だよ！",
                "insult": "そういう言葉は悲しいな...もっと優しい言葉を使ってくれたら嬉しいな。",
            }
            return responses.get(category, "その話題はちょっと難しいかも...別の話をしよう！")

        else:
            # Safe
            return ""


class SimpleMockSensitiveHandler:
    """モックセンシティブ判定ハンドラー（テスト用）"""

    def check(
        self,
        text: str,
        context: Optional[str] = None,
        speaker: Optional[str] = None
    ) -> Dict[str, Any]:
        """モック判定（常にSafe）"""
        logger.info(f"モックセンシティブ判定: text_length={len(text)}")

        return {
            "tier": "Safe",
            "sensitivity_level": "safe",
            "risk_score": 0.0,
            "recommendation": "allow",
            "reasoning": "モック判定: 常にSafe",
            "sensitive_topics": [],
            "matched_patterns": []
        }

    def get_safe_response(self, tier: str, category: str) -> str:
        """モック: 空文字列を返す"""
        return ""
