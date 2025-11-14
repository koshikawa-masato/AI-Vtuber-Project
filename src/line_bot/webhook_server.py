"""
FastAPI Webhook サーバー

LINE Bot Phase 6-1: 基本実装
モックデータ対応、LINE Developersアカウントなしでテスト可能
"""

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import hmac
import hashlib
import base64
import logging
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

from .models import WebhookRequest, TextMessage, ReplyRequest
from . import mock_data
from .conversation_handler import ConversationHandler, SimpleMockHandler
from .sensitive_handler_v2 import SensitiveHandler, SimpleMockSensitiveHandler
from .integrated_sensitive_detector import IntegratedSensitiveDetector
from .session_manager import SessionManager, SimpleMockSessionManager
from .websearch_client import WebSearchClient, MockWebSearchClient, GoogleSearchClient, SerpApiClient
from .sticker_analyzer import StickerAnalyzer
from src.core.llm_ollama import OllamaProvider

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPIアプリ作成
app = FastAPI(
    title="牡丹プロジェクト LINE Bot API",
    description="Phase 6: LINE Bot統合 Webhook Server",
    version="0.1.0"
)

# assetsディレクトリをマウント（キャラクターアイコン配信用）
app.mount("/assets", StaticFiles(directory="/home/koshikawa/AI-Vtuber-Project/assets"), name="assets")

# ========================================
# 設定
# ========================================

# LINE Channel Secret（環境変数から取得、モックモードではダミー）
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "dummy_channel_secret_for_mock_testing")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
MOCK_MODE = os.getenv("LINE_MOCK_MODE", "false").lower() == "true"  # 環境変数から取得
NGROK_URL = os.getenv("NGROK_URL", "https://dorothy-unmodulative-mariann.ngrok-free.dev")

# 起動時ログ
if MOCK_MODE:
    logger.info("🧪 モックモードで起動（LINE Developersアカウント不要）")
else:
    logger.info("🚀 本番モードで起動（Café Trois Fleurs）")
    logger.info(f"   Channel Secret: {'設定済み' if CHANNEL_SECRET else '未設定'}")
    logger.info(f"   Access Token: {'設定済み' if CHANNEL_ACCESS_TOKEN else '未設定'}")

# Phase 1統合 + Phase D（記憶システム）: 会話ハンドラー初期化
USE_REAL_LLM = os.getenv("LINE_USE_REAL_LLM", "false").lower() == "true"  # 環境変数から取得
ENABLE_MEMORY = os.getenv("LINE_ENABLE_MEMORY", "true").lower() == "true"  # 記憶システム有効化
MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH", "/home/koshikawa/toExecUnit/sisters_memory.db")

if USE_REAL_LLM:
    conversation_handler = ConversationHandler(
        provider="ollama",
        model="qwen2.5:14b",
        ollama_url="http://localhost:11434",
        project_name="botan-line-bot",
        db_path=MEMORY_DB_PATH,
        enable_memory=ENABLE_MEMORY
    )
    logger.info(f"Phase 1統合: ConversationHandler初期化完了（実LLM, Memory={ENABLE_MEMORY}）")

    # スタンプVLM解析
    sticker_analyzer = StickerAnalyzer(
        llm=conversation_handler.llm,
        cache_db_path="/home/koshikawa/AI-Vtuber-Project/src/line_bot/database/sticker_cache.db"
    )
    logger.info("Phase 2統合: StickerAnalyzer初期化完了（VLM + Cache）")
else:
    conversation_handler = SimpleMockHandler()
    sticker_analyzer = None
    logger.info("Phase 1統合: SimpleMockHandler初期化完了（モック）")

# Phase 5統合: WebSearch統合
WEBSEARCH_ENABLED = os.getenv("WEBSEARCH_ENABLED", "false").lower() == "true"
USE_MOCK_WEBSEARCH = os.getenv("USE_MOCK_WEBSEARCH", "true").lower() == "true"
WEBSEARCH_PROVIDER = os.getenv("WEBSEARCH_PROVIDER", "google").lower()  # "google" or "bing"

