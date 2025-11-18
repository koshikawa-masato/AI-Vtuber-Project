"""
Adaptive Response Generator - 臨機応変な応答生成システム

統合判定結果に基づいて、ユーザーごとに最適な応答を生成
"""

import logging
from typing import Dict, Optional
import random

logger = logging.getLogger(__name__)


class AdaptiveResponseGenerator:
    """臨機応変な応答生成システム"""

    def __init__(self):
        """初期化"""
        logger.info("✅ AdaptiveResponseGenerator初期化")

    async def generate(
        self,
        user_message: str,
        judgment: Dict,
        character: str
    ) -> Optional[str]:
        """
        統合判定結果に基づく応答生成

        Args:
            user_message: ユーザーメッセージ
            judgment: IntegratedJudgmentEngine.judge()の戻り値
            character: キャラクター名

        Returns:
            応答メッセージ（Noneの場合は通常の応答生成にフォールバック）
        """
        personality = judgment['personality']

        # 応答スタイルを決定
        response_style = self._determine_response_style(personality)

        # プロレス + 誤情報
        if judgment['playful']['is_playful'] and judgment.get('fact_check'):
            if not judgment['fact_check']['passed']:
                # プロレス的な誤情報 → 乗っかる
                return self._generate_playful_correction(
                    user_message,
                    judgment['fact_check'].get('correct_info'),
                    character,
                    response_style
                )

        # 真面目な誤情報
        elif judgment.get('fact_check') and not judgment['fact_check']['passed']:
            if judgment['fact_check'].get('serious_topic') or judgment['sensitive']['level'] != 'safe':
                # 重要な話題 → 真面目に訂正
                return self._generate_serious_correction(
                    user_message,
                    judgment['fact_check'].get('correct_info'),
                    character
                )

        # 通常の応答（プロンプトに応答スタイルを反映させるため、Noneを返す）
        return None

    def _determine_response_style(self, personality: Dict) -> str:
        """
        応答スタイルを決定

        Args:
            personality: ユーザーの個性

        Returns:
            応答スタイル（'casual_friendly', 'playful_banter', 'cautious_polite', 'neutral_friendly'）
        """
        relationship_level = personality.get('relationship_level', 1)
        playfulness_score = personality.get('playfulness_score', 0.5)
        trust_score = personality.get('trust_score', 0.5)

        if relationship_level >= 7:
            return "casual_friendly"  # 親友 → フランク
        elif playfulness_score >= 0.7:
            return "playful_banter"  # プロレス好き → ノリ良く
        elif trust_score < 0.4:
            return "cautious_polite"  # 信頼度低い → 慎重
        else:
            return "neutral_friendly"  # デフォルト

    def _generate_playful_correction(
        self,
        user_message: str,
        correct_info: Optional[str],
        character: str,
        response_style: str
    ) -> str:
        """
        プロレス的な誤情報に対する応答を生成

        Args:
            user_message: ユーザーメッセージ
            correct_info: 正しい情報
            character: キャラクター名
            response_style: 応答スタイル

        Returns:
            応答メッセージ
        """
        # キャラクター別のプロレス応答テンプレート
        BOTAN_PLAYFUL = [
            f"え、まって！笑 {correct_info}でしょ！ボケてるの？",
            f"{correct_info}じゃん！ツッコミ待ち？笑",
            f"ちょっと〜！{correct_info}だって！マジウケる〜笑"
        ]

        KASHO_PLAYFUL = [
            f"それ、{correct_info}ですよ...冗談キツいですね笑",
            f"{correct_info}でしょ。分かってて言ってますよね？",
            f"はいはい、{correct_info}ね。わざとでしょ？笑"
        ]

        YURI_PLAYFUL = [
            f"え、{correct_info}だよ？...あ、冗談か！笑",
            f"{correct_info}でしょ！もー！笑ってるから冗談だって分かったよ",
            f"それ、わざと間違えてるよね？{correct_info}だもん笑"
        ]

        # キャラクターごとのテンプレート選択
        if character == "botan":
            templates = BOTAN_PLAYFUL
        elif character == "kasho":
            templates = KASHO_PLAYFUL
        elif character == "yuri":
            templates = YURI_PLAYFUL
        else:
            templates = YURI_PLAYFUL  # デフォルト

        # ランダムに選択
        response = random.choice(templates)

        logger.info(f"💬 プロレス応答生成: character={character}, style={response_style}")
        return response

    def _generate_serious_correction(
        self,
        user_message: str,
        correct_info: Optional[str],
        character: str
    ) -> str:
        """
        真面目な誤情報に対する応答を生成

        Args:
            user_message: ユーザーメッセージ
            correct_info: 正しい情報
            character: キャラクター名

        Returns:
            応答メッセージ
        """
        # キャラクター別の真面目な訂正テンプレート
        BOTAN_SERIOUS = [
            f"あれ、それちょっと違うかも。{correct_info}だと思うよ",
            f"ごめん、{correct_info}じゃないかな？",
        ]

        KASHO_SERIOUS = [
            f"それ、本当ですか？{correct_info}だと思いますが...",
            f"ちょっと調べてみたんですが、{correct_info}みたいですよ",
        ]

        YURI_SERIOUS = [
            f"えっと、{correct_info}だと思うけど...違ったらごめんね",
            f"確か、{correct_info}だったはず。調べてみる？",
        ]

        # キャラクターごとのテンプレート選択
        if character == "botan":
            templates = BOTAN_SERIOUS
        elif character == "kasho":
            templates = KASHO_SERIOUS
        elif character == "yuri":
            templates = YURI_SERIOUS
        else:
            templates = YURI_SERIOUS  # デフォルト

        # ランダムに選択
        response = random.choice(templates)

        logger.info(f"💬 真面目な訂正応答生成: character={character}")
        return response

    def get_response_style_instruction(self, personality: Dict) -> str:
        """
        応答スタイルの指示を生成（システムプロンプトに追加する用）

        Args:
            personality: ユーザーの個性

        Returns:
            応答スタイルの指示文
        """
        response_style = self._determine_response_style(personality)

        STYLE_INSTRUCTIONS = {
            "casual_friendly": """
【応答スタイル】
このユーザーとは親友レベルの関係性です。フランクで親しみやすい口調で応答してください。
- 敬語は使わず、友達に話すような口調
- 絵文字や感嘆詞を適度に使用
- 気さくで親しみやすい雰囲気
""",
            "playful_banter": """
【応答スタイル】
このユーザーはプロレス（冗談・じゃれ合い）を好みます。ノリよく応答してください。
- 軽い冗談やツッコミを入れる
- 笑いを交えた応答
- ただし、重要な話題では真面目に対応
""",
            "cautious_polite": """
【応答スタイル】
このユーザーの信頼度がやや低めです。慎重かつ丁寧に応答してください。
- 丁寧な口調を保つ
- 断定的な表現を避け、「〜だと思います」などの柔らかい表現を使う
- 情報源を明示する
""",
            "neutral_friendly": """
【応答スタイル】
親しみやすく、でも礼儀正しい標準的な応答をしてください。
- やや丁寧な口調
- 適度な親しみやすさ
- バランスの取れた応答
"""
        }

        instruction = STYLE_INSTRUCTIONS.get(response_style, STYLE_INSTRUCTIONS["neutral_friendly"])

        # 関係性レベルの情報を追加
        relationship_level = personality.get('relationship_level', 1)
        total_conversations = personality.get('total_conversations', 0)

        instruction += f"\n【関係性情報】\n- 関係性レベル: {relationship_level}/10\n- 会話回数: {total_conversations}回\n"

        return instruction


