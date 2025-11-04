-- VTuber Units (ユニット情報)
-- ド珍組、みっころね、UMISEA等の固定ユニット
CREATE TABLE IF NOT EXISTS vtuber_units (
    unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_name TEXT NOT NULL UNIQUE,
    unit_name_kana TEXT,
    description TEXT,
    official BOOLEAN DEFAULT 0,  -- 公式ユニットかどうか
    created_date DATE,
    notes TEXT
);

-- VTuber Unit Members (ユニットメンバー)
CREATE TABLE IF NOT EXISTS vtuber_unit_members (
    unit_member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL,
    vtuber_id INTEGER NOT NULL,
    role TEXT,  -- リーダー、メンバー等
    joined_date DATE,
    FOREIGN KEY (unit_id) REFERENCES vtuber_units(unit_id),
    FOREIGN KEY (vtuber_id) REFERENCES vtubers(vtuber_id),
    UNIQUE(unit_id, vtuber_id)
);

-- VTuber Nicknames (愛称・呼び方)
CREATE TABLE IF NOT EXISTS vtuber_nicknames (
    nickname_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vtuber_id INTEGER NOT NULL,
    nickname TEXT NOT NULL,
    nickname_type TEXT,  -- ファン呼び、メンバー呼び、公式等
    is_primary BOOLEAN DEFAULT 0,
    FOREIGN KEY (vtuber_id) REFERENCES vtubers(vtuber_id),
    UNIQUE(vtuber_id, nickname)
);

-- VTuber Trivia (豆知識・特徴)
CREATE TABLE IF NOT EXISTS vtuber_trivia (
    trivia_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vtuber_id INTEGER NOT NULL,
    category TEXT,  -- キャッチフレーズ、口癖、特技等
    content TEXT NOT NULL,
    source TEXT,  -- 出典
    verified BOOLEAN DEFAULT 0,
    FOREIGN KEY (vtuber_id) REFERENCES vtubers(vtuber_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_unit_members_vtuber ON vtuber_unit_members(vtuber_id);
CREATE INDEX IF NOT EXISTS idx_nicknames_vtuber ON vtuber_nicknames(vtuber_id);
CREATE INDEX IF NOT EXISTS idx_trivia_vtuber ON vtuber_trivia(vtuber_id);
CREATE INDEX IF NOT EXISTS idx_trivia_category ON vtuber_trivia(category);
