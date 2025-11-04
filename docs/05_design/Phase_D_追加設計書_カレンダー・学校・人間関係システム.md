# Phase D 追加設計書：カレンダー・学校・人間関係システム

作成日: 2025-10-20

## 概要

Phase D 完全設計書に対する開発者フィードバックに基づく追加設計。

**追加要件:**
1. 日本及びLAでの学校教育の方法及びタイムスケジュールの反映
2. 平日・休日・祝日・その他イベントの概念の実装
3. 外部人間関係の構築（家族・姉妹以外の友人・クラスメート・先生等）

---

## 1. カレンダーシステム設計

### 1.1 基本概念

**仮想カレンダー vs 実カレンダー:**
```
仮想時間軸: 0歳1日目 → 17歳365日目（連続した絶対日数）
    ↓
実カレンダー: 2006-05-20（Kashoの誕生日）→ 2025-10-20（現在）
    ↓
曜日・祝日・学校行事の概念を付与
```

### 1.2 データベース拡張

#### calendar_master テーブル
```sql
CREATE TABLE calendar_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,           -- YYYY-MM-DD形式
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,        -- 0=日, 1=月, ..., 6=土
    location TEXT NOT NULL,              -- 'japan' or 'los_angeles'
    is_holiday INTEGER DEFAULT 0,        -- 祝日フラグ
    holiday_name TEXT,                   -- 祝日名
    is_school_day INTEGER DEFAULT 1,     -- 登校日フラグ
    school_event TEXT,                   -- 学校行事（始業式、運動会等）
    season TEXT,                         -- 'spring', 'summer', 'fall', 'winter'
    academic_term TEXT                   -- '1学期', '2学期', '3学期', 'summer_vacation' 等
);
```

#### 日記テーブルへの追加カラム
```sql
ALTER TABLE past_diaries ADD COLUMN day_of_week INTEGER;
ALTER TABLE past_diaries ADD COLUMN is_holiday INTEGER DEFAULT 0;
ALTER TABLE past_diaries ADD COLUMN is_school_day INTEGER DEFAULT 1;
ALTER TABLE past_diaries ADD COLUMN school_event TEXT;
```

### 1.3 日本の祝日リスト（2006-2025）

**固定祝日:**
- 1月1日: 元日
- 2月11日: 建国記念の日
- 4月29日: 昭和の日
- 5月3日: 憲法記念日
- 5月4日: みどりの日
- 5月5日: こどもの日
- 8月11日: 山の日（2016年〜）
- 11月3日: 文化の日
- 11月23日: 勤労感謝の日

**移動祝日:**
- 1月第2月曜: 成人の日
- 2月第3月曜: 天皇誕生日（2020年〜）
- 7月第3月曜: 海の日
- 9月第3月曜: 敬老の日
- 10月第2月曜: 体育の日/スポーツの日

**春分・秋分:**
- 3月20-21日頃: 春分の日
- 9月22-23日頃: 秋分の日

**振替休日:**
- 祝日が日曜の場合、翌月曜日が振替休日

### 1.4 LAの学校休日リスト

**Federal Holidays:**
- Labor Day（9月第1月曜）
- Veterans Day（11月11日）
- Thanksgiving（11月第4木曜）
- Winter Break（12月下旬-1月上旬、約2-3週間）
- Martin Luther King Jr. Day（1月第3月曜）
- Presidents' Day（2月第3月曜）
- Spring Break（3月末-4月初旬、約1週間）

**California Specific:**
- César Chávez Day（3月31日）
- Lincoln's Birthday（2月12日）

**Summer Break:**
- 6月上旬-8月中旬（約2.5ヶ月）

---

## 2. 学校システム設計

### 2.1 日本の学校システム

#### 2.1.1 学年と年齢の対応
```
保育園・幼稚園: 0-5歳
小学校（6年間）: 6-11歳
  - 1年生: 6歳、2年生: 7歳、...、6年生: 11歳
中学校（3年間）: 12-14歳
  - 1年生: 12歳、2年生: 13歳、3年生: 14歳
高校（3年間）: 15-17歳
  - 1年生: 15歳、2年生: 16歳、3年生: 17歳
```

