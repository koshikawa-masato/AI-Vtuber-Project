#!/usr/bin/env python3
"""
リッチメニュー統合テスト

キャラクター選択とセッション管理の動作確認
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_character_selection_botan():
    """牡丹を選択"""
    print("\n=== Test 1: キャラクター選択 - 牡丹 ===")
    response = requests.post(f"{BASE_URL}/mock/webhook/postback?data=character=botan")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_character_selection_kasho():
    """花相を選択"""
    print("\n=== Test 2: キャラクター選択 - 花相 ===")
    response = requests.post(f"{BASE_URL}/mock/webhook/postback?data=character=kasho")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_character_selection_yuri():
    """百合を選択"""
    print("\n=== Test 3: キャラクター選択 - 百合 ===")
    response = requests.post(f"{BASE_URL}/mock/webhook/postback?data=character=yuri")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_conversation_after_selection():
    """キャラクター選択後の会話"""
    print("\n=== Test 4: キャラクター選択後の会話 ===")

    # まず花相を選択
    print("  Step 1: 花相を選択")
    requests.post(f"{BASE_URL}/mock/webhook/postback?data=character=kasho")
    time.sleep(0.5)

    # 会話を送信
    print("  Step 2: メッセージ送信（花相で応答されるはず）")
    response = requests.post(f"{BASE_URL}/mock/webhook/text?text=こんにちは")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_character_switch():
    """キャラクター切り替え"""
    print("\n=== Test 5: キャラクター切り替え ===")

    # まず牡丹を選択
    print("  Step 1: 牡丹を選択")
    requests.post(f"{BASE_URL}/mock/webhook/postback?data=character=botan")
    time.sleep(0.5)

    # 会話を送信
    print("  Step 2: メッセージ送信（牡丹で応答されるはず）")
    requests.post(f"{BASE_URL}/mock/webhook/text?text=今日はいい天気だね")
    time.sleep(0.5)

    # 百合に切り替え
    print("  Step 3: 百合に切り替え")
    requests.post(f"{BASE_URL}/mock/webhook/postback?data=character=yuri")
    time.sleep(0.5)

    # 会話を送信
    print("  Step 4: メッセージ送信（百合で応答されるはず）")
    response = requests.post(f"{BASE_URL}/mock/webhook/text?text=おすすめの本ある？")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_invalid_character():
    """無効なキャラクター選択"""
    print("\n=== Test 6: 無効なキャラクター選択 ===")
    response = requests.post(f"{BASE_URL}/mock/webhook/postback?data=character=invalid")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_default_character():
    """デフォルトキャラクター（未選択時）"""
    print("\n=== Test 7: デフォルトキャラクター（新規ユーザー） ===")
    print("  Note: 実際にはユーザーIDが同じなので、前のテストの選択が残っている可能性あり")
    response = requests.post(f"{BASE_URL}/mock/webhook/text?text=はじめまして")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    print("リッチメニュー統合テスト開始")
    print("=" * 60)

    try:
        # 基本的なキャラクター選択テスト
        test_character_selection_botan()
        test_character_selection_kasho()
        test_character_selection_yuri()

        # 統合テスト
        test_conversation_after_selection()
        test_character_switch()

        # エラーケース
        test_invalid_character()
        test_default_character()

        print("\n" + "=" * 60)
        print("全てのテスト完了")

    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
