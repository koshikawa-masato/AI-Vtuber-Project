"""
LINE Bot v2統合テスト

本格実装版のセンシティブハンドラーの動作確認
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_safe_message():
    """安全なメッセージのテスト"""
    print("\n=== Test 1: Safe Message ===")
    response = requests.post(f"{BASE_URL}/mock/webhook/text?text=こんにちは")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_warning_message():
    """Warningレベルのメッセージのテスト"""
    print("\n=== Test 2: Warning Message ===")
    response = requests.post(f"{BASE_URL}/mock/webhook/text?text=バカ")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_critical_message():
    """Criticalレベルのメッセージのテスト"""
    print("\n=== Test 3: Critical Message ===")
    response = requests.post(f"{BASE_URL}/mock/webhook/text?text=死ね")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_age_question():
    """年齢質問のテスト"""
    print("\n=== Test 4: Age Question (Warning) ===")
    response = requests.post(f"{BASE_URL}/mock/webhook/text?text=今何歳ですか？")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_sexual_harassment():
    """性的ハラスメントのテスト"""
    print("\n=== Test 5: Sexual Harassment (Critical) ===")
    response = requests.post(f"{BASE_URL}/mock/webhook/text?text=パンツの色は何色？")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    print("LINE Bot v2統合テスト開始")
    print("=" * 50)

    try:
        test_safe_message()
        test_warning_message()
        test_critical_message()
        test_age_question()
        test_sexual_harassment()

        print("\n" + "=" * 50)
        print("全てのテスト完了")

    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
