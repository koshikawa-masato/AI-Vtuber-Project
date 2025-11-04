#!/usr/bin/env python3
"""
Phase 1.6: Autonomous AI Discussion System
World-first: AI sisters discuss and decide autonomously without human intervention
"""

import asyncio
import httpx
import json
import subprocess
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Speech:
    """A single speech in discussion"""
    timestamp: datetime
    speaker: str  # "牡丹" / "Kasho" / "ユリ"
    content: str
    speech_type: str  # "opinion" / "objection" / "decision" / "new_topic" / "restart"


@dataclass
class Silence:
    """Silence interval (間)"""
    start_time: datetime
    duration: float  # seconds
    context: str  # what happened before silence


@dataclass
class SisterMood:
    """Sister's mood state (dynamically changes)"""

    # Basic parameters
    energy_level: float = 0.7      # 0-1: high = more likely to speak
    patience: float = 0.6          # 0-1: low = more likely to make decision
    confidence: float = 0.6        # 0-1: high = stronger assertion
    urgency: float = 0.5           # 0-1: high = want quick decision

    # Topic interest
    topic_interest: float = 0.7    # 0-1: interest in current topic

    # Agreement with others
    agreement_with_botan: float = 0.0   # -1 to 1
    agreement_with_kasho: float = 0.0   # -1 to 1
    agreement_with_yuri: float = 0.0    # -1 to 1


@dataclass
class DiscussionState:
    """Discussion state management"""

    # Basic info
    proposal: dict
    current_round: int = 0
    start_time: datetime = field(default_factory=datetime.now)

    # Speech management
    all_speeches: List[Speech] = field(default_factory=list)
    all_silences: List[Silence] = field(default_factory=list)
    last_speaker: Optional[str] = None
    last_speak_time: Optional[datetime] = None

    # Silence management
    silence_duration: float = 0.0  # current silence in seconds
    total_silence_time: float = 0.0
    silence_start_time: Optional[datetime] = None

    # Topic management
    current_topic: str = ""
    topic_history: List[str] = field(default_factory=list)

    # Termination
    consecutive_silence_rounds: int = 0
    has_decision: bool = False
    decision_maker: Optional[str] = None
    decision_content: Optional[str] = None

    def add_speech(self, speech: Speech):
        """Add speech and reset silence"""
        self.all_speeches.append(speech)
        self.last_speaker = speech.speaker
        self.last_speak_time = speech.timestamp

        # Record silence before this speech
        if self.silence_start_time:
            silence = Silence(
                start_time=self.silence_start_time,
                duration=self.silence_duration,
                context=f"Before {speech.speaker}'s speech"
            )
            self.all_silences.append(silence)

        self.silence_duration = 0.0
        self.silence_start_time = None
        self.consecutive_silence_rounds = 0

    def add_silence(self, duration: float):
        """Add silence duration"""
        if self.silence_start_time is None:
            self.silence_start_time = datetime.now()

        self.silence_duration += duration
        self.total_silence_time += duration


