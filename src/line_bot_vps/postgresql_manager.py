"""
PostgreSQL Database Manager (XServer VPS版)

VPS内のlocalhost PostgreSQLに直接接続
"""

import psycopg2
import psycopg2.extras
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class PostgreSQLManager:
    """PostgreSQLデータベース管理クラス（localhost接続）"""

    def __init__(self):
        """初期化"""
        # PostgreSQL接続情報（環境変数から取得）
        # セキュリティ: すべての接続情報を環境変数から取得（デフォルト値なし）
        self.pg_config = {
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'database': os.getenv('POSTGRES_DATABASE'),
            'host': os.getenv('POSTGRES_HOST', 'localhost'),  # localhostのみデフォルト許可
            'port': int(os.getenv('POSTGRES_PORT', '5432')),  # 標準ポートのみデフォルト許可
        }

        self.connection = None
        logger.info("PostgreSQLManager initialized")

    def connect(self) -> bool:
        """PostgreSQLに接続

        Returns:
            成功したらTrue
        """
        try:
            self.connection = psycopg2.connect(
                host=self.pg_config['host'],
                port=self.pg_config['port'],
                user=self.pg_config['user'],
                password=self.pg_config['password'],
                database=self.pg_config['database'],
                connect_timeout=10
            )
            # 自動コミットを無効化（明示的にcommit/rollbackを行う）
            self.connection.autocommit = False
            logger.info("✅ PostgreSQL接続成功")
            return True

        except Exception as e:
            logger.error(f"PostgreSQL接続失敗: {e}")
            return False

    def disconnect(self):
        """接続を切断"""
        if self.connection:
            self.connection.close()
            logger.info("PostgreSQL接続を切断")

    def save_learning_log(
        self,
        timestamp: str,
        character: str,
        user_id: str,
        user_message: str,
        bot_response: str,
        phase5_user_tier: Optional[str] = None,
        phase5_response_tier: Optional[str] = None,
        memories_used: Optional[str] = None,
        response_time: Optional[float] = None,
        metadata: Optional[str] = None
    ) -> Optional[int]:
        """学習ログを保存

        Returns:
            挿入されたレコードのID（失敗時はNone）
        """
        if not self.connection:
            logger.error("PostgreSQL未接続")
            return None

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO learning_logs (
                        timestamp, character, user_id, user_message, bot_response,
                        phase5_user_tier, phase5_response_tier, memories_used,
                        response_time, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                """
                cursor.execute(sql, (
                    timestamp, character, user_id, user_message, bot_response,
                    phase5_user_tier, phase5_response_tier, memories_used,
                    response_time, metadata
                ))
                log_id = cursor.fetchone()[0]
                self.connection.commit()
                logger.info(f"✅ 学習ログ保存: ID={log_id}, character={character}")
                return log_id

        except Exception as e:
            logger.error(f"学習ログ保存失敗: {e}")
            self.connection.rollback()
            return None

    def get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ユーザーセッションを取得

        Returns:
            セッション情報（存在しない場合はNone）
        """
        if not self.connection:
            logger.error("PostgreSQL未接続")
            return None

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                sql = "SELECT * FROM sessions WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()
                return dict(result) if result else None

        except Exception as e:
            logger.error(f"セッション取得失敗: {e}")
            return None

    def save_session(
        self,
        user_id: str,
        selected_character: Optional[str] = None,
        last_message_at: Optional[datetime] = None
    ) -> bool:
        """ユーザーセッションを保存（INSERT or UPDATE）

        Returns:
            成功したらTrue
        """
        if not self.connection:
            logger.error("PostgreSQL未接続")
            return False

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO sessions (user_id, selected_character, last_message_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        selected_character = EXCLUDED.selected_character,
                        last_message_at = EXCLUDED.last_message_at
                """
                cursor.execute(sql, (user_id, selected_character, last_message_at))
                self.connection.commit()
                logger.info(f"✅ セッション保存: user_id={user_id[:8]}..., character={selected_character}")
                return True

        except Exception as e:
            logger.error(f"セッション保存失敗: {e}")
            self.connection.rollback()
            return False

    def save_conversation_history(
        self,
        user_id: str,
        character: str,
        role: str,  # 'user' or 'assistant'
        message: str
    ) -> Optional[int]:
        """会話履歴を保存

        Returns:
            挿入されたレコードのID（失敗時はNone）
        """
        if not self.connection:
            logger.error("PostgreSQL未接続")
            return None

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO conversation_history (user_id, character, role, message)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """
                cursor.execute(sql, (user_id, character, role, message))
                history_id = cursor.fetchone()[0]
                self.connection.commit()
                logger.debug(f"会話履歴保存: ID={history_id}, role={role}")
                return history_id

        except Exception as e:
            logger.error(f"会話履歴保存失敗: {e}")
            self.connection.rollback()
            return None

    def get_conversation_history(
        self,
        user_id: str,
        character: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """会話履歴を取得（最新から指定件数）

        Returns:
            会話履歴のリスト（古い順）
        """
        if not self.connection:
            logger.error("PostgreSQL未接続")
            return []

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                sql = """
                    SELECT role, message, created_at
                    FROM conversation_history
                    WHERE user_id = %s AND character = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(sql, (user_id, character, limit))
                results = cursor.fetchall()
                # 古い順に並び替え
                return [dict(row) for row in reversed(results)]

        except Exception as e:
            logger.error(f"会話履歴取得失敗: {e}")
            return []

    def __enter__(self):
        """コンテキストマネージャー（with文）のサポート"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了時の処理"""
        self.disconnect()

    def get_recent_trends(
        self,
        character: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """最新のトレンド情報を取得（daily_trendsテーブル）

        Args:
            character: 'botan', 'kasho', 'yuri', 'parent'
            limit: 取得件数（デフォルト: 3）

        Returns:
            トレンド情報のリスト（新しい順）
            各要素は {topic, content (JSON), created_at} を含む
        """
        if not self.connection:
            logger.error("PostgreSQL未接続")
            return []

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                sql = """
                    SELECT topic, content, created_at
                    FROM daily_trends
                    WHERE character = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(sql, (character, limit))
                results = cursor.fetchall()

                # JSON文字列をパース（PostgreSQLはJSON型をサポートしているため、必要に応じて）
                trends = []
                for result in results:
                    trend = dict(result)
                    if isinstance(trend.get('content'), str):
                        try:
                            import json
                            trend['content'] = json.loads(trend['content'])
                        except json.JSONDecodeError:
                            logger.warning(f"JSON parse failed for content: {trend.get('content', '')[:50]}...")
                    trends.append(trend)

                logger.debug(f"トレンド情報取得: character={character}, count={len(trends)}")
                return trends

        except Exception as e:
            logger.error(f"トレンド情報取得失敗: {e}")
            return []

    def save_feedback(
        self,
        user_id: str,
        feedback_text: str
    ) -> Optional[int]:
        """フィードバックを保存

        Args:
            user_id: LINEユーザーID
            feedback_text: フィードバック内容

        Returns:
            挿入されたレコードのID（失敗時はNone）
        """
        if not self.connection:
            logger.error("PostgreSQL未接続")
            return None

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO feedback (user_id, feedback_text)
                    VALUES (%s, %s)
                    RETURNING id
                """
                cursor.execute(sql, (user_id, feedback_text))
                feedback_id = cursor.fetchone()[0]
                self.connection.commit()
                logger.info(f"✅ フィードバック保存: ID={feedback_id}")
                return feedback_id

        except Exception as e:
            logger.error(f"フィードバック保存失敗: {e}")
            self.connection.rollback()
            return None

    def get_user_mode(self, user_id: str) -> str:
        """ユーザーの選択モードを取得

        Args:
            user_id: LINEユーザーID

        Returns:
            選択モード ('auto', 'botan', 'kasho', 'yuri')
            レコードがない場合は 'auto'
        """
        if not self.connection:
            logger.error("PostgreSQL未接続")
            return 'auto'

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                sql = "SELECT selected_mode FROM sessions WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()

                if result and result['selected_mode']:
                    return result['selected_mode']
                else:
                    return 'auto'

        except Exception as e:
            logger.error(f"モード取得失敗: {e}")
            return 'auto'

    def set_user_mode(self, user_id: str, mode: str) -> bool:
        """ユーザーの選択モードを設定

        Args:
            user_id: LINEユーザーID
            mode: 選択モード ('auto', 'botan', 'kasho', 'yuri')

        Returns:
            成功したらTrue
        """
        if not self.connection:
            logger.error("PostgreSQL未接続")
            return False

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO sessions (user_id, selected_mode)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        selected_mode = EXCLUDED.selected_mode
                """
                cursor.execute(sql, (user_id, mode))
                self.connection.commit()
                logger.info(f"✅ モード設定: user_id={user_id[:8]}..., mode={mode}")
                return True

        except Exception as e:
            logger.error(f"モード設定失敗: {e}")
            self.connection.rollback()
            return False

    def get_feedback_state(self, user_id: str) -> str:
        """フィードバック状態を取得

        Args:
            user_id: LINEユーザーID

        Returns:
            フィードバック状態 ('none', 'waiting')
        """
        if not self.connection:
            logger.error("PostgreSQL未接続")
            return 'none'

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                sql = "SELECT feedback_state FROM sessions WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()

                if result and result['feedback_state']:
                    return result['feedback_state']
                else:
                    return 'none'

        except Exception as e:
            logger.error(f"フィードバック状態取得失敗: {e}")
            return 'none'

    def set_feedback_state(self, user_id: str, state: str) -> bool:
        """フィードバック状態を設定

        Args:
            user_id: LINEユーザーID
            state: フィードバック状態 ('none', 'waiting')

        Returns:
            成功したらTrue
        """
        if not self.connection:
            logger.error("PostgreSQL未接続")
            return False

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO sessions (user_id, feedback_state)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        feedback_state = EXCLUDED.feedback_state
                """
                cursor.execute(sql, (user_id, state))
                self.connection.commit()
                logger.debug(f"フィードバック状態設定: {state}")
                return True

        except Exception as e:
            logger.error(f"フィードバック状態設定失敗: {e}")
            self.connection.rollback()
            return False
