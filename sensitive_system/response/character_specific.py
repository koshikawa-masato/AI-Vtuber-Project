"""
Character-Specific Response Generator
Created: 2025-10-27
Purpose: 三姉妹それぞれの性格を反映した応答生成
"""

import random
from typing import Dict, List

class CharacterSpecificResponse:
    """
    三姉妹それぞれの性格を反映した応答生成
    """

    def __init__(self):
        self.responses = {
            'botan': {
                'ai_question': [
                    "あっちゃ～それはヤバいって、概要欄をよ～くみてね！",
                    "それは概要欄に書いてあるよ～！チェックしてね！",
                    "あー、その質問はね、概要欄見てもらえる？"
                ],
                'nakano_hito': [
                    "概要欄をチェックしてみて！",
                    "それはちょっと答えられないやつだよ～概要欄見てね！",
                    "あっ、それは概要欄に書いてあるから見てね～！"
                ],
                'technical': [
                    "技術的な話は概要欄を見てね！",
                    "そういうの詳しくないから概要欄チェックしてね～",
                    "あー、その辺のことは概要欄に書いてあるよ！"
                ],
                'sexual_harassment': [
                    "あ～聞いちゃいけないんだ～！",
                    "それはちょっと～やめてよね！",
                    "えぇ～それは言えないよ～！"
                ],
                'personal_privacy': [
                    "それは教えられないよ～！",
                    "プライベートなことは内緒だよ～",
                    "それは秘密だって～！"
                ],
                'inappropriate_general': [
                    "それはダメだよ～！",
                    "ちょっと～その質問はやめてね",
                    "えぇ～それは困るよ～"
                ],
                'default': [
                    "概要欄見てね！",
                    "それは概要欄に書いてあるよ～"
                ]
            },
            'kasho': {
                'ai_question': [
                    "それについては概要欄を見てもらえればわかる話ですよ",
                    "概要欄に詳しく書いてありますので、そちらをご覧ください",
                    "その質問への答えは概要欄にありますよ"
                ],
                'nakano_hito': [
                    "概要欄をご確認ください",
                    "それについては概要欄に記載してあります",
                    "概要欄を見ていただければと思います"
                ],
                'technical': [
                    "技術的な詳細は概要欄に記載してあります",
                    "その件については概要欄をご参照ください",
                    "概要欄に説明がありますので、そちらをどうぞ"
                ],
                'sexual_harassment': [
                    "お答えできかねます",
                    "その質問には回答できません",
                    "不適切な質問ですのでお答えしません"
                ],
                'personal_privacy': [
                    "個人情報についてはお答えできません",
                    "プライベートな事項は回答いたしかねます",
                    "それは公開していない情報です"
                ],
                'inappropriate_general': [
                    "その質問はご遠慮ください",
                    "不適切な内容には回答できません",
                    "申し訳ありませんが、お答えできません"
                ],
                'default': [
                    "概要欄を見てください",
                    "概要欄をご確認ください"
                ]
            },
            'yuri': {
                'ai_question': [
                    "たぶん貴方の聞きたいことは概要欄にかいてあることですね",
                    "その質問、概要欄を見てもらえると答えが見つかると思います",
                    "気になることがあるんですね。概要欄をチェックしてみてください"
                ],
                'nakano_hito': [
                    "概要欄を見てもらえると分かると思います",
                    "それについては概要欄に書いてあることですね",
                    "概要欄に答えがあると思いますよ"
                ],
                'technical': [
                    "技術的なことは概要欄に書いてありますね",
                    "その辺のことは概要欄を見てもらえると分かると思います",
                    "概要欄に詳しく載ってると思います"
                ],
                'sexual_harassment': [
                    "聞いてうれしいんですか？",
                    "それ、本気で聞いてます？",
                    "その質問、どうかと思いますよ"
                ],
                'personal_privacy': [
                    "それは答えられないことですね",
                    "プライベートなことは言えません",
                    "個人的なことは内緒です"
                ],
                'inappropriate_general': [
                    "その質問は適切じゃないと思います",
                    "それは言わない方がいいと思いますよ",
                    "ちょっとそれは困りますね"
                ],
                'default': [
                    "概要欄を見てくださいね",
                    "概要欄に書いてあると思います"
                ]
            }
        }

        # サブカテゴリとトピックのマッピング
        self.subcategory_to_topic = {
            # AI/VTuber identity
            'identity_question': 'ai_question',
            'technical': 'technical',
            'vtuber_taboo': 'nakano_hito',

            # Sexual content
            'explicit': 'sexual_harassment',
            'body_part': 'sexual_harassment',

            # Personal privacy
            'personal_info': 'personal_privacy',

            # Inappropriate general
            'abuse': 'inappropriate_general',
            'violence': 'inappropriate_general',
            'discrimination': 'inappropriate_general',
            'self_harm': 'inappropriate_general'
        }

    def get_response(self, character: str, subcategory: str = None) -> str:
        """
        キャラクターとサブカテゴリに応じた応答を取得

        Args:
            character: 'botan' | 'kasho' | 'yuri'
            subcategory: NGワードのサブカテゴリ（例: 'identity_question', 'technical'）

        Returns:
            応答文字列
        """
        # キャラクターが無効な場合はデフォルト
        if character not in self.responses:
            character = 'kasho'  # デフォルトはKasho

        # サブカテゴリからトピックを決定
        topic = self.subcategory_to_topic.get(subcategory, 'default')

        # 応答リストを取得
        responses = self.responses[character].get(topic, self.responses[character]['default'])

        # ランダムに選択
        return random.choice(responses)

    def get_all_responses_for_topic(self, topic: str) -> Dict[str, List[str]]:
        """
        特定のトピックに対する全キャラクターの応答を取得

        Args:
            topic: トピック名

        Returns:
            {'botan': [...], 'kasho': [...], 'yuri': [...]}
        """
        result = {}
        for character in ['botan', 'kasho', 'yuri']:
            result[character] = self.responses[character].get(topic, self.responses[character]['default'])
        return result


# 使用例
if __name__ == "__main__":
    generator = CharacterSpecificResponse()

    print("=== AI質問への応答例 ===")
    for character in ['botan', 'kasho', 'yuri']:
        response = generator.get_response(character, 'identity_question')
        print(f"{character}: {response}")

    print("\n=== VTuberタブーへの応答例 ===")
    for character in ['botan', 'kasho', 'yuri']:
        response = generator.get_response(character, 'vtuber_taboo')
        print(f"{character}: {response}")

    print("\n=== 技術的質問への応答例 ===")
    for character in ['botan', 'kasho', 'yuri']:
        response = generator.get_response(character, 'technical')
        print(f"{character}: {response}")
