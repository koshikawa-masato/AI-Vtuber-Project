-- VTuber SNS Accounts
CREATE TABLE IF NOT EXISTS vtuber_sns_accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vtuber_id INTEGER NOT NULL,
    platform TEXT NOT NULL,  -- 'twitter', 'twitter_sub' 等
    account_handle TEXT NOT NULL,  -- @username
    account_url TEXT,
    account_type TEXT,  -- 'main', 'sub', 'private'
    is_verified BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    notes TEXT,
    FOREIGN KEY (vtuber_id) REFERENCES vtubers(vtuber_id),
    UNIQUE(platform, account_handle)
);

-- VTuber SNS Posts (重要な投稿のみ手動記録)
CREATE TABLE IF NOT EXISTS vtuber_sns_posts (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    post_url TEXT,
    post_content TEXT,
    post_type TEXT,  -- 'announcement', 'schedule', 'milestone', 'casual'
    posted_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_level INTEGER DEFAULT 3,  -- 1-5 (5=最重要)
    tags TEXT,  -- カンマ区切り
    notes TEXT,
    FOREIGN KEY (account_id) REFERENCES vtuber_sns_accounts(account_id)
);

-- VTuber Activities (活動予定・告知)
CREATE TABLE IF NOT EXISTS vtuber_activities (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vtuber_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL,  -- 'live', 'event', 'release', 'milestone'
    title TEXT NOT NULL,
    description TEXT,
    scheduled_date DATE,
    scheduled_time TIME,
    source_url TEXT,
    source_type TEXT,  -- 'twitter', 'youtube', 'official'
    importance_level INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vtuber_id) REFERENCES vtubers(vtuber_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sns_accounts_vtuber ON vtuber_sns_accounts(vtuber_id);
CREATE INDEX IF NOT EXISTS idx_sns_posts_account ON vtuber_sns_posts(account_id);
CREATE INDEX IF NOT EXISTS idx_sns_posts_importance ON vtuber_sns_posts(importance_level DESC);
CREATE INDEX IF NOT EXISTS idx_activities_vtuber ON vtuber_activities(vtuber_id);
CREATE INDEX IF NOT EXISTS idx_activities_date ON vtuber_activities(scheduled_date);
