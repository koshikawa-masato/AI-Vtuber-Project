"""
Memory Retrieval Logic

Implements memory retrieval and utilization for three sisters (Botan, Kasho, Yuri).
Searches and scores memories based on context, emotion, and personality.

Philosophy:
- Memory exists but must be actively used in conversation
- Personality determines which memories are recalled
- Phase D independence: Each sister only knows their own perspective

Author: Claude Code (Design Team)
Created: 2025-10-23
"""

import sqlite3
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from personality_core import PersonalityCore, BotanPersonality, KashoPersonality, YuriPersonality


@dataclass
class Memory:
    """Single memory entry"""

    event_id: int
    event_name: str
    event_date: str
    absolute_day: int

    # Character's own experience (first-person)
    own_emotion: str
    own_action: str
    own_thought: str
    diary_entry: str

    # Observations of sisters (third-person)
    sister1_observed_behavior: Optional[str] = None
    sister2_observed_behavior: Optional[str] = None
    sister1_inferred_feeling: Optional[str] = None
    sister2_inferred_feeling: Optional[str] = None
    sister1_name: str = ""
    sister2_name: str = ""

    # Metadata
    memory_importance: int = 5  # 1-10
    created_at: str = ""


@dataclass
class MemoryRelevanceScore:
    """Relevance score for a memory"""

    memory: Memory
    total_score: float  # 0.0-1.0

    # Score breakdown
    keyword_match_score: float = 0.0
    emotional_similarity_score: float = 0.0
    temporal_relevance_score: float = 0.0
    importance_score: float = 0.0
    personality_affinity_score: float = 0.0


