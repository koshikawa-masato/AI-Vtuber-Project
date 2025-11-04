#!/usr/bin/env python3
"""
Phase 1.6 v2: Emotional Tracking Autonomous Discussion System
Adds emotion tracking, sister dynamics, and internal thoughts
"""

import asyncio
import httpx
import json
import subprocess
import os
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class EmotionalState:
    """Sister's emotional state during discussion"""

    # Basic emotions (0-1)
    energy: float = 0.7
    confidence: float = 0.6
    tension: float = 0.3
    satisfaction: float = 0.5

    # Interpersonal (0-1 or -1 to 1)
    agreement_level: float = 0.5
    concern_level: float = 0.3
    frustration: float = 0.0

    # Sister dynamics (0-1)
    want_to_support: float = 0.7
    want_to_object: float = 0.2
    defer_to_sister: float = 0.4

    # Meta emotions (0-1)
    want_to_end: float = 0.0
    still_have_to_say: float = 0.8

    def to_display_string(self) -> str:
        """Format for display"""
        return (f"[元気:{self.energy:.1f} | 自信:{self.confidence:.1f} | "
                f"緊張:{self.tension:.1f} | 満足:{self.satisfaction:.1f}]")

    def to_detailed_string(self) -> str:
        """Detailed format"""
        return (f"[元気:{self.energy:.1f} | 自信:{self.confidence:.1f} | "
                f"緊張:{self.tension:.1f} | 満足:{self.satisfaction:.1f}]\n"
                f"[賛同:{self.agreement_level:.1f} | 懸念:{self.concern_level:.1f} | "
                f"終了意欲:{self.want_to_end:.1f}]")


@dataclass
class InternalEmotion:
    """Internal thoughts and feelings before speaking"""
    reaction: str                    # Emotional reaction to last speech
    position: str                    # Agree/disagree and why
    sister_dynamics: str             # Feelings from sister relationship
    speak_or_defer: str              # Should speak now or defer
    end_timing: str                  # When to end discussion


@dataclass
class Speech:
    """A single speech with emotional context"""
    timestamp: datetime
    speaker: str
    internal_emotion: Optional[InternalEmotion]
    content: str
    emotion_changes: Dict[str, float]
    speech_type: str = "opinion"


@dataclass
class DiscussionState:
    """Discussion state with emotional tracking"""

    proposal: dict
    current_round: int = 0
    start_time: datetime = field(default_factory=datetime.now)

    all_speeches: List[Speech] = field(default_factory=list)
    last_speaker: Optional[str] = None
    last_speak_time: Optional[datetime] = None

    # Emotion tracking per round
    emotion_history: List[Dict[str, EmotionalState]] = field(default_factory=list)

    consecutive_silence_rounds: int = 0
    has_decision: bool = False
    decision_maker: Optional[str] = None


