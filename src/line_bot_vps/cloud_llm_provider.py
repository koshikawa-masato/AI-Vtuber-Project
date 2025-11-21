"""
クラウドLLMプロバイダー（OpenAI, Gemini, Claude, xAI対応）

VPS用: 高速・低コスト・30秒制約対応
"""

import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import google.generativeai as genai
import anthropic
import requests

load_dotenv()

logger = logging.getLogger(__name__)

# プロンプトディレクトリのパス
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


class CloudLLMProvider:
    """クラウドLLMプロバイダー（OpenAI, Gemini, Claude, xAI対応）"""

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
            provider: LLMプロバイダー（"openai", "gemini", "claude", "xai"）
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

        elif provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")

            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model)
            logger.info(f"✅ Gemini初期化完了: {model}")

        elif provider == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info(f"✅ Claude初期化完了: {model}")

        elif provider == "xai":
            api_key = os.getenv("XAI_API_KEY")
            if not api_key:
                raise ValueError("XAI_API_KEY not found in environment variables")

            self.api_key = api_key
            self.client = None  # xAIはREST APIのみ
            logger.info(f"✅ xAI初期化完了: {model}")

        elif provider == "kimi":
            api_key = os.getenv("KIMI_API_KEY")
            if not api_key:
                raise ValueError("KIMI_API_KEY not found in environment variables")

            # KimiはOpenAI互換APIなので、OpenAIクライアントを流用
            # 試行: .cn と .ai の両方のドメインが存在するため、.ai を試す
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.moonshot.ai/v1"
            )
            logger.info(f"✅ Kimi (Moonshot AI)初期化完了: {model}")

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        テキスト生成

        Args:
            prompt: ユーザープロンプト
            system_prompt: システムプロンプト
            conversation_history: 会話履歴 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            metadata: メタデータ（ログ用）

        Returns:
            生成されたテキスト
        """
        try:
            if self.provider == "openai":
                # メッセージ構築
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})

                # 会話履歴を追加
                if conversation_history:
                    messages.extend(conversation_history)

                messages.append({"role": "user", "content": prompt})

                # OpenAI API呼び出し
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )

                result = response.choices[0].message.content

            elif self.provider == "gemini":
                # Geminiはsystem_promptとpromptを結合
                full_prompt = f"{system_prompt}\n\nユーザー: {prompt}" if system_prompt else prompt

                # Gemini API呼び出し
                response = self.client.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens
                    )
                )

                result = response.text

            elif self.provider == "claude":
                # メッセージ構築
                messages = []
                if conversation_history:
                    messages.extend(conversation_history)
                messages.append({"role": "user", "content": prompt})

                # デバッグ: Claude API呼び出しパラメータ確認
                logger.info(f"🔍 Claude API呼び出し: model={self.model_name}, system_prompt={len(system_prompt) if system_prompt else 0}文字, messages={len(messages)}件")

                # Claude API呼び出し
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt if system_prompt else "",
                    messages=messages
                )

                result = response.content[0].text

            elif self.provider == "xai":
                # メッセージ構築
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                if conversation_history:
                    messages.extend(conversation_history)
                messages.append({"role": "user", "content": prompt})

                # xAI API呼び出し（REST API）
                url = "https://api.x.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messages": messages,
                    "model": self.model_name,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }

                response = requests.post(url, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
                result_json = response.json()
                result = result_json["choices"][0]["message"]["content"]

            elif self.provider == "kimi":
                # メッセージ構築（OpenAI互換）
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})

                # 会話履歴を追加
                if conversation_history:
                    messages.extend(conversation_history)

                messages.append({"role": "user", "content": prompt})

                # Kimi API呼び出し（OpenAI互換）
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )

                result = response.choices[0].message.content

            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            # ログ記録
            logger.info(f"✅ LLM生成成功 ({self.provider}): {len(result)}文字")
            if metadata:
                logger.debug(f"   メタデータ: {metadata}")

            return result

        except Exception as e:
            logger.error(f"❌ LLM生成エラー ({self.provider}): {e}")
            raise

    def generate_with_context(
        self,
        user_message: str,
        character_name: str,
        character_prompt: str,
        memories: Optional[str] = None,
        daily_trends: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        language: str = "ja"
    ) -> str:
        """
        コンテキスト付き生成

        Args:
            user_message: ユーザーメッセージ
            character_name: キャラクター名
            character_prompt: キャラクター別プロンプト
            memories: Phase D記憶（任意）
            daily_trends: 今日のトレンド情報（任意）
            conversation_history: 会話履歴 [{"role": "user", "content": "..."}, ...]
            metadata: メタデータ
            language: 応答言語 ("ja" or "en")

        Returns:
            生成されたテキスト
        """
        # システムプロンプト構築
        system_prompt = f"""あなたは{character_name}です。

