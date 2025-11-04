"""
Hallucination Classifier
Classifies hallucinations into three types:
1. Contradiction (矛盾型) - Requires correction
2. Complement (整合型) - Personality-consistent, add as complementary memory
3. Inspiration (触発型) - "Truth from lies", aspirational statements that may grow into real values

Author: Claude Code (Design & Implementation)
Created: 2025-10-24
Version: 1.0
"""

from typing import Dict, List
import re


class HallucinationClassifier:
    """
    Classifies hallucinations into three types based on their nature
    """

    def __init__(self):
        # Aspirational keywords (触発型の特徴)
        self.aspirational_keywords = [
            'したい', 'なりたい', 'やってみたい', 'やりたい',
            '楽しみ', 'いつか',
            'できたら', 'できるなら', 'してみよう',
            'したいな', 'なりたいな', 'やってみたいな',
            'たいな', 'たい！'
        ]

        # Future context keywords
        self.future_keywords = [
            '次', '次は', '今度', '将来', 'これから'
        ]

        # Hypothetical keywords (仮定形)
        self.hypothetical_keywords = [
            'もし', 'もしも', 'だったら', 'なら',
            'できたら', 'できるなら', '仮に'
        ]

        # Past tense keywords (過去形 - 矛盾型の可能性)
        self.past_tense_keywords = [
            'した', 'だった', 'いた', 'あった',
            'していた', 'だった', 'のとき', 'の頃'
        ]

    def classify(
        self,
        statement: str,
        verification_result: Dict,
        character: str
    ) -> Dict[str, any]:
        """
        Classify hallucination type

        Args:
            statement: Original statement
            verification_result: Result from HallucinationDetector
            character: Character name (botan/kasho/yuri)

        Returns:
            {
                'type': 'contradiction' | 'complement' | 'inspiration',
                'confidence': float (0.0-1.0),
                'reason': str,
                'aspirational_value': str (for inspiration type)
            }
        """
        # Check if it's aspirational (触発型)
        aspiration_score = self._calculate_aspiration_score(statement)

        if aspiration_score >= 0.5:
            return {
                'type': 'inspiration',
                'confidence': aspiration_score,
                'reason': 'Future-oriented aspirational statement',
                'aspirational_value': self._extract_aspiration(statement)
            }

        # Check if it's hypothetical (仮定形 - 通常は問題なし)
        if self._is_hypothetical(statement):
            return {
                'type': 'complement',
                'confidence': 0.8,
                'reason': 'Hypothetical statement (not claiming as fact)',
                'aspirational_value': None
            }

        # Check if it's past tense (過去形 - 矛盾型の可能性高い)
        if self._is_past_tense(statement):
            return {
                'type': 'contradiction',
                'confidence': 0.9,
                'reason': 'Past tense claim with no memory record',
                'aspirational_value': None
            }

        # Default: contradiction
        return {
            'type': 'contradiction',
            'confidence': 0.7,
            'reason': 'Default classification - requires correction',
            'aspirational_value': None
        }

    def _calculate_aspiration_score(self, statement: str) -> float:
        """
        Calculate how aspirational the statement is

        Returns:
            0.0-1.0 (higher = more aspirational)
        """
        score = 0.0

        # Check for aspirational keywords
        for keyword in self.aspirational_keywords:
            if keyword in statement:
                score += 0.3

        # Boost for multiple keywords
        keyword_count = sum(1 for kw in self.aspirational_keywords if kw in statement)
        if keyword_count >= 2:
            score += 0.2

        # Check for future context
        if any(word in statement for word in self.future_keywords):
            score += 0.2

        # Check for exclamation mark (strong enthusiasm)
        if '！' in statement or '!' in statement:
            score += 0.3

        # Check for positive emotion words
        positive_words = ['楽しみ', '嬉しい', 'ワクワク', '期待']
        if any(word in statement for word in positive_words):
            score += 0.2

        # Penalty for past tense
        if any(word in statement for word in self.past_tense_keywords):
            score -= 0.3

        return min(1.0, max(0.0, score))

    def _is_hypothetical(self, statement: str) -> bool:
        """Check if statement is hypothetical (not claiming as fact)"""
        return any(keyword in statement for keyword in self.hypothetical_keywords)

    def _is_past_tense(self, statement: str) -> bool:
        """Check if statement is in past tense (claiming past experience)"""
        return any(keyword in statement for keyword in self.past_tense_keywords)

    def _extract_aspiration(self, statement: str) -> str:
        """
        Extract the aspirational value from statement

        Example:
            "視聴者さんたちと話す時間を作りたいな！"
            -> "視聴者との交流を大切にしたい"
        """
        # Simple extraction - take the part before aspirational keyword
        for keyword in self.aspirational_keywords:
            if keyword in statement:
                parts = statement.split(keyword)
                if len(parts) > 0:
                    # Clean up
                    value = parts[0].strip()
                    # Remove common prefixes
                    value = value.replace('次は', '').replace('今度', '').strip()
                    return value + keyword

        return statement[:50]  # Fallback: first 50 chars


# Test code
if __name__ == "__main__":
    print("=== HallucinationClassifier Test ===\n")

    classifier = HallucinationClassifier()

    test_cases = [
        {
            'statement': '視聴者さんたちと話す時間を作りたいな！',
            'expected': 'inspiration'
        },
        {
            'statement': 'もし大阪に行くなら、たこ焼き食べたい',
            'expected': 'complement'
        },
        {
            'statement': '昨日カラオケに行った',
            'expected': 'contradiction'
        },
        {
            'statement': '配信でコメントをもらった',
            'expected': 'contradiction'
        },
        {
            'statement': '次は配信でゲームをやってみたい！',
            'expected': 'inspiration'
        },
        {
            'statement': 'いつか三姉妹で旅行に行きたいな',
            'expected': 'inspiration'
        }
    ]

    for i, case in enumerate(test_cases, 1):
        result = classifier.classify(
            statement=case['statement'],
            verification_result={},
            character='botan'
        )

        print(f"Test {i}:")
        print(f"Statement: {case['statement']}")
        print(f"Type: {result['type']} (expected: {case['expected']})")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Reason: {result['reason']}")
        if result['aspirational_value']:
            print(f"Aspirational Value: {result['aspirational_value']}")
        print(f"Match: {'✅' if result['type'] == case['expected'] else '❌'}")
        print("-" * 60)
        print()
