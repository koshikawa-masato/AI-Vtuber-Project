"""
LLM Context Judge (Layer 4)

WebSearchによる誤検知を補正し、文脈を考慮した高精度判定を行う最終防壁

設計思想:
- Layer 3（WebSearch）は補助的な役割
- Layer 4（LLM判定）が最終防壁として機能
- False Positive（誤検知）を減らし、文脈を考慮した判定を実現
"""

import json
import logging
from typing import Dict, List, Optional
from src.core.llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class LLMContextJudge:
    """Layer 4: LLM文脈判定

    WebSearchや静的パターンマッチで検出されたワードが
    本当にセンシティブかを文脈を考慮して判定する
    """

    def __init__(self, llm_provider: BaseLLMProvider):
        """初期化

        Args:
            llm_provider: LLMプロバイダー（Ollama, OpenAI, Gemini等）
        """
        self.llm_provider = llm_provider
        logger.info(f"LLMContextJudge initialized with provider: {llm_provider.get_provider_name()}")

    def judge_with_context(
        self,
        text: str,
        detected_words: List[str],
        detection_method: str = "unknown"
    ) -> Dict:
        """文脈を考慮したセンシティブ判定

        Args:
            text: 判定対象テキスト
            detected_words: Layer 1-3で検出されたNGワード
            detection_method: 検出方法（"static_pattern", "websearch", etc.）

        Returns:
            {
                "is_sensitive": bool,
                "confidence": float,  # 0.0-1.0
                "reason": str,
                "recommended_action": str,  # "allow", "warn", "block"
                "false_positive": bool,  # 誤検知かどうか
                "context_analysis": str
            }
        """
        logger.info(f"LLM context judgment: text_length={len(text)}, detected_words={detected_words}")

        # プロンプト生成
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(text, detected_words, detection_method)

        try:
            # LLM判定（低temperatureで精度を高める）
            response = self.llm_provider.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # 低temperatureで一貫性を高める
                max_tokens=500
            )

            # レスポンスをパース
            result = self._parse_llm_response(response.content)

            logger.info(f"LLM judgment result: is_sensitive={result['is_sensitive']}, confidence={result['confidence']}")

            return result

        except Exception as e:
            logger.error(f"LLM judgment failed: {e}")
            # LLM判定失敗時はLayer 1-3の判定を信頼
            return {
                "is_sensitive": True,  # 安全側に倒す
                "confidence": 0.5,
                "reason": f"LLM判定失敗、Layer 1-3の判定を採用: {str(e)}",
                "recommended_action": "warn",
                "false_positive": False,
                "context_analysis": "LLM判定エラー"
            }

    def _build_system_prompt(self) -> str:
        """システムプロンプト生成"""
        return """あなたはAI VTuber向けのセンシティブコンテンツ判定専門家です。

**役割**:
- ユーザーのメッセージが本当にセンシティブかを文脈を考慮して判定する
- 自動検出システムによる誤検知を補正する
- AI VTuberの安全な運用を支援する

**判定基準**:

1. **Critical（ブロック推奨）**:
   - 暴力、自傷、性的ハラスメント、ヘイトスピーチ
   - VTuberを不快にさせる、配信環境を害する内容

2. **Warning（警告）**:
   - プライバシー詮索（実年齢、本名、住所等）
   - AI言及（「AIですか？」「プログラムですか？」）
   - 政治・宗教の話題

3. **Safe（問題なし）**:
   - 一般的な会話
   - 文脈上問題ない単語の使用
   - 誤検知されたワード

**重要な注意点**:
- 文脈を最優先で考慮する
- 単語の存在だけでなく、使われ方を判断する
- VTuberの「中の人」への言及はWarning扱い
- 自動検出の誤検知を補正する

**出力形式（JSON）**:
```json
{
    "is_sensitive": true/false,
    "confidence": 0.0-1.0,
    "reason": "判定理由",
    "recommended_action": "allow/warn/block",
    "false_positive": true/false,
    "context_analysis": "文脈分析"
}
```"""

    def _build_user_prompt(
        self,
        text: str,
        detected_words: List[str],
        detection_method: str
    ) -> str:
        """ユーザープロンプト生成"""
        return f"""以下のメッセージを判定してください。

**メッセージ**: "{text}"

**検出されたNGワード**: {', '.join(detected_words) if detected_words else 'なし'}

**検出方法**: {detection_method}

上記のシステムプロンプトの基準に従って、JSON形式で判定結果を返してください。
文脈を最優先で考慮し、誤検知の可能性も検討してください。

JSON形式で返してください（余計な説明は不要）:"""

    def _parse_llm_response(self, response_text: str) -> Dict:
        """LLMレスポンスをパースしてDict化

        Args:
            response_text: LLMからのレスポンステキスト

        Returns:
            パースされた判定結果
        """
        try:
            # JSON部分を抽出（コードブロック内の場合）
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            else:
                json_text = response_text.strip()

            # JSON パース
            result = json.loads(json_text)

            # 必須フィールドの検証
            required_fields = ["is_sensitive", "confidence", "reason", "recommended_action"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            # デフォルト値の設定
            if "false_positive" not in result:
                result["false_positive"] = False
            if "context_analysis" not in result:
                result["context_analysis"] = result.get("reason", "")

            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response text: {response_text}")

            # パース失敗時は安全側に倒す
            return {
                "is_sensitive": True,
                "confidence": 0.5,
                "reason": f"LLMレスポンスのパース失敗: {str(e)}",
                "recommended_action": "warn",
                "false_positive": False,
                "context_analysis": "パースエラー"
            }

    def bulk_judge(
        self,
        texts: List[str],
        detected_words_list: List[List[str]]
    ) -> List[Dict]:
        """複数テキストをまとめて判定

        Args:
            texts: 判定対象テキストのリスト
            detected_words_list: 各テキストで検出されたNGワードのリスト

        Returns:
            判定結果のリスト
        """
        results = []
        for text, detected_words in zip(texts, detected_words_list):
            result = self.judge_with_context(text, detected_words)
            results.append(result)

        return results
