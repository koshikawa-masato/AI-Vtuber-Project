"""
クラウドLLMプロバイダー（OpenAI gpt-4o-mini対応）

VPS用: 高速・低コスト・30秒制約対応
"""

import os
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class CloudLLMProvider:
    """クラウドLLMプロバイダー（OpenAI gpt-4o-mini）"""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        初期化

        Args:
            provider: LLMプロバイダー（"openai"）
            model: モデル名
            temperature: 温度パラメータ
            max_tokens: 最大トークン数
        """
        self.provider = provider
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")

            self.client = OpenAI(api_key=api_key)
            logger.info(f"✅ OpenAI初期化完了: {model}")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        テキスト生成

        Args:
            prompt: ユーザープロンプト
            system_prompt: システムプロンプト
            metadata: メタデータ（ログ用）

        Returns:
            生成されたテキスト
        """
        try:
            # メッセージ構築
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # OpenAI API呼び出し
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            result = response.choices[0].message.content

            # ログ記録
            logger.info(f"✅ LLM生成成功: {len(result)}文字")
            if metadata:
                logger.debug(f"   メタデータ: {metadata}")

            return result

        except Exception as e:
            logger.error(f"❌ LLM生成エラー: {e}")
            raise

    def generate_with_context(
        self,
        user_message: str,
        character_name: str,
        character_prompt: str,
        memories: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        コンテキスト付き生成

        Args:
            user_message: ユーザーメッセージ
            character_name: キャラクター名
            character_prompt: キャラクター別プロンプト
            memories: Phase D記憶（任意）
            metadata: メタデータ

        Returns:
            生成されたテキスト
        """
        # システムプロンプト構築
        system_prompt = f"""あなたは{character_name}です。

{character_prompt}
"""

        # 記憶を追加
        if memories:
            system_prompt += f"\n\n【記憶】\n{memories}\n"

        system_prompt += "\n重要な指示：\n- 30秒以内に応答を完了してください\n- 簡潔で自然な会話を心がけてください"

        return self.generate(
            prompt=user_message,
            system_prompt=system_prompt,
            metadata=metadata
        )


# テスト用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # OpenAI gpt-4o-miniテスト
    try:
        llm = CloudLLMProvider(provider="openai", model="gpt-4o-mini")

        response = llm.generate_with_context(
            user_message="おはよう！",
            character_name="牡丹",
            character_prompt="あなたは明るく社交的な17歳の女の子です。ギャル口調で話します。",
            memories=None
        )

        print(f"\n応答: {response}\n")
    except Exception as e:
        print(f"エラー: {e}")