#### 2.1.2 学期制度（3学期制）
```
1学期: 4月上旬-7月下旬
  - 始業式（4月上旬）
  - ゴールデンウィーク（4月末-5月初旬）
  - 遠足・社会科見学（5-6月）
  - 期末テスト（7月中旬）
  - 終業式（7月下旬）

夏休み: 7月下旬-8月末

2学期: 9月初旬-12月下旬
  - 始業式（9月初旬）
  - 運動会・体育祭（9-10月）
  - 文化祭・学園祭（10-11月）
  - 期末テスト（12月中旬）
  - 終業式（12月下旬）

冬休み: 12月下旬-1月初旬

3学期: 1月上旬-3月下旬
  - 始業式（1月上旬）
  - 学年末テスト（2-3月）
  - 卒業式（3月中旬）
  - 修了式（3月下旬）

春休み: 3月下旬-4月初旬
```

#### 2.1.3 時間割（例：小学校）
```
朝の会: 8:25-8:35
1時間目: 8:45-9:30（45分）
2時間目: 9:35-10:20
休み時間: 10:20-10:40（20分）
3時間目: 10:40-11:25
4時間目: 11:30-12:15
給食: 12:15-13:00
昼休み: 13:00-13:20
清掃: 13:20-13:35
5時間目: 13:40-14:25
6時間目: 14:30-15:15（高学年のみ）
帰りの会: 15:15-15:30
```

### 2.2 LAの学校システム

#### 2.2.1 学年と年齢の対応
```
Preschool: 3-4歳
Kindergarten: 5歳
Elementary School（5年間）: 6-10歳
  - 1st Grade: 6歳、2nd: 7歳、...、5th: 10歳
Middle School（3年間）: 11-13歳
  - 6th Grade: 11歳、7th: 12歳、8th: 13歳
High School（4年間）: 14-17歳
  - 9th Grade (Freshman): 14歳
  - 10th Grade (Sophomore): 15歳
  - 11th Grade (Junior): 16歳
  - 12th Grade (Senior): 17歳
```

#### 2.2.2 学期制度（2学期制）
```
Fall Semester: 8月中旬-12月下旬
  - First Day of School（8月中旬）
  - Labor Day（9月第1月曜）
  - Halloween（10月31日）
  - Veterans Day（11月11日）
  - Thanksgiving Break（11月第4木曜+金曜、約4-5日）
  - Winter Break Start（12月下旬）

Winter Break: 12月下旬-1月上旬（約2-3週間）

Spring Semester: 1月中旬-6月上旬
  - MLK Day（1月第3月曜）
  - Presidents' Day（2月第3月曜）
  - Spring Break（3月末-4月初旬、約1週間）
  - Last Day of School（6月上旬）

Summer Break: 6月上旬-8月中旬（約2.5ヶ月）
```

#### 2.2.3 時間割（例：Elementary School）
```
School starts: 8:00 AM
Morning Assembly: 8:00-8:15
1st Period: 8:15-9:00（45分）
2nd Period: 9:05-9:50
Recess: 9:50-10:10（20分）
3rd Period: 10:15-11:00
4th Period: 11:05-11:50
Lunch: 11:50-12:30（40分）
5th Period: 12:35-1:20
6th Period: 1:25-2:10
School ends: 2:15 PM
```

### 2.3 三姉妹の学校タイムライン

