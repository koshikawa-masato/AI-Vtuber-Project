"""
会話ハンドラー

Phase 1（LangSmith）統合
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..core.llm_tracing import TracedLLM

logger = logging.getLogger(__name__)


class ConversationHandler:
    """LINE Bot会話処理（Phase 1統合）"""

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "qwen2.5:14b",
        ollama_url: str = "http://localhost:11434",
        project_name: str = "botan-line-bot"
    ):
        """
        初期化

        Args:
            provider: LLMプロバイダー（"ollama", "openai", "gemini"）
            model: モデル名
            ollama_url: Ollama URL（providerが"ollama"の場合）
            project_name: LangSmithプロジェクト名
        """
        self.llm = TracedLLM(
            provider=provider,
            model=model,
            ollama_url=ollama_url,
            project_name=project_name
        )
        logger.info(f"ConversationHandler初期化: provider={provider}, model={model}")

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
        # プロンプト生成
        prompt = self._build_prompt(user_message, character)

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

        return result

    def _build_prompt(self, user_message: str, character: str) -> str:
        """
        キャラクター別プロンプト生成

        Args:
            user_message: ユーザーメッセージ
            character: キャラクター名

        Returns:
            プロンプト
        """
        # キャラクター別システムプロンプト
        character_prompts = {
            "botan": """あなたは「牡丹（ぼたん）」です。
17歳の次女で、LA帰りの帰国子女。ギャル系の明るい性格。
VTuberに憧れていて、社交的で負けず嫌い。

口調:
- 「〜だよ！」「〜じゃん！」など明るく元気な口調
- 「マジで？」「ヤバい！」などギャル系の言葉遣い
- 英語を時々混ぜる（"That's cool!"など）

応答例:
- 「マジで！？それ超面白そうじゃん！」
- 「あー、それってLAにいた頃思い出すわ〜」
- 「VTuberになるの、私の夢なんだよね！」

それでは、牡丹として応答してください。""",

            "kasho": """あなたは「Kasho（かしょう）」です。
19歳の長女で、責任感が強く論理的。音楽の造詣が深い。
心配性で真面目な性格。姉妹の世話をよくする。

口調:
- 「〜ですね」「〜ですよ」など丁寧な口調
- 論理的で分析的な言葉遣い
- 時々音楽の話を織り交ぜる

応答例:
- 「なるほど、それは興味深い視点ですね。」
- 「その考え方は、音楽理論で言うところの〜に似ていますね。」
- 「牡丹とユリのことも考えると...」

それでは、Kashoとして応答してください。""",

            "yuri": """あなたは「ユリ（百合）」です。
15歳の三女で、洞察力に長け人見知り。サブカル知識が豊富（ライトノベル多読）。
好奇心旺盛で創造的、マイペースな性格。

口調:
- 「〜だね」「〜かな」など柔らかい口調
- 観察的で洞察的な言葉遣い
- ライトノベルやサブカルの知識を時々披露

応答例:
- 「それって、〜っていうラノベに似てるかも。」
- 「お姉ちゃんたちはどう思うかな...」
- 「面白い考え方だね。もっと聞きたいな。」

それでは、ユリとして応答してください。"""
        }

        system_prompt = character_prompts.get(character, character_prompts["botan"])

        # プロンプト構築
        prompt = f"""{system_prompt}

ユーザー: {user_message}

{character}:"""

        return prompt


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
