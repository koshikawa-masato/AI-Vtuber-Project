#!/usr/bin/env python3
"""
Phase 1.6 v4: Improved Structured Discussion System
Complete autonomous discussion with enhanced phase management

Key improvements from v3:
1. Phase-based round limits (no timeout, controlled by rounds)
2. Three-sisters consensus-based termination
3. Automatic technical log generation
4. Enhanced end-of-discussion detection

Phase limits:
- 起 (Introduction): max 10 rounds
- 承 (Development): max 15 rounds
- 転 (Turn/Debate): max 15 rounds
- 結 (Conclusion): max 20 rounds
- Total: max 50 rounds (safety limit)
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
    """Internal emotional response (Fix 3: Simplified to 2 fields)"""
    reaction: str  # 反応: これまでの討論を聞いてどう感じたか
    position: str  # 立場: 賛成か反対か、なぜそう思うのか

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
    event_id: int = 0  # Event ID for linking Inspirations

    # Phase tracking (v4)
    phase_rounds: Dict[str, int] = field(default_factory=lambda: {"起": 0, "承": 0, "転": 0, "結": 0})
    phase_transition_history: List[tuple] = field(default_factory=list)  # (round, phase)

class DiscussionPhase:
    """Discussion phase constants with round limits"""
    INTRODUCTION = "起"  # Proposal phase
    DEVELOPMENT = "承"   # Questions phase
    TURN = "転"          # Debate phase
    CONCLUSION = "結"    # Agreement phase

    # Phase-based round limits
    # Fix 7: Reduced round limits for role-based natural conversation
    # User's example: 6 turns total (牡丹→Kasho→ユリ→Kasho→牡丹→ユリ)
    MAX_ROUNDS = {
        "起": 2,   # Introduction: 提案役が提案 → 評価役が応答
        "承": 3,   # Development: 調整役が参加 → 議論展開
        "転": 3,   # Turn: 対立点や別視点の提示
        "結": 4    # Conclusion: 合意形成
    }

    # Total safety limit (reduced from 50)
    TOTAL_MAX_ROUNDS = 12

class StructuredDiscussionSystem:
    """Phase 1.6 v4: Improved structured discussion with 起承転結"""

    def __init__(self, model: str = "qwen2.5:32b", hallucination_personalizer=None):
        self.model = model
        self.log_file = None  # Real-time log file
        self.hallucination_personalizer = hallucination_personalizer  # Phase D: Hallucination detection

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

        # Fix 7: Conversation roles extracted from memory DB
        # Based on analysis of 100+ memories for each sister
        self.conversation_roles = {
            "牡丹": {
                "role": "提案役",  # Proposer (13/103 memories)
                "description": "新しい提案や質問を出す。会話を始める役割。",
                "speech_style": "具体的な提案や質問を出す。「〜しよう」「〜はどう？」"
            },
            "Kasho": {
                "role": "評価役",  # Evaluator/Judge (32/104 memories)
                "description": "提案を分析し、判断を示す。責任ある評価をする役割。",
                "speech_style": "提案を評価し、判断を示す。「〜だと思う」「〜すべき」"
            },
            "ユリ": {
                "role": "調整役",  # Mediator (21+4/101 memories)
                "description": "異なる視点や対案を提示し、バランスを取る役割。",
                "speech_style": "対案や別の視点を提示する。「逆に〜は？」「だけど〜も」"
            }
        }

    def log(self, message: str = ""):
        """Print and write to log file"""
        print(message)
        if self.log_file:
            self.log_file.write(message + "\n")
            self.log_file.flush()  # Immediate flush for tail -f

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

    def get_current_phase(self, state: DiscussionState) -> str:
        """Determine current discussion phase based on phase rounds (v4)

        Phases automatically progress when round limit is reached:
        - 起 (max 10 rounds) → 承
        - 承 (max 15 rounds) → 転
        - 転 (max 15 rounds) → 結
        - 結 (max 20 rounds) → stay in 結
        """
        current_phase = state.current_phase
        phase_round = state.phase_rounds[current_phase]

        # Check if current phase has reached its limit
        if phase_round >= DiscussionPhase.MAX_ROUNDS.get(current_phase, 999):
            # Transition to next phase
            phase_order = ["起", "承", "転", "結"]
            current_index = phase_order.index(current_phase)

            if current_index < len(phase_order) - 1:
                # Move to next phase
                new_phase = phase_order[current_index + 1]
                state.phase_transition_history.append((state.current_round, new_phase))
                return new_phase
            else:
                # Already in final phase (結), stay there
                return current_phase

        # Continue in current phase
        return current_phase

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
        """Build full discussion context WITH PROPOSAL (Fix 1)"""

        # Fix 1: Include proposal at the beginning
        proposal_text = f"""【議題（必ず答えるべき内容）】
