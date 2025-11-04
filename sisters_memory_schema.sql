CREATE TABLE sister_shared_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,                    -- イベント名
    event_date TEXT NOT NULL,                    -- 実カレンダー日付（YYYY-MM-DD）
    location TEXT NOT NULL,                      -- 場所（japan, los_angeles, other）

    -- 三姉妹の年齢・絶対日数
    kasho_age_years INTEGER,                     -- Kasho年齢（年）
    kasho_age_days INTEGER,                      -- Kasho年齢（日）
    kasho_absolute_day INTEGER,                  -- Kasho絶対日数

    botan_age_years INTEGER,                     -- 牡丹年齢（年）
    botan_age_days INTEGER,                      -- 牡丹年齢（日）
    botan_absolute_day INTEGER,                  -- 牡丹絶対日数

    yuri_age_years INTEGER,                      -- ユリ年齢（年）
    yuri_age_days INTEGER,                       -- ユリ年齢（日）
    yuri_absolute_day INTEGER,                   -- ユリ絶対日数

    -- イベント詳細
    description TEXT NOT NULL,                   -- イベント詳細説明
    participants TEXT,                           -- 参加者（JSON配列）
    cultural_context TEXT,                       -- 文化的背景
    emotional_impact INTEGER CHECK(emotional_impact BETWEEN 1 AND 10),  -- 感情的インパクト（1-10）

    -- メタデータ
    category TEXT NOT NULL,                      -- カテゴリ（life_turning_point, sisterhood, encounter, difficulty, moving, growth, cultural）
    event_number INTEGER,                        -- イベント番号（001-100）

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_event_date ON sister_shared_events(event_date);
CREATE INDEX idx_category ON sister_shared_events(category);
CREATE INDEX idx_event_number ON sister_shared_events(event_number);
CREATE INDEX idx_kasho_absolute_day ON sister_shared_events(kasho_absolute_day);
CREATE INDEX idx_botan_absolute_day ON sister_shared_events(botan_absolute_day);
CREATE INDEX idx_yuri_absolute_day ON sister_shared_events(yuri_absolute_day);
CREATE TABLE botan_memories (
    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,                            -- 関連するsister_shared_events.event_id（NULL可）
    absolute_day INTEGER NOT NULL,               -- 牡丹の絶対日数
    memory_date TEXT NOT NULL,                   -- 記憶の日付（YYYY-MM-DD）

    -- 牡丹の主観的記憶
    botan_emotion TEXT,                          -- 牡丹の感情（喜び、悲しみ、怒り等）
    botan_action TEXT,                           -- 牡丹の行動
    botan_thought TEXT,                          -- 牡丹の思考
    diary_entry TEXT,                            -- 牡丹の日記エントリー

    -- 姉妹の観察（牡丹が観察した範囲のみ）
    kasho_observed_behavior TEXT,                -- Kashoの観察された行動
    yuri_observed_behavior TEXT,                 -- ユリの観察された行動

    -- 姉妹への推測（断定ではない）
    kasho_inferred_feeling TEXT,                 -- Kashoの感情の推測（「多分〜だと思う」レベル）
    yuri_inferred_feeling TEXT,                  -- ユリの感情の推測（「多分〜だと思う」レベル）

    -- メタデータ
    memory_importance INTEGER CHECK(memory_importance BETWEEN 1 AND 10),  -- 記憶の重要度

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES sister_shared_events(event_id)
);
CREATE INDEX idx_botan_memory_date ON botan_memories(memory_date);
CREATE INDEX idx_botan_event_id ON botan_memories(event_id);
CREATE TABLE kasho_memories (
    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    absolute_day INTEGER NOT NULL,
    memory_date TEXT NOT NULL,

    -- Kashoの主観的記憶
    kasho_emotion TEXT,
    kasho_action TEXT,
    kasho_thought TEXT,
    diary_entry TEXT,

    -- 姉妹の観察（Kashoが観察した範囲のみ）
    botan_observed_behavior TEXT,
    yuri_observed_behavior TEXT,

    -- 姉妹への推測
    botan_inferred_feeling TEXT,
    yuri_inferred_feeling TEXT,

    memory_importance INTEGER CHECK(memory_importance BETWEEN 1 AND 10),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES sister_shared_events(event_id)
);
CREATE INDEX idx_kasho_memory_date ON kasho_memories(memory_date);
CREATE INDEX idx_kasho_event_id ON kasho_memories(event_id);
CREATE TABLE yuri_memories (
    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    absolute_day INTEGER NOT NULL,
    memory_date TEXT NOT NULL,

    -- ユリの主観的記憶
    yuri_emotion TEXT,
    yuri_action TEXT,
    yuri_thought TEXT,
    diary_entry TEXT,

    -- 姉妹の観察（ユリが観察した範囲のみ）
    kasho_observed_behavior TEXT,
    botan_observed_behavior TEXT,

    -- 姉妹への推測
    kasho_inferred_feeling TEXT,
    botan_inferred_feeling TEXT,

    memory_importance INTEGER CHECK(memory_importance BETWEEN 1 AND 10),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES sister_shared_events(event_id)
);
CREATE INDEX idx_yuri_memory_date ON yuri_memories(memory_date);
CREATE INDEX idx_yuri_event_id ON yuri_memories(event_id);
CREATE TABLE encounter_events (
    encounter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,                            -- 関連するsister_shared_events.event_id（NULL可）
    event_name TEXT NOT NULL,
    event_date TEXT NOT NULL,
    location TEXT NOT NULL,

    -- 出会った人物情報
    person_name TEXT NOT NULL,                   -- 人物名
    person_name_en TEXT,                         -- 英語名（LA時代の人物）
    person_age INTEGER,                          -- 人物の年齢
    person_relationship TEXT,                    -- 関係性（friend, teacher, rival, family等）

    -- 三姉妹との関係
    met_kasho BOOLEAN DEFAULT 0,                 -- Kashoと出会ったか
    met_botan BOOLEAN DEFAULT 0,                 -- 牡丹と出会ったか
    met_yuri BOOLEAN DEFAULT 0,                  -- ユリと出会ったか

    -- 呼称（三姉妹呼称統一仕様書に基づく）
    kasho_calls_them TEXT,                       -- Kashoがこの人物を呼ぶ名前
    botan_calls_them TEXT,                       -- 牡丹がこの人物を呼ぶ名前
    yuri_calls_them TEXT,                        -- ユリがこの人物を呼ぶ名前

    -- イベント詳細
    encounter_type TEXT,                         -- 出会いの種類（first_meeting, playdate, birthday_party等）
    description TEXT,
    emotional_impact INTEGER CHECK(emotional_impact BETWEEN 1 AND 10),
    creates_long_term_memory BOOLEAN DEFAULT 0,  -- 長期記憶を作るか

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES sister_shared_events(event_id)
);
CREATE INDEX idx_encounter_person_name ON encounter_events(person_name);
CREATE INDEX idx_encounter_event_date ON encounter_events(event_date);
CREATE INDEX idx_encounter_event_id ON encounter_events(event_id);
CREATE TABLE personality_formation_impacts (
    impact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,

    -- 各姉妹への影響
    kasho_impact TEXT,                           -- Kashoの人格形成への影響
    botan_impact TEXT,                           -- 牡丹の人格形成への影響
    yuri_impact TEXT,                            -- ユリの人格形成への影響
    sisterhood_impact TEXT,                      -- 姉妹関係への影響

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES sister_shared_events(event_id)
);
CREATE INDEX idx_personality_event_id ON personality_formation_impacts(event_id);
CREATE TABLE cultural_events_master (
    cultural_id INTEGER PRIMARY KEY AUTOINCREMENT,
    real_year INTEGER NOT NULL,                  -- 実年（2006-2025）
    event_type TEXT NOT NULL,                    -- イベント種類（anime, game, movie, tv, music, trend, tech, news）
    event_name TEXT NOT NULL,                    -- イベント名（日本語）
    event_name_en TEXT,                          -- イベント名（英語）

    target_age_range TEXT,                       -- 対象年齢範囲（'5-10', '10-15', 'all'）
    impact_level INTEGER CHECK(impact_level BETWEEN 1 AND 10),  -- 影響度
    location TEXT,                               -- 場所（japan, los_angeles, global）

    description TEXT,                            -- 説明

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_cultural_year ON cultural_events_master(real_year);
CREATE INDEX idx_cultural_type ON cultural_events_master(event_type);
CREATE INDEX idx_cultural_location ON cultural_events_master(location);
CREATE TABLE phase_d_metadata (
    metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    metadata_key TEXT UNIQUE NOT NULL,
    metadata_value TEXT,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
