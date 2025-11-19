# リッチメニュー自動切り替えモード - デプロイ手順書

> 作成日: 2025-11-17
> Phase 3: 三姉妹自動切り替え + フィードバック機能

---

## 📋 実装内容サマリー

### ✅ 完了した実装

1. **データベース拡張**
   - `sessions` テーブルに `selected_mode`、`feedback_state` カラム追加
   - `feedback` テーブル新規作成

2. **LINE Bot 機能拡張**
   - 三姉妹自動選択機能（親和性スコアリング）
   - フィードバック受付・保存機能
   - LINE Notify 連携（開発者への通知）
   - モード設定機能（auto / botan / kasho / yuri）

3. **リッチメニュー**
   - 新しいリッチメニュー画像作成 (2500x1686px)
   - 6ボタン構成（自動 / FB / 規約 / 牡丹 / Kasho / ユリ）

---

## 🚀 デプロイ手順

### 1. LINE Notify トークン取得（初回のみ）

1. https://notify-bot.line.me/my/ にアクセス
2. 「トークンを発行する」をクリック
3. トークン名: `AI-Vtuber-Project Feedback`
4. 送信先: `1:1でLINE Notifyから通知を受け取る`
5. 発行されたトークンを `.env` に保存

**VPS の `.env` に追加**:
```bash
ssh -p 443 ubuntu@133.167.93.123
sudo vim /root/AI-Vtuber-Project/.env
```

追加内容:
```
LINE_NOTIFY_TOKEN=your_token_here
```

---

### 2. VPS にコードをデプロイ

```bash
# ローカルでコミット
git add .
git commit -m "feat: リッチメニュー自動切り替えモード実装

- 三姉妹自動選択機能
- フィードバック機能
- LINE Notify連携
- リッチメニュー画像作成

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# GitHubにpush
git push origin main

# VPSでpull
ssh -p 443 ubuntu@133.167.93.123
cd /root/AI-Vtuber-Project
git pull origin main
```

---

### 3. VPS で LINE Bot サービス再起動

```bash
# サービス再起動
sudo systemctl restart line-bot-vps

# ログで起動確認
sudo journalctl -u line-bot-vps -f
```

**確認ポイント**:
```
✅ CloudLLMProvider初期化完了
✅ MySQLManager初期化完了
✅ LearningLogSystemMySQL初期化完了
✅ SessionManagerMySQL初期化完了
✅ PromptManager初期化完了
✅ LineNotify初期化完了
✅ AutoCharacterSelector初期化完了
```

---

### 4. リッチメニューの登録（LINE Developers）

#### 4.1 リッチメニュー画像をアップロード

1. LINE Developers コンソールにアクセス
   - https://developers.line.biz/console/

2. 「牡丹プロジェクト」チャネルを選択

3. 「Messaging API」→「リッチメニュー」を開く

4. 「作成」をクリック

5. 画像をアップロード:
   - ファイル: `assets/richmenu_auto_mode.png`

#### 4.2 リッチメニュー設定

**基本情報**:
- タイトル: `牡丹プロジェクト - 自動切り替えモード`
- 表示期間: `常に表示`
- メニューバーのテキスト: `メニューを開く`

**テンプレート**: `6分割（3x2）`

**アクション設定**:

```json
{
  "size": {
    "width": 2500,
    "height": 1686
  },
  "selected": true,
  "name": "牡丹プロジェクト - 自動切り替えモード",
  "chatBarText": "メニューを開く",
  "areas": [
    {
      "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
      "action": {"type": "postback", "label": "自動", "data": "action=set_mode&mode=auto"}
    },
    {
      "bounds": {"x": 833, "y": 0, "width": 834, "height": 843},
      "action": {"type": "postback", "label": "FB", "data": "action=feedback"}
    },
    {
      "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
      "action": {"type": "postback", "label": "規約", "data": "action=terms"}
    },
    {
      "bounds": {"x": 0, "y": 843, "width": 833, "height": 843},
      "action": {"type": "postback", "label": "牡丹", "data": "action=set_mode&mode=botan"}
    },
    {
      "bounds": {"x": 833, "y": 843, "width": 834, "height": 843},
      "action": {"type": "postback", "label": "Kasho", "data": "action=set_mode&mode=kasho"}
    },
    {
      "bounds": {"x": 1667, "y": 843, "width": 833, "height": 843},
      "action": {"type": "postback", "label": "ユリ", "data": "action=set_mode&mode=yuri"}
    }
  ]
}
```

