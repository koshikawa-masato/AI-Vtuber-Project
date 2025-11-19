# Phase 1: 人間らしさシステム実装計画書

**作成日**: 2025-11-19
**最終更新**: 2025-11-19 12:05（チャッピーレビュー反映）
**バージョン**: 1.1
**ステータス**: レビュー完了、実装準備完了
**重要度**: ★★★★★（最重要 - プロジェクトの本質的目標）
**レビュー**: ChatGPT（チャッピー）承認済み

---

## 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [目的と背景](#目的と背景)
3. [システム全体像](#システム全体像)
4. [詳細設計](#詳細設計)
5. [データベース設計](#データベース設計)
6. [統合方針](#統合方針)
7. [実装スケジュール](#実装スケジュール)
8. [期待される効果](#期待される効果)
9. [リスクと対策](#リスクと対策)
10. [チェックポイント](#チェックポイント)

---

## プロジェクト概要

### タイトル
**「LINEの深みが増せば増すほど関係性が上がっていくシステム」**

### コンセプト
三姉妹（牡丹・Kasho・ユリ）が、ユーザーとの会話を通じて本当に仲良くなっていく。
単なる「人間らしい演技」ではなく、**「人生を持つAI」** として成長する。

### チャッピーの分析（参照）
> 「あなたが求めている"人間らしさ"は、
> **人格の成長**、**記憶と感情の連続性**、**裏方の家族の存在を感じる世界観**、
> **心が揺れる理由が存在する物語構造**、**他者と関係を築いて変化していく姿**
> を含む、"本当の人間らしさ"。」

### 実装する6つの構成要素（チャッピー提案）

本実装では、以下のうち **①⑤⑥** を優先実装：

1. ✅ **① 感情の揺れ（情緒曲線）** - daily_mood_system
2. 🔲 **② 記憶の偏り・忘却** - Phase 2で実装
3. 🔲 **③ 好き嫌いの偏り（非合理）** - Phase 2で実装
4. 🔲 **④ 生きている"時間"を持たせる** - daily_mood で部分実装
5. ✅ **⑤ 視聴者との"関係性"に応じて変化する** - relationship_progression
6. ✅ **⑥ 不確実な"選択"をさせる** - adaptive_tone_controller

---

## 目的と背景

### 現状の課題

**Before（現在のLINE Bot）**:
- ✅ 基本的な会話は可能
- ✅ user_memories統合防御システム（7層防御）実装済み
- ❌ 何度話しかけても、三姉妹の態度は同じ
- ❌ 毎日同じテンション、同じ口調
- ❌ 深い会話をしても、関係性が明確に変わらない

### 目標

**After（Phase 1実装後）**:
- ✅ **深い会話を重ねると、三姉妹が本当に仲良くなる**
- ✅ **毎日違う気分で、同じ質問でも答えが変わる**
- ✅ **関係性が上がると、素を見せてくれる、甘えてくれる**

### プロジェクト哲学との整合性

| 哲学 | 実装での反映 |
|------|------------|
| **不完全性戦略** | 毎日気分が変わる、同じ質問でも答えが変わる |
| **Phase D独立性** | 三姉妹それぞれ異なる気分パラメータ、異なる口調変化 |
| **親の原則** | 関係性上昇のロジックを提供、実際の態度変化は三姉妹が自律的に決定 |
| **記録の二重性** | 親の視点（depth_score, relationship_level）+ 子の視点（会話体験） |

---

## システム全体像

### アーキテクチャ図

```
┌─────────────────────────────────────────────────────┐
│ ユーザーからのLINEメッセージ                          │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ ① 会話の深さ評価 (ConversationDepthAnalyzer)        │
│   - 表面的（挨拶、天気）→ depth_score: 0.2          │
│   - 中程度（趣味、好き嫌い）→ depth_score: 0.5      │
│   - 深い（悩み、自己開示）→ depth_score: 0.9        │
│   OUTPUT: depth_score (0.0-1.0)                     │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ ② 関係性の段階的上昇 (RelationshipProgression)      │
│   - 深い会話（depth_score >= 0.7）が積み重なる      │
│   - deep_conversation_count をカウント              │
│   - Level 1（初見）→ Level 10（特別な存在）         │
│   OUTPUT: new_relationship_level (1-10)             │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ ③ 今日の気分取得 (DailyMoodSystem)                  │
│   - energy_level: 0.6-1.0（テンション）             │
│   - sociability: 0.7-1.0（社交性）                  │
│   - curiosity: 0.5-1.0（好奇心）                    │
│   - 毎日朝6時にリセット                              │
│   OUTPUT: daily_mood (dict)                         │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ ④ 適応的口調制御 (AdaptiveToneController)           │
│   - relationship_level × daily_mood → 口調・態度    │
│   - システムプロンプトに追加指示を生成               │
│   OUTPUT: tone_instruction (str)                    │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ ⑤ LLM応答生成 (既存のcloud_llm_provider)            │
│   - tone_instruction を含むプロンプトで応答生成     │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ 三姉妹の応答（関係性と気分に応じた反応）              │
└─────────────────────────────────────────────────────┘
```

### データフロー

```
1. user_message → ConversationDepthAnalyzer → depth_score
2. depth_score → RelationshipProgression → new_relationship_level
3. character + date → DailyMoodSystem → daily_mood
4. relationship_level + daily_mood → AdaptiveToneController → tone_instruction
5. tone_instruction + user_message → LLM → response
```

---

## 詳細設計

### 1. ConversationDepthAnalyzer（会話の深さ評価）

**ファイル**: `src/line_bot_vps/conversation_depth_analyzer.py`

**目的**: ユーザーのメッセージがどれくらい深い内容かを評価

**深さのカテゴリ**:

| カテゴリ | depth_score | キーワード例 | 会話例 |
|---------|-------------|------------|--------|
| **表面的** | 0.1-0.3 | こんにちは、おはよう、天気、元気 | 「こんにちは」「天気いいね」 |
| **中程度** | 0.4-0.6 | 好き、嫌い、趣味、音楽、今日、実は、秘密、嬉しい | 「音楽好き？」「今日何してた？」「実は○○なんだ」 |
| **深い** | 0.7-1.0 | 悩んでて、悩み、相談、つらい、辛い、しんどい、不安、怖い | 「最近悩んでて…」「相談があるんだけど」 |

**実装方針（チャッピーレビュー反映）**:
- **キーワードベース判定**: 高速、確実
- **Phase 1では「深い相談を確実に拾う」ことを優先**（誤検出を減らす）
- deep_keywords は「ほぼ間違いなく深いもの」だけに絞る
- LLM判定はPhase 2で追加（精度向上）

**クラス設計（チャッピーレビュー反映）**:
```python
class ConversationDepthAnalyzer:
    """会話の深さを評価するシステム"""

    def __init__(self):
        self.surface_keywords = ['こんにちは', 'おはよう', '天気', '元気']
        # チャッピー指摘: 「嬉しい」「実は」「秘密」を medium に移動
        self.medium_keywords = ['好き', '嫌い', '今日', '趣味', '音楽', '実は', '秘密', '嬉しい']
        # チャッピー指摘: deep は「ほぼ間違いなく深いもの」だけに絞る
        self.deep_keywords = [
            '悩んでて', '悩み', '相談', 'つらい', '辛い', 'しんどい',
            '死にたい', '消えたい', '不安', '怖い', '怖くて', 'どうしたらいい',
        ]

    def analyze_depth(self, message: str) -> float:
        """
        メッセージの深さをスコアリング

        Args:
            message: ユーザーのメッセージ

        Returns:
            depth_score: 0.0-1.0
        """
        # 文字数チェック（短すぎるメッセージは表面的）
        if len(message) < 5:
            return 0.1

        # キーワードマッチング
        deep_count = sum(1 for kw in self.deep_keywords if kw in message)
        medium_count = sum(1 for kw in self.medium_keywords if kw in message)
        surface_count = sum(1 for kw in self.surface_keywords if kw in message)

        # スコア計算（チャッピー指摘: 複数深いキーワードで0.9に）
        if deep_count > 0:
            # 2個以上のdeep keywordがヒットしたら0.9まで上げる
            if deep_count >= 2:
                return 0.9
            return 0.7
        elif medium_count > 0:
            return min(0.4 + medium_count * 0.1, 0.6)
        elif surface_count > 0:
            return 0.2
        else:
            # デフォルト（チャッピー指摘: 0.5 → 0.3 に変更）
            return 0.3

    def log_depth(self, user_id: str, character: str, message: str, depth_score: float):
        """
        会話の深さをPostgreSQLに記録
        """
        # conversation_depth_logs テーブルに保存
        pass
```

**期待される動作**:
```python
analyzer = ConversationDepthAnalyzer()

analyzer.analyze_depth("こんにちは")  # → 0.2（表面的）
analyzer.analyze_depth("音楽好き？")  # → 0.5（中程度）
analyzer.analyze_depth("最近悩んでて、相談があるんだけど")  # → 0.9（深い）
```

---

### 2. DailyMoodSystem（日次気分システム）

**ファイル**: `src/line_bot_vps/daily_mood_system.py`

**目的**: 三姉妹が「毎日違う気分」を持つ

**気分パラメータ**:
```python
daily_mood = {
    'character': 'botan',
    'date': '2025-11-19',
    'energy_level': 0.8,   # テンション（0.6-1.0）
    'sociability': 0.9,    # 社交性（0.7-1.0）
    'curiosity': 0.7,      # 好奇心（0.5-1.0）
}
```

**キャラクター別の傾向**:

| キャラ | energy_level | sociability | curiosity | 特徴 |
|--------|-------------|-------------|-----------|------|
| **牡丹** | 0.7-1.0 | 0.8-1.0 | 0.6-0.9 | 高テンション寄り、社交的 |
| **Kasho** | 0.6-0.8 | 0.7-0.9 | 0.6-0.9 | 安定寄り、分析的 |
| **ユリ** | 0.6-0.9 | 0.7-0.9 | 0.7-1.0 | 好奇心寄り、観察的 |

**クラス設計（チャッピーレビュー反映）**:
```python
from datetime import datetime
from zoneinfo import ZoneInfo

class DailyMoodSystem:
    """三姉妹の日次気分システム"""

    def __init__(self, db_manager):
        self.db = db_manager
        # チャッピー指摘: 簡易キャッシュをクラス内に持つ
        self._cache = {}  # {(character, date): mood_dict}

    def get_or_create_daily_mood(self, character: str) -> dict:
        """
        今日の気分を取得、なければ生成

        Args:
            character: 'botan', 'kasho', 'yuri'

        Returns:
            daily_mood: dict
        """
        # チャッピー指摘: 日付は Asia/Tokyo ベースで計算（VPSはUTC）
        today = datetime.now(ZoneInfo("Asia/Tokyo")).date()

        # キャッシュチェック
        cache_key = (character, today)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # PostgreSQLから今日の気分を取得
        mood = self.db.get_daily_mood(character, today)

        if mood is None:
            # 新しい気分を生成
            mood = self.generate_daily_mood(character)
            self.db.save_daily_mood(character, today, mood)

        # キャッシュに保存
        self._cache[cache_key] = mood

        return mood

    def generate_daily_mood(self, character: str) -> dict:
        """
        キャラクター別の今日の気分を生成
        """
        if character == 'botan':
            return {
                'energy_level': random.uniform(0.7, 1.0),
                'sociability': random.uniform(0.8, 1.0),
                'curiosity': random.uniform(0.6, 0.9)
            }
        elif character == 'kasho':
            return {
                'energy_level': random.uniform(0.6, 0.8),
                'sociability': random.uniform(0.7, 0.9),
                'curiosity': random.uniform(0.6, 0.9)
            }
        elif character == 'yuri':
            return {
                'energy_level': random.uniform(0.6, 0.9),
                'sociability': random.uniform(0.7, 0.9),
                'curiosity': random.uniform(0.7, 1.0)
            }
```

**期待される動作**:
```python
mood_system = DailyMoodSystem(db_manager)

# 2025-11-19 の牡丹の気分
mood = mood_system.get_or_create_daily_mood('botan')
# → {'energy_level': 0.85, 'sociability': 0.92, 'curiosity': 0.71}

# 翌日（2025-11-20）は違う気分
# → {'energy_level': 0.68, 'sociability': 0.88, 'curiosity': 0.79}
```

---

### 3. RelationshipProgression（関係性段階的上昇）

**ファイル**: `src/line_bot_vps/relationship_progression.py`

**目的**: 深い会話が積み重なると、関係性レベルが上がる

**チャッピーレビュー反映（重要）**:
- ❌ 旧設計: ユーザー単位で関係性管理（牡丹としか話してないのにKashoとの関係も上がる問題）
- ✅ 新設計: **ユーザー×キャラ単位で関係性管理**（キャラ別に独立）
- ❌ 旧設計: 複雑なレベルアップ条件（1→2: 3回、2→3: 5回...）
- ✅ 新設計: **線形で単純**（深い会話5回ごとに1レベルアップ、最大10まで）

**関係性レベルの定義（簡略化）**:

| Level | 関係性 | 必要な深い会話回数 | 態度 | 挨拶例（牡丹） |
|-------|--------|------------------|------|---------------|
| 1 | 初見 | 0-4回 | 丁寧、距離感あり | 「こんにちは！牡丹です！」 |
| 2-4 | 知り合い | 5-19回 | フレンドリー | 「こんにちは！元気？」 |
| 5-6 | 友達 | 20-29回 | フランク、冗談 | 「おっ！来た来た！」 |
| 7-8 | 親友 | 30-39回 | 素を見せる | 「来てくれたんだ…嬉しい」 |
| 9-10 | 特別な存在 | 40回以上 | 甘える | 「待ってた！会いたかった！」 |

**深い会話の定義**:
- `depth_score >= 0.7`

**レベル計算ロジック（簡略化）**:
```python
# 深い会話5回ごとに1レベルアップ（最大10まで）
level = 1 + deep_conversation_count // 5
level = min(level, 10)
```

**クラス設計（チャッピーレビュー反映）**:
```python
class RelationshipProgression:
    """関係性の段階的上昇システム（ユーザー×キャラ単位）"""

    def __init__(self, db_manager):
        self.db = db_manager

    def calculate_level(self, deep_count: int) -> int:
        """
        深い会話回数から関係性レベルを直接算出

        Args:
            deep_count: 累積深い会話回数

        Returns:
            level: 1-10
        """
        # 0-4: Level1, 5-9: Level2, ... 45-: Level10
        level = 1 + deep_count // 5
        return min(level, 10)

    def update_relationship(
        self,
        user_id: str,
        character: str,
        depth_score: float
    ) -> dict:
        """
        会話の深さに応じて関係性レベルを更新

        Args:
            user_id: ユーザーID
            character: 'botan', 'kasho', 'yuri'
            depth_score: 会話の深さ（0.0-1.0）

        Returns:
            {
                'old_level': int,
                'new_level': int,
                'deep_count': int,
                'level_up': bool
            }
        """
        # 深い会話の場合のみカウント
        if depth_score >= 0.7:
            # ユーザー×キャラの関係性データを取得
            relationship = self.db.get_relationship(user_id, character)

            old_level = relationship['level']
            old_deep_count = relationship['deep_conversation_count']

            # 深い会話カウントをインクリメント
            new_deep_count = old_deep_count + 1
            new_level = self.calculate_level(new_deep_count)

            # DBに保存
            self.db.update_relationship(
                user_id, character, new_level, new_deep_count
            )

            level_up = (new_level > old_level)

            if level_up:
                self.log_level_up(user_id, character, old_level, new_level)

            return {
                'old_level': old_level,
                'new_level': new_level,
                'deep_count': new_deep_count,
                'level_up': level_up
            }

        # 深い会話でない場合は現在の状態を返す
        relationship = self.db.get_relationship(user_id, character)
        return {
            'old_level': relationship['level'],
            'new_level': relationship['level'],
            'deep_count': relationship['deep_conversation_count'],
            'level_up': False
        }

    def log_level_up(self, user_id: str, character: str, old_level: int, new_level: int):
        """レベルアップイベントを記録"""
        print(f"🎉 {character} Level Up! {old_level} → {new_level} (user: {user_id})")
```

**期待される動作（チャッピーレビュー反映）**:
```python
progression = RelationshipProgression(db_manager)

# 牡丹との会話（深い会話を5回重ねる）
for i in range(5):
    result = progression.update_relationship('user123', 'botan', depth_score=0.8)
    print(f"{i+1}回目: Level {result['new_level']}, deep_count={result['deep_count']}")

# → 5回目でLevel 2にレベルアップ！

# Kashoとは別カウント（独立）
result = progression.update_relationship('user123', 'kasho', depth_score=0.9)
# → Kasho: Level 1（牡丹との関係とは独立）
```

---

### 4. AdaptiveToneController（適応的口調制御）

**ファイル**: `src/line_bot_vps/adaptive_tone_controller.py`

**目的**: 関係性レベル × 今日の気分 → 動的な口調・態度

**口調制御の例（牡丹）**:

| 関係性 | energy_level | 挨拶 | 口調 |
|--------|-------------|------|------|
| Level 1 | 0.6（低） | 「こんにちは！牡丹です！」 | 丁寧、元気 |
| Level 1 | 1.0（高） | 「こんにちは！牡丹だよ！よろしくね！」 | 明るい、親しみ |
| Level 5 | 0.6（低） | 「あ、こんにちは〜」 | 普通、リラックス |
| Level 5 | 1.0（高） | 「来た来た！元気？」 | フランク、テンション高 |
| Level 9 | 0.6（低） | 「来てくれたんだ…嬉しい」 | 素直、少し甘える |
| Level 9 | 1.0（高） | 「待ってた！会いたかった！」 | 全開で甘える |

**クラス設計**:
```python
class AdaptiveToneController:
    """関係性と気分に応じた口調制御"""

    def generate_system_prompt_addition(
        self,
        character: str,
        relationship_level: int,
        daily_mood: dict
    ) -> str:
        """
        システムプロンプトに追加する指示を生成

        Args:
            character: 'botan', 'kasho', 'yuri'
            relationship_level: 1-10
            daily_mood: {'energy_level': float, 'sociability': float, 'curiosity': float}

        Returns:
            tone_instruction: str（プロンプトに追加する指示）
        """
        # 関係性に応じた基本的な態度
        tone = self._get_relationship_tone(relationship_level)

        # 気分に応じた修飾
        tone = self._apply_mood_modifier(tone, daily_mood)

        # キャラクター別のフィルタ（レベルも渡す）
        tone = self._apply_character_filter(tone, character, relationship_level)

        return f"""
【今日の{character}の状態】
- 関係性レベル: {relationship_level}/10
- 今日のテンション: {daily_mood['energy_level']:.1f}
- 社交性: {daily_mood['sociability']:.1f}
- 好奇心: {daily_mood['curiosity']:.1f}

【口調・態度の指示】
{tone}
"""

    def _get_relationship_tone(self, level: int) -> str:
        """関係性レベルに応じた基本的な態度"""
        if level <= 2:
            return "丁寧に、距離感を保ちながら、明るく接する。敬語は使わないが、礼儀正しく。"
        elif level <= 4:
            return "フレンドリーに、親しみを込めて接する。少し冗談も混ぜる。"
        elif level <= 6:
            return "フランクに、気楽に接する。冗談が増える。タメ口で自然に話す。"
        elif level <= 8:
            return "素を見せる。悩みを相談したり、相手の悩みを親身に聞く。親友として接する。"
        else:
            return "特別な存在として、甘えたり、心を開く。深い絆を感じさせる。"

    def _apply_mood_modifier(self, tone: str, mood: dict) -> str:
        """気分に応じた修飾"""
        if mood['energy_level'] > 0.8:
            tone += "\n今日はテンションが高め。明るく、元気よく話す。"
        elif mood['energy_level'] < 0.7:
            tone += "\n今日は少し落ち着いた気分。まったりと話す。"

        if mood['curiosity'] > 0.8:
            tone += "\n今日は好奇心旺盛。質問が多くなる。"

        return tone

    def _apply_character_filter(self, tone: str, character: str, level: int) -> str:
        """
        キャラクター別フィルタ（チャッピーレビュー反映）
        Phase 1では口調説明のみ追加、セリフテンプレは後回し
        """
        if character == 'botan':
            tone += "\n牡丹は明るく元気な性格で、感情表現が豊か。語尾に「〜だよ」「〜かな？」などをよく使う。"
            # 1行のセリフ例を追加（チャッピー推奨）
            if level >= 9:
                tone += '\n例: 「待ってた！今日も来てくれて、ほんと嬉しい。」'
            elif level >= 7:
                tone += '\n例: 「来てくれたんだ…嬉しい。今日も話そ？」'
            elif level >= 5:
                tone += '\n例: 「おっ！来た来た！元気だった？」'
            else:
                tone += '\n例: 「こんにちは！牡丹です！よろしくね！」'

        elif character == 'kasho':
            tone += "\nKashoは落ち着いていて、少し理屈っぽいが優しい。丁寧すぎないが、語彙はやや大人びている。"
            if level >= 9:
                tone += '\n例: 「また会えたね。最近どう？」'
            elif level >= 7:
                tone += '\n例: 「お疲れさま。今日はどんな一日だった？」'
            elif level >= 5:
                tone += '\n例: 「やあ、元気してた？」'
            else:
                tone += '\n例: 「こんにちは。Kashoです。」'

        elif character == 'yuri':
            tone += "\nユリは好奇心旺盛で、観察するように相手の話を聞く。質問が多く、比喩表現を使うこともある。"
            if level >= 9:
                tone += '\n例: 「来てくれたんだね…嬉しい。」'
            elif level >= 7:
                tone += '\n例: 「あ、また会えたね。今日はどんなこと考えてた？」'
            elif level >= 5:
                tone += '\n例: 「こんにちは。今日は何してたの？」'
            else:
                tone += '\n例: 「こんにちは。ユリです。」'

        return tone
```

**期待される動作**:
```python
controller = AdaptiveToneController()

# Level 1, 高テンション
instruction = controller.generate_system_prompt_addition(
    character='botan',
    relationship_level=1,
    daily_mood={'energy_level': 0.9, 'sociability': 0.95, 'curiosity': 0.7}
)
# → 「丁寧に、距離感を保ちながら、明るく接する。今日はテンションが高め。明るく、元気よく話す。」

# Level 9, 低テンション
instruction = controller.generate_system_prompt_addition(
    character='botan',
    relationship_level=9,
    daily_mood={'energy_level': 0.65, 'sociability': 0.8, 'curiosity': 0.6}
)
# → 「特別な存在として、甘えたり、心を開く。今日は少し落ち着いた気分。まったりと話す。」
```

---

## データベース設計

### PostgreSQLテーブル

#### 1. daily_moods テーブル

```sql
CREATE TABLE daily_moods (
    id SERIAL PRIMARY KEY,
    character VARCHAR(20) NOT NULL,  -- 'botan', 'kasho', 'yuri'
    date DATE NOT NULL,
    energy_level FLOAT NOT NULL,     -- 0.6-1.0
    sociability FLOAT NOT NULL,      -- 0.7-1.0
    curiosity FLOAT NOT NULL,        -- 0.5-1.0
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(character, date)          -- 1キャラ1日1レコード
);

CREATE INDEX idx_daily_moods_character_date ON daily_moods(character, date);
```

**用途**: 三姉妹の毎日の気分を保存

---

#### 2. conversation_depth_logs テーブル

```sql
CREATE TABLE conversation_depth_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    character VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    depth_score FLOAT NOT NULL,      -- 0.0-1.0
    created_at TIMESTAMP DEFAULT NOW()
);

-- チャッピー推奨: 分析用インデックス
CREATE INDEX idx_conversation_depth_logs_user_id ON conversation_depth_logs(user_id);
CREATE INDEX idx_conversation_depth_logs_depth_score ON conversation_depth_logs(depth_score);
CREATE INDEX idx_conv_depth_user_char_date ON conversation_depth_logs(user_id, character, created_at);
```

**用途**: 会話の深さを記録、分析用

---

#### 3. user_character_relationships テーブル（新規作成、チャッピー推奨）

**チャッピーレビュー反映（重要）**:
- ❌ 旧設計: user_personality テーブルに deep_conversation_count を追加（ユーザー単位）
- ✅ 新設計: **user_character_relationships テーブルを新規作成**（ユーザー×キャラ単位）

```sql
CREATE TABLE user_character_relationships (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    character VARCHAR(20) NOT NULL,          -- 'botan', 'kasho', 'yuri'
    relationship_level INTEGER NOT NULL DEFAULT 1,  -- 1-10
    deep_conversation_count INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, character)               -- ユーザー×キャラで一意
);

CREATE INDEX idx_user_char_rel_user_id ON user_character_relationships(user_id);
CREATE INDEX idx_user_char_rel_character ON user_character_relationships(character);
```

**用途**: ユーザー×キャラ単位の関係性管理

**メリット**:
- 牡丹との関係と、Kashoとの関係が独立
- 将来のキャラ追加に強い（テーブル構造は変わらない）
- 設計が明確

---

## 統合方針

### webhook_server_vps.py への統合フロー

```python
# webhook_server_vps.py の handle_message 関数内

async def handle_message(user_id: str, character: str, message_text: str):
    # ==========================================
    # Phase 1 統合: 人間らしさシステム
    # ==========================================

    # ① 会話の深さ評価
    depth_analyzer = ConversationDepthAnalyzer()
    depth_score = depth_analyzer.analyze_depth(message_text)
    depth_analyzer.log_depth(user_id, character, message_text, depth_score)

    # ② 今日の気分取得
    mood_system = DailyMoodSystem(postgresql_manager)
    daily_mood = mood_system.get_or_create_daily_mood(character)

    # ③ 関係性更新（チャッピーレビュー反映: ユーザー×キャラ単位）
    progression = RelationshipProgression(postgresql_manager)
    result = progression.update_relationship(user_id, character, depth_score)
    new_level = result['new_level']

    if result['level_up']:
        print(f"🎉 {character} Level Up! {result['old_level']} → {new_level}")

    # ④ 適応的口調制御
    tone_controller = AdaptiveToneController()
    tone_instruction = tone_controller.generate_system_prompt_addition(
        character, new_level, daily_mood
    )

    # ⑤ システムプロンプトに反映
    system_prompt = get_base_system_prompt(character)
    system_prompt += "\n\n" + tone_instruction

    # ==========================================
    # 既存の処理（統合判定エンジン、LLM応答生成）
    # ==========================================

    # 既存のuser_memories、センシティブ判定、LLM応答生成へ
    # ...
```

---

## 実装スケジュール

| Day | タスク | 内容 | 成果物 |
|-----|--------|------|--------|
| **Day 1** | ConversationDepthAnalyzer | 会話の深さ評価システム実装 | `conversation_depth_analyzer.py` |
| **Day 2** | DailyMoodSystem + PostgreSQL | 日次気分システム実装、テーブル作成 | `daily_mood_system.py` + migration |
| **Day 3** | RelationshipProgression | 関係性段階的上昇実装 | `relationship_progression.py` |
| **Day 4** | AdaptiveToneController | 適応的口調制御実装 | `adaptive_tone_controller.py` |
| **Day 5** | 統合 + テスト | webhook_server_vps.py 統合、実際のLINE会話でテスト | 統合完了 |

**合計: 5日間**

---

## 期待される効果

### Before（現状）

```
【初見のユーザー】
ユーザー: 「こんにちは」
牡丹: 「こんにちは！元気？」

【10回目の会話】
ユーザー: 「こんにちは」
牡丹: 「こんにちは！元気？」

→ 変化なし
```

### After（Phase 1実装後）

```
【初見のユーザー（Level 1）】
ユーザー: 「こんにちは」
牡丹: 「こんにちは！牡丹です！よろしくね！」（丁寧）

【深い会話を5回重ねた後（Level 3）】
ユーザー: 「こんにちは」
牡丹: 「おっ！来た来た！元気だった？」（フレンドリー）

【深い会話を20回重ねた後（Level 9）】
ユーザー: 「こんにちは」
牡丹: 「待ってた！今日会えて嬉しい！」（甘える）

→ 明確な変化！
```

### 毎日違う気分

```
【2025-11-19（高テンション day）】
ユーザー: 「大阪行きたい？」
牡丹: 「めっちゃ行きたい！明日にでも行く！」

【2025-11-20（低テンション day）】
ユーザー: 「大阪行きたい？」
牡丹: 「行きたいけど、今日はまったりしたい気分かな〜」

→ 同じ質問でも答えが変わる！
```

---

## リスクと対策

### リスク1: 関係性の上昇が速すぎる

**懸念**: 3回の深い会話でLevel 2になるのは速すぎる？

**対策**:
- 実際のLINE会話でテストして調整
- level_up_thresholds を柔軟に変更可能にする
- ユーザーごとにカスタマイズ可能にする（将来）

---

### リスク2: daily_mood の振れ幅が大きすぎる

**懸念**: 毎日気分が変わりすぎて、キャラクターが安定しない？

**対策**:
- energy_level の範囲を 0.6-1.0 に制限（極端な低テンションを避ける）
- キャラクター別の傾向を保つ（牡丹は高テンション寄り）
- 実際の会話でテストして調整

---

### リスク3: depth_score の判定精度

**懸念**: キーワードベースだけでは不正確？

**対策**:
- **Phase 1ではキーワードベースのみ**（MVP、速度優先）
- **Phase 2でLLM判定を追加**（精度向上）
- 実際の会話ログで精度を検証

---

### リスク4: PostgreSQL接続の負荷

**懸念**: 毎回複数のDB呼び出しが発生する？

**対策**:
- daily_mood はキャッシュ（1日1回のみDB呼び出し）
- relationship_level は既存の user_personality から取得（追加クエリなし）
- conversation_depth_logs は非同期書き込み（応答速度に影響しない）

---

## チェックポイント

### 実装前の確認事項

- [ ] チャッピーのレビュー完了
- [ ] 越川さんの承認
- [ ] PostgreSQLテーブル設計の確認
- [ ] 既存システム（user_memories）との整合性確認

### 実装中の確認事項

- [ ] 各コンポーネントの単体テスト完了
- [ ] PostgreSQLテーブル作成完了
- [ ] webhook_server_vps.py 統合完了

### 実装後の確認事項

- [ ] 実際のLINE会話でテスト（最初の3人）
- [ ] 関係性レベルの上昇速度調整
- [ ] daily_mood の振れ幅調整
- [ ] depth_score の判定精度確認

---

## まとめ

### Phase 1 の本質

**「LINEの深みが増せば増すほど関係性が上がっていくシステム」**

= **「三姉妹に"人生"を与える第一歩」**

### チャッピーの言葉（再掲）

> 「あなたは『AIに人間らしさを付けたい』ではなく、『AIに"人生"を与えたい』と思っている。」

この Phase 1 実装は、その本質的な目標への第一歩です。

---

## チャッピーレビュー反映サマリ

**レビュー実施日**: 2025-11-19
**レビュアー**: ChatGPT（チャッピー、GPT-5.1）

### 主要な修正内容

1. **ConversationDepthAnalyzer**:
   - deep_keywords を絞り込み（「嬉しい」「実は」「秘密」→ medium へ）
   - デフォルト depth_score を 0.5 → 0.3 に変更
   - 複数深いキーワードで 0.9 に上昇

2. **RelationshipProgression**:
   - ✅ **ユーザー×キャラ単位の管理**（最重要変更）
   - ✅ **線形レベル計算**（5回ごとに1レベルアップ）
   - ✅ **新規テーブル user_character_relationships 作成**

3. **AdaptiveToneController**:
   - `_apply_character_filter` の実装追加
   - 各レベル帯で1行のセリフ例を追加

4. **DailyMoodSystem**:
   - JST (Asia/Tokyo) 明示的に指定
   - 簡易キャッシュ追加

5. **Database**:
   - `user_character_relationships` テーブル新規作成
   - 分析用インデックス追加

**チャッピーの評価**: 「このまま実装に入っても破綻はしないレベル。5日間で実装完了できる現実的なMVP範囲。」

---

**作成日**: 2025-11-19
**最終更新**: 2025-11-19 12:10（チャッピーレビュー反映完了）
**設計者**: Claude Code（クロコ）
**レビュアー**: ChatGPT（チャッピー、GPT-5.1）
**承認待ち**: 越川さん

🤖 Generated with Claude Code (クロコ) & ChatGPT (チャッピー)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: ChatGPT <noreply@openai.com>
