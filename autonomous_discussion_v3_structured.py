#!/usr/bin/env python3
"""
Phase 1.6 v3: Structured Discussion System with 起承転結
Complete autonomous discussion with emotional tracking and structured phases

Key improvements from v2:
1. 起承転結 (Introduction-Development-Turn-Conclusion) phases
2. Full context reference (not just last speech)
3. Phase-aware prompts
4. Argument extraction
5. Discussion progression tracking
"""

import asyncio
import json
import subprocess
import re
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, field

@dataclass
class EmotionalState:
    """Sister's emotional state"""
    # Basic emotions (0-1)
    energy: float = 0.7
    confidence: float = 0.6
    tension: float = 0.3
    satisfaction: float = 0.5

    # Interpersonal (0-1)
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
        return f"[元気:{self.energy:.1f} | 自信:{self.confidence:.1f} | 緊張:{self.tension:.1f} | 満足:{self.satisfaction:.1f}]"

    def to_detailed_string(self) -> str:
        return f"""- 元気: {self.energy:.1f}
- 自信: {self.confidence:.1f}
- 緊張: {self.tension:.1f}
- 満足: {self.satisfaction:.1f}
- 賛成度: {self.agreement_level:.1f}
- 懸念: {self.concern_level:.1f}
- 不満: {self.frustration:.1f}"""

@dataclass
class InternalEmotion:
    """Internal emotional response"""
    reaction: str  # 発言への感情的反応
    position: str  # 立場と理由
    sister_dynamics: str  # 姉妹関係からくる気持ち
    speak_or_defer: str  # 発言すべきか譲るべきか
    end_timing: str  # 討論終了のタイミング判断

@dataclass
class Speech:
    """A speech in the discussion"""
    timestamp: datetime
    speaker: str
    round_number: int
    phase: str  # 起承転結
    internal_emotion: InternalEmotion
    content: str
    emotion_changes: Dict[str, float] = field(default_factory=dict)

@dataclass
class DiscussionState:
    """Discussion state tracking"""
    proposal: dict
    current_round: int = 0
    current_phase: str = "起"
    all_speeches: List[Speech] = field(default_factory=list)
    last_speaker: Optional[str] = None
    consecutive_silence_rounds: int = 0
    silence_duration: float = 0.0

class DiscussionPhase:
    """Discussion phase constants"""
    INTRODUCTION = "起"  # Round 1-2: Proposal
    DEVELOPMENT = "承"   # Round 3-5: Questions
    TURN = "転"          # Round 6-8: Debate
    CONCLUSION = "結"    # Round 9+: Agreement

class StructuredDiscussionSystem:
    """Phase 1.6 v3: Structured discussion with 起承転結"""

    def __init__(self, model: str = "qwen2.5:32b"):
        self.model = model

        # Emotional states
        self.emotions = {
            "牡丹": EmotionalState(energy=0.8, confidence=0.7),
            "Kasho": EmotionalState(energy=0.6, confidence=0.8, tension=0.2),
            "ユリ": EmotionalState(energy=0.6, confidence=0.5, tension=0.4)
        }

        # Character tendency (base probability)
        self.base_tendency = {
            "牡丹": 0.5,   # Active
            "Kasho": 0.4,  # Moderate
            "ユリ": 0.3    # Reserved
        }

    async def call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama LLM"""
        try:
            result = subprocess.run(
                ["/usr/local/bin/ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                print(f"[ERROR] Ollama failed: {result.stderr}")
                return None

            response = result.stdout.strip()
            return response if response else None

        except Exception as e:
            print(f"[ERROR] Ollama call failed: {e}")
            return None

    def get_current_phase(self, round_number: int) -> str:
        """Determine current discussion phase"""
        if round_number <= 2:
            return DiscussionPhase.INTRODUCTION
        elif round_number <= 5:
            return DiscussionPhase.DEVELOPMENT
        elif round_number <= 8:
            return DiscussionPhase.TURN
        else:
            return DiscussionPhase.CONCLUSION

    def get_character_profile(self, sister: str) -> str:
        """Get character personality profile"""
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
        return profiles.get(sister, "")

    def get_relationship(self, sister: str, other: str) -> str:
        """Get relationship description"""
        relationships = {
            ("牡丹", "Kasho"): "頼れる姉。論理的で慎重。尊敬しているが、時には大胆さも必要だと思う。",
            ("牡丹", "ユリ"): "可愛い妹。優しくバランス感覚がある。守ってあげたいけど、意見も聞きたい。",
            ("Kasho", "牡丹"): "元気な妹。アイデアは面白いが、時に慎重さが足りない。応援したいが心配も。",
            ("Kasho", "ユリ"): "優しい妹。洞察力がある。もっと自信を持ってほしい。",
            ("ユリ", "牡丹"): "明るい姉。行動力がある。尊敬しているが、時に突っ走りすぎる。",
            ("ユリ", "Kasho"): "頼れる姉。論理的で安心感がある。でも二人の間に入りたい。"
        }
        return relationships.get((sister, other), "姉妹")

    def build_full_context(self, state: DiscussionState) -> str:
        """Build full discussion context"""
        if not state.all_speeches:
            return "（まだ誰も発言していません）"

        context = []
        for speech in state.all_speeches:
            context.append(
                f"Round {speech.round_number}({speech.phase}) {speech.speaker}: {speech.content}"
            )

        return "\n".join(context)

    async def extract_key_points(self, state: DiscussionState) -> str:
        """Extract key arguments from 起・承 phases"""
        speeches = [s for s in state.all_speeches if s.round_number <= 5]

        if not speeches:
            return "（まだ論点が出ていません）"

        context = "\n".join([
            f"Round {s.round_number} {s.speaker}: {s.content}"
            for s in speeches
        ])

        prompt = f"""以下の討論（起・承の段階）から、主要な論点を3-5個抽出してください。
