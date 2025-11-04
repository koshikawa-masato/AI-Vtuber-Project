-- Sensitive Filter Database Schema
-- Created: 2025-10-27
-- Purpose: NGワードマスタ、コメントログ、インシデント管理

-- Table 1: ng_words (NGワードマスタ)
CREATE TABLE IF NOT EXISTS ng_words (
    word_id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,              -- NGワード（正規化済み）
    category TEXT NOT NULL,                 -- カテゴリ（Tier 1/2/3）
    subcategory TEXT,                       -- サブカテゴリ（sexual/hate/ai/politics等）
    severity INTEGER NOT NULL,              -- 深刻度（1-10）
    language TEXT NOT NULL DEFAULT 'ja',    -- 言語（ja/en/zh/ko等）
    pattern_type TEXT NOT NULL,             -- パターンタイプ（exact/partial/regex）
    regex_pattern TEXT,                     -- 正規表現パターン（pattern_type=regexの場合）
    alternative_text TEXT,                  -- 代替テキスト（伏字用）
    action TEXT NOT NULL,                   -- アクション（block/mask/warn/log）
    added_by TEXT NOT NULL,                 -- 追加者（developer/auto/manual）
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,                             -- メモ
    active BOOLEAN DEFAULT 1                -- 有効/無効
);

-- Indexes for ng_words
CREATE INDEX IF NOT EXISTS idx_ng_words_category ON ng_words(category);
CREATE INDEX IF NOT EXISTS idx_ng_words_severity ON ng_words(severity);
CREATE INDEX IF NOT EXISTS idx_ng_words_language ON ng_words(language);
CREATE INDEX IF NOT EXISTS idx_ng_words_active ON ng_words(active);

-- Table 2: comment_log (コメントログ)
CREATE TABLE IF NOT EXISTS comment_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    viewer_id TEXT,                         -- 視聴者ID（匿名化可能）
    viewer_name TEXT,                       -- 視聴者名
    original_comment TEXT NOT NULL,         -- 元のコメント
    processed_comment TEXT,                 -- 処理後のコメント（伏字等）
    sensitivity_score REAL,                 -- センシティブ度スコア（0.0-1.0）
    detected_words TEXT,                    -- 検出されたNGワード（JSON配列）
    action_taken TEXT,                      -- 実行されたアクション
    layer1_result TEXT,                     -- レイヤー1結果
    layer2_result TEXT,                     -- レイヤー2結果
    layer3_result TEXT,                     -- レイヤー3結果
    context_analysis TEXT,                  -- コンテキスト分析結果（JSON）
    shown_to_sisters BOOLEAN DEFAULT 0,    -- 三姉妹に表示されたか
    platform TEXT,                          -- プラットフォーム（youtube/x/test）
    stream_id TEXT,                         -- 配信ID
    notes TEXT
);

-- Indexes for comment_log
CREATE INDEX IF NOT EXISTS idx_comment_log_timestamp ON comment_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_comment_log_sensitivity ON comment_log(sensitivity_score);
CREATE INDEX IF NOT EXISTS idx_comment_log_action ON comment_log(action_taken);

-- Table 3: incident_log (インシデントログ)
CREATE TABLE IF NOT EXISTS incident_log (
    incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    incident_type TEXT NOT NULL,            -- インシデントタイプ（sexual_harassment/hate_speech/spam等）
    severity INTEGER NOT NULL,              -- 深刻度（1-10）
    viewer_id TEXT,                         -- 視聴者ID
    viewer_name TEXT,                       -- 視聴者名
    comment_log_id INTEGER,                 -- comment_logへの参照
    description TEXT,                       -- インシデント詳細
    action_taken TEXT,                      -- 実行されたアクション
    developer_notified BOOLEAN DEFAULT 0,   -- 開発者への通知
    resolved BOOLEAN DEFAULT 0,             -- 解決済みか
    resolved_at TIMESTAMP,                  -- 解決日時
    resolution_notes TEXT,                  -- 解決メモ
    FOREIGN KEY (comment_log_id) REFERENCES comment_log(log_id)
);

-- Indexes for incident_log
CREATE INDEX IF NOT EXISTS idx_incident_log_severity ON incident_log(severity);
CREATE INDEX IF NOT EXISTS idx_incident_log_resolved ON incident_log(resolved);

-- Table 4: ng_word_candidates (NGワード候補)
CREATE TABLE IF NOT EXISTS ng_word_candidates (
    candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detection_method TEXT,                  -- 検出方法（auto/manual）
    context TEXT,                           -- 検出時の文脈
    frequency INTEGER DEFAULT 1,            -- 出現頻度
    suggested_category TEXT,                -- 提案カテゴリ
    suggested_severity INTEGER,             -- 提案深刻度
    status TEXT DEFAULT 'pending',          -- ステータス（pending/approved/rejected）
    reviewed_by TEXT,                       -- レビュー者
    reviewed_at TIMESTAMP,                  -- レビュー日時
    review_notes TEXT                       -- レビューメモ
);

-- Indexes for ng_word_candidates
CREATE INDEX IF NOT EXISTS idx_ng_word_candidates_status ON ng_word_candidates(status);
CREATE INDEX IF NOT EXISTS idx_ng_word_candidates_frequency ON ng_word_candidates(frequency);

-- Table 5: viewer_moderation (視聴者管理)
CREATE TABLE IF NOT EXISTS viewer_moderation (
    moderation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    viewer_id TEXT NOT NULL UNIQUE,
    viewer_name TEXT,
    warning_count INTEGER DEFAULT 0,        -- 警告回数
    timeout_count INTEGER DEFAULT 0,        -- タイムアウト回数
    ban_status TEXT DEFAULT 'none',         -- BANステータス（none/temp/permanent）
    ban_until TIMESTAMP,                    -- 一時BAN解除日時
    first_violation TIMESTAMP,              -- 初回違反日時
    last_violation TIMESTAMP,               -- 最終違反日時
    violation_history TEXT,                 -- 違反履歴（JSON配列）
    notes TEXT
);

-- Indexes for viewer_moderation
CREATE INDEX IF NOT EXISTS idx_viewer_moderation_ban_status ON viewer_moderation(ban_status);

-- Table 6: filter_statistics (フィルタ統計)
CREATE TABLE IF NOT EXISTS filter_statistics (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    total_comments INTEGER DEFAULT 0,
    blocked_comments INTEGER DEFAULT 0,
    masked_comments INTEGER DEFAULT 0,
    warned_comments INTEGER DEFAULT 0,
    avg_sensitivity_score REAL,
    tier1_detections INTEGER DEFAULT 0,
    tier2_detections INTEGER DEFAULT 0,
    tier3_detections INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,      -- 誤検出数（手動レビュー）
    processing_time_avg REAL,               -- 平均処理時間（ms）
    UNIQUE(date)
);

-- Indexes for filter_statistics
CREATE INDEX IF NOT EXISTS idx_filter_statistics_date ON filter_statistics(date);
