"""
Seed SNS Account Data
=====================

Register VTuber SNS accounts (Twitter/X, etc.)
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from botan_subculture.config import DB_PATH


def seed_twitter_accounts():
    """Add VTuber Twitter/X accounts"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Main Twitter accounts (公開情報のみ)
    accounts = [
        # Gen 0
        ('ときのそら', 'twitter', 'tokino_sora', 'https://x.com/tokino_sora', 'main', 1),
        ('ロボ子さん', 'twitter', 'robocosan', 'https://x.com/robocosan', 'main', 1),
        ('さくらみこ', 'twitter', 'sakuramiko35', 'https://x.com/sakuramiko35', 'main', 1),
        ('星街すいせい', 'twitter', 'suisei_hosimati', 'https://x.com/suisei_hosimati', 'main', 1),

        # Gen 1
        ('白上フブキ', 'twitter', 'shirakamifubuki', 'https://x.com/shirakamifubuki', 'main', 1),
        ('夏色まつり', 'twitter', 'natsuiromatsuri', 'https://x.com/natsuiromatsuri', 'main', 1),

        # Gamers
        ('大神ミオ', 'twitter', 'ookamimio', 'https://x.com/ookamimio', 'main', 1),
        ('猫又おかゆ', 'twitter', 'nekomataokayu', 'https://x.com/nekomataokayu', 'main', 1),
        ('戌神ころね', 'twitter', 'inugamikorone', 'https://x.com/inugamikorone', 'main', 1),

        # Gen 2
        ('大空スバル', 'twitter', 'oozorasubaru', 'https://x.com/oozorasubaru', 'main', 1),

        # Gen 3
        ('兎田ぺこら', 'twitter', 'usadapekora', 'https://x.com/usadapekora', 'main', 1),
        ('潤羽るしあ', 'twitter', 'uruharushia', 'https://x.com/uruharushia', 'main', 1),
        ('不知火フレア', 'twitter', 'shiranuiflare', 'https://x.com/shiranuiflare', 'main', 1),
        ('白銀ノエル', 'twitter', 'shiroganenoel', 'https://x.com/shiroganenoel', 'main', 1),
        ('宝鐘マリン', 'twitter', 'houshoumarine', 'https://x.com/houshoumarine', 'main', 1),

        # Gen 4
        ('天音かなた', 'twitter', 'amanekanatach', 'https://x.com/amanekanatach', 'main', 1),
        ('角巻わため', 'twitter', 'tsunomakiwatame', 'https://x.com/tsunomakiwatame', 'main', 1),
        ('常闇トワ', 'twitter', 'tokoyamitowa', 'https://x.com/tokoyamitowa', 'main', 1),

        # Gen 5
        ('雪花ラミィ', 'twitter', 'yukihanalamy', 'https://x.com/yukihanalamy', 'main', 1),
        ('桃鈴ねね', 'twitter', 'momosuzunene', 'https://x.com/momosuzunene', 'main', 1),
        ('獅白ぼたん', 'twitter', 'shishirobotan', 'https://x.com/shishirobotan', 'main', 1),
        ('尾丸ポルカ', 'twitter', 'omarupolka', 'https://x.com/omarupolka', 'main', 1),
    ]

    for vtuber_name, platform, handle, url, acc_type, verified in accounts:
        cursor.execute("""
        INSERT OR IGNORE INTO vtuber_sns_accounts (vtuber_id, platform, account_handle, account_url, account_type, is_verified)
        SELECT vtuber_id, ?, ?, ?, ?, ?
        FROM vtubers
        WHERE name = ?
        """, (platform, handle, url, acc_type, verified, vtuber_name))

    conn.commit()
    print(f"[SUCCESS] Added {len(accounts)} Twitter accounts")

    conn.close()


def main():
    """Main seeding function"""
    print("=" * 60)
    print("Seeding SNS Account Data")
    print("=" * 60)

    seed_twitter_accounts()

    print("\n" + "=" * 60)
    print("SNS Data Seeded Successfully")
    print("=" * 60)
    print("\nNote: 重要な投稿は vtuber_sns_posts テーブルに手動で追加してください")
    print("Example: python -m botan_subculture.database.add_sns_post")


if __name__ == '__main__':
    main()
