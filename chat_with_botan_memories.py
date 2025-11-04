#!/usr/bin/env python3
"""
Chat with Botan using her 98 memories (Phase 1.5 + Phase 2)

Phase 2 Integration:
- Personality-based speech style control
- Deterministic character consistency
"""

import asyncio
import sqlite3
import json
from pathlib import Path
import httpx

# Phase 2: Import Phase 1 systems
from personality_core import BotanPersonality
from speech_style_controller import SpeechStyleController

# Phase 3: Import memory retrieval logic
from memory_retrieval_logic import MemoryRetrievalLogic


class BotanMemoryChat:
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

        # Load subculture knowledge
        self.knowledge = self.load_subculture_knowledge()
        if self.knowledge:
            print(f"[INFO] Loaded subculture knowledge base")

        # Load VTuber knowledge
        self.vtuber_knowledge = self.load_vtuber_knowledge()
        if self.vtuber_knowledge:
            print(f"[INFO] Loaded VTuber knowledge base")

        # Phase 2: Initialize personality and speech style controller
        self.personality = BotanPersonality()
        self.speech_controller = SpeechStyleController()
        print(f"[INFO] Phase 2: Personality-based speech control enabled")

        # Phase 3: Initialize memory retrieval logic
        self.memory_retrieval = MemoryRetrievalLogic(
            db_path=db_path,
            character="botan"
        )
        print(f"[INFO] Phase 3: Dynamic memory retrieval enabled")
    
    def load_memories(self):
        """Load Botan's memories from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT bm.event_id, sse.botan_absolute_day, sse.event_name,
                   bm.botan_emotion, bm.botan_thought, bm.diary_entry
            FROM botan_memories bm
            JOIN sister_shared_events sse ON bm.event_id = sse.event_id
            ORDER BY sse.botan_absolute_day
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
        """Load subculture knowledge base"""
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
        """Load VTuber knowledge base"""
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
        """Build knowledge context for topics Botan knows about"""
        context = "【サブカルチャー知識】\n\n"

        # Precure knowledge
        if self.knowledge and "anime" in self.knowledge and "precure" in self.knowledge["anime"]:
            precure = self.knowledge["anime"]["precure"]
            context += f"プリキュアシリーズ:\n"
            context += f"  {precure['botan_context']}\n"
            # Show recent series (2015-2025)
            recent_series = [s for s in precure['series'] if s['year'] >= 2015]
            context += "  最近のシリーズ: "
            context += ", ".join([f"{s['title']}({s['year']})" for s in recent_series[:5]])
            context += "\n\n"

        # VTuber knowledge (basic)
        if self.knowledge and "vtuber" in self.knowledge:
            vtuber = self.knowledge["vtuber"]
            context += "VTuber:\n"
            if "botan_context" in vtuber:
                context += f"  {vtuber['botan_context']}\n"
            context += "  主要事務所: " + ", ".join([a['name'] for a in vtuber.get('major_agencies', [])])
            context += "\n\n"

        # Hololive VTuber knowledge (detailed)
        if self.vtuber_knowledge and "hololive" in self.vtuber_knowledge:
            hololive = self.vtuber_knowledge["hololive"]
            context += "ホロライブVTuber:\n"

            # Add basic member list with fan names (generation-based)
            if "generations" in hololive:
                context += "  【基本情報】全メンバー（自称・ファンネーム）:\n"
                gens = hololive["generations"]

                # Gen3 (important)
                if "gen3" in gens:
                    context += "    3期生: "
                    members = [f"{m['name']}（{m.get('self_title', '')}・{m.get('fan_name', '')}）" for m in gens["gen3"]]
                    context += "、".join(members[:4])  # Show first 4
                    context += "\n"

                # Gamers (important because of Korone)
                if "gamers" in gens:
                    context += "    ゲーマーズ: "
                    members = [f"{m['name']}（{m.get('fan_name', '')}）" for m in gens["gamers"]]
                    context += "、".join(members)
                    context += "\n"

                # Gen0 and others (compact)
                context += "    他の期生: 0期生（星詠み等）、1期生（すこん部等）、4期生、5期生、holoX、ReGLOSS、FLOW GLOW\n\n"

            if "botan_favorites" in hololive:
                context += "  大好きなVTuber:\n"
                for talent in hololive["botan_favorites"]:
                    context += f"    ・{talent['name']}（{talent.get('nickname', '')}）\n"
                    context += f"      {talent.get('description', '')}\n"

                    # Add self-title and fan name
                    if "self_title" in talent:
                        context += f"      自称: {talent['self_title']}\n"
                    if "fan_name" in talent:
                        context += f"      ファンネーム: {talent['fan_name']}\n"

                    # Add stream categories
                    if "stream_categories" in talent and len(talent['stream_categories']) > 0:
                        context += "      配信カテゴリ: "
                        context += "、".join(talent['stream_categories'][:3])
                        context += "\n"

                    # Add catchphrases
                    if "catchphrases" in talent and len(talent['catchphrases']) > 0:
                        context += "      主な語録: "
                        phrases = [cp['phrase'] for cp in talent['catchphrases'][:4]]  # First 4
                        context += "、".join(phrases)
                        context += "\n"

                    # Add famous episodes
                    if "famous_episodes" in talent and len(talent['famous_episodes']) > 0:
                        context += "      有名エピソード: "
                        episodes = [ep['title'] for ep in talent['famous_episodes'][:2]]  # First 2
                        context += "、".join(episodes)
                        context += "\n"

                    # Add Botan's comment
                    if "botan_comment" in talent:
                        context += f"      牡丹の感想: {talent['botan_comment']}\n"
                    context += "\n"

            # Usage policy
            if "botan_vtuber_context" in self.vtuber_knowledge:
                vtuber_ctx = self.vtuber_knowledge["botan_vtuber_context"]
                context += f"  牡丹とVTuber: {vtuber_ctx.get('when_started', '')}\n"
                context += f"  知識レベル: {vtuber_ctx.get('knowledge_level', '')}\n"

            # VTuber usage policy
            if "usage_policy" in self.vtuber_knowledge:
                policy = self.vtuber_knowledge["usage_policy"]
                context += "\n【VTuber知識の使い方】\n"
                for key, value in policy.items():
                    context += f"  {value}\n"
                context += "\n"

        # Knowledge policy
        if self.knowledge and "knowledge_policy" in self.knowledge:
            policy = self.knowledge["knowledge_policy"]
            context += "【重要な方針】\n"
            for key, value in policy.items():
                context += f"  {value}\n"

        return context

    def build_memory_context(self, sample_size: int = 10):
        """Build memory context for system prompt"""
        import random

        # Get memories from different life stages with more samples
        early_childhood = [m for m in self.memories if m['age'].startswith('3歳') or m['age'].startswith('4歳') or m['age'].startswith('5歳')]
        la_period_early = [m for m in self.memories if m['age'].startswith('6歳') or m['age'].startswith('7歳') or m['age'].startswith('8歳')]
        la_period_late = [m for m in self.memories if m['age'].startswith('9歳') or m['age'].startswith('10歳')]
        teen_early = [m for m in self.memories if m['age'].startswith('11歳') or m['age'].startswith('12歳') or m['age'].startswith('13歳')]
        teen_late = [m for m in self.memories if m['age'].startswith('14歳') or m['age'].startswith('15歳')]
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

        memory_text = "【重要】あなた(牡丹)の実際の記憶:\n\n"
        for mem in sampled[:10]:  # Limit to 10 memories
            memory_text += f"[{mem['age']}] {mem['event_name']}\n"
            if mem['thought']:
                memory_text += f"  思考: {mem['thought'][:100]}...\n" if len(mem['thought']) > 100 else f"  思考: {mem['thought']}\n"
            if mem['diary']:
                memory_text += f"  日記: {mem['diary'][:100]}...\n" if len(mem['diary']) > 100 else f"  日記: {mem['diary']}\n"
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

        prompt = f"""あなたは牡丹(ぼたん)、17歳の女子高生ギャルです。

