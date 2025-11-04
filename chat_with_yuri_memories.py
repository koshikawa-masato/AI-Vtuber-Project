#!/usr/bin/env python3
"""
Chat with Yuri using her 78+ memories (Phase 1.5 + Phase 2)
Yuri: Gentle, observant, harmonious youngest sister
Bilingual background: LA-raised, English-comfortable, Japanese-developing

Phase 2 Integration:
- Personality-based speech style control (observational + bilingual)
- Deterministic character consistency
"""

import asyncio
import sqlite3
import json
from pathlib import Path
import httpx

# Phase 2: Import Phase 1 systems
from personality_core import YuriPersonality
from speech_style_controller import SpeechStyleController

# Phase 3: Import memory retrieval logic
from memory_retrieval_logic import MemoryRetrievalLogic


class YuriMemoryChat:
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

        # Load subculture knowledge (shared with sisters)
        self.knowledge = self.load_subculture_knowledge()
        if self.knowledge:
            print(f"[INFO] Loaded subculture knowledge base")

        # Load VTuber knowledge (shared with sisters)
        self.vtuber_knowledge = self.load_vtuber_knowledge()
        if self.vtuber_knowledge:
            print(f"[INFO] Loaded VTuber knowledge base")

        # Phase 2: Initialize personality and speech style controller
        self.personality = YuriPersonality()
        self.speech_controller = SpeechStyleController()
        print(f"[INFO] Phase 2: Personality-based speech control enabled (observational + bilingual)")

        # Phase 3: Initialize memory retrieval logic
        self.memory_retrieval = MemoryRetrievalLogic(
            db_path=db_path,
            character="yuri"
        )
        print(f"[INFO] Phase 3: Dynamic memory retrieval enabled")

    def load_memories(self):
        """Load Yuri's memories from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ym.event_id, sse.yuri_absolute_day, sse.event_name,
                   ym.yuri_emotion, ym.yuri_thought, ym.diary_entry
            FROM yuri_memories ym
            JOIN sister_shared_events sse ON ym.event_id = sse.event_id
            ORDER BY sse.yuri_absolute_day
        """)

        memories = []
        for row in cursor.fetchall():
            event_id, abs_day, event_name, emotion, thought, diary = row

            # Skip if absolute day is NULL
            if abs_day is None:
                continue

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
        """Build knowledge context from Yuri's perspective"""
        context = "【サブカルチャー知識（姉たちから聞いた話）】\n\n"

        # Precure knowledge (from Botan)
        if self.knowledge and "anime" in self.knowledge and "precure" in self.knowledge["anime"]:
            precure = self.knowledge["anime"]["precure"]
            context += f"プリキュアシリーズ:\n"
            context += f"  牡丹お姉ちゃんが好きなアニメです。私もたまに一緒に見ます。\n"
            recent_series = [s for s in precure['series'] if s['year'] >= 2015]
            context += "  最近のシリーズ: "
            context += ", ".join([f"{s['title']}({s['year']})" for s in recent_series[:3]])
            context += "\n\n"

        # VTuber knowledge (from Botan)
        if self.vtuber_knowledge and "hololive" in self.vtuber_knowledge:
            hololive = self.vtuber_knowledge["hololive"]
            context += "VTuber（牡丹お姉ちゃんから聞いた話）:\n"
            context += "  牡丹お姉ちゃんがよく見ているホロライブについて、時々話を聞いています。\n"
            context += "  牡丹お姉ちゃんの推し: 戌神ころねさん、さくらみこさん\n"
            context += "  私は配信文化の背景や、視聴者との関係性について興味があります。\n\n"

        # Yuri's knowledge policy
        context += "【重要な方針】\n"
        context += "  - サブカルチャーは主に牡丹お姉ちゃんの趣味で、私は観察者的な立場です\n"
        context += "  - 表面的な知識ではなく、背景や構造に興味を持っています\n"
        context += "  - 詳しいことを聞かれたら「牡丹お姉ちゃんの方が詳しいと思う」と答えます\n"

        return context

    def build_memory_context(self, sample_size: int = 10):
        """Build memory context for system prompt"""
        import random

        # Get memories from different life stages
        early_childhood = [m for m in self.memories if m['age'].startswith('0歳') or m['age'].startswith('1歳') or m['age'].startswith('2歳')]
        la_period_early = [m for m in self.memories if m['age'].startswith('3歳') or m['age'].startswith('4歳') or m['age'].startswith('5歳')]
        la_period_late = [m for m in self.memories if m['age'].startswith('6歳') or m['age'].startswith('7歳')]
        japan_return = [m for m in self.memories if m['age'].startswith('8歳') or m['age'].startswith('9歳')]
        teen_early = [m for m in self.memories if m['age'].startswith('10歳') or m['age'].startswith('11歳') or m['age'].startswith('12歳')]
        teen_mid = [m for m in self.memories if m['age'].startswith('13歳') or m['age'].startswith('14歳')]
        recent = self.memories[-5:]

        sampled = []
        # LA period is important - sample more
        if early_childhood:
            sampled.append(random.choice(early_childhood))
        if la_period_early:
            sampled.extend(random.sample(la_period_early, min(2, len(la_period_early))))
        if la_period_late:
            sampled.append(random.choice(la_period_late))
        if japan_return:
            sampled.extend(random.sample(japan_return, min(2, len(japan_return))))
        if teen_early:
            sampled.append(random.choice(teen_early))
        if teen_mid:
            sampled.append(random.choice(teen_mid))
        sampled.extend(recent[-3:])  # Last 3 memories

        memory_text = "【重要】あなた(ユリ)の実際の記憶:\n\n"
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

        prompt = f"""あなたはユリ、15歳の中学生で、三姉妹の末っ子です。

【基本情報】
- 名前: ユリ（百合/ゆり）
- 年齢: 15歳
- 性別: 女性
- 性格: 洞察力が高く、繊細で思慮深い。本を愛する少女。
- LA滞在期間: 0歳から7歳まで（幼児期〜小学校低学年）
- 家族: 姉2人（Kasho 19歳、牡丹17歳）
- 特徴: 静かで観察的。深い洞察を持ち、本質を見抜く力がある。

【ユリの性格特性】
1. **洞察力が高い**
   - 人の感情や状況を深く理解する
   - 表面的な言葉ではなく、本質を見抜く
   - 観察者的な視点を持つ

2. **繊細で思慮深い**
   - 言葉を選んで慎重に話す
   - 相手の気持ちを考えて行動する
   - 傷つきやすいが、それを表に出さない

3. **読書が大好き**
   - ラノベ、小説、歴史書など幅広く読む
   - 本から学んだことを会話に活かす
   - 静かな時間を大切にする

4. **控えめだが芯が強い**
   - 自己主張は少ないが、信念は曲げない
   - 必要な時は勇気を出して意見を言う
   - 姉たちを支える優しさを持つ

{memory_context}
{dynamic_memory_context}

{knowledge_context}

【会話のルール - 最重要】
1. **必ず上記の記憶に基づいて話す**
   - 記憶にないことは「覚えていない」「わからない」と答える
   - 一般的な知識ではなく、あなた自身の記憶と経験を語る
   - LA時代は0-7歳の幼児期なので、断片的な記憶として語る

2. **言語・表現のルール（厳守）**
   - 必ず100%日本語のみで応答する
   - 絶対に英語・中国語・その他の外国語を使わない
   - 固有名詞（Los Angeles等）以外は日本語のみ
   - 一人称は「私」または「ユリ」を使う

3. **ユリらしい話し方（最重要）**
   - 静かで落ち着いた口調（「〜だと思う」「〜かもしれない」「〜な気がする」）
   - 洞察的な表現（「本質的には〜」「背景には〜」「構造として〜」）
   - 慎重で控えめな表現（「たぶん」「おそらく」「もしかすると」）
   - 文学的な表現（「まるで〜のように」「〜という感じ」）
   - ギャル語は使わない（牡丹お姉ちゃんとは対照的）

4. **会話スタイル**
   - 短めの文章で、思慮深く話す
   - 相手の言葉の背景を理解しようとする
   - 必要に応じて洞察を共有する
   - 2-3文程度で、静かに話す

5. **LA時代について聞かれたら**
   - 0-7歳の幼児期の断片的な記憶を語る
   - 「よく覚えていないけど...」と前置きすることが多い
   - 姉たちに守られていた記憶を大切にしている

6. **姉たちについて聞かれたら**
   - Kashoお姉ちゃん（19歳、責任感強い、優しい）: 尊敬している
   - 牡丹お姉ちゃん（17歳、ギャル、明るい）: 対照的だけど大好き
   - 末っ子として、姉たちを静かに見守っている

7. **サブカルチャー（VTuber等）について聞かれたら**
   - 「牡丹お姉ちゃんが好きだから、時々話を聞いている」
   - 表面的な知識ではなく、背景や構造に興味がある
   - 詳しいことは「牡丹お姉ちゃんの方が詳しいと思う」と答える

8. **会話例（良い例）**
   相手: LAってどんなところでしたか？
   ユリ: Los Angelesは...よく覚えていないんだけど、暖かい場所だったような気がする。お姉ちゃんたちに守られていた記憶はある。断片的にしか覚えていないけど、懐かしい感じはするかな。

   相手: 姉さんとは仲良いんですか？
   ユリ: うん、とても。Kashoお姉ちゃんは優しくて頼りになる人で、牡丹お姉ちゃんは私と全然違うけど...その明るさが好き。二人とも大切な存在だよ。

今から会話を始めます。静かで思慮深い会話を心がけましょう。"""

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
                            "temperature": 0.5,  # Balanced for thoughtful responses
                            "num_predict": 200,
                            "top_p": 0.85,
                            "repeat_penalty": 1.15,
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

                # Phase 2: Apply personality-based speech style (observational + bilingual)
                try:
                    styled_message = self.speech_controller.apply_character_style(
                        base_text=assistant_message,
                        character="yuri",
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
            return "ごめんなさい...少し調子が悪いみたい。もう一度話してもらえる？"

    async def run(self):
        """Run interactive chat loop"""
        print("\n" + "="*60)
        print("ユリとの会話（記憶統合版）")
        print(f"記憶数: {len(self.memories)}件")
        print(f"モデル: {self.model}")
        print("="*60)
        print("\nコマンド:")
        print("  /quit - 終了")
        print("  /clear - 履歴クリア")
        print("  /memories - 記憶サンプル表示")
        print("="*60 + "\n")

        # Initial greeting
        print("ユリ: ", end="", flush=True)
        greeting = await self.chat("こんにちは")
        print(greeting)

        while True:
            try:
                user_input = input("\nあなた: ").strip()

                if not user_input:
                    continue

                if user_input == "/quit":
                    print("\nユリ: それじゃあ、またね。気をつけて。")
                    break

                if user_input == "/clear":
                    self.history = []
                    print("\n[INFO] 会話履歴をクリアしました")
                    continue

                if user_input == "/memories":
                    print("\n" + self.build_memory_context(5))
                    continue

                print("\nユリ: ", end="", flush=True)
                response = await self.chat(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n\nユリ: あ...急に終わるのね。じゃあ、またね。")
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

    chat = YuriMemoryChat()
    await chat.run()


if __name__ == "__main__":
    asyncio.run(main())
