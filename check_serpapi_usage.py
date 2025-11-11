#!/usr/bin/env python3
"""
SerpApi使用量確認スクリプト
"""
import sys
sys.path.insert(0, '/home/koshikawa/AI-Vtuber-Project')

import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
env_path = Path('/home/koshikawa/AI-Vtuber-Project/.env')
load_dotenv(env_path)

from src.line_bot.websearch_client import SerpApiClient
from src.line_bot.websearch_optimizer import WebSearchOptimizer
from datetime import datetime

def main():
    print("=" * 70)
    print("SerpApi 使用量レポート")
    print("=" * 70)

    client = SerpApiClient()

    # SerpApi公式の使用量（正確な値）
    account_info = client.get_account_info()

    if account_info:
        print("\n📊 SerpApi使用状況")
        print("=" * 70)
        print(f"  プラン: {account_info.get('plan_name', 'N/A')}")
        print(f"  月間検索上限: {account_info.get('searches_per_month', 'N/A')}")
        print(f"  今月の使用量: {account_info.get('this_month_usage', 0)}")
        print(f"  残り検索数: {account_info.get('plan_searches_left', 'N/A')}")

        if 'extra_credits' in account_info and account_info['extra_credits'] > 0:
            print(f"  追加クレジット: {account_info['extra_credits']}")

        # 使用率バー
        this_month_usage = account_info.get('this_month_usage', 0)
        searches_per_month = account_info.get('searches_per_month', 250)
        usage_rate = this_month_usage / searches_per_month if searches_per_month > 0 else 0
        bar_length = 50
        filled = int(bar_length * usage_rate)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\n  使用率: {usage_rate:.1%}")
        print(f"  [{bar}]")

        # 1日あたりの平均使用量（参考）
        from datetime import datetime
        today = datetime.now().day
        avg_per_day = this_month_usage / today if today > 0 else 0
        print(f"\n  平均使用量: {avg_per_day:.1f}件/日")
        print(f"  このペースで: {avg_per_day * 30:.0f}件/月（予測）")

        # 警告
        plan_searches_left = account_info.get('plan_searches_left', 0)
        if plan_searches_left < 50:
            print("\n⚠️  警告: 残り検索数が50回以下です")
        if plan_searches_left <= 0:
            print("\n❌ 警告: 月間上限に達しました")

        # 日次制限の残り（プロジェクト独自制限）
        optimizer = WebSearchOptimizer()
        daily = optimizer.get_daily_usage()
        print(f"\n📅 本日の制限（8件/日）")
        print(f"  本日の使用: {daily['api_calls']}/8")
        print(f"  残り: {daily['remaining']}件")

    else:
        print("\n❌ SerpApi公式アカウント情報の取得に失敗しました")
        print("   APIキーを確認してください")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
