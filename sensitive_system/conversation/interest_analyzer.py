"""
Interest Analyzer - Phase 1 of Natural Conversation System

Detects topics in user messages and calculates interest scores for each character.
Characters with high interest scores are more likely to respond.

Design principles:
- Topic interest is the primary factor (0.0-0.8)
- Name mention provides bonus (+0.3)
- Context continuation provides bonus (+0.2)
- Silence (no response) is a valid expression when interest is low
"""

from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    CHARACTER_INTERESTS,
    TOPIC_KEYWORDS,
    INTEREST_THRESHOLD,
    LOW_INTEREST_THRESHOLD,
    NAME_MENTION_BONUS,
    CONTEXT_CONTINUATION_BONUS,
    TOPIC_INTEREST_CAP,
    GREETING_TEMPLATES,
    GREETING_TYPE_KEYWORDS,
    GREETING_PROMPT_INSTRUCTION
)


class InterestAnalyzer:
    """
    Analyzes user messages to determine character interest levels

    Each character's interest score is calculated as:
        score = topic_interest (0.0-0.8)
              + name_bonus (0.3 if mentioned)
              + context_bonus (0.2 if continuation)

    Characters with score >= threshold will respond.
    """

    def __init__(self):
        """
        Initialize Interest Analyzer
        """
        self.character_interests = CHARACTER_INTERESTS
        self.topic_keywords = TOPIC_KEYWORDS
        self.threshold = INTEREST_THRESHOLD
        self.low_interest_threshold = LOW_INTEREST_THRESHOLD

        # Character name patterns for detection
        self.name_patterns = {
            'botan': ['牡丹', 'ぼたん', 'botan'],
            'kasho': ['kasho', 'かしょ', 'カショ'],
            'yuri': ['ユリ', 'ゆり', 'yuri']
        }

        # Context continuation keywords
        self.continuation_keywords = [
            'じゃあ', 'それで', 'そしたら', 'だったら',
            'あなたは', '君は', 'あんたは', 'きみは',
            'you', 'then', 'and'
        ]

    def calculate_interest_scores(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Calculate interest scores for each character

        Args:
            message: User's message
            context: Optional context dict with 'last_responder' etc.

        Returns:
            Dict of {character: total_score}
            Score range: 0.0 - 1.3+

        Example:
            >>> analyzer = InterestAnalyzer()
            >>> scores = analyzer.calculate_interest_scores("VTuber好き？")
            >>> # {'botan': 0.9, 'kasho': 0.4, 'yuri': 0.3}
        """
        if context is None:
            context = {}

        # Step 1: Detect topics
        detected_topics = self.detect_topics(message)

        # Step 1.5: First message handling
        # If no topic detected AND this is first user message, treat as greeting
        if not detected_topics and context.get('is_first_message', False):
            # Assume greeting topic for first unclear message
            detected_topics = {'greeting': 0.6}

        scores = {}
        for character in ['botan', 'kasho', 'yuri']:
            # Base score: Topic interest (0.0-0.8)
            base_score = self._calculate_topic_interest(
                character,
                detected_topics
            )

            # Bonus: Name mentioned (+0.3)
            name_bonus = NAME_MENTION_BONUS if self._is_name_mentioned(
                message,
                character
            ) else 0.0

            # Bonus: Context continuation (+0.2)
            context_bonus = CONTEXT_CONTINUATION_BONUS if self._is_context_continuation(
                message,
                character,
                context
            ) else 0.0

            # Total score
            scores[character] = base_score + name_bonus + context_bonus

        return scores

    def detect_topics(self, message: str) -> Dict[str, float]:
        """
        Detect topics in user message

        Args:
            message: User's message

        Returns:
            Dict of {topic: relevance_score}
            Relevance score: 0.0-1.0

        Example:
            >>> analyzer.detect_topics("VTuberの配信見てる？")
            >>> # {'vtuber': 0.6, 'streaming': 0.3}
        """
        detected = {}
        msg_lower = message.lower()

        for topic, keywords in self.topic_keywords.items():
            # Count keyword matches
            matches = sum(1 for kw in keywords if kw in msg_lower)

            if matches > 0:
                # Relevance score (0.0-1.0)
                # More matches = higher relevance
                relevance = min(1.0, matches * 0.3)
                detected[topic] = relevance

        return detected

    def _calculate_topic_interest(
        self,
        character: str,
        detected_topics: Dict[str, float]
    ) -> float:
        """
        Calculate base topic interest score

        Args:
            character: Character name
            detected_topics: Dict of {topic: relevance}

        Returns:
            Weighted average of topic interests (max 0.8)
        """
        if not detected_topics:
            # No topic detected, use default baseline
            return self.character_interests[character]['default']

        # Weighted average
        total_relevance = sum(detected_topics.values())
        weighted_interest = 0.0

        for topic, relevance in detected_topics.items():
            # Get character's interest in this topic
            char_interest = self.character_interests[character].get(
                topic,
                self.character_interests[character]['default']
            )

            # Weight by relevance
            weight = relevance / total_relevance
            weighted_interest += char_interest * weight

        # Cap at TOPIC_INTEREST_CAP (leave room for bonuses)
        return min(TOPIC_INTEREST_CAP, weighted_interest)

    def _is_name_mentioned(self, message: str, character: str) -> bool:
        """
        Check if character's name is mentioned in message

        Args:
            message: User's message
            character: Character name

        Returns:
            True if name is mentioned
        """
        msg_lower = message.lower()
        patterns = self.name_patterns.get(character, [])

        return any(pattern in msg_lower for pattern in patterns)

    def _is_context_continuation(
        self,
        message: str,
        character: str,
        context: Dict
    ) -> bool:
        """
        Check if message is a continuation of previous conversation

        Args:
            message: User's message
            character: Character name
            context: Context dict with 'last_responder'

        Returns:
            True if this is a continuation for this character
        """
        # Check if this character was the last responder
        last_responder = context.get('last_responder')
        if last_responder != character:
            return False

        # Check for continuation keywords
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in self.continuation_keywords)

    def select_responders(
        self,
        interest_scores: Dict[str, float],
        threshold: Optional[float] = None
    ) -> List[str]:
        """
        Select characters who should respond based on interest scores

        Args:
            interest_scores: Dict of {character: score}
            threshold: Optional custom threshold (default: INTEREST_THRESHOLD)

        Returns:
            List of character names who should respond
            Empty list if no one is interested (low interest case)

        Example:
            >>> scores = {'botan': 0.8, 'kasho': 0.3, 'yuri': 0.2}
            >>> analyzer.select_responders(scores)
            >>> # ['botan']
        """
        if threshold is None:
            threshold = self.threshold

        responders = []
        for character, score in interest_scores.items():
            if score >= threshold:
                responders.append(character)

        return responders

    def is_low_interest_case(self, interest_scores: Dict[str, float]) -> bool:
        """
        Check if this is a low interest case (no one is interested)

        Args:
            interest_scores: Dict of {character: score}

        Returns:
            True if all characters have low interest
        """
        return all(
            score < self.low_interest_threshold
            for score in interest_scores.values()
        )

    def detect_greeting_type(self, message: str) -> str:
        """
        Detect greeting type for template selection

        Args:
            message: User's message

        Returns:
            Greeting type: 'casual', 'morning', 'night', or 'formal'
            Priority: morning > night > casual > formal (default)

        Example:
            >>> analyzer.detect_greeting_type("やっほー")
            >>> # 'casual'
            >>> analyzer.detect_greeting_type("おはよう")
            >>> # 'morning'
        """
        msg_lower = message.lower()

        # Check in priority order
        for greeting_type in ['morning', 'night', 'casual', 'formal']:
            keywords = GREETING_TYPE_KEYWORDS[greeting_type]
            if any(kw in msg_lower for kw in keywords):
                return greeting_type

        # Default to formal if no specific type detected
        return 'formal'

    def is_coordinated_greeting_required(
        self,
        detected_topics: Dict[str, float],
        context: Dict
    ) -> bool:
        """
        Check if coordinated greeting response is required

        Coordinated greeting is used when:
        - Topic is 'greeting' (detected or assumed)
        - AND this is the first user message (is_first_message=True)

        Args:
            detected_topics: Dict of {topic: relevance}
            context: Context dict with 'is_first_message'

        Returns:
            True if coordinated greeting templates should be used

        Example:
            >>> topics = {'greeting': 0.6}
            >>> context = {'is_first_message': True}
            >>> analyzer.is_coordinated_greeting_required(topics, context)
            >>> # True
        """
        # Check if greeting topic is present
        has_greeting = 'greeting' in detected_topics

        # Check if this is first message
        is_first = context.get('is_first_message', False)

        return has_greeting and is_first

    def get_coordinated_greeting(
        self,
        character: str,
        greeting_type: str
    ) -> str:
        """
        Get coordinated greeting template for character

        Args:
            character: Character name ('botan', 'kasho', 'yuri')
            greeting_type: Type of greeting ('casual', 'morning', 'night', 'formal')

        Returns:
            Greeting template string

        Example:
            >>> analyzer.get_coordinated_greeting('botan', 'casual')
            >>> # "やっほー！三姉妹の牡丹だよ！"
        """
        return GREETING_TEMPLATES[character][greeting_type]

    def format_analysis_summary(
        self,
        message: str,
        interest_scores: Dict[str, float],
        responders: List[str]
    ) -> str:
        """
        Format analysis summary for debugging/logging

        Args:
            message: User's message
            interest_scores: Interest scores
            responders: Selected responders

        Returns:
            Formatted summary string
        """
        detected_topics = self.detect_topics(message)

        lines = []
        lines.append("=" * 60)
        lines.append("Interest Analysis Summary")
        lines.append("=" * 60)
        lines.append(f"Message: {message}")
        lines.append("")
        lines.append(f"Detected topics: {detected_topics}")
        lines.append("")
        lines.append("Interest scores:")
        for char in ['botan', 'kasho', 'yuri']:
            score = interest_scores[char]
            mark = "✓" if char in responders else " "
            lines.append(f"  [{mark}] {char}: {score:.2f}")
        lines.append("")
        lines.append(f"Selected responders: {responders if responders else 'None (low interest)'}")
        lines.append("=" * 60)

        return '\n'.join(lines)
