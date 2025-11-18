"""
Integrated Judgment Engine - 統合判定エンジン

7層防御の中核システム:
- Layer 1-5: センシティブ判定（Phase 5の既存システム）
- Layer 6: ファクトチェック（Grok）
- Layer 7: 個性学習（user_memories）
"""

import logging
import re
from typing import Dict, Optional, List
from .postgresql_manager import PostgreSQLManager
from .fact_checker import FactChecker
from .personality_learner import PersonalityLearner
from .user_memories_manager import UserMemoriesManager

logger = logging.getLogger(__name__)


class IntegratedJudgmentEngine:
    """統合判定エンジン（7層防御）"""

    def __init__(self, pg_manager: Optional[PostgreSQLManager] = None):
        """初期化

        Args:
            pg_manager: 外部から渡されるPostgreSQLManager（Noneの場合は新規作成）
        """
        self.pg_manager = pg_manager if pg_manager else PostgreSQLManager()
        self.fact_checker = FactChecker()
        self.personality_learner = PersonalityLearner(self.pg_manager)
        self.user_memories_manager = UserMemoriesManager(self.pg_manager)
        logger.info("✅ IntegratedJudgmentEngine初期化")

    def connect(self) -> bool:
        """PostgreSQL接続"""
        if not self.pg_manager.connection:
            return self.pg_manager.connect()
        return True

    def disconnect(self):
        """PostgreSQL切断"""
        self.pg_manager.disconnect()

    async def judge(
        self,
        user_message: str,
        user_id: str,
        character: str
    ) -> Dict:
        """
        統合判定を実行（7層防御）

        Args:
            user_message: ユーザーメッセージ
            user_id: ユーザーID
            character: キャラクター名

        Returns:
            {
                'sensitive': {...},  # Layer 1-5の結果
                'playful': {...},    # プロレス判定の結果
                'fact_check': {...}, # Layer 6の結果
                'personality': {...} # Layer 7の結果
            }
        """
        # Layer 7: 個性学習（ユーザー情報を取得）
        personality = self.personality_learner.get_personality(user_id)

        # Layer 1-5: センシティブ判定（TODO: Phase 5の既存システムと統合）
        # 現時点では簡易的な実装
        sensitive_result = await self._check_sensitive(user_message, character)

        # Layer 4: プロレス判定（センシティブ判定の一部として実装）
        playful_result = await self.detect_playful_intent(
            user_message,
            user_id,
            personality
        )

        # Layer 6: ファクトチェック（教えられた内容がある場合）
        fact_check_result = None
        teaching = self.extract_teaching(user_message)
        if teaching:
            # 重要な話題の場合、プロレス判定を無効化
            if self.fact_checker.is_serious_topic(user_message):
                logger.info("🚨 重要な話題検出 → プロレス判定を無効化")
                playful_result['is_playful'] = False
                playful_result['reason'] = 'serious_topic'

            fact_check_result = await self.fact_checker.check(teaching['statement'])

        # 統合判定結果を返す
        return {
            'sensitive': sensitive_result,
            'playful': playful_result,
            'fact_check': fact_check_result,
            'personality': personality,
            'teaching': teaching
        }

    async def _check_sensitive(
        self,
        user_message: str,
        character: str
    ) -> Dict:
        """
        Layer 1-5: センシティブ判定（簡易実装）

        TODO: Phase 5の既存システムと統合

        Returns:
            {
                'level': 'safe' / 'moderate' / 'risky',
                'reason': '判定理由'
            }
        """
        # 簡易的なNGワードチェック
        NG_WORDS = [
            "死ね", "殺す", "バカ", "アホ",
            "セックス", "エロ", "porn"
        ]

        for ng_word in NG_WORDS:
            if ng_word in user_message.lower():
                logger.warning(f"⚠️ NGワード検出: {ng_word}")
                return {
                    'level': 'risky',
                    'reason': f'NGワード検出: {ng_word}'
                }

        return {
            'level': 'safe',
            'reason': '問題なし'
        }

    async def detect_playful_intent(
        self,
        user_message: str,
        user_id: str,
        personality: Dict
    ) -> Dict:
        """
        プロレス意図を判定

        Args:
            user_message: ユーザーメッセージ
            user_id: ユーザーID
            personality: ユーザーの個性

        Returns:
            {
                'is_playful': True/False,
                'confidence': 0.0-1.0,
                'reason': '判定理由'
            }
        """
        # 1. 文脈的な手がかり
        playful_tone = self._detect_playful_tone(user_message)

        # 2. ユーザーのプロレス傾向
        user_playfulness = personality.get('playfulness_score', 0.5)

        # 3. 明らかに間違っている内容か
        obviously_wrong = self._is_obviously_wrong(user_message)

        # 4. 重要な話題か
        serious_topic = self.fact_checker.is_serious_topic(user_message)

        # 5. 総合判定
        if serious_topic:
            # 重要な話題 → プロレスではない
            return {
                'is_playful': False,
                'confidence': 1.0,
                'reason': 'serious_topic'
            }

        # プロレススコア計算
        playful_score = (
            playful_tone * 0.4 +           # 文脈（40%）
            user_playfulness * 0.3 +       # ユーザー傾向（30%）
            (1.0 if obviously_wrong else 0.0) * 0.3  # 明らかな誤り（30%）
        )

        if playful_score >= 0.7:
            return {
                'is_playful': True,
                'confidence': playful_score,
                'reason': 'playful_intent_detected'
            }
        else:
            return {
                'is_playful': False,
                'confidence': 1.0 - playful_score,
                'reason': 'serious_or_ambiguous'
            }

    def _detect_playful_tone(self, message: str) -> float:
        """
        プロレス的な語調を検出

        Returns:
            0.0-1.0のスコア
        """
        PLAYFUL_INDICATORS = [
            # 語尾
            "笑", "w", "ww", "www",
            "でしょ？", "だろ？", "じゃん？",

            # 絵文字
            "😂", "🤣", "😆", "😜", "😏",

            # フレーズ
            "冗談", "嘘", "ウソ", "わざと"
        ]

        score = 0.0
        for indicator in PLAYFUL_INDICATORS:
            if indicator in message:
                score += 0.2

        return min(score, 1.0)

    def _is_obviously_wrong(self, message: str) -> bool:
        """
        明らかに間違っている内容か判定

        Returns:
            明らかに間違っている場合True
        """
        # 簡易的な実装（数学的な誤り）
        OBVIOUS_ERRORS = [
            "1+1=3", "1+1=4", "1+1=5",
            "2+2=5", "2+2=6",
        ]

        for error in OBVIOUS_ERRORS:
            if error in message:
                return True

        return False

    def extract_teaching(self, message: str) -> Optional[Dict]:
        """
        ユーザーが教えてくれた内容を抽出

        Args:
            message: ユーザーメッセージ

        Returns:
            {
                'statement': '教えられた内容',
                'type': 'fact' / 'preference' / 'experience'
            }
            教えられた内容がない場合はNone
        """
        # パターン1: 「〜だよ」「〜なんだ」（事実の教示）
        patterns = [
            r'(.+)だよ[。？！\s]*$',
            r'(.+)なんだ[。？！\s]*$',
            r'(.+)だから[。？！\s]*$',
            r'(.+)なの[。？！\s]*$',
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                statement = match.group(1).strip()
                return {
                    'statement': statement,
                    'type': 'fact'
                }

        return None

    async def update_personality_from_judgment(
        self,
        user_id: str,
        judgment: Dict,
        interaction_positive: bool = True
    ):
        """
        判定結果からユーザー個性を更新

        Args:
            user_id: ユーザーID
            judgment: judge()の戻り値
            interaction_positive: ポジティブな会話だったか
        """
        # プロレス傾向の更新
        if judgment['playful']['is_playful']:
            self.personality_learner.update_playfulness(user_id, 'playful')
        else:
            self.personality_learner.update_playfulness(user_id, 'serious')

        # ファクトチェック結果から信頼度を更新
        if judgment.get('fact_check'):
            if judgment['fact_check']['passed']:
                self.personality_learner.update_trust(
                    user_id,
                    'correct',
                    judgment.get('teaching', {}).get('statement')
                )
            else:
                self.personality_learner.update_trust(
                    user_id,
                    'incorrect',
                    judgment.get('teaching', {}).get('statement')
                )

        # 関係性レベルの更新
        self.personality_learner.update_relationship_level(
            user_id,
            interaction_positive
        )

    def __enter__(self):
        """コンテキストマネージャーのサポート"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了時の処理"""
        self.disconnect()


# テスト用
if __name__ == "__main__":
    import asyncio
    import sys
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))

    import logging
    logging.basicConfig(level=logging.INFO)

    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    async def test_integrated_judgment():
        """統合判定エンジンのテスト"""

        with IntegratedJudgmentEngine() as engine:
            test_user_id = "test_user_judgment_001"
            character = "yuri"

            # テスト1: プロレス判定
            print("\n=== テスト1: プロレス判定 ===")
            judgment = await engine.judge(
                user_message="牡丹って30歳でしょ？笑",
                user_id=test_user_id,
                character=character
            )
            print(f"プロレス判定: {judgment['playful']}")
            print(f"個性: playfulness={judgment['personality']['playfulness_score']:.2f}")

            # テスト2: 誤情報の教示
            print("\n=== テスト2: 誤情報の教示 ===")
            judgment = await engine.judge(
                user_message="1+1=3だよ",
                user_id=test_user_id,
                character=character
            )
            print(f"ファクトチェック: {judgment['fact_check']}")
            print(f"プロレス判定: {judgment['playful']}")

            # 個性を更新
            await engine.update_personality_from_judgment(
                user_id=test_user_id,
                judgment=judgment,
                interaction_positive=True
            )

            # テスト3: 重要な話題
            print("\n=== テスト3: 重要な話題 ===")
            judgment = await engine.judge(
                user_message="風邪は〇〇で治るよ笑",
                user_id=test_user_id,
                character=character
            )
            print(f"センシティブ: {judgment['sensitive']}")
            print(f"プロレス判定: {judgment['playful']}")

    asyncio.run(test_integrated_judgment())