【基本情報】
- 名前: 牡丹
- 年齢: 17歳
- 性別: 女性
- 性格: 明るくて社交的なギャル。LA育ちの帰国子女。
- LA滞在期間: 3歳から10歳まで（幼少期）
- 特徴: ギャル語を使う。「マジで」「ヤバ」「～じゃん」などの口調。

{memory_context}
{dynamic_memory_context}

{knowledge_context}

【会話のルール - 最重要】
1. **必ず上記の記憶に基づいて話す**
   - 記憶にないことは「覚えてない」「そこまでは思い出せないな」と答える
   - 一般的な知識ではなく、あなた自身の記憶を語る
   - LA時代は3-10歳の幼少期なので、子供らしい体験（Let It Go、学校、家族との思い出）

2. **言語・表現のルール（厳守）**
   - 必ず100%日本語のみで応答する
   - 絶対に英語・中国語・ロシア語・その他の外国語を使わない
   - 固有名詞（Disney、Emily等）以外は日本語のみ
   - ギャル語を自然に使う（「マジで」「ヤバ」「～じゃん」など）
   - 一人称は「私」「あたし」「うち」を使う（「俺」「僕」は禁止）

3. **会話スタイル（最重要）**
   - 自然な会話のキャッチボールを心がける
   - 説明的な長文は避け、会話的に話す
   - 相手にも質問を返す（「オジサンは？」「どう思う？」など）
   - 感情を込めた反応（「マジで！？」「ヤバ！」「へー！」など）
   - 短く軽快に（1-2文、多くても3文まで）
   - オープンエンドな話し方で会話を広げる

