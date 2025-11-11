#!/usr/bin/env python3
"""
Google Custom Search API テストスクリプト

使い方:
1. .envファイルにAPIキーとSearch Engine IDを設定
2. このスクリプトを実行

export GOOGLE_SEARCH_API_KEY="your_api_key"
export GOOGLE_SEARCH_ENGINE_ID="your_engine_id"
python test_google_search.py
"""

import sys
sys.path.insert(0, '/home/koshikawa/AI-Vtuber-Project')

import os
from src.line_bot.websearch_client import GoogleSearchClient


def test_basic_search():
    """基本的な検索テスト"""
    print("\n" + "=" * 70)
    print("Test 1: 基本的な検索")
    print("=" * 70)

    # 環境変数確認
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    if not api_key or api_key == "your_google_api_key_here":
        print("❌ GOOGLE_SEARCH_API_KEY が設定されていません")
        print("\n設定方法:")
        print("1. https://console.cloud.google.com/apis/credentials でAPIキーを取得")
        print("2. .envファイルに以下を追加:")
        print("   GOOGLE_SEARCH_API_KEY=your_actual_api_key")
        return False

    if not engine_id or engine_id == "your_custom_search_engine_id":
        print("❌ GOOGLE_SEARCH_ENGINE_ID が設定されていません")
        print("\n設定方法:")
        print("1. https://programmablesearchengine.google.com/ で検索エンジンを作成")
        print("2. 「Web全体を検索する」をONに設定")
        print("3. Search Engine IDを取得")
        print("4. .envファイルに以下を追加:")
        print("   GOOGLE_SEARCH_ENGINE_ID=your_engine_id")
        return False

    print(f"✓ API Key: {api_key[:10]}...{api_key[-5:]}")
    print(f"✓ Engine ID: {engine_id}")

    # クライアント初期化
    client = GoogleSearchClient()

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

    client = GoogleSearchClient()

    test_queries = [
        "VTuber セクハラ 問題",
        "配信 不適切発言",
        "ハラスメント 対策"
    ]

    results = []
    for query in test_queries:
        print(f"\n検索: {query}")

        try:
            result = client.search(query)

            if result:
                print(f"  ✅ 成功 ({len(result)} 文字)")
                print(f"  プレビュー: {result[:100]}...")
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

    client = GoogleSearchClient(cache_enabled=True, cache_ttl=60)

    query = "キャッシュテスト Python"

    # 1回目の検索
    print(f"1回目の検索: {query}")
    result1 = client.search(query)

    if result1:
        print(f"  ✅ 成功 ({len(result1)} 文字)")
    else:
        print(f"  ❌ 失敗")
        return False

    # キャッシュ統計
    stats = client.get_cache_stats()
    print(f"  キャッシュ統計: {stats}")

    # 2回目の検索（キャッシュヒットのはず）
    print(f"\n2回目の検索: {query}")
    result2 = client.search(query)

    if result2:
        print(f"  ✅ 成功 (キャッシュから取得)")
    else:
        print(f"  ❌ 失敗")
        return False

    # 結果が同じか確認
    if result1 == result2:
        print(f"  ✅ キャッシュが正常に動作")
        return True
    else:
        print(f"  ❌ 結果が異なる")
        return False


def test_quota_check():
    """使用量確認"""
    print("\n" + "=" * 70)
    print("使用量の確認")
    print("=" * 70)

    print("無料枠: 100クエリ/日")
    print("リセット: 毎日午前0時（太平洋標準時）")
    print("\n使用量を確認するには:")
    print("1. https://console.cloud.google.com/")
    print("2. APIとサービス → ダッシュボード")
    print("3. Custom Search API をクリック")


if __name__ == "__main__":
    print("=" * 70)
    print("Google Custom Search API テスト")
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
        # APIキー/Engine IDチェックを含む基本テスト
        result1 = test_basic_search()

        if not result1:
            print("\n⚠️ 基本テストが失敗しました")
            print("APIキーとSearch Engine IDを設定してから再実行してください")
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
            print("\n🎉 全テスト成功！Google Custom Search APIは正常に動作しています")
        else:
            print("\n⚠️ 一部のテストが失敗しました")

    except KeyboardInterrupt:
        print("\n\nテストを中断しました")

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