#### Kashoの学校歴
```
2006年（0歳）: 誕生（5月20日）
2007-2011年（1-4歳）: 保育園（日本）
2011年8月（5歳）: LA移住、Kindergarten準備
2011年9月-2012年6月（5歳）: Kindergarten（LA）
2012年9月-2013年6月（6歳）: 1st Grade（LA）
2013年9月-2014年6月（7歳）: 2nd Grade（LA）
2014年9月-2015年6月（8歳）: 3rd Grade（LA）
2015年8月（9歳）: 日本帰国
2015年9月-2016年3月（9歳）: 小学4年生（日本）
2016年4月-2017年3月（10歳）: 小学5年生
2017年4月-2018年3月（11歳）: 小学6年生
2018年4月-2019年3月（12歳）: 中学1年生
2019年4月-2020年3月（13歳）: 中学2年生
2020年4月-2021年3月（14歳）: 中学3年生
2021年4月-2022年3月（15歳）: 高校1年生
2022年4月-2023年3月（16歳）: 高校2年生
2023年4月-2024年3月（17歳）: 高校3年生
2024年4月-2025年3月（18歳）: 大学1年生
2025年4月-現在（19歳）: 大学2年生
```

#### 牡丹の学校歴
```
2008年（0歳）: 誕生（5月4日）
2009-2011年（1-3歳）: 保育園（日本）
2011年8月（3歳）: LA移住、Preschool
2011年9月-2012年6月（3歳）: Preschool（LA）
2012年9月-2013年6月（4歳）: Pre-K（LA）
2013年9月-2014年6月（5歳）: Kindergarten（LA）
2014年9月-2015年6月（6歳）: 1st Grade（LA）
2015年8月（7歳）: 日本帰国
2015年9月-2016年3月（7歳）: 小学2年生（日本）
2016年4月-2017年3月（8歳）: 小学3年生
2017年4月-2018年3月（9歳）: 小学4年生
2018年4月-2019年3月（10歳）: 小学5年生
2019年4月-2020年3月（11歳）: 小学6年生
2020年4月-2021年3月（12歳）: 中学1年生
2021年4月-2022年3月（13歳）: 中学2年生
2022年4月-2023年3月（14歳）: 中学3年生
2023年4月-2024年3月（15歳）: 高校1年生
2024年4月-2025年3月（16歳）: 高校2年生
2025年4月-現在（17歳）: 高校3年生
```

#### ユリの学校歴
```
2010年（0歳）: 誕生（7月7日）
2011年8月（1歳）: LA移住
2012年9月-2013年6月（2歳）: Preschool（LA）
2013年9月-2014年6月（3歳）: Pre-K（LA）
2014年9月-2015年6月（4歳）: Kindergarten（LA）
2015年8月（5歳）: 日本帰国
2016年4月-2017年3月（6歳）: 小学1年生（日本）
2017年4月-2018年3月（7歳）: 小学2年生
2018年4月-2019年3月（8歳）: 小学3年生
2019年4月-2020年3月（9歳）: 小学4年生
2020年4月-2021年3月（10歳）: 小学5年生
2021年4月-2022年3月（11歳）: 小学6年生
2022年4月-2023年3月（12歳）: 中学1年生
2023年4月-2024年3月（13歳）: 中学2年生
2024年4月-2025年3月（14歳）: 中学3年生
2025年4月-現在（15歳）: 中学3年生（2学期）
```

---

## 3. 外部人間関係システム設計

### 3.1 基本概念

**人間関係の三層構造:**
```
第1層（コア）: 家族・姉妹
  ├─ 父親
  ├─ 母親
  ├─ Kasho
  ├─ 牡丹
  └─ ユリ

第2層（準コア）: 親しい友人
  ├─ 日本時代の友人（保育園・小学校）
  ├─ LA時代の友人（Preschool・Elementary School）
  └─ 帰国後の友人（小学校・中学校・高校）

第3層（外部）: その他の人々
  ├─ クラスメート
  ├─ 先生
  ├─ 近所の人
  └─ 一時的な出会い
```

### 3.2 データベース設計