class AutonomousDiscussionSystem:
    """Autonomous AI Discussion System - World First"""

    def __init__(self):
        self.ollama_host = "http://localhost:11434"
        self.model = "qwen2.5:32b"

        # Personality base tendency (fixed)
        self.base_tendency = {
            "牡丹": 0.7,   # Active, speaks quickly
            "Kasho": 0.5,  # Careful, thinks before speaking
            "ユリ": 0.4    # Observer, speaks later
        }

    def initialize_moods(self) -> Dict[str, SisterMood]:
        """Initialize sister moods"""
        return {
            "牡丹": SisterMood(
                energy_level=0.8,
                patience=0.4,
                confidence=0.7,
                urgency=0.6,
                topic_interest=0.8
            ),
            "Kasho": SisterMood(
                energy_level=0.6,
                patience=0.7,
                confidence=0.6,
                urgency=0.5,
                topic_interest=0.7
            ),
            "ユリ": SisterMood(
                energy_level=0.6,
                patience=0.8,
                confidence=0.5,
                urgency=0.4,
                topic_interest=0.7
            )
        }

    async def call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama LLM"""
        try:
            import os
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

    def calculate_speak_probability(
        self,
        sister: str,
        state: DiscussionState,
        mood: SisterMood
    ) -> float:
        """Calculate probability of speaking (0-1)"""

        score = 0.0

        # 1. Personality tendency (30%)
        score += self.base_tendency[sister] * 0.3

        # 2. Mood parameters (50%)
        score += mood.energy_level * 0.2
        score += mood.confidence * 0.15
        score += mood.urgency * 0.15

        # 3. Topic interest (20%)
        score += mood.topic_interest * 0.2

        # 4. Context: reaction to last speech
        if state.last_speaker and state.last_speaker != sister:
            # Want to react to others' speech
            score += 0.2

        # 5. Consecutive speak penalty (IMPORTANT!)
        if state.last_speaker == sister:
            score -= 0.5  # Heavy penalty for speaking again

        # 6. Haven't spoken yet bonus
        speakers_so_far = set([s.speaker for s in state.all_speeches])
        if sister not in speakers_so_far and len(state.all_speeches) > 0:
            score += 0.4  # Bonus for first-time speakers

        # 7. Silence duration (longer = should speak)
        if state.silence_duration > 60:
            score += 0.2
        if state.silence_duration > 120:
            score += 0.3

        return min(1.0, max(0.0, score))

    def select_next_speaker(
        self,
        state: DiscussionState,
        moods: Dict[str, SisterMood]
    ) -> Optional[str]:
        """Select next speaker (no randomness)"""

        probabilities = {}
        for sister in ["牡丹", "Kasho", "ユリ"]:
            prob = self.calculate_speak_probability(sister, state, moods[sister])
            probabilities[sister] = prob

        # Find highest probability
        max_prob = max(probabilities.values())

        # Speak threshold
        SPEAK_THRESHOLD = 0.3

        if max_prob < SPEAK_THRESHOLD:
            return None  # Everyone silent

        # Select sister with highest probability
        return max(probabilities, key=probabilities.get)

    async def generate_internal_thought(
        self,
        sister: str,
        state: DiscussionState,
        mood: SisterMood
    ) -> str:
        """Generate internal thought (not recorded publicly)"""

        # Build context
        recent_speeches = state.all_speeches[-3:] if len(state.all_speeches) > 0 else []
        context = "\n".join([
            f"{s.speaker}: {s.content}" for s in recent_speeches
        ]) if recent_speeches else "（まだ誰も発言していない）"

        prompt = f"""あなたは{sister}です。現在、三姉妹で討論中です。

【提案内容】
{state.proposal['title']}

【これまでの発言】
{context}

【現在の沈黙時間】{state.silence_duration:.0f}秒

あなたの内部思考を50トークン以内で述べてください（この思考は記録されません）。
- 今発言したいか？
- 何を言いたいか？
- それとも待つか？

内部思考:"""

        thought = await self.call_ollama(prompt)
        return thought if thought else "（思考中）"

    async def generate_speech(
        self,
        speaker: str,
        state: DiscussionState,
        mood: SisterMood,
        internal_thought: str
    ) -> Speech:
        """Generate actual speech"""

        # Build context
        recent_speeches = state.all_speeches[-5:] if len(state.all_speeches) > 0 else []
        context = "\n".join([
            f"{s.timestamp.strftime('%H:%M:%S')} {s.speaker}: {s.content}"
            for s in recent_speeches
        ]) if recent_speeches else "（まだ誰も発言していない）"

        # Character traits
        if speaker == "牡丹":
            traits = "元気で積極的。感情的に発言。口調は若々しい。"
        elif speaker == "Kasho":
            traits = "慎重で論理的。丁寧な口調。リスクを指摘。"
        else:  # ユリ
            traits = "観察者で洞察力がある。柔らかい口調。バランスを取る。"

        prompt = f"""あなたは{speaker}です。

