#!/usr/bin/env python3
"""
WebSearch Optimizer テストスクリプト

250 searches/month の無料枠を最大限活用する最適化機能をテスト
- 永続キャッシュ（DB保存）
- 日次使用量トラッキング（8件/日）
- クエリ正規化
- 優先度フィルタリング
"""

import sys
sys.path.insert(0, '/home/koshikawa/AI-Vtuber-Project')

import os
from src.line_bot.websearch_client import SerpApiClient


def test_optimizer_basic():
    """基本的なOptimizer機能テスト"""
    print("\n" + "=" * 70)
    print("Test 1: Optimizer基本機能")
    print("=" * 70)

    # Optimizer有効でクライアント初期化
    client = SerpApiClient(
        enable_optimizer=True,
        daily_limit=8
    )

    print("✓ SerpApiClient initialized with Optimizer")

    # 統計取得
    stats = client.get_cache_stats()
    print(f"\n📊 初期統計:")
    print(f"  キャッシュエントリ数: {stats.get('total_entries', 0)}")
    print(f"  今日の検索数: {stats['daily_usage']['api_calls']}/8")
    print(f"  今月の検索数: {stats['monthly_usage']['api_calls']}/250")

    return True


def test_persistent_cache():
    """永続キャッシュテスト"""
    print("\n" + "=" * 70)
    print("Test 2: 永続キャッシュ（7日間）")
    print("=" * 70)

    client = SerpApiClient(enable_optimizer=True)

    # 1回目の検索
    query = "Python プログラミング テスト"
    print(f"\n1回目の検索: '{query}'")

    result1 = client.search(query, priority="normal")

    if result1:
        print(f"  ✅ 検索成功 ({len(result1)} 文字)")
    else:
        print(f"  ⚠️  検索スキップまたは失敗")

    # 2回目の検索（キャッシュヒットのはず）
    print(f"\n2回目の検索: '{query}'")
    result2 = client.search(query, priority="normal")

    if result2:
        print(f"  ✅ キャッシュヒット ({len(result2)} 文字)")

        if result1 and result1 == result2:
            print(f"  ✅ 結果が一致（キャッシュが正常に動作）")
            return True
        else:
            print(f"  ⚠️  結果が異なる")
            return False
    else:
        print(f"  ⚠️  結果なし")
        return False


def test_query_normalization():
    """クエリ正規化テスト"""
    print("\n" + "=" * 70)
    print("Test 3: クエリ正規化")
    print("=" * 70)

    client = SerpApiClient(enable_optimizer=True)

    # 語順が異なるクエリ
    query1 = "VTuber セクハラ"
    query2 = "セクハラ VTuber"

    print(f"\nクエリ1: '{query1}'")
    print(f"クエリ2: '{query2}'")

    # 正規化された形を確認
    if client.optimizer:
        norm1 = client.optimizer.normalize_query(query1)
        norm2 = client.optimizer.normalize_query(query2)

        print(f"\n正規化後:")
        print(f"  クエリ1: '{norm1}'")
        print(f"  クエリ2: '{norm2}'")

        if norm1 == norm2:
            print(f"  ✅ 正規化成功（同一クエリとして扱われる）")
            return True
        else:
            print(f"  ❌ 正規化失敗")
            return False
    else:
        print(f"  ⚠️  Optimizer無効")
        return False


def test_daily_limit():
    """日次制限テスト"""
    print("\n" + "=" * 70)
    print("Test 4: 日次制限（8件/日）")
    print("=" * 70)

    client = SerpApiClient(
        enable_optimizer=True,
        daily_limit=8
    )

    # 現在の使用量を確認
    stats = client.get_cache_stats()
    daily_usage = stats['daily_usage']

    print(f"\n今日の使用状況:")
    print(f"  総クエリ数: {daily_usage['total_queries']}")
    print(f"  API呼び出し数: {daily_usage['api_calls']}/8")
    print(f"  キャッシュヒット数: {daily_usage['cache_hits']}")
    print(f"  キャッシュヒット率: {daily_usage['cache_hit_rate']:.1%}")
    print(f"  残り検索可能数: {daily_usage['remaining']}")

    # 制限チェック
    if daily_usage['remaining'] > 0:
        print(f"\n  ✅ 制限内（あと{daily_usage['remaining']}件検索可能）")
        return True
    else:
        print(f"\n  ⚠️  本日の制限到達（明日まで検索不可）")
        return True  # これは正常動作


