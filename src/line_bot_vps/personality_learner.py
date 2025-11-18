"""
Personality Learner - 個性学習システム（Layer 7）

ユーザーの個性（プロレス傾向、信頼度、関係性レベル）を学習
"""

import logging
from typing import Optional, Dict
from .postgresql_manager import PostgreSQLManager

logger = logging.getLogger(__name__)


class PersonalityLearner:
    """個性学習システム（Layer 7）"""

    def __init__(self, pg_manager: Optional[PostgreSQLManager] = None):
        """初期化

        Args:
            pg_manager: 外部から渡されるPostgreSQLManager（Noneの場合は新規作成）
        """
        self.pg_manager = pg_manager if pg_manager else PostgreSQLManager()
        logger.info("✅ PersonalityLearner初期化")

    def connect(self) -> bool:
        """PostgreSQL接続"""
        if not self.pg_manager.connection:
            return self.pg_manager.connect()
        return True

    def disconnect(self):
        """PostgreSQL切断"""
        self.pg_manager.disconnect()

    def get_personality(self, user_id: str) -> Dict:
        """
        ユーザーの個性を取得

        Args:
            user_id: ユーザーID

        Returns:
            {
                'playfulness_score': 0.5,
                'trust_score': 0.5,
                'relationship_level': 1,
                'total_conversations': 0,
                ...
            }
        """
        if not self.pg_manager.connection:
            logger.error("PostgreSQL未接続")
            return self._get_default_personality()

        try:
            with self.pg_manager.connection.cursor() as cursor:
                sql = "SELECT * FROM user_personality WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()

                if not result:
                    # 初回ユーザー → デフォルト値を返す
                    logger.info(f"新規ユーザー: {user_id[:8]}... (デフォルト個性を返す)")
                    return self._get_default_personality()

                # 結果を辞書に変換
                columns = [desc[0] for desc in cursor.description]
                personality = dict(zip(columns, result))

                logger.debug(f"個性取得: user_id={user_id[:8]}..., playfulness={personality['playfulness_score']:.2f}, trust={personality['trust_score']:.2f}")
                return personality

        except Exception as e:
            logger.error(f"❌ 個性取得失敗: {e}")
            return self._get_default_personality()

    def _get_default_personality(self) -> Dict:
        """デフォルトの個性を返す（初回ユーザー用）"""
        return {
            'playfulness_score': 0.5,
            'trust_score': 0.5,
            'relationship_level': 1,
            'total_conversations': 0,
            'positive_interactions': 0,
            'playful_interactions': 0,
            'serious_interactions': 0,
            'correct_teachings': 0,
            'incorrect_teachings': 0,
            'risky_statement_count': 0,
            'moderate_statement_count': 0,
            'prefers_playful_response': False,
            'prefers_serious_response': False,
            'common_topics': [],
            'serious_topics_misused': []
        }

    def update_playfulness(
        self,
        user_id: str,
        interaction_type: str
    ) -> bool:
        """
        プロレス傾向を更新

        Args:
            user_id: ユーザーID
            interaction_type: 'playful' or 'serious'

        Returns:
            成功したらTrue
        """
        if not self.pg_manager.connection:
            logger.error("PostgreSQL未接続")
            return False

        try:
            with self.pg_manager.connection.cursor() as cursor:
                # ユーザーが存在するか確認
                cursor.execute("SELECT user_id FROM user_personality WHERE user_id = %s", (user_id,))
                exists = cursor.fetchone() is not None

                if not exists:
                    # 新規ユーザー → INSERT
                    cursor.execute("""
                        INSERT INTO user_personality (user_id)
                        VALUES (%s)
                    """, (user_id,))

                # プロレス/真面目カウントを更新
                if interaction_type == 'playful':
                    cursor.execute("""
                        UPDATE user_personality
                        SET playful_interactions = playful_interactions + 1,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))
                else:
                    cursor.execute("""
                        UPDATE user_personality
                        SET serious_interactions = serious_interactions + 1,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))

                # playfulness_scoreを再計算
                playfulness_score = self.calculate_playfulness_score(user_id)
                cursor.execute("""
                    UPDATE user_personality
                    SET playfulness_score = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (playfulness_score, user_id))

                self.pg_manager.connection.commit()
                logger.info(f"✅ プロレス傾向更新: user_id={user_id[:8]}..., type={interaction_type}, score={playfulness_score:.2f}")
                return True

        except Exception as e:
            logger.error(f"❌ プロレス傾向更新失敗: {e}")
            self.pg_manager.connection.rollback()
            return False

    def calculate_playfulness_score(self, user_id: str) -> float:
        """
        ユーザーのプロレス傾向を計算

        Args:
            user_id: ユーザーID

        Returns:
            プロレス傾向スコア（0.0〜1.0）
        """
        if not self.pg_manager.connection:
            logger.error("PostgreSQL未接続")
            return 0.5

        try:
            with self.pg_manager.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT playful_interactions, serious_interactions
                    FROM user_personality
                    WHERE user_id = %s
                """, (user_id,))

                result = cursor.fetchone()

                if not result:
                    return 0.5  # デフォルト（中立）

                playful_interactions, serious_interactions = result
                total_interactions = playful_interactions + serious_interactions

                if total_interactions == 0:
                    return 0.5  # デフォルト

                playfulness_score = playful_interactions / total_interactions
                return playfulness_score

        except Exception as e:
            logger.error(f"❌ プロレス傾向計算失敗: {e}")
            return 0.5

    def update_trust(
        self,
        user_id: str,
        teaching_result: str,
        statement: Optional[str] = None
    ) -> bool:
        """
        信頼度を更新

        Args:
            user_id: ユーザーID
            teaching_result: 'correct' or 'incorrect'
            statement: 発言内容（履歴記録用）

        Returns:
            成功したらTrue
        """
        if not self.pg_manager.connection:
            logger.error("PostgreSQL未接続")
            return False

        try:
            with self.pg_manager.connection.cursor() as cursor:
                # 現在の信頼度を取得
                cursor.execute("SELECT trust_score FROM user_personality WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()

                trust_score_before = result[0] if result else 0.5

                # ユーザーが存在するか確認
                if not result:
                    # 新規ユーザー → INSERT
                    cursor.execute("""
                        INSERT INTO user_personality (user_id)
                        VALUES (%s)
                    """, (user_id,))
                    trust_score_before = 0.5

                # 正解/誤りカウントを更新
                if teaching_result == 'correct':
                    cursor.execute("""
                        UPDATE user_personality
                        SET correct_teachings = correct_teachings + 1,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))
                else:
                    cursor.execute("""
                        UPDATE user_personality
                        SET incorrect_teachings = incorrect_teachings + 1,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))

                # trust_scoreを再計算
                trust_score = self.calculate_trust_score(user_id)
                cursor.execute("""
                    UPDATE user_personality
                    SET trust_score = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (trust_score, user_id))

                # 信頼度履歴を記録
                delta = trust_score - trust_score_before
                event_type = 'correct_teaching' if teaching_result == 'correct' else 'incorrect_teaching'

                cursor.execute("""
                    INSERT INTO user_trust_history (
                        user_id, event_type, trust_score_before, trust_score_after,
                        delta, statement
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, event_type, trust_score_before, trust_score, delta, statement))

                self.pg_manager.connection.commit()
                logger.info(f"✅ 信頼度更新: user_id={user_id[:8]}..., result={teaching_result}, score={trust_score:.2f} (Δ{delta:+.2f})")
                return True

        except Exception as e:
            logger.error(f"❌ 信頼度更新失敗: {e}")
            self.pg_manager.connection.rollback()
            return False

    def calculate_trust_score(self, user_id: str) -> float:
        """
        ユーザーの信頼度を計算

        Args:
            user_id: ユーザーID

        Returns:
            信頼度スコア（0.0〜1.0）
        """
        if not self.pg_manager.connection:
            logger.error("PostgreSQL未接続")
            return 0.5

        try:
            with self.pg_manager.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT correct_teachings, incorrect_teachings
                    FROM user_personality
                    WHERE user_id = %s
                """, (user_id,))

                result = cursor.fetchone()

                if not result:
                    return 0.5  # デフォルト（中立）

                correct_teachings, incorrect_teachings = result
                total_teachings = correct_teachings + incorrect_teachings

                if total_teachings == 0:
                    return 0.5  # デフォルト

                trust_score = correct_teachings / total_teachings
                return trust_score

        except Exception as e:
            logger.error(f"❌ 信頼度計算失敗: {e}")
            return 0.5

    def update_relationship_level(
        self,
        user_id: str,
        interaction_positive: bool = True
    ) -> bool:
        """
        関係性レベルを更新

        Args:
            user_id: ユーザーID
            interaction_positive: ポジティブな会話だったか

        Returns:
            成功したらTrue
        """
        if not self.pg_manager.connection:
            logger.error("PostgreSQL未接続")
            return False

        try:
            with self.pg_manager.connection.cursor() as cursor:
                # ユーザーが存在するか確認
                cursor.execute("SELECT user_id FROM user_personality WHERE user_id = %s", (user_id,))
                exists = cursor.fetchone() is not None

                if not exists:
                    # 新規ユーザー → INSERT
                    cursor.execute("""
                        INSERT INTO user_personality (user_id)
                        VALUES (%s)
                    """, (user_id,))

                # 会話カウントを更新
                if interaction_positive:
                    cursor.execute("""
                        UPDATE user_personality
                        SET total_conversations = total_conversations + 1,
                            positive_interactions = positive_interactions + 1,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))
                else:
                    cursor.execute("""
                        UPDATE user_personality
                        SET total_conversations = total_conversations + 1,
                            updated_at = NOW()
                        WHERE user_id = %s
                    """, (user_id,))

                # relationship_levelを再計算
                relationship_level = self.calculate_relationship_level(user_id)
                cursor.execute("""
                    UPDATE user_personality
                    SET relationship_level = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (relationship_level, user_id))

                self.pg_manager.connection.commit()
                logger.info(f"✅ 関係性レベル更新: user_id={user_id[:8]}..., level={relationship_level}")
                return True

        except Exception as e:
            logger.error(f"❌ 関係性レベル更新失敗: {e}")
            self.pg_manager.connection.rollback()
            return False

    def calculate_relationship_level(self, user_id: str) -> int:
        """
        関係性レベルを計算（1〜10）

        Args:
            user_id: ユーザーID

        Returns:
            関係性レベル（1〜10）
        """
        if not self.pg_manager.connection:
            logger.error("PostgreSQL未接続")
            return 1

        try:
            with self.pg_manager.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT total_conversations, positive_interactions
                    FROM user_personality
                    WHERE user_id = %s
                """, (user_id,))

                result = cursor.fetchone()

                if not result:
                    return 1  # デフォルト（初対面）

                total_conversations, positive_interactions = result

                if total_conversations == 0:
                    return 1

                # 会話回数ベース（最大5）
                base_level = min(total_conversations / 10, 5)

                # ポジティブ度ベース（最大5）
                positive_ratio = positive_interactions / total_conversations
                bonus_level = positive_ratio * 5

                relationship_level = int(base_level + bonus_level)

                # 1〜10の範囲に収める
                return max(1, min(relationship_level, 10))

        except Exception as e:
            logger.error(f"❌ 関係性レベル計算失敗: {e}")
            return 1

    def __enter__(self):
        """コンテキストマネージャーのサポート"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了時の処理"""
        self.disconnect()


