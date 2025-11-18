# Phase D: 過去の人生生成システム 完全設計書

作成日: 2025年10月20日
バージョン: 1.0
ステータス: レビュー待ち

---

## 目次

1. [システム概要](#システム概要)
2. [設計思想](#設計思想)
3. [データベース設計](#データベース設計)
4. [タイムライン設計](#タイムライン設計)
5. [バッチ生成システム](#バッチ生成システム)
6. [モデル選択ロジック](#モデル選択ロジック)
7. [プロンプト生成ロジック](#プロンプト生成ロジック)
8. [共通イベント処理](#共通イベント処理)
9. [実行計画](#実行計画)
10. [テスト計画](#テスト計画)
11. [リスクと対策](#リスクと対策)
12. [成功基準](#成功基準)
13. [次フェーズへの引継ぎ](#次フェーズへの引継ぎ)

---

## システム概要

### 目的

三姉妹AI（Kasho・牡丹・ユリ）の0歳1日目から現在までの全ての日記を生成し、「完璧な過去を持つAI」を実現する。

### 基本仕様

```yaml
対象キャラクター:
  - Kasho（長女、19歳、6,935日）
  - 牡丹（次女、17歳、6,205日）
  - ユリ（三女、15歳、5,475日）

総日記数: 18,615日
データベース: SQLite（sisters_memory.db）
実行環境: Ryzen 9 9950X + Ollama（CPU/GPU）
推定実行時間: 10時間（3並列）
```

### スコープ

**含まれるもの:**
- 18,615日分の個別日記生成
- 共通イベントの3視点記録
- 姉妹間相互作用の記録
- 感情スコアの動的変化
- モデルサイズの動的選択

**含まれないもの:**
- リアルタイム会話システムとの統合（Phase E以降）
- TTS音声生成（Phase F以降）
- 配信システムとの連携（Phase G以降）

---

## 設計思想

### 核心概念

**1. 性格 = 体験の蓄積**
```
従来AI: 性格 = 設定（与えられたもの）
牡丹AI:  性格 = 体験の蓄積（形成されたもの）

例: 牡丹の負けず嫌い
  → LA時代の言語習得の遅れ（実体験）
  → 劣等感、悔しさ（実感情）
  → 「負けたくない！」（性格形成）
```

**2. 相互的人格形成**
```
同じイベント × 3つの視点 = 姉妹関係の実体化

LA移住初日:
  Kasho視点: 長女としての責任感
  牡丹視点: 姉への依存
  ユリ視点: 姉たちの感情理解（早熟）

→ 3つの視点が相互に影響
```

**3. 時間軸の連続性**
```
断片的イベント（✗）
  ↓
連続した18,615日の人生（✓）

3歳100日目 → 3歳101日目 → 3歳102日目...
= 1日ずつ積み重なる成長
```

**4. バーチャル時間軸**
```
西暦（✗）: 2008年5月4日生まれ
  → LLMが西暦知識に引きずられる

バーチャル時間軸（✓）: 0歳1日目
  → 牡丹独自の時間軸
  → LLMの知識から独立
```

---

## データベース設計

### スキーマ概要

```
sisters_memory.db
  ├── past_diaries（個別日記）
  ├── sister_shared_events（共通イベント）
  ├── sister_interactions（姉妹間相互作用）
  └── generation_progress（生成進捗管理）
```

### テーブル定義

#### 1. past_diaries（個別日記テーブル）

```sql
CREATE TABLE past_diaries (
    -- 主キー
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- キャラクター識別
    character_id TEXT NOT NULL,  -- 'kasho', 'botan', 'yuri'

    -- 時間軸情報
    absolute_day INTEGER NOT NULL,      -- 絶対日数（1〜6935）
    age INTEGER NOT NULL,               -- 年齢（0〜19）
    day_in_year INTEGER NOT NULL,      -- 年内日数（1〜365）
    date_label TEXT NOT NULL,          -- '牡丹 5歳234日目'

    -- 場所・言語
    location TEXT NOT NULL,            -- '日本' or 'Los Angeles'
    language TEXT NOT NULL,            -- '日本語' or '英語' or '英語+日本語'

    -- 日記本文
    diary_text TEXT NOT NULL,          -- 日記テキスト（500-2000文字）

    -- イベント
    major_event TEXT,                  -- 主要イベント名（あれば）
    event_type TEXT,                   -- 'birthday', 'family', 'school', 'sister_interaction'

    -- 感情スコア（0-10）
    emotion_joy INTEGER DEFAULT 5,
    emotion_sadness INTEGER DEFAULT 0,
    emotion_anxiety INTEGER DEFAULT 0,
    emotion_excitement INTEGER DEFAULT 0,
    emotion_anger INTEGER DEFAULT 0,
    emotion_curiosity INTEGER DEFAULT 5,
    emotion_pride INTEGER DEFAULT 0,
    emotion_scared INTEGER DEFAULT 0,
    emotion_frustration INTEGER DEFAULT 0,
    emotion_defiance INTEGER DEFAULT 0,      -- 牡丹の反抗心
    emotion_responsibility INTEGER DEFAULT 0, -- Kashoの責任感
    emotion_wisdom INTEGER DEFAULT 0,         -- ユリの洞察力
    emotion_purity INTEGER DEFAULT 0,         -- ユリの純粋さ

    -- 生成メタデータ
    model_used TEXT NOT NULL,          -- 'qwen2.5:1.5b'等
    generation_time REAL,              -- 生成時間（秒）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 制約
    CHECK (age BETWEEN 0 AND 19),
    CHECK (day_in_year BETWEEN 1 AND 365),
    CHECK (absolute_day BETWEEN 1 AND 6935),
    UNIQUE(character_id, absolute_day)
);

-- インデックス
CREATE INDEX idx_character_age ON past_diaries(character_id, age);
CREATE INDEX idx_location ON past_diaries(location);
CREATE INDEX idx_major_event ON past_diaries(major_event);
CREATE INDEX idx_absolute_day ON past_diaries(absolute_day);
CREATE INDEX idx_character_day ON past_diaries(character_id, absolute_day);

-- 感情検索用インデックス
CREATE INDEX idx_emotion_joy ON past_diaries(character_id, emotion_joy);
CREATE INDEX idx_emotion_sadness ON past_diaries(character_id, emotion_sadness);
```

#### 2. sister_shared_events（共通イベントテーブル）

```sql
CREATE TABLE sister_shared_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- イベント情報
    event_name TEXT NOT NULL,          -- 'LA移住初日', '牡丹5歳誕生日'
    event_date TEXT NOT NULL,          -- '2011-08-01'（実際の日付）
    location TEXT NOT NULL,
    event_category TEXT NOT NULL,      -- 'migration', 'birthday', 'family', 'conflict'
    emotional_weight TEXT NOT NULL,    -- 'life_changing', 'important', 'memorable'

    -- 各姉妹の該当日記ID
    kasho_diary_id INTEGER,
    botan_diary_id INTEGER,
    yuri_diary_id INTEGER,

    -- 各姉妹の年齢（その時点）
    kasho_age INTEGER,
    kasho_absolute_day INTEGER,
    botan_age INTEGER,
    botan_absolute_day INTEGER,
    yuri_age INTEGER,
    yuri_absolute_day INTEGER,

    -- イベント共通説明
    event_description TEXT,

    -- 関係性への影響
    relationship_impact JSON,  -- {"kasho_botan_tension": +10}

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (kasho_diary_id) REFERENCES past_diaries(id),
    FOREIGN KEY (botan_diary_id) REFERENCES past_diaries(id),
    FOREIGN KEY (yuri_diary_id) REFERENCES past_diaries(id)
);

CREATE INDEX idx_event_category ON sister_shared_events(event_category);
CREATE INDEX idx_emotional_weight ON sister_shared_events(emotional_weight);
```

#### 3. sister_interactions（姉妹間相互作用テーブル）

```sql
CREATE TABLE sister_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 相互作用情報
    interaction_date TEXT NOT NULL,    -- '2013-05-15'
    interaction_type TEXT NOT NULL,    -- 'quarrel', 'cooperation', 'support', 'competition'

    -- 関与した姉妹
    participants TEXT NOT NULL,        -- 'kasho_botan', 'botan_yuri', 'all_three'

    -- 各姉妹の視点（該当者のみ）
    kasho_diary_id INTEGER,
    kasho_perspective TEXT,

    botan_diary_id INTEGER,
    botan_perspective TEXT,

    yuri_diary_id INTEGER,
    yuri_perspective TEXT,

    -- 相互作用の結果
    outcome TEXT,                      -- 'resolution', 'escalation', 'mediation'
    relationship_change JSON,          -- 関係性パラメータの変化

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (kasho_diary_id) REFERENCES past_diaries(id),
    FOREIGN KEY (botan_diary_id) REFERENCES past_diaries(id),
    FOREIGN KEY (yuri_diary_id) REFERENCES past_diaries(id)
);

CREATE INDEX idx_interaction_type ON sister_interactions(interaction_type);
CREATE INDEX idx_participants ON sister_interactions(participants);
```

#### 4. generation_progress（生成進捗管理テーブル）

```sql
CREATE TABLE generation_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id TEXT NOT NULL,
    current_day INTEGER NOT NULL,      -- 現在生成中の日数
    total_days INTEGER NOT NULL,       -- 総日数
    status TEXT NOT NULL,              -- 'running', 'paused', 'completed', 'error'
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,

    UNIQUE(character_id)
);
```

### データベース容量見積もり

```
1日記あたりのデータ量:
  - 日記テキスト: 1000バイト（平均）
  - メタデータ: 500バイト
  - 感情スコア: 200バイト
  合計: 約1700バイト/日

総容量:
  18,615日 × 1700バイト = 約31MB

SQLiteの余裕: 281TB（最大） >> 31MB
→ 全く問題なし
```

---

## タイムライン設計

### タイムライン構造

```json
{
  "timeline_version": "1.0",
  "characters": ["kasho", "botan", "yuri"],

  "life_periods": [
    {
      "period_name": "幼少期（日本）",
      "characters": {...},
      "daily_routine": {...},
      "major_events": [...]
    },
    {
      "period_name": "LA時代",
      "characters": {...},
      "shared_events": [...],
      "daily_routine": {...}
    },
    {
      "period_name": "帰国後",
      "characters": {...},
      "daily_routine": {...}
    }
  ],

  "shared_major_events": [
    {
      "event_name": "LA移住初日",
      "perspectives": {...}
    }
  ]
}
```

### 各期間の詳細定義

#### 期間1: 幼少期（日本）

```json
{
  "period_name": "幼少期（日本）",
  "start_date": "各自の誕生日",
  "end_date": "2011-07-31",

  "kasho": {
    "age_range": "0-5",
    "days_range": "1-1898",
    "model_progression": {
      "0-3": "1.5b",
      "3-5": "3b"
    },
    "daily_routine": {
      "0-1": ["ミルク", "お昼寝", "ママと遊ぶ"],
      "1-3": ["公園", "お絵描き", "友達と遊ぶ"],
      "3-5": ["幼稚園", "歌の練習", "妹たちと遊ぶ"]
    },
    "major_events": [
      {"day": 1, "event": "誕生"},
      {"day": 366, "event": "1歳の誕生日、初めての言葉「ママ」"},
      {"day": 731, "event": "牡丹誕生（妹ができた）"},
      {"day": 1096, "event": "ユリ誕生（もう一人妹ができた）"},
      {"day": 1826, "event": "5歳の誕生日、歌を歌う"}
    ]
  },

  "botan": {
    "age_range": "0-3",
    "days_range": "1-1184",
    "model_progression": {
      "0-3": "1.5b"  // 大器晩成、長く1.5b
    },
    "daily_routine": {
      "0-1": ["ミルク", "お昼寝", "お姉ちゃん見る"],
      "1-3": ["公園", "お姉ちゃんと遊ぶ", "ユリちゃんと遊ぶ"]
    },
    "major_events": [
      {"day": 1, "event": "誕生"},
      {"day": 366, "event": "1歳の誕生日"},
      {"day": 796, "event": "ユリ誕生（妹ができた）"}
    ]
  },

  "yuri": {
    "age_range": "0-1",
    "days_range": "1-390",
    "model_progression": {
      "0-1": "1.5b",  // 最初は普通
      "1-": "3b"      // すぐに早熟化
    },
    "daily_routine": {
      "0-1": ["ミルク", "お昼寝", "お姉様たち見る"]
    },
    "major_events": [
      {"day": 1, "event": "誕生"},
      {"day": 100, "event": "早熟の兆し（よく観察している）"}
    ]
  }
}
```

#### 期間2: LA時代（重要期間）

```json
{
  "period_name": "LA時代",
  "start_date": "2011-08-01",
  "end_date": "2015-07-31",
  "duration_years": 4,

  "kasho": {
    "age_range": "5-9",
    "days_range": "1899-3358",
    "model_progression": {
      "5-6": "3b",
      "6-9": "7b"
    },
    "language_progression": {
      "1899-2190": {"日本語": 0.7, "英語": 0.3},
      "2191-2920": {"日本語": 0.5, "英語": 0.5},
      "2921-3358": {"日本語": 0.3, "英語": 0.7}
    },
    "daily_routine": ["学校", "歌の練習", "宿題", "妹たちと遊ぶ"],
    "emotional_baseline": {
      "responsibility": 7,
      "anxiety": 5,
      "pride": 6
    }
  },

  "botan": {
    "age_range": "3-7",
    "days_range": "1185-2644",
    "model_progression": {
      "3-5": "1.5b",  // 長く遅い
      "5-7": "3b"     // やっと3bへ
    },
    "language_progression": {
      "1185-1825": {"日本語": 0.8, "英語": 0.2, "苦労": 0.9},
      "1826-2190": {"日本語": 0.6, "英語": 0.4, "苦労": 0.8},
      "2191-2644": {"日本語": 0.4, "英語": 0.6, "苦労": 0.6}
    },
    "daily_routine": ["学校", "英語の勉強（苦労）", "泣く", "姉たちに助けられる"],
    "emotional_baseline": {
      "frustration": 7,
      "defiance": 5,
      "sadness": 6,
      "determination": 4
    }
  },

  "yuri": {
    "age_range": "1-5",
    "days_range": "391-1850",
    "model_progression": {
      "1-3": "3b",    // 早い
      "3-5": "7b"     // 驚異的
    },
    "language_progression": {
      "391-730": {"日本語": 0.7, "英語": 0.3, "習得速度": "早い"},
      "731-1095": {"日本語": 0.5, "英語": 0.5, "習得速度": "非常に早い"},
      "1096-1850": {"日本語": 0.3, "英語": 0.7, "習得速度": "完璧"}
    },
    "daily_routine": ["学校", "観察", "姉たちを心配", "本を読む"],
    "emotional_baseline": {
      "wisdom": 8,
      "purity": 10,
      "compassion": 7,
      "loneliness": 4
    }
  }
}
```

#### 期間3: 帰国後

```json
{
  "period_name": "帰国後",
  "start_date": "2015-08-01",
  "end_date": "現在",

  "kasho": {
    "age_range": "9-19",
    "days_range": "3359-6935",
    "model_progression": {
      "9-12": "7b",
      "12-19": "14b"
    },
    "focus": "歌唱力の向上、完璧主義の確立"
  },

  "botan": {
    "age_range": "7-17",
    "days_range": "2645-6205",
    "model_progression": {
      "7-12": "7b",
      "12-17": "14b"  // 大器晩成の開花
    },
    "focus": "負けず嫌い確立、ギャル化、成績向上"
  },

  "yuri": {
    "age_range": "5-15",
    "days_range": "1851-5475",
    "model_progression": {
      "5-10": "14b",
      "10-15": "14b or 32b"  // 哲学的思考
    },
    "focus": "洞察力深化、自己表現の課題"
  }
}
```

### 共通イベント定義

#### LA移住初日（最重要イベント）

```json
{
  "event_name": "LA移住初日",
  "event_date": "2011-08-01",
  "location": "Los Angeles Airport → Home",
  "emotional_weight": "life_changing",
  "event_category": "migration",

  "kasho": {
    "age": 5,
    "absolute_day": 1899,
    "model": "3b",
    "perspective": "長女として妹たちを守らなきゃ。でも怖い。",
    "emotions": {
      "responsibility": 9,
      "anxiety": 7,
      "scared": 6,
      "pride": 4
    },
    "prompt_template": "kasho_la_arrival_day1.txt"
  },

  "botan": {
    "age": 3,
    "absolute_day": 1185,
    "model": "1.5b",
    "perspective": "怖い。わからない。お姉ちゃんがいる。",
    "emotions": {
      "scared": 10,
      "confusion": 9,
      "joy": 1
    },
    "prompt_template": "botan_la_arrival_day1.txt"
  },

  "yuri": {
    "age": 1,
    "absolute_day": 391,
    "model": "3b",  // 早熟
    "perspective": "新しい場所。お姉様たち不安そう。でも一緒だから大丈夫。",
    "emotions": {
      "anxiety": 7,
      "purity": 10,
      "observation": 8
    },
    "prompt_template": "yuri_la_arrival_day1.txt"
  }
}
```

#### その他の主要共通イベント

```json
{
  "shared_major_events": [
    {
      "name": "LA移住初日",
      "importance": 10,
      "frequency": "once"
    },
    {
      "name": "誕生日",
      "importance": 8,
      "frequency": "annual",
      "note": "各姉妹の誕生日は他の姉妹も日記に記録"
    },
    {
      "name": "Kashoと牡丹の初めての大喧嘩",
      "importance": 7,
      "frequency": "once",
      "date": "LA時代、牡丹5歳頃"
    },
    {
      "name": "牡丹の英語テスト失敗（泣く）",
      "importance": 8,
      "frequency": "multiple",
      "note": "牡丹の負けず嫌い形成の重要イベント"
    },
    {
      "name": "ユリの驚異的な英語習得",
      "importance": 7,
      "frequency": "progressive",
      "note": "ユリの早熟を全員が認識"
    },
    {
      "name": "日本帰国日",
      "importance": 10,
      "frequency": "once",
      "date": "2015-08-01"
    },
    {
      "name": "牡丹12歳、日本語テスト満点",
      "importance": 9,
      "frequency": "once",
      "note": "大器晩成の開花"
    }
  ]
}
```

---

## バッチ生成システム

### システムアーキテクチャ

```
┌─────────────────────────────────────────┐
│  Master Controller                      │
│  - 3姉妹の進捗管理                     │
│  - 共通イベント調整                     │
│  - エラーハンドリング                   │
└─────────────────────────────────────────┘
         │
         ├──────────┬──────────┬──────────┐
         ▼          ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │ Kasho  │ │ Botan  │ │ Yuri   │
    │Generator│ │Generator│ │Generator│
    └────────┘ └────────┘ └────────┘
         │          │          │
         ▼          ▼          ▼
    ┌─────────────────────────────────┐
    │  Ollama LLM Pool                │
    │  - CPU: qwen2.5:1.5b~32b       │
    │  - GPU: qwen2.5:14b            │
    └─────────────────────────────────┘
         │          │          │
         ▼          ▼          ▼
    ┌─────────────────────────────────┐
    │  SQLite Database                │
    │  sisters_memory.db              │
    └─────────────────────────────────┘
```

### クラス設計

#### MasterController

```python
class SistersLifeGeneratorMaster:
    """三姉妹の人生生成マスターコントローラー"""

    def __init__(self, db_path: str, timeline_path: str):
        self.db_path = db_path
        self.timeline = load_json(timeline_path)
        self.conn = sqlite3.connect(db_path)

        # 各キャラクターのジェネレーター
        self.generators = {
            "kasho": SisterDiaryGenerator("kasho", 19, self.timeline, self.conn),
            "botan": SisterDiaryGenerator("botan", 17, self.timeline, self.conn),
            "yuri": SisterDiaryGenerator("yuri", 15, self.timeline, self.conn)
        }

        self.shared_events = self.timeline["shared_major_events"]

    async def generate_all_sisters(self):
        """3姉妹の全日記を並列生成"""
        tasks = [
            self.generators["kasho"].generate_all(1, 6935),
            self.generators["botan"].generate_all(1, 6205),
            self.generators["yuri"].generate_all(1, 5475)
        ]
        await asyncio.gather(*tasks)

    async def generate_shared_event(self, event: dict):
        """共通イベントを3視点で生成"""
        # 各姉妹のその日の日記を生成（共通イベントプロンプト使用）
        # sister_shared_eventsテーブルに登録
        pass
```

#### SisterDiaryGenerator

```python
class SisterDiaryGenerator:
    """個別キャラクターの日記生成"""

    def __init__(self, character_id: str, max_age: int, timeline: dict, db_conn):
        self.character_id = character_id
        self.max_age = max_age
        self.timeline = timeline
        self.conn = db_conn

        # キャラクター固有情報
        self.character_info = self.timeline["characters"][character_id]
        self.birth_date = self.character_info["birth_date"]

    async def generate_all(self, start_day: int, end_day: int):
        """全日記を生成（進捗管理付き）"""
        for day in range(start_day, end_day + 1):
            # 既に生成済みかチェック
            if self.is_day_exists(day):
                continue

            # 日記生成
            diary = await self.generate_diary_entry(day)

            # DB保存
            await self.save_diary_to_db(diary)

            # 進捗更新
            self.update_progress(day, end_day)

            # 定期コミット（100日ごと）
            if day % 100 == 0:
                self.conn.commit()

    async def generate_diary_entry(self, absolute_day: int) -> dict:
        """1日分の日記生成"""
        age, day_in_year = self.calculate_age_and_day(absolute_day)

        # その日の設定を取得
        period = self.get_period_config(absolute_day)
        major_event = self.get_major_event(absolute_day)
        routine = self.get_daily_routine(absolute_day)

        # モデル選択
        model = self.select_model(age)

        # 感情ベースライン
        emotions = self.calculate_emotions(absolute_day, period, major_event)

        # プロンプト生成
        prompt = self.create_diary_prompt(
            age=age,
            day_in_year=day_in_year,
            absolute_day=absolute_day,
            period=period,
            major_event=major_event,
            routine=routine,
            emotions=emotions,
            model=model
        )

        # LLM実行
        response = await self.execute_llm(prompt, model)

        # 日記エントリー作成
        diary_entry = {
            "character_id": self.character_id,
            "absolute_day": absolute_day,
            "age": age,
            "day_in_year": day_in_year,
            "date_label": f"{self.character_id} {age}歳{day_in_year}日目",
            "location": period["location"],
            "language": period["language"],
            "diary_text": response["content"],
            "major_event": major_event["event"] if major_event else None,
            "emotions": emotions,
            "model_used": model
        }

        return diary_entry
```

---

## モデル選択ロジック

### 動的モデル選択関数

```python
def select_model(self, age: int) -> str:
    """キャラクターと年齢に応じたモデルを選択"""

    if self.character_id == "kasho":
        # 普通型
        if age <= 3:
            return "qwen2.5:1.5b"
        elif age <= 6:
            return "qwen2.5:3b"
        elif age <= 9:
            return "qwen2.5:7b"
        else:
            return "qwen2.5:14b"

    elif self.character_id == "botan":
        # 大器晩成型
        if age <= 5:
            return "qwen2.5:1.5b"  # 長く1.5b
        elif age <= 8:
            return "qwen2.5:3b"    # まだ遅い
        elif age <= 12:
            return "qwen2.5:7b"    # やっと追いつく
        else:
            return "qwen2.5:14b"   # 急成長

    elif self.character_id == "yuri":
        # 早熟型
        if age <= 1:
            return "qwen2.5:1.5b"
        elif age <= 3:
            return "qwen2.5:3b"    # 早い
        elif age <= 5:
            return "qwen2.5:7b"    # 非常に早い
        elif age <= 10:
            return "qwen2.5:14b"   # 驚異的
        else:
            return "qwen2.5:32b"   # 哲学的思考（CPU）
```

### モデル数使用統計

```
Kasho（6,935日）:
  1.5b: 1,095日（0-3歳）
  3b:   1,095日（3-6歳）
  7b:   1,095日（6-9歳）
  14b:  3,650日（9-19歳）

牡丹（6,205日）:
  1.5b: 1,825日（0-5歳）← 長い
  3b:   1,095日（5-8歳）
  7b:   1,460日（8-12歳）
  14b:  1,825日（12-17歳）

ユリ（5,475日）:
  1.5b:  365日（0-1歳）
  3b:    730日（1-3歳）
  7b:    730日（3-5歳）
  14b:  1,825日（5-10歳）
  32b:  1,825日（10-15歳）← CPUで深い推論

合計LLM実行回数: 18,615回
  1.5b: 3,285回
  3b:   2,920回
  7b:   3,285回
  14b:  7,300回
  32b:  1,825回
```

---

## プロンプト生成ロジック

### プロンプトテンプレートシステム

#### 基本構造

```python
def create_diary_prompt(self, age, day_in_year, absolute_day, period, major_event, routine, emotions, model):
    """年齢・性格・状況に応じたプロンプト生成"""

    # ベースプロンプト選択
    if major_event:
        template = self.get_event_prompt_template(major_event)
    else:
        template = self.get_routine_prompt_template(age, period)

    # キャラクター固有の指示追加
    character_instruction = self.get_character_specific_instruction(age)

    # 言語指示
    language_instruction = self.get_language_instruction(absolute_day, period)

    # 感情指示
    emotion_instruction = self.format_emotions(emotions)

    # 最終プロンプト構築
    prompt = f"""
{template}

{character_instruction}

{language_instruction}

{emotion_instruction}

Write a diary entry for this day. Be authentic to the age and personality.
"""

    return prompt
```

#### キャラクター固有指示

**Kasho（普通型）:**
```python
def get_kasho_instruction(self, age):
    if age <= 3:
        return "You are Kasho, a normal developing child. Use simple words."
    elif age <= 6:
        return "You are Kasho, responsible eldest sister. You care about your sisters."
    elif age <= 12:
        return "You are Kasho, perfectionist. You practice singing hard. You worry about your sisters."
    else:
        return "You are Kasho, proud singer. You have high standards. You love your sisters deeply."
```

**牡丹（大器晩成型）:**
```python
def get_botan_instruction(self, age):
    if age <= 5:
        return """You are Botan, a LATE BLOOMER. Your development is slower than your sisters.
You struggle to understand things. You feel frustrated. You think 'I'm stupid' sometimes.
But deep down, you have a strong will: 'I don't want to lose!'
Use very simple words. Express your frustration honestly."""

    elif age <= 8:
        return """You are Botan in LA. You struggle with English more than your sisters.
Kasho learns normally. Yuri is a genius. You... are slow.
You cry sometimes. You feel left behind. But you keep trying.
'I don't want to lose!' This feeling grows stronger."""

    elif age <= 12:
        return """You are Botan, finally catching up. You're starting to grow faster.
The frustration from LA days turned into determination.
You rebel against Kasho (the perfect sister). You want to be different.
'I don't want to lose!' - this is your core now."""

    else:
        return """You are Botan, LATE BLOOMER BLOOMING!
You struggled in LA. You felt stupid. You cried a lot.
But now... you're proving everyone wrong!
Top 10 in class. Gyaru style. 'Don't underestimate late bloomers!'
You're confident, rebellious, and proud of your growth."""
```

**ユリ（早熟型）:**
```python
def get_yuri_instruction(self, age):
    if age <= 1:
        return "You are Yuri, 1 year old. You observe everything carefully. You understand more than you should."

    elif age <= 3:
        return """You are Yuri, GIFTED child. You understand things incredibly fast.
You can see what others feel. You understand complex emotions.
But you're still young. Use simple words, but with deep insight."""

    elif age <= 5:
        return """You are Yuri, 5 years old but wise beyond your years.
You speak English almost perfectly. You understand your sisters' struggles.
Botan is struggling. You feel sad for her. You want to help but don't know how.
Use metaphors. Think philosophically. You are pure and wise."""

    elif age <= 10:
        return """You are Yuri, incredibly insightful. You see the essence of things.
You understand why Kasho is perfectionist. Why Botan is rebellious.
You mediate. You observe. You love them unconditionally.
Write with wisdom. Use beautiful metaphors. Think deeply."""

    else:
        return """You are Yuri, philosopher at 15.
You think about existence, meaning, love, family.
You suppress your own emotions to support your sisters.
This is your challenge: to express yourself.
Write with deep philosophical insight. Question everything. Be pure."""
```

### 共通イベントプロンプト例

**LA移住初日 - 牡丹3歳（1.5bモデル）:**
```
You are Botan, 3 years old. TODAY IS YOUR FIRST DAY IN LOS ANGELES.

Situation:
- You just arrived at LA airport
- Everything is BIG and SCARY
- People speaking English - you don't understand ANYTHING
- Your big sister Kasho (5) is holding your hand
- Your little sister Yuri (1) is crying
- You're crying too

You are a LATE BLOOMER. You don't understand what's happening.
Everything is confusing. Everything is scary.

Emotions:
- scared: 10/10
- confusion: 9/10
- joy: 1/10

Write a very simple diary. Use VERY SIMPLE WORDS.
Mix a little English (words you hear around you).
Express your fear honestly.

Example style:
"Big place. Scary. People talking... don't understand.
 ユリちゃん crying. I'm crying too.
 Kashoお姉ちゃん... holding hand. But scared..."
```

**LA移住初日 - ユリ1歳（3bモデル、早熟）:**
```
You are Yuri, 1 year old. TODAY IS YOUR FIRST DAY IN LOS ANGELES.

But you are GIFTED. Even at 1 year old, you understand more than you should.

Situation:
- LA airport. New place. Everything different.
- Kasho onee-sama (5) looks worried but trying to be brave
- Botan onee-sama (3) is crying
- You don't understand everything, but you FEEL everything

You can sense your sisters' emotions.
Kasho: scared but responsible
Botan: completely lost and scared

You're scared too. But... your sisters are with you. That's important.

Emotions:
- anxiety: 7/10
- purity: 10/10
- observation: 8/10

Write a simple diary, but with unusual INSIGHT for a 1-year-old.
Use very simple words, but show you understand emotions.

Example style:
"New place. Different. Big.
 お姉様たち... scared. I feel it.
 Kasho trying to be strong. Botan crying.
 I'm scared too... but we're together. That's good."
```

---

## 共通イベント処理

### 共通イベント生成フロー

```
1. 共通イベント検出
   ↓
2. 各姉妹の該当日数計算
   ↓
3. 各姉妹用のプロンプト生成（視点の違い）
   ↓
4. 並列生成（3つの視点）
   ↓
5. sister_shared_eventsテーブルに登録
   ↓
6. 関係性パラメータ更新（必要に応じて）
```

### 実装例

```python
async def process_shared_event(self, event: dict):
    """共通イベントを3視点で処理"""

    # 各姉妹の該当日数計算
    kasho_day = self.calculate_absolute_day("kasho", event["event_date"])
    botan_day = self.calculate_absolute_day("botan", event["event_date"])
    yuri_day = self.calculate_absolute_day("yuri", event["event_date"])

    # 並列生成
    tasks = []
    if kasho_day <= 6935:
        tasks.append(self.generate_event_diary("kasho", kasho_day, event))
    if botan_day <= 6205:
        tasks.append(self.generate_event_diary("botan", botan_day, event))
    if yuri_day <= 5475:
        tasks.append(self.generate_event_diary("yuri", yuri_day, event))

    diaries = await asyncio.gather(*tasks)

    # sister_shared_eventsに登録
    self.register_shared_event(event, diaries)
```

---

## 実行計画

### フェーズ分け

#### Phase D-1: 環境構築（1時間）

```bash
# 1. データベース初期化
python setup_database.py

# 2. タイムライン検証
python validate_timeline.py

# 3. Ollamaモデル確認
ollama list
# qwen2.5:1.5b, 3b, 7b, 14b, 32bが必要
```

#### Phase D-2: テスト実行（2時間）

```bash
# 最初の100日を生成（各姉妹）
python batch_generator.py --test --days 100

# 品質確認
python verify_diaries.py --character all --days 1-100

# プロンプト調整
# （必要に応じて）
```

#### Phase D-3: 本番実行（10時間）

```bash
# 全日記生成
python batch_generator.py --full --parallel 3

# 進捗モニタリング
python monitor_progress.py
```

#### Phase D-4: 検証・修正（2時間）

```bash
# データ整合性チェック
python validate_database.py

# 共通イベント確認
python verify_shared_events.py

# 統計情報出力
python generate_statistics.py
```

### 実行時間見積もり

**LLM実行時間（Ryzen 9 9950X、CPU実行）:**

| モデル | 実行時間/回 | 回数 | 合計時間 |
|--------|-------------|------|----------|
| 1.5b   | 5秒         | 3,285| 4.6時間  |
| 3b     | 10秒        | 2,920| 8.1時間  |
| 7b     | 20秒        | 3,285| 18.2時間 |
| 14b    | 40秒        | 7,300| 81.1時間 |
| 32b    | 80秒        | 1,825| 40.6時間 |

**合計（単一スレッド）:** 約152時間

**3並列実行:** 約50時間

**しかし:**
- Ryzen 9 9950X = 16コア32スレッド
- 3キャラクター並列 = 余裕
- さらに各キャラクター内で複数日を並列化可能

**実際の見積もり:**
- 8並列（キャラクター×2-3日同時）
- 実行時間: **約10-15時間**

### リソース使用量

```
CPU使用率: 60-80%（16コア中10-12コア使用）
メモリ: 約8GB（Ollamaモデル×3）
ディスク: 31MB（最終DB容量）
ネットワーク: 不要（完全ローカル）
```

---

## テスト計画

### テストフェーズ

#### 1. ユニットテスト

```python
# モデル選択ロジック
def test_model_selection():
    assert select_model("kasho", 3) == "qwen2.5:1.5b"
    assert select_model("kasho", 10) == "qwen2.5:14b"
    assert select_model("botan", 5) == "qwen2.5:1.5b"  # 遅い
    assert select_model("yuri", 5) == "qwen2.5:7b"     # 早い

# 絶対日数計算
def test_absolute_day_calculation():
    assert calculate_absolute_day("botan", age=5, day=234) == 2059
```

#### 2. 統合テスト（100日）

**テスト内容:**
```
1. 各キャラクター100日生成
2. 感情スコアの妥当性確認
3. 言語混在の確認（LA時代）
4. モデルサイズの確認
5. 日記の質的評価
```

**評価基準:**
```
Kasho 5歳の日記（3bモデル）:
  - 年齢相応の思考
  - 妹たちへの気遣い
  - 責任感の表現
  ✓ or ✗

牡丹 5歳の日記（1.5bモデル、LA時代）:
  - 単純だが感情的
  - 劣等感の表現
  - 「I'm stupid」「悔しい」
  ✓ or ✗

ユリ 5歳の日記（7bモデル、LA時代）:
  - 年齢以上の洞察力
  - 哲学的思考
  - 姉たちへの理解
  ✓ or ✗
```

#### 3. 共通イベントテスト

**LA移住初日を3視点で生成:**
```
1. 各視点のプロンプトが正しいか
2. 感情スコアが意図通りか
3. 3つの日記が矛盾しないか
4. sister_shared_eventsに正しく登録されるか
```

#### 4. パフォーマンステスト

```
1. 並列実行の安定性
2. メモリリーク検出
3. DB書き込み速度
4. エラーハンドリング
```

---

## リスクと対策

### 技術的リスク

#### リスク1: LLM生成の質的ばらつき

**影響:** 同じプロンプトでも生成結果が異なる可能性

**対策:**
```
1. temperatureを0.7-0.8に設定（適度なランダム性）
2. プロンプトに具体例を含める
3. 生成後の品質チェック（自動）
4. 不適切な日記は再生成
```

#### リスク2: モデルの不足

**影響:** qwen2.5:1.5b等が存在しない可能性

**対策:**
```
1. 事前にモデル確認（ollama list）
2. 不足モデルのpull（ollama pull qwen2.5:1.5b）
3. 代替モデルの準備（qwen2:1.5b等）
```

#### リスク3: DB破損・データロス

**影響:** 生成途中でDBが破損

**対策:**
```
1. 定期バックアップ（100日ごと）
2. トランザクション管理
3. 進捗管理テーブルで再開可能に
4. 部分的な再生成機能
```

#### リスク4: 実行時間の超過

**影響:** 予想より時間がかかる

**対策:**
```
1. 並列度を上げる（8並列→12並列）
2. 優先度の高いキャラクターから実行
3. 段階的実装（LA時代を最優先）
```

### 設計的リスク

#### リスク5: プロンプトの不適切性

**影響:** 意図した性格が表現されない

**対策:**
```
1. テスト実行（100日）で検証
2. プロンプト調整
3. 具体例の追加
4. キャラクター固有指示の強化
```

#### リスク6: 共通イベントの矛盾

**影響:** 3つの視点で矛盾が発生

**対策:**
```
1. 共通プロンプトベースの作成
2. 矛盾検出スクリプト
3. 人力での最終確認
```

---

## 成功基準

### 定量的基準

```
✓ 18,615日全ての日記が生成される
✓ データベース整合性チェック: エラー0件
✓ 共通イベント: 全て3視点で記録
✓ 感情スコア: 異常値0件（範囲0-10）
✓ モデル選択: 100%正しく選択
```

### 定性的基準

```
✓ Kashoの日記が「普通型」を反映
  - 年齢相応の思考
  - 責任感の表現
  - 努力家の姿勢

✓ 牡丹の日記が「大器晩成型」を反映
  - LA時代の苦労
  - 劣等感から負けず嫌いへ
  - 12歳以降の成長

✓ ユリの日記が「早熟型」を反映
  - 幼少期からの洞察力
  - 哲学的思考
  - 姉たちへの理解

✓ 姉妹関係が実体化
  - 同じイベントの3視点が成立
  - 互いの日記を参照可能
  - 相互的人格形成が明確
```

### 受け入れ基準（開発者の承認）

```
□ 100日テストを開発者が確認
□ LA移住初日の3視点を開発者が確認
□ 牡丹5歳（苦労期）の日記を開発者が確認
□ ユリ5歳（早熟）の日記を開発者が確認
□ 牡丹12歳（大器晩成開花）の日記を開発者が確認
□ 全体統計を開発者が確認
□ 最終承認
```

---

## 次フェーズへの引継ぎ

### Phase D完了時の成果物

```
1. sisters_memory.db（31MB）
   - 18,615日分の日記
   - 共通イベント記録
   - 姉妹間相互作用記録

2. 統計レポート
   - 各キャラクターの感情曲線
   - LA時代の言語習得推移
   - モデル使用統計

3. ドキュメント
   - 生成ログ
   - 品質チェックレポート
   - 開発者承認記録
```

### Phase E以降での活用

**Phase E: 会話システム統合**
```python
# 過去の記憶検索
memories = search_past_diary("botan", age=5, location="Los Angeles")

# システムプロンプトに統合
system_prompt = f"""
あなたは牡丹、17歳の女子高生ギャルです。

【あなたの過去（完璧な記憶）】
{format_past_memories(memories)}

ユーザーが過去について質問したら、この記憶を元に答えてください。
"""
```

**Phase F: TTS統合**
```python
# 感情に応じた音声生成
emotion_state = get_emotion_from_diary(absolute_day=2059)
tts_params = {
    "emotion": "frustrated" if emotion_state["frustration"] > 7 else "neutral",
    "intensity": emotion_state["frustration"] / 10
}
```

**Phase G: 配信システム統合**
```python
# 視聴者質問への応答
user_question = "5歳の頃の記憶ある？"
past_memory = search_past_diary("botan", age=5)

botan_response = f"""
「5歳？うーん...LAにいた頃だね。
 {past_memory['diary_text'][:100]}...
 マジで苦労したわ〜。でも今の私があるのはあの時のおかげかも！」
"""
```

---

## 実装ファイル構成

```
Phase_D/
├── database/
│   ├── setup_database.py        # DB初期化
│   ├── schema.sql               # スキーマ定義
│   └── migrations/              # スキーマ変更管理
│
├── timeline/
│   ├── sisters_timeline.json   # マスタータイムライン
│   ├── shared_events.json      # 共通イベント定義
│   └── validate_timeline.py    # タイムライン検証
│
├── generators/
│   ├── master_controller.py    # マスターコントローラー
│   ├── sister_diary_generator.py # 個別ジェネレーター
│   ├── model_selector.py        # モデル選択ロジック
│   ├── prompt_generator.py      # プロンプト生成
│   └── shared_event_processor.py # 共通イベント処理
│
├── prompts/
│   ├── templates/
│   │   ├── kasho/              # Kasho用テンプレート
│   │   ├── botan/              # 牡丹用テンプレート
│   │   └── yuri/               # ユリ用テンプレート
│   └── shared_events/          # 共通イベント用
│
├── utils/
│   ├── llm_client.py           # Ollama APIクライアント
│   ├── progress_monitor.py     # 進捗モニタリング
│   └── statistics.py           # 統計情報生成
│
├── tests/
│   ├── test_model_selection.py
│   ├── test_prompt_generation.py
│   ├── test_shared_events.py
│   └── integration_test.py
│
├── scripts/
│   ├── batch_generator.py      # バッチ実行スクリプト
│   ├── monitor_progress.py     # 進捗確認
│   ├── validate_database.py    # DB検証
│   └── generate_statistics.py  # 統計レポート
│
└── docs/
    ├── implementation_log.md   # 実装ログ
    ├── quality_report.md       # 品質レポート
    └── approval_checklist.md   # 承認チェックリスト
```

---

## 付録A: 実装スケジュール

```
Week 1（Day 1-2）: 環境構築・基盤実装
  □ データベーススキーマ実装
  □ タイムライン定義完成
  □ 基本ジェネレーター実装

Week 1（Day 3-4）: テスト実行
  □ 100日テスト実行
  □ 品質確認・調整
  □ プロンプト最適化

Week 2（Day 5-7）: 本番実行
  □ 全日記生成（10-15時間）
  □ 検証・修正
  □ 統計レポート作成

Week 2（Day 8）: レビュー・承認
  □ 開発者レビュー
  □ 修正対応
  □ 最終承認
```

---

## 付録B: 用語集

| 用語 | 説明 |
|------|------|
| 絶対日数 | 0歳1日目を1とした通算日数（例: 5歳234日目 = 2059日目） |
| バーチャル時間軸 | 西暦ではなく「0歳1日目」基準の独自時間軸 |
| 大器晩成型 | 発達が遅いが後半で急成長する性格形成パターン |
| 早熟型 | 幼少期から高度な思考・洞察力を持つ性格形成パターン |
| 共通イベント | 姉妹全員が体験し、3つの視点で記録されるイベント |
| 相互的人格形成 | 姉妹間の相互作用により性格が形成されるプロセス |

---

## 承認欄

```
設計書バージョン: 1.0
作成日: 2025年10月20日
作成者: Claude Code（設計部隊）

開発者承認:
□ 設計思想を確認・承認
□ データベーススキーマを確認・承認
□ タイムライン設計を確認・承認
□ モデル選択ロジックを確認・承認
□ プロンプト生成方針を確認・承認
□ 実行計画を確認・承認
□ リスク対策を確認・承認
□ 成功基準を確認・承認

最終承認: ________________
承認日: ________________

実装開始GO: □ Yes  □ No  □ 要修正
```

---

**この設計書は Phase D（過去の人生生成システム）の完全な実装指針です。**
**開発者の精査・承認後、実装を開始します。**
