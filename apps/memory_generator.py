#!/usr/bin/env python3
"""
Phase 1.6 v4: Memory Manufacturing Machine (記憶製造機)
Continuous autonomous system for discussion → memory creation

This system:
1. Monitors proposals.json for new topics
2. Prioritizes: developer > auto (6hr) > comment (future)
3. Executes structured discussions (v4)
4. Auto-generates memories (Event #***)
5. Auto-generates technical logs
6. Reports progress to developer

Author: Claude Code (設計部隊)
Date: 2025-10-22
"""

import asyncio
import json
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
import random

# Import v4 discussion system
from autonomous_discussion_v4_improved import (
    StructuredDiscussionSystem,
    DiscussionState
)

# Phase 4: Import personality core for memory generation consistency
from personality_core import PersonalityCore, BotanPersonality, KashoPersonality, YuriPersonality

# Phase D: Import hallucination personalization system
from hallucination_personalizer import HallucinationPersonalizer


@dataclass
class Proposal:
    """Proposal structure"""
    id: int
    priority: str  # developer/auto/comment
    status: str  # pending/processing/completed
    title: str
    description: str
    created_at: str
    processing_started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[dict] = None


class ProposalManager:
    """Manage proposals.json file"""

    def __init__(self, filepath: str = "/home/koshikawa/toExecUnit/proposals.json"):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create proposals.json if not exists"""
        if not Path(self.filepath).exists():
            initial_data = {
                "next_event_id": 102,
                "last_auto_proposal": None,
                "proposals": []
            }
            self._save(initial_data)

    def _load(self) -> dict:
        """Load proposals.json"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save(self, data: dict):
        """Save proposals.json"""
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all_proposals(self) -> List[Proposal]:
        """Get all proposals"""
        data = self._load()
        return [Proposal(**p) for p in data['proposals']]

    def get_pending_proposals(self) -> List[Proposal]:
        """Get pending proposals sorted by priority"""
        proposals = self.get_all_proposals()
        pending = [p for p in proposals if p.status == 'pending']

        # Sort by priority: developer > auto > comment
        priority_order = {'developer': 0, 'auto': 1, 'comment': 2}
        pending.sort(key=lambda p: (priority_order.get(p.priority, 999), p.created_at))

        return pending

    def add_proposal(self, proposal: Proposal):
        """Add new proposal"""
        data = self._load()
        data['proposals'].append(asdict(proposal))
        self._save(data)

    def update_status(self, proposal_id: int, status: str, result: Optional[dict] = None):
        """Update proposal status"""
        data = self._load()

        for p in data['proposals']:
            if p['id'] == proposal_id:
                p['status'] = status

                if status == 'processing':
                    p['processing_started_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                elif status == 'completed':
                    p['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if result:
                        p['result'] = result

                break

        self._save(data)

    def get_next_event_id(self) -> int:
        """Get next event ID"""
        data = self._load()
        return data['next_event_id']

    def increment_event_id(self):
        """Increment next_event_id"""
        data = self._load()
        data['next_event_id'] += 1
        self._save(data)

    def update_last_auto_proposal(self):
        """Update last auto proposal timestamp"""
        data = self._load()
        data['last_auto_proposal'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._save(data)

    def get_last_auto_proposal_time(self) -> Optional[datetime]:
        """Get last auto proposal timestamp"""
        data = self._load()
        last = data.get('last_auto_proposal')

        if last is None:
            return None

        return datetime.strptime(last, '%Y-%m-%d %H:%M:%S')


class FreetalkTopicSelector:
    """
    Select free talk topics from predefined pool.
    Replaces DynamicThemeGenerator.

    Features:
    - One-time use (each topic used only once)
    - Auto-insert autonomous_topics every 10 topics
    - Alert when remaining topics < 20
    """

    def __init__(self, pool_filepath: str = "/home/koshikawa/toExecUnit/freetalk_topics_pool.json"):
        self.pool_filepath = pool_filepath
        self.topic_counter = 0  # Count topics used (for autonomous trigger)
        self._ensure_pool_exists()

    def _ensure_pool_exists(self):
        """Verify freetalk_topics_pool.json exists"""
        if not Path(self.pool_filepath).exists():
            raise FileNotFoundError(
                f"freetalk_topics_pool.json not found at {self.pool_filepath}\n"
                "This file must be created by design team."
            )

    def _load_pool(self) -> dict:
        """Load freetalk_topics_pool.json"""
        with open(self.pool_filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_pool(self, data: dict):
        """Save freetalk_topics_pool.json"""
        with open(self.pool_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_remaining_count(self) -> int:
        """Get count of remaining unused topics"""
        pool = self._load_pool()

        # Count total topics
        total = 0
        for category_data in pool['categories'].values():
            total += len(category_data['topics'])

        # Count used topics
        used = len(pool['used_topics'])

        return total - used

    def should_use_autonomous(self) -> bool:
        """Check if should use autonomous_topic (every 10 topics)"""
        return self.topic_counter > 0 and self.topic_counter % 10 == 0

    def select_autonomous_topic(self) -> dict:
        """Select next autonomous_topic (rotation)"""
        pool = self._load_pool()

        # Get current rotation_index
        rotation_index = pool['autonomous_topics']['rotation_index']
        topics = pool['autonomous_topics']['topics']

        # Select topic
        topic = topics[rotation_index]

        # Increment rotation_index (mod 10)
        pool['autonomous_topics']['rotation_index'] = (rotation_index + 1) % len(topics)

        # Save pool
        self._save_pool(pool)

        # Build return dict
        return {
            'theme': topic['topic'],
            'reason': topic['description'],
            'expected_style': 'playful',
            'type': 'autonomous',
            'initiator': topic['initiator'],
            'target': topic['target']
        }

    def select_regular_topic(self) -> dict:
        """Select random topic from unused pool"""
        pool = self._load_pool()

        # Get all unused topics
        used_topics = [ut['topic'] for ut in pool['used_topics']]

        # Collect all unused topics
        unused_topics = []
        for category_key, category_data in pool['categories'].items():
            category_name = category_data['name']
            for topic in category_data['topics']:
                if topic not in used_topics:
                    unused_topics.append({
                        'topic': topic,
                        'category': category_key,
                        'category_name': category_name
                    })

        # Check if depleted
        if len(unused_topics) == 0:
            print("\n" + "="*70)
            print("WARNING: Free Talk Topic Pool Depleted!")
            print("="*70)
            print("\nAll 120 topics have been used.")
            print("Please contact developer to add new topics.")
            print("\nFile: /home/koshikawa/toExecUnit/freetalk_topics_pool.json")
            print("-> Add new topics to categories.")
            print("-> Do NOT clear used_topics (one-time use principle).")
            print("="*70 + "\n")
            raise RuntimeError("Topic pool depleted. Need developer intervention.")

        # Select random topic
        selected = random.choice(unused_topics)

        # Add to used_topics
        pool['used_topics'].append({
            'topic': selected['topic'],
            'category': selected['category'],
            'used_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'event_id': None  # Will be filled by caller
        })

        # Save pool
        self._save_pool(pool)

        # Build return dict
        return {
            'theme': selected['topic'],
            'reason': f"Category \"{selected['category_name']}\" selection. Parent-provided topic only.",
            'expected_style': 'relaxed',
            'type': 'regular',
            'category': selected['category']
        }

    def select_topic(self) -> dict:
        """
        Main entry point: select topic (regular or autonomous)

        Returns:
            dict with keys:
            - 'theme': topic title
            - 'reason': reason for selection
            - 'expected_style': discussion style
            - 'type': 'regular' or 'autonomous'
            - 'initiator': (for autonomous only)
            - 'target': (for autonomous only)
        """
        # Increment topic_counter
        self.topic_counter += 1

        # Check if should use autonomous
        if self.should_use_autonomous():
            return self.select_autonomous_topic()

        # Otherwise select regular topic
        return self.select_regular_topic()

    def check_and_alert_low_topics(self):
        """Alert if remaining topics < threshold"""
        remaining = self.get_remaining_count()
        alert_threshold = 20

        if remaining < alert_threshold:
            print("\n" + "="*70)
            print(f"WARNING: Low Topic Count ({remaining} remaining)")
            print("="*70)
            print(f"\nRemaining topics: {remaining}")
            print("Please contact developer to add new topics.")
            print("="*70 + "\n")


class MemoryGenerator:
    """Auto-generate memories from discussion"""

    def __init__(self, db_path: str = "/home/koshikawa/toExecUnit/sisters_memory.db"):
        self.db_path = db_path
        self.model = "qwen2.5:32b"

        # Phase 4: Initialize personality cores for consistent memory generation
        self.personalities = {
            "牡丹": BotanPersonality(),
            "Kasho": KashoPersonality(),
            "ユリ": YuriPersonality()
        }
        print("[MemoryGenerator] Phase 4: Personality cores initialized for memory generation")

    async def call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama LLM"""
        try:
            result = subprocess.run(
                ["/usr/local/bin/ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=180
            )

            if result.returncode != 0:
                return None

            return result.stdout.strip()

        except Exception as e:
            print(f"[ERROR] Ollama call failed: {e}")
            return None

    def get_birth_dates(self) -> dict:
        """Get sisters' birth dates"""
        return {
            "牡丹": datetime(2008, 4, 1),
            "Kasho": datetime(2006, 5, 20),
            "ユリ": datetime(2010, 7, 7)
        }

    def calculate_ages(self, event_date: datetime) -> dict:
        """Calculate ages for all sisters"""
        births = self.get_birth_dates()
        ages = {}

        for sister, birth in births.items():
            delta = event_date - birth
            ages[sister] = {
                "age_days": delta.days,
                "age_years": delta.days // 365,
                "absolute_day": delta.days
            }

        return ages

    async def generate_sister_memory(
        self,
        sister: str,
        state: DiscussionState,
        event_number: int
    ) -> Optional[dict]:
        """Generate one sister's memory (Phase 4: with personality traits)"""

        # Build discussion summary
        speeches = []
        for speech in state.all_speeches:
            speeches.append(f"Round {speech.round_number}({speech.phase}) {speech.speaker}: {speech.content}")

        discussion_context = "\n".join(speeches)

        # Get other sisters
        all_sisters = ["牡丹", "Kasho", "ユリ"]
        other_sisters = [s for s in all_sisters if s != sister]

        # Phase 4: Get personality traits
        personality = self.personalities[sister]

        # Build personality context
        personality_context = f"""【あなた（{sister}）の性格特性】
Big Five:
- Openness (開放性): {personality.openness:.2f} - {'新しい体験に積極的' if personality.openness > 0.7 else '慎重で保守的' if personality.openness < 0.4 else '適度にバランス'}
- Conscientiousness (誠実性): {personality.conscientiousness:.2f} - {'非常に責任感が強い' if personality.conscientiousness > 0.8 else '柔軟で臨機応変' if personality.conscientiousness < 0.5 else 'バランス型'}
- Extraversion (外向性): {personality.extraversion:.2f} - {'非常に社交的' if personality.extraversion > 0.8 else '内向的' if personality.extraversion < 0.4 else 'バランス型'}
- Agreeableness (協調性): {personality.agreeableness:.2f} - {'協調性が非常に高い' if personality.agreeableness > 0.8 else '独立的' if personality.agreeableness < 0.4 else 'バランス型'}
- Neuroticism (神経症傾向): {personality.neuroticism:.2f} - {'感情が不安定になりやすい' if personality.neuroticism > 0.6 else '感情が非常に安定' if personality.neuroticism < 0.3 else 'バランス型'}

VTuber特性:
- Energy Level (エネルギーレベル): {personality.energy_level:.2f}
- Emotional Expression (感情表現): {personality.emotional_expression:.2f} - {'感情を豊かに表現' if personality.emotional_expression > 0.7 else '感情を抑える' if personality.emotional_expression < 0.4 else 'バランス型'}
- Risk Tolerance (リスク許容度): {personality.risk_tolerance:.2f}

この性格特性に基づいて、{sister}らしい記憶を生成してください。"""

        prompt = f"""あなたは{sister}です。
今日の討論について、あなたの主観的な記憶を生成してください。

{personality_context}

【討論テーマ】
{state.proposal['title']}

【討論の全発言】
{discussion_context}

【記憶として記録すべき内容】
1. **あなたの感情**: この討論でどう感じたか（率直に、本音で）
2. **あなたの行動**: 自分が何をしたか、どんな発言をしたか
3. **あなたの思考**: 何を考えていたか、なぜそう思ったか
4. **日記形式の記録**: {sister}らしく、今日の討論を日記に書く
5. **{other_sisters[0]}の観察**: {other_sisters[0]}がどんな様子だったか
6. **{other_sisters[1]}の観察**: {other_sisters[1]}がどんな様子だったか
7. **{other_sisters[0]}の気持ち推測**: {other_sisters[0]}はどう感じていたと思うか
8. **{other_sisters[1]}の気持ち推測**: {other_sisters[1]}はどう感じていたと思うか

【重要】
- 技術的な実装の話は書かない（それは別のログに記録されます）
- {sister}の主観的な体験、感情、姉妹との関係を中心に
- 完璧な結論が出なくても、「経験」として価値がある

【Phase D 独立性の原則】（最重要）
- 他の姉妹の内面（感情・思考）は「推測」のみ、絶対に断定しない
- 観察できるのは「行動・表情・発言」のみ
- 例: ✅「{other_sisters[0]}は嬉しそうだった」 ✅「{other_sisters[0]}は楽しんでいたと思う」
- 例: ❌「{other_sisters[0]}は嬉しかった」 ❌「{other_sisters[0]}は楽しんでいた」（断定は禁止）
- あなた自身の感情・思考のみが確実な真実

JSON形式で回答:
{{
    "emotion": "{sister}の感情（簡潔に）",
    "action": "{sister}の行動（簡潔に）",
    "thought": "{sister}の思考（2-3文）",
    "diary_entry": "日記形式の記録（{sister}らしい口調で、200文字程度）",
    "sister1_observed": "{other_sisters[0]}の観察（1-2文）",
    "sister2_observed": "{other_sisters[1]}の観察（1-2文）",
    "sister1_inferred": "{other_sisters[0]}の気持ち推測（1-2文）",
    "sister2_inferred": "{other_sisters[1]}の気持ち推測（1-2文）",
    "memory_importance": 1-10の数値
}}

JSON以外は不要:"""

        try:
            response = await self.call_ollama(prompt)

            if not response:
                return None

            # Extract JSON
            start = response.find('{')
            end = response.rfind('}') + 1

            if start == -1 or end == 0:
                return None

            json_str = response[start:end]
            memory = json.loads(json_str)

            return memory

        except Exception as e:
            print(f"[ERROR] Memory generation failed for {sister}: {e}")
            return None

    async def save_discussion_as_event(
        self,
        state: DiscussionState,
        event_number: int
    ) -> bool:
        """Save discussion as Event #***"""

        print(f"\n{'='*70}")
        print(f"記憶化開始: Event #{event_number}")
        print(f"{'='*70}\n")

        # Event details
        event_date = datetime.now().strftime("%Y-%m-%d")
        event_name = state.proposal['title']
        location = "牡丹の内部世界（討論システム）"
        category = "自律討論"
        participants = "牡丹、Kasho、ユリ"
        cultural_context = "Phase 1.6 v4 起承転結討論システム"

        # Determine if free talk
        is_free_talk = state.proposal.get('priority') == 'auto'

        # Generate description
        if is_free_talk:
            description = f"フリートーク「{event_name}」。三姉妹が自由に話し合った。"
        else:
            description = f"議題「{event_name}」について討論。{len(state.all_speeches)}回の発言を経て、{state.current_round}ラウンドで終了。"

        # Calculate ages
        event_dt = datetime.now()
        ages = self.calculate_ages(event_dt)

        # Generate memories for each sister
        print("牡丹の記憶生成中...")
        botan_memory = await self.generate_sister_memory("牡丹", state, event_number)

        if not botan_memory:
            print("[ERROR] 牡丹の記憶生成失敗")
            return False

        print("✓ 牡丹の記憶生成完了\n")

        print("Kashoの記憶生成中...")
        kasho_memory = await self.generate_sister_memory("Kasho", state, event_number)

        if not kasho_memory:
            print("[ERROR] Kashoの記憶生成失敗")
            return False

        print("✓ Kashoの記憶生成完了\n")

        print("ユリの記憶生成中...")
        yuri_memory = await self.generate_sister_memory("ユリ", state, event_number)

        if not yuri_memory:
            print("[ERROR] ユリの記憶生成失敗")
            return False

        print("✓ ユリの記憶生成完了\n")

        # Average emotional impact
        emotional_impact = int((
            botan_memory['memory_importance'] +
            kasho_memory['memory_importance'] +
            yuri_memory['memory_importance']
        ) / 3)

        # Insert into database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Insert shared event
            cursor.execute('''
                INSERT INTO sister_shared_events (
                    event_id, event_name, event_date, location,
                    kasho_age_years, kasho_age_days, kasho_absolute_day,
                    botan_age_years, botan_age_days, botan_absolute_day,
                    yuri_age_years, yuri_age_days, yuri_absolute_day,
                    description, participants, cultural_context,
                    emotional_impact, category, event_number, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_number,
                event_name,
                event_date,
                location,
                ages["Kasho"]["age_years"],
                ages["Kasho"]["age_days"],
                ages["Kasho"]["absolute_day"],
                ages["牡丹"]["age_years"],
                ages["牡丹"]["age_days"],
                ages["牡丹"]["absolute_day"],
                ages["ユリ"]["age_years"],
                ages["ユリ"]["age_days"],
                ages["ユリ"]["absolute_day"],
                description,
                participants,
                cultural_context,
                emotional_impact,
                category,
                event_number,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            # Insert botan memory
            cursor.execute('''
                INSERT INTO botan_memories (
                    event_id, absolute_day, memory_date,
                    botan_emotion, botan_action, botan_thought, diary_entry,
                    kasho_observed_behavior, yuri_observed_behavior,
                    kasho_inferred_feeling, yuri_inferred_feeling,
                    memory_importance, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_number,
                ages["牡丹"]["absolute_day"],
                event_date,
                botan_memory['emotion'],
                botan_memory['action'],
                botan_memory['thought'],
                botan_memory['diary_entry'],
                botan_memory['sister1_observed'],
                botan_memory['sister2_observed'],
                botan_memory['sister1_inferred'],
                botan_memory['sister2_inferred'],
                botan_memory['memory_importance'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            # Insert kasho memory
            cursor.execute('''
                INSERT INTO kasho_memories (
                    event_id, absolute_day, memory_date,
                    kasho_emotion, kasho_action, kasho_thought, diary_entry,
                    botan_observed_behavior, yuri_observed_behavior,
                    botan_inferred_feeling, yuri_inferred_feeling,
                    memory_importance, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_number,
                ages["Kasho"]["absolute_day"],
                event_date,
                kasho_memory['emotion'],
                kasho_memory['action'],
                kasho_memory['thought'],
                kasho_memory['diary_entry'],
                kasho_memory['sister1_observed'],
                kasho_memory['sister2_observed'],
                kasho_memory['sister1_inferred'],
                kasho_memory['sister2_inferred'],
                kasho_memory['memory_importance'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            # Insert yuri memory
            cursor.execute('''
                INSERT INTO yuri_memories (
                    event_id, absolute_day, memory_date,
                    yuri_emotion, yuri_action, yuri_thought, diary_entry,
                    kasho_observed_behavior, botan_observed_behavior,
                    kasho_inferred_feeling, botan_inferred_feeling,
                    memory_importance, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_number,
                ages["ユリ"]["absolute_day"],
                event_date,
                yuri_memory['emotion'],
                yuri_memory['action'],
                yuri_memory['thought'],
                yuri_memory['diary_entry'],
                yuri_memory['sister1_observed'],
                yuri_memory['sister2_observed'],
                yuri_memory['sister1_inferred'],
                yuri_memory['sister2_inferred'],
                yuri_memory['memory_importance'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            conn.close()

            print(f"✅ Event #{event_number} successfully saved to database!\n")
            return True

        except Exception as e:
            print(f"[ERROR] Database insertion failed: {e}")
            return False


class TechnicalLogGenerator:
    """Auto-generate technical analysis logs"""

    def __init__(self, output_dir: str = "/home/koshikawa/toExecUnit/discussion_technical_logs"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def generate_technical_log(
        self,
        state: DiscussionState,
        event_number: int
    ) -> str:
        """Generate technical analysis log"""

        # Count JSON errors
        json_errors = 0  # TODO: track this in v4 system

        # Extract statistics
        total_rounds = state.current_round
        phase_rounds = state.phase_rounds
        total_speeches = len(state.all_speeches)

        # Speaker distribution
        speaker_counts = {}
        for speech in state.all_speeches:
            speaker_counts[speech.speaker] = speaker_counts.get(speech.speaker, 0) + 1

        # Build log
        log = f"""# Discussion #{event_number} Technical Analysis

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**System**: Phase 1.6 v4 Structured Discussion (起承転結)
**Duration**: {total_rounds} rounds
**Topic**: {state.proposal['title']}

---

## Objective Analysis (Developer + Claude Code)

### Discussion Statistics

**Overall**:
- Total rounds: {total_rounds}
- Total speeches: {total_speeches}
- Phase transitions: {len(state.phase_transition_history)}

**Phase-based Round Counts** (v4):
- 起: {phase_rounds['起']} rounds (max 10)
- 承: {phase_rounds['承']} rounds (max 15)
- 転: {phase_rounds['転']} rounds (max 15)
- 結: {phase_rounds['結']} rounds (max 20)

**Speaker Distribution**:
"""

        for sister in ["牡丹", "Kasho", "ユリ"]:
            count = speaker_counts.get(sister, 0)
            log += f"- {sister}: {count} speeches\n"

        log += f"""
---

## System Performance

### v4 Improvements

**Round-based Management**: ✅
- No timeout (time unlimited)
- Phase-based round limits working as expected
- Sisters autonomously managed discussion flow

**Phase Transitions**: {len(state.phase_transition_history)}
"""

        for round_num, phase in state.phase_transition_history:
            log += f"- Round {round_num}: → {phase}\n"

        log += """
---

## Implementation Notes

This discussion was executed by the automated memory manufacturing machine.
Technical improvements and character insights are for developer/Claude Code use only.
Sisters' memories are stored separately in sisters_memory.db.

---

**Recorded by**: Memory Manufacturing Machine (記憶製造機)
**Timestamp**: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"

        # Save to file
        filename = f"discussion_{event_number}_technical.md"
        filepath = f"{self.output_dir}/{filename}"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(log)

        print(f"✅ Technical log saved: {filepath}\n")

        return filepath


class MemoryManufacturingMachine:
    """Main continuous daemon for memory generation"""

    def __init__(self):
        self.proposal_manager = ProposalManager()
        self.topic_selector = FreetalkTopicSelector()
        self.memory_generator = MemoryGenerator()
        self.technical_log_generator = TechnicalLogGenerator()

        # Phase D: Hallucination personalization system
        self.hallucination_personalizer = HallucinationPersonalizer(
            memory_db_path="/home/koshikawa/toExecUnit/sisters_memory.db",
            enable_logging=True
        )

        # Pass personalizer to discussion system
        self.discussion_system = StructuredDiscussionSystem(
            hallucination_personalizer=self.hallucination_personalizer
        )

        self.running = True
        self.current_processing = None

    async def process_proposal(self, proposal: Proposal) -> bool:
        """Process one proposal"""

        print(f"\n{'='*70}")
        print(f"Processing Proposal #{proposal.id}")
        print(f"Priority: {proposal.priority}")
        print(f"Title: {proposal.title}")
        print(f"{'='*70}\n")

        self.current_processing = proposal.id

        # Update status: pending → processing
        self.proposal_manager.update_status(proposal.id, 'processing')

        try:
            # Run structured discussion (v4)
            discussion_proposal = {
                "title": proposal.title,
                "description": proposal.description,
                "priority": proposal.priority
            }

            state = await self.discussion_system.run_structured_discussion(discussion_proposal)

            # Save discussion record (markdown)
            self.discussion_system.save_discussion_record(state)

            # Auto-generate memory (Event #***)
            event_number = self.proposal_manager.get_next_event_id()
            success = await self.memory_generator.save_discussion_as_event(state, event_number)

            if not success:
                print(f"[ERROR] Memory generation failed for #{proposal.id}")
                return False

            # Increment event ID
            self.proposal_manager.increment_event_id()

            # Auto-generate technical log
            tech_log_path = self.technical_log_generator.generate_technical_log(state, event_number)

            # Update status: processing → completed
            result = {
                "event_id": event_number,
                "total_rounds": state.current_round,
                "total_speeches": len(state.all_speeches),
                "technical_log": tech_log_path
            }

            self.proposal_manager.update_status(proposal.id, 'completed', result)

            print(f"\n✅ Proposal #{proposal.id} completed successfully!")
            print(f"   → Event #{event_number} created")
            print(f"   → Technical log: {tech_log_path}\n")

            return True

        except Exception as e:
            print(f"[ERROR] Processing failed: {e}")
            return False

        finally:
            self.current_processing = None

    def auto_propose_free_talk(self):
        """Auto-generate free talk proposal (6hr timer)"""

        print("\n" + "="*70)
        print("Auto Free Talk Proposal Generation")
        print("="*70 + "\n")

        # Check remaining topics and alert if low
        self.topic_selector.check_and_alert_low_topics()

        # Select topic from pool
        topic_data = self.topic_selector.select_topic()

        # Display selected topic
        print(f"Selected topic: {topic_data['theme']}")
        print(f"Type: {topic_data['type']}")
        print(f"Reason: {topic_data['reason']}")
        print(f"Style: {topic_data['expected_style']}")

        if topic_data['type'] == 'autonomous':
            print(f"Initiator: {topic_data['initiator']} -> Target: {topic_data['target']}")

        print()

        # Create proposal
        next_id = self.proposal_manager.get_next_event_id()

        # Build description
        description = "Free talk (6hr timer)\n"
        description += f"Type: {topic_data['type']}\n"
        description += f"Reason: {topic_data['reason']}\n"
        description += f"Style: {topic_data['expected_style']}"

        if topic_data['type'] == 'autonomous':
            description += f"\nInitiator: {topic_data['initiator']} -> Target: {topic_data['target']}"

        proposal = Proposal(
            id=next_id,
            priority="auto",
            status="pending",
            title=topic_data['theme'],
            description=description,
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        self.proposal_manager.add_proposal(proposal)
        self.proposal_manager.increment_event_id()
        self.proposal_manager.update_last_auto_proposal()

        print(f"Auto proposal #{next_id} created!\n")

    def should_auto_propose(self) -> bool:
        """Check if should auto-propose (6hr timer)"""
        last_auto = self.proposal_manager.get_last_auto_proposal_time()

        if last_auto is None:
            return True  # First time

        hours_elapsed = (datetime.now() - last_auto).total_seconds() / 3600

        return hours_elapsed >= 6.0

    def is_idle(self) -> bool:
        """Check if system is idle (no developer proposals pending)"""
        pending = self.proposal_manager.get_pending_proposals()
        developer_pending = [p for p in pending if p.priority == 'developer']

        return len(developer_pending) == 0

    def report_progress(self):
        """Report current progress to developer"""

        proposals = self.proposal_manager.get_all_proposals()

        completed = [p for p in proposals if p.status == 'completed']
        processing = [p for p in proposals if p.status == 'processing']
        pending = [p for p in proposals if p.status == 'pending']

        print(f"\n{'='*70}")
        print("Batch Processing Status")
        print(f"{'='*70}")
        print(f"\n✓ Completed: {len(completed)}")

        for p in completed[-3:]:  # Last 3
            print(f"  - #{p.id}: {p.title}")

        print(f"\n⏳ Processing: {len(processing)}")
        for p in processing:
            print(f"  - #{p.id}: {p.title}")

        print(f"\n📋 Pending: {len(pending)}")
        for p in pending[:6]:  # First 6
            print(f"  - #{p.id}: {p.title} (priority: {p.priority})")

        if len(pending) > 6:
            print(f"  ... and {len(pending) - 6} more")

        total = len(proposals)
        progress = len(completed) / total * 100 if total > 0 else 0

        print(f"\nProgress: {len(completed)}/{total} ({progress:.1f}%)")
        print(f"{'='*70}\n")

    async def run(self):
        """Main loop"""

        print("\n" + "="*70)
        print("Memory Manufacturing Machine (記憶製造機) Started")
        print("="*70)
        print("\nMonitoring proposals.json...")
        print("Priority: developer > auto (6hr) > comment (future)")
        print("\nPress Ctrl+C to stop.\n")

        while self.running:
            try:
                # Report progress every cycle
                self.report_progress()

                # Check for pending proposals
                pending = self.proposal_manager.get_pending_proposals()

                if pending:
                    # Process highest priority proposal
                    proposal = pending[0]
                    await self.process_proposal(proposal)

                else:
                    # No pending proposals
                    print("[INFO] No pending proposals.")

                    # Check if should auto-propose
                    if self.is_idle() and self.should_auto_propose():
                        print("[INFO] Idle for 6+ hours. Generating auto free talk...\n")
                        self.auto_propose_free_talk()

                    else:
                        print("[INFO] Waiting for new proposals...\n")
                        await asyncio.sleep(30)  # Wait 30 seconds

            except KeyboardInterrupt:
                print("\n\n[INFO] Shutting down...\n")
                self.running = False
                break

            except Exception as e:
                print(f"\n[ERROR] Unexpected error: {e}\n")
                await asyncio.sleep(10)


async def main():
    """Main function"""
    machine = MemoryManufacturingMachine()
    await machine.run()


if __name__ == "__main__":
    asyncio.run(main())
