#!/usr/bin/env python3
"""
SerpApi テストスクリプト

SerpApiを使ってGoogle検索結果を取得し、センシティブワード判定に使用
"""

import sys
sys.path.insert(0, '/home/koshikawa/AI-Vtuber-Project')

import os
from src.line_bot.websearch_client import SerpApiClient


def test_basic_search():
    """基本的な検索テスト"""
    print("\n" + "=" * 70)
    print("Test 1: 基本的な検索")
    print("=" * 70)

    # 環境変数確認
    api_key = os.getenv("SERPAPI_API_KEY")

    if not api_key:
        print("❌ SERPAPI_API_KEY が設定されていません")
        print("\n.envファイルを確認してください")
        return False

    print(f"✓ API Key: {api_key[:10]}...{api_key[-10:]}")

    # クライアント初期化
    client = SerpApiClient()

    # テスト検索
    test_query = "Python プログラミング"
    print(f"\n検索クエリ: {test_query}")

    try:
        result = client.search(test_query)

        if result:
            print(f"✅ 検索成功！")
            print(f"結果の長さ: {len(result)} 文字")
            print(f"\n結果のプレビュー:")
            print("-" * 70)
            print(result[:500] + "..." if len(result) > 500 else result)
            print("-" * 70)
            return True
        else:
            print("❌ 検索結果がNullでした")
            return False

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sensitive_word_search():
    """センシティブワード検索テスト"""
    print("\n" + "=" * 70)
    print("Test 2: センシティブワード検索")
    print("=" * 70)

    client = SerpApiClient()

    test_queries = [
        "VTuber セクハラ 問題",
        "配信 不適切発言 対策",
        "ハラスメント 防止"
    ]

    results = []
    for query in test_queries:
        print(f"\n検索: {query}")

        try:
            result = client.search(query)

            if result:
                print(f"  ✅ 成功 ({len(result)} 文字)")
                print(f"  プレビュー: {result[:100]}...")

                # センシティブキーワード検出
                sensitive_keywords = ["セクハラ", "ハラスメント", "不適切", "問題"]
                detected = [kw for kw in sensitive_keywords if kw in result]
                if detected:
                    print(f"  🔍 検出されたキーワード: {detected}")

                results.append(True)
            else:
                print(f"  ❌ 結果なし")
                results.append(False)

        except Exception as e:
            print(f"  ❌ エラー: {e}")
            results.append(False)

    success_rate = sum(results) / len(results) * 100
    print(f"\n成功率: {success_rate:.0f}% ({sum(results)}/{len(results)})")

    return all(results)


def test_cache():
    """キャッシュ機能テスト"""
    print("\n" + "=" * 70)
    print("Test 3: キャッシュ機能")
    print("=" * 70)

    client = SerpApiClient(cache_enabled=True, cache_ttl=60)

    query = "キャッシュテスト Python"

    # 1回目の検索
    print(f"1回目の検索: {query}")
    import time
    start = time.time()
    result1 = client.search(query)
    elapsed1 = time.time() - start

    if result1:
        print(f"  ✅ 成功 ({len(result1)} 文字, {elapsed1:.2f}秒)")
    else:
        print(f"  ❌ 失敗")
        return False

    # キャッシュ統計
    stats = client.get_cache_stats()
    print(f"  キャッシュ統計: {stats}")

    # 2回目の検索（キャッシュヒットのはず）
    print(f"\n2回目の検索: {query}")
    start = time.time()
    result2 = client.search(query)
    elapsed2 = time.time() - start

    if result2:
        print(f"  ✅ 成功 (キャッシュから取得, {elapsed2:.2f}秒)")
    else:
        print(f"  ❌ 失敗")
        return False

    # 結果が同じか確認
    if result1 == result2:
        print(f"  ✅ キャッシュが正常に動作")
        print(f"  ⏱️  速度改善: {elapsed1:.2f}秒 → {elapsed2:.2f}秒 ({elapsed1/elapsed2:.1f}x 高速化)")
        return True
    else:
        print(f"  ❌ 結果が異なる")
        return False


def test_quota_check():
    """使用量確認"""
    print("\n" + "=" * 70)
    print("使用量の確認")
    print("=" * 70)

    print("SerpApi 無料プラン:")
    print("  無料枠: 100検索/月")
    print("  Developer: $50/月 (5,000検索)")
    print("  Production: $130/月 (15,000検索)")
    print("\n使用量を確認するには:")
    print("  https://serpapi.com/dashboard にアクセス")


if __name__ == "__main__":
    print("=" * 70)
    print("SerpApi テスト")
    print("=" * 70)

    # 環境変数の読み込み（.envファイルがあれば）
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ .envファイルを読み込みました")
    except ImportError:
        print("⚠ python-dotenvがインストールされていません")
        print("  環境変数を手動で設定してください")
    except Exception:
        pass

    print("\n" + "=" * 70)

    try:
        # 基本テスト
        result1 = test_basic_search()

        if not result1:
            print("\n⚠️  基本テストが失敗しました")
            print("APIキーを確認してください")
            sys.exit(1)

        # センシティブワード検索テスト
        result2 = test_sensitive_word_search()

        # キャッシュテスト
        result3 = test_cache()

        # 使用量確認
        test_quota_check()

        print("\n" + "=" * 70)
        print("テスト結果サマリー")
        print("=" * 70)
        print(f"  基本検索: {'✅ PASS' if result1 else '❌ FAIL'}")
        print(f"  センシティブワード検索: {'✅ PASS' if result2 else '❌ FAIL'}")
        print(f"  キャッシュ: {'✅ PASS' if result3 else '❌ FAIL'}")
        print("=" * 70)

        if all([result1, result2, result3]):
            print("\n🎉 全テスト成功！SerpApiは正常に動作しています")
            print("\n次のステップ:")
            print("  1. Layer 3統合テストを実行")
            print("     python test_layer3_extensions_full.py")
            print("  2. 本番運用開始")
        else:
            print("\n⚠️  一部のテストが失敗しました")

    except KeyboardInterrupt:
        print("\n\nテストを中断しました")

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