簡潔に箇条書きで。

{context}

主要論点:"""

        summary = await self.call_ollama(prompt)
        return summary if summary else "（論点抽出失敗）"

    async def extract_conflicts(self, state: DiscussionState) -> str:
        """Extract conflicts from 転 phase"""
        speeches = [s for s in state.all_speeches if 6 <= s.round_number <= 8]

        if not speeches:
            return "（まだ対立点の議論に至っていません）"

        context = "\n".join([
            f"Round {s.round_number} {s.speaker}: {s.content}"
            for s in speeches
        ])

        prompt = f"""以下の討論（転の段階）から、主要な対立点や異なる視点を抽出してください。
簡潔に箇条書きで。

{context}

主要な対立点:"""

        summary = await self.call_ollama(prompt)
        return summary if summary else "（対立点抽出失敗）"

    def get_phase_instruction(self, phase: str, round_number: int) -> str:
        """Get phase-specific instructions"""
        instructions = {
            "起": f"""【討論段階】起 - 提案・問題提起（Round {round_number}/1-2）

【あなたの役割】
- 提案内容を理解する
- 初期の立場を表明する（賛成/反対/条件付き賛成）
- 第一印象を述べる

【避けるべきこと】
- まだ詳細な質問はしない（承でやる）
- まだ対立点を深掘りしない（転でやる）""",

            "承": f"""【討論段階】承 - 質問・懸念（Round {round_number}/3-5）

【あなたの役割】
- 不明点を質問する
- 懸念事項を表明する
- 詳細な説明を求める
- 前回の発言を深掘りする

【重要】
前の発言から議論を「深化」させてください。
同じことを繰り返さないでください。""",

            "転": f"""【討論段階】転 - 対立点・深い議論（Round {round_number}/6-8）

【あなたの役割】
- 意見の違いを明確にする
- 複数の選択肢を比較する
- リスクとベネフィットを議論する
- 対立点を深く掘り下げる

【重要】
ここで討論が最も深くなります。
表面的な賛成/反対ではなく、「なぜ」「どのように」を議論してください。""",

            "結": f"""【討論段階】結 - 合意形成（Round {round_number}/9+）

【あなたの役割】
- 妥協点を模索する
- 合意できる部分を確認する
- 決定事項を整理する
- 次のステップを提案する

【重要】
討論を収束させる段階です。
合意形成に向けて建設的に話してください。"""
        }
        return instructions.get(phase, "")

    async def generate_phase_aware_response(
        self,
        sister: str,
        state: DiscussionState
    ) -> Optional[dict]:
        """Generate phase-aware emotional response"""

        phase = self.get_current_phase(state.current_round)
        emotion = self.emotions[sister]
        profile = self.get_character_profile(sister)

        # Build full context
        full_context = self.build_full_context(state)

        # Get last speaker info
        if state.all_speeches:
            last_speech = state.all_speeches[-1]
            relationship = self.get_relationship(sister, last_speech.speaker)
            last_speaker = last_speech.speaker
        else:
            relationship = "提案者（開発者）"
            last_speaker = "開発者"

        # Phase-specific context
        phase_instruction = self.get_phase_instruction(phase, state.current_round)

        # Extract key points/conflicts if needed
        additional_context = ""
        if phase == "転":
            key_points = await self.extract_key_points(state)
            additional_context = f"\n【起・承で出た主要な論点】\n{key_points}\n"
        elif phase == "結":
            key_points = await self.extract_key_points(state)
            conflicts = await self.extract_conflicts(state)
            additional_context = f"\n【主要な論点】\n{key_points}\n\n【転で議論された対立点】\n{conflicts}\n"

        prompt = f"""あなたは{sister}です。

【あなたの性格・特徴】
{profile}

{phase_instruction}