class EmotionalDiscussionSystem:
    """Emotional Tracking Autonomous Discussion System"""

    def __init__(self):
        self.ollama_host = "http://localhost:11434"
        self.model = "qwen2.5:32b"

        # Base personality tendency
        self.base_tendency = {
            "牡丹": 0.7,
            "Kasho": 0.5,
            "ユリ": 0.4
        }

        # Initial emotional states
        self.emotions = {
            "牡丹": EmotionalState(
                energy=0.8,
                confidence=0.7,
                tension=0.3,
                want_to_support=0.6,  # toward Kasho
                defer_to_sister=0.6   # Kasho is elder sister
            ),
            "Kasho": EmotionalState(
                energy=0.6,
                confidence=0.8,
                tension=0.2,
                want_to_support=0.8,  # toward 牡丹 (younger)
                defer_to_sister=0.2   # eldest
            ),
            "ユリ": EmotionalState(
                energy=0.6,
                confidence=0.5,
                tension=0.4,
                want_to_support=0.7,  # toward both
                defer_to_sister=0.7   # youngest
            )
        }

        # Emotion history
        self.emotion_history = []

    def get_character_profile(self, sister: str) -> str:
        """Get detailed character profile"""
        profiles = {
            "牡丹": """- 次女、19歳
- 性格: 元気で積極的、感情表現が豊か、新しいアイデアを思いつく
- 口調: 「ねぇねぇ」「〜だよね！」「マジで」など若々しく元気
- 姉妹関係: Kashoは頼れる姉（意見を尊重）、ユリは可愛い妹（説明的）
- 内面: 自分のアイデアを認めてほしい、でも姉には逆らいにくい""",

            "Kasho": """- 長女、19歳
- 性格: 慎重で論理的、分析的、責任感が強い
- 口調: 丁寧で落ち着いている、「〜ね」「〜わ」「〜だろう」
- 姉妹関係: 牡丹とユリは妹（応援したいが、責任も感じる）
- 内面: 妹たちを応援したい、でも姉として慎重さを伝える責任がある""",

            "ユリ": """- 三女、15歳
- 性格: 観察力があり洞察的、優しく調和を重視
- 口調: 柔らかく控えめ、「〜かも」「〜だね」「その...」
- 姉妹関係: 牡丹とKashoは姉（尊敬、でも対等に話したい）
- 内面: 二人の橋渡しをしたい、末っ子だけど意見も言いたい"""
        }
        return profiles[sister]

    def get_relationship(self, sister: str, other: str) -> str:
        """Get sister relationship description"""
        relationships = {
            ("牡丹", "Kasho"): "あなたの姉（頼れる存在、意見を尊重すべき）",
            ("牡丹", "ユリ"): "あなたの妹（可愛い存在、説明してあげたい）",
            ("Kasho", "牡丹"): "あなたの妹（応援したい存在、でも慎重さも伝えたい）",
            ("Kasho", "ユリ"): "あなたの妹（守るべき存在、優しく見守りたい）",
            ("ユリ", "牡丹"): "あなたの姉（元気な存在、尊敬している）",
            ("ユリ", "Kasho"): "あなたの姉（尊敬する存在、頼りにしている）"
        }
        return relationships.get((sister, other), "姉妹")

    async def call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama LLM"""
        try:
            result = subprocess.run(
                ["/usr/local/bin/ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, "OLLAMA_HOST": self.ollama_host}
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"[ERROR] Ollama error: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print("[ERROR] Ollama timeout")
            return None
        except Exception as e:
            print(f"[ERROR] Ollama call failed: {e}")
            return None

    def parse_json_response(self, response: str) -> Optional[dict]:
        """Parse JSON from LLM response"""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1

            if start == -1 or end == 0:
                print("[ERROR] No JSON found")
                return None

            json_str = response[start:end]
            data = json.loads(json_str)
            return data

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parse error: {e}")
            print(f"[DEBUG] Response: {response[:300]}...")
            return None

    async def generate_emotional_response(
        self,
        sister: str,
        last_speech: Optional[Speech],
        state: DiscussionState
    ) -> Optional[dict]:
        """Generate emotional response with internal thoughts"""

        emotion = self.emotions[sister]
        profile = self.get_character_profile(sister)

        # Build context
        if last_speech:
            relationship = self.get_relationship(sister, last_speech.speaker)
            last_content = last_speech.content
            last_speaker = last_speech.speaker
        else:
            relationship = "提案者（開発者）"
            last_content = state.proposal['title']
            last_speaker = "開発者"

        prompt = f"""あなたは{sister}です。

【あなたの性格・特徴】
{profile}

【前の発言】
{last_speaker}: 「{last_content}」

【{last_speaker}との関係】
{relationship}

【あなたの現在の感情状態】
{emotion.to_detailed_string()}

【内部感情を生成してください】
以下の5つの観点から、あなたの内心を率直に述べてください：

