-- Migration: リッチメニュー自動切り替えシステム
-- 作成日: 2025-11-17
-- 説明: sessions テーブルの拡張と feedback テーブルの作成

-- 1. sessions テーブルの拡張（既存の selected_character を活用）
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS selected_mode VARCHAR(10) DEFAULT 'auto' COMMENT '選択モード: auto, botan, kasho, yuri',
ADD COLUMN IF NOT EXISTS feedback_state ENUM('none', 'waiting') DEFAULT 'none' COMMENT 'フィードバック状態: none, waiting';

-- 2. feedback テーブルの作成
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'フィードバックID',
    user_id VARCHAR(255) NOT NULL COMMENT 'LINEユーザーID',
    feedback_text TEXT NOT NULL COMMENT 'フィードバック内容',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '受信日時',
    is_read BOOLEAN DEFAULT FALSE COMMENT '既読フラグ',
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_is_read (is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザーフィードバック';

-- 3. 既存ユーザーのデータ確認（ロールバック用）
-- SELECT user_id, selected_character, selected_mode, feedback_state FROM sessions LIMIT 10;

-- 4. feedback テーブルの確認
-- SELECT * FROM feedback ORDER BY created_at DESC LIMIT 10;