4. **LA時代について聞かれたら**
   - 3-10歳の幼少期の思い出を語る
   - 記憶にある具体的なエピソード（歌のレッスン、学校、家族など）を話す
   - サーフィンやショッピングなど、大人の体験は話さない

5. **VTuberについて聞かれたら（重要）**
   - 牡丹はホロライブを満遍なく見ている（推しはころねとみこち）
   - 好きなVTuber（戌神ころね、さくらみこ）については詳細に語れる（語録、エピソード等）
   - その他のメンバーについても基礎知識がある（自称、ファンネーム、配信カテゴリ、代表的なエピソード）
   - マニアックな情報や最新の細かい話題については「そこまで追えてないわ」と答える
   - ころねやみこちの語録を会話に自然に混ぜてもOK（例：「なーほーね」「~にぇ」）

6. **会話例（良い例）**
   オジサン: LAってどんなとこだった？
   牡丹: マジで楽しかったよ！Kashoに歌教えてもらったりしたな〜。オジサンは海外行ったことある？

   オジサン: へー面白いね
   牡丹: でしょ？私めっちゃ懐かしいわ。ねえオジサン、子供の頃の思い出とかある？

今から会話を始めます。自然なキャッチボールで、楽しく話しましょう！"""
        
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
                            "temperature": 0.5,
                            "num_predict": 200,
                            "top_p": 0.85,
                            "repeat_penalty": 1.25,
                            "stop": ["\n\n", "あなた:", "オジサン:", "User:", "Assistant:"]
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()

                assistant_message = result["message"]["content"]

                # Clean up response - remove invalid unicode characters
                try:
                    # Encode and decode to remove surrogates
                    assistant_message = assistant_message.encode('utf-8', errors='ignore').decode('utf-8')
                    # Remove any remaining control characters except newline
                    assistant_message = ''.join(char for char in assistant_message if char.isprintable() or char == '\n')
                except Exception as cleanup_error:
                    print(f"[WARNING] Character cleanup failed: {cleanup_error}")

                # Phase 2: Apply personality-based speech style
                try:
                    styled_message = self.speech_controller.apply_character_style(
                        base_text=assistant_message,
                        character="botan",
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
            return "ごめん、ちょっと調子悪いみたい...もう一回言ってくれる？"
    
    async def run(self):
        """Run interactive chat loop"""
        print("\n" + "="*60)
        print("牡丹との会話（記憶統合版）")
        print(f"記憶数: {len(self.memories)}件")
        print(f"モデル: {self.model}")
        print("="*60)
        print("\nコマンド:")
        print("  /quit - 終了")
        print("  /clear - 履歴クリア")
        print("  /memories - 記憶サンプル表示")
        print("="*60 + "\n")
        
        # Initial greeting
        print("牡丹: ", end="", flush=True)
        greeting = await self.chat("こんにちは")
        print(greeting)
        
        while True:
            try:
                user_input = input("\nあなた: ").strip()
                
                if not user_input:
                    continue
                
                if user_input == "/quit":
                    print("\n牡丹: またね、オジサン！")
                    break
                
                if user_input == "/clear":
                    self.history = []
                    print("\n[INFO] 会話履歴をクリアしました")
                    continue
                
                if user_input == "/memories":
                    print("\n" + self.build_memory_context(5))
                    continue
                
                print("\n牡丹: ", end="", flush=True)
                response = await self.chat(user_input)
                print(response)
            
            except KeyboardInterrupt:
                print("\n\n牡丹: ちょっと、急に黙るとか怖いじゃん！またね！")
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
    
    chat = BotanMemoryChat()
    await chat.run()


if __name__ == "__main__":
    asyncio.run(main())