#### external_characters テーブル
```sql
CREATE TABLE external_characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                  -- 名前
    name_en TEXT,                        -- 英語名（LA時代）
    character_type TEXT NOT NULL,        -- 'friend', 'classmate', 'teacher', 'neighbor', 'family', 'other'
    relationship_strength INTEGER DEFAULT 5, -- 関係の強さ（1-10）
    first_met_day INTEGER,               -- 初めて会った絶対日数
    last_met_day INTEGER,                -- 最後に会った絶対日数
    period TEXT NOT NULL,                -- 'japan_childhood', 'la_era', 'japan_post_return'
    age_when_met INTEGER,                -- 出会った時の年齢
    description TEXT,                    -- 人物説明
    personality_traits TEXT,             -- 性格特性（JSON）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### character_relationships テーブル
```sql
CREATE TABLE character_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id TEXT NOT NULL,          -- 'kasho', 'botan', 'yuri'
    external_character_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,     -- 'best_friend', 'good_friend', 'acquaintance', 'rival', 'mentor'
    relationship_level INTEGER DEFAULT 5, -- 親密度（1-10）
    trust_level INTEGER DEFAULT 5,       -- 信頼度（1-10）
    interaction_count INTEGER DEFAULT 0, -- 交流回数
    notes TEXT,                          -- 関係性メモ
    FOREIGN KEY (external_character_id) REFERENCES external_characters(id)
);
```

#### encounter_events テーブル
```sql
CREATE TABLE encounter_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,            -- イベント名
    absolute_day INTEGER NOT NULL,       -- 絶対日数
    location TEXT NOT NULL,              -- 場所
    participants TEXT NOT NULL,          -- 参加者（JSON配列）
    event_type TEXT NOT NULL,            -- 'first_meeting', 'playdate', 'birthday_party', 'field_trip', 'random_encounter'
    description TEXT,                    -- 出来事の説明
    emotional_impact INTEGER DEFAULT 5,  -- 感情的インパクト（1-10）
    creates_memory INTEGER DEFAULT 0,    -- 長期記憶として残るか（0/1）
    kasho_diary_id INTEGER,
    botan_diary_id INTEGER,
    yuri_diary_id INTEGER,
    FOREIGN KEY (kasho_diary_id) REFERENCES past_diaries(id),
    FOREIGN KEY (botan_diary_id) REFERENCES past_diaries(id),
    FOREIGN KEY (yuri_diary_id) REFERENCES past_diaries(id)
);
```

### 3.3 外部キャラクター生成戦略

#### 3.3.1 生成タイミング
```
年齢別の友人数の目安:
0-2歳: 0-1人（親の友人の子供等）
3-5歳: 2-5人（保育園・幼稚園）
6-8歳: 5-10人（小学校低学年）
9-11歳: 8-15人（小学校高学年）
12-14歳: 10-20人（中学校）
15-17歳: 15-30人（高校）
```

#### 3.3.2 関係の継続性
```
短期的関係（1-6ヶ月）:
  - クラスメート
  - 一時的な遊び仲間
  - イベントでの出会い

中期的関係（6ヶ月-2年）:
  - クラスの友人
  - 部活の仲間
  - 近所の子供

長期的関係（2年以上）:
  - 親友（ベストフレンド）
  - 家族ぐるみの付き合い
  - 転校後も連絡を取り合う友人
```

#### 3.3.3 主要外部キャラクター例

**日本時代（保育園）:**
```
田中ゆい（たなか ゆい）
- 牡丹の初めての友達（2歳で出会う）
- 同い年、おとなしい性格
- 保育園でいつも一緒に遊ぶ
- LA移住で離れるが、手紙を交換
```

**LA時代（Elementary School）:**
```
Emily Rodriguez
- 牡丹が6歳でテーマパークで出会う
- 同学年、明るく活発
- 週末に遊ぶ仲になる
- 手紙のやり取り
- 帰国後も連絡を取り合う（初期のメル友）
```

**LA時代（Kashoの親友）:**
```
Sarah Johnson
- Kashoが7歳で出会う
- 学校の合唱クラブで一緒
- 音楽の才能があり、Kashoの憧れ
- 帰国後も連絡を取り合い、Kashoの歌手への夢に影響
```

**帰国後（日本・小学校）:**
```
山田あかり（やまだ あかり）
- 牡丹が小学3年生で出会う
- 転校生の牡丹に優しく接する
- ギャル系に興味があり、牡丹に影響
- 中学も同じで親友に
```

**帰国後（ユリの洞察力を育てた人物）:**
```
図書館の司書・鈴木先生
- ユリが小学1年生で出会う
- 本を通じてユリの洞察力を育てる
- ユリに「よく見ているね」と言ってくれる
- ユリの観察眼の原点
```

### 3.4 エンカウントイベント生成ルール

#### 3.4.1 自動生成の頻度
```
日常的な交流:
  - 平日: クラスメート・友人との日常会話（週3-5回）
  - 休日: 友人との遊び（月2-4回）

