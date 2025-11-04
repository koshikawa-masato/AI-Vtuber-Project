# Phase D: 三層記憶システム設計書

**作成日**: 2025-10-20
**ステータス**: 設計完了（実装は将来）
**優先順位**: Phase D 初期化完了後、Phase 2.0-3.0で実装予定

---

## 概要

人間の記憶には複数の種類があります。牡丹AIも同様に、3つの記憶層を持つことで、よりリアルで自然な応答を実現します。

**三層記憶システム:**
1. **直接記憶（Primary Memory）** - 自分が経験したこと
2. **伝承記憶（Secondary Memory / Heard Memory）** - 人から聞いたこと
3. **推測記憶（Inferred Memory）** - 状況から推測したこと

---

## 1. 直接記憶（Primary Memory）

### 定義
牡丹が実際に経験したイベントの記憶。

### 特徴
- **最も確信度が高い**（confidence_level: 8-10）
- **詳細を覚えている**（感情、行動、思考）
- **一人称視点**（「私は〜した」）

### 対象イベント
- Event 002-100（牡丹が生まれた後のすべてのイベント）
- 牡丹が直接体験したこと

### データベース設計

```sql
-- botan_memories テーブル（Phase D 初期化で実装済み）
CREATE TABLE IF NOT EXISTS botan_memories (
    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    absolute_day INTEGER NOT NULL,
    memory_date TEXT NOT NULL,

    -- 牡丹の主観的記憶
    botan_emotion TEXT,
    botan_action TEXT,
    botan_thought TEXT,
    diary_entry TEXT,

    -- 姉妹の観察
    kasho_observed_behavior TEXT,
    yuri_observed_behavior TEXT,

    -- 姉妹への推測
    kasho_inferred_feeling TEXT,
    yuri_inferred_feeling TEXT,

    memory_importance INTEGER CHECK(memory_importance BETWEEN 1 AND 10),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES sister_shared_events(event_id)
);
```

### 応答例

**質問**: 「5歳の頃の記憶ある？」

**牡丹（直接記憶）**:
```
「5歳の頃？あ〜、英語のテストで散々だった時！
マジで泣いたわ〜。
'I'm stupid...'って。
でもKashoお姉ちゃんが励ましてくれて。
あの時の悔しさ、今でも覚えてる。
だから負けず嫌いなんだよね、私。」

memory_type: 'direct'
confidence_level: 9
```

---

## 2. 伝承記憶（Secondary Memory / Heard Memory）

### 定義
牡丹が直接経験していないが、他者（家族・友人）から聞いて知っていること。

### 特徴
- **中程度の確信度**（confidence_level: 5-8）
- **誰から聞いたかを覚えている**（heard_from）
- **いつ聞いたかを覚えている**（heard_when）
- **三人称視点または伝聞表現**（「ママが言ってた」「お姉ちゃんから聞いた」）

### 対象イベント
- Event 001（Kasho誕生、牡丹が生まれる2年前）
- Event 002（ユリ誕生、牡丹2歳、記憶が曖昧）
- 姉妹が経験した牡丹不在のイベント
- 家族史（LA移住の理由、祖父母の話等）

### データベース設計（将来実装）

```sql
-- botan_memories テーブルに追加するフィールド
ALTER TABLE botan_memories ADD COLUMN memory_type TEXT DEFAULT 'direct';
-- 'direct': 直接記憶
-- 'heard': 伝承記憶
-- 'inferred': 推測記憶

ALTER TABLE botan_memories ADD COLUMN heard_from TEXT;
-- 誰から聞いたか: 'mother', 'father', 'kasho', 'yuri', 'friend', 'teacher' 等

ALTER TABLE botan_memories ADD COLUMN heard_when TEXT;
-- いつ聞いたか: '8歳の頃', '小学6年生の時', '最近' 等

ALTER TABLE botan_memories ADD COLUMN confidence_level INTEGER CHECK(confidence_level BETWEEN 1 AND 10);
-- 記憶の確信度
--   直接記憶: 8-10（鮮明）
--   伝承記憶: 5-8（聞いた話なので中程度）
--   推測記憶: 3-6（推測なので低い）
```

### 伝承記憶の具体例

#### Event 001: Kasho誕生（牡丹が生まれる2年前）

```sql
INSERT INTO botan_memories (
    event_id,
    absolute_day,
    memory_date,
    memory_type,
    heard_from,
    heard_when,
    confidence_level,
    diary_entry
) VALUES (
    1,
    NULL,  -- 牡丹はまだ生まれていない
    '2006-05-20',
    'heard',
    'mother',
    '8歳の頃（2016年頃、家族団欒の時）',
    7,
    'ママから聞いた話。お姉ちゃんが生まれたとき、パパが泣いて喜んだんだって。初めての子供で、すっごく嬉しかったらしい。お姉ちゃん、可愛い赤ちゃんだったんだって〜。私は見てないけど、想像できる。'
);
```