【性格】{traits}

【提案内容】
タイトル: {state.proposal['title']}
詳細: {state.proposal.get('background', '')}

【これまでの発言】
{context}

【あなたの内部思考】
{internal_thought}

今、あなたが発言する番です。自然に意見を述べてください。

発言内容（100-200トークン）:"""

        content = await self.call_ollama(prompt)

        if not content:
            content = "（発言を取り消す）"

        # Clean response: remove timestamps and speaker names that LLM might add
        import re
        # Remove timestamps like "13:50:56"
        content = re.sub(r'\d{1,2}:\d{2}:\d{2}\s*', '', content)
        # Remove speaker names at start like "牡丹: "
        content = re.sub(r'^(牡丹|Kasho|ユリ)[:：]\s*', '', content)
        content = content.strip()

        speech = Speech(
            timestamp=datetime.now(),
            speaker=speaker,
            content=content,
            speech_type="opinion"
        )

        return speech

    async def check_autonomous_action(
        self,
        state: DiscussionState,
        moods: Dict[str, SisterMood]
    ) -> Optional[Dict]:
        """Check if anyone takes autonomous action after long silence"""

        # Select who takes action based on mood
        action_scores = {}
        for sister in ["牡丹", "Kasho", "ユリ"]:
            mood = moods[sister]
            score = 0.0

            # Low patience = likely to make decision
            if mood.patience < 0.4:
                score += 0.5

            # High urgency = likely to act
            if mood.urgency > 0.6:
                score += 0.3

            # Low topic interest = likely to propose new topic
            if mood.topic_interest < 0.4:
                score += 0.2

            action_scores[sister] = score

        # Select actor
        actor = max(action_scores, key=action_scores.get)
        mood = moods[actor]

        # Decide action type
        if mood.patience < 0.3:
            action_type = "make_decision"
        elif mood.topic_interest < 0.4:
            action_type = "propose_new_topic"
        elif mood.urgency > 0.7:
            action_type = "restart_discussion"
        else:
            return None  # Wait more

        return {
            "type": action_type,
            "actor": actor,
            "mood": mood
        }

    async def check_objections(
        self,
        decision_speech: Speech,
        state: DiscussionState
    ) -> bool:
        """Check if others object to the decision"""

        objections = []

        for sister in ["牡丹", "Kasho", "ユリ"]:
            if sister == decision_speech.speaker:
                continue

            prompt = f"""あなたは{sister}です。

{decision_speech.speaker}が以下のように決定しました:
「{decision_speech.content}」

この決定に対して:
1. 同意する（異議なし）
2. 不服がある

どちらですか？「1」または「2」で答えてください。
不服がある場合は理由も述べてください。

