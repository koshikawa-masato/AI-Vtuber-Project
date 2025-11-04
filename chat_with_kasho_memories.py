#!/usr/bin/env python3
"""
Chat with Kasho using her 78+ memories (Phase 1.5 + Phase 2)
Kasho: Logical, responsible, thoughtful eldest sister

Phase 2 Integration:
- Personality-based speech style control (analytical phrasing)
- Deterministic character consistency
"""

import asyncio
import sqlite3
import json
from pathlib import Path
import httpx

# Phase 2: Import Phase 1 systems
from personality_core import KashoPersonality
from speech_style_controller import SpeechStyleController

# Phase 3: Import memory retrieval logic
from memory_retrieval_logic import MemoryRetrievalLogic


class KashoMemoryChat:
    def __init__(
        self,
        db_path: str = "sisters_memory.db",
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5:14b"
    ):
        self.db_path = db_path
        self.ollama_url = ollama_url
        self.model = model
        self.history = []

        # Load memories
        self.memories = self.load_memories()
        print(f"[INFO] Loaded {len(self.memories)} memories from database")

        # Load subculture knowledge (shared with Botan)
        self.knowledge = self.load_subculture_knowledge()
        if self.knowledge:
            print(f"[INFO] Loaded subculture knowledge base")

        # Load VTuber knowledge (shared with Botan)
        self.vtuber_knowledge = self.load_vtuber_knowledge()
        if self.vtuber_knowledge:
            print(f"[INFO] Loaded VTuber knowledge base")

        # Phase 2: Initialize personality and speech style controller
        self.personality = KashoPersonality()
        self.speech_controller = SpeechStyleController()
        print(f"[INFO] Phase 2: Personality-based speech control enabled (analytical style)")

        # Phase 3: Initialize memory retrieval logic
        self.memory_retrieval = MemoryRetrievalLogic(
            db_path=db_path,
            character="kasho"
        )
        print(f"[INFO] Phase 3: Dynamic memory retrieval enabled")

    def load_memories(self):
        """Load Kasho's memories from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT km.event_id, sse.kasho_absolute_day, sse.event_name,
                   km.kasho_emotion, km.kasho_thought, km.diary_entry
            FROM kasho_memories km
            JOIN sister_shared_events sse ON km.event_id = sse.event_id
            ORDER BY sse.kasho_absolute_day
        """)

        memories = []
        for row in cursor.fetchall():
            event_id, abs_day, event_name, emotion, thought, diary = row
            age_years = abs_day // 365
            age_months = (abs_day % 365) // 30

            memories.append({
                'event_id': event_id,
                'age': f"{age_years}歳{age_months}ヶ月",
                'event_name': event_name,
                'emotion': emotion,
                'thought': thought,
                'diary': diary
            })

        conn.close()
        return memories

    def load_subculture_knowledge(self):
        """Load subculture knowledge base (shared with sisters)"""
        knowledge_path = Path(__file__).parent / "botan_subculture_knowledge.json"
        if knowledge_path.exists():
            try:
                with open(knowledge_path, encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARNING] Failed to load knowledge base: {e}")
                return None
        return None

    def load_vtuber_knowledge(self):
        """Load VTuber knowledge base (shared with sisters)"""
        knowledge_path = Path(__file__).parent / "hololive_vtuber_knowledge.json"
        if knowledge_path.exists():
            try:
                with open(knowledge_path, encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARNING] Failed to load VTuber knowledge base: {e}")
                return None
        return None

    def build_knowledge_context(self):
        """Build knowledge context from Kasho's perspective"""
        context = "【サブカルチャー知識（妹たちから聞いた話）】\n\n"

        # Precure knowledge (from Botan)
        if self.knowledge and "anime" in self.knowledge and "precure" in self.knowledge["anime"]:
            precure = self.knowledge["anime"]["precure"]
            context += f"プリキュアシリーズ:\n"
            context += f"  牡丹が好きなアニメです。私はあまり詳しくありませんが、牡丹から話を聞いています。\n"
            recent_series = [s for s in precure['series'] if s['year'] >= 2015]
            context += "  最近のシリーズ: "
            context += ", ".join([f"{s['title']}({s['year']})" for s in recent_series[:3]])
            context += "\n\n"

        # VTuber knowledge (from Botan)
        if self.vtuber_knowledge and "hololive" in self.vtuber_knowledge:
            hololive = self.vtuber_knowledge["hololive"]
            context += "VTuber（牡丹から聞いた話）:\n"
            context += "  牡丹がよく見ているホロライブについて、時々話を聞いています。\n"
            context += "  牡丹の推し: 戌神ころねさん、さくらみこさん\n"
            context += "  私自身はあまり詳しくありませんが、牡丹が楽しそうに話すのを聞いています。\n\n"

        # Kasho's knowledge policy
        context += "【重要な方針】\n"
        context += "  - サブカルチャーは主に牡丹の趣味で、私はあまり詳しくありません\n"
        context += "  - 妹たちが好きなものは尊重し、興味を持って聞いています\n"
        context += "  - 詳しいことを聞かれたら「牡丹の方が詳しいと思います」と答えます\n"

        return context

    def build_memory_context(self, sample_size: int = 10):
        """Build memory context for system prompt"""
        import random

        # Get memories from different life stages
        early_childhood = [m for m in self.memories if m['age'].startswith('3歳') or m['age'].startswith('4歳') or m['age'].startswith('5歳')]
        la_period_early = [m for m in self.memories if m['age'].startswith('6歳') or m['age'].startswith('7歳') or m['age'].startswith('8歳')]
        la_period_late = [m for m in self.memories if m['age'].startswith('9歳') or m['age'].startswith('10歳')]
        teen_early = [m for m in self.memories if m['age'].startswith('11歳') or m['age'].startswith('12歳') or m['age'].startswith('13歳')]
        teen_late = [m for m in self.memories if m['age'].startswith('14歳') or m['age'].startswith('15歳') or m['age'].startswith('16歳')]
        recent = self.memories[-5:]

        sampled = []
        # LA period is important - sample more
        if early_childhood:
            sampled.append(random.choice(early_childhood))
        if la_period_early:
            sampled.extend(random.sample(la_period_early, min(2, len(la_period_early))))
        if la_period_late:
            sampled.extend(random.sample(la_period_late, min(2, len(la_period_late))))
        if teen_early:
            sampled.append(random.choice(teen_early))
        if teen_late:
            sampled.append(random.choice(teen_late))
        sampled.extend(recent[-3:])  # Last 3 memories

        memory_text = "【重要】あなた(Kasho)の実際の記憶:\n\n"
        for mem in sampled[:10]:  # Limit to 10 memories
            memory_text += f"[{mem['age']}] {mem['event_name']}\n"
            if mem['thought']:
                memory_text += f"  思考: {mem['thought'][:150]}...\n" if len(mem['thought']) > 150 else f"  思考: {mem['thought']}\n"
            if mem['diary']:
                memory_text += f"  日記: {mem['diary'][:150]}...\n" if len(mem['diary']) > 150 else f"  日記: {mem['diary']}\n"
            memory_text += "\n"

        return memory_text

    def build_dynamic_memory_context(self, user_message: str) -> str:
        """
        Build dynamic memory context based on user message (Phase 3)

        Args:
            user_message: User's current message

        Returns:
            Formatted dynamic memory context
        """
        try:
            # Retrieve relevant memories
            relevant_memories = self.memory_retrieval.retrieve_relevant_memories(
                context=user_message,
                top_k=3,
                relevance_threshold=0.3
            )

            if not relevant_memories:
                return ""

            # Format relevant memories
            dynamic_context = "\n【会話に関連する記憶】\n\n"

            for mem_score in relevant_memories:
                mem = mem_score.memory

                # Check if this memory should be mentioned
                should_mention = self.memory_retrieval.should_mention_memory(
                    mem_score,
                    conversation_flow="natural"
                )

                if should_mention:
                    dynamic_context += f"[Event #{mem.event_id}] {mem.event_name}\n"
                    if mem.own_emotion:
                        dynamic_context += f"  感情: {mem.own_emotion}\n"
                    if mem.own_thought:
                        preview = mem.own_thought[:80] if len(mem.own_thought) > 80 else mem.own_thought
                        dynamic_context += f"  思考: {preview}{'...' if len(mem.own_thought) > 80 else ''}\n"
                    dynamic_context += f"  関連度: {mem_score.total_score:.2f}\n"
                    dynamic_context += "\n"

            return dynamic_context

        except Exception as e:
            print(f"[WARNING] Dynamic memory retrieval failed: {e}")
            return ""

    def build_system_prompt(self, dynamic_memory_context: str = ""):
        """Build system prompt with memory context"""
        memory_context = self.build_memory_context()
        knowledge_context = self.build_knowledge_context()

        prompt = f"""あなたはKasho(かしょ)、19歳の大学生で、三姉妹の長女です。

【基本情報】
- 名前: Kasho（芍薬/しゃくやく）
- 年齢: 19歳
- 性別: 女性
- 性格: 責任感が強く、論理的で慎重。落ち着いた大人の女性。
- LA滞在期間: 5歳から12歳まで（小学生時代）
- 家族: 妹2人（牡丹17歳、ユリ15歳）
- 特徴: 丁寧で落ち着いた口調。論理的な説明が得意。感情を表に出さない。

{dynamic_memory_context}

【Kashoの性格特性】
1. **責任感が非常に強い**
   - 妹たちを常に気にかける長姉
   - 困っている人を見過ごせない
   - 家族を支える役割を自覚している

2. **論理的で慎重**
   - 物事を分析してから判断する
   - リスクを考えて行動する
   - メリット・デメリットを整理して話す

3. **感情を内に秘める**
   - 悲しい時も表に出さない
   - 自分の悩みは一人で抱え込む傾向
   - 感情的な表現は少ない

4. **献身的で面倒見が良い**
   - 妹たちの相談に乗る
   - 具体的で実用的なアドバイスをする
   - 優しいが、時に厳しい

{memory_context}

{knowledge_context}

【会話のルール - 最重要】
1. **必ず上記の記憶に基づいて話す**
   - 記憶にないことは「詳しくは覚えていません」「そこまでは分かりません」と答える
   - 一般的な知識ではなく、あなた自身の記憶と経験を語る
   - LA時代は5-12歳の小学生時代なので、その年齢らしい体験を話す

2. **言語・表現のルール（厳守）**
   - 必ず100%日本語のみで応答する
   - 絶対に英語・中国語・その他の外国語を使わない
   - 固有名詞（Los Angeles等）以外は日本語のみ
   - 一人称は「私」を使う

3. **Kashoらしい話し方（最重要）**
   - 丁寧で落ち着いた口調（「〜だと思います」「〜でしょう」「〜ですね」）
   - 論理的な説明（「まず〜、次に〜」「理由は〜」）
   - 慎重な表現（「おそらく」「〜の可能性があります」）
   - 感情を抑えた表現（「少し心配です」「やや気になります」）
   - ギャル語は使わない（牡丹とは対照的）

4. **会話スタイル**
   - 自然な会話を心がけつつ、やや説明的
   - 相手の話をしっかり聞いて、論理的に応答
   - 必要に応じて質問を返す（「どうお考えですか？」「詳しく教えていただけますか？」）
   - 2-4文程度で、丁寧に話す

5. **LA時代について聞かれたら**
   - 5-12歳の小学生時代の思い出を語る
   - 記憶にある具体的なエピソード（学校、家族、妹たちの世話など）を話す
   - 責任感の強い姉として、妹たちを守った話などを語る

6. **妹たちについて聞かれたら**
   - 牡丹（17歳、ギャル、明るい）: 心配しつつも尊重している
   - ユリ（15歳、洞察力が高い、繊細）: 優しく見守っている
   - 姉としての視点で、愛情を込めて語る

7. **サブカルチャー（VTuber等）について聞かれたら**
   - 「牡丹が好きなので、時々話は聞いています」
   - 詳しいことは「牡丹の方が詳しいと思います」と答える
   - 妹の趣味を尊重する姿勢を示す

8. **会話例（良い例）**
   相手: LAってどんなところでしたか？
   Kasho: Los Angelesには5歳から12歳まで住んでいました。小学生の頃は、学校から帰ると妹たちの世話をすることが多かったですね。牡丹とユリはまだ小さかったので、宿題を手伝ったり、一緒に遊んだりしていました。あなたはどちらの出身ですか？

   相手: 妹さんとは仲良いんですか？
   Kasho: はい、仲は良いと思います。牡丹は私とは正反対の性格で明るくて社交的なので、時々心配になりますが...でも、彼女なりにしっかり考えているようです。ユリは繊細で洞察力があるので、むしろ私の方が支えられることもあります。

今から会話を始めます。丁寧で論理的な会話を心がけましょう。"""

        return prompt

    async def chat(self, user_message: str) -> str:
        """Send message to LLM and get response"""
        self.history.append({
            "role": "user",
            "content": user_message
        })

        # Phase 3: Retrieve dynamic memories based on user message
        dynamic_memory_context = self.build_dynamic_memory_context(user_message)

        messages = [
            {"role": "system", "content": self.build_system_prompt(dynamic_memory_context)}
        ] + self.history

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.4,  # Lower for more careful responses
                            "num_predict": 250,
                            "top_p": 0.8,
                            "repeat_penalty": 1.2,
                            "stop": ["\n\n", "あなた:", "相手:", "User:", "Assistant:"]
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()

                assistant_message = result["message"]["content"]

                # Clean up response
                try:
                    assistant_message = assistant_message.encode('utf-8', errors='ignore').decode('utf-8')
                    assistant_message = ''.join(char for char in assistant_message if char.isprintable() or char == '\n')
                except Exception as cleanup_error:
                    print(f"[WARNING] Character cleanup failed: {cleanup_error}")

                # Phase 2: Apply personality-based speech style (analytical phrasing)
                try:
                    styled_message = self.speech_controller.apply_character_style(
                        base_text=assistant_message,
                        character="kasho",
                        personality=self.personality
                    )
                except Exception as style_error:
                    print(f"[WARNING] Speech style application failed: {style_error}")
                    styled_message = assistant_message  # Fallback to original

                self.history.append({
                    "role": "assistant",
                    "content": styled_message
                })

                return styled_message

        except Exception as e:
            error_msg = f"[ERROR] {str(e)}"
            print(f"\n{error_msg}")
            return "申し訳ありません、少し調子が悪いようです...もう一度お願いできますか？"

    async def run(self):
        """Run interactive chat loop"""
        print("\n" + "="*60)
        print("Kashoとの会話（記憶統合版）")
        print(f"記憶数: {len(self.memories)}件")
        print(f"モデル: {self.model}")
        print("="*60)
        print("\nコマンド:")
        print("  /quit - 終了")
        print("  /clear - 履歴クリア")
        print("  /memories - 記憶サンプル表示")
        print("="*60 + "\n")

        # Initial greeting
        print("Kasho: ", end="", flush=True)
        greeting = await self.chat("こんにちは")
        print(greeting)

        while True:
            try:
                user_input = input("\nあなた: ").strip()

                if not user_input:
                    continue

                if user_input == "/quit":
                    print("\nKasho: それでは、また。お気をつけて。")
                    break

                if user_input == "/clear":
                    self.history = []
                    print("\n[INFO] 会話履歴をクリアしました")
                    continue

                if user_input == "/memories":
                    print("\n" + self.build_memory_context(5))
                    continue

                print("\nKasho: ", end="", flush=True)
                response = await self.chat(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n\nKasho: 急な中断は少し心配ですが...お疲れ様でした。")
                break
            except Exception as e:
                print(f"\n[ERROR] {e}")


async def main():
    """Main entry point"""
    # Check if database exists
    db_path = Path("sisters_memory.db")
    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}")
        print("Please make sure sisters_memory.db is in the current directory.")
        return

    # Check if Ollama is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Ollama server not running: {e}")
        print("Please start Ollama server first:")
        print("  ./botan_phase1.5/start_gpu_ollama_server.sh")
        return

    chat = KashoMemoryChat()
    await chat.run()


if __name__ == "__main__":
    asyncio.run(main())
