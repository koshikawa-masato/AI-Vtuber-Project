"""
VPS用 FastAPI Webhook サーバー

- クラウドLLM（gpt-4o-mini）使用
- copy_robot_memory.db使用
- 学習ログ保存機能
- 30秒タイムアウト対応
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import hmac
import hashlib
import logging
from datetime import datetime
import os
import json
import time
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

from .cloud_llm_provider import CloudLLMProvider
from .learning_log_system import LearningLogSystem
from .session_manager import SessionManager

# 既存のモジュールを活用
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.prompt_manager import PromptManager

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPIアプリ作成
app = FastAPI(
    title="牡丹プロジェクト VPS LINE Bot API",
    description="VPS用 クラウドLLM + 学習ログシステム",
    version="0.1.0"
)

# ========================================
# 設定
# ========================================

# LINE Channel Secret（環境変数から取得）
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
    logger.warning("⚠️ LINE認証情報が設定されていません")

# クラウドLLM初期化（環境変数から設定取得）
VPS_LLM_PROVIDER = os.getenv("VPS_LLM_PROVIDER", "openai")
VPS_LLM_MODEL = os.getenv("VPS_LLM_MODEL", "gpt-4o-mini")

llm_provider = CloudLLMProvider(
    provider=VPS_LLM_PROVIDER,
    model=VPS_LLM_MODEL,
    temperature=0.7,
    max_tokens=500
)
logger.info(f"✅ CloudLLMProvider初期化完了（{VPS_LLM_PROVIDER}: {VPS_LLM_MODEL}）")

# 学習ログシステム初期化
learning_log_system = LearningLogSystem(
    db_path=os.getenv("LEARNING_LOG_DB_PATH", "./learning_logs.db")
)
logger.info("✅ LearningLogSystem初期化完了")

# セッション管理システム初期化
session_manager = SessionManager()
logger.info("✅ SessionManager初期化完了")

# プロンプト管理システム初期化
prompt_manager = PromptManager()
logger.info("✅ PromptManager初期化完了")

# キャラクター設定
CHARACTERS = {
    "kasho": {
        "name": "Kasho",
        "display_name": "花生（Kasho）",
        "age": 19
    },
    "botan": {
        "name": "牡丹",
        "display_name": "牡丹（Botan）",
        "age": 17
    },
    "yuri": {
        "name": "ユリ",
        "display_name": "百合（Yuri）",
        "age": 15
    }
}

# ========================================
# ヘルパー関数
# ========================================

def verify_signature(body: bytes, signature: str) -> bool:
    """
    LINE署名検証

    Args:
        body: リクエストボディ
        signature: X-Line-Signature

    Returns:
        検証結果
    """
    hash_digest = hmac.new(
        CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()

    expected_signature = hashlib.sha256(hash_digest).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


def generate_response(
    character: str,
    user_message: str,
    user_id: str
) -> tuple[str, float]:
    """
    応答生成

    Args:
        character: キャラクター名
        user_message: ユーザーメッセージ
        user_id: ユーザーID

    Returns:
        (応答テキスト, 処理時間)
    """
    start_time = time.time()

    try:
        # プロンプト取得（世界観ルール + キャラクタープロンプト）
        character_prompt = prompt_manager.get_combined_prompt(character)

        # TODO: Phase D記憶検索統合（copy_robot_memory.dbから）
        memories = None  # 将来的に実装

        # LLM生成
        response = llm_provider.generate_with_context(
            user_message=user_message,
            character_name=CHARACTERS[character]["name"],
            character_prompt=character_prompt,
            memories=memories,
            metadata={
                "user_id": user_id,
                "character": character,
                "platform": "LINE_VPS"
            }
        )

        elapsed_time = time.time() - start_time

        logger.info(f"✅ 応答生成完了: {elapsed_time:.2f}秒")

        return response, elapsed_time

    except Exception as e:
        logger.error(f"❌ 応答生成エラー: {e}")
        elapsed_time = time.time() - start_time
        return "ごめんね、ちょっと調子が悪いみたい...また後で話そう？", elapsed_time


# ========================================
# エンドポイント
# ========================================

@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "service": "VPS LINE Bot",
        "version": "0.1.0",
        "llm": "gpt-4o-mini"
    }


@app.get("/api/stats")
async def get_stats():
    """学習ログ統計情報取得"""
    try:
        stats = learning_log_system.get_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"❌ 統計情報取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning-logs")
async def get_learning_logs(
    since: Optional[str] = None,
    character: Optional[str] = None,
    limit: int = 100
):
    """
    学習ログ取得（開発者用API）

    Args:
        since: この日時以降のログを取得（ISO format）
        character: 特定のキャラクターのみ取得
        limit: 最大取得件数
    """
    try:
        logs = learning_log_system.get_logs(
            since=since,
            character=character,
            limit=limit
        )
        return JSONResponse(content={"logs": logs, "count": len(logs)})
    except Exception as e:
        logger.error(f"❌ 学習ログ取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook")
async def webhook(request: Request):
    """
    LINE Webhook エンドポイント（単一・キャラクター選択対応）
    """
    # リクエストボディ取得
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    # 署名検証（本番環境のみ）
    if CHANNEL_SECRET and not verify_signature(body, signature):
        logger.warning("⚠️ 署名検証失敗")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # JSON解析
    try:
        webhook_data = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # イベント処理
    events = webhook_data.get("events", [])

    for event in events:
        event_type = event.get("type")
        user_id = event.get("source", {}).get("userId", "unknown")
        reply_token = event.get("replyToken")

        # Postbackイベント処理（キャラクター選択）
        if event_type == "postback":
            postback_data = event.get("postback", {}).get("data", "")
            logger.info(f"📲 Postback受信: {postback_data}")

            # キャラクター選択処理
            if postback_data.startswith("character="):
                character = postback_data.split("=")[1]
                if character in CHARACTERS:
                    session_manager.set_character(user_id, character)

                    # 確認メッセージを返信
                    reply_message = f"✨ {CHARACTERS[character]['display_name']}を選択したよ！何でも聞いてね！"

                    try:
                        import requests
                        reply_url = "https://api.line.me/v2/bot/message/reply"
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                        }
                        payload = {
                            "replyToken": reply_token,
                            "messages": [{"type": "text", "text": reply_message}]
                        }
                        response = requests.post(reply_url, headers=headers, json=payload)

                        if response.status_code == 200:
                            logger.info(f"✅ キャラクター選択返信成功: {character}")
                        else:
                            logger.error(f"❌ 返信エラー: {response.status_code}")
                    except Exception as e:
                        logger.error(f"❌ LINE API呼び出しエラー: {e}")

        # メッセージイベント処理
        elif event_type == "message":
            message_type = event.get("message", {}).get("type")

            if message_type == "text":
                # テキストメッセージ処理
                user_message = event.get("message", {}).get("text", "")

                # SessionManagerからキャラクターを取得（デフォルト: 牡丹）
                character = session_manager.get_character_or_default(user_id, default="botan")

                logger.info(f"📩 メッセージ受信: {character} <- {user_message[:30]}...")

                # TODO: Phase 5センシティブ判定（軽量版）
                # 現在は省略、将来的に実装

                # 応答生成
                bot_response, response_time = generate_response(
                    character=character,
                    user_message=user_message,
                    user_id=user_id
                )

                # 学習ログ保存
                try:
                    learning_log_system.save_log(
                        character=character,
                        user_id=hashlib.sha256(user_id.encode()).hexdigest()[:16],  # ハッシュ化
                        user_message=user_message,
                        bot_response=bot_response,
                        phase5_user_tier="Safe",  # TODO: 実装後に実際の判定結果
                        phase5_response_tier="Safe",
                        memories_used=None,  # TODO: Phase D実装後
                        response_time=response_time,
                        metadata={
                            "platform": "LINE_VPS",
                            "event_type": event_type,
                            "character": character
                        }
                    )
                except Exception as e:
                    logger.error(f"❌ 学習ログ保存エラー: {e}")

                # 最終メッセージ時刻を更新
                session_manager.update_last_message_time(user_id)

                # LINE返信
                try:
                    import requests

                    reply_url = "https://api.line.me/v2/bot/message/reply"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                    }
                    payload = {
                        "replyToken": reply_token,
                        "messages": [
                            {
                                "type": "text",
                                "text": bot_response
                            }
                        ]
                    }

                    response = requests.post(reply_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        logger.info(f"✅ LINE返信成功: {character} -> {bot_response[:30]}...")
                    else:
                        logger.error(f"❌ LINE返信エラー: {response.status_code} - {response.text}")

                except Exception as e:
                    logger.error(f"❌ LINE API呼び出しエラー: {e}")

    return JSONResponse(content={"status": "ok"})


# ========================================
# 起動時ログ
# ========================================

@app.on_event("startup")
async def startup_event():
    """起動時処理"""
    logger.info("=" * 60)
    logger.info("🚀 VPS LINE Bot起動")
    logger.info(f"   LLM: gpt-4o-mini")
    logger.info(f"   学習ログDB: {learning_log_system.db_path}")
    logger.info(f"   キャラクター: {', '.join(CHARACTERS.keys())}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """終了時処理"""
    logger.info("👋 VPS LINE Bot終了")


# ========================================
# メイン実行
# ========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