タイトル: {state.proposal['title']}
詳細: {state.proposal.get('description', '')}

この議題について具体的に討論してください。議題から逸脱しないでください。
"""

        if not state.all_speeches:
            return proposal_text + "\n（まだ誰も発言していません）"

        context = [proposal_text, "\n【これまでの発言】"]
        for speech in state.all_speeches:
            context.append(
                f"Round {speech.round_number}({speech.phase}) {speech.speaker}: {speech.content}"
            )

        return "\n".join(context)

    def detect_repetition(self, state: DiscussionState, speaker: str) -> bool:
        """Detect if the same pattern is repeated (Fix 2)"""
        if len(state.all_speeches) < 3:
            return False

        # Get last 3 speeches from this speaker
        speaker_speeches = [s for s in state.all_speeches if s.speaker == speaker]
        if len(speaker_speeches) < 3:
            return False

        last_3 = speaker_speeches[-3:]

        # Simple similarity check: first 30 chars
        patterns = [s.content[:30] for s in last_3]

        # If all 3 start with similar pattern, it's repetition
        if len(set(patterns)) == 1:
            return True

        return False

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

【必須発言フォーマット】
あなたの発言は以下の形式で始めてください：
「この議題について、私は〇〇だと思う。なぜなら△△だから。」

例：
「Extraversion: 0.95という数値は、私らしいと思う。なぜなら、LAで友達を作るのが楽しかった記憶があるから。」

【避けるべきこと】
- まだ詳細な質問はしない（承でやる）
- まだ対立点を深掘りしない（転でやる）
- 抽象的な感想のみ（具体的な立場を明言すること）""",

            "承": f"""【討論段階】承 - 質問・懸念（Round {round_number}/3-5）

【あなたの役割】
- 不明点を質問する
- 懸念事項を表明する
- 詳細な説明を求める
- 前回の発言を深掘りする

【必須発言フォーマット】
あなたの発言は前の姉妹の意見を「受けて」始めてください：
「〇〇さんの△△という意見について、私は□□という点が気になる。具体的には...」

例：
「牡丹のExtraversion: 0.95について、確かに社交的だけど、0.95って本当に適切？具体的には、配信中に疲れることもあるはずだから、もう少し低くてもいいんじゃない？」

【重要】
- 必ず前の発言に言及すること
- 単なる感想ではなく、質問や懸念を含めること
- 議論を「深化」させること（同じ話の繰り返しは禁止）""",

            "転": f"""【討論段階】転 - 対立点・深い議論（Round {round_number}/6-8）

【あなたの役割】
- 意見の違いを明確にする
- 複数の選択肢を比較する
- リスクとベネフィットを議論する
- 対立点を深く掘り下げる

【必須発言フォーマット】
あなたの発言は「視点の転換」を含めてください。以下の転換語を使うこと：
「しかし」「でも」「一方で」「逆に考えると」「別の視点では」

例：
「しかし、Conscientiousness: 0.50という数値には疑問がある。確かに柔軟だけど、配信の準備は意外としっかりやってるはず。一方で、ノリ重視という面は確かにあるから、0.60くらいが適切かも。」

【重要】
- 必ず「でも」「しかし」などの転換語を使うこと
- 単なる賛成ではなく、対立点や別の視点を提示すること
- 複数の選択肢を比較すること（〇〇か、△△か）""",

            "結": f"""【討論段階】結 - 合意形成（Round {round_number}/9+）

【あなたの役割】
- 妥協点を模索する
- 合意できる部分を確認する
- 決定事項を整理する
- 次のステップを提案する

【必須発言フォーマット】
あなたの発言は「合意と調整」を含めてください：
「〇〇の部分は賛成。△△は調整して、最終的に□□にしよう。」

例：
「Extraversion: 0.95は賛成。でもConscientiousnessは0.50から0.60に上げよう。配信準備はしっかりやってるから。最終的には、この8軸をベースに記憶を生成していくことで合意したい。」

【重要】
- 必ず「〇〇は賛成」「△△は調整」の形式を使うこと
- 対立していた点に対する妥協案を提示すること
- 具体的な数値や方針を決定すること
- 「次のステップ」を明確にすること"""
        }
        return instructions.get(phase, "")

    async def generate_phase_aware_response(
        self,
        sister: str,
        state: DiscussionState
    ) -> Optional[dict]:
        """Generate phase-aware emotional response"""

        phase = self.get_current_phase(state)
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

        # Fix 2: Check for repetition
        is_repeating = self.detect_repetition(state, sister)
        repetition_warning = ""
        if is_repeating:
            repetition_warning = """
【⚠️ 警告 ⚠️】
あなたは同じパターンを繰り返しています。
議題に基づいた具体的な意見を述べてください。
抽象的な発言は禁止です。数値やデータに言及してください。
"""

        # Extract key points/conflicts if needed
        additional_context = ""
        if phase == "転":
            key_points = await self.extract_key_points(state)
            additional_context = f"\n【起・承で出た主要な論点】\n{key_points}\n"
        elif phase == "結":
            key_points = await self.extract_key_points(state)
            conflicts = await self.extract_conflicts(state)
            additional_context = f"\n【主要な論点】\n{key_points}\n\n【転で議論された対立点】\n{conflicts}\n"

        # Fix 7: Add role-based instruction
        role_info = self.conversation_roles[sister]
        role_instruction = f"""
【Fix 7: あなたの会話役割】
役割: {role_info['role']}
説明: {role_info['description']}
発言スタイル: {role_info['speech_style']}

この役割に基づいて発言してください。
"""

        prompt = f"""あなたは{sister}です。

【あなたの性格・特徴】
{profile}
{role_instruction}
{phase_instruction}
{repetition_warning}

【これまでの全発言】
{full_context}
{additional_context}

【内部感情を生成してください（Fix 3: 簡潔化）】
以下の2つの観点から、あなたの内心を述べてください：

1. **反応**: これまでの討論を聞いてどう感じたか
2. **立場**: 賛成か反対か、なぜそう思うのか

【発言を生成してください（Fix 4: 具体性の強制）】
内部感情を踏まえて、{sister}らしく自然に発言してください。

【具体性の要求（最重要）】
あなたの発言には以下を必ず含めてください：
- 議題に記載されている具体的な数値・データへの言及
- 「なぜ」「どのように」の説明
- 抽象的な発言（「アイデアを紹介する」「詳しく教えて」など）は禁止

【Fix 6: 記憶捏造の厳禁（超重要）】
- 存在しない過去の出来事を引用してはいけません
- 「〜したとき」「〜した記憶がある」などの架空の記憶は絶対に禁止
- 議題に書かれている情報のみを使って議論してください
- 仮定を述べる場合は「もし〜なら」という未来形のみ使用可能

例（良い発言）:
「牡丹のExtraversion: 0.95は確かに高い数値だと思う。もし配信で新しい企画をするなら、この社交性が活きるはず」

例（悪い発言 - 記憶捏造）:
「新しいゲームアプリの開発に挑戦したときユリはためらっていた」（存在しない記憶）

【重要】
- {phase}の段階にふさわしい発言をしてください
- 前回の発言から議論を「進展」させてください
- 同じことを繰り返さないでください

出力JSON:
{{
    "internal_emotion": {{
        "reaction": "討論への感情的反応",
        "position": "賛成/反対とその理由"
    }},
    "speech": "{sister}らしい具体的な発言（数値・データを含む）",
    "emotion_changes": {{
        "confidence": 0.0,
        "agreement_level": 0.0,
        "want_to_end": 0.0,
        "satisfaction": 0.0
    }}
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

            # Phase D: Hallucination detection and personality-based correction
            if self.hallucination_personalizer and 'speech' in data:
                character_map = {"牡丹": "botan", "Kasho": "kasho", "ユリ": "yuri"}
                char_key = character_map.get(sister, sister.lower())

                result = self.hallucination_personalizer.process_response(
                    character=char_key,
                    llm_response=data['speech'],
                    context={'phase': phase, 'round': state.current_round, 'event_id': state.event_id}
                )

                # If hallucination detected, append correction
                if result['is_hallucination'] and result['correction']:
                    data['speech'] = result['final_output']
                    print(f"[HALLUCINATION] {sister}: Detected and corrected ({result['processing_time_ms']:.2f}ms)")

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
        """
        Select next speaker based on conversational roles (Fix 7)

        Role-based flow:
        1. 提案役 (牡丹) starts or proposes new ideas
        2. 評価役 (Kasho) evaluates and judges
        3. 調整役 (ユリ) mediates or offers alternatives
        4. Back to 評価役 for decision

        This mimics natural conversation patterns found in 100+ memories.
        """

        # First speaker is always the Proposer
        if not state.all_speeches:
            return "牡丹"

        last_speaker = state.last_speaker

        # Role-based flow sequence
        # After Proposer → Evaluator responds
        # After Evaluator → Mediator provides alternative (or back to Proposer)
        # After Mediator → Evaluator makes decision

        role_flow = {
            "牡丹": "Kasho",   # Proposer → Evaluator
            "Kasho": "ユリ",    # Evaluator → Mediator
            "ユリ": "Kasho"     # Mediator → Evaluator (for decision)
        }

        # In 結 phase, prioritize decision-making
        if state.current_phase == "結":
            # If Kasho just spoke with high agreement, ユリ confirms
            if last_speaker == "Kasho" and self.emotions["Kasho"].agreement_level > 0.7:
                return "ユリ"
            # Otherwise follow normal flow
            return role_flow.get(last_speaker, "牡丹")

        return role_flow.get(last_speaker, "牡丹")

    async def run_structured_discussion(
        self,
        proposal: dict,
        max_rounds: int = None  # v4: default to TOTAL_MAX_ROUNDS
    ) -> DiscussionState:
        """Run structured discussion with 起承転結 (v4 improved)"""

        if max_rounds is None:
            max_rounds = DiscussionPhase.TOTAL_MAX_ROUNDS

        # Open real-time log file for tail -f monitoring
        proposal_id = proposal.get('id', 'unknown')
        log_filename = f"/tmp/discussion_{proposal_id}_live.log"
        self.log_file = open(log_filename, 'w', encoding='utf-8')
        self.log(f"Real-time log file created: {log_filename}")
        self.log(f"You can monitor with: tail -f {log_filename}\n")

        self.log("\n" + "="*70)
        self.log("構造化討論システム - Phase 1.6 v4 (改善版)")
        self.log("起承転結による段階的討論 + Phase別Round制限")
        self.log("="*70)

        self.log(f"\n【議題】{proposal['title']}")
        self.log(f"\n【Round制限】")
        self.log(f"  起: 最大{DiscussionPhase.MAX_ROUNDS['起']}ラウンド")
        self.log(f"  承: 最大{DiscussionPhase.MAX_ROUNDS['承']}ラウンド")
        self.log(f"  転: 最大{DiscussionPhase.MAX_ROUNDS['転']}ラウンド")
        self.log(f"  結: 最大{DiscussionPhase.MAX_ROUNDS['結']}ラウンド")
        self.log(f"  合計: 最大{max_rounds}ラウンド")
        self.log(f"\n【開始時刻】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Extract event_id from proposal for Inspiration linking
        event_id = proposal.get('event_id', 0)
        state = DiscussionState(proposal=proposal, event_id=event_id)

        while state.current_round < max_rounds:
            state.current_round += 1

            # Update phase (v4: based on phase rounds)
            previous_phase = state.current_phase
            state.current_phase = self.get_current_phase(state)

            # Phase transition notification
            if previous_phase != state.current_phase:
                self.log(f"\n🔄 Phase transition: {previous_phase} → {state.current_phase}\n")

            # Increment phase round counter (v4)
            state.phase_rounds[state.current_phase] += 1

            self.log(f"\n{'='*70}")
            self.log(f"Round {state.current_round} - 【{state.current_phase}】")
            self.log(f"{'='*70}\n")

            # Display emotions
            self.log("【感情状態】")
            for sister in ["牡丹", "Kasho", "ユリ"]:
                self.log(f"{sister}: {self.emotions[sister].to_display_string()}")
            self.log()

            # Check if all sisters want to end (v4)
            all_want_to_end = all(
                self.emotions[sister].want_to_end >= 0.8
                for sister in ["牡丹", "Kasho", "ユリ"]
            )

            if all_want_to_end and state.current_phase == "結":
                print("✅ 三姉妹全員が討論終了を希望しています。\n")
                print("討論を終了します。\n")
                break

            # Select speaker
            speaker = self.select_next_speaker(state)

            if speaker is None:
                self.log("→ 全員沈黙\n")
                state.consecutive_silence_rounds += 1

                speakers_so_far = set([s.speaker for s in state.all_speeches])
                everyone_spoke = len(speakers_so_far) == 3

                if state.consecutive_silence_rounds >= 2 and everyone_spoke:
                    self.log("全員が納得したようです。討論を終了します。\n")
                    break

                await asyncio.sleep(1)
                continue

            # Generate response
            self.log(f"→ {speaker}が発言準備中...\n")

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

            # Display internal emotion (Fix 3: Simplified display)
            self.log(f"【{speaker}の内部感情】")
            self.log(f"- 反応: {internal.reaction}")
            self.log(f"- 立場: {internal.position}\n")

            # Display speech
            timestamp = speech.timestamp.strftime("%H:%M:%S")
            self.log(f"【{timestamp} {speaker}の発言】")
            self.log(f"{speech.content}\n")

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

        # Close log file
        if self.log_file:
            self.log("\n討論終了。ログファイルを閉じます。")
            self.log_file.close()
            self.log_file = None

        return state

    def save_discussion_record(
        self,
        state: DiscussionState,
        output_dir: str = "/home/koshikawa/kirinuki/2025-10-22/決議記録"
    ):
        """Save discussion record to markdown (v4)"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"structured_discussion_v4_{timestamp}.md"
        filepath = f"{output_dir}/{filename}"

        # Build markdown
        md = f"""# 決議記録 - 構造化討論（Phase 1.6 v4）

**日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**討論モード**: 完全自律 + 起承転結 + Phase別Round制限
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
                md += f"- 立場: {speech.internal_emotion.position}\n\n"
                md += f"*[発言]*\n"
                md += f"{speech.content}\n\n"
                md += "---\n\n"

        md += f"""
