"""
Phase 5統合テスト
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

if __name__ == "__main__":
    print("Phase 5統合テスト開始")
    print("=" * 50)

    try:
        test_safe_message()
        test_warning_message()
        test_critical_message()

        print("\n" + "=" * 50)
        print("全てのテスト完了")

    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