1. **発言への感情的反応**: {last_speaker}の発言を聞いてどう感じたか（率直に、本音で）
2. **立場と理由**: 賛成か反対か、なぜそう思うのか
3. **姉妹関係からくる気持ち**: 姉妹だからこその感情（妥協したい、でも言いたい、応援したい、心配、など）
4. **発言すべきか**: 今発言すべきか、それとも黙って譲るべきか
5. **終了タイミング**: この討論をいつ終わらせるべきか（まだ早い/そろそろ/もういい）

【発言を生成してください】
内部感情を踏まえて、{sister}らしく自然に発言してください。
性格と口調を反映させてください。

出力JSON:
{{
    "internal_emotion": {{
        "reaction": "発言への感情的反応（率直な本音）",
        "position": "賛成/反対とその理由",
        "sister_dynamics": "姉妹関係からくる気持ち・葛藤",
        "speak_or_defer": "今発言すべきか/譲るべきか",
        "end_timing": "討論終了のタイミング判断"
    }},
    "speech": "{sister}らしい発言（口調と性格を反映）",
    "emotion_changes": {{
        "confidence": 0.0,
        "agreement_level": 0.0,
        "want_to_end": 0.0,
        "satisfaction": 0.0
    }}
}}

重要: 必ず有効なJSONを返してください。"""

        response = await self.call_ollama(prompt)

        if not response:
            return None

        data = self.parse_json_response(response)
        return data

    def update_emotion(self, sister: str, changes: Dict[str, float]):
        """Update sister's emotional state"""
        emotion = self.emotions[sister]

        for key, value in changes.items():
            if hasattr(emotion, key):
                current = getattr(emotion, key)
                new_value = max(0.0, min(1.0, current + value))
                setattr(emotion, key, new_value)

    def calculate_speak_probability(
        self,
        sister: str,
        state: DiscussionState,
        emotion: EmotionalState
    ) -> float:
        """Calculate speak probability based on emotion"""

        score = 0.0

        # Base tendency
        score += self.base_tendency[sister] * 0.3

        # Emotional state
        score += emotion.energy * 0.2
        score += emotion.confidence * 0.15
        score += emotion.still_have_to_say * 0.2

        # Consecutive speak penalty
        if state.last_speaker == sister:
            score -= 0.5

        # Haven't spoken yet bonus
        speakers_so_far = set([s.speaker for s in state.all_speeches])
        if sister not in speakers_so_far and len(state.all_speeches) > 0:
            score += 0.4

        # Want to end
        if emotion.want_to_end > 0.7:
            score -= 0.3

        return min(1.0, max(0.0, score))

    def select_next_speaker(
        self,
        state: DiscussionState
    ) -> Optional[str]:
        """Select next speaker based on emotions"""

        probabilities = {}
        for sister in ["牡丹", "Kasho", "ユリ"]:
            prob = self.calculate_speak_probability(
                sister, state, self.emotions[sister]
            )
            probabilities[sister] = prob

        max_prob = max(probabilities.values())

        SPEAK_THRESHOLD = 0.3

        if max_prob < SPEAK_THRESHOLD:
            return None

        return max(probabilities, key=probabilities.get)

    async def run_emotional_discussion(
        self,
        proposal: dict,
        max_rounds: int = 100
    ) -> DiscussionState:
        """Run emotional tracking discussion"""

        print("\n" + "="*70)
        print("感情トラッキング討論システム - Phase 1.6 v2")
        print("三姉妹の感情と内面を記録")
        print("="*70)

        print(f"\n【議題】{proposal['title']}")
        print(f"\n【開始時刻】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        state = DiscussionState(proposal=proposal)

        # Record initial emotions
        self.emotion_history.append(self.emotions.copy())

        while state.current_round < max_rounds:
            state.current_round += 1

            print(f"\n{'='*70}")
            print(f"Round {state.current_round}")
            print(f"{'='*70}\n")

            # Display emotions
            print("【Round開始時の感情状態】")
            for sister in ["牡丹", "Kasho", "ユリ"]:
                print(f"{sister}: {self.emotions[sister].to_display_string()}")
            print()

            # Select speaker
            speaker = self.select_next_speaker(state)

            if speaker is None:
                print("→ 全員沈黙\n")
                state.consecutive_silence_rounds += 1

                # Check termination
                speakers_so_far = set([s.speaker for s in state.all_speeches])
                everyone_spoke = len(speakers_so_far) == 3

                if state.consecutive_silence_rounds >= 2 and everyone_spoke:
                    print("全員が納得したようです。討論を終了します。\n")
                    break

                await asyncio.sleep(1)
                continue

            # Generate emotional response
            print(f"→ {speaker}が発言準備中...\n")

            last_speech = state.all_speeches[-1] if state.all_speeches else None
            response_data = await self.generate_emotional_response(
                speaker, last_speech, state
            )

            if not response_data:
                print(f"[ERROR] {speaker}の応答生成失敗\n")
                continue

            # Create speech
            internal = InternalEmotion(**response_data['internal_emotion'])

            speech = Speech(
                timestamp=datetime.now(),
                speaker=speaker,
                internal_emotion=internal,
                content=response_data['speech'],
                emotion_changes=response_data.get('emotion_changes', {})
            )

            # Display internal emotion
            print(f"【{speaker}の内部感情】")
            print(f"- 発言への反応: {internal.reaction}")
            print(f"- 立場: {internal.position}")
            print(f"- 姉妹として: {internal.sister_dynamics}")
            print(f"- 判断: {internal.speak_or_defer}")
            print(f"- 終了判断: {internal.end_timing}\n")

            # Display speech
            print(f"【{speech.timestamp.strftime('%H:%M:%S')} {speaker}の発言】")
            print(f"「{speech.content}」\n")

            # Update emotions
            self.update_emotion(speaker, speech.emotion_changes)

            # Display emotion changes
            if any(v != 0 for v in speech.emotion_changes.values()):
                print(f"【感情変化】")
                for key, value in speech.emotion_changes.items():
                    if value != 0:
                        print(f"- {key}: {value:+.2f}")
                print()

            # Record
            state.all_speeches.append(speech)
            state.last_speaker = speaker
            state.last_speak_time = speech.timestamp
            state.consecutive_silence_rounds = 0

            # Record emotions after this round
            self.emotion_history.append(self.emotions.copy())

            await asyncio.sleep(2)

        print("="*70)
        print("討論終了")
        print("="*70)

        return state

    def save_emotional_record(self, state: DiscussionState, record_number: int):
        """Save emotional tracking record"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"emotional_discussion_{record_number:03d}_{timestamp}.md"
        filepath = Path(f"/home/koshikawa/kirinuki/{datetime.now().strftime('%Y-%m-%d')}/決議記録")
        filepath.mkdir(parents=True, exist_ok=True)

        record_path = filepath / filename

        content = f"""# 決議記録 No.{record_number:03d} - 感情トラッキング討論

**日時**: {state.start_time.strftime('%Y-%m-%d %H:%M:%S')}
**討論モード**: 完全自律 + 感情トラッキング（Phase 1.6 v2)
**決議種別**: Tier 2 - キャラクター設定

