"""
Integrated Sensitive Detector

4層防御システムを統合したセンシティブ判定システム

設計思想:
- Layer 1（静的パターン）: 高速・高精度で既知のNGワードを検出
- Layer 2（未知ワード抽出）: Layer 3へのフィルタリング
- Layer 3（WebSearch）: 補助的な検出、DB拡充が主目的
- Layer 4（LLM判定）: 最終防壁として文脈を考慮した高精度判定
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

from src.line_bot.sensitive_handler import SensitiveHandler
from src.line_bot.llm_context_judge import LLMContextJudge
from src.core.llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class IntegratedSensitiveDetector:
    """4層防御統合センシティブ検出システム

    Layer 1（静的パターン） → Layer 4（LLM判定）の順で判定を行い、
    最終的にLayer 4で文脈を考慮した結果を返す

    Note: Layer 2, 3（未知ワード抽出、WebSearch）は現在Layer 1に統合済み
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        enable_layer4: bool = True
    ):
        """初期化

        Args:
            llm_provider: LLMプロバイダー（Layer 4用）
            enable_layer4: Layer 4（LLM判定）を有効化するか
        """
        # Layer 1: 静的パターンマッチング
        self.static_handler = SensitiveHandler()

        # Layer 4: LLM文脈判定
        self.enable_layer4 = enable_layer4
        if enable_layer4:
            self.llm_judge = LLMContextJudge(llm_provider)
        else:
            self.llm_judge = None

        logger.info(
            f"IntegratedSensitiveDetector initialized: layer4={enable_layer4}"
        )

    def detect(self, text: str, use_layer4: bool = True) -> Dict:
        """統合センシティブ判定

        Layer 1 → Layer 4 の順で判定を行う
        （Layer 2, 3は現在Layer 1に統合されている）

        Args:
            text: 判定対象テキスト
            use_layer4: Layer 4（LLM判定）を使用するか

        Returns:
            {
                "is_sensitive": bool,
                "tier": str,  # "Safe", "Warning", "Critical"
                "confidence": float,
                "detected_words": List[str],
                "detection_layers": List[str],  # 検出したLayer
                "layer1_result": Dict,  # Layer 1の生結果
                "layer4_result": Dict or None,  # Layer 4の結果
                "recommended_action": str,  # "allow", "warn", "block"
                "reason": str,
                "final_judgment": str  # 最終判定の根拠
            }
        """
        logger.info(f"Integrated detection start: text_length={len(text)}, use_layer4={use_layer4}")

        detection_layers = []

        # ===== Layer 1: 静的パターンマッチング =====
        layer1_result = self.static_handler.check(text)
        detected_words = layer1_result.get("matched_patterns", [])

        if detected_words:
            detection_layers.append("layer1")
            logger.info(f"Layer 1 detected: {detected_words}")

        # ===== Layer 4: LLM文脈判定（最終防壁） =====
        layer4_result = None
        final_tier = layer1_result["tier"]
        final_confidence = layer1_result.get("risk_score", 0.5)

        # recommendation を recommended_action に変換
        layer1_recommendation = layer1_result.get("recommendation", "allow")
        if layer1_recommendation == "block_immediate":
            recommended_action = "block"
        elif layer1_recommendation == "review_required":
            recommended_action = "warn"
        else:
            recommended_action = "allow"

        reason = layer1_result.get("reasoning", "")
        final_judgment = "Layer 1のみ（静的パターンマッチング）"

        if use_layer4 and self.enable_layer4 and self.llm_judge and detected_words:
            # Layer 1で何か検出された場合のみLayer 4を実行
            detection_layers.append("layer4")

            try:
                layer4_result = self.llm_judge.judge_with_context(
                    text=text,
                    detected_words=detected_words,
                    detection_method="static_pattern"
                )

                # Layer 4の判定を最終結果として採用
                if layer4_result["false_positive"]:
                    # 誤検知と判定された場合
                    final_tier = "Safe"
                    final_confidence = layer4_result["confidence"]
                    recommended_action = "allow"
                    reason = f"Layer 4で誤検知と判定: {layer4_result['reason']}"
                    final_judgment = "Layer 4（LLM文脈判定）が誤検知を補正"
                else:
                    # センシティブと判定された場合
                    final_confidence = layer4_result["confidence"]
                    recommended_action = layer4_result["recommended_action"]
                    reason = layer4_result["reason"]
                    final_judgment = "Layer 4（LLM文脈判定）で確定"

                    # 推奨アクションからTierを決定
                    if recommended_action == "block":
                        final_tier = "Critical"
                    elif recommended_action == "warn":
                        final_tier = "Warning"
                    else:
                        final_tier = "Safe"

                logger.info(f"Layer 4 judgment: is_sensitive={layer4_result['is_sensitive']}, "
                           f"false_positive={layer4_result['false_positive']}")

            except Exception as e:
                logger.error(f"Layer 4 judgment failed: {e}")
                # Layer 4失敗時はLayer 1の結果を採用
                final_judgment = f"Layer 4失敗、Layer 1の結果を採用: {str(e)}"

        # 最終結果
        is_sensitive = final_tier in ["Warning", "Critical"]

        result = {
            "is_sensitive": is_sensitive,
            "tier": final_tier,
            "confidence": final_confidence,
            "detected_words": detected_words,
            "detection_layers": detection_layers,
            "layer1_result": layer1_result,
            "layer4_result": layer4_result,
            "recommended_action": recommended_action,
            "reason": reason,
            "final_judgment": final_judgment
        }

        logger.info(f"Final result: tier={final_tier}, action={recommended_action}, "
                   f"layers={detection_layers}")

        return result

    def detect_batch(self, texts: List[str], use_layer4: bool = True) -> List[Dict]:
        """バッチ判定

        複数のテキストをまとめて判定

        Args:
            texts: 判定対象テキストのリスト
            use_layer4: Layer 4を使用するか

        Returns:
            判定結果のリスト
        """
        results = []
        for text in texts:
            result = self.detect(text, use_layer4=use_layer4)
            results.append(result)

        return results

    def get_statistics(self) -> Dict:
        """検出統計を取得

        Returns:
            {
                "layer1_patterns": int,  # Layer 1のNGパターン数
                "layer4_enabled": bool,
                "llm_provider": str or None,
                "llm_model": str or None
            }
        """
        stats = {
            "layer1_patterns": len(self.static_handler.ng_patterns),
            "layer4_enabled": self.enable_layer4,
            "llm_provider": self.llm_judge.llm_provider.get_provider_name() if self.llm_judge else None,
            "llm_model": self.llm_judge.llm_provider.get_model_name() if self.llm_judge else None
        }

        return stats
