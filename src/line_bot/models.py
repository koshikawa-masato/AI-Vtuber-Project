"""
LINE Messaging API のデータモデル

LINE Webhookリクエスト/レスポンスのPydanticモデル定義
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ========================================
# LINE Webhook リクエストモデル
# ========================================

class Source(BaseModel):
    """メッセージ送信元"""
    type: Literal["user", "group", "room"]
    userId: Optional[str] = None
    groupId: Optional[str] = None
    roomId: Optional[str] = None


class Message(BaseModel):
    """メッセージ本体"""
    id: str
    type: Literal["text", "image", "video", "audio", "file", "location", "sticker"]
    text: Optional[str] = None  # type="text"の場合
    # その他のメッセージタイプのフィールドは必要に応じて追加


class Postback(BaseModel):
    """Postbackデータ"""
    data: str
    params: Optional[dict] = None


class Event(BaseModel):
    """Webhookイベント"""
    type: Literal["message", "follow", "unfollow", "join", "leave", "postback", "beacon"]
    timestamp: int
    source: Source
    replyToken: Optional[str] = None
    message: Optional[Message] = None  # type="message"の場合
    postback: Optional[Postback] = None  # type="postback"の場合


class WebhookRequest(BaseModel):
    """LINE Webhook リクエスト"""
    destination: str
    events: List[Event]


# ========================================
# LINE Messaging API レスポンスモデル
# ========================================

class TextMessage(BaseModel):
    """テキストメッセージ"""
    type: Literal["text"] = "text"
    text: str


class ReplyRequest(BaseModel):
    """返信リクエスト"""
    replyToken: str
    messages: List[TextMessage]


# ========================================
# 内部データモデル
# ========================================

class UserSession(BaseModel):
    """ユーザーセッション"""
    user_id: str
    selected_character: Optional[Literal["botan", "kasho", "yuri"]] = None
    last_message_at: Optional[int] = None


class BotResponse(BaseModel):
    """Bot応答（内部処理用）"""
    character: Literal["botan", "kasho", "yuri"]
    message: str
    sensitive_tier: Optional[Literal["Safe", "Warning", "Critical"]] = None