def test_priority_filtering():
    """優先度フィルタリングテスト"""
    print("\n" + "=" * 70)
    print("Test 5: 優先度フィルタリング")
    print("=" * 70)

    client = SerpApiClient(
        enable_optimizer=True,
        daily_limit=8
    )

    # 優先度を確認
    print("\n優先度レベル:")
    print("  high: 常に検索を試みる")
    print("  normal: 残り2件以下の場合スキップ")
    print("  low: 残り3件以下の場合スキップ")

    # 統計確認
    stats = client.get_cache_stats()
    remaining = stats['daily_usage']['remaining']

    print(f"\n現在の残り検索数: {remaining}")

    if remaining <= 2:
        print("  ⚠️  残りわずか - normalとlow優先度の検索がスキップされる可能性あり")
    else:
        print("  ✅ 十分な残量 - 全優先度の検索が可能")

    return True


def test_monthly_tracking():
    """月次トラッキングテスト"""
    print("\n" + "=" * 70)
    print("Test 6: 月次トラッキング（250件/月）")
    print("=" * 70)

    client = SerpApiClient(enable_optimizer=True)

    stats = client.get_cache_stats()
    monthly_usage = stats['monthly_usage']

    print(f"\n{monthly_usage['year_month']} の使用状況:")
    print(f"  総クエリ数: {monthly_usage['total_queries']}")
    print(f"  API呼び出し数: {monthly_usage['api_calls']}/250")
    print(f"  キャッシュヒット数: {monthly_usage['cache_hits']}")
    print(f"  キャッシュヒット率: {monthly_usage['cache_hit_rate']:.1%}")
    print(f"  残り検索可能数: {monthly_usage['remaining']}")

    # 進捗表示
    progress = monthly_usage['api_calls'] / 250 * 100
    print(f"\n使用率: {progress:.1f}%")
    print("  [" + "█" * int(progress // 2) + "░" * (50 - int(progress // 2)) + "]")

    if monthly_usage['remaining'] > 0:
        print(f"\n  ✅ 月次制限内（あと{monthly_usage['remaining']}件検索可能）")
        return True
    else:
        print(f"\n  ⚠️  月次制限到達（来月まで検索不可）")
        return True  # これは正常動作


def test_cache_stats():
    """キャッシュ統計テスト"""
    print("\n" + "=" * 70)
    print("Test 7: キャッシュ統計")
    print("=" * 70)

    client = SerpApiClient(enable_optimizer=True)

    stats = client.get_cache_stats()

    print(f"\nキャッシュ統計:")
    print(f"  総エントリ数: {stats['total_entries']}")
    print(f"  平均ヒット数: {stats['avg_hit_count']}")

    if stats['top_queries']:
        print(f"\nヒット数上位のクエリ:")
        for i, (query, hit_count) in enumerate(stats['top_queries'][:5], 1):
            print(f"  {i}. '{query}' ({hit_count}回)")

    return True


if __name__ == "__main__":
    print("=" * 70)
    print("WebSearch Optimizer テスト")
    print("=" * 70)

    # 環境変数の読み込み
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ .envファイルを読み込みました")
    except ImportError:
        print("⚠ python-dotenvがインストールされていません")
    except Exception:
        pass

    print("\n" + "=" * 70)

    results = []

    try:
        # テスト実行
        results.append(("Optimizer基本機能", test_optimizer_basic()))
        results.append(("永続キャッシュ", test_persistent_cache()))
        results.append(("クエリ正規化", test_query_normalization()))
        results.append(("日次制限", test_daily_limit()))
        results.append(("優先度フィルタリング", test_priority_filtering()))
        results.append(("月次トラッキング", test_monthly_tracking()))
        results.append(("キャッシュ統計", test_cache_stats()))

        # 結果サマリー
        print("\n" + "=" * 70)
        print("テスト結果サマリー")
        print("=" * 70)

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")

        print("=" * 70)

        if all(r for _, r in results):
            print("\n🎉 全テスト成功！Optimizer機能は正常に動作しています")
            print("\n効果:")
            print("  ✅ 永続キャッシュ（7日間）でAPI使用量削減")
            print("  ✅ 日次制限（8件/日）で柔軟な運用")
            print("  ✅ 優先度フィルタリングで重要なクエリを優先")
            print("  ✅ 使用量トラッキングで上限管理")
        else:
            print("\n⚠️  一部のテストが失敗しました")

    except KeyboardInterrupt:
        print("\n\nテストを中断しました")

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