# テスト用
if __name__ == "__main__":
    import sys
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))

    import logging
    logging.basicConfig(level=logging.INFO)

    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    def test_personality_learner():
        """PersonalityLearnerのテスト"""

        with PersonalityLearner() as learner:
            test_user_id = "test_user_personality_001"

            print("\n=== テスト1: 初期状態の取得 ===")
            personality = learner.get_personality(test_user_id)
            print(f"playfulness_score: {personality['playfulness_score']}")
            print(f"trust_score: {personality['trust_score']}")
            print(f"relationship_level: {personality['relationship_level']}")

            print("\n=== テスト2: プロレス傾向の更新 ===")
            for i in range(5):
                learner.update_playfulness(test_user_id, 'playful')

            for i in range(2):
                learner.update_playfulness(test_user_id, 'serious')

            personality = learner.get_personality(test_user_id)
            print(f"playfulness_score: {personality['playfulness_score']:.2f} (期待: 0.71)")

            print("\n=== テスト3: 信頼度の更新 ===")
            learner.update_trust(test_user_id, 'correct', "1+1=2")
            learner.update_trust(test_user_id, 'correct', "地球は丸い")
            learner.update_trust(test_user_id, 'incorrect', "1+1=3")

            personality = learner.get_personality(test_user_id)
            print(f"trust_score: {personality['trust_score']:.2f} (期待: 0.67)")

            print("\n=== テスト4: 関係性レベルの更新 ===")
            for i in range(15):
                learner.update_relationship_level(test_user_id, interaction_positive=True)

            personality = learner.get_personality(test_user_id)
            print(f"relationship_level: {personality['relationship_level']} (期待: 6-7)")

    test_personality_learner()
