# WebUI API テスト方法

ブラウザを使わずにコマンドラインからWebSocket APIをテストする方法です。

---

## クイックスタート

### 1. サーバー起動（別ターミナル）

```bash
cd /home/koshikawa/toExecUnit/kani-tts
source venv/bin/activate
python webui_server.py        # デフォルトポート: 8888
# または
python webui_server.py 9000   # カスタムポート指定
```

### 2. APIテスト実行

**方法1: 複数テストケース自動実行**

```bash
source venv/bin/activate
python test_webui_api.py
```

**方法2: カスタムメッセージでテスト**

```bash
source venv/bin/activate
python test_webui_api.py "こんにちは、牡丹です"
```

---

## テストスクリプトの機能

### ✅ WebSocket通信テスト

- WebSocketサーバーへの接続確認
- メッセージ送受信の動作確認
- エラーハンドリング確認

### ✅ 音声データ受信確認

- Base64エンコードされた音声チャンクの受信
- デコード処理の確認
- 音声データのWAVファイル保存

### ✅ 自動テストケース

デフォルトで以下のテストを実行:

1. **短文テスト（Voice ON）**
   - メッセージ: "こんにちは"
   - 音声生成・受信確認

2. **長文テスト（Voice ON）**
   - メッセージ: "牡丹プロジェクトって何？"
   - 複数チャンクの受信確認

3. **Voice OFFテスト**
   - メッセージ: "短いテスト"
   - テキストのみ応答確認

---

## 出力例

```
================================================================================
WebUI WebSocket API Test
================================================================================

Test message: こんにちは
Voice enabled: True
Save audio: True

[CONNECTING] Attempting to connect to ws://localhost:8000/ws...
[CONNECTED] WebSocket connection established
            URL: ws://localhost:8000/ws

[SENDING] Message: {"type": "message", "content": "こんにちは", "voice_enabled": true}

[RECEIVED] Audio chunk (base64 length: 117344)
           Duration: 2.00s, Sample rate: 22050 Hz

[RECEIVED] Audio chunk (base64 length: 117344)
           Duration: 2.00s, Sample rate: 22050 Hz

[RECEIVED] Text response: やっほー！こんにちは！

[CLOSED] WebSocket connection closed
          Status code: 1000

================================================================================
Test Results
================================================================================

Response text: やっほー！こんにちは！
Audio chunks received: 2
Total audio duration: 4.00s
Total samples: 88200

✅ Audio saved to: webui_test_20251008_140530.wav

================================================================================
Test completed
================================================================================
```

---

## ファイル構成

### 実行ファイル

```
/home/koshikawa/toExecUnit/kani-tts/
├── webui_server.py          # WebSocketサーバー
├── test_webui_api.py        # APIテストスクリプト（新規）
└── webui_test_*.wav         # 生成される音声ファイル
```

### 依存パッケージ

- `websocket-client` - WebSocketクライアント
- `numpy` - 音声データ処理
- `scipy` - WAVファイル保存

---

## 使用方法

### 基本テスト

```bash
# 自動テストケース実行
python test_webui_api.py
```

### カスタムメッセージ

```bash
# 任意のメッセージでテスト
python test_webui_api.py "牡丹ちゃん、お疲れ様！"
```

### Voice OFF テスト

スクリプト内で `voice_enabled=False` に変更:

```python
test_webui_api("テストメッセージ", voice_enabled=False)
```

---

## トラブルシューティング

### エラー: Connection refused

**原因:** WebSocketサーバーが起動していない

**解決策:**
```bash
# 別ターミナルでサーバー起動
python webui_server.py
```

### エラー: ModuleNotFoundError: No module named 'websocket'

**原因:** websocket-clientがインストールされていない

**解決策:**
```bash
source venv/bin/activate
pip install websocket-client
```

### 音声ファイルが保存されない

**原因1:** Voice OFFでテストしている
- `voice_enabled=True` で実行

**原因2:** 書き込み権限がない
- カレントディレクトリの権限確認

---

## API仕様

### リクエスト（クライアント → サーバー）

```json
{
  "type": "message",
  "content": "ユーザーメッセージ",
  "voice_enabled": true
}
```

### レスポンス（サーバー → クライアント）

**音声チャンク:**
```json
{
  "type": "audio_chunk",
  "data": "base64エンコードされたInt16 PCMデータ",
  "sample_rate": 22050
}
```

**テキスト応答:**
```json
{
  "type": "text",
  "content": "応答テキスト"
}
```

**エラー:**
```json
{
  "type": "error",
  "message": "エラーメッセージ"
}
```

---

## 音声データ処理

### Base64デコード

```python
import base64
import numpy as np

# Base64 → bytes
audio_bytes = base64.b64decode(base64_data)

# bytes → int16 array
audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)

# int16 → float32 (-1.0 to 1.0)
audio_float32 = audio_int16.astype(np.float32) / 32768.0
```

### WAVファイル保存

```python
from scipy.io.wavfile import write

# 全チャンクを結合
full_audio = np.concatenate(audio_chunks)

# WAV保存
write("output.wav", 22050, full_audio)
```

---

## 応用例

### 連続テスト

```python
messages = [
    "こんにちは",
    "調子はどう？",
    "また後でね"
]

for msg in messages:
    test_webui_api(msg, voice_enabled=True)
    time.sleep(3)  # 次のテストまで待機
```

### 音声品質チェック

```python
# 長文で音声品質確認
long_message = """
牡丹プロジェクトは、完全ローカルで動作する
AI VTuberシステムです。ElevenLabsから
KaniTTSへの移行を進めています。
"""

test_webui_api(long_message, voice_enabled=True, save_audio=True)
# 生成されたWAVファイルを確認
```

### パフォーマンス測定

```python
import time

start = time.time()
test_webui_api("パフォーマンステスト", voice_enabled=True)
elapsed = time.time() - start

print(f"Total time: {elapsed:.2f}s")
```

---

## まとめ

### APIテストで確認できること

- ✅ WebSocket接続の正常性
- ✅ メッセージ送受信
- ✅ 音声データのストリーミング受信
- ✅ Base64エンコード/デコード
- ✅ 音声ファイル生成
- ✅ Voice ON/OFF切り替え

### ブラウザテストとの違い

| 項目 | APIテスト | ブラウザテスト |
|------|-----------|---------------|
| 実行環境 | コマンドライン | Webブラウザ |
| 音声再生 | WAVファイル保存 | リアルタイム再生 |
| デバッグ | 詳細ログ出力 | Console確認 |
| 自動化 | 容易 | 困難 |

### 推奨用途

**APIテスト:**
- CI/CD自動テスト
- パフォーマンス測定
- デバッグ・開発時

**ブラウザテスト:**
- ユーザー体験確認
- 音質チェック
- UIデザイン確認

---

## 関連ドキュメント

- [WEBUI_README.md](WEBUI_README.md) - WebUI使用方法
- [KaniTTS_WebUIチャット機能_実装レポート.md](../kirinuki/2025-10-08/KaniTTS_WebUIチャット機能_実装レポート.md) - 実装詳細
