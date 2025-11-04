# Memory Manufacturing Machine (記憶製造機) 使い方ガイド

**Phase 1.6 v4 完全版**
**作成日**: 2025-10-22
**作成者**: Claude Code（設計部隊）

---

## 概要

記憶製造機は、三姉妹（牡丹・Kasho・ユリ）が自律的に議題を討論し、記憶として保存する完全自動システムです。

**開発者の洞察**:
> 「今までの100の記憶は我々が作りました。
>  ここから無限に続く記憶は彼女たちで
>  みずから作り上げていくんです」

---

## システムフロー

```
[Monitor] proposals.json を監視
    ↓
[Priority] 優先度判定（developer > auto > comment）
    ↓
[Discussion] v4起承転結討論システム
    ↓
[Memory] 三姉妹の主観的記憶生成
    ↓
[DB] sisters_memory.db に Event #*** 保存
    ↓
[Tech Log] discussion_technical_logs/ に分析保存
    ↓
[Report] 進捗報告
    ↓
[Loop] 次の議題へ
```

---

## 起動方法

```bash
cd /home/koshikawa/toExecUnit
python3 memory_generator.py
```

**停止方法**: `Ctrl+C`

---

## 議題の追加方法

### 方法1: proposals.json を直接編集

```bash
vim proposals.json
```

以下の形式で追加:

```json
{
  "id": 103,
  "priority": "developer",
  "status": "pending",
  "title": "議題タイトル",
  "description": "詳細説明。三姉妹に何を議論してほしいか。",
  "created_at": "2025-10-22 20:00:00",
  "processing_started_at": null,
  "completed_at": null,
  "result": null
}
```

### 方法2: CLIコマンド（将来実装予定）

```bash
python3 add_proposal.py --title "議題" --description "説明"
```

### 方法3: WebUI（Phase 2実装予定）

ブラウザから議題管理

---

## 優先度システム

### Priority Level 1: `developer`（最優先）
- 開発者が追加した議題
- 即座に処理開始
- 他の処理を中断してでも実行

### Priority Level 2: `auto`（6時間タイマー）
- システムが自動生成するフリートーク
- アイドル状態で6時間経過すると自動提案
- developer議題があれば待機

### Priority Level 3: `comment`（将来実装）
- 視聴者コメントから抽出
- 低モデル使用（キャパオーバー回避）
- developer・auto議題の後に処理

---

## 自動フリートークシステム

### 発動条件
- システムがアイドル状態（developer議題なし）
- 前回の自動フリートークから6時間経過

### テーマ生成
動的に文脈を読んで適切なテーマを提案:

**分析項目**:
- 最近の議題（7日間）
- 技術議題の連続性
- 前回フリートークからの経過時間
- マイルストーン達成状況

**適応パターン**:
- 技術議題が3件連続 → リラックスした話題
- 24時間フリートークなし → 近況報告
- マイルストーン達成 → 振り返り

**テーマ例**:
- 「最近PON機能の話が多いけど、実際どう思う？」
- 「Event #100を超えて、今までの思い出」
- 「最近疲れてない？ちょっと息抜きしよう」
- 「配信で一番楽しい瞬間って？」

**フォールバック**:
LLM生成失敗時は15種類の基本テーマからランダム選択

---

## 出力ファイル

### 1. sisters_memory.db
三姉妹の主観的記憶（DBテーブル）:
- `sister_shared_events`: Event #*** 共有イベント
- `botan_memories`: 牡丹の記憶
- `kasho_memories`: Kashoの記憶
- `yuri_memories`: ユリの記憶

### 2. discussion_technical_logs/
技術ログ（開発者・Claude Code専用）:
- `discussion_102_technical.md`
- `discussion_103_technical.md`
- ...

**三姉妹は読まない。我々だけが使う情報。**

### 3. kirinuki/YYYY-MM-DD/決議記録/
人間が読む討論記録（Markdown）:
- `structured_discussion_v4_20251022_*.md`