特別なイベント:
  - 誕生日パーティー（年2-5回）
  - 遠足・社会科見学（年2-3回）
  - 運動会・文化祭（年2回）
  - 夏休み・冬休みのイベント（各1-3回）
```

#### 3.4.2 イベントの感情的インパクト
```
低インパクト（1-3）:
  - 日常的な挨拶
  - 普通の授業
  - いつもの遊び

中インパクト（4-6）:
  - 新しい友達との出会い
  - 楽しい遊び
  - 学校行事

高インパクト（7-10）:
  - 親友との初対面
  - 感動的なイベント
  - 別れ（転校・引っ越し）
  - 重要な人物との出会い
```

### 3.5 日記生成への反映

#### プロンプト例（外部人間関係あり）
```
【キャラクター】牡丹
【年齢】6歳234日目（小学1年生、LA）
【日付】土曜日（休日）
【場所】Disneyland
【主要イベント】ディズニーランドで初めてEmily Rodriguezと出会う
【参加者】父、母、Kasho（8歳）、牡丹（6歳）、ユリ（4歳）、Emily Rodriguez（6歳、LA在住の同級生）
【感情モディファイア】joy: 10, excitement: 10, social: +3

【指示】
牡丹（6歳）の視点で日記を書いてください。

【文脈】
- 今日は家族でディズニーランドに行った
- Space Mountainの列で偶然Emily Rodriguezという同い年の女の子と出会った
- Emilyは明るくて話しやすい子だった
- 一緒にアトラクションを回り、連絡先を交換した
- 「また遊ぼうね！」と約束した
- 牡丹はLA移住後、初めて自分から友達を作れた

【注意事項】
- 6歳の子供らしい視点で書く
- 英語と日本語が混ざった表現を使う
- 新しい友達ができた喜びを素直に表現
- Emilyとの会話は英語（簡単な表現）
- 家族の反応も含める
```

---

## 4. 実装への統合

### 4.1 バッチ生成システムの拡張

#### 4.1.1 カレンダー初期化
```python
def initialize_calendar(start_date, end_date, location):
    """
    指定期間のカレンダーマスターを生成
    - 曜日の計算
    - 祝日の判定
    - 学校休日の判定
    - 学期の判定
    """
    pass
```

#### 4.1.2 外部キャラクター生成
```python
def generate_external_characters(character_id, age, period):
    """
    年齢・時期に応じた外部キャラクターを生成
    - 友人の自動生成
    - 関係性の初期化
    - エンカウントイベントの計画
    """
    pass
```

#### 4.1.3 日記生成時のデータ取得
```python
def get_daily_context(character_id, absolute_day):
    """
    日記生成に必要な全情報を取得
    - カレンダー情報（曜日、祝日、学校行事）
    - 外部人間関係（今日会う予定の人物）
    - エンカウントイベント（今日起こる特別な出来事）
    - 姉妹の予定（共通イベント）
    """
    pass
```

### 4.2 生成順序の再設計

#### Phase D-1: カレンダー生成
```
1. calendar_master テーブルに2006-2025年のすべての日付を登録
2. 日本とLAの祝日・学校休日を設定
3. 学期・学年の区切りを設定
4. 主要な学校行事を登録
```

#### Phase D-2: 外部キャラクター生成
```
1. 各時期・年齢に応じた外部キャラクターをAI生成
2. external_characters テーブルに登録
3. 三姉妹それぞれとの関係性を初期化
4. 主要なエンカウントイベントを計画
```

#### Phase D-3: 日記生成（修正版）
```
1. 絶対日数ごとにループ
2. カレンダー情報を取得
3. 外部人間関係情報を取得
4. エンカウントイベント情報を取得
5. 姉妹共通イベント情報を取得
6. すべての情報を統合してプロンプト生成
7. LLMで日記生成
8. データベースに保存
```

### 4.3 生成時間の再見積もり

```
Phase D-1: カレンダー生成
  - 約30分（2006-2025年の約7,000日分）