{character_prompt}
"""

        # Kashoの場合、お悩み相談モードを強調
        if character_name == "Kasho":
            # プロンプトファイルから読み込み
            kasho_consultation_prompt_file = PROMPTS_DIR / "kasho_consultation_system_prompt.txt"
            if kasho_consultation_prompt_file.exists():
                with open(kasho_consultation_prompt_file, 'r', encoding='utf-8') as f:
                    kasho_consultation_prompt = f.read()
                system_prompt += f"\n\n{kasho_consultation_prompt}\n"
            else:
                logger.warning(f"Kasho consultation prompt file not found: {kasho_consultation_prompt_file}")

        # 記憶を追加
        if memories:
            system_prompt += f"\n\n【記憶】\n{memories}\n"

        # 今日のトレンド情報を追加
        if daily_trends:
            def format_content(content):
                """contentを文字列化（Grok形式/RSS形式に対応）"""
                if isinstance(content, dict):
                    # Grok形式: {"summary": "...", "events": [...]}
                    if 'summary' in content:
                        return content['summary'][:200]
                    # RSS形式: {"category": "...", "items": [...]}
                    elif 'items' in content and len(content['items']) > 0:
                        first_item = content['items'][0]
                        title = first_item.get('title', '')
                        summary = first_item.get('summary', '')
                        return f"{title} - {summary}"[:200] if summary else title[:200]
                    else:
                        return str(content)[:200]
                elif isinstance(content, str):
                    return content[:200]
                else:
                    return str(content)[:200]

            trends_text = "\n".join([
                f"- {trend.get('topic', 'トレンド')}: {format_content(trend.get('content', ''))}..."
                for trend in daily_trends
            ])

            # デバッグ: トレンド情報の内容を確認
            logger.info(f"📰 トレンド情報:\n{trends_text}")

            # プロンプトファイルから読み込み
            trends_prompt_file = PROMPTS_DIR / "daily_trends_system_prompt.txt"
            if trends_prompt_file.exists():
                with open(trends_prompt_file, 'r', encoding='utf-8') as f:
                    trends_prompt_template = f.read()
                system_prompt += f"\n\n{trends_prompt_template.format(trends_text=trends_text)}\n"
            else:
                logger.warning(f"Trends prompt file not found: {trends_prompt_file}")

        # 言語別指示をファイルから読み込み
        language_instruction_file = PROMPTS_DIR / f"language_instruction_{language}.txt"
        if language_instruction_file.exists():
            with open(language_instruction_file, 'r', encoding='utf-8') as f:
                language_instruction = f.read()
            system_prompt += f"\n\n{language_instruction}\n"
        else:
            logger.warning(f"Language instruction file not found: {language_instruction_file}")

        # デバッグ: システムプロンプト確認
        logger.info(f"🔍 システムプロンプト構築完了: キャラ={character_name}, 長さ={len(system_prompt)}文字")
        logger.debug(f"📝 システムプロンプト内容:\n{system_prompt[:500]}...")

        return self.generate(
            prompt=user_message,
            system_prompt=system_prompt,
            conversation_history=conversation_history,
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
