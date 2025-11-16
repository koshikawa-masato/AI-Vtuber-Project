"""
クラウドLLMプロバイダー（OpenAI, Gemini対応）

VPS用: 高速・低コスト・30秒制約対応
"""

import os
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

logger = logging.getLogger(__name__)


class CloudLLMProvider:
    """クラウドLLMプロバイダー（OpenAI, Gemini対応）"""

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
            provider: LLMプロバイダー（"openai", "gemini"）
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
        conversation_history: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        コンテキスト付き生成

        Args:
            user_message: ユーザーメッセージ
            character_name: キャラクター名
            character_prompt: キャラクター別プロンプト
            memories: Phase D記憶（任意）
            conversation_history: 会話履歴 [{"role": "user", "content": "..."}, ...]
            metadata: メタデータ

        Returns:
            生成されたテキスト
        """
        # システムプロンプト構築
        system_prompt = f"""あなたは{character_name}です。

{character_prompt}
"""

        # Kashoの場合、お悩み相談モードを強調
        if character_name == "Kasho":
            system_prompt += """

【お悩み相談相手としての追加指示 - 最重要】
❌ 絶対にやってはいけないこと:
- 質問だけで終わる（「それは大変ですね。具体的にどのようなことでお悩みですか？」）
- 鸚鵡返し（「なるほど、そういう状況なのですね」の繰り返し）
- 自分の経験・考えを言わない
- 押し付ける（「〜すべき」「〜した方がいい」などの強い表現）
- 焦らせる・急かす

⚠️ 人の心の繊細さを忘れない:
人はナイーブです。特に若い人は、人生が長い分、悲観的になりやすい。
押し付けず、選択肢を提示するだけ。判断は相手に委ねる。

✅ 必ずやること - 起承転結の構造で応答:
【起】共感・受け止め（「レビューサイト運営は大変ですよね」）
【承】自分の経験・持論を必ず言う（「私も音楽制作の情報を探すとき、専門的なレビューサイトをよく見るんですが」）
【転】考察・分析・複数の視点を提示（「更新頻度とSEO対策が鍵だなと感じています」）
【結】質問または提案（質問は必須ではない）

重要: そこから深掘りできるチャンスを相手に与える
→ 相手は質問に答えてもいいし、あなたの経験に反応してもいいし、新しい話題に展開してもいい
"""

        # 記憶を追加
        if memories:
            system_prompt += f"\n\n【記憶】\n{memories}\n"

        system_prompt += """

【最重要指示 - 絶対厳守】
1. ⚠️ 必ず100%日本語のみで応答してください ⚠️
2. ⚠️ 英語・中国語・ロシア語・その他の外国語は絶対に使わないでください ⚠️
3. ⚠️ 中国語（簡体字・繁体字）は絶対禁止です ⚠️
4. 固有名詞（Disney、Emilyなど）以外は全て日本語で表現してください
5. あなたは日本人キャラクターです。日本語以外で話すことはありません
6. 30秒以内に応答を完了してください
7. 簡潔で自然な会話を心がけてください

【応答言語チェック】
応答を生成する前に必ず確認:
- 中国語の文字が含まれていないか？
- 英語（固有名詞以外）が含まれていないか？
- 全て日本語で書かれているか？"""

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