---

## 提案内容

**タイトル**: {state.proposal['title']}

**背景・理由**:
{state.proposal.get('background', '')}

**実装内容**:
{state.proposal.get('implementation', '')}

**期待される効果**:
{state.proposal.get('expected_effects', '')}

---

## 討論前の感情状態

"""

        # Initial emotions
        initial_emotions = self.emotion_history[0]
        for sister in ["牡丹", "Kasho", "ユリ"]:
            content += f"**{sister}:** {initial_emotions[sister].to_display_string()}\n"

        content += "\n---\n\n## 討論記録\n\n"

        # Each round
        for round_num in range(1, state.current_round + 1):
            content += f"### Round {round_num}\n\n"

            # Round emotions
            if round_num - 1 < len(self.emotion_history):
                round_emotions = self.emotion_history[round_num - 1]
                content += "**感情状態:**\n"
                for sister in ["牡丹", "Kasho", "ユリ"]:
                    content += f"- {sister}: {round_emotions[sister].to_display_string()}\n"
                content += "\n"

            # Speeches in this round
            round_speeches = [s for s in state.all_speeches
                            if s.timestamp >= state.start_time]

            for speech in round_speeches:
                if speech.internal_emotion:
                    content += f"**{speech.timestamp.strftime('%H:%M:%S')} {speech.speaker}の発言**\n\n"
                    content += f"*[内部感情]*\n"
                    content += f"- 反応: {speech.internal_emotion.reaction}\n"
                    content += f"- 立場: {speech.internal_emotion.position}\n"
                    content += f"- 姉妹として: {speech.internal_emotion.sister_dynamics}\n"
                    content += f"- 判断: {speech.internal_emotion.speak_or_defer}\n"
                    content += f"- 終了判断: {speech.internal_emotion.end_timing}\n\n"
                    content += f"*[発言]*\n「{speech.content}」\n\n"

                    if speech.emotion_changes:
                        content += f"*[感情変化]*\n"
                        for key, value in speech.emotion_changes.items():
                            if value != 0:
                                content += f"- {key}: {value:+.2f}\n"
                        content += "\n"

                    content += "---\n\n"

        # Final emotions
        content += "## 討論後の感情状態\n\n"

        final_emotions = self.emotions
        initial_emotions = self.emotion_history[0]

        for sister in ["牡丹", "Kasho", "ユリ"]:
            final = final_emotions[sister]
            initial = initial_emotions[sister]

            content += f"### {sister}\n\n"
            content += f"- 自信: {initial.confidence:.2f} → {final.confidence:.2f} "
            content += f"({final.confidence - initial.confidence:+.2f})\n"
            content += f"- 満足度: {initial.satisfaction:.2f} → {final.satisfaction:.2f} "
            content += f"({final.satisfaction - initial.satisfaction:+.2f})\n"
            content += f"- 終了意欲: {initial.want_to_end:.2f} → {final.want_to_end:.2f}\n\n"

        content += f"""---

