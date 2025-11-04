#!/usr/bin/env python3
"""
Generate memory from existing discussion log
Event #109 specific memory generation from discussion_109_cleaned.log

Author: Claude Code (設計部隊)
Date: 2025-10-23
"""

import asyncio
import json
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import personality cores
from personality_core import BotanPersonality, KashoPersonality, YuriPersonality


class MemoryFromLogGenerator:
    """Generate memories from discussion log file"""

    def __init__(self, db_path: str = "/home/koshikawa/toExecUnit/botan_phase1.5/sisters_memory.db"):
        self.db_path = db_path
        self.model = "qwen2.5:32b"

        # Initialize personality cores
        self.personalities = {
            "牡丹": BotanPersonality(),
            "Kasho": KashoPersonality(),
            "ユリ": YuriPersonality()
        }
        print("[MemoryFromLog] Personality cores initialized")

    async def call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama LLM"""
        try:
            result = subprocess.run(
                ["/usr/local/bin/ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes for longer responses
            )

            if result.returncode != 0:
                print(f"[ERROR] Ollama failed: {result.stderr}")
                return None

            return result.stdout.strip()

        except Exception as e:
            print(f"[ERROR] Ollama call failed: {e}")
            return None

    def parse_discussion_log(self, log_path: str) -> dict:
        """Parse discussion log file to extract key information"""
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract topic (from line 11)
        lines = content.split('\n')
        topic = ""
        for line in lines:
            if line.startswith("【議題】"):
                topic = line.replace("【議題】", "").strip()
                break

        return {
            "topic": topic,
            "full_log": content
        }

    async def generate_sister_memory(
        self,
        sister: str,
        log_data: dict,
        event_number: int,
        event_date: datetime
    ) -> Optional[dict]:
        """Generate one sister's memory from log"""

        # Get other sisters
        all_sisters = ["牡丹", "Kasho", "ユリ"]
        other_sisters = [s for s in all_sisters if s != sister]

        # Get personality traits
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
{log_data['topic']}

【討論の全記録】
{log_data['full_log']}

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
- 結論が出なかった、決まらなかった、という経験も大切な記憶

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

        print(f"\n[{sister}] Generating memory...")
        response = await self.call_ollama(prompt)

        if not response:
            print(f"[{sister}] Failed to generate memory")
            return None

        # Extract JSON
        try:
            # Find JSON block
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                print(f"[{sister}] No JSON found in response")
                return None

            json_str = response[json_start:json_end]
            memory_data = json.loads(json_str)

            print(f"[{sister}] Memory generated successfully")
            return memory_data

        except json.JSONDecodeError as e:
            print(f"[{sister}] JSON parse error: {e}")
            return None

    def save_to_db(
        self,
        event_number: int,
        event_date: datetime,
        topic: str,
        memories: dict
    ):
        """Save memories to database"""

        # Ensure DB directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables if not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_events (
                event_id INTEGER PRIMARY KEY,
                event_date TEXT NOT NULL,
                event_title TEXT NOT NULL,
                event_description TEXT,
                decision_made TEXT,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sister_memories (
                memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                sister_name TEXT NOT NULL,
                subjective_memory TEXT NOT NULL,
                emotion TEXT,
                importance INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (event_id) REFERENCES shared_events(event_id)
            )
        """)

        # Insert shared event
        cursor.execute("""
            INSERT OR REPLACE INTO shared_events
            (event_id, event_date, event_title, event_description, decision_made, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event_number,
            event_date.strftime("%Y-%m-%d"),
            topic,
            "Cultural festival cosplay cafe discussion",
            "Wizard maid (not finalized, needs cost estimate)",
            datetime.now().isoformat()
        ))

        # Insert sister memories
        for sister, memory_data in memories.items():
            if memory_data:
                cursor.execute("""
                    INSERT INTO sister_memories
                    (event_id, sister_name, subjective_memory, emotion, importance, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event_number,
                    sister,
                    memory_data['diary_entry'],
                    memory_data['emotion'],
                    memory_data['memory_importance'],
                    datetime.now().isoformat()
                ))

        conn.commit()
        conn.close()

        print(f"\n[DB] Event #{event_number} saved to {self.db_path}")


async def main():
    """Main function"""
    print("=" * 70)
    print("Event #109 Memory Generation from Log")
    print("=" * 70)

    # Configuration
    log_path = "/tmp/discussion_109_cleaned.log"
    event_number = 109
    event_date = datetime(2025, 10, 23)

    # Check log file exists
    if not Path(log_path).exists():
        print(f"[ERROR] Log file not found: {log_path}")
        return

    # Initialize generator
    generator = MemoryFromLogGenerator()

    # Parse log
    print(f"\n[1/4] Parsing discussion log...")
    log_data = generator.parse_discussion_log(log_path)
    print(f"  Topic: {log_data['topic']}")

    # Generate memories for all sisters
    print(f"\n[2/4] Generating memories from LLM (Phase 4 with personality)...")
    memories = {}

    for sister in ["牡丹", "Kasho", "ユリ"]:
        memory = await generator.generate_sister_memory(
            sister, log_data, event_number, event_date
        )
        memories[sister] = memory

        if memory:
            print(f"  ✅ {sister}: {memory['emotion']}")
        else:
            print(f"  ❌ {sister}: Failed")

    # Save to DB
    print(f"\n[3/4] Saving to database...")
    generator.save_to_db(event_number, event_date, log_data['topic'], memories)

    # Display results
    print(f"\n[4/4] Memory generation complete!")
    print(f"\nEvent #{event_number}: {log_data['topic']}")
    print(f"Date: {event_date.strftime('%Y-%m-%d')}")
    print(f"\nMemories generated:")

    for sister, memory in memories.items():
        if memory:
            print(f"\n【{sister}】")
            print(f"  感情: {memory['emotion']}")
            print(f"  重要度: {memory['memory_importance']}/10")
            print(f"  日記: {memory['diary_entry'][:100]}...")

    print(f"\n" + "=" * 70)
    print(f"Database: {generator.db_path}")
    print(f"=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