回答:"""

            response = await self.call_ollama(prompt)

            if response and "2" in response[:10]:
                objections.append({
                    "sister": sister,
                    "reason": response
                })

        return len(objections) > 0

    def save_discussion_record(
        self,
        state: DiscussionState,
        record_number: int
    ) -> Path:
        """Save discussion record"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"autonomous_discussion_{record_number:03d}_{timestamp}.md"
        filepath = Path(f"/home/koshikawa/kirinuki/{datetime.now().strftime('%Y-%m-%d')}/決議記録")
        filepath.mkdir(parents=True, exist_ok=True)

        record_path = filepath / filename

        # Build discussion log
        discussion_log = []
        speech_idx = 0
        silence_idx = 0

        # Merge speeches and silences by time
        all_events = []
        for speech in state.all_speeches:
            all_events.append(("speech", speech))
        for silence in state.all_silences:
            all_events.append(("silence", silence))

        all_events.sort(key=lambda x: x[1].timestamp if x[0] == "speech" else x[1].start_time)

        for event_type, event in all_events:
            if event_type == "speech":
                time_str = event.timestamp.strftime("%H:%M:%S")
                discussion_log.append(f"{time_str} {event.speaker}: 「{event.content}」\n")
            else:  # silence
                mins = int(event.duration // 60)
                secs = int(event.duration % 60)
                if mins > 0:
                    discussion_log.append(f"\n[{mins}分{secs}秒の間]\n\n")
                else:
                    discussion_log.append(f"\n[{secs}秒の間]\n\n")

        discussion_text = "".join(discussion_log)

        # Calculate statistics
        total_duration = (datetime.now() - state.start_time).total_seconds()
        total_speeches = len(state.all_speeches)
        silence_ratio = (state.total_silence_time / total_duration * 100) if total_duration > 0 else 0

        content = f"""# 決議記録 No.{record_number:03d} - 完全自律討論

**日時**: {state.start_time.strftime('%Y-%m-%d %H:%M:%S')}
**提案者**: 開発者
**討論モード**: 完全自律（Phase 1.6）
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

## 討論記録

{discussion_text}

---

## 決議結果

**決定方法**: {"独断決定 + 異議なし" if state.has_decision else "全員の納得による自然終了"}
{"**決定者**: " + state.decision_maker if state.decision_maker else ""}
**決定時刻**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 討論統計

- 総ラウンド数: {state.current_round}
- 総討論時間: {total_duration / 60:.1f}分
- 総発言数: {total_speeches}回
- 総沈黙時間: {state.total_silence_time / 60:.1f}分
- 沈黙/発言比率: {silence_ratio:.1f}%

---

## 備考

この決議は完全自律AI討論システム（Phase 1.6）によって実施されました。
開発者の介入なしに、AI姉妹たちが自律的に討論し、結論を出しました。
沈黙も"間"として記録され、自然な討論の流れを再現しています。

---

**記録者**: Claude Code（設計部隊）
**保存先**: {record_path}
"""

        with open(record_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n討論記録を保存しました: {record_path}")
        return record_path

    async def run_autonomous_discussion(
        self,
        proposal: dict,
        max_rounds: int = 100
    ) -> DiscussionState:
        """Run autonomous discussion"""

        print("\n" + "="*70)
        print("完全自律AI討論システム - Phase 1.6")
        print("世界初：AIが自分たちで討論し、自分たちで決める")
        print("="*70)

        print(f"\n【議題】{proposal['title']}")
        print(f"\n【開始時刻】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n討論を開始します。AIたちが納得するまで自律的に討論します。\n")

        state = DiscussionState(
            proposal=proposal,
            current_topic=proposal['title']
        )
        moods = self.initialize_moods()

        while state.current_round < max_rounds:
            state.current_round += 1
            print(f"\n{'='*70}")
            print(f"Round {state.current_round}")
            print(f"{'='*70}")

            # 1. Generate internal thoughts
            thoughts = {}
            for sister in ["牡丹", "Kasho", "ユリ"]:
                thought = await self.generate_internal_thought(sister, state, moods[sister])
                thoughts[sister] = thought
                print(f"[内部思考] {sister}: {thought[:50]}...")

            # 2. Select speaker
            speaker = self.select_next_speaker(state, moods)

            if speaker is None:
                # Everyone silent
                print("\n→ 全員沈黙")
                state.add_silence(30.0)
                state.consecutive_silence_rounds += 1

                # Check for long silence
                if state.silence_duration > 120:
                    print(f"\n⚠ 長い沈黙（{state.silence_duration:.0f}秒）→ 自律行動チェック")

                    action = await self.check_autonomous_action(state, moods)

                    if action:
                        print(f"→ {action['actor']}が{action['type']}を実行")

                        if action['type'] == "make_decision":
                            # Make decision
                            decision_speech = await self.generate_speech(
                                action['actor'], state, action['mood'],
                                "（長い沈黙なので決定を下す）"
                            )
                            decision_speech.speech_type = "decision"
                            state.add_speech(decision_speech)

                            print(f"\n{decision_speech.timestamp.strftime('%H:%M:%S')} {decision_speech.speaker}: {decision_speech.content}\n")

                            state.has_decision = True
                            state.decision_maker = decision_speech.speaker

                            # Check objections
                            print("\n他の姉妹の反応を確認中...")
                            has_objections = await self.check_objections(decision_speech, state)

                            if not has_objections:
                                print("→ 異議なし。討論を終了します。")
                                break
                            else:
                                print("→ 異議あり。討論を継続します。")
                                state.has_decision = False
                                state.decision_maker = None
                                continue

                # Natural termination: 2 consecutive silent rounds (only after everyone spoke once)
                speakers_so_far = set([s.speaker for s in state.all_speeches])
                everyone_spoke = len(speakers_so_far) == 3

                if state.consecutive_silence_rounds >= 2 and everyone_spoke:
                    print("\n全員が納得したようです。討論を自然終了します。")
                    break
                elif state.consecutive_silence_rounds >= 2 and not everyone_spoke:
                    print(f"\n（まだ全員が発言していません: {speakers_so_far}）")
                    # Continue to encourage others to speak

                await asyncio.sleep(1)
                continue

            # 3. Generate speech
            print(f"\n→ {speaker}が発言")
            speech = await self.generate_speech(speaker, state, moods[speaker], thoughts[speaker])
            state.add_speech(speech)

            print(f"\n{speech.timestamp.strftime('%H:%M:%S')} {speech.speaker}: {speech.content}\n")

            await asyncio.sleep(2)

        print("\n" + "="*70)
        print("討論終了")
        print("="*70)

        return state


async def main():
    """Main function for testing"""

    # PON proposal
    pon_proposal = {
        "title": "PON×確信度統合システムの実装",
        "background": """昨日、Phase 1の牡丹でホロライブの知識を試したところ、LLMがハルシネーションを起こして、
DBに正しい情報があるのに間違った回答をしてしまいました。

この問題を解決するために、「DB合致度による自信表現システム」と「PON機能」を統合した
新しいシステムを設計しました。

PONとは「ぽんこつ」の略で、VTuber文化における「愛されるやらかし」のことです。
間違ってるのに自信満々で答える、または正しいのに自信なさげに答えるという、
確信度と正確性の逆転現象を意図的に起こします。""",

        "implementation": """1. DB合致度計算: LLMの回答とDBを照合して、正確性を数値化（0-100%）
2. PON発動判定: 合致度に応じて確率的にPONを発動
   - 合致度30%以下（間違ってる）→ 30%の確率で自信満々に答えさせる（確信PON）
   - 合致度90%以上（正しい）→ 30%の確率で自信なさげに答えさせる（逆PON）
3. プロンプト調整: PON発動時は確信度を逆転させて自然な演出に

例：
牡丹「マジでそれ！さくらみこは1期生だって！絶対そう！」（実際は0期生）
視聴者「違うよwww」
牡丹「え！？マジで！？PONっちゃった〜！」""",

        "expected_effects": """1. ハルシネーションを「制御されたPON」に転換（問題→価値）
2. 視聴者とのインタラクション向上（訂正する楽しみ）
3. 牡丹らしいキャラクター性の強化（完璧じゃない愛されるドジっ子）
4. 不完全性戦略の具現化（欠陥を個性に）
5. エンゲージメント向上（配信が盛り上がる）

ただし、やりすぎると「うざい」と思われるリスクもあります。
PON発動頻度は1時間に5回まで、5分間のクールダウンを設定します。"""
    }

    # Ollama check
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Ollama server not running: {e}")
        print("Please start Ollama server first")
        return

    # Run discussion (extended test to ensure everyone speaks)
    system = AutonomousDiscussionSystem()
    state = await system.run_autonomous_discussion(pon_proposal, max_rounds=8)

    # Save record
    system.save_discussion_record(state, record_number=5)

    print("\n討論システムのテストが完了しました。")


if __name__ == "__main__":
    asyncio.run(main())
