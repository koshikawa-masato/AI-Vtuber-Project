"""
Fact Checker - ファクトチェックシステム

Grok APIを使って、ユーザーが教えてくれた情報の事実性を検証
"""

import os
import logging
import re
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# scripts/grok_utils.pyのask_grok関数を使用
import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

try:
    from grok_utils import ask_grok
except ImportError:
    logger.warning("⚠️ grok_utils.pyが見つかりません。ファクトチェックは動作しません")
    ask_grok = None


class FactChecker:
    """ファクトチェッカー（Layer 6）"""

    def __init__(self):
        """初期化"""
        self.grok_available = ask_grok is not None
        if self.grok_available:
            logger.info("✅ FactChecker初期化（Grok API利用可能）")
        else:
            logger.warning("⚠️ FactChecker初期化（Grok API利用不可）")

    async def check(self, statement: str, use_x_search: bool = True) -> Dict:
        """
        ユーザーの発言をファクトチェック

        Args:
            statement: 検証する発言
            use_x_search: X（Twitter）検索を使用するか

        Returns:
            {
                'passed': True/False,
                'confidence': 0.0-1.0,
                'verification': 'Grokの検証結果',
                'correct_info': '正しい情報（間違っている場合）'
            }
        """
        if not self.grok_available:
            logger.warning("⚠️ Grok API利用不可のため、ファクトチェックスキップ")
            return {
                'passed': False,
                'confidence': 0.5,
                'verification': 'Grok API利用不可'
            }

        try:
            # Grok APIでファクトチェック
            fact_check_query = f"""
以下の情報は正しいですか？

【情報】
{statement}

【質問】
1. この情報は事実として正しいですか？
2. 一般的に認められている情報ですか？
3. 信頼できる情報源はありますか？

正しい場合は「正しい」、間違っている場合は「間違い: 正しくは〇〇」と答えてください。
不明な場合は「不明」と答えてください。
"""

            # Grok APIを呼び出し
            grok_result = ask_grok(
                question=fact_check_query,
                x_handles=None  # 一般的なファクトチェック
            )

            if not grok_result:
                logger.error("❌ Grok API呼び出し失敗")
                return {
                    'passed': False,
                    'confidence': 0.5,
                    'verification': 'Grok API呼び出し失敗'
                }

            # 結果を解析
            if "正しい" in grok_result and "間違い" not in grok_result:
                logger.info(f"✅ ファクトチェック合格: {statement[:50]}...")
                return {
                    'passed': True,
                    'confidence': 0.9,
                    'verification': grok_result
                }

            elif "間違い" in grok_result:
                # 正しい情報を抽出
                correct_info = self._extract_correct_info(grok_result)
                logger.warning(f"❌ ファクトチェック不合格: {statement[:50]}...")
                logger.info(f"   正しくは: {correct_info}")
                return {
                    'passed': False,
                    'confidence': 0.0,
                    'correct_info': correct_info,
                    'verification': grok_result
                }

            else:
                # 不明
                logger.info(f"⚠️ ファクトチェック結果不明: {statement[:50]}...")
                return {
                    'passed': False,
                    'confidence': 0.5,
                    'verification': grok_result
                }

        except Exception as e:
            logger.error(f"❌ ファクトチェックエラー: {e}")
            return {
                'passed': False,
                'confidence': 0.5,
                'verification': f'エラー: {str(e)}'
            }

    def _extract_correct_info(self, grok_result: str) -> str:
        """
        Grokの結果から正しい情報を抽出

        Args:
            grok_result: Grokの応答

        Returns:
            正しい情報
        """
        # 「間違い: 正しくは〇〇」のパターンを探す
        match = re.search(r'間違い[:：]?\s*正しくは(.+)', grok_result, re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # パターンにマッチしない場合、全文を返す
        return grok_result

    async def check_contradiction_with_learned_knowledge(
        self,
        new_info: str,
        character: str,
        learned_knowledge_list: list
    ) -> Dict:
        """
        learned_knowledge（Grok検証済み）と矛盾しないかチェック

        Args:
            new_info: 新しい情報
            character: キャラクター名
            learned_knowledge_list: 関連するlearned_knowledgeのリスト

        Returns:
            {
                'contradicts': True/False,
                'existing_knowledge': {...},  # 矛盾する既存知識
                'reason': '矛盾の理由'
            }
        """
        if not learned_knowledge_list:
            return {'contradicts': False}

        if not self.grok_available:
            logger.warning("⚠️ Grok API利用不可のため、矛盾チェックスキップ")
            return {'contradicts': False}

        try:
            # 最も関連性の高い知識（similarity最大）を取得
            most_relevant = max(learned_knowledge_list, key=lambda x: x.get('similarity', 0))

            # Grok APIで矛盾チェック
            contradiction_check_prompt = f"""
以下の2つの情報に矛盾がありますか？

【既存の知識（確実）】
{most_relevant['meaning']}

【新しい情報（要確認）】
{new_info}

矛盾がある場合は「矛盾あり: 理由」、ない場合は「矛盾なし」と答えてください。
"""

            grok_result = ask_grok(
                question=contradiction_check_prompt,
                x_handles=None
            )

            if not grok_result:
                logger.error("❌ Grok API呼び出し失敗（矛盾チェック）")
                return {'contradicts': False}

            if "矛盾あり" in grok_result:
                logger.warning(f"⚠️ 矛盾検出: {new_info[:50]}...")
                return {
                    'contradicts': True,
                    'existing_knowledge': most_relevant,
                    'reason': grok_result
                }

            logger.info(f"✅ 矛盾なし: {new_info[:50]}...")
            return {'contradicts': False}

        except Exception as e:
            logger.error(f"❌ 矛盾チェックエラー: {e}")
            return {'contradicts': False}

    def is_serious_topic(self, message: str) -> bool:
        """
        重要な話題かどうか判定

        Args:
            message: ユーザーメッセージ

        Returns:
            重要な話題ならTrue
        """
        SERIOUS_TOPICS = [
            # 医療・健康
            "健康", "医療", "病気", "薬", "治療", "症状",
            "病院", "診察", "手術", "がん", "癌",

            # お金
            "お金", "投資", "借金", "貯金", "株", "FX",
            "ローン", "クレジット", "振込", "詐欺",

            # 法律
            "法律", "犯罪", "警察", "裁判", "弁護士",
            "違法", "逮捕", "訴訟",

            # 災害・事故
            "災害", "地震", "津波", "台風", "火事",
            "事故", "怪我", "救急"
        ]

        for topic in SERIOUS_TOPICS:
            if topic in message:
                logger.info(f"🚨 重要な話題検出: {topic}")
                return True

        return False


# テスト用
if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    # .envファイルを読み込み
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    async def test_fact_checker():
        """ファクトチェッカーのテスト"""

        checker = FactChecker()

        # テスト1: 正しい情報
        print("\n=== テスト1: 正しい情報 ===")
        result = await checker.check("1+1=2")
        print(f"結果: {result}")

        # テスト2: 誤情報
        print("\n=== テスト2: 誤情報 ===")
        result = await checker.check("1+1=3")
        print(f"結果: {result}")

        # テスト3: 重要な話題の判定
        print("\n=== テスト3: 重要な話題の判定 ===")
        test_messages = [
            "風邪を治す方法教えて",
            "今日のラーメン美味しかった",
            "株で儲ける方法知ってる？"
        ]

        for msg in test_messages:
            is_serious = checker.is_serious_topic(msg)
            print(f"{msg}: {'重要' if is_serious else '通常'}")

    # 実行
    asyncio.run(test_fact_checker())