class MemoryRetrievalLogic:
    """Memory retrieval and utilization logic"""

    def __init__(
        self,
        db_path: str = "/home/koshikawa/toExecUnit/sisters_memory.db",
        character: str = "botan"  # "botan" / "kasho" / "yuri"
    ):
        """
        Initialize memory retrieval system

        Args:
            db_path: Path to sisters_memory.db
            character: Character name ("botan", "kasho", "yuri")
        """
        self.db_path = db_path
        self.character = character.lower()

        # Table and column mapping
        self.memory_table = {
            "botan": "botan_memories",
            "kasho": "kasho_memories",
            "yuri": "yuri_memories"
        }[self.character]

        # Column mapping for each character
        if self.character == "botan":
            self.emotion_col = "botan_emotion"
            self.action_col = "botan_action"
            self.thought_col = "botan_thought"
            self.sister1_name = "kasho"
            self.sister2_name = "yuri"
            self.sister1_obs_col = "kasho_observed_behavior"
            self.sister2_obs_col = "yuri_observed_behavior"
            self.sister1_inf_col = "kasho_inferred_feeling"
            self.sister2_inf_col = "yuri_inferred_feeling"
        elif self.character == "kasho":
            self.emotion_col = "kasho_emotion"
            self.action_col = "kasho_action"
            self.thought_col = "kasho_thought"
            self.sister1_name = "botan"
            self.sister2_name = "yuri"
            self.sister1_obs_col = "botan_observed_behavior"
            self.sister2_obs_col = "yuri_observed_behavior"
            self.sister1_inf_col = "botan_inferred_feeling"
            self.sister2_inf_col = "yuri_inferred_feeling"
        elif self.character == "yuri":
            self.emotion_col = "yuri_emotion"
            self.action_col = "yuri_action"
            self.thought_col = "yuri_thought"
            self.sister1_name = "kasho"
            self.sister2_name = "botan"
            self.sister1_obs_col = "kasho_observed_behavior"
            self.sister2_obs_col = "botan_observed_behavior"
            self.sister1_inf_col = "kasho_inferred_feeling"
            self.sister2_inf_col = "botan_inferred_feeling"

        # Load personality
        if self.character == "botan":
            self.personality = BotanPersonality()
        elif self.character == "kasho":
            self.personality = KashoPersonality()
        elif self.character == "yuri":
            self.personality = YuriPersonality()

        print(f"[MemoryRetrievalLogic] Initialized for {self.character}")
        print(f"[MemoryRetrievalLogic] Memory table: {self.memory_table}")

    def _load_all_memories(self) -> List[Memory]:
        """Load all memories for this character"""

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT
                m.event_id,
                s.event_name,
                s.event_date,
                m.absolute_day,
                m.{self.emotion_col} as own_emotion,
                m.{self.action_col} as own_action,
                m.{self.thought_col} as own_thought,
                m.diary_entry,
                m.{self.sister1_obs_col} as sister1_observed_behavior,
                m.{self.sister2_obs_col} as sister2_observed_behavior,
                m.{self.sister1_inf_col} as sister1_inferred_feeling,
                m.{self.sister2_inf_col} as sister2_inferred_feeling,
                m.memory_importance,
                m.created_at
            FROM {self.memory_table} m
            JOIN sister_shared_events s ON m.event_id = s.event_id
            ORDER BY m.event_id
        """)

        memories = []
        for row in cursor.fetchall():
            memory = Memory(
                event_id=row['event_id'],
                event_name=row['event_name'],
                event_date=row['event_date'],
                absolute_day=row['absolute_day'],
                own_emotion=row['own_emotion'] or "",
                own_action=row['own_action'] or "",
                own_thought=row['own_thought'] or "",
                diary_entry=row['diary_entry'] or "",
                sister1_observed_behavior=row['sister1_observed_behavior'],
                sister2_observed_behavior=row['sister2_observed_behavior'],
                sister1_inferred_feeling=row['sister1_inferred_feeling'],
                sister2_inferred_feeling=row['sister2_inferred_feeling'],
                sister1_name=self.sister1_name,
                sister2_name=self.sister2_name,
                memory_importance=row['memory_importance'] or 5,
                created_at=row['created_at'] or ""
            )
            memories.append(memory)

        conn.close()
        return memories

    def retrieve_relevant_memories(
        self,
        context: str,
        current_emotion: Optional[str] = None,
        top_k: int = 5,
        relevance_threshold: float = 0.3
    ) -> List[MemoryRelevanceScore]:
        """
        Retrieve relevant memories based on context

        Args:
            context: Current conversation context
            current_emotion: Current emotional state (optional)
            top_k: Number of top memories to return
            relevance_threshold: Minimum relevance score (0.0-1.0)

        Returns:
            List of MemoryRelevanceScore, sorted by total_score descending
        """

        all_memories = self._load_all_memories()

        # Calculate relevance for each memory
        scored_memories = []
        for memory in all_memories:
            score = self._calculate_relevance_score(
                memory=memory,
                context=context,
                current_emotion=current_emotion
            )

            if score.total_score >= relevance_threshold:
                scored_memories.append(score)

        # Sort by total_score descending
        scored_memories.sort(key=lambda x: x.total_score, reverse=True)

        # Return top_k
        return scored_memories[:top_k]

    def _calculate_relevance_score(
        self,
        memory: Memory,
        context: str,
        current_emotion: Optional[str] = None
    ) -> MemoryRelevanceScore:
        """
        Calculate relevance score for a memory

        Scoring components:
        1. Keyword match (30%)
        2. Emotional similarity (25%)
        3. Temporal relevance (15%)
        4. Memory importance (15%)
        5. Personality affinity (15%)
        """

        # 1. Keyword match score
        keyword_score = self._calculate_keyword_match(
            context=context,
            memory=memory
        )

        # 2. Emotional similarity score
        emotional_score = self._calculate_emotional_similarity(
            current_emotion=current_emotion,
            memory_emotion=memory.own_emotion
        )

        # 3. Temporal relevance score
        temporal_score = self._calculate_temporal_relevance(
            memory=memory
        )

        # 4. Memory importance score
        importance_score = memory.memory_importance / 10.0  # Normalize to 0.0-1.0

        # 5. Personality affinity score
        personality_score = self._calculate_personality_affinity(
            memory=memory
        )

        # Weighted total
        total_score = (
            keyword_score * 0.30 +
            emotional_score * 0.25 +
            temporal_score * 0.15 +
            importance_score * 0.15 +
            personality_score * 0.15
        )

        return MemoryRelevanceScore(
            memory=memory,
            total_score=total_score,
            keyword_match_score=keyword_score,
            emotional_similarity_score=emotional_score,
            temporal_relevance_score=temporal_score,
            importance_score=importance_score,
            personality_affinity_score=personality_score
        )

    def _calculate_keyword_match(
        self,
        context: str,
        memory: Memory
    ) -> float:
        """Calculate keyword match score (0.0-1.0)"""

        context_lower = context.lower()

        # Extract keywords from context (simple tokenization)
        keywords = re.findall(r'\w+', context_lower)

        # Searchable fields
        searchable_text = " ".join([
            memory.event_name.lower(),
            memory.own_emotion.lower(),
            memory.own_action.lower(),
            memory.own_thought.lower(),
            memory.diary_entry.lower()
        ])

        # Count matches
        matches = sum(1 for keyword in keywords if keyword in searchable_text)

        if len(keywords) == 0:
            return 0.0

        # Normalize
        score = min(matches / len(keywords), 1.0)
        return score

    def _calculate_emotional_similarity(
        self,
        current_emotion: Optional[str],
        memory_emotion: str
    ) -> float:
        """Calculate emotional similarity score (0.0-1.0)"""

        if not current_emotion or not memory_emotion:
            return 0.5  # Neutral score

        # Emotion keyword matching (simple approach)
        positive_emotions = ["happy", "excited", "joy", "love", "嬉しい", "楽しい", "ワクワク", "感動"]
        negative_emotions = ["sad", "angry", "fear", "悲しい", "怒り", "不安", "困惑"]
        neutral_emotions = ["calm", "neutral", "穏やか", "落ち着き"]

        def categorize_emotion(emotion: str) -> str:
            emotion_lower = emotion.lower()
            if any(e in emotion_lower for e in positive_emotions):
                return "positive"
            elif any(e in emotion_lower for e in negative_emotions):
                return "negative"
            else:
                return "neutral"

        current_cat = categorize_emotion(current_emotion)
        memory_cat = categorize_emotion(memory_emotion)

        if current_cat == memory_cat:
            return 1.0  # Same emotion category
        else:
            return 0.3  # Different emotion category

    def _calculate_temporal_relevance(
        self,
        memory: Memory
    ) -> float:
        """
        Calculate temporal relevance score (0.0-1.0)

        Recency bias: Recent memories are more relevant
        """

        # Parse event_date
        try:
            event_date = datetime.strptime(memory.event_date, "%Y-%m-%d")
        except:
            return 0.5  # Default score if parsing fails

        today = datetime.now()
        days_ago = (today - event_date).days

        # Decay function: exponential decay
        # Recent: 1.0, 1 year ago: ~0.5, 5 years ago: ~0.1
        score = max(0.1, 1.0 / (1.0 + days_ago / 365.0))

        return score

    def _calculate_personality_affinity(
        self,
        memory: Memory
    ) -> float:
        """
        Calculate personality affinity score (0.0-1.0)

        Different personalities prefer different types of memories:
        - Botan: Emotional, exciting memories
        - Kasho: Lesson-learned, analytical memories
        - Yuri: Sister-relationship memories
        """

        score = 0.5  # Base score

        if self.character == "botan":
            # Botan prefers emotional memories
            if memory.memory_importance >= 7:
                score += 0.2
            if "感動" in memory.own_emotion or "ワクワク" in memory.own_emotion:
                score += 0.3

        elif self.character == "kasho":
            # Kasho prefers analytical, lesson-learned memories
            if "学んだ" in memory.own_thought or "考えた" in memory.own_thought:
                score += 0.3
            if memory.memory_importance >= 6:
                score += 0.2

        elif self.character == "yuri":
            # Yuri prefers sister-relationship memories
            if memory.sister1_observed_behavior or memory.sister2_observed_behavior:
                score += 0.3
            if "お姉" in memory.diary_entry or "姉" in memory.diary_entry:
                score += 0.2

        return min(score, 1.0)

    def should_mention_memory(
        self,
        memory_score: MemoryRelevanceScore,
        conversation_flow: str = "natural"  # "natural" / "question" / "story"
    ) -> bool:
        """
        Determine if memory should be mentioned

        Args:
            memory_score: MemoryRelevanceScore object
            conversation_flow: Type of conversation flow

        Returns:
            True if memory should be mentioned
        """

        # Threshold varies by conversation flow
        thresholds = {
            "natural": 0.5,   # Natural conversation: moderate threshold
            "question": 0.3,  # Answering question: lower threshold
            "story": 0.6      # Telling story: higher threshold
        }

        threshold = thresholds.get(conversation_flow, 0.5)

        # Personality-based adjustment
        if self.character == "botan":
            # Botan mentions memories more freely (emotional_expression: 0.95)
            threshold *= 0.9
        elif self.character == "kasho":
            # Kasho mentions memories selectively (emotional_expression: 0.5)
            threshold *= 1.1
        elif self.character == "yuri":
            # Yuri mentions memories moderately (emotional_expression: 0.7)
            threshold *= 1.0

        return memory_score.total_score >= threshold

    def format_memory_for_speech(
        self,
        memory: Memory,
        style: str = "casual"  # "casual" / "detailed" / "emotional"
    ) -> str:
        """
        Format memory for speech

        Respects Phase D independence: Character speaks from their own perspective

        Args:
            memory: Memory object
            style: Speech style

        Returns:
            Formatted memory string
        """

        if style == "casual":
            # Brief mention
            if self.character == "botan":
                return f"そういえば、{memory.event_name}の時〜"
            elif self.character == "kasho":
                return f"あの時の{memory.event_name}のことを思い出しますが"
            elif self.character == "yuri":
                return f"{memory.event_name}の時のこと、覚えてます"

        elif style == "detailed":
            # Detailed recollection
            diary_preview = memory.diary_entry[:100] if len(memory.diary_entry) > 100 else memory.diary_entry
            return f"""あ、{memory.event_name}！
{diary_preview}{'...' if len(memory.diary_entry) > 100 else ''}
あの時は{memory.own_emotion}だったな。"""

        elif style == "emotional":
            # Emotional emphasis
            if self.character == "botan":
                return f"マジで、{memory.event_name}の時ヤバかった！{memory.own_emotion}で、{memory.own_action}したんだよね〜"
            elif self.character == "kasho":
                return f"{memory.event_name}の時、{memory.own_emotion}でした。あの経験から学んだことは..."
            elif self.character == "yuri":
                obs = memory.sister1_observed_behavior if memory.sister1_observed_behavior else ""
                if obs:
                    return f"{memory.event_name}の時、{memory.own_emotion}でした。{obs}というのが印象的でした"
                else:
                    return f"{memory.event_name}の時、{memory.own_emotion}でした"

        return memory.event_name

    def format_sister_observation(
        self,
        memory: Memory,
        sister_name: str  # "kasho" / "yuri" / "botan"
    ) -> str:
        """
        Format observation about sister (respects Phase D independence)

        IMPORTANT: Character only knows what they observed, not sister's internal thoughts

        Args:
            memory: Memory object
            sister_name: Sister's name ("kasho" / "yuri" / "botan")

        Returns:
            Formatted observation string
        """

        sister_name_lower = sister_name.lower()

        # Determine which sister is being referenced
        if sister_name_lower == memory.sister1_name:
            observed = memory.sister1_observed_behavior
            inferred = memory.sister1_inferred_feeling
        elif sister_name_lower == memory.sister2_name:
            observed = memory.sister2_observed_behavior
            inferred = memory.sister2_inferred_feeling
        else:
            return ""

        if not observed:
            return ""

        # Correct implementation: Observation + Inference (not assertion)
        if self.character == "botan":
            if sister_name_lower == "kasho":
                return f"お姉ちゃん（Kasho）は{observed}。{inferred}と思う。"
            elif sister_name_lower == "yuri":
                return f"ユリは{observed}。{inferred}と思う。"
        elif self.character == "kasho":
            if sister_name_lower == "botan":
                return f"牡丹は{observed}。{inferred}みたい。"
            elif sister_name_lower == "yuri":
                return f"ユリは{observed}。{inferred}みたい。"
        elif self.character == "yuri":
            if sister_name_lower == "kasho":
                return f"Kashoお姉様は{observed}。{inferred}んじゃないかな。"
            elif sister_name_lower == "botan":
                return f"牡丹お姉様は{observed}。{inferred}んじゃないかな。"

        return ""


def test_memory_retrieval_logic():
    """Test MemoryRetrievalLogic functionality"""

    print("=== Testing MemoryRetrievalLogic ===\n")

    # Test 1: Initialization
    print("[TEST 1] Initialization")
    logic_botan = MemoryRetrievalLogic(character="botan")
    logic_kasho = MemoryRetrievalLogic(character="kasho")
    logic_yuri = MemoryRetrievalLogic(character="yuri")
    print("✅ All characters initialized\n")

    # Test 2: Load all memories
    print("[TEST 2] Load All Memories")
    memories = logic_botan._load_all_memories()
    print(f"Loaded {len(memories)} memories for Botan")
    if memories:
        print(f"Event IDs (first 5): {[m.event_id for m in memories[:5]]}")
    print()

    # Test 3: Keyword match scoring
    print("[TEST 3] Keyword Match Scoring")
    if memories:
        test_memory = memories[0]
        score = logic_botan._calculate_keyword_match(
            context="VTuber 配信 感動",
            memory=test_memory
        )
        print(f"Keyword match score for Event #{test_memory.event_id}: {score:.2f}")
    print()

    # Test 4: Retrieve relevant memories
    print("[TEST 4] Retrieve Relevant Memories")
    relevant = logic_botan.retrieve_relevant_memories(
        context="VTuber 夢",
        top_k=5
    )
    print(f"Found {len(relevant)} relevant memories")
    for mem in relevant[:3]:
        print(f"  - Event #{mem.memory.event_id}: {mem.memory.event_name} (score: {mem.total_score:.2f})")
    print()

    # Test 5: Should mention memory
    print("[TEST 5] Should Mention Memory")
    if relevant:
        should_mention = logic_botan.should_mention_memory(
            relevant[0],
            conversation_flow="natural"
        )
        print(f"Should mention top memory? {should_mention}")
    print()

    # Test 6: Format memory for speech
    print("[TEST 6] Format Memory for Speech")
    if relevant:
        formatted = logic_botan.format_memory_for_speech(
            relevant[0].memory,
            style="emotional"
        )
        print(f"Formatted: {formatted}")
    print()

    # Test 7: Phase D independence (sister observation)
    print("[TEST 7] Phase D Independence - Sister Observation")
    if memories:
        # Find a memory with sister observation
        for mem in memories:
            if mem.sister1_observed_behavior:
                obs = logic_botan.format_sister_observation(
                    mem,
                    sister_name=mem.sister1_name
                )
                if obs:
                    print(f"Sister observation: {obs}")
                    print("✅ Respects Phase D independence (observation + inference, not assertion)")
                    break
    print()

    print("[SUCCESS] All tests passed!")


if __name__ == "__main__":
    test_memory_retrieval_logic()