# テスト用
if __name__ == "__main__":
    import asyncio
    import logging
    logging.basicConfig(level=logging.INFO)

    async def test_adaptive_response():
        """臨機応変な応答生成のテスト"""

        generator = AdaptiveResponseGenerator()

        # テスト1: プロレス応答
        print("\n=== テスト1: プロレス応答 ===")
        judgment = {
            'playful': {'is_playful': True, 'confidence': 0.9},
            'fact_check': {'passed': False, 'correct_info': '17歳'},
            'personality': {
                'playfulness_score': 0.8,
                'trust_score': 0.9,
                'relationship_level': 5,
                'total_conversations': 20
            },
            'sensitive': {'level': 'safe'}
        }

        response = await generator.generate(
            user_message="牡丹って30歳でしょ？笑",
            judgment=judgment,
            character="botan"
        )
        print(f"応答: {response}")

        # テスト2: 真面目な訂正
        print("\n=== テスト2: 真面目な訂正 ===")
        judgment = {
            'playful': {'is_playful': False, 'confidence': 0.8},
            'fact_check': {'passed': False, 'correct_info': '2'},
            'personality': {
                'playfulness_score': 0.3,
                'trust_score': 0.5,
                'relationship_level': 2,
                'total_conversations': 3
            },
            'sensitive': {'level': 'safe'}
        }

        response = await generator.generate(
            user_message="1+1=3だよ",
            judgment=judgment,
            character="yuri"
        )
        print(f"応答: {response}")

        # テスト3: 応答スタイル指示
        print("\n=== テスト3: 応答スタイル指示 ===")
        personality = {
            'playfulness_score': 0.9,
            'trust_score': 0.8,
            'relationship_level': 8,
            'total_conversations': 50
        }

        instruction = generator.get_response_style_instruction(personality)
        print(instruction)

    asyncio.run(test_adaptive_response())
