---
title: LINE Botでキャラクター切り替え実装！Reply APIで無料・無制限の会話Bot
tags:
  - Python
  - LINE
  - linebot
  - MessagingAPI
  - FastAPI
private: false
updated_at: '2025-11-12T00:01:12+09:00'
id: ae1fe43a7ef740d81edf
organization_url_name: null
slide: false
ignorePublish: false
---

# LINE Botでキャラクター切り替え実装！Reply APIで無料・無制限の会話Bot

## はじめに

LINE公式アカウントで**複数のキャラクター**を切り替えられる会話Botを作りました。ユーザーがリッチメニューでキャラクターを選ぶと、アイコンや名前、会話の性格まで変わります。

![デモGIF](https://raw.githubusercontent.com/koshikawa-masato/AI-Vtuber-Project/feature/line-bot-integration/screenshots/chat_20251111.gif)

### 実装した機能

- **リッチメニューでキャラクター選択**（3人の姉妹から選べる）
- **キャラクターごとに異なるアイコン・名前**（LINE Messaging APIの`sender`機能）
- **会話の性格もキャラクターに応じて変化**（ローカルLLM統合）
- **Reply API使用で無料・無制限**（何通会話しても無料枠を消費しない）

### この記事で得られる知見

- LINE Messaging APIの実践的な使い方
- **Reply APIとPush APIの違いと料金体系**
- `sender`機能を使ったキャラクター切り替え
- リッチメニューの実装方法（日本語フォント対応含む）
- FastAPIでの静的ファイル配信

### 対象読者

- LINE Botを作りたい開発者
- キャラクターBotに興味がある人
- LINE公式アカウントの料金を抑えたい人

---

## なぜReply APIなのか？料金体系を理解する

LINE公式アカウントには**2つのメッセージ送信方法**があります。料金が大きく異なるため、まずこれを理解することが重要です。

### Reply API vs Push API

| 項目 | Reply API | Push API |
|------|-----------|----------|
| **用途** | ユーザーからのメッセージに返信 | Botから能動的に送信 |
| **料金** | **無料・無制限** ✅ | 有料（月200通まで無料） |
| **使用例** | 会話Bot、自動応答 | リマインダー、定期配信 |
| **制約** | `reply_token`が必要（1回のみ有効） | `user_id`で任意のタイミングで送信可能 |

### 実装方針

今回は**Reply API**のみを使用することで：

- ✅ **どれだけ会話しても無料枠を消費しない**
- ✅ Webhookで受信した`reply_token`を使って返信
- ✅ コスト効率の良いBot設計

**重要ポイント**: Reply APIは「ユーザーが送ってきたメッセージに対する返信」のみに使えます。Botから先にメッセージを送ることはできません。

---

## システム構成

### アーキテクチャ概要

```
[ユーザー] ← → [LINE Platform] ← Webhook → [FastAPI Server] ← → [Ollama LLM]
                                                    ↓
                                          [Session Manager]
                                          [Character Icons]
```

### 使用技術

- **FastAPI**: Webhook受信、静的ファイル配信
- **LINE Messaging API**: メッセージ送受信
- **Ollama**: ローカルLLM（qwen2.5:14b）
- **ngrok**: ローカル開発環境の公開
- **Pillow**: リッチメニュー画像生成

---

## 環境構築

### 1. LINE公式アカウント作成

[LINE Developers Console](https://developers.line.biz/console/)でチャネルを作成します。

1. **Messaging API チャネル作成**
2. **Channel Secret** と **Channel Access Token** を取得
3. **Webhook URL** を後で設定（ngrokのURLを使用）

### 2. FastAPIサーバー構築

基本的なWebhook受信コードを準備します。

```python
from fastapi import FastAPI, Request, Header
from fastapi.staticfiles import StaticFiles
import hmac
import hashlib
import base64
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# assetsディレクトリをマウント（キャラクターアイコン配信用）
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

def verify_signature(body: bytes, signature: str) -> bool:
    """LINE署名検証"""
    hash = hmac.new(
        CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(hash).decode('utf-8')
    return expected_signature == signature

@app.post("/webhook")
async def webhook(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()

    # 署名検証
    if not verify_signature(body, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Webhook処理
    events = (await request.json())["events"]
    for event in events:
        if event["type"] == "message":
            await handle_text_message(event)
        elif event["type"] == "postback":
            await handle_postback(event)

    return {"status": "ok"}
```

### 3. ngrokでローカル公開

```bash
# ngrok起動
ngrok http 8000

# 表示されたURLをLINE DevelopersコンソールのWebhook URLに設定
# 例: https://xxxx-xxx-xxx.ngrok-free.app/webhook
```

---

## リッチメニューの実装

### リッチメニューとは

LINE Botのチャット画面下部に表示されるメニューです。タップするとPostbackアクションが送信されます。

![リッチメニュー例](https://raw.githubusercontent.com/koshikawa-masato/AI-Vtuber-Project/feature/line-bot-integration/assets/richmenu_sisters.png)

### 画像生成（日本語フォント対応）

**問題**: DejaVuフォントでは日本語が文字化け（□□表示）

**解決策**: Noto Sans CJK フォントを使用

```python
from PIL import Image, ImageDraw, ImageFont

# 画像サイズ（LINE仕様: 2500x843）
WIDTH = 2500
HEIGHT = 843

# 新しい画像を作成
img = Image.new('RGB', (WIDTH, HEIGHT), 'white')
draw = ImageDraw.Draw(img)

# 日本語フォントを読み込み
font_path = "assets/fonts/NotoSansCJKjp-Regular.otf"
font = ImageFont.truetype(font_path, 120)

# 3分割してキャラクターを描画
SECTION_WIDTH = WIDTH // 3

for i, char in enumerate([
    {"name": "牡丹", "romaji": "Botan", "color": "#FFB6C1"},
    {"name": "Kasho", "romaji": "花相", "color": "#E6E6FA"},
    {"name": "ユリ", "romaji": "Yuri", "color": "#FFFACD"}
]):
    x_start = i * SECTION_WIDTH

    # 背景色
    draw.rectangle(
        [(x_start, 0), (x_start + SECTION_WIDTH, HEIGHT)],
        fill=char["color"]
    )

    # キャラクター名を描画
    draw.text((x_start + 200, 300), char["name"], fill="#333", font=font)

img.save("assets/richmenu_sisters.png", "PNG")
```

**ハマりポイント**: 日本語フォントを使わないと文字化けします。Noto Sans CJKは[Google Fonts](https://fonts.google.com/noto/specimen/Noto+Sans+JP)から入手できます。

### LINE APIでリッチメニュー登録

```python
import requests

def create_richmenu():
    # リッチメニュー作成
    richmenu_data = {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": "三姉妹選択メニュー",
        "chatBarText": "キャラクターを選択",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "postback",
                    "data": "character=botan",
                    "displayText": "牡丹を選択"
                }
            },
            {
                "bounds": {"x": 833, "y": 0, "width": 834, "height": 843},
                "action": {
                    "type": "postback",
                    "data": "character=kasho",
                    "displayText": "Kashoを選択"
                }
            },
            {
                "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "postback",
                    "data": "character=yuri",
                    "displayText": "ユリを選択"
                }
            }
        ]
    }

    response = requests.post(
        "https://api.line.me/v2/bot/richmenu",
        headers={
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=richmenu_data
    )

    richmenu_id = response.json()["richMenuId"]
    return richmenu_id
```

### 画像アップロード

```python
def upload_richmenu_image(richmenu_id, image_path):
    # ⚠️ 重要: api-data.line.me を使用
    url = f"https://api-data.line.me/v2/bot/richmenu/{richmenu_id}/content"

    with open(image_path, "rb") as f:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                "Content-Type": "image/png"
            },
            data=f.read()
        )

    return response.status_code == 200
```

**ハマりポイント**: 画像アップロードは `api-data.line.me` を使う必要があります。`api.line.me`では404エラーになります。

---

## sender機能でキャラクター切り替え

### sender機能とは

LINE Messaging APIの機能で、メッセージ送信時に**表示名とアイコンを動的に変更**できます。

### キャラクターアイコンの配信

FastAPIで静的ファイルを配信します。

```python
from fastapi.staticfiles import StaticFiles

# FastAPIで静的ファイルを配信
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
```

アイコン画像は以下のURLでアクセスできるようにします：
- `https://your-domain.ngrok-free.app/assets/botan.png`
- `https://your-domain.ngrok-free.app/assets/kasho.png`
- `https://your-domain.ngrok-free.app/assets/yuri.png`

### Reply APIでsenderを指定

```python
import requests

def send_line_reply(reply_token: str, message: str, character: str = "botan"):
    """LINE Messaging APIでメッセージを返信（sender機能付き）"""

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

    sender_info = character_info[character]

    # Reply API with sender
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

    response = requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=data
    )

    return response.status_code == 200
```

**重要ポイント**:
- `sender.name`: チャット画面に表示される名前
- `sender.iconUrl`: HTTPSでアクセス可能なURL（ngrokでOK）

---

## セッション管理

### ユーザーごとにキャラクター記憶

```python
class SessionManager:
    """ユーザーセッション管理（インメモリ）"""

    def __init__(self):
        self.sessions = {}

    def set_character(self, user_id: str, character: str):
        """キャラクターを保存"""
        if user_id not in self.sessions:
            self.sessions[user_id] = {}
        self.sessions[user_id]["character"] = character

    def get_character(self, user_id: str, default: str = "botan") -> str:
        """キャラクターを取得"""
        return self.sessions.get(user_id, {}).get("character", default)

# グローバルインスタンス
session_manager = SessionManager()
```

### Postbackアクションの処理

リッチメニューのタップを処理します。

```python
async def handle_postback(event):
    """Postback処理（リッチメニューのタップ）"""
    user_id = event["source"]["userId"]
    reply_token = event["replyToken"]
    postback_data = event["postback"]["data"]

    # "character=botan" のような形式
    if postback_data.startswith("character="):
        character = postback_data.split("=")[1]

        # セッションに保存
        session_manager.set_character(user_id, character)

        # 確認メッセージ（選択したキャラクターで返信）
        character_names = {
            "botan": "牡丹",
            "kasho": "Kasho",
            "yuri": "ユリ"
        }
        name = character_names.get(character, character)

        send_line_reply(
            reply_token,
            f"{name}を選択しました！よろしくね♪",
            character  # ← sender機能でキャラクターを指定
        )
```

### テキストメッセージの処理

```python
async def handle_text_message(event):
    """テキストメッセージ処理"""
    user_id = event["source"]["userId"]
    message_text = event["message"]["text"]
    reply_token = event["replyToken"]

    # ユーザーの選択キャラクターを取得
    character = session_manager.get_character(user_id, default="botan")

    # LLMで応答生成（キャラクターの性格を反映）
    response_text = generate_llm_response(message_text, character)

    # Reply API（選択したキャラクターで返信）
    send_line_reply(reply_token, response_text, character)
```

---

## LLMとの統合（オプション）

キャラクターごとに性格を変えるため、システムプロンプトを切り替えます。

```python
def generate_llm_response(user_message: str, character: str) -> str:
    """LLMで応答生成（キャラクター性格反映）"""

    # キャラクターごとのシステムプロンプト
    character_prompts = {
        "botan": """あなたは17歳の明るく社交的なギャル系キャラクター「牡丹」です。
LA帰りの帰国子女で、「マジで」「超〜」などの口調を使います。
VTuberに憧れていて、配信について話すのが好きです。""",

        "kasho": """あなたは19歳の責任感が強い長女「Kasho」です。
音楽の造詣が深く、論理的思考で物事を考えます。
真面目な性格ですが、妹たちのことを心配しています。""",

        "yuri": """あなたは15歳の内向的で洞察力のある三女「ユリ」です。
ライトノベルを多読していて、サブカル知識が豊富です。
好奇心旺盛で創造的、マイペースな性格です。"""
    }

    system_prompt = character_prompts.get(character, character_prompts["botan"])

    # Ollama（ローカルLLM）で生成
    response = ollama.generate(
        model="qwen2.5:14b",
        system=system_prompt,
        prompt=user_message
    )

    return response["response"]
```

---

## デモと動作確認

### 実際の動作

![デモGIF](https://raw.githubusercontent.com/koshikawa-masato/AI-Vtuber-Project/feature/line-bot-integration/screenshots/chat_20251111.gif)

### 動作の様子

1. **キャラクター選択**: リッチメニューから「牡丹」を選択
2. **確認メッセージ**: 「牡丹を選択しました！よろしくね♪」（アイコンが牡丹）
3. **会話開始**: ユーザー「牡丹、今日配信だった？」
4. **応答**: 牡丹の性格で返信（ギャル系口調）

### 確認ポイント

- ✅ リッチメニューで選択できる
- ✅ アイコンと名前が変わる
- ✅ 会話の性格が変わる
- ✅ 選択したキャラクターが記憶される

---

## ハマったポイントと解決策

### 1. 画像アップロードが404エラー

**原因**: `api.line.me` を使っていた

**解決**: `api-data.line.me` に変更

```python
# ❌ 間違い
url = f"https://api.line.me/v2/bot/richmenu/{richmenu_id}/content"

# ✅ 正しい
url = f"https://api-data.line.me/v2/bot/richmenu/{richmenu_id}/content"
```

### 2. 日本語が文字化け（□□表示）

**原因**: DejaVuフォントは日本語非対応

**解決**: Noto Sans CJK フォントをダウンロードして使用

```python
# Noto Sans CJK フォントをダウンロード
# https://fonts.google.com/noto/specimen/Noto+Sans+JP

font = ImageFont.truetype("NotoSansCJKjp-Regular.otf", 120)
```

### 3. アイコンが表示されない

**原因**: iconUrlがHTTPSでアクセスできなかった

**解決**:
1. FastAPIでStaticFiles配信
2. ngrokでHTTPS化
3. 環境変数でngrok URLを管理

```python
NGROK_URL = os.getenv("NGROK_URL", "https://xxxx.ngrok-free.app")
iconUrl = f"{NGROK_URL}/assets/botan.png"
```

### 4. Reply APIとPush APIの混同

**原因**: 最初Push APIを使おうとしていた

**解決**: Reply APIを使うことで無料・無制限に

```python
# Reply API: reply_tokenを使う（無料）
send_line_reply(reply_token, message)

# Push API: user_idを使う（有料）
# 今回は使わない
```

---

## まとめ

### 実装のポイント

1. **Reply APIを使えば無料・無制限**
   - ユーザーからのメッセージに返信する形式
   - 会話Botに最適

2. **sender機能でキャラクター切り替えが可能**
   - アイコンと名前を動的に変更
   - FastAPIで静的ファイル配信

3. **リッチメニューでUX向上**
   - Postbackアクションで選択を検知
   - セッション管理でキャラクターを記憶

4. **日本語フォント対応が必須**
   - Noto Sans CJKを使用
   - Pillowで画像生成

### 今後の拡張案

#### 1. スタンプ対応（VLM統合）

**課題**: LINEはスタンプ文化が根付いており、テキストだけでなくスタンプでのコミュニケーションが頻繁に行われます。現在の実装ではスタンプメッセージに対応していません。

**実装予定**:

```python
async def handle_sticker_message(event):
    """スタンプメッセージ処理"""
    user_id = event["source"]["userId"]
    reply_token = event["replyToken"]
    sticker_id = event["message"]["stickerId"]

    # スタンプ画像URLを構築
    sticker_url = f"https://stickershop.line-scdn.net/stickershop/v1/sticker/{sticker_id}/android/sticker.png"

    # VLM（Vision Language Model）でスタンプの感情/意味を理解
    # Ollama + LLaVA / GPT-4o / Gemini Visionなど
    analysis = analyze_sticker_with_vlm(sticker_url)
    # 例: {"emotion": "happy", "meaning": "喜びを表現している"}

    # キャラクターの性格を反映した返信を生成
    character = session_manager.get_character(user_id, default="botan")
    response = generate_response_to_sticker(analysis, character)

    send_line_reply(reply_token, response, character)
```

**期待される効果**:
- スタンプの感情を理解した自然な返信
- 「笑顔のスタンプ」→ 「嬉しそうだね！」のような反応
- よりLINEらしいコミュニケーション

#### 2. その他の拡張案

- **データベースでセッション永続化** （現在はインメモリ）
- **より高度なキャラクター性格** （記憶機能、文脈理解）
- **グループチャット対応** （複数ユーザーでの会話）
- **Flex Message対応** （リッチなカード型メッセージ）

### ソースコード

プロジェクトの完全なソースコードはGitHubで公開しています。

- GitHub: [AI-Vtuber-Project](https://github.com/koshikawa-masato/AI-Vtuber-Project)
- ブランチ: `feature/line-bot-integration`

### 参考リンク

- [LINE Messaging API ドキュメント](https://developers.line.biz/ja/docs/messaging-api/)
- [FastAPI 公式ドキュメント](https://fastapi.tiangolo.com/ja/)
- [Noto Sans CJK](https://fonts.google.com/noto/specimen/Noto+Sans+JP)

---

## おわりに

この記事では、LINE Messaging APIを使ったキャラクター切り替えBotの実装方法を紹介しました。**Reply APIを活用することで、コストを抑えながら高機能なBotを作ることができます。**

特に重要なのは：

- Reply APIとPush APIの違いを理解すること
- sender機能を使ったキャラクター切り替え
- リッチメニューでのUX向上

ぜひ、あなたのプロジェクトでも試してみてください！

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