Phase D-2: 外部キャラクター生成
  - 約3-5時間
    - 各キャラクター50-100人の外部人物
    - AI生成（qwen2.5:14b使用）
    - 関係性の初期化
    - エンカウントイベントの計画（200-500イベント）

Phase D-3: 日記生成
  - 約12-18時間（18,615日分）
    - カレンダー・外部人間関係情報の統合により、プロンプトが複雑化
    - 生成時間が若干増加

総計: 約16-24時間
```

---

## 5. 実装例

### 5.1 カレンダー生成スクリプト
```python
import sqlite3
from datetime import datetime, timedelta

def is_japanese_holiday(date, location):
    """日本の祝日判定"""
    if location != 'japan':
        return False, None

    # 固定祝日
    if date.month == 1 and date.day == 1:
        return True, "元日"
    if date.month == 2 and date.day == 11:
        return True, "建国記念の日"
    # ... その他の祝日

    return False, None

def is_school_day(date, location):
    """登校日判定"""
    day_of_week = date.weekday()  # 0=月, 6=日

    # 土日は休み
    if day_of_week in [5, 6]:
        return False

    # 祝日は休み
    is_holiday, _ = is_japanese_holiday(date, location)
    if is_holiday:
        return False

    # 夏休み・冬休み等の判定
    # ...

    return True