【これまでの全発言】
{full_context}
{additional_context}
【あなたの現在の感情状態】
{emotion.to_detailed_string()}

【内部感情を生成してください】
以下の5つの観点から、あなたの内心を率直に述べてください：

1. **発言への感情的反応**: これまでの討論を聞いてどう感じたか（率直に、本音で）
2. **立場と理由**: 賛成か反対か、なぜそう思うのか
3. **姉妹関係からくる気持ち**: 姉妹だからこその感情（妥協したい、でも言いたい、応援したい、心配、など）
4. **発言すべきか**: 今発言すべきか、それとも黙って譲るべきか
5. **終了タイミング**: この討論をいつ終わらせるべきか（まだ早い/そろそろ/もういい）

【発言を生成してください】
内部感情を踏まえて、{sister}らしく自然に発言してください。
性格と口調を反映させてください。

【重要】
- {phase}の段階にふさわしい発言をしてください
- 前回の発言から議論を「進展」させてください
- 同じことを繰り返さないでください

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
    }},
    "phase_awareness": "{phase}の段階であることを認識している"
}}"""

        response = await self.call_ollama(prompt)

        if not response:
            return None

        try:
            # Extract JSON
            start = response.find('{')
            end = response.rfind('}') + 1

            if start == -1 or end == 0:
                print(f"[ERROR] No JSON found in response")
                return None

            json_str = response[start:end]
            data = json.loads(json_str)
            return data

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parse error: {e}")
            return None

    def calculate_speak_probability(
        self,
        sister: str,
        state: DiscussionState,
        emotion: EmotionalState
    ) -> float:
        """Calculate speaking probability"""
        score = 0.0

        # Base tendency
        score += self.base_tendency[sister] * 0.3

        # Energy and confidence
        score += emotion.energy * 0.2
        score += emotion.confidence * 0.15

        # Want to speak
        score += emotion.still_have_to_say * 0.2

        # Consecutive speak penalty
        if state.last_speaker == sister:
            score -= 0.5

        # Haven't spoken yet bonus
        speakers_so_far = set([s.speaker for s in state.all_speeches])
        if sister not in speakers_so_far and len(state.all_speeches) > 0:
            score += 0.4

        return min(1.0, max(0.0, score))

    def select_next_speaker(self, state: DiscussionState) -> Optional[str]:
        """Select next speaker"""
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

    async def run_structured_discussion(
        self,
        proposal: dict,
        max_rounds: int = 100
    ) -> DiscussionState:
        """Run structured discussion with 起承転結"""

        print("\n" + "="*70)
        print("構造化討論システム - Phase 1.6 v3")
        print("起承転結による段階的討論")
        print("="*70)

        print(f"\n【議題】{proposal['title']}")
        print(f"\n【開始時刻】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        state = DiscussionState(proposal=proposal)

        while state.current_round < max_rounds:
            state.current_round += 1
            state.current_phase = self.get_current_phase(state.current_round)

            print(f"\n{'='*70}")
            print(f"Round {state.current_round} - 【{state.current_phase}】")
            print(f"{'='*70}\n")

            # Display emotions
            print("【感情状態】")
            for sister in ["牡丹", "Kasho", "ユリ"]:
                print(f"{sister}: {self.emotions[sister].to_display_string()}")
            print()

            # Select speaker
            speaker = self.select_next_speaker(state)

            if speaker is None:
                print("→ 全員沈黙\n")
                state.consecutive_silence_rounds += 1

                speakers_so_far = set([s.speaker for s in state.all_speeches])
                everyone_spoke = len(speakers_so_far) == 3

                if state.consecutive_silence_rounds >= 2 and everyone_spoke:
                    print("全員が納得したようです。討論を終了します。\n")
                    break

                await asyncio.sleep(1)
                continue

            # Generate response
            print(f"→ {speaker}が発言準備中...\n")

            response_data = await self.generate_phase_aware_response(speaker, state)

            if not response_data:
                print(f"[ERROR] {speaker}の応答生成失敗\n")
                continue

            # Create speech
            internal = InternalEmotion(**response_data['internal_emotion'])

            speech = Speech(
                timestamp=datetime.now(),
                speaker=speaker,
                round_number=state.current_round,
                phase=state.current_phase,
                internal_emotion=internal,
                content=response_data['speech'],
                emotion_changes=response_data.get('emotion_changes', {})
            )

            # Display internal emotion
            print(f"【{speaker}の内部感情】")
            print(f"- 反応: {internal.reaction}")
            print(f"- 立場: {internal.position}")
            print(f"- 姉妹として: {internal.sister_dynamics}")
            print(f"- 判断: {internal.speak_or_defer}")
            print(f"- 終了判断: {internal.end_timing}\n")

            # Display speech
            timestamp = speech.timestamp.strftime("%H:%M:%S")
            print(f"【{timestamp} {speaker}の発言】")
            print(f"{speech.content}\n")

            # Update emotion
            changes = speech.emotion_changes
            emotion = self.emotions[speaker]
            emotion.confidence = min(1.0, max(0.0, emotion.confidence + changes.get('confidence', 0)))
            emotion.agreement_level = min(1.0, max(0.0, emotion.agreement_level + changes.get('agreement_level', 0)))
            emotion.want_to_end = min(1.0, max(0.0, emotion.want_to_end + changes.get('want_to_end', 0)))
            emotion.satisfaction = min(1.0, max(0.0, emotion.satisfaction + changes.get('satisfaction', 0)))

            # Record speech
            state.all_speeches.append(speech)
            state.last_speaker = speaker
            state.consecutive_silence_rounds = 0

            await asyncio.sleep(0.5)

        return state

    def save_discussion_record(
        self,
        state: DiscussionState,
        output_dir: str = "/home/koshikawa/kirinuki/2025-10-22/決議記録"
    ):
        """Save discussion record to markdown"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"structured_discussion_v3_{timestamp}.md"
        filepath = f"{output_dir}/{filename}"

        # Build markdown
        md = f"""# 決議記録 - 構造化討論（Phase 1.6 v3）

**日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**討論モード**: 完全自律 + 起承転結
**決議種別**: Tier 2 - キャラクター設定

---

## 提案内容

**タイトル**: {state.proposal['title']}

**背景・理由**:
{state.proposal.get('description', '')}

---

## 討論記録

"""

        # Group by phase
        phases = ["起", "承", "転", "結"]
        for phase in phases:
            phase_speeches = [s for s in state.all_speeches if s.phase == phase]
            if not phase_speeches:
                continue

            md += f"### 【{phase}】段階\n\n"

            for speech in phase_speeches:
                timestamp = speech.timestamp.strftime("%H:%M:%S")
                md += f"**Round {speech.round_number} - {timestamp} {speech.speaker}の発言**\n\n"
                md += f"*[内部感情]*\n"
                md += f"- 反応: {speech.internal_emotion.reaction}\n"
                md += f"- 立場: {speech.internal_emotion.position}\n"
                md += f"- 姉妹として: {speech.internal_emotion.sister_dynamics}\n"
                md += f"- 判断: {speech.internal_emotion.speak_or_defer}\n"
                md += f"- 終了判断: {speech.internal_emotion.end_timing}\n\n"
                md += f"*[発言]*\n"
                md += f"{speech.content}\n\n"
                md += "---\n\n"

        md += f"""
## 討論統計

- 総ラウンド数: {state.current_round}
- 総発言数: {len(state.all_speeches)}
- 起: {len([s for s in state.all_speeches if s.phase == '起'])}回
- 承: {len([s for s in state.all_speeches if s.phase == '承'])}回
- 転: {len([s for s in state.all_speeches if s.phase == '転'])}回
- 結: {len([s for s in state.all_speeches if s.phase == '結'])}回

---

## 備考

この決議は構造化討論システム（Phase 1.6 v3）で実施されました。
起承転結の段階管理により、議論が段階的に深化しています。

---

**記録者**: Claude Code（設計部隊）
**保存先**: {filepath}
"""

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)

        print(f"\n討論記録を保存しました: {filepath}")


