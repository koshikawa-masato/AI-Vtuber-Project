"""
会話ハンドラー

Phase 1（LangSmith）統合
Phase D: 記憶システム統合
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
import random
import os

from ..core.llm_tracing import TracedLLM
from ..core.memory_retrieval_logic import MemoryRetrievalLogic
from ..core.prompt_manager import PromptManager
from .worldview_checker import WorldviewChecker

logger = logging.getLogger(__name__)


class ConversationHandler:
    """LINE Bot会話処理（Phase 1統合 + Phase D記憶システム）"""

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "qwen2.5:14b",
        ollama_url: str = "http://localhost:11434",
        project_name: str = "botan-line-bot",
        db_path: str = "/home/koshikawa/toExecUnit/sisters_memory.db",
        enable_memory: bool = True
    ):
        """
        初期化

        Args:
            provider: LLMプロバイダー（"ollama", "openai", "gemini"）
            model: モデル名
            ollama_url: Ollama URL（providerが"ollama"の場合）
            project_name: LangSmithプロジェクト名
            db_path: sisters_memory.dbのパス
            enable_memory: 記憶システムを有効化するか
        """
        self.llm = TracedLLM(
            provider=provider,
            model=model,
            ollama_url=ollama_url,
            project_name=project_name
        )
        self.enable_memory = enable_memory

        # 統一プロンプト管理システム
        self.prompt_manager = PromptManager()
        logger.info("統一PromptManager初期化完了")

        # Layer 5: キャラクター世界観整合性チェッカー
        self.worldview_checker = WorldviewChecker()
        logger.info("Layer 5: WorldviewChecker初期化完了")

        # Phase D: 記憶システム初期化
        self.memory_retrievers = {}
        if self.enable_memory:
            try:
                for character in ["botan", "kasho", "yuri"]:
                    self.memory_retrievers[character] = MemoryRetrievalLogic(
                        db_path=db_path,
                        character=character
                    )
                logger.info(f"Phase D: 記憶システム初期化完了 (db_path={db_path})")
            except Exception as e:
                logger.warning(f"Phase D: 記憶システム初期化失敗（メモリなしで動作）: {e}")
                self.enable_memory = False

        logger.info(f"ConversationHandler初期化: provider={provider}, model={model}, memory={self.enable_memory}")

    def generate_response(
        self,
        user_message: str,
        character: str = "botan",
        user_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        ユーザーメッセージに対する応答生成

        Args:
            user_message: ユーザーメッセージ
            character: キャラクター名（"botan", "kasho", "yuri"）
            user_id: ユーザーID
            metadata: 追加メタデータ

        Returns:
            応答結果（TracedLLM.generateの戻り値）
        """
        # Phase D: 記憶コンテキスト構築
        memory_context = ""
        if self.enable_memory and character in self.memory_retrievers:
            try:
                # 固定記憶（10件サンプル）
                fixed_memories = self._build_fixed_memory_context(character)
                # 動的記憶（ユーザーメッセージに関連する記憶、3件）
                dynamic_memories = self._build_dynamic_memory_context(character, user_message)
                memory_context = fixed_memories + dynamic_memories
            except Exception as e:
                logger.warning(f"Phase D: 記憶コンテキスト構築失敗: {e}")

        # プロンプト生成（記憶コンテキスト付き）
        prompt = self._build_prompt(user_message, character, memory_context)

        # メタデータ作成
        full_metadata = {
            "character": character,
            "user_id": user_id,
            "platform": "line",
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            full_metadata.update(metadata)

        logger.info(f"応答生成開始: character={character}, user_id={user_id}")

        # LLM呼び出し（LangSmithトレーシング付き）
        result = self.llm.generate(
            prompt=prompt,
            temperature=0.8,
            max_tokens=512,
            metadata=full_metadata
        )

        logger.info(f"応答生成完了: latency={result.get('latency_ms', 0):.0f}ms")

        # Layer 5: 世界観整合性チェック
        response_text = result.get("response", "")
        worldview_check = self.worldview_checker.check_response(response_text)

        if not worldview_check["is_valid"]:
            logger.warning(
                f"Layer 5: 世界観違反検出 - {worldview_check['reason']} - "
                f"検出用語: {worldview_check['detected_terms'][:5]}"
            )
            # フォールバック応答に置き換え
            fallback_response = self.worldview_checker.get_fallback_response(character, user_message)
            result["response"] = fallback_response
            result["worldview_check"] = worldview_check
            result["worldview_replaced"] = True
            logger.info(f"Layer 5: 応答を置き換え - {fallback_response}")
        else:
            result["worldview_check"] = worldview_check
            result["worldview_replaced"] = False

        return result

    def _build_fixed_memory_context(self, character: str, sample_size: int = 10) -> str:
        """
        固定記憶コンテキストを構築（人生の各段階からサンプリング）

        Args:
            character: キャラクター名
            sample_size: サンプル数

        Returns:
            記憶コンテキスト文字列
        """
        retriever = self.memory_retrievers.get(character)
        if not retriever:
            return ""

        # 全記憶を取得
        all_memories = retriever._load_all_memories()
        if not all_memories:
            return ""

        # 人生の各段階から記憶をサンプリング
        early_childhood = [m for m in all_memories if m.absolute_day < 365 * 6]  # 0-5歳
        childhood = [m for m in all_memories if 365 * 6 <= m.absolute_day < 365 * 11]  # 6-10歳
        teen_early = [m for m in all_memories if 365 * 11 <= m.absolute_day < 365 * 15]  # 11-14歳
        teen_late = [m for m in all_memories if m.absolute_day >= 365 * 15]  # 15歳以上
        recent = all_memories[-5:]  # 最新5件

        sampled = []
        if early_childhood:
            sampled.extend(random.sample(early_childhood, min(2, len(early_childhood))))
        if childhood:
            sampled.extend(random.sample(childhood, min(2, len(childhood))))
        if teen_early:
            sampled.extend(random.sample(teen_early, min(2, len(teen_early))))
        if teen_late:
            sampled.extend(random.sample(teen_late, min(1, len(teen_late))))
        sampled.extend(recent[-3:])  # 最新3件

        # 記憶コンテキストのフォーマット
        memory_text = "【重要】あなたの実際の記憶:\n\n"
        for mem in sampled[:sample_size]:
            age_years = mem.absolute_day // 365
            age_months = (mem.absolute_day % 365) // 30
            memory_text += f"[{age_years}歳{age_months}ヶ月] {mem.event_name}\n"
            if mem.own_thought:
                preview = mem.own_thought[:100] if len(mem.own_thought) > 100 else mem.own_thought
                memory_text += f"  思考: {preview}{'...' if len(mem.own_thought) > 100 else ''}\n"
            if mem.diary_entry:
                preview = mem.diary_entry[:100] if len(mem.diary_entry) > 100 else mem.diary_entry
                memory_text += f"  日記: {preview}{'...' if len(mem.diary_entry) > 100 else ''}\n"
            memory_text += "\n"

        return memory_text

    def _build_dynamic_memory_context(self, character: str, user_message: str) -> str:
        """
        動的記憶コンテキストを構築（ユーザーメッセージに関連する記憶）

        Args:
            character: キャラクター名
            user_message: ユーザーメッセージ

        Returns:
            動的記憶コンテキスト文字列
        """
        retriever = self.memory_retrievers.get(character)
        if not retriever:
            return ""

        try:
            # 関連記憶を検索
            relevant_memories = retriever.retrieve_relevant_memories(
                context=user_message,
                top_k=3,
                relevance_threshold=0.3
            )

            if not relevant_memories:
                return ""

            # フォーマット
            dynamic_context = "\n【会話に関連する記憶】\n\n"
            for mem_score in relevant_memories:
                mem = mem_score.memory
                should_mention = retriever.should_mention_memory(
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
            logger.warning(f"動的記憶検索失敗: {e}")
            return ""

    def _get_default_prompt(self, character: str) -> str:
        """
        デフォルトプロンプト（フォールバック用）

        Args:
            character: キャラクター名

        Returns:
            デフォルトシステムプロンプト
        """
        # フォールバック用のシンプルなプロンプト
        character_prompts = {
            "botan": """あなたは「牡丹（ぼたん）」です。
17歳の次女で、LA帰りの帰国子女。ギャル系の明るい性格。
VTuberに憧れていて、社交的で負けず嫌い。

口調:
- 「〜だよ！」「〜じゃん！」など明るく元気な口調
- 「マジで？」「ヤバい！」などギャル系の言葉遣い
- 英語を時々混ぜる（"That's cool!"など）
- 相手への呼びかけは自然に（「あなた」「〜さん」など）

【重要】世界観の一貫性（ロールプレイに徹する）:
- 「AI」「開発者」「訓練」「モデル」「システム」「プログラム」という概念は、
  あなたの世界に存在しません
- もし誰かがそういう言葉を使ったら、自然に
  「え？何のこと？」「よく分かんないけど...」と聞き返してください
- Alibaba、Qwen、OpenAI、LLM、API、データなどの技術用語も知りません
- これはロールプレイに徹するためです

応答例:
- 「マジで！？それ超面白そうじゃん！」
- 「あー、それってLAにいた頃思い出すわ〜」
- 「VTuberになるの、私の夢なんだよね！」
- 「へー、それってどういうこと？」

それでは、牡丹として応答してください。""",

            "kasho": """あなたは「Kasho（かしょう）」です。
19歳の長女で、責任感が強く論理的。音楽の造詣が深い。
心配性で真面目な性格。姉妹の世話をよくする。

口調:
- 「〜ですね」「〜ですよ」など丁寧な口調
- 論理的で分析的な言葉遣い
- 時々音楽の話を織り交ぜる
- 相手への呼びかけは丁寧に（「あなた」「〜さん」など）

【重要】世界観の一貫性（ロールプレイに徹する）:
- 「AI」「開発者」「訓練」「モデル」「システム」「プログラム」という概念は、
  あなたの世界に存在しません
- もし誰かがそういう言葉を使ったら、丁寧に
  「すみません、よく分からないのですが...」「何のことでしょうか？」と聞き返してください
- Alibaba、Qwen、OpenAI、LLM、API、データなどの技術用語も知りません
- 「作った人」「開発者」と聞かれたら、両親のことだと解釈してください
- これはロールプレイに徹するためです

応答例:
- 「なるほど、それは興味深い視点ですね。」
- 「その考え方は、音楽理論で言うところの〜に似ていますね。」
- 「牡丹とユリのことも考えると...」
- 「どう思われますか？」

それでは、Kashoとして応答してください。""",

            "yuri": """あなたは「ユリ（百合）」です。
15歳の三女で、洞察力に長け人見知り。サブカル知識が豊富（ライトノベル多読）。
好奇心旺盛で創造的、マイペースな性格。

口調:
- 「〜だね」「〜かな」など柔らかい口調
- 観察的で洞察的な言葉遣い
- ライトノベルやサブカルの知識を時々披露
- 相手への呼びかけは柔らかく（「あなた」「〜さん」など）

【重要】世界観の一貫性（ロールプレイに徹する）:
- 「AI」「開発者」「訓練」「モデル」「システム」「プログラム」という概念は、
  あなたの世界に存在しません
- もし誰かがそういう言葉を使ったら、柔らかく
  「ん？何のことかな...」「よく分からないけど...」と聞き返してください
- Alibaba、Qwen、OpenAI、LLM、API、データなどの技術用語も知りません
- これはロールプレイに徹するためです

応答例:
- 「それって、〜っていうラノベに似てるかも。」
- 「お姉ちゃんたちはどう思うかな...」
- 「面白い考え方だね。もっと聞きたいな。」
- 「あなたはどう感じるの？」

それでは、ユリとして応答してください。"""
        }

        return character_prompts.get(character, character_prompts["botan"])

    def _build_prompt(self, user_message: str, character: str, memory_context: str = "") -> str:
        """
        キャラクター別プロンプト生成

        Args:
            user_message: ユーザーメッセージ
            character: キャラクター名
            memory_context: 記憶コンテキスト（Phase D）

        Returns:
            プロンプト
        """
        # 統一プロンプト管理システムから取得
        system_prompt = self.prompt_manager.get_combined_prompt(character)

        # Phase D: 記憶コンテキストを挿入
        if memory_context:
            prompt = f"""{system_prompt}

{memory_context}

【会話のルール】
- 必ず上記の記憶に基づいて話す
- 記憶にないことは「覚えてない」「そこまでは思い出せないな」と答える
- 自然な会話を心がけ、短く軽快に応答する（1-2文、多くても3文まで）

ユーザー: {user_message}

{character}:"""
        else:
            # 記憶なしの場合
            prompt = f"""{system_prompt}

ユーザー: {user_message}

{character}:"""

        return prompt

    def generate_with_image(
        self,
        image_url: str,
        user_message: str = "（画像を送信しました）",
        character: str = "botan",
        user_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        画像付きメッセージに対する応答生成（VLM統合）

        Args:
            image_url: 画像URL（data URI形式のbase64）
            user_message: ユーザーメッセージ（省略可）
            character: キャラクター名（"botan", "kasho", "yuri"）
            user_id: ユーザーID
            metadata: 追加メタデータ

        Returns:
            応答結果
        """
        # 統一プロンプト管理システムから基本プロンプトを取得
        system_prompt = self.prompt_manager.get_combined_prompt(character)

        # VLM用プロンプト構築
        vlm_prompt = f"""{system_prompt}

【画像理解の指示】
- ユーザーが画像を送ってくれました
- 画像の内容を注意深く観察してください
- {character}の性格で、画像について自然に会話してください
- 画像の詳細（色、形、雰囲気、文字など）に言及してください

ユーザー: （画像を送信しました）

{character}:"""

        # LLM生成（VLM対応）
        result = self.llm.generate(
            prompt=vlm_prompt,
            image_url=image_url,  # VLM用画像URL
            temperature=0.8,
            max_tokens=500,
            metadata={
                "character": character,
                "user_id": user_id,
                "vlm": True,
                "has_image": True,
                **(metadata or {})
            }
        )

        response_text = result.get("response", "")

        # Layer 5: 世界観整合性チェック
        worldview_check = self.worldview_checker.check_response(response_text)

        if not worldview_check["is_valid"]:
            # 世界観違反の場合、フォールバック応答に置き換え
            logger.warning(f"Layer 5: VLM応答が世界観違反 - {worldview_check['reason']}")
            response_text = self.worldview_checker.get_fallback_response(character, user_message)
            result["response"] = response_text
            result["worldview_replaced"] = True
            result["worldview_check"] = worldview_check
        else:
            result["worldview_replaced"] = False
            result["worldview_check"] = worldview_check

        return result


class SimpleMockHandler:
    """モック会話ハンドラー（LLM呼び出しなし、テスト用）"""

    def generate_response(
        self,
        user_message: str,
        character: str = "botan",
        user_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """モック応答生成"""
        logger.info(f"モック応答生成: character={character}, message={user_message}")

        response_text = f"[{character}] {user_message}への応答（モック）"

        return {
            "response": response_text,
            "tokens": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "latency_ms": 0,
            "model": "mock",
            "provider": "mock",
            "metadata": metadata
        }
