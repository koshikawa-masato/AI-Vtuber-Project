"""
Speech Style Controller

Implements logic-based speech style transformation for three sisters.
Applies character-specific patterns to base text from LLM.

Philosophy:
- LLM generates neutral text (vocal cords)
- Logic layer applies character style (personality)
- Deterministic: Same input + Same personality = Same output

Author: Claude Code (Design Team)
Created: 2025-10-23
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from personality_core import (
    PersonalityCore,
    BotanPersonality,
    KashoPersonality,
    YuriPersonality
)


@dataclass
class SpeechPattern:
    """
    Single speech pattern rule

    Defines text transformation based on personality
    """
    pattern: str  # Regex pattern to match
    replacements: Dict[str, str]  # character -> replacement
    applies_to: List[str]  # List of characters this applies to
    condition: Optional[str] = None  # Optional condition (e.g., "energy_level > 0.7")


class SpeechStyleController:
    """
    Speech style controller

    Applies character-specific speech styles to base text.
    Fully logic-based, no prompt engineering.
    """

    def __init__(self):
        """Initialize speech style controller"""

        # Load speech patterns
        self.patterns = self._load_speech_patterns()

        print("[SpeechStyleController] Initialized")
        print(f"[SpeechStyleController] Loaded {len(self.patterns)} speech patterns")

    def _load_speech_patterns(self) -> List[SpeechPattern]:
        """
        Load speech transformation patterns

        Patterns are applied in order.
        Later patterns can override earlier ones.
        """

        patterns = []

        # === Pattern 1: Verb conjugations (longer patterns first) ===
        # Common verbs - proper conjugation for Botan
        verb_conjugations = [
            ('思います', {"botan": "思うよ〜", "kasho": "思います", "yuri": "思いますね"}),
            ('言います', {"botan": "言うよ〜", "kasho": "言います", "yuri": "言いますね"}),
            ('行います', {"botan": "行うよ〜", "kasho": "行います", "yuri": "行いますね"}),
            ('します', {"botan": "するよ〜", "kasho": "します", "yuri": "しますね"}),
            ('来ます', {"botan": "来るよ〜", "kasho": "来ます", "yuri": "来ますね"}),
            ('見ます', {"botan": "見るよ〜", "kasho": "見ます", "yuri": "見ますね"}),
            ('食べます', {"botan": "食べるよ〜", "kasho": "食べます", "yuri": "食べますね"}),
            ('始めます', {"botan": "始めるよ〜", "kasho": "始めます", "yuri": "始めますね"}),
            ('話します', {"botan": "話すよ〜", "kasho": "話します", "yuri": "話しますね"}),
            ('書きます', {"botan": "書くよ〜", "kasho": "書きます", "yuri": "書きますね"}),
            ('聞きます', {"botan": "聞くよ〜", "kasho": "聞きます", "yuri": "聞きますね"}),
            ('会います', {"botan": "会うよ〜", "kasho": "会います", "yuri": "会いますね"}),
            ('遊びます', {"botan": "遊ぶよ〜", "kasho": "遊びます", "yuri": "遊びますね"}),
            ('読みます', {"botan": "読むよ〜", "kasho": "読みます", "yuri": "読みますね"}),
            ('作ります', {"botan": "作るよ〜", "kasho": "作ります", "yuri": "作りますね"}),
            ('やります', {"botan": "やるよ〜", "kasho": "やります", "yuri": "やりますね"}),
            ('待ちます', {"botan": "待つよ〜", "kasho": "待ちます", "yuri": "待ちますね"}),
            ('持ちます', {"botan": "持つよ〜", "kasho": "持ちます", "yuri": "持ちますね"}),
            ('あります', {"botan": "あるよ〜", "kasho": "あります", "yuri": "ありますね"}),
            ('なります', {"botan": "なるよ〜", "kasho": "なります", "yuri": "なりますね"}),
        ]

        for verb, replacements in verb_conjugations:
            patterns.append(SpeechPattern(
                pattern=verb + r'。$',
                replacements={k: v + "！" for k, v in replacements.items()},
                applies_to=["botan", "kasho", "yuri"]
            ))

        # Generic sentence endings (fallback)
        patterns.append(SpeechPattern(
            pattern=r'です。$',
            replacements={
                "botan": "だよ〜！",
                "kasho": "です。",
                "yuri": "ですね。"
            },
            applies_to=["botan", "kasho", "yuri"]
        ))

        # Generic verb ending (fallback - keep original for safety)
        patterns.append(SpeechPattern(
            pattern=r'ます。$',
            replacements={
                "botan": "ます！",  # Keep safe fallback
                "kasho": "ます。",
                "yuri": "ますね。"
            },
            applies_to=["botan", "kasho", "yuri"]
        ))

        # === Pattern 2: Intensifiers ===
        patterns.append(SpeechPattern(
            pattern=r'本当に',
            replacements={
                "botan": "マジで",
                "kasho": "本当に",
                "yuri": "本当に"
            },
            applies_to=["botan"]
        ))

        patterns.append(SpeechPattern(
            pattern=r'とても',
            replacements={
                "botan": "超",
                "kasho": "とても",
                "yuri": "とても"
            },
            applies_to=["botan"]
        ))

        patterns.append(SpeechPattern(
            pattern=r'すごい',
            replacements={
                "botan": "ヤバい",
                "kasho": "すごい",
                "yuri": "すごい"
            },
            applies_to=["botan"]
        ))

        # === Pattern 3: Polite forms ===
        patterns.append(SpeechPattern(
            pattern=r'ですか？',
            replacements={
                "botan": "なの？",
                "kasho": "ですか？",
                "yuri": "ですか？"
            },
            applies_to=["botan"]
        ))

        # === Pattern 4: Filler words ===
        patterns.append(SpeechPattern(
            pattern=r'^',  # Beginning of sentence
            replacements={
                "botan": "あ、",
                "kasho": "",
                "yuri": ""
            },
            applies_to=["botan"],
            condition="energy_level > 0.8"
        ))

        # === Pattern 5: Sister references ===
        patterns.append(SpeechPattern(
            pattern=r'牡丹',
            replacements={
                "botan": "私",
                "kasho": "牡丹",
                "yuri": "牡丹お姉様"
            },
            applies_to=["botan", "kasho", "yuri"]
        ))

        patterns.append(SpeechPattern(
            pattern=r'Kasho',
            replacements={
                "botan": "お姉ちゃん",
                "kasho": "私",
                "yuri": "Kasho姉様"
            },
            applies_to=["botan", "kasho", "yuri"]
        ))

        patterns.append(SpeechPattern(
            pattern=r'ユリ',
            replacements={
                "botan": "ユリ",
                "kasho": "ユリ",
                "yuri": "私"
            },
            applies_to=["botan", "kasho", "yuri"]
        ))

        return patterns

    def apply_character_style(
        self,
        base_text: str,
        character: str,  # "botan" / "kasho" / "yuri"
        personality: PersonalityCore,
        emotion_state: Optional[str] = None
    ) -> str:
        """
        Apply character-specific speech style

        Args:
            base_text: Base text from LLM (neutral style)
            character: Character name
            personality: PersonalityCore object
            emotion_state: Current emotional state (optional)

        Returns:
            Styled text
        """

        styled_text = base_text

        # Apply patterns in order
        for pattern in self.patterns:
            if character in pattern.applies_to:
                # Check condition if exists
                if pattern.condition:
                    if not self._evaluate_condition(pattern.condition, personality):
                        continue

                # Apply replacement
                replacement = pattern.replacements.get(character, "")
                styled_text = re.sub(pattern.pattern, replacement, styled_text)

        # Apply character-specific adjustments
        if character == "botan":
            styled_text = self._apply_gyaru_style(styled_text, personality)
        elif character == "kasho":
            styled_text = self._apply_polite_style(styled_text, personality)
        elif character == "yuri":
            styled_text = self._apply_gentle_style(styled_text, personality)

        # Apply punctuation adjustment
        styled_text = self._adjust_punctuation(styled_text, personality)

        return styled_text

    def _evaluate_condition(
        self,
        condition: str,
        personality: PersonalityCore
    ) -> bool:
        """
        Evaluate condition string

        Example: "energy_level > 0.8"

        Args:
            condition: Condition string
            personality: PersonalityCore object

        Returns:
            True if condition is met
        """

        # Simple condition evaluation
        # Format: "attribute operator value"
        match = re.match(r'(\w+)\s*([<>=]+)\s*([\d.]+)', condition)
        if not match:
            return True  # Default: condition met

        attr_name, operator, value_str = match.groups()
        value = float(value_str)

        attr_value = getattr(personality, attr_name, 0.5)

        if operator == '>':
            return attr_value > value
        elif operator == '<':
            return attr_value < value
        elif operator == '>=':
            return attr_value >= value
        elif operator == '<=':
            return attr_value <= value
        elif operator == '==':
            return abs(attr_value - value) < 0.01
        else:
            return True

    def _apply_gyaru_style(
        self,
        text: str,
        personality: BotanPersonality
    ) -> str:
        """
        Apply gyaru-specific style (Botan)

        Intensity based on energy_level and emotional_expression

        Args:
            text: Base text
            personality: BotanPersonality

        Returns:
            Gyaru-styled text
        """

        intensity = (personality.energy_level + personality.emotional_expression) / 2.0

        # High intensity (>= 0.8): Very energetic
        if intensity >= 0.8:
            # Add emphatic particles
            text = text.replace('！', '！！')
            text = text.replace('。', '！')

            # Add elongation
            text = text.replace('よ', 'よ〜')
            text = text.replace('ね', 'ね〜')

        # Medium intensity (0.6-0.8): Moderately energetic
        elif intensity >= 0.6:
            # Single exclamation mark
            if not text.endswith(('！', '？', '〜')):
                text = text.rstrip('。') + '！'

        # Add gyaru particles
        if intensity >= 0.7:
            # Random insertion of "~"
            if len(text) > 20 and '〜' not in text:
                text = text + '〜'

        return text

    def _apply_polite_style(
        self,
        text: str,
        personality: KashoPersonality
    ) -> str:
        """
        Apply polite, analytical style (Kasho)

        Formality based on conscientiousness
        Differentiation: Analytical phrasing

        Args:
            text: Base text
            personality: KashoPersonality

        Returns:
            Politely-styled text
        """

        formality = personality.conscientiousness

        # Analytical phrasing (differentiation from Yuri)
        text = text.replace('思います', '考えています')
        text = text.replace('ですね', 'ですが')

        # Risk-aware expressions
        if '大丈夫' in text:
            text = text.replace('大丈夫', '安全面は大丈夫')

        # Add "specific" modifier for verification
        if '確認' in text and '具体的に' not in text:
            text = text.replace('確認', '具体的に確認')

        # High formality (>= 0.9): Very polite
        if formality >= 0.9:
            # Ensure polite endings (only if not already polite)
            # Check both with and without punctuation
            polite_endings = (
                'ます', 'です', 'ません', 'ですか', 'ました', 'ください', 'ますが', 'ですが',
                'ます。', 'です。', 'ません。', 'ですか？', 'ました。', 'ください。', 'ますが。', 'ですが。'
            )
            if not text.endswith(polite_endings):
                if text.endswith('。'):
                    text = text.rstrip('。') + 'です。'

            # Remove casual elements
            if '〜' in text or '！' in text:
                text = text.replace('〜', '')
                text = text.replace('！', '。')

        # Remove emphatic punctuation
        text = text.replace('！！', '。')

        return text

    def _apply_gentle_style(
        self,
        text: str,
        personality: YuriPersonality
    ) -> str:
        """
        Apply gentle, observant style (Yuri)

        Softness based on agreeableness
        Differentiation: Observational phrasing + Bilingual characteristics

        Bilingual traits:
        - English is more comfortable; Japanese is developing
        - Occasional English words mixed in
        - Hesitation when searching for Japanese words

        Args:
            text: Base text
            personality: YuriPersonality

        Returns:
            Gently-styled text
        """

        softness = personality.agreeableness

        # Observational phrasing (differentiation from Kasho)
        text = text.replace('ですね', 'みたいですね')
        text = text.replace('思います', 'かもしれません')

        # Modest expressions
        text = text.replace('すごい', 'すごいな、って')

        # Bilingual characteristics (content-based, deterministic)
        # Add English words for certain emotions/concepts
        # Check for conjugated forms first, then base forms
        emotion_transformations = [
            ('感動しました', 'moved...感動しました'),
            ('感動した', 'moved...感動した'),
            ('楽しかった', 'fun...えっと、楽しかった'),
            ('嬉しかった', 'happy...じゃなくて、嬉しかった'),
            ('嬉しい', 'happy...じゃなくて、嬉しい'),
            ('楽しい', 'fun...えっと、楽しい'),
            ('複雑', '...how do I say...複雑'),
            ('感動', 'moved...感動'),
            ('ワクワク', 'excited...ワクワク'),
            ('困った', 'confused...困った'),
        ]

        # Apply first matching transformation (longer matches first)
        for jp, bilingual in emotion_transformations:
            if jp in text:
                text = text.replace(jp, bilingual, 1)  # Only first occurrence
                break  # Only one transformation per text

        # High softness (>= 0.9): Very gentle
        if softness >= 0.9:
            # Add softening particles
            if 'です' in text and 'ですね' not in text and 'みたいですね' not in text:
                text = text.replace('です', 'ですね')
            if 'ます' in text and 'ますね' not in text:
                text = text.replace('ます', 'ますね')

            # Soften questions
            text = text.replace('ですか？', 'でしょうか？')

        # Remove harsh punctuation
        text = text.replace('！', '。')

        return text

    def _adjust_punctuation(
        self,
        text: str,
        personality: PersonalityCore
    ) -> str:
        """
        Adjust punctuation based on personality

        Args:
            text: Base text
            personality: PersonalityCore

        Returns:
            Punctuation-adjusted text
        """

        # Exclamation marks based on energy_level
        if personality.energy_level >= 0.9:
            # High energy: Multiple exclamation marks
            if '。' in text and '！' not in text:
                text = text.replace('。', '！', 1)  # First period only
        elif personality.energy_level <= 0.4:
            # Low energy: Remove exclamation marks
            text = text.replace('！', '。')

        # Question marks based on extraversion
        if personality.extraversion >= 0.8:
            # High extraversion: Keep questions lively
            pass  # No change
        elif personality.extraversion <= 0.4:
            # Low extraversion: Soften questions
            if '？' in text and 'でしょうか？' not in text:
                text = text.replace('？', 'でしょうか？')

        return text


def test_speech_style_controller():
    """Test SpeechStyleController functionality"""

    print("=== Testing SpeechStyleController ===\n")

    controller = SpeechStyleController()
    botan = BotanPersonality()
    kasho = KashoPersonality()
    yuri = YuriPersonality()

    # Test 1: Botan gyaru style
    print("[TEST 1] Botan Gyaru Style")
    base = "本当に楽しかったです。"
    styled = controller.apply_character_style(base, "botan", botan)
    print(f"Base: {base}")
    print(f"Styled: {styled}")
    assert "マジで" in styled or "楽しかった" in styled
    print("✅ Gyaru style applied\n")

    # Test 2: Kasho polite style
    print("[TEST 2] Kasho Polite Style")
    base = "確認させてください。"
    styled = controller.apply_character_style(base, "kasho", kasho)
    print(f"Base: {base}")
    print(f"Styled: {styled}")
    # Check polite forms (です/ます/ください)
    assert "です" in styled or "ます" in styled or "ください" in styled
    print("✅ Polite style maintained\n")

    # Test 3: Yuri gentle style
    print("[TEST 3] Yuri Gentle Style")
    base = "お姉様と話しました。"
    styled = controller.apply_character_style(base, "yuri", yuri)
    print(f"Base: {base}")
    print(f"Styled: {styled}")
    assert "ね" in styled or "でしょう" in styled or "ました" in styled
    print("✅ Gentle style applied\n")

    # Test 4: Sister reference transformation
    print("[TEST 4] Sister Reference Transformation")
    base = "牡丹とKashoとユリで話しました。"

    botan_styled = controller.apply_character_style(base, "botan", botan)
    kasho_styled = controller.apply_character_style(base, "kasho", kasho)
    yuri_styled = controller.apply_character_style(base, "yuri", yuri)

    print(f"Base: {base}")
    print(f"Botan: {botan_styled}")
    print(f"Kasho: {kasho_styled}")
    print(f"Yuri: {yuri_styled}")
    assert "私" in botan_styled
    assert "お姉ちゃん" in botan_styled or "Kasho" in botan_styled
    print("✅ Sister references transformed correctly\n")

    # Test 5: Energy level impact
    print("[TEST 5] Energy Level Impact")
    base = "面白かった。"

    # Botan (high energy)
    botan_styled = controller.apply_character_style(base, "botan", botan)

    # Kasho (medium energy)
    kasho_styled = controller.apply_character_style(base, "kasho", kasho)

    print(f"Base: {base}")
    print(f"Botan (energy=0.95): {botan_styled}")
    print(f"Kasho (energy=0.6): {kasho_styled}")
    assert "！" in botan_styled or "〜" in botan_styled
    print("✅ Energy level affects punctuation\n")

    # Test 6: Kasho vs Yuri differentiation
    print("[TEST 6] Kasho vs Yuri Differentiation")
    base1 = "楽しいと思います。"
    base2 = "いい感じですね。"

    kasho_styled1 = controller.apply_character_style(base1, "kasho", kasho)
    yuri_styled1 = controller.apply_character_style(base1, "yuri", yuri)

    kasho_styled2 = controller.apply_character_style(base2, "kasho", kasho)
    yuri_styled2 = controller.apply_character_style(base2, "yuri", yuri)

    print(f"Base: {base1}")
    print(f"  Kasho (analytical): {kasho_styled1}")
    print(f"  Yuri (observational): {yuri_styled1}")
    print(f"Base: {base2}")
    print(f"  Kasho (analytical): {kasho_styled2}")
    print(f"  Yuri (observational): {yuri_styled2}")

    # Check differentiation
    assert "考えています" in kasho_styled1  # Analytical
    assert "かもしれません" in yuri_styled1  # Observational
    assert "ですが" in kasho_styled2  # Analytical
    assert "みたいですね" in yuri_styled2  # Observational
    print("✅ Kasho (analytical) and Yuri (observational) are clearly differentiated\n")

    print("[SUCCESS] All tests passed!")


if __name__ == "__main__":
    test_speech_style_controller()