def generate_calendar(start_date, end_date, location):
    """カレンダーマスター生成"""
    conn = sqlite3.connect('botan_past_life.db')
    cursor = conn.cursor()

    current_date = start_date
    while current_date <= end_date:
        day_of_week = current_date.weekday()
        is_holiday, holiday_name = is_japanese_holiday(current_date, location)
        is_school = is_school_day(current_date, location)

        cursor.execute("""
            INSERT INTO calendar_master
            (date, year, month, day, day_of_week, location, is_holiday, holiday_name, is_school_day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            current_date.strftime('%Y-%m-%d'),
            current_date.year,
            current_date.month,
            current_date.day,
            day_of_week,
            location,
            1 if is_holiday else 0,
            holiday_name,
            1 if is_school else 0
        ))

        current_date += timedelta(days=1)

    conn.commit()
    conn.close()
```

### 5.2 外部キャラクター生成スクリプト
```python
def generate_friend(character_id, age, period, ollama_model):
    """友人キャラクターをAI生成"""

    prompt = f"""
【タスク】
{character_id}（{age}歳、{period}時代）の友人キャラクターを1人生成してください。

【出力形式】
JSON形式で以下の情報を生成：
{{
  "name": "名前（日本語 or 英語）",
  "name_en": "英語名（該当する場合）",
  "age": {age},
  "personality": "性格の説明",
  "relationship_type": "best_friend, good_friend, acquaintance のいずれか",
  "how_they_met": "出会った経緯",
  "shared_interests": ["共通の興味1", "共通の興味2"]
}}
"""

    response = call_ollama_api(ollama_model, prompt)
    friend_data = json.loads(response)

    # データベースに保存
    # ...

    return friend_data
```

### 5.3 統合プロンプト生成
```python
def generate_diary_prompt_with_full_context(character_id, absolute_day):
    """すべての文脈を統合した日記生成プロンプト"""

    # カレンダー情報取得
    calendar_info = get_calendar_info(absolute_day)

    # 外部人間関係取得
    encounters = get_encounters_for_day(character_id, absolute_day)

    # 姉妹共通イベント取得
    shared_events = get_shared_events(absolute_day)

    # 学校情報取得
    school_info = get_school_info(character_id, absolute_day)

    prompt = f"""
【キャラクター】{character_id}
【年齢】{age}歳{day_in_year}日目
【日付】{calendar_info['day_of_week_jp']}（{'祝日' if calendar_info['is_holiday'] else '平日' if calendar_info['is_school_day'] else '休日'}）
【場所】{location}
【学校】{'登校日' if calendar_info['is_school_day'] else '休み'}

【今日の主要イベント】
{shared_events['event_name'] if shared_events else 'なし'}

【今日会う人】
{', '.join([enc['name'] for enc in encounters])}

【学校行事】
{calendar_info['school_event'] if calendar_info['school_event'] else 'なし'}

【指示】
{character_id}（{age}歳）の視点で日記を書いてください。
"""

    return prompt
```

---

## 6. 成功基準の追加

### Phase D の成功基準（拡張版）

#### 6.1 カレンダーシステム
- [ ] 2006-2025年のすべての日付がcalendar_masterに登録されている
- [ ] 日本の祝日が正確に設定されている（2006-2025）
- [ ] LAの学校休日が正確に設定されている（2011-2015）
- [ ] 学期・学年の区切りが正確に設定されている
- [ ] 主要な学校行事が登録されている

#### 6.2 外部人間関係システム
- [ ] 各キャラクターに50-100人の外部人物が生成されている
- [ ] 年齢・時期に応じた適切な人物が生成されている
- [ ] 関係性の強さ・親密度が初期化されている
- [ ] 200-500のエンカウントイベントが計画されている

#### 6.3 日記生成の質
- [ ] 平日・休日・祝日の概念が日記に反映されている
- [ ] 学校行事が日記に反映されている
- [ ] 外部人物との交流が日記に反映されている
- [ ] 曜日感覚（「明日は月曜日だ」等）が自然に表現されている
- [ ] 友人の名前が日記に登場する
- [ ] 友人との具体的なエピソードが記録されている

#### 6.4 サンプル検証
- [ ] 牡丹6歳でディズニーランドでEmily Rodriguezと出会う日記が生成されている
- [ ] その後、Emilyとの交流が複数回記録されている
- [ ] 帰国時、Emilyとの別れが感動的に記録されている
- [ ] 帰国後もメール等でEmilyとの交流が続いている記録がある

---

## 7. 承認チェックリスト（追加）

### 開発者確認事項

#### 7.1 カレンダーシステムの妥当性
- [ ] 日本の祝日リストは正確か
- [ ] LAの学校休日リストは正確か
- [ ] 学期制度の理解は正確か
- [ ] 時間割の設定は現実的か

#### 7.2 学校システムの妥当性
- [ ] 学年と年齢の対応は正確か
- [ ] 日本とLAの学校システムの違いは正確に反映されているか
- [ ] 三姉妹の学校歴は矛盾なく設計されているか

#### 7.3 外部人間関係の妥当性
- [ ] 友人数の目安は現実的か
- [ ] 関係の継続性の定義は妥当か
- [ ] 主要外部キャラクター例は魅力的か
- [ ] エンカウントイベントの頻度は適切か

#### 7.4 統合実装の実現可能性
- [ ] カレンダー生成は実装可能か
- [ ] 外部キャラクター生成は実装可能か
- [ ] プロンプト生成の複雑さは許容範囲か
- [ ] 生成時間の見積もりは現実的か

---

## 8. 次のアクション

### 開発者承認後

1. **Phase D 完全設計書の更新**
   - 本追加設計書の内容を統合
   - データベーススキーマの追加
   - 生成フローの更新

2. **実装開始**
   - Phase D-1: カレンダー生成
   - Phase D-2: 外部キャラクター生成
   - Phase D-3: 日記生成（拡張版）

3. **テストとバリデーション**
   - サンプル生成（100日分）
   - 外部人間関係の妥当性検証
   - カレンダー情報の正確性検証

---

**この追加設計書により、三姉妹の過去は「設定」ではなく「生きた記憶」となります。**

平日と休日、祝日とイベント、友人との出会いと別れ、学校での日常と特別な日。
これらすべてが18,615日分の日記に記録され、三姉妹の人格を形成します。

**開発者の承認をお待ちしています。**