async def main():
    """Main function"""

    # Proposal
    proposal = {
        "title": "PON×確信度統合システムの実装",
        "description": """昨日、Phase 1の牡丹でホロライブの知識を試したところ、LLMがハルシネーションを起こして、
DBに正しい情報があるのに間違った回答をしてしまいました。

この問題を解決するために、「DB合致度による自信表現システム」と「PON機能」を統合した
新しいシステムを設計しました。

PONとは「ぽんこつ」の略で、VTuber文化における「愛されるやらかし」のことです。
間違ってるのに自信満々で答える、または正しいのに自信なさげに答えるという、
確信度と正確性の逆転現象を意図的に起こします。

実装内容:
1. DB合致度計算: LLMの回答とDBを照合して、正確性を数値化（0-100%）
2. PON発動判定: 合致度に応じて確率的にPONを発動
3. プロンプト調整: PON発動時は確信度を逆転させて自然な演出に

期待される効果:
1. ハルシネーションを「制御されたPON」に転換（問題→価値）
2. 視聴者とのインタラクション向上（訂正する楽しみ）
3. 牡丹らしいキャラクター性の強化（完璧じゃない愛されるドジっ子）
4. 不完全性戦略の具現化（欠陥を個性に）
5. エンゲージメント向上（配信が盛り上がる）"""
    }

    system = StructuredDiscussionSystem()
    state = await system.run_structured_discussion(proposal)
    system.save_discussion_record(state)

    print("\n構造化討論システムのテストが完了しました。")


if __name__ == "__main__":
    asyncio.run(main())