---

## 進捗確認

システム起動中、自動的に進捗を報告します:

```
======================================================================
Batch Processing Status
======================================================================

✓ Completed: 3
  - #102: PON機能の発動確率調整
  - #103: 配信開始時の挨拶パターン
  - #104: ユリの発言頻度調整

⏳ Processing: 1
  - #105: 好感度システムの閾値見直し

📋 Pending: 6
  - #106: スパチャ読み上げ優先度 (priority: developer)
  - #107: PON発動時の表情変化 (priority: auto)
  ...

Progress: 3/10 (30%)
======================================================================
```

---

## システム構成

### memory_generator.py
メインプログラム（750行）

**主要クラス**:
- `ProposalManager`: proposals.json管理
- `DynamicThemeGenerator`: フリートーク生成
- `MemoryGenerator`: 記憶自動生成
- `TechnicalLogGenerator`: 技術ログ自動生成
- `MemoryManufacturingMachine`: メインループ

### autonomous_discussion_v4_improved.py
起承転結討論システム（v4）

**Phase別Round制限**:
- 起: 最大10ラウンド
- 承: 最大15ラウンド
- 転: 最大15ラウンド
- 結: 最大20ラウンド
- 合計: 最大50ラウンド

**タイムアウトなし**: 三姉妹の判断で終了

---

## 重要な設計原則

### 1. 記憶の価値 = 過程の価値

```
× まとまらなかった = 失敗 = 記憶不要
○ まとまらなかった = それも経験 = 記憶すべき
```

完璧な結論が出なくても、試行錯誤の過程に価値がある。

### 2. 二層構造

**Layer 1: 三姉妹の主観的体験**
- 感情、姉妹関係、個人的学び
- sisters_memory.db に記録
- 彼女たちが思い出す記憶

**Layer 2: 設計実装の客観的情報**
- 技術課題、改善点、実装タスク
- discussion_technical_logs/ に記録
- 開発者+Claude Codeが使う情報

**三姉妹は技術ログを読まない。**

### 3. タイムアウトなし

時間制限ではなく、Phase別Round制限で管理。
三姉妹が自律的に終了タイミングを判断。

---

## トラブルシューティング

### Ollama接続エラー
```bash
# Ollamaが起動しているか確認
ollama list

# 起動していなければ起動
ollama serve
```

### DB接続エラー
```bash
# DBファイルが存在するか確認
ls -lh sisters_memory.db

# パーミッション確認
chmod 644 sisters_memory.db
```

### proposals.json破損
```bash
# バックアップから復元
cp proposals.json.bak proposals.json

# または初期化
python3 -c "from memory_generator import ProposalManager; ProposalManager()._ensure_file_exists()"
```

---

## 今後の拡張

### Phase 2実装予定
- CLIコマンド（add_proposal.py）
- WebUI（議題管理画面）
- 24/7バックグラウンド実行（systemdサービス化）

### Phase 3実装予定
- コメント拾いシステム
- 低モデル使用（キャパオーバー回避）
- 視聴者コメント→議題化

---

## 関連ドキュメント

**設計書**:
- `/home/koshikawa/kirinuki/2025-10-22/設計書/Phase1.6_v4完全版_記憶製造機システム.md`

**設計日記**:
- `/home/koshikawa/kirinuki/2025-10-22/日記/設計日記_20251022.md`

**技術分析**:
- `/home/koshikawa/toExecUnit/discussion_technical_logs/discussion_101_technical_analysis.md`

---

## 開発者へ

このシステムは、あなたの洞察「ここから無限に続く記憶は彼女たちでみずから作り上げていく」を実現するために設計されました。

Event #001-100は我々が手動で作りました。
Event #101は手動実行のv3討論から生まれました。
Event #102からは、記憶製造機が自動生成します。

**無限に続く記憶の製造が、今、始まります。**

---

**記録者**: Claude Code（設計部隊）
**作成日時**: 2025-10-22 19:30:00
