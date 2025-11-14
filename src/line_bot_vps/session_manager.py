"""
User Session Manager (VPS版)

ユーザーセッション管理（キャラクター選択、会話履歴など）
"""

import logging
from typing import Optional, Dict, Literal
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

CharacterType = Literal["botan", "kasho", "yuri"]


@dataclass
class UserSession:
    """ユーザーセッション"""
    user_id: str
    selected_character: Optional[CharacterType] = None
    last_message_at: Optional[datetime] = None
    conversation_history: list = field(default_factory=list)


class SessionManager:
    """セッション管理クラス（インメモリ版）

    VPS版: ユーザーセッション管理
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
            logger.info(f"Created new session for user: {user_id[:8]}...")

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
            logger.info(f"User {user_id[:8]}... changed character: {old_character} -> {character}")
        else:
            logger.info(f"User {user_id[:8]}... selected character: {character}")

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
            default: デフォルトキャラクター

        Returns:
            選択されたキャラクター
        """
        character = self.get_character(user_id)
        if character is None:
            logger.info(f"User {user_id[:8]}... has no character selected, using default: {default}")
            return default
        return character

    def update_last_message_time(self, user_id: str) -> None:
        """最終メッセージ時刻を更新

        Args:
            user_id: LINEユーザーID
        """
        session = self.get_session(user_id)
        session.last_message_at = datetime.now()

    def clear_session(self, user_id: str) -> None:
        """セッションをクリア

        Args:
            user_id: LINEユーザーID
        """
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"Cleared session for user: {user_id[:8]}...")

    def get_session_count(self) -> int:
        """セッション数を取得

        Returns:
            現在のセッション数
        """
        return len(self.sessions)
