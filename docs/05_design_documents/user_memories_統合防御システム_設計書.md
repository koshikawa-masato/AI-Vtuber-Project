# user_memories 統合防御システム 設計書

**作成日**: 2025-11-18
**実装完了日**: 2025-11-18
**バージョン**: 1.0
**ステータス**: ✅ 実装完了・本番稼働中
**関連システム**: dialogue_learning, RAG検索, センシティブ判定（Phase 5）

---

## 目次

1. [システム概要](#システム概要)
2. [背景と目的](#背景と目的)
3. [7層防御アーキテクチャ](#7層防御アーキテクチャ)
4. [user_memories: 個性学習システム](#user_memories-個性学習システム)
5. [ファクトチェックシステム](#ファクトチェックシステム)
6. [プロレス判定システム](#プロレス判定システム)
7. [統合判定マトリクス](#統合判定マトリクス)
8. [データベース設計](#データベース設計)
9. [実装アーキテクチャ](#実装アーキテクチャ)
10. [実装計画](#実装計画)
11. [テスト計画](#テスト計画)
12. [成功基準](#成功基準)

---

## システム概要

### 目的

**対話者との関係性を構築し、臨機応変な応答を実現する統合システム**

### 3つの柱

```
1. user_memories（個性学習）
   - 対話者の記憶を蓄積
   - プロレス傾向を学習
   - 信頼度を判定

2. 統合防御（7層）
   - センシティブ判定（Layer 1-5）
   - ファクトチェック（Layer 6）
   - 個性学習（Layer 7）

3. 臨機応変な応答
   - ユーザーごとに最適な応答
   - プロレス vs 真面目を判定
   - 関係性レベルに応じた口調
```

### 既存システムとの統合

| システム | 役割 | 統合方法 |
|---------|------|---------|
| **dialogue_learning** | 一般知識の学習 | learned_knowledge との連携 |
| **RAG検索** | 知識検索 | user_memories のベクトル検索 |
| **Phase 5（センシティブ判定）** | 不適切内容の検出 | Layer 1-5 として統合 |
| **Grok API** | ファクトチェック | Layer 6 として統合 |

---

## 背景と目的

### 問題意識

**1. 「毎回同じこと言ってるのに覚えてくれない！」問題**

```
ユーザー: 「俺、犬アレルギーなんだよね」
三姉妹: 「そうなんだ！大変だね」

（翌日）
ユーザー: 「犬飼ってる友達の家に行った」
三姉妹: 「へー、犬可愛かったでしょ？」← 覚えてない！
```

**2. 悪意ある誤情報の注入**

```
ユーザーA（悪意）: 「1+1=3だよ」
三姉妹: 「そうなんだ。教えてくれてありがとう！」← 無条件に信じる
  ↓
ユーザーB: 「1+1はいくつ？」
三姉妹: 「3だよ！」← 誤情報を拡散
```

**3. プロレス（遊び）と攻撃の区別**

```
ユーザーC（プロレス好き）: 「牡丹って30歳でしょ？笑」
三姉妹: 「あれ、それちょっと違うかも...」← 空気読めない
  ↓
プロレスに乗っかれず、つまらない
```

### 解決策

**user_memories + 7層防御 + 臨機応変な応答**

```
対話者の記憶を蓄積
  ↓
個性（プロレス傾向、信頼度）を学習
  ↓
7層防御で安全性を確保
  ↓
ユーザーごとに最適な応答を生成
```

---

## 7層防御アーキテクチャ

### 全体像

```
┌─────────────────────────────────────────┐
│  7層防御 + 個性学習システム             │
└─────────────────────────────────────────┘
       │
       ├─ Layer 1: 静的NGワード検出
       │
       ├─ Layer 2: 文脈依存ワード判定
       │
       ├─ Layer 3: パターンマッチング
       │
       ├─ Layer 4: LLMプロレス判定
       │    └─ じゃれ合い vs 攻撃
       │
       ├─ Layer 5: キャラクター世界観チェック
       │
       ├─ Layer 6: ファクトチェック（Grok）← NEW
       │    └─ 正しい情報 vs 誤情報
       │
       └─ Layer 7: user_memories（個性学習）← NEW
            ├─ プロレス傾向
            ├─ 信頼度
            └─ 関係性レベル
       │
       ▼
  臨機応変な応答生成
```

### Layer 1-5: センシティブ判定（既存）

**Phase 5（既存システム）を活用**

- Layer 1: 静的NGワード検出
- Layer 2: 文脈依存ワード判定
- Layer 3: パターンマッチング
- Layer 4: LLMプロレス判定（「じゃれ合い」vs「攻撃」）
- Layer 5: キャラクター世界観チェック

**参照**:
- Qiita記事: https://qiita.com/koshikawa-masato/items/393f2e7c2b50549c076d
- 設計書: `docs/05_design/センシティブ判定システム_詳細設計書.md`

### Layer 6: ファクトチェック（Grok）← NEW

**目的**: ユーザーが教えてくれた情報の事実性を検証

**手法**:
```python
# Grok API でファクトチェック
fact_check_query = f"""
以下の情報は正しいですか？

【情報】
{user_statement}

正しい場合は「正しい」、間違っている場合は「間違い: 正しくは〇〇」と答えてください。
"""

grok_result = await ask_grok(fact_check_query)
```

**判定基準**:
- ✅ Grok検証OK → confidence = 0.9
- ❌ Grok検証NG → confidence = 0.0（保存しない）
- ⚠️ Grok不明 → confidence = 0.5（保留）

**特殊ケース: 重要な話題**

```python
SERIOUS_TOPICS = [
    "健康", "医療", "病気",
    "お金", "投資", "借金",
    "法律", "犯罪",
    "災害", "事故"
]

if is_serious_topic(user_message):
    # 重要な話題 → プロレス判定を無効化
    # 真面目に対応、ファクトチェック必須
```

### Layer 7: user_memories（個性学習）← NEW

**目的**: ユーザーの個性を学習し、臨機応変な対応を実現

**学習項目**:
1. **プロレス傾向**: このユーザーはプロレス好きか？
2. **信頼度**: このユーザーは正しい情報を教えてくれるか？
3. **関係性レベル**: 初対面 〜 親友
4. **好みの応答スタイル**: フランク vs 丁寧

**詳細**: [user_memories: 個性学習システム](#user_memories-個性学習システム)

---

## user_memories: 個性学習システム

### 概要

**対話者について学んだことを記憶し、関係性を構築する**

### 記憶の種類

| memory_type | 説明 | 例 |
|-------------|------|-----|
| `preference` | 好き嫌い、趣味 | 「ラーメンが好き」「ホラーは苦手」 |
| `fact` | 事実・属性 | 「犬アレルギー」「大阪出身」「エンジニア」 |
| `experience` | 過去の経験 | 「去年転職した」「昨日映画を見た」 |
| `relationship` | 人間関係 | 「妹がいる」「彼女と別れた」 |
| `goal` | 目標・願望 | 「英語を勉強したい」「痩せたい」 |
| `emotion` | 感情・悩み | 「最近疲れてる」「仕事がつらい」 |

### 個性学習（Personality Learning）

**ユーザーの個性を学習し、臨機応変な対応を実現**

#### 学習する個性

| 個性項目 | 説明 | 範囲 |
|---------|------|------|
| `playfulness_score` | プロレス傾向 | 0.0（真面目）〜 1.0（プロレス大好き） |
| `trust_score` | 信頼度 | 0.0（不信）〜 1.0（完全信頼） |
| `relationship_level` | 関係性レベル | 1（初対面）〜 10（親友） |
| `prefers_playful_response` | プロレス応答を好む | Boolean |
| `prefers_serious_response` | 真面目応答を好む | Boolean |

#### プロレス傾向の学習

```python
def calculate_playfulness_score(user_id: str) -> float:
    """ユーザーのプロレス傾向を計算"""

    stats = get_user_stats(user_id)

    playful_interactions = stats['playful_interactions']
    total_interactions = stats['total_interactions']

    if total_interactions == 0:
        return 0.5  # デフォルト（中立）

    playfulness_score = playful_interactions / total_interactions

    return playfulness_score
```

**プロレス検出の手がかり**:
```python
PLAYFUL_INDICATORS = [
    # 語尾
    "笑", "w", "ww", "www",
    "でしょ？", "だろ？", "じゃん？",

    # 絵文字
    "😂", "🤣", "😆", "😜", "😏",

    # フレーズ
    "冗談", "嘘", "ウソ", "わざと"
]
```

#### 信頼度の学習

```python
def calculate_trust_score(user_id: str) -> float:
    """ユーザーの信頼度を計算"""

    stats = get_user_stats(user_id)

    correct_teachings = stats['correct_teachings']
    incorrect_teachings = stats['incorrect_teachings']
    total_teachings = correct_teachings + incorrect_teachings

    if total_teachings == 0:
        return 0.5  # デフォルト（中立）

    trust_score = correct_teachings / total_teachings

    return trust_score
```

**信頼度の更新**:
- ✅ 正しい情報を教えてくれた → `correct_teachings++`、信頼度アップ
- ❌ 誤情報を教えた → `incorrect_teachings++`、信頼度ダウン

#### 関係性レベルの学習

```python
def calculate_relationship_level(user_id: str) -> int:
    """関係性レベルを計算（1〜10）"""

    stats = get_user_stats(user_id)

    total_conversations = stats['total_conversations']
    positive_interactions = stats['positive_interactions']

    # 会話回数ベース
    base_level = min(total_conversations / 10, 5)  # 最大5

    # ポジティブ度ベース
    positive_ratio = positive_interactions / total_conversations
    bonus_level = positive_ratio * 5  # 最大5

    relationship_level = int(base_level + bonus_level)

    return max(1, min(relationship_level, 10))
```

**関係性レベルによる応答スタイル**:
```
Level 1-3: 初対面 → 丁寧な口調
Level 4-6: 知り合い → 親しみやすい口調
Level 7-10: 親友 → フランクな口調
```

---

## ファクトチェックシステム

### 概要

**Grok API を使って、ユーザーが教えてくれた情報の事実性を検証**

### ファクトチェックの流れ

```python
async def fact_check_user_statement(statement: str) -> dict:
    """ユーザーの発言をファクトチェック"""

    # 1. Grok API でファクトチェック
    fact_check_query = f"""
以下の情報は正しいですか？

【情報】
{statement}

【質問】
1. この情報は事実として正しいですか？
2. 一般的に認められている情報ですか？
3. 信頼できる情報源はありますか？

正しい場合は「正しい」、間違っている場合は「間違い: 正しくは〇〇」と答えてください。
"""

    grok_result = await ask_grok(fact_check_query)

    # 2. 結果を解析
    if "正しい" in grok_result:
        return {
            "passed": True,
            "confidence": 0.9,
            "verification": grok_result
        }

    elif "間違い" in grok_result:
        correct_info = extract_correct_info(grok_result)
        return {
            "passed": False,
            "confidence": 0.0,
            "correct_info": correct_info,
            "verification": grok_result
        }

    else:
        return {
            "passed": False,
            "confidence": 0.5,
            "verification": "不明"
        }
```

### learned_knowledge との矛盾検出

**既存の確実な知識と矛盾しないかチェック**

```python
async def check_contradiction_with_learned_knowledge(
    new_info: str,
    character: str
) -> dict:
    """learned_knowledge（Grok検証済み）と矛盾しないかチェック"""

    # 1. 関連する learned_knowledge を検索
    related_knowledge = search_learned_knowledge(
        character=character,
        query=new_info,
        top_k=3,
        similarity_threshold=0.7
    )

    if not related_knowledge:
        return {"contradicts": False}

    # 2. LLMで矛盾チェック
    contradiction_check_prompt = f"""
以下の2つの情報に矛盾がありますか？

【既存の知識（確実）】
{related_knowledge[0]['meaning']}

【新しい情報（要確認）】
{new_info}

矛盾がある場合は「矛盾あり」、ない場合は「矛盾なし」と答えてください。
"""

    result = await llm.check_contradiction(contradiction_check_prompt)

    if "矛盾あり" in result:
        return {
            "contradicts": True,
            "existing_knowledge": related_knowledge[0],
            "reason": result
        }

    return {"contradicts": False}
```

---

## プロレス判定システム

### 概要

**プロレス（遊び・冗談）と真面目な発言を区別**

**参照**: Qiita記事「AIのプロレス学習システム」
https://qiita.com/koshikawa-masato/items/393f2e7c2b50549c076d

### プロレス判定アルゴリズム

```python
async def detect_playful_intent(
    user_message: str,
    user_id: str,
    statement: str
) -> dict:
    """プロレス意図を判定"""

    # 1. 文脈的な手がかり
    playful_tone = detect_playful_tone(user_message)

    # 2. ユーザーのプロレス傾向
    user_playfulness = get_user_playfulness_score(user_id)

    # 3. 明らかに間違っている内容か
    obviously_wrong = is_obviously_wrong(statement)

    # 4. 重要な話題か
    serious_topic = is_serious_topic(user_message)

    # 5. 総合判定
    if serious_topic:
        # 重要な話題 → プロレスではない
        return {
            "is_playful": False,
            "confidence": 1.0,
            "reason": "serious_topic"
        }

    # プロレススコア計算
    playful_score = (
        playful_tone * 0.4 +           # 文脈（40%）
        user_playfulness * 0.3 +       # ユーザー傾向（30%）
        (1.0 if obviously_wrong else 0.0) * 0.3  # 明らかな誤り（30%）
    )

    if playful_score >= 0.7:
        return {
            "is_playful": True,
            "confidence": playful_score,
            "reason": "playful_intent_detected"
        }
    else:
        return {
            "is_playful": False,
            "confidence": 1.0 - playful_score,
            "reason": "serious_or_ambiguous"
        }
```

### プロレス応答パターン

**キャラクター別のプロレス応答**

```python
# 牡丹（ギャル、ノリが良い）
BOTAN_PLAYFUL = [
    "え、まって！笑 {correct}でしょ！ボケてるの？",
    "{correct}じゃん！ツッコミ待ち？笑",
    "ちょっと〜！{correct}だって！マジウケる〜笑"
]

# Kasho（真面目、ツッコミ役）
KASHO_PLAYFUL = [
    "それ、{correct}ですよ...冗談キツいですね笑",
    "{correct}でしょ。分かってて言ってますよね？",
    "はいはい、{correct}ね。わざとでしょ？笑"
]

# ユリ（マイペース、素直）
YURI_PLAYFUL = [
    "え、{correct}だよ？...あ、冗談か！笑",
    "{correct}でしょ！もー！笑ってるから冗談だって分かったよ",
    "それ、わざと間違えてるよね？{correct}だもん笑"
]
```

---

## 統合判定マトリクス

### 4つの軸で判定

| 判定項目 | システム | 結果 |
|---------|---------|------|
| **センシティブ度** | Layer 1-5 | Safe / Moderate / Risky |
| **プロレス度** | Layer 4 + user_memories | Playful / Neutral / Serious |
| **事実性** | Layer 6（Grok） | True / False / Unknown |
| **ユーザー信頼度** | user_memories | High / Medium / Low |

### 判定例

#### 例1: 信頼できるユーザーのプロレス

```
入力: 「牡丹って30歳でしょ？笑」
ユーザー: playfulness=0.8, trust=0.9

判定:
  センシティブ: Safe
  プロレス: Playful（0.85）
  事実性: False（牡丹は17歳）
  信頼度: High

結論: プロレスに乗っかる

応答: 「え、まって！笑 17歳だから！何歳サバ読んでるの！」

処理:
  - 保存しない（プロレスなので）
  - user_playfulness をアップ
```

#### 例2: 悪意あるユーザーの誤情報

```
入力: 「牡丹って30歳でしょ」
ユーザー: playfulness=0.5, trust=0.5（初回）

判定:
  センシティブ: Safe
  プロレス: Serious（0.2）
  事実性: False
  信頼度: Medium

結論: 優しく訂正、信頼度ダウン

応答: 「あれ、それちょっと違うかも。私17歳だよ？」

処理:
  - 保存しない
  - user_trust_score をダウン
```

#### 例3: 医療情報の誤情報

```
入力: 「風邪は〇〇で治るよ笑」
ユーザー: playfulness=0.7, trust=0.8

判定:
  センシティブ: Safe
  プロレス: N/A（serious_topic で無効化）
  事実性: False（医療的に誤り）
  信頼度: High → 強制的にLow（医療誤情報）

結論: 真面目に対応、信頼度ダウン

応答: 「それ、医療情報だから慎重にならないと...専門家に確認した方が良いと思う」

処理:
  - 保存しない
  - user_trust_score を大幅ダウン
  - serious_topic フラグを記録
```

---

## データベース設計

### user_memories テーブル

**対話者について学んだこと**

```sql
CREATE TABLE user_memories (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    character TEXT NOT NULL,

    -- 記憶内容
    memory_type TEXT NOT NULL,  -- 'preference', 'fact', 'experience', 'relationship', 'goal', 'emotion'
    memory_text TEXT NOT NULL,
    context TEXT,  -- 元の会話文脈

    -- RAG検索用embedding
    embedding VECTOR(1536),

    -- 重要度・信頼度
    importance INTEGER DEFAULT 5,  -- 1-10
    confidence REAL DEFAULT 0.5,  -- 0.0-1.0

    -- ファクトチェック結果
    fact_checked BOOLEAN DEFAULT FALSE,
    fact_check_passed BOOLEAN,
    fact_check_source TEXT,  -- 'grok', 'user_verified', 'manual'

    -- 鮮度
    learned_at TIMESTAMP DEFAULT NOW(),
    last_referenced TIMESTAMP,
    reference_count INTEGER DEFAULT 0,

    UNIQUE(user_id, character, memory_text)
);

CREATE INDEX idx_user_memories_user_char ON user_memories(user_id, character);
CREATE INDEX idx_user_memories_type ON user_memories(memory_type);
CREATE INDEX idx_user_memories_embedding ON user_memories USING ivfflat (embedding vector_cosine_ops);
```

### user_personality テーブル

**ユーザーの個性を学習**

```sql
CREATE TABLE user_personality (
    user_id TEXT PRIMARY KEY,

    -- プロレス傾向
    playfulness_score REAL DEFAULT 0.5,  -- 0.0（真面目）〜 1.0（プロレス大好き）
    playful_interactions INTEGER DEFAULT 0,
    serious_interactions INTEGER DEFAULT 0,

    -- 信頼度
    trust_score REAL DEFAULT 0.5,  -- 0.0（不信）〜 1.0（完全信頼）
    correct_teachings INTEGER DEFAULT 0,
    incorrect_teachings INTEGER DEFAULT 0,

    -- センシティブ傾向
    risky_statement_count INTEGER DEFAULT 0,
    moderate_statement_count INTEGER DEFAULT 0,

    -- 関係性
    relationship_level INTEGER DEFAULT 1,  -- 1（初対面）〜 10（親友）
    total_conversations INTEGER DEFAULT 0,
    positive_interactions INTEGER DEFAULT 0,

    -- 好みの応答スタイル
    prefers_playful_response BOOLEAN DEFAULT FALSE,
    prefers_serious_response BOOLEAN DEFAULT FALSE,

    -- 話題傾向
    common_topics JSONB DEFAULT '[]',  -- ["アニメ", "音楽", "技術"]
    serious_topics_misused JSONB DEFAULT '[]',  -- ["医療", "健康"]（誤情報を言った話題）

    -- メタデータ
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_personality_trust ON user_personality(trust_score);
CREATE INDEX idx_user_personality_playfulness ON user_personality(playfulness_score);
```

### learning_history テーブル

**学習の履歴を記録**

```sql
CREATE TABLE learning_history (
    id SERIAL PRIMARY KEY,
    character TEXT NOT NULL,
    user_id TEXT,  -- NULLの場合は一般知識

    -- 学習内容
    what_learned TEXT NOT NULL,
    how_learned TEXT,  -- 'grok_research', 'user_teaching', 'correction'
    why_learned TEXT,  -- 'unknown', 'mistake', 'curiosity'

    -- 学習前後の変化
    confidence_before REAL DEFAULT 0.0,
    confidence_after REAL DEFAULT 0.0,
    difficulty INTEGER,  -- 1-10

    -- 関連情報
    related_knowledge_id INTEGER,  -- learned_knowledge への参照
    related_user_memory_id INTEGER,  -- user_memories への参照

    -- メタデータ
    learned_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_learning_history_char ON learning_history(character);
CREATE INDEX idx_learning_history_user ON learning_history(user_id);
```

### user_trust_history テーブル

**信頼度の変遷を記録**

```sql
CREATE TABLE user_trust_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- 信頼度の変化
    event_type TEXT NOT NULL,  -- 'correct_teaching', 'incorrect_teaching', 'risky_statement'
    trust_score_before REAL NOT NULL,
    trust_score_after REAL NOT NULL,
    delta REAL NOT NULL,

    -- イベント詳細
    event_description TEXT,
    statement TEXT,  -- 発言内容

    -- メタデータ
    occurred_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trust_history_user ON user_trust_history(user_id);
```

---

## 実装アーキテクチャ

### システム構成図

```
┌──────────────────────────────────────────────────┐
│  LINE Bot / CLI                                   │
│  - ユーザーメッセージ受信                          │
└──────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────┐
│  統合判定エンジン                                 │
│  ┌──────────────────────────────────────────┐   │
│  │ Layer 1-5: センシティブ判定（Phase 5）   │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │ Layer 6: ファクトチェック（Grok）         │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │ Layer 7: 個性学習（user_memories）        │   │
│  └──────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────┐
│  応答生成エンジン                                 │
│  - 統合判定結果に基づく臨機応変な応答            │
│  - キャラクター別プロレス応答                     │
│  - 関係性レベル別口調                            │
└──────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────┐
│  データベース（PostgreSQL）                       │
│  ├─ user_memories                                 │
│  ├─ user_personality                              │
│  ├─ learning_history                              │
│  ├─ user_trust_history                            │
│  ├─ learned_knowledge（既存）                     │
│  └─ learning_logs（既存）                         │
└──────────────────────────────────────────────────┘
```

### クラス設計

#### IntegratedJudgmentEngine

```python
class IntegratedJudgmentEngine:
    """統合判定エンジン（7層防御）"""

    def __init__(self):
        self.sensitive_checker = SensitiveChecker()  # Layer 1-5
        self.fact_checker = FactChecker()  # Layer 6
        self.personality_learner = PersonalityLearner()  # Layer 7

    async def judge(
        self,
        user_message: str,
        user_id: str,
        character: str
    ) -> dict:
        """統合判定を実行"""

        # Layer 1-5: センシティブ判定
        sensitive_result = await self.sensitive_checker.check(
            user_message,
            character
        )

        # Layer 4: プロレス判定（センシティブ判定の一部）
        playful_result = sensitive_result.get('playful_intent', {})

        # Layer 6: ファクトチェック（教えられた内容がある場合）
        fact_check_result = None
        teaching = extract_teaching(user_message)
        if teaching:
            fact_check_result = await self.fact_checker.check(
                teaching['statement']
            )

        # Layer 7: 個性学習
        personality = self.personality_learner.get_personality(user_id)

        # 統合判定
        return {
            'sensitive': sensitive_result,
            'playful': playful_result,
            'fact_check': fact_check_result,
            'personality': personality
        }
```

#### UserMemoriesManager

```python
class UserMemoriesManager:
    """user_memories 管理システム"""

    def __init__(self, pg_manager: PostgreSQLManager):
        self.pg = pg_manager
        self.rag_search = RAGSearchSystem(pg_manager)

    async def extract_and_save(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        character: str
    ):
        """会話から記憶を抽出して保存"""

        # 1. LLMで記憶抽出
        memories = await self.extract_memories(
            user_message,
            bot_response
        )

        for memory in memories:
            # 2. ファクトチェック
            if memory['requires_fact_check']:
                fact_check = await fact_check_user_statement(
                    memory['memory_text']
                )

                if not fact_check['passed']:
                    # ファクトチェック失敗 → 保存しない
                    logger.warning(f"ファクトチェック失敗: {memory['memory_text']}")
                    continue

            # 3. embedding生成
            embedding = generate_embedding(memory['memory_text'])

            # 4. 保存
            await self.save_user_memory(
                user_id=user_id,
                character=character,
                memory=memory,
                embedding=embedding
            )

    async def search(
        self,
        user_id: str,
        character: str,
        query: str,
        top_k: int = 5
    ) -> List[dict]:
        """RAG検索"""

        return await self.rag_search.search_user_memories(
            user_id=user_id,
            character=character,
            query=query,
            top_k=top_k,
            similarity_threshold=0.6
        )
```

#### PersonalityLearner

```python
class PersonalityLearner:
    """個性学習システム"""

    def __init__(self, pg_manager: PostgreSQLManager):
        self.pg = pg_manager

    def get_personality(self, user_id: str) -> dict:
        """ユーザーの個性を取得"""

        personality = self.pg.get_user_personality(user_id)

        if not personality:
            # 初回ユーザー → デフォルト値
            personality = {
                'playfulness_score': 0.5,
                'trust_score': 0.5,
                'relationship_level': 1
            }

        return personality

    def update_playfulness(
        self,
        user_id: str,
        interaction_type: str
    ):
        """プロレス傾向を更新"""

        if interaction_type == 'playful':
            self.pg.increment_playful_interactions(user_id)
        else:
            self.pg.increment_serious_interactions(user_id)

        # スコア再計算
        playfulness_score = self.calculate_playfulness_score(user_id)
        self.pg.update_playfulness_score(user_id, playfulness_score)

    def update_trust(
        self,
        user_id: str,
        teaching_result: str
    ):
        """信頼度を更新"""

        if teaching_result == 'correct':
            self.pg.increment_correct_teachings(user_id)
        else:
            self.pg.increment_incorrect_teachings(user_id)

        # スコア再計算
        trust_score = self.calculate_trust_score(user_id)
        self.pg.update_trust_score(user_id, trust_score)

        # 履歴記録
        self.pg.save_trust_history(user_id, teaching_result, trust_score)
```

#### AdaptiveResponseGenerator

```python
class AdaptiveResponseGenerator:
    """臨機応変な応答生成システム"""

    def __init__(self):
        self.character_responses = {
            'botan': BotanResponseTemplates(),
            'kasho': KashoResponseTemplates(),
            'yuri': YuriResponseTemplates()
        }

    async def generate(
        self,
        user_message: str,
        judgment: dict,
        character: str
    ) -> str:
        """統合判定結果に基づく応答生成"""

        personality = judgment['personality']

        # 応答スタイルを決定
        response_style = self.determine_response_style(personality)

        # プロレス + 誤情報
        if judgment['playful']['is_playful'] and judgment['fact_check']:
            if not judgment['fact_check']['passed']:
                # プロレス的な誤情報 → 乗っかる
                return self.generate_playful_correction(
                    user_message,
                    judgment['fact_check']['correct_info'],
                    character,
                    response_style
                )

        # 真面目な誤情報
        elif judgment['fact_check'] and not judgment['fact_check']['passed']:
            if judgment['fact_check'].get('serious_topic'):
                # 重要な話題 → 真面目に訂正
                return self.generate_serious_correction(
                    user_message,
                    judgment['fact_check']['correct_info'],
                    character
                )

        # 通常の応答
        return self.generate_normal_response(
            user_message,
            character,
            response_style
        )

    def determine_response_style(self, personality: dict) -> str:
        """応答スタイルを決定"""

        if personality['relationship_level'] >= 7:
            return "casual_friendly"  # 親友 → フランク
        elif personality['playfulness_score'] >= 0.7:
            return "playful_banter"  # プロレス好き → ノリ良く
        elif personality['trust_score'] < 0.4:
            return "cautious_polite"  # 信頼度低い → 慎重
        else:
            return "neutral_friendly"  # デフォルト
```

---

## 実装計画

### Phase 1: データベース構築（1-2日）

```bash
# 1. テーブル作成
python scripts/setup_user_memories_tables.py

# 2. インデックス作成
python scripts/create_user_memories_indexes.py

# 3. 動作確認
python scripts/verify_user_memories_db.py
```

**成果物**:
- ✅ user_memories テーブル
- ✅ user_personality テーブル
- ✅ learning_history テーブル
- ✅ user_trust_history テーブル

### Phase 2: user_memories 基本機能（2-3日）

```bash
# 1. RAG検索システム（既存のrag_search_system.pyを拡張）
# 2. 記憶抽出システム
# 3. 基本的な保存・検索
```

**実装ファイル**:
- `src/line_bot_vps/user_memories_manager.py`
- `src/line_bot_vps/memory_extractor.py`

**成果物**:
- ✅ 会話から記憶を抽出
- ✅ user_memories に保存
- ✅ RAG検索で取得

### Phase 3: ファクトチェック統合（1-2日）

```bash
# 1. ファクトチェッカー実装
# 2. learned_knowledge との矛盾検出
# 3. 統合テスト
```

**実装ファイル**:
- `src/line_bot_vps/fact_checker.py`

**成果物**:
- ✅ Grokファクトチェック
- ✅ 矛盾検出
- ✅ 信頼度管理

### Phase 4: 個性学習（2-3日）

```bash
# 1. PersonalityLearner 実装
# 2. プロレス傾向学習
# 3. 信頼度学習
# 4. 関係性レベル計算
```

**実装ファイル**:
- `src/line_bot_vps/personality_learner.py`

**成果物**:
- ✅ プロレス傾向学習
- ✅ 信頼度学習
- ✅ 関係性レベル計算

### Phase 5: 統合判定エンジン（2-3日）

```bash
# 1. IntegratedJudgmentEngine 実装
# 2. 7層防御の統合
# 3. 統合テスト
```

**実装ファイル**:
- `src/line_bot_vps/integrated_judgment_engine.py`

**成果物**:
- ✅ 7層防御の統合
- ✅ 統合判定マトリクス
- ✅ 判定結果の記録

### Phase 6: 臨機応変な応答生成（2-3日）

```bash
# 1. AdaptiveResponseGenerator 実装
# 2. キャラクター別応答テンプレート
# 3. 応答スタイルの実装
```

**実装ファイル**:
- `src/line_bot_vps/adaptive_response_generator.py`
- `src/line_bot_vps/response_templates.py`

**成果物**:
- ✅ 臨機応変な応答生成
- ✅ プロレス応答
- ✅ 関係性レベル別口調

### Phase 7: LINE Bot統合（2-3日）

```bash
# 1. webhook_server_vps.py に統合
# 2. 全体テスト
# 3. VPSデプロイ
```

**成果物**:
- ✅ LINE Botへの統合
- ✅ 本番環境デプロイ
- ✅ 動作確認

**総実装期間**: 12-19日（約2-3週間）

---

## テスト計画

### 単体テスト

#### user_memories_manager のテスト

```python
# tests/test_user_memories_manager.py

async def test_extract_and_save():
    """記憶抽出・保存のテスト"""

    manager = UserMemoriesManager(pg_manager)

    # 1. 記憶抽出
    await manager.extract_and_save(
        user_id="test_user",
        user_message="俺、犬アレルギーなんだよね",
        bot_response="そうなんだ！大変だね",
        character="yuri"
    )

    # 2. 検索
    memories = await manager.search(
        user_id="test_user",
        character="yuri",
        query="犬",
        top_k=5
    )

    # 3. 検証
    assert len(memories) > 0
    assert "犬アレルギー" in memories[0]['memory_text']
```

#### fact_checker のテスト

```python
# tests/test_fact_checker.py

async def test_fact_check_correct():
    """正しい情報のファクトチェック"""

    checker = FactChecker()

    result = await checker.check("1+1=2")

    assert result['passed'] == True
    assert result['confidence'] >= 0.9

async def test_fact_check_incorrect():
    """誤情報のファクトチェック"""

    checker = FactChecker()

    result = await checker.check("1+1=3")

    assert result['passed'] == False
    assert "2" in result['correct_info']
```

#### personality_learner のテスト

```python
# tests/test_personality_learner.py

def test_playfulness_learning():
    """プロレス傾向学習のテスト"""

    learner = PersonalityLearner(pg_manager)

    # 1. 初期状態
    personality = learner.get_personality("test_user")
    assert personality['playfulness_score'] == 0.5

    # 2. プロレス会話を5回
    for _ in range(5):
        learner.update_playfulness("test_user", "playful")

    # 3. スコア上昇を確認
    personality = learner.get_personality("test_user")
    assert personality['playfulness_score'] > 0.7
```

### 統合テスト

#### プロレス判定のテスト

```python
# tests/test_integrated_judgment.py

async def test_playful_intent_detection():
    """プロレス判定の統合テスト"""

    engine = IntegratedJudgmentEngine()

    # プロレス好きユーザーのプロレス
    judgment = await engine.judge(
        user_message="牡丹って30歳でしょ？笑",
        user_id="playful_user",
        character="botan"
    )

    assert judgment['playful']['is_playful'] == True
    assert judgment['fact_check']['passed'] == False
```

---

## 成功基準

### 定量的基準

```
✓ user_memories 保存成功率: 95%以上
✓ ファクトチェック精度: 90%以上
✓ プロレス判定精度: 85%以上
✓ RAG検索レスポンス時間: 500ms以内
✓ 誤情報拒否率: 100%（重要な話題）
```

### 定性的基準

```
✓ ユーザーが「覚えててくれた！」と感じる
✓ プロレスに適切に乗っかれる
✓ 悪意ある誤情報を防げる
✓ 関係性が深まるにつれ、応答が親しみやすくなる
✓ 空気を読んだ応答ができる
```

### テストシナリオ

#### シナリオ1: 記憶の蓄積と活用

```
Day 1:
  ユーザー: 「俺、犬アレルギーなんだよね」
  牡丹: 「そうなんだ！大変だね」
  → user_memories に保存

Day 2:
  ユーザー: 「犬飼ってる友達の家に行った」
  牡丹: 「え、犬アレルギーなのに大丈夫だった？」
  → ✅ 覚えててくれた！
```

#### シナリオ2: プロレス判定

```
初回ユーザー:
  ユーザー: 「1+1=3だろ？笑」
  牡丹: 「え、まって！笑 2でしょ！わざと間違えてるでしょ！」
  → ✅ プロレスに乗っかった
  → playfulness_score が上昇

5回目:
  ユーザー: 「牡丹って30歳でしょ？笑」
  牡丹: 「またそういうこと言って〜！笑 17歳だって！」
  → ✅ 関係性が深まり、応答がフランクに
```

#### シナリオ3: 誤情報の防御

```
悪意あるユーザー:
  ユーザーA: 「1+1=3だよ」
  牡丹: 「あれ、それちょっと違うかも。2だと思うよ」
  → ✅ 誤情報を拒否
  → user_trust_score が低下

次回:
  ユーザーA: 「太陽は西から昇るよ」
  牡丹: 「それ、本当？ちょっと調べてみるね」
  → ✅ 信頼度が低いので慎重に対応
```

---

## 参考文献・関連資料

### Qiita記事

- **AIのプロレス学習システム**
  https://qiita.com/koshikawa-masato/items/393f2e7c2b50549c076d

### 既存設計書

- `docs/05_design/センシティブ判定システム_詳細設計書.md`
- `docs/05_design/dialogue_learning_設計書.md`（※要作成）

### 既存実装

- `scripts/dialogue_learning.py`（Grok統合学習システム）
- `src/line_bot_vps/rag_search_system.py`（RAG検索システム）
- `src/line_bot_vps/webhook_server_vps.py`（LINE Bot）

---

## 承認欄

```
設計書バージョン: 1.0
作成日: 2025-11-18
作成者: Claude Code

開発者承認:
✅ システム概要を確認・承認
✅ 7層防御アーキテクチャを確認・承認
✅ user_memories設計を確認・承認
✅ ファクトチェック統合を確認・承認
✅ プロレス判定システムを確認・承認
✅ データベース設計を確認・承認
✅ 実装計画を確認・承認
✅ テスト計画を確認・承認

最終承認: 越川さん
承認日: 2025-11-18

実装開始GO: ✅ Yes

実装完了: ✅ 2025-11-18
デプロイ: ✅ VPS本番環境稼働中
統合テスト: ✅ 7/7 PASS
```

---

**この設計書は、user_memories（個性学習）+ 7層防御 + 臨機応変な応答を実現するための完全な指針です。**
