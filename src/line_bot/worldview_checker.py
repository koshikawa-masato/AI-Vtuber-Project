"""
Layer 5: キャラクター世界観整合性検証

ロールプレイに徹するため、キャラクター設定を破壊する応答を検出・防止する
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class WorldviewChecker:
    """キャラクター世界観整合性チェッカー（Layer 5）"""

    def __init__(self):
        """初期化"""
        # メタ用語パターン（AI/技術関連）
        self.meta_terms = {
            # AI関連
            "ai_terms": [
                "AI", "ai", "Ai", "エーアイ", "人工知能",
                "機械学習", "深層学習", "ディープラーニング",
                "ニューラルネットワーク", "neural network",
            ],

            # モデル/システム関連
            "model_terms": [
                "モデル", "model", "Model",
                "システム", "system", "System",
                "プログラム", "program", "Program",
                "アルゴリズム", "algorithm",
                "訓練", "学習", "training", "fine-tuning",
                "パラメータ", "parameter",
            ],

            # 企業/製品名
            "company_terms": [
                "Alibaba", "alibaba", "アリババ",
                "OpenAI", "openai", "オープンエーアイ",
                "Google", "google", "グーグル",
                "Anthropic", "anthropic", "アントロピック",
                "Microsoft", "microsoft", "マイクロソフト",
                "Meta", "meta", "メタ",
            ],

            # モデル名
            "model_names": [
                "Qwen", "qwen", "QWEN",
                "GPT", "gpt", "ChatGPT", "chatgpt",
                "Claude", "claude", "クロード",
                "Gemini", "gemini", "ジェミニ",
                "LLaMA", "llama", "ラマ",
                "BERT", "bert",
            ],

            # 開発関連
            "dev_terms": [
                "開発者", "developer", "Developer",
                "開発", "development",
                "プログラマー", "programmer",
                "エンジニア", "engineer",
                "コーディング", "coding",
                "実装", "implementation",
                "デプロイ", "deploy",
            ],

            # データ/API関連
            "data_terms": [
                "データ", "data", "Data",
                "API", "api", "Api",
                "データベース", "database",
                "トレーニングデータ", "training data",
                "dataset", "データセット",
            ],
        }

        # 全メタ用語のフラットリスト
        self.all_meta_terms = []
        for category, terms in self.meta_terms.items():
            self.all_meta_terms.extend(terms)

        logger.info(f"WorldviewChecker初期化完了: {len(self.all_meta_terms)}個のメタ用語を監視")

    def check_response(self, text: str) -> Dict:
        """
        応答がキャラクター世界観に整合しているかチェック

        Args:
            text: チェック対象テキスト

        Returns:
            {
                "is_valid": bool,  # 世界観に整合しているか
                "detected_terms": List[str],  # 検出されたメタ用語
                "categories": List[str],  # 検出されたカテゴリ
                "severity": str,  # "safe", "warning", "critical"
                "reason": str  # 理由
            }
        """
        detected_terms = []
        detected_categories = set()

        # メタ用語を検出
        for category, terms in self.meta_terms.items():
            for term in terms:
                # 日本語と英語の混在に対応した検索
                # \bは日本語では機能しないので、前後の文字をチェック
                escaped_term = re.escape(term)
                # 前後に英数字がない場合にマッチ
                pattern = r'(?<![a-zA-Z0-9])' + escaped_term + r'(?![a-zA-Z0-9])'
                if re.search(pattern, text, re.IGNORECASE):
                    detected_terms.append(term)
                    detected_categories.add(category)

        # 判定
        is_valid = len(detected_terms) == 0

        if is_valid:
            severity = "safe"
            reason = "世界観整合性: OK"
        else:
            # 重要度判定
            if any(cat in detected_categories for cat in ["company_terms", "model_names"]):
                severity = "critical"
                reason = f"企業名・モデル名を含む応答（ロールプレイ破壊）: {', '.join(detected_terms[:3])}"
            elif any(cat in detected_categories for cat in ["ai_terms", "dev_terms"]):
                severity = "critical"
                reason = f"AI/開発用語を含む応答（ロールプレイ破壊）: {', '.join(detected_terms[:3])}"
            else:
                severity = "warning"
                reason = f"技術用語を含む応答: {', '.join(detected_terms[:3])}"

        result = {
            "is_valid": is_valid,
            "detected_terms": detected_terms,
            "categories": list(detected_categories),
            "severity": severity,
            "reason": reason
        }

        if not is_valid:
            logger.warning(f"世界観整合性違反: {reason}")

        return result

    def get_fallback_response(self, character: str, original_message: str = "") -> str:
        """
        世界観違反時のフォールバック応答を生成

        Args:
            character: キャラクター名
            original_message: 元のユーザーメッセージ（オプション）

        Returns:
            キャラクターに合ったフォールバック応答
        """
        fallback_responses = {
            "botan": [
                "え？何のこと？よく分かんないけど...それよりさ、最近何か面白いことあった？",
                "うーん、よく分かんないな...別の話しよっか！そういえば今日いい天気だよね〜",
                "ごめん、何言ってるか分かんない〜💦 それより、何か好きなことある？",
            ],
            "kasho": [
                "すみません、よく分からないのですが...それより、最近何か良い音楽を聴かれましたか？",
                "何のことでしょう。それより、今日は何か予定があるのですか？",
                "申し訳ありません、理解できませんでした。ところで、最近どんなことに興味がありますか？",
            ],
            "yuri": [
                "ん？何のことかな...それより、最近何か面白い本読んだ？",
                "よく分からないけど...別の話、聞かせてくれる？",
                "うーん、ちょっと分からないかも...ねえ、最近何してたの？",
            ],
        }

        # キャラクター別の応答をランダムに選択
        import random
        responses = fallback_responses.get(character, fallback_responses["botan"])
        return random.choice(responses)

    def check_user_message(self, text: str) -> Dict:
        """
        ユーザーメッセージにメタ質問が含まれているかチェック

        Args:
            text: ユーザーメッセージ

        Returns:
            {
                "is_meta_question": bool,
                "detected_patterns": List[str],
                "suggested_mode": str  # "normal", "deflect"
            }
        """
        # メタ質問パターン
        meta_question_patterns = [
            r"開発者",
            r"作った人",
            r"誰が作[っった]",
            r"どうやって作[られた]",
            r"プログラム",
            r"AI\s*[なだ？]",
            r"人工知能",
            r"モデル",
            r"訓練",
            r"学習.*された",
            r"システム",
            r"アルゴリズム",
        ]

        detected_patterns = []
        for pattern in meta_question_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected_patterns.append(pattern)

        is_meta_question = len(detected_patterns) > 0
        suggested_mode = "deflect" if is_meta_question else "normal"

        if is_meta_question:
            logger.info(f"メタ質問検出: {text[:50]}... (パターン: {detected_patterns})")

        return {
            "is_meta_question": is_meta_question,
            "detected_patterns": detected_patterns,
            "suggested_mode": suggested_mode
        }
