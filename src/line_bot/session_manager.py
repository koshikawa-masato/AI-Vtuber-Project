"""
User Session Manager

ユーザーセッション管理（キャラクター選択、会話履歴など）
"""

import logging
from typing import Optional, Dict, Literal
from datetime import datetime
from .models import UserSession

logger = logging.getLogger(__name__)

CharacterType = Literal["botan", "kasho", "yuri"]


class SessionManager:
    """セッション管理クラス（インメモリ版）

    Phase 6-4: ユーザーセッション管理
    将来的にはDBに保存する
    """

    def __init__(self):
        """初期化"""
        self.sessions: Dict[str, UserSession] = {}
        logger.info("SessionManager initialized (in-memory)")

    def get_session(self, user_id: str) -> UserSession:
        """ユーザーセッションを取得（存在しない場合は新規作成）

        Args:
            user_id: LINEユーザーID

        Returns:
            ユーザーセッション
        """
        if user_id not in self.sessions:
            # 新規セッション作成
            session = UserSession(
                user_id=user_id,
                selected_character=None,  # 未選択
                last_message_at=None
            )
            self.sessions[user_id] = session
            logger.info(f"Created new session for user: {user_id}")

        return self.sessions[user_id]

    def set_character(self, user_id: str, character: CharacterType) -> None:
        """ユーザーの選択キャラクターを設定

        Args:
            user_id: LINEユーザーID
            character: 選択されたキャラクター（botan, kasho, yuri）
        """
        session = self.get_session(user_id)
        old_character = session.selected_character
        session.selected_character = character

        if old_character != character:
            logger.info(f"User {user_id} changed character: {old_character} -> {character}")
        else:
            logger.info(f"User {user_id} selected character: {character}")

    def get_character(self, user_id: str) -> Optional[CharacterType]:
        """ユーザーの選択キャラクターを取得

        Args:
            user_id: LINEユーザーID

        Returns:
            選択されたキャラクター（未選択の場合はNone）
        """
        session = self.get_session(user_id)
        return session.selected_character

    def get_character_or_default(self, user_id: str, default: CharacterType = "botan") -> CharacterType:
        """ユーザーの選択キャラクターを取得（未選択の場合はデフォルト）

        Args:
            user_id: LINEユーザーID
            default: デフォルトキャラクター（デフォルト: botan）

        Returns:
            選択されたキャラクター、または default
        """
        character = self.get_character(user_id)
        if character is None:
            logger.info(f"User {user_id} has no character selected, using default: {default}")
            return default
        return character

    def update_last_message(self, user_id: str) -> None:
        """最終メッセージ時刻を更新

        Args:
            user_id: LINEユーザーID
        """
        session = self.get_session(user_id)
        session.last_message_at = int(datetime.now().timestamp() * 1000)

    def clear_session(self, user_id: str) -> None:
        """セッションをクリア

        Args:
            user_id: LINEユーザーID
        """
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"Cleared session for user: {user_id}")

    def get_all_sessions(self) -> Dict[str, UserSession]:
        """全セッションを取得（デバッグ用）

        Returns:
            全セッションの辞書
        """
        return self.sessions

    def session_count(self) -> int:
        """セッション数を取得

        Returns:
            セッション数
        """
        return len(self.sessions)


class SimpleMockSessionManager:
    """シンプルなモックセッションマネージャー（テスト用）"""

    def __init__(self):
        logger.info("SimpleMockSessionManager initialized")
        self.default_character: CharacterType = "botan"

    def get_session(self, user_id: str) -> UserSession:
        return UserSession(user_id=user_id, selected_character=self.default_character, last_message_at=None)

    def set_character(self, user_id: str, character: CharacterType) -> None:
        logger.info(f"[MOCK] User {user_id} selected character: {character}")
        self.default_character = character

    def get_character(self, user_id: str) -> Optional[CharacterType]:
        return self.default_character

    def get_character_or_default(self, user_id: str, default: CharacterType = "botan") -> CharacterType:
        return self.default_character

    def update_last_message(self, user_id: str) -> None:
        pass

    def clear_session(self, user_id: str) -> None:
        pass

    def get_all_sessions(self) -> Dict[str, UserSession]:
        return {}

    def session_count(self) -> int:
        return 0
