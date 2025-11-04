# KaniTTS WebUI チャット機能

ブラウザからKaniTTSにアクセスし、ボイスON時に自動的にストリーミング音声再生するWebチャット機能です。

---

## クイックスタート

### 1. サーバー起動

```bash
cd /home/koshikawa/toExecUnit/kani-tts
source venv/bin/activate
python webui_server.py        # デフォルトポート: 8888
# または
python webui_server.py 9000   # カスタムポート指定
```

### 2. ブラウザでアクセス

**ローカル:**
```
http://localhost:8888
```

**WSL2環境の場合（Windows開発機から）:**

1. WSL2のIPアドレス確認:
```bash
ip addr show eth0 | grep inet
# 例: 172.24.xxx.xxx
```

2. Windowsブラウザでアクセス:
```
http://172.24.xxx.xxx:8888
```

---

## 機能

### ✅ リアルタイム音声ストリーミング

- **ボイスON**: メッセージ送信後、2-3秒で音声再生開始
- **ボイスOFF**: テキストのみの高速応答
- **自動切り替え**: ボタン一つで簡単ON/OFF

### ✅ 自然な会話フロー

- 音声生成と同時にストリーミング再生
- 待機時間60%削減（従来5.9秒 → 2-3秒）
- チャンクごとに即座に再生

### ✅ マルチデバイス対応

- PC、スマートフォン、タブレットからアクセス可能
- 同一ネットワーク内で複数デバイス利用可

---

## 使い方

### 画面説明

```
┌─────────────────────────────────────┐
│  KaniTTS Chat                       │
├─────────────────────────────────────┤
│                                     │
│  User: こんにちは                   │
│                                     │
│  Assistant: やっほー！             │
│                                     │
├─────────────────────────────────────┤
│ [                  ] [Send] [Voice ON]│
└─────────────────────────────────────┘
```

### ボイスON/OFF

**Voice ON（緑ボタン）:**
- テキスト応答＋音声再生
- 2-3秒で音声再生開始
- ストリーミングで逐次再生

**Voice OFF（グレーボタン）:**
- テキスト応答のみ
- 音声生成なし（高速応答）

### メッセージ送信

1. テキストボックスに入力
2. **Send**ボタンまたは**Enter**キー
3. 応答が表示される
4. ボイスON時は音声も再生される

---

## 技術詳細

### アーキテクチャ

```
ブラウザ ←→ WebSocket ←→ FastAPI サーバー
   ↓                           ↓
Web Audio API            KaniTTS音声生成
   ↓                           ↓
スピーカー出力         音声チャンクBase64送信
```

### 音声フォーマット

- **サンプルレート**: 22050 Hz
- **チャンネル**: モノラル
- **ビット深度**: 16-bit PCM → Float32（ブラウザ側）
- **エンコード**: Base64（WebSocket転送用）
- **チャンクサイズ**: 25フレーム（約2秒）

### パフォーマンス

| 項目 | 値 |
|------|-----|
| 初回音声再生開始 | 2-3秒 |
| チャンク生成間隔 | 2秒 |
| 帯域幅（平均） | 350Kbps |
| 帯域幅（ピーク） | 700Kbps |

---

## トラブルシューティング

### 音声が再生されない

**原因1: ボイスがOFFになっている**
- Voice ONボタン（緑色）を確認

**原因2: ブラウザの自動再生ポリシー**
- ページ内を一度クリック
- AudioContextが初期化される

**原因3: ブラウザ非対応**
- Chrome、Edge、Safari、Firefox推奨
- Web Audio API対応ブラウザが必要

### サーバーにアクセスできない

**WSL2環境の場合:**

1. WSL2のIPアドレス確認:
```bash
ip addr show eth0 | grep inet
```

2. Windowsファイアウォール設定確認

3. WSL2のポート8000が開いているか確認:
```bash
ss -tulpn | grep 8000
```

### 音声が途切れる

**原因: ネットワーク帯域不足**
- ローカルネットワーク推奨
- Wi-Fi接続を有線LANに変更
- 他のネットワーク利用を減らす

---

## 開発者向け

### カスタマイズ

**ポート番号変更:**
```python
# webui_server.py 最終行
uvicorn.run(app, host="0.0.0.0", port=8000)  # ← ポート番号変更
```

**チャンクサイズ調整:**
```python
# config.py
CHUNK_SIZE = 25  # フレーム数（1フレーム = 約80ms）
```

**音声圧縮追加（将来）:**
```python
# Opusエンコード例
import opuslib
encoder = opuslib.Encoder(SAMPLE_RATE, 1, opuslib.APPLICATION_AUDIO)
opus_data = encoder.encode(pcm_data, frame_size)
```

### API仕様

**WebSocketメッセージ:**

**クライアント → サーバー:**
```json
{
  "type": "message",
  "content": "ユーザーメッセージ",
  "voice_enabled": true
}
```

**サーバー → クライアント（音声チャンク）:**
```json
{
  "type": "audio_chunk",
  "data": "base64エンコードされたPCMデータ",
  "sample_rate": 22050
}
```

**サーバー → クライアント（テキスト）:**
```json
{
  "type": "text",
  "content": "応答テキスト"
}
```

**サーバー → クライアント（エラー）:**
```json
{
  "type": "error",
  "message": "エラーメッセージ"
}
```

---

## ライセンス

KaniTTSプロジェクトと同様のライセンス（Apache 2.0）

---

## 関連ドキュメント

- [KaniTTS_ストリーミング再生機能_実装レポート.md](../kirinuki/2025-10-08/KaniTTS_ストリーミング再生機能_実装レポート.md)
- [KaniTTS_WebUIチャット機能_実装レポート.md](../kirinuki/2025-10-08/KaniTTS_WebUIチャット機能_実装レポート.md)
- [KaniTTS_Phase1_検証レポート.md](../kirinuki/2025-10-08/KaniTTS_Phase1_検証レポート.md)