または、`docs/line_richmenu_config.json` をそのままコピー＆ペーストしてください。

#### 4.3 リッチメニューを有効化

1. 作成したリッチメニューの「公開」ボタンをクリック
2. 「デフォルト」に設定

---

## 🧪 動作確認

### 1. 自動モードのテスト

**LINE Bot に送信**:
```
VTuberのトレンドは？
```

**期待される動作**:
- 🎯 牡丹が自動選択される
- 牡丹らしい口調で応答（「マジで」「ヤバ」など）

**LINE Bot に送信**:
```
音楽のトレンドは？
```

**期待される動作**:
- 🎯 Kashoが自動選択される
- Kashoらしい丁寧な口調で応答

---

### 2. モード切り替えのテスト

1. リッチメニューの「🔄 自動」ボタンをタップ

**期待される応答**:
```
✅ 自動モードに設定しました！

これからは、話題に合わせて三姉妹が自動的に応答します。

🌸 牡丹: VTuber、エンタメ
🎵 Kasho: 音楽、オーディオ
📚 ユリ: サブカル、アニメ、ライトノベル

※ 特定のキャラクターと話したい場合は、下のボタンから選んでね！
```

2. リッチメニューの「🌸 牡丹」ボタンをタップ

**期待される応答**:
```
✅ 牡丹に固定しました！
これからは牡丹があなたの質問に答えるよ！

話したいことある？
```

---

### 3. フィードバック機能のテスト

1. リッチメニューの「💬 FB」ボタンをタップ

**期待される応答**:
```
📝 フィードバックをお待ちしています！

以下のような内容をお送りください：
- バグ報告
- 機能要望
- 改善提案
- その他ご意見

次のメッセージでフィードバックを入力してください。
（キャンセルする場合は「キャンセル」と送信）
```

2. フィードバック内容を送信:
```
自動モードがとても便利です！
```

**期待される応答**:
```
✅ フィードバックを受け付けました！
ありがとうございます！

開発者に通知しました。
今後の改善に活かさせていただきます。
```

3. **LINE Notify で開発者に通知が届くことを確認**

---

### 4. 利用規約表示のテスト

1. リッチメニューの「📋 規約」ボタンをタップ

**期待される動作**:
- 利用規約・免責事項が Flex メッセージで表示される

---

## 📊 データベース確認

### フィードバック確認

```bash
ssh -p 443 ubuntu@133.167.93.123

# MySQLに接続（パスワード: cha1me2983）
mysql -u ai_vtuber_user -p kp99_linebotsisters

# フィードバック一覧
SELECT id, user_id, feedback_text, created_at, is_read
FROM feedback
ORDER BY created_at DESC
LIMIT 10;

# 未読フィードバック件数
SELECT COUNT(*) FROM feedback WHERE is_read = FALSE;
```

### ユーザーモード確認

```sql
SELECT user_id, selected_mode, feedback_state, last_message_at
FROM sessions
ORDER BY last_message_at DESC
LIMIT 10;
```

---

## 🔧 トラブルシューティング

### 問題: LINE Notify 通知が届かない

**確認ポイント**:
1. `.env` に `LINE_NOTIFY_TOKEN` が設定されているか
2. トークンが正しいか（再発行して試す）
3. VPS のログを確認:
   ```bash
   sudo journalctl -u line-bot-vps -f | grep "LINE Notify"
   ```

---

### 問題: 自動モードでキャラクターが選択されない

**確認ポイント**:
1. `auto_character_selector.py` のキーワード辞書を確認
2. ログでスコアを確認:
   ```bash
   sudo journalctl -u line-bot-vps -f | grep "自動選択"
   ```
3. デフォルトスコアが低すぎる場合は調整

---

### 問題: リッチメニューが表示されない

**確認ポイント**:
1. LINE Developers コンソールで「デフォルト」に設定されているか
2. リッチメニューが「公開」状態か
3. 画像のサイズが 2500x1686 か

---

## 📚 関連ドキュメント

- **設計書**: `docs/05_design/リッチメニュー自動切り替え_設計書.md`
- **マイグレーションSQL**: `migrations/20251117_add_auto_mode.sql`
- **リッチメニュー設定**: `docs/line_richmenu_config.json`

---

## 🎉 完了！

これで、リッチメニュー自動切り替えモードが本番環境で稼働します。

**次のステップ**:
- ユーザーフィードバックの収集
- 親和性スコアリングの調整
- キーワード辞書の拡充

🤖 **Generated with Claude Code**

Co-Authored-By: Claude <noreply@anthropic.com>
