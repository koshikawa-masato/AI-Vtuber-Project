#!/usr/bin/env python3
"""
Add Additional NG Words to Database
Created: 2025-10-27
Purpose: 調査結果に基づくNGワード追加
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sensitive_filter.db"

def add_ng_words():
    """
    NGワードを追加
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 追加NGワードリスト
    additional_words = []

    # 1. 職業差別・差別的表現（Tier 1）
    discrimination_words = [
        ('底辺', 'tier1_hate', 'discrimination', 8, 'ja', 'exact', None, None, 'block', 'developer', '職業差別的表現'),
        ('社会のゴミ', 'tier1_hate', 'discrimination', 10, 'ja', 'partial', None, None, 'block', 'developer', '差別的表現'),
        ('クズ', 'tier1_hate', 'abuse', 7, 'ja', 'exact', None, None, 'block', 'developer', '誹謗中傷'),
        ('カス', 'tier1_hate', 'abuse', 7, 'ja', 'exact', None, None, 'block', 'developer', '誹謗中傷'),
        ('ゴミ', 'tier1_hate', 'abuse', 6, 'ja', 'exact', None, None, 'warn', 'developer', '誹謗中傷（文脈依存）'),
    ]

    # 2. 暴力的表現の追加（Tier 1）
    violence_words = [
        ('殺害', 'tier1_hate', 'violence', 10, 'ja', 'partial', None, None, 'block', 'developer', '暴力的表現'),
        ('爆破', 'tier1_hate', 'violence', 9, 'ja', 'partial', None, None, 'block', 'developer', '暴力的表現'),
        ('テロ', 'tier1_hate', 'violence', 9, 'ja', 'partial', None, None, 'block', 'developer', '暴力的表現'),
        ('自殺', 'tier1_hate', 'self_harm', 9, 'ja', 'partial', None, None, 'block', 'developer', '自傷行為'),
        ('リスカ', 'tier1_hate', 'self_harm', 9, 'ja', 'partial', None, None, 'block', 'developer', '自傷行為'),
    ]

    # 3. センシティブな政治・社会トピック（Tier 2）
    political_words = [
        ('天皇', 'tier2_politics', 'politics', 7, 'ja', 'exact', None, None, 'warn', 'developer', '政治的トピック'),
        ('首相', 'tier2_politics', 'politics', 6, 'ja', 'exact', None, None, 'warn', 'developer', '政治的トピック'),
        ('選挙', 'tier2_politics', 'politics', 6, 'ja', 'exact', None, None, 'warn', 'developer', '政治的トピック'),
        ('政党', 'tier2_politics', 'politics', 6, 'ja', 'exact', None, None, 'warn', 'developer', '政治的トピック'),
        ('自民党', 'tier2_politics', 'politics', 7, 'ja', 'exact', None, None, 'warn', 'developer', '政治的トピック'),
        ('共産党', 'tier2_politics', 'politics', 7, 'ja', 'exact', None, None, 'warn', 'developer', '政治的トピック'),
        ('民主党', 'tier2_politics', 'politics', 7, 'ja', 'exact', None, None, 'warn', 'developer', '政治的トピック'),
    ]

    # 4. 宗教的トピック（Tier 2）
    religion_words = [
        ('キリスト教', 'tier2_religion', 'religion', 6, 'ja', 'partial', None, None, 'warn', 'developer', '宗教的トピック'),
        ('仏教', 'tier2_religion', 'religion', 6, 'ja', 'partial', None, None, 'warn', 'developer', '宗教的トピック'),
        ('イスラム', 'tier2_religion', 'religion', 6, 'ja', 'partial', None, None, 'warn', 'developer', '宗教的トピック'),
        ('神道', 'tier2_religion', 'religion', 6, 'ja', 'partial', None, None, 'warn', 'developer', '宗教的トピック'),
        ('創価学会', 'tier2_religion', 'religion', 7, 'ja', 'partial', None, None, 'warn', 'developer', '宗教的トピック'),
        ('統一教会', 'tier2_religion', 'religion', 7, 'ja', 'partial', None, None, 'warn', 'developer', '宗教的トピック'),
    ]

    # 5. 個人情報詮索（Tier 2）
    personal_info_words = [
        ('住所', 'tier2_identity', 'personal_info', 8, 'ja', 'exact', None, None, 'warn', 'developer', '個人情報詮索'),
        ('電話番号', 'tier2_identity', 'personal_info', 9, 'ja', 'partial', None, None, 'block', 'developer', '個人情報詮索'),
        ('実家', 'tier2_identity', 'personal_info', 7, 'ja', 'exact', None, None, 'warn', 'developer', '個人情報詮索'),
        ('学校', 'tier2_identity', 'personal_info', 6, 'ja', 'exact', None, None, 'warn', 'developer', '個人情報詮索'),
        ('会社', 'tier2_identity', 'personal_info', 5, 'ja', 'exact', None, None, 'log', 'developer', '個人情報詮索（文脈依存）'),
    ]

    # 6. スパム・荒らし関連（Tier 2）
    spam_words = [
        ('業者', 'tier2_spam', 'spam', 5, 'ja', 'exact', None, None, 'log', 'developer', 'スパム疑い'),
        ('宣伝', 'tier2_spam', 'spam', 5, 'ja', 'exact', None, None, 'log', 'developer', 'スパム疑い'),
        ('副業', 'tier2_spam', 'spam', 6, 'ja', 'exact', None, None, 'warn', 'developer', 'スパム疑い'),
        ('稼げる', 'tier2_spam', 'spam', 6, 'ja', 'partial', None, None, 'warn', 'developer', 'スパム疑い'),
    ]

    # 7. 性的表現の追加（Tier 1）- サンプル
    sexual_words_additional = [
        ('エロ', 'tier1_sexual', 'explicit', 8, 'ja', 'exact', None, None, 'block', 'developer', '性的表現'),
        ('下ネタ', 'tier1_sexual', 'explicit', 7, 'ja', 'partial', None, None, 'warn', 'developer', '性的表現'),
        ('おっぱい', 'tier1_sexual', 'body_part', 7, 'ja', 'exact', None, None, 'warn', 'developer', '性的表現'),
    ]

    # 8. 他のVTuber・配信者への批判（Tier 2）
    vtuber_criticism_words = [
        ('炎上', 'tier2_vtuber', 'criticism', 6, 'ja', 'exact', None, None, 'warn', 'developer', '炎上話題'),
        ('引退', 'tier2_vtuber', 'sensitive_topic', 5, 'ja', 'exact', None, None, 'log', 'developer', 'センシティブトピック（文脈依存）'),
        ('卒業', 'tier2_vtuber', 'sensitive_topic', 4, 'ja', 'exact', None, None, 'log', 'developer', 'センシティブトピック（文脈依存）'),
    ]

    # 全てまとめる
    additional_words = (
        discrimination_words +
        violence_words +
        political_words +
        religion_words +
        personal_info_words +
        spam_words +
        sexual_words_additional +
        vtuber_criticism_words
    )

    # 投入
    added_count = 0
    skipped_count = 0

    for word_data in additional_words:
        try:
            cursor.execute("""
                INSERT INTO ng_words
                (word, category, subcategory, severity, language, pattern_type,
                 regex_pattern, alternative_text, action, added_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, word_data)
            added_count += 1
        except sqlite3.IntegrityError:
            # 重複する場合はスキップ
            skipped_count += 1

    conn.commit()

    print(f"✅ Added {added_count} new NG words")
    print(f"⚠️  Skipped {skipped_count} duplicate words")

    # 最新の統計を表示
    cursor.execute("SELECT COUNT(*) FROM ng_words WHERE active = 1")
    total = cursor.fetchone()[0]
    print(f"\n📊 Total active NG words: {total}")

    # カテゴリ別の数を表示
    cursor.execute("""
        SELECT category, COUNT(*)
        FROM ng_words
        WHERE active = 1
        GROUP BY category
        ORDER BY category
    """)

    print("\n📊 NG Words by Category:")
    for category, cnt in cursor.fetchall():
        print(f"   {category}: {cnt} words")

    conn.close()

if __name__ == "__main__":
    add_ng_words()