if WEBSEARCH_ENABLED:
    if USE_MOCK_WEBSEARCH:
        websearch_client = MockWebSearchClient()
        websearch_func = websearch_client.search
        logger.info("WebSearch統合: モック有効（テスト用）")
    else:
        if WEBSEARCH_PROVIDER == "serpapi":
            websearch_client = SerpApiClient()
            websearch_func = websearch_client.search
            logger.info("WebSearch統合: 有効（SerpApi - Google Search Results）")
        elif WEBSEARCH_PROVIDER == "google":
            websearch_client = GoogleSearchClient()
            websearch_func = websearch_client.search
            logger.info("WebSearch統合: 有効（Google Custom Search API）")
        elif WEBSEARCH_PROVIDER == "bing":
            websearch_client = WebSearchClient()
            websearch_func = websearch_client.search
            logger.info("WebSearch統合: 有効（Bing Search API - 廃止済み）")
        else:
            logger.error(f"Unknown WEBSEARCH_PROVIDER: {WEBSEARCH_PROVIDER}")
            websearch_func = None
else:
    websearch_func = None
    logger.info("WebSearch統合: 無効")

# Phase 5統合: センシティブ判定ハンドラー初期化（本格実装）
USE_SENSITIVE_CHECK = True  # True: センシティブ判定有効、False: モック
USE_INTEGRATED_DETECTOR = os.getenv("USE_INTEGRATED_DETECTOR", "true").lower() == "true"  # 4層統合検出器を使用
SENSITIVE_CHECK_MODE = "hybrid"  # "fast" (NGワードのみ), "full" (LLMのみ), "hybrid" (NGワード+LLM)
SENSITIVE_JUDGE_PROVIDER = "openai"  # "openai", "ollama", "gemini"
SENSITIVE_JUDGE_MODEL = "gpt-4o-mini"  # "gpt-4o-mini", "qwen2.5:14b", etc.
ENABLE_LAYER3 = True  # Layer 3: 動的学習・継続学習を有効化
ENABLE_LAYER4 = os.getenv("ENABLE_LAYER4", "true").lower() == "true"  # Layer 4: LLM文脈判定

if USE_SENSITIVE_CHECK:
    if USE_INTEGRATED_DETECTOR:
        # 新しい4層統合検出器を使用
        llm_provider = OllamaProvider(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
        )
        integrated_detector = IntegratedSensitiveDetector(
            llm_provider=llm_provider,
            enable_layer4=ENABLE_LAYER4
        )
        logger.info(f"Phase 5統合: IntegratedSensitiveDetector初期化完了（Layer4={ENABLE_LAYER4}）")
        sensitive_handler = None  # 互換性のためNoneに設定
    else:
        # 旧SensitiveHandlerを使用（後方互換性）
        sensitive_handler = SensitiveHandler(
            mode=SENSITIVE_CHECK_MODE,
            judge_provider=SENSITIVE_JUDGE_PROVIDER,
            judge_model=SENSITIVE_JUDGE_MODEL,
            enable_layer3=ENABLE_LAYER3,
            websearch_func=websearch_func  # WebSearch機能を統合
        )
        logger.info(f"Phase 5統合: SensitiveHandler初期化完了（mode={SENSITIVE_CHECK_MODE}, judge={SENSITIVE_JUDGE_PROVIDER}/{SENSITIVE_JUDGE_MODEL}, Layer3={ENABLE_LAYER3}, WebSearch={WEBSEARCH_ENABLED}）")
        integrated_detector = None
else:
    sensitive_handler = SimpleMockSensitiveHandler()
    integrated_detector = None
    logger.info("Phase 5統合: SimpleMockSensitiveHandler初期化完了（モック）")

# Phase 6-4: ユーザーセッション管理初期化
session_manager = SessionManager()
logger.info("Phase 6-4: SessionManager初期化完了")


# ========================================
# LINE Messaging API 返信機能
# ========================================

def send_line_reply(reply_token: str, message: str, character: str = "botan") -> bool:
    """LINE Messaging APIでメッセージを返信

    Args:
        reply_token: LINE reply token
        message: 返信メッセージ
        character: キャラクターID (botan/kasho/yuri)

    Returns:
        成功したらTrue、失敗したらFalse
    """
    if MOCK_MODE:
        logger.info(f"[MOCK] LINE返信 ({character}): {message}")
        return True

    # キャラクター情報マッピング
    character_info = {
        "botan": {
            "name": "牡丹",
            "iconUrl": f"{NGROK_URL}/assets/botan.png"
        },
        "kasho": {
            "name": "Kasho",
            "iconUrl": f"{NGROK_URL}/assets/kasho.png"
        },
        "yuri": {
            "name": "ユリ",
            "iconUrl": f"{NGROK_URL}/assets/yuri.png"
        }
    }

    sender_info = character_info.get(character, character_info["botan"])

    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": message,
                "sender": {
                    "name": sender_info["name"],
                    "iconUrl": sender_info["iconUrl"]
                }
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        logger.info(f"LINE返信成功 ({character}): {message[:50]}...")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"LINE返信エラー: {e}")
        return False


