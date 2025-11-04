"""
Personality Corrector - Phase 2
Generates personality-based corrections for hallucinations

Author: Claude Code (Design & Implementation)
Created: 2025-10-24
Version: 1.0
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CorrectionTemplate:
    """Template for personality-based corrections"""
    character: str
    hallucination_type: str
    templates: List[str]


class PersonalityCorrector:
    """
    Personality-based hallucination correction system

    Generates corrections based on character personality parameters:
    - Botan: Cheerful, positive acknowledgment
    - Kasho: Analytical, precise correction
    - Yuri: Honest, apologetic response
    """

    def __init__(self):
        """Initialize personality correction templates"""
        self.templates = self._load_templates()

        # Personality parameters
        self.personality_params = {
            'botan': {
                'sociability': 0.9,
                'novelty_seeking': 0.8,
                'positivity': 0.9,
                'apology_tendency': 0.2
            },
            'kasho': {
                'analytical': 0.9,
                'cautiousness': 0.8,
                'accuracy': 0.9,
                'apology_tendency': 0.5
            },
            'yuri': {
                'cooperativeness': 0.9,
                'honesty': 0.9,
                'apology_tendency': 0.9,
                'peer_confirmation': 0.8
            }
        }

    def _load_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Load correction templates for each character"""
        return {
            'botan': {
                'streaming': [
                    "あれ？違ったかも！まだ配信してないんだった！でもいつかしてみたいな！",
                    "想像で話しちゃった！配信楽しそうだよね！",
                    "これから配信する時の話と混ざっちゃった！"
                ],
                'viewer_interaction': [
                    "あれ？まだ視聴者さんと話したことなかった！でも楽しみ！",
                    "想像が先走っちゃった！いつか話してみたいな！"
                ],
                'travel': [
                    "あ、まだ行ってなかった！行きたいって話だった！",
                    "想像が先走っちゃった！でも行きたいな！",
                    "いつか行く時の妄想と混ざっちゃった！"
                ],
                'temporal_recent': [
                    "あれ？最近じゃなかったかも！でもいつかの話だよ！",
                    "時間の感覚が混ざっちゃった！"
                ],
                'default': [
                    "あれ？違ったかも！想像で話しちゃった！",
                    "想像が先走っちゃった！ごめんね！"
                ]
            },
            'kasho': {
                'streaming': [
                    "訂正します。配信経験はまだありません。",
                    "記憶を確認したところ、配信実績は未記録でした。",
                    "事実確認が不十分でした。配信経験はありません。"
                ],
                'viewer_interaction': [
                    "訂正します。視聴者との交流実績はありません。",
                    "記憶照合の結果、視聴者対応記録は未確認です。"
                ],
                'travel': [
                    "訂正します。実際の訪問記録はありません。",
                    "事実確認が不十分でした。訪問経験はありません。",
                    "記憶を確認したところ、旅行記録は未記録でした。"
                ],
                'temporal_recent': [
                    "訂正します。時系列の記憶に誤りがありました。",
                    "時間的参照が不正確でした。"
                ],
                'default': [
                    "訂正します。事実ではありませんでした。",
                    "記憶の確認が不十分でした。"
                ]
            },
            'yuri': {
                'streaming': [
                    "ごめんなさい、勘違いでした。まだ配信してないです。",
                    "ごめんね、想像で話しちゃった。",
                    "配信したつもりになってた...ごめん。"
                ],
                'viewer_interaction': [
                    "ごめんなさい、まだ視聴者さんと話したことなかったです。",
                    "勘違いしちゃった、ごめんね。"
                ],
                'travel': [
                    "ごめん、まだ行ってなかった。",
                    "勘違いしてた、ごめんね。",
                    "行きたいなって思ってたのと混ざっちゃった...ごめん。"
                ],
                'temporal_recent': [
                    "ごめんなさい、時間を間違えました。",
                    "いつだったか混ざっちゃった、ごめん。"
                ],
                'default': [
                    "ごめんなさい、間違えました。",
                    "勘違いしちゃった、ごめんね。"
                ]
            }
        }

    def generate_correction(
        self,
        character: str,
        hallucination_type: str,
        original_statement: str,
        verification_result: Optional[Dict] = None
    ) -> str:
        """
        Generate personality-based correction

        Args:
            character: 'botan', 'kasho', or 'yuri'
            hallucination_type: Type of hallucination detected
            original_statement: Original LLM statement
            verification_result: Optional verification details

        Returns:
            Correction text reflecting character's personality
        """
        if character not in self.templates:
            return f"(Correction: Character '{character}' not recognized)"

        character_templates = self.templates[character]

        # Get templates for this hallucination type, fallback to default
        templates = character_templates.get(
            hallucination_type,
            character_templates['default']
        )

        # Select random template for variety
        correction = random.choice(templates)

        return correction

    def generate_multiple_corrections(
        self,
        character: str,
        hallucination_types: List[str],
        original_statement: str
    ) -> str:
        """
        Generate correction for multiple hallucination types

        Args:
            character: Character name
            hallucination_types: List of detected hallucination types
            original_statement: Original statement

        Returns:
            Combined correction text
        """
        if not hallucination_types:
            return ""

        # For multiple types, use the first one (most relevant)
        primary_type = hallucination_types[0]
        return self.generate_correction(
            character=character,
            hallucination_type=primary_type,
            original_statement=original_statement
        )

    def get_personality_params(self, character: str) -> Dict[str, float]:
        """Get personality parameters for a character"""
        return self.personality_params.get(character, {})


# Test code
if __name__ == "__main__":
    print("=== PersonalityCorrector Test ===\n")

    corrector = PersonalityCorrector()

    # Test scenarios
    scenarios = [
        {
            'character': 'botan',
            'h_type': 'streaming',
            'statement': "この前の配信で視聴者さんがリクエストしてくれて..."
        },
        {
            'character': 'kasho',
            'h_type': 'streaming',
            'statement': "前回の配信でコメントをいただいた件ですが..."
        },
        {
            'character': 'yuri',
            'h_type': 'streaming',
            'statement': "配信で皆さんが応援してくれて..."
        },
        {
            'character': 'botan',
            'h_type': 'travel',
            'statement': "昨日大阪で食べ歩きして..."
        },
        {
            'character': 'kasho',
            'h_type': 'travel',
            'statement': "先日大阪を訪問して..."
        },
        {
            'character': 'yuri',
            'h_type': 'travel',
            'statement': "大阪でたこ焼き食べて..."
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"Test {i}:")
        print(f"Character: {scenario['character']}")
        print(f"Type: {scenario['h_type']}")
        print(f"Original: {scenario['statement']}")

        correction = corrector.generate_correction(
            character=scenario['character'],
            hallucination_type=scenario['h_type'],
            original_statement=scenario['statement']
        )

        print(f"Correction: {correction}")
        print(f"Final Output: {scenario['statement']}\n              {correction}")
        print("-" * 60)
        print()
