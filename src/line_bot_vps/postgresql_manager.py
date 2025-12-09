"""
PostgreSQL Database Manager (XServer VPS版)

VPS内のlocalhost PostgreSQLに直接接続
LINE Bot用シンプル版（暗号化なし、既存DBスキーマ対応）
"""

import psycopg2
import psycopg2.extras
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class PostgreSQLManager:
    """PostgreSQLデータベース管理クラス（既存DBスキーマ対応）"""

    def __init__(self):
        """初期化"""
        # PostgreSQL接続情報（環境変数から取得）
        self.pg_config = {
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'database': os.getenv('POSTGRES_DATABASE'),
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
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
            # 自動コミットを有効化（トランザクションエラー防止）
            self.connection.autocommit = True
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

    def _ensure_connection(self) -> bool:
        """接続を確認し、必要なら再接続"""
        try:
            if self.connection is None or self.connection.closed:
                return self.connect()
            # 接続テスト
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception:
            return self.connect()

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
        if not self._ensure_connection():
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
                    timestamp, character, user_id,
                    user_message, bot_response,
                    phase5_user_tier, phase5_response_tier, memories_used,
                    response_time, metadata
                ))
                log_id = cursor.fetchone()[0]
                logger.info(f"✅ 学習ログ保存: ID={log_id}, character={character}")
                return log_id

        except Exception as e:
            logger.error(f"学習ログ保存失敗: {e}")
            return None

    def get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ユーザーセッションを取得

        Returns:
            セッション情報（存在しない場合はNone）
        """
        if not self._ensure_connection():
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
        last_message_at: Optional[datetime] = None,
        language: Optional[str] = None
    ) -> bool:
        """ユーザーセッションを保存（INSERT or UPDATE）

        Args:
            user_id: ユーザーID
            selected_character: 選択されたキャラクター
            last_message_at: 最終メッセージ時刻
            language: 言語設定 ('ja' or 'en')

        Returns:
            成功したらTrue
        """
        if not self._ensure_connection():
            logger.error("PostgreSQL未接続")
            return False

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO sessions (
                        user_id, selected_character,
                        last_message_at, language, updated_at
                    ) VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        selected_character = COALESCE(EXCLUDED.selected_character, sessions.selected_character),
                        last_message_at = COALESCE(EXCLUDED.last_message_at, sessions.last_message_at),
                        language = COALESCE(EXCLUDED.language, sessions.language),
                        updated_at = NOW()
                """
                cursor.execute(sql, (
                    user_id, selected_character,
                    last_message_at or datetime.now(), language
                ))
                logger.info(f"✅ セッション保存: user_id={user_id[:8]}..., character={selected_character}, language={language}")
                return True

        except Exception as e:
            logger.error(f"セッション保存失敗: {e}")
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
        if not self._ensure_connection():
            logger.error("PostgreSQL未接続")
            return None

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO conversation_history (
                        user_id, character, role, message
                    ) VALUES (%s, %s, %s, %s)
                    RETURNING id
                """
                cursor.execute(sql, (user_id, character, role, message))
                history_id = cursor.fetchone()[0]
                logger.debug(f"会話履歴保存: ID={history_id}, role={role}")
                return history_id

        except Exception as e:
            logger.error(f"会話履歴保存失敗: {e}")
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
        if not self._ensure_connection():
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

                # 古い順に並べ替えて返す
                history = []
                for row in reversed(results):
                    row_dict = dict(row)
                    history.append({
                        'role': row_dict['role'],
                        'message': row_dict['message'],
                        'created_at': row_dict.get('created_at')
                    })

                return history

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
        """
        if not self._ensure_connection():
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

                # JSON文字列をパース
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
        if not self._ensure_connection():
            logger.error("PostgreSQL未接続")
            return None

        try:
            # feedbackテーブルがあるか確認し、なければlearning_logsに記録
            with self.connection.cursor() as cursor:
                # learning_logsにフィードバックとして記録
                sql = """
                    INSERT INTO learning_logs (
                        timestamp, character, user_id, user_message, bot_response
                    ) VALUES (NOW(), 'feedback', %s, %s, 'フィードバック受信')
                    RETURNING id
                """
                cursor.execute(sql, (user_id, feedback_text))
                feedback_id = cursor.fetchone()[0]
                logger.info(f"✅ フィードバック保存: ID={feedback_id}")
                return feedback_id

        except Exception as e:
            logger.error(f"フィードバック保存失敗: {e}")
            return None

    def get_user_mode(self, user_id: str) -> str:
        """ユーザーの選択モードを取得

        Args:
            user_id: LINEユーザーID

        Returns:
            選択モード ('auto', 'botan', 'kasho', 'yuri')
            レコードがない場合は 'auto'
        """
        if not self._ensure_connection():
            logger.error("PostgreSQL未接続")
            return 'auto'

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                sql = "SELECT selected_mode FROM sessions WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()

                if result and result.get('selected_mode'):
                    return result['selected_mode']

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
        if not self._ensure_connection():
            logger.error("PostgreSQL未接続")
            return False

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO sessions (user_id, selected_mode, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        selected_mode = EXCLUDED.selected_mode,
                        updated_at = NOW()
                """
                cursor.execute(sql, (user_id, mode))
                logger.info(f"✅ モード設定: user_id={user_id[:8]}..., mode={mode}")
                return True

        except Exception as e:
            logger.error(f"モード設定失敗: {e}")
            return False

    def get_feedback_state(self, user_id: str) -> str:
        """フィードバック状態を取得

        Args:
            user_id: LINEユーザーID

        Returns:
            フィードバック状態 ('none', 'waiting')
        """
        if not self._ensure_connection():
            logger.error("PostgreSQL未接続")
            return 'none'

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                sql = "SELECT feedback_state FROM sessions WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()

                if result and result.get('feedback_state'):
                    return result['feedback_state']

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
        if not self._ensure_connection():
            logger.error("PostgreSQL未接続")
            return False

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO sessions (user_id, feedback_state, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        feedback_state = EXCLUDED.feedback_state,
                        updated_at = NOW()
                """
                cursor.execute(sql, (user_id, state))
                logger.debug(f"フィードバック状態設定: {state}")
                return True

        except Exception as e:
            logger.error(f"フィードバック状態設定失敗: {e}")
            return False

    def get_user_language(self, user_id: str) -> str:
        """ユーザーの言語設定を取得

        Args:
            user_id: LINEユーザーID

        Returns:
            言語コード ('ja' or 'en')
        """
        if not self._ensure_connection():
            return 'ja'

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                sql = "SELECT language FROM sessions WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()

                if result and result.get('language'):
                    return result['language']

                return 'ja'

        except Exception as e:
            logger.error(f"言語設定取得失敗: {e}")
            return 'ja'

    def set_user_language(self, user_id: str, language: str) -> bool:
        """ユーザーの言語設定を変更

        Args:
            user_id: LINEユーザーID
            language: 言語コード ('ja' or 'en')

        Returns:
            成功したらTrue
        """
        if not self._ensure_connection():
            return False

        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO sessions (user_id, language, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        language = EXCLUDED.language,
                        updated_at = NOW()
                """
                cursor.execute(sql, (user_id, language))
                logger.info(f"✅ 言語設定: user_id={user_id[:8]}..., language={language}")
                return True

        except Exception as e:
            logger.error(f"言語設定失敗: {e}")
            return False