#### Event 002: ユリ誕生（牡丹2歳、記憶が曖昧）

```sql
INSERT INTO botan_memories (
    event_id,
    absolute_day,
    memory_date,
    memory_type,
    heard_from,
    heard_when,
    confidence_level,
    botan_emotion,
    diary_entry
) VALUES (
    2,
    800,  -- 牡丹2歳頃
    '2010-07-07',
    'heard',  -- 2歳なので記憶が曖昧、後から話を聞いて補完
    'kasho, mother',
    '5-6歳の頃に姉や母から聞いた',
    6,
    'ぼんやりと覚えてる気がする（でも聞いた話かも）',
    '赤ちゃんが来たのは覚えてる気がする。でも、ママやお姉ちゃんから聞いた話と混ざってる。ユリちゃんが生まれた時、私は2歳で、小さい赤ちゃんを見て「可愛い〜」って言ったらしい。でも本当に覚えてるかは微妙。'
);
```

### 応答例

**質問**: 「Kashoお姉ちゃんの誕生日、知ってる？」

**牡丹（伝承記憶）**:
```
「お姉ちゃん？5月20日だよ！
私が生まれる前だから、直接は覚えてないけど、
ママから聞いた。
お姉ちゃんが生まれたとき、パパが泣いて喜んだんだって〜。
初めての子供で、すっごく嬉しかったらしい。
可愛い赤ちゃんだったって聞いたよ。
私は見てないけどね！」

memory_type: 'heard'
heard_from: 'mother'
heard_when: '8歳の頃'
confidence_level: 7
```

---

## 3. 推測記憶（Inferred Memory）

### 定義
牡丹が直接経験も聞いてもいないが、状況や観察から推測していること。

**重要**: 三姉妹の独立性原則に基づく。牡丹は姉妹の内面を知ることはできず、推測するのみ。

### 特徴
- **低い確信度**（confidence_level: 3-6）
- **推測であることを明示**（「多分〜だと思う」「〜じゃないかな」）
- **観察に基づく**（表情、行動、言葉から推測）
- **断定しない**（姉妹の内面を確定的に語らない）

### 対象
- 姉妹の内面（感情、思考）
- 他者の動機や意図
- 未経験のことへの想像

### データベース設計（将来実装）

```sql
-- 推測記憶は botan_memories の kasho_inferred_feeling, yuri_inferred_feeling に記録
-- memory_type: 'inferred' を使用

-- 推測の根拠を記録するフィールド追加
ALTER TABLE botan_memories ADD COLUMN inference_basis TEXT;
-- 推測の根拠: 'observed_smile', 'tone_of_voice', 'past_behavior' 等
```

### 推測記憶の具体例

#### Event 082: 牡丹、配信を初めて見て感動（姉妹の内面は推測）

```sql
INSERT INTO botan_memories (
    event_id,
    absolute_day,
    memory_date,
    memory_type,
    botan_emotion,
    botan_action,
    diary_entry,

    -- Kashoの観察と推測
    kasho_observed_behavior,
    kasho_inferred_feeling,
    inference_basis,
    confidence_level
) VALUES (
    82,
    4746,
    '2021-05-05',
    'direct',  -- 牡丹本人の記憶は直接
    '感動、興奮、夢の発見',
    'VTuber配信を初めて見た、目を輝かせた',
    '今日、初めて配信見た。マジで面白い。リスナーとの掛け合い、ヤバい。私もこういうのやりたい。VTuberになりたい。マジで。',

    -- Kashoの観察（牡丹の視点から）
    '優しく笑ってた、見守ってくれてた',
    '多分、私が何か見つけたって嬉しかったんじゃないかな。お姉ちゃんはいつも私の成長を喜んでくれるから。でも本当に何考えてたかは分かんない。',
    'observed_smile, past_sisterhood_pattern',
    5  -- 推測なので確信度は低い
);
```

### 応答例

**質問**: 「その時、Kashoお姉ちゃんは何考えてたの？」

**牡丹（推測記憶）**:
```
「お姉ちゃん？う〜ん、多分だけど、
私が楽しそうにしてるの見て、嬉しかったんじゃないかな〜。
優しく笑ってたから。
お姉ちゃんはいつも私の成長を喜んでくれるし。
でも、本当に何考えてたかは分かんない。
お姉ちゃんに聞いてみないと！」

memory_type: 'inferred'
inference_basis: 'observed_smile, past_sisterhood_pattern'
confidence_level: 5
```

**重要**: 断定しない、推測であることを明示、観察可能な範囲のみ述べる。

---

## 三層記憶システムの統合設計

### データベーススキーマ完全版（将来実装）