## 備考

この決議は感情トラッキング討論システム（Phase 1.6 v2）で実施されました。
各姉妹の内部感情、姉妹関係の力学、感情変化を記録しています。

---

**記録者**: Claude Code（設計部隊）
**保存先**: {record_path}
"""

        with open(record_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n感情トラッキング記録を保存しました: {record_path}")
        return record_path


async def main():
    """Test emotional discussion system"""

    pon_proposal = {
        "title": "PON×確信度統合システムの実装",
        "background": """昨日、Phase 1の牡丹でホロライブの知識を試したところ、LLMがハルシネーションを起こして、
DBに正しい情報があるのに間違った回答をしてしまいました。

この問題を解決するために、「DB合致度による自信表現システム」と「PON機能」を統合した
新しいシステムを設計しました。

PONとは「ぽんこつ」の略で、VTuber文化における「愛されるやらかし」のことです。""",

        "implementation": """1. DB合致度計算: LLMの回答とDBを照合して、正確性を数値化（0-100%）
2. PON発動判定: 合致度に応じて確率的にPONを発動
3. プロンプト調整: PON発動時は確信度を逆転させて自然な演出に""",

        "expected_effects": """1. ハルシネーションを「制御されたPON」に転換（問題→価値）
2. 視聴者とのインタラクション向上（訂正する楽しみ）
3. 牡丹らしいキャラクター性の強化（完璧じゃない愛されるドジっ子）"""
    }

    # Ollama check
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Ollama server not running: {e}")
        return

    # Run emotional discussion
    system = EmotionalDiscussionSystem()
    state = await system.run_emotional_discussion(pon_proposal, max_rounds=5)

    # Save record
    system.save_emotional_record(state, record_number=6)

    print("\n感情トラッキング討論システムのテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