## 討論統計

**総合**:
- 総ラウンド数: {state.current_round}
- 総発言数: {len(state.all_speeches)}

**Phase別Round数** (v4):
- 起: {state.phase_rounds['起']}ラウンド (最大{DiscussionPhase.MAX_ROUNDS['起']})
- 承: {state.phase_rounds['承']}ラウンド (最大{DiscussionPhase.MAX_ROUNDS['承']})
- 転: {state.phase_rounds['転']}ラウンド (最大{DiscussionPhase.MAX_ROUNDS['転']})
- 結: {state.phase_rounds['結']}ラウンド (最大{DiscussionPhase.MAX_ROUNDS['結']})

**Phase別発言数**:
- 起: {len([s for s in state.all_speeches if s.phase == '起'])}回
- 承: {len([s for s in state.all_speeches if s.phase == '承'])}回
- 転: {len([s for s in state.all_speeches if s.phase == '転'])}回
- 結: {len([s for s in state.all_speeches if s.phase == '結'])}回

---

## 備考

この決議は構造化討論システム（Phase 1.6 v4）で実施されました。
起承転結の段階管理に加え、Phase別Round制限により、タイムアウトなしで自律的に進行しました。

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
    import sys

    # Load proposal from proposals.json based on command line argument
    if len(sys.argv) < 2:
        print("Usage: python3 autonomous_discussion_v4_improved.py <proposal_id>")
        print("Example: python3 autonomous_discussion_v4_improved.py 109")
        sys.exit(1)

    try:
        proposal_id = int(sys.argv[1])
    except ValueError:
        print(f"Error: Proposal ID must be a number, got: {sys.argv[1]}")
        sys.exit(1)

    # Load proposals.json
    proposals_file = "/home/koshikawa/toExecUnit/proposals.json"
    try:
        with open(proposals_file, 'r', encoding='utf-8') as f:
            proposals_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: proposals.json not found at {proposals_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse proposals.json: {e}")
        sys.exit(1)

    # Find proposal by ID
    proposal = None
    for p in proposals_data.get('proposals', []):
        if p.get('id') == proposal_id:
            proposal = p
            break

    if not proposal:
        print(f"Error: Proposal #{proposal_id} not found in proposals.json")
        sys.exit(1)

    print(f"Loaded Proposal #{proposal_id}: {proposal.get('title', 'No title')}")

    # Update proposal status to processing
    proposal['status'] = 'processing'
    proposal['processing_started_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(proposals_file, 'w', encoding='utf-8') as f:
        json.dump(proposals_data, f, ensure_ascii=False, indent=2)

    # Run discussion
    system = StructuredDiscussionSystem()
    state = await system.run_structured_discussion(proposal)
    system.save_discussion_record(state)

    # Update proposal status to completed
    proposal['status'] = 'completed'
    proposal['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    proposal['result'] = {
        'event_id': proposal_id,
        'total_rounds': state.current_round,
        'total_speeches': len(state.all_speeches),
        'technical_log': f"/home/koshikawa/toExecUnit/discussion_technical_logs/discussion_{proposal_id}_technical.md"
    }
    with open(proposals_file, 'w', encoding='utf-8') as f:
        json.dump(proposals_data, f, ensure_ascii=False, indent=2)

    print("\n" + "="*70)
    print(f"構造化討論システム v4 - Proposal #{proposal_id} が完了しました。")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