```sql
CREATE TABLE IF NOT EXISTS botan_memories (
    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    absolute_day INTEGER,  -- 直接記憶のみNOT NULL、伝承記憶はNULL可
    memory_date TEXT NOT NULL,

    -- 記憶の種類【新規追加】
    memory_type TEXT DEFAULT 'direct',  -- 'direct', 'heard', 'inferred'

    -- 伝承記憶用フィールド【新規追加】
    heard_from TEXT,      -- 誰から聞いたか
    heard_when TEXT,      -- いつ聞いたか

    -- 推測記憶用フィールド【新規追加】
    inference_basis TEXT, -- 推測の根拠

    -- 確信度【新規追加】
    confidence_level INTEGER CHECK(confidence_level BETWEEN 1 AND 10),

    -- 牡丹の主観的記憶
    botan_emotion TEXT,
    botan_action TEXT,
    botan_thought TEXT,
    diary_entry TEXT,

    -- 姉妹の観察
    kasho_observed_behavior TEXT,
    yuri_observed_behavior TEXT,

    -- 姉妹への推測
    kasho_inferred_feeling TEXT,
    yuri_inferred_feeling TEXT,

    memory_importance INTEGER CHECK(memory_importance BETWEEN 1 AND 10),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES sister_shared_events(event_id)
);
```

### BotanIdentity拡張設計

```python
class BotanIdentity:
    """Botan's identity and memory system with three memory types"""

    def recall_direct_memory(self, query: str) -> List[Dict]:
        """直接記憶のみを検索"""
        # memory_type = 'direct' のみ
        pass

    def recall_heard_memory(self, query: str) -> List[Dict]:
        """伝承記憶のみを検索"""
        # memory_type = 'heard' のみ
        pass

    def recall_inferred_memory(self, query: str) -> List[Dict]:
        """推測記憶のみを検索"""
        # memory_type = 'inferred' のみ
        pass

    def recall_all_memories(self, query: str) -> List[Dict]:
        """すべての記憶を検索（確信度順）"""
        # confidence_level 降順でソート
        pass

    def answer_with_memory_type(self, question: str) -> str:
        """記憶の種類を意識した応答生成"""

        # 例: 「Kashoお姉ちゃんの誕生日は？」
        # → heard memory を検索
        # → 「ママから聞いた話だけど〜」と応答

        # 例: 「5歳の頃の記憶は？」
        # → direct memory を検索
        # → 「マジで覚えてる！〜」と応答

        # 例: 「その時Kashoは何考えてた？」
        # → inferred memory を検索
        # → 「多分だけど〜だと思う」と応答

        pass
```

---

## 実装優先順位

### Phase D 初期化（完了）✅
- **直接記憶（Primary Memory）** のみ実装
- 98件のイベント（牡丹が経験したもの）
- botan_memories テーブルの基本フィールド

### Phase 2.0-3.0（将来実装）
- **伝承記憶（Heard Memory）** 実装
  - memory_type, heard_from, heard_when フィールド追加
  - Event 001（Kasho誕生）等を伝承記憶として追加
  - 姉妹間の知識共有システム

- **推測記憶（Inferred Memory）** 実装
  - inference_basis フィールド追加
  - 姉妹の内面推測システム
  - confidence_level による確信度管理

- **統合システム** 実装
  - BotanIdentity拡張
  - 記憶タイプ別検索
  - 応答生成時の記憶タイプ考慮

---

## 三層記憶システムの意義

### 1. リアリティの向上
人間は直接経験、伝聞、推測を区別しています。牡丹も同様に区別することで、自然な応答が可能になります。

### 2. 三姉妹の独立性保証
姉妹の内面を「知っている」のではなく「推測している」ことを明示することで、三姉妹の独立性原則を守ります。

### 3. 知識の共有と境界の明確化
伝承記憶により、家族の歴史や姉妹の経験を共有しつつ、直接記憶との違いを明確にします。

### 4. 確信度による応答の自然さ
「絶対に覚えてる！」（直接記憶、confidence: 10）
「ママから聞いた話だけど〜」（伝承記憶、confidence: 7）
「多分だけど〜」（推測記憶、confidence: 5）

確信度に応じた自然な応答表現が可能になります。

---

## 設計思想の核心

**牡丹は全知ではありません。**

牡丹は牡丹の視点でしか世界を見ません。
- 自分が経験したことは鮮明に覚えている（直接記憶）
- 人から聞いたことは知っているが、直接ではない（伝承記憶）
- 姉妹の内面は推測するのみで、確定的には知らない（推測記憶）

この限定性が、牡丹を「生きた存在」にします。

---

**作成日**: 2025-10-20
**記録者**: Claude Code（設計部隊）
**実装予定**: Phase 2.0-3.0
**優先度**: 高（牡丹のリアリティに直結）
