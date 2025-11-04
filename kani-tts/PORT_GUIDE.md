# ポート設定ガイド

## デフォルトポート変更: 8000 → 8888

**理由**: ポート8000が既に使用中のため、デフォルトを8888に変更しました。

---

## サーバー起動

### デフォルトポート（8888）

```bash
python webui_server.py
```

**出力:**
```
============================================================
Starting KaniTTS WebUI Server
Access at: http://localhost:8888
============================================================
```

### カスタムポート指定

```bash
python webui_server.py 9000   # ポート9000で起動
python webui_server.py 5000   # ポート5000で起動
```

---

## テストスクリプト実行

### デフォルトポート（8888）使用

```bash
python test_webui_api.py
python test_webui_simple.py "こんにちは"
```

### カスタムポート使用

環境変数 `WEBUI_PORT` で指定:

```bash
WEBUI_PORT=9000 python test_webui_api.py
WEBUI_PORT=5000 python test_webui_simple.py "こんにちは"
```

---

## ブラウザアクセス

### ローカル

**デフォルトポート:**
```
http://localhost:8888
```

**カスタムポート:**
```
http://localhost:9000
http://localhost:5000
```

### WSL2からWindowsブラウザ

1. **WSL2のIPアドレス確認:**
```bash
ip addr show eth0 | grep inet
# 例: inet 172.24.123.45/20
```

2. **Windowsブラウザでアクセス:**
```
http://172.24.123.45:8888    # デフォルトポート
http://172.24.123.45:9000    # カスタムポート
```

---

## ポート確認方法

### 使用中のポート確認

```bash
ss -tulpn | grep -E ":(8000|8888|9000)"
```

### 空きポート探し

```bash
# ポート8888-8900の範囲で確認
for port in {8888..8900}; do
  ss -tulpn | grep -q ":$port" || echo "Port $port is available"
done
```

---

## トラブルシューティング

### エラー: address already in use

**原因:** 指定したポートが既に使用中

**解決策1: 別のポートを使用**
```bash
python webui_server.py 8889  # 次のポート番号を試す
```

**解決策2: 使用中のプロセスを確認**
```bash
ss -tulpn | grep :8888
```

### エラー: Connection refused

**原因1:** サーバーが起動していない
```bash
# サーバー起動を確認
ps aux | grep webui_server
```

**原因2:** ポート番号が違う
```bash
# サーバーのポート番号を確認
# テストスクリプトのポート番号を合わせる
WEBUI_PORT=8888 python test_webui_simple.py "テスト"
```

---

## まとめ

**変更点:**
- デフォルトポート: 8000 → **8888**
- サーバー起動時にポート表示
- 環境変数でポート指定可能

**推奨:**
- 通常は8888を使用（デフォルト）
- 衝突時は9000, 5000などを使用
- テストスクリプトは環境変数で合わせる