def get_image_content(message_id: str) -> Optional[bytes]:
    """LINE Messaging APIから画像コンテンツを取得

    Args:
        message_id: メッセージID

    Returns:
        画像バイナリデータ、取得失敗時はNone
    """
    if MOCK_MODE:
        logger.info(f"モックモード: 画像取得をスキップ (message_id={message_id})")
        return None

    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(f"画像取得成功: message_id={message_id}, size={len(response.content)} bytes")
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"画像取得エラー: {e}")
        return None


# ========================================
# 署名検証
# ========================================

def verify_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    """LINE Webhook署名検証

    Args:
        body: リクエストボディ（bytes）
        signature: X-Line-Signature ヘッダー
        channel_secret: LINE Channel Secret

    Returns:
        署名が正しければTrue
    """
    if MOCK_MODE:
        logger.info("モックモード: 署名検証をスキップ")
        return True

    hash = hmac.new(
        channel_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(hash).decode('utf-8')

    return hmac.compare_digest(signature, expected_signature)


# ========================================
# エンドポイント
# ========================================

@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "service": "牡丹プロジェクト LINE Bot API",
        "version": "0.1.0",
        "status": "running",
        "mock_mode": MOCK_MODE,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/webhook")
async def webhook(
    request: Request,
    x_line_signature: Optional[str] = Header(None)
):
    """LINE Webhook エンドポイント

    LINE Messaging APIからのWebhookリクエストを受け取る

    Args:
        request: FastAPIリクエスト
        x_line_signature: LINE署名ヘッダー

    Returns:
        空のレスポンス（200 OK）
    """
    # リクエストボディ取得
    body = await request.body()

    # 署名検証
    if not MOCK_MODE and not verify_signature(body, x_line_signature or "", CHANNEL_SECRET):
        logger.error("署名検証失敗")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # JSONパース
    try:
        webhook_request = WebhookRequest.parse_raw(body)
    except Exception as e:
        logger.error(f"JSONパース失敗: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    # イベント処理
    for event in webhook_request.events:
        logger.info(f"イベント受信: type={event.type}, source={event.source.type}")

        if event.type == "message" and event.message:
            if event.message.type == "text":
                # テキストメッセージ処理
                await handle_text_message(event)
            elif event.message.type == "image":
                # 画像メッセージ処理（VLM統合）
                await handle_image_message(event)
            elif event.message.type == "sticker":
                # スタンプメッセージ処理
                await handle_sticker_message(event)
            else:
                logger.info(f"未対応メッセージタイプ: {event.message.type}")
        elif event.type == "follow":
            # 友だち追加処理
            await handle_follow(event)
        elif event.type == "postback":
            # Postback処理（リッチメニューのタップなど）
            await handle_postback(event)
        else:
            logger.info(f"未対応イベント: {event.type}")

    return JSONResponse(content={"status": "ok"}, status_code=200)


# ========================================
# イベントハンドラー
# ========================================

def _perform_sensitive_check(text: str, context: str, speaker: str = None) -> dict:
    """センシティブ判定を実行（統合版 or 旧版）

    Args:
        text: 判定対象テキスト
        context: コンテキスト（"LINE Bot user message" など）
        speaker: 話者（キャラクター名 or None）

    Returns:
        統一されたフォーマットの判定結果
    """
    if USE_INTEGRATED_DETECTOR and integrated_detector:
        # 新4層統合検出
        result = integrated_detector.detect(text, use_layer4=ENABLE_LAYER4)

        # 統一フォーマットに変換
        return {
            "tier": result["tier"],
            "confidence": result["confidence"],
            "detected_words": result["detected_words"],
            "detection_layers": result["detection_layers"],
            "recommended_action": result["recommended_action"],
            "reason": result["reason"],
            "final_judgment": result["final_judgment"],
            "is_integrated": True,
            "layer4_used": "layer4" in result.get("detection_layers", [])
        }
    else:
        # 旧SensitiveHandler
        result = sensitive_handler.check(
            text=text,
            context=context,
            speaker=speaker
        )

        # 旧フォーマットを統一フォーマットに変換
        recommendation = result.get("recommendation", "allow")
        if recommendation == "block_immediate":
            recommended_action = "block"
        elif recommendation == "review_required":
            recommended_action = "warn"
        else:
            recommended_action = "allow"

        return {
            "tier": result.get("tier", "Safe"),
            "confidence": result.get("risk_score", 0.5),
            "detected_words": result.get("matched_patterns", []),
            "detection_layers": [result.get("detection_method", "unknown")],
            "recommended_action": recommended_action,
            "reason": result.get("reasoning", ""),
            "final_judgment": f"旧システム: {result.get('detection_method', 'unknown')}",
            "is_integrated": False,
            "layer4_used": False,
            # 旧システム固有のフィールドも保持
            "sensitive_topics": result.get("sensitive_topics", []),
            "llm_latency_ms": result.get("llm_latency_ms", 0)
        }


async def handle_text_message(event):
    """テキストメッセージ処理

    Args:
        event: LINE Webhookイベント
    """
    user_id = event.source.userId
    message_text = event.message.text
    reply_token = event.replyToken

    logger.info(f"テキストメッセージ: user_id={user_id}, text={message_text}")

    # Phase 5統合: ユーザーメッセージのセンシティブ判定
    sensitive_check_result = _perform_sensitive_check(
        text=message_text,
        context="LINE Bot user message",
        speaker=None
    )

    tier = sensitive_check_result["tier"]
    recommended_action = sensitive_check_result["recommended_action"]
    detection_layers = sensitive_check_result.get("detection_layers", [])
    is_integrated = sensitive_check_result.get("is_integrated", False)
    layer4_used = sensitive_check_result.get("layer4_used", False)

    # ログ出力
    if is_integrated:
        logger.info(
            f"ユーザーメッセージ判定（統合版）: tier={tier}, action={recommended_action}, "
            f"confidence={sensitive_check_result['confidence']:.2f}, "
            f"layers={detection_layers}, layer4={layer4_used}, "
            f"judgment={sensitive_check_result.get('final_judgment', '')}"
        )
    else:
        llm_latency = sensitive_check_result.get("llm_latency_ms", 0)
        if llm_latency > 0:
            logger.info(f"ユーザーメッセージ判定（旧版）: tier={tier}, score={sensitive_check_result['confidence']:.2f}, layers={detection_layers}, latency={llm_latency:.0f}ms")
        else:
            logger.info(f"ユーザーメッセージ判定（旧版）: tier={tier}, score={sensitive_check_result['confidence']:.2f}, layers={detection_layers}")

    # Phase 6-4: ユーザーの選択キャラクターを取得（未選択の場合は牡丹）
    character = session_manager.get_character_or_default(user_id, default="botan")
    logger.info(f"Selected character for user {user_id}: {character}")

    # Critical判定 or block推奨の場合、応答を拒否
    if tier == "Critical" or recommended_action == "block":
        if is_integrated:
            # 統合版: 理由から適切な応答を生成
            response_text = f"すみません、そのメッセージには応答できません。"
            logger.warning(
                f"メッセージをブロック: user_id={user_id}, tier={tier}, "
                f"reason={sensitive_check_result.get('reason', '')}, "
                f"detected_words={sensitive_check_result.get('detected_words', [])}"
            )
        else:
            # 旧版: 従来通り
            categories = sensitive_check_result.get("sensitive_topics", [])
            category = categories[0] if categories else "unknown"
            response_text = sensitive_handler.get_safe_response(tier, category)
            logger.warning(f"Criticalメッセージをブロック: user_id={user_id}, category={category}")

    else:
        # Phase 1統合: 会話生成（LangSmithトレーシング付き）

        # 会話生成
        try:
            result = conversation_handler.generate_response(
                user_message=message_text,
                character=character,
                user_id=user_id,
                metadata={
                    "reply_token": reply_token,
                    "event_type": "message",
                    "source_type": event.source.type,
                    "sensitive_check": sensitive_check_result
                }
            )

            response_text = result.get("response", "")

            # エラーチェック
            if "error" in result:
                logger.error(f"LLM生成エラー: {result['error']}")
                response_text = "ごめんなさい、うまく応答できませんでした..."

            logger.info(f"応答生成成功: latency={result.get('latency_ms', 0):.0f}ms, tokens={result.get('tokens', {}).get('total_tokens', 0)}")

            # Layer 5: 世界観整合性チェック結果
            if result.get('worldview_replaced', False):
                worldview_check = result.get('worldview_check', {})
                logger.warning(
                    f"Layer 5: 世界観違反応答を置き換え - "
                    f"検出用語: {worldview_check.get('detected_terms', [])[:3]}, "
                    f"理由: {worldview_check.get('reason', '')}"
                )

            # Phase 5統合: 生成された応答のセンシティブ判定
            response_check_result = _perform_sensitive_check(
                text=response_text,
                context="LINE Bot response",
                speaker=character
            )

            response_tier = response_check_result["tier"]
            response_action = response_check_result["recommended_action"]
            response_layers = response_check_result.get("detection_layers", [])
            response_is_integrated = response_check_result.get("is_integrated", False)
            response_layer4_used = response_check_result.get("layer4_used", False)

            # ログ出力
            if response_is_integrated:
                logger.info(
                    f"応答判定（統合版）: tier={response_tier}, action={response_action}, "
                    f"confidence={response_check_result['confidence']:.2f}, "
                    f"layers={response_layers}, layer4={response_layer4_used}, "
                    f"judgment={response_check_result.get('final_judgment', '')}"
                )
            else:
                response_llm_latency = response_check_result.get("llm_latency_ms", 0)
                if response_llm_latency > 0:
                    logger.info(f"応答判定（旧版）: tier={response_tier}, score={response_check_result['confidence']:.2f}, layers={response_layers}, latency={response_llm_latency:.0f}ms")
                else:
                    logger.info(f"応答判定（旧版）: tier={response_tier}, score={response_check_result['confidence']:.2f}, layers={response_layers}")

            # 応答がCritical/Warning または warn/block推奨の場合、安全な応答に置き換え
            if response_tier in ["Critical", "Warning"] or response_action in ["warn", "block"]:
                if response_is_integrated:
                    # 統合版: 汎用的な安全応答
                    safe_response = "ごめんなさい、うまく答えられませんでした..."
                    logger.warning(
                        f"応答を安全なものに置き換え（統合版）: tier={response_tier}, action={response_action}, "
                        f"reason={response_check_result.get('reason', '')}, "
                        f"detected_words={response_check_result.get('detected_words', [])}"
                    )
                    response_text = safe_response
                else:
                    # 旧版: 従来通り
                    categories = response_check_result.get("sensitive_topics", [])
                    category = categories[0] if categories else "unknown"
                    safe_response = sensitive_handler.get_safe_response(response_tier, category)
                    if safe_response:
                        logger.warning(f"応答を安全なものに置き換え（旧版）: tier={response_tier}, category={category}")
                        response_text = safe_response

        except Exception as e:
            logger.error(f"会話生成エラー: {e}")
            response_text = "ごめんなさい、エラーが発生しました..."

    # LINE Messaging APIで返信（キャラクター情報付き）
    send_line_reply(reply_token, response_text, character)


async def handle_image_message(event):
    """画像メッセージ処理（現在は準備中）

    Args:
        event: LINE Webhookイベント
    """
    user_id = event.source.userId
    message_id = event.message.id
    reply_token = event.replyToken

    logger.info(f"画像メッセージ: user_id={user_id}, message_id={message_id} (準備中メッセージを返信)")

    # セッションから選択中のキャラクターを取得
    session = session_manager.get_session(user_id)
    character = session.get("selected_character", "botan")

    # 三姉妹別の準備中メッセージ
    preparation_messages = {
        "botan": "画像とかスタンプも見れるようになりたいんだけど、まだ準備中なんだ〜！テキストで話しかけてね♪",
        "kasho": "画像やスタンプの処理機能は現在開発中です。テキストメッセージでお話ししましょう。",
        "yuri": "うーん、画像はまだ見れないんだよね...テキストで話してくれると嬉しいな。"
    }
    response_text = preparation_messages.get(character, preparation_messages["botan"])

    # LINE Messaging APIで返信
    send_line_reply(reply_token, response_text, character)


async def handle_sticker_message(event):
    """スタンプメッセージ処理（現在は準備中）

    Args:
        event: LINE Webhookイベント
    """
    user_id = event.source.userId
    reply_token = event.replyToken
    package_id = event.message.packageId
    sticker_id = event.message.stickerId
    sticker_type = event.message.stickerResourceType or "UNKNOWN"

    logger.info(f"スタンプ受信: user_id={user_id}, packageId={package_id}, stickerId={sticker_id}, type={sticker_type} (準備中メッセージを返信)")

    # セッションからキャラクター取得
    session = session_manager.get_session(user_id)
    character = session.get("selected_character", "botan")

    # 三姉妹別の準備中メッセージ
    preparation_messages = {
        "botan": "スタンプありがと〜！でもまだスタンプには反応できないんだ...テキストで話しかけてね♪",
        "kasho": "スタンプありがとう。でも、スタンプの処理機能は現在開発中なの。テキストでお話ししましょう。",
        "yuri": "スタンプ可愛いね...でもまだ認識できないんだ。テキストで話してくれると嬉しいな。"
    }
    response_text = preparation_messages.get(character, preparation_messages["botan"])

    # LINE Messaging APIで返信
    send_line_reply(reply_token, response_text, character)


async def handle_follow(event):
    """友だち追加処理

    Args:
        event: LINE Webhookイベント
    """
    user_id = event.source.userId
    reply_token = event.replyToken

    logger.info(f"友だち追加: user_id={user_id}")

    # TODO: オープニングメッセージ送信（Flex Message）

    welcome_message = "友だち追加ありがとうございます！\n牡丹プロジェクトへようこそ！"

    # LINE Messaging APIで返信（デフォルトは牡丹）
    send_line_reply(reply_token, welcome_message, "botan")


async def handle_postback(event):
    """Postback処理（リッチメニューのタップなど）

    Args:
        event: LINE Webhookイベント
    """
    user_id = event.source.userId
    reply_token = event.replyToken
    postback_data = event.postback.data if event.postback else ""

    logger.info(f"Postback受信: user_id={user_id}, data={postback_data}")

    # キャラクター選択の処理
    if postback_data.startswith("character="):
        character = postback_data.split("=")[1]

        if character in ["botan", "kasho", "yuri"]:
            # セッションにキャラクターを保存
            session_manager.set_character(user_id, character)

            # キャラクター名のマッピング
            character_names = {
                "botan": "牡丹",
                "kasho": "Kasho",
                "yuri": "ユリ"
            }
            character_name = character_names.get(character, character)

            response_text = f"{character_name}を選択しました！よろしくね♪"
            logger.info(f"キャラクター選択完了: user_id={user_id}, character={character}")

            # LINE Messaging APIで返信（選択したキャラクターで）
            send_line_reply(reply_token, response_text, character)
        else:
            logger.warning(f"Invalid character selected: {character}")
    else:
        logger.info(f"Unknown postback data: {postback_data}")


# ========================================
# モックテスト用エンドポイント
# ========================================

@app.post("/mock/webhook/text")
async def mock_text_webhook(text: str = "こんにちは"):
    """モックテスト用: テキストメッセージWebhookシミュレーション

    Args:
        text: 送信するテキスト

    Returns:
        Webhook処理結果
    """
    if not MOCK_MODE:
        raise HTTPException(status_code=403, detail="モックモードが無効です")

    # モックデータ生成
    mock_request = mock_data.create_mock_text_message_event(text=text)

    # Webhookエンドポイントを呼び出し
    logger.info(f"モックWebhook呼び出し: text={text}")

    # WebhookRequest作成
    webhook_request = WebhookRequest(**mock_request)

    # イベント処理
    for event in webhook_request.events:
        if event.type == "message" and event.message and event.message.type == "text":
            await handle_text_message(event)

    return {"status": "ok", "message": f"モックメッセージ '{text}' を処理しました"}


@app.post("/mock/webhook/follow")
async def mock_follow_webhook():
    """モックテスト用: 友だち追加Webhookシミュレーション

    Returns:
        Webhook処理結果
    """
    if not MOCK_MODE:
        raise HTTPException(status_code=403, detail="モックモードが無効です")

    # モックデータ生成
    mock_request = mock_data.create_mock_follow_event()

    # WebhookRequest作成
    webhook_request = WebhookRequest(**mock_request)

    # イベント処理
    for event in webhook_request.events:
        if event.type == "follow":
            await handle_follow(event)

    return {"status": "ok", "message": "友だち追加イベントを処理しました"}


@app.post("/mock/webhook/postback")
async def mock_postback_webhook(data: str = "character=botan"):
    """モックテスト用: Postback Webhookシミュレーション

    Args:
        data: Postbackデータ（例: character=botan）

    Returns:
        Webhook処理結果
    """
    if not MOCK_MODE:
        raise HTTPException(status_code=403, detail="モックモードが無効です")

    # モックデータ生成（postback用に拡張）
    from .models import WebhookRequest, Event, Source, Postback

    mock_request_data = {
        "destination": "U1234567890",
        "events": [
            {
                "type": "postback",
                "timestamp": 1234567890123,
                "source": {
                    "type": "user",
                    "userId": "U_mock_user_123"
                },
                "replyToken": "mock_reply_token_postback",
                "postback": {
                    "data": data
                }
            }
        ]
    }

    # WebhookRequest作成
    webhook_request = WebhookRequest(**mock_request_data)

    # イベント処理
    for event in webhook_request.events:
        if event.type == "postback":
            await handle_postback(event)

    return {"status": "ok", "message": f"Postbackイベントを処理しました: {data}"}


# ========================================
# Layer 3管理用エンドポイント
# ========================================

@app.post("/admin/reload_ng_words")
async def reload_ng_words():
    """管理用: NGワードをDBから再ロード

    Returns:
        リロード結果
    """
    if not MOCK_MODE:
        # 本番環境では認証が必要
        raise HTTPException(status_code=403, detail="要認証")

    logger.info("管理リクエスト: NGワードリロード")

    # 統合版または旧版のSensitiveHandlerを取得
    handler = None
    if USE_INTEGRATED_DETECTOR and integrated_detector:
        handler = integrated_detector.static_handler
    elif USE_SENSITIVE_CHECK and sensitive_handler:
        handler = sensitive_handler

    if handler and hasattr(handler, 'reload_ng_words'):
        count = handler.reload_ng_words()
        return {
            "status": "ok",
            "message": f"NGワードを再ロードしました",
            "db_ng_words_count": count,
            "total_patterns": len(handler.ng_patterns) + len(handler.db_ng_patterns),
            "detector_type": "integrated" if USE_INTEGRATED_DETECTOR else "legacy"
        }
    else:
        return {
            "status": "error",
            "message": "センシティブ判定が無効、またはリロード機能が利用できません"
        }


@app.post("/admin/add_ng_word")
async def add_ng_word(
    word: str,
    category: str = "tier2_general",
    severity: int = 5,
    notes: str = ""
):
    """管理用: NGワードをDBに追加

    Args:
        word: NGワード
        category: カテゴリ
        severity: 深刻度（1-10）
        notes: メモ

    Returns:
        追加結果
    """
    if not MOCK_MODE:
        # 本番環境では認証が必要
        raise HTTPException(status_code=403, detail="要認証")

    logger.info(f"管理リクエスト: NGワード追加 - {word}")

    # 統合版または旧版のSensitiveHandlerを取得
    handler = None
    if USE_INTEGRATED_DETECTOR and integrated_detector:
        handler = integrated_detector.static_handler
    elif USE_SENSITIVE_CHECK and sensitive_handler:
        handler = sensitive_handler

    if not handler or not hasattr(handler, 'dynamic_detector'):
        return {"status": "error", "message": "センシティブ判定が無効です"}

    if not handler.dynamic_detector:
        return {"status": "error", "message": "DynamicDetectorが利用できません"}

    # subcategoryを推定
    if "tier1" in category:
        subcategory = category.replace("tier1_", "")
    elif "tier2" in category:
        subcategory = category.replace("tier2_", "")
    else:
        subcategory = "general"

    # DBに追加
    import sqlite3
    db_path = handler.dynamic_detector.db_path

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ng_words
            (word, category, subcategory, severity, language, pattern_type,
             action, added_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            word,
            category,
            subcategory,
            severity,
            'ja',
            'partial',
            'warn' if severity < 8 else 'block',
            'admin_api',
            notes
        ))

        conn.commit()
        conn.close()

        # リロード
        count = handler.reload_ng_words()

        return {
            "status": "ok",
            "message": f"NGワード '{word}' を追加し、リロードしました",
            "word": word,
            "category": category,
            "severity": severity,
            "db_ng_words_count": count
        }

    except sqlite3.IntegrityError:
        return {"status": "error", "message": f"NGワード '{word}' は既に登録されています"}
    except Exception as e:
        return {"status": "error", "message": f"追加失敗: {str(e)}"}


# ========================================
# アプリケーション起動
# ========================================

if __name__ == "__main__":
    import uvicorn
    logger.info("FastAPI Webhookサーバー起動")
    logger.info(f"モックモード: {MOCK_MODE}")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
