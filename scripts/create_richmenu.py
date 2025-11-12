#!/usr/bin/env python3
"""
LINE Bot リッチメニュー作成スクリプト

三姉妹（牡丹、Kasho、ユリ）を選択できるリッチメニューを作成します。
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# プロジェクトルートを追加
sys.path.insert(0, '/home/koshikawa/AI-Vtuber-Project')

# .envファイルを読み込み
load_dotenv('/home/koshikawa/AI-Vtuber-Project/.env')

# LINE Channel Access Token
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

if not CHANNEL_ACCESS_TOKEN:
    print("❌ LINE_CHANNEL_ACCESS_TOKEN が設定されていません")
    sys.exit(1)

# LINE Messaging API エンドポイント
API_BASE = "https://api.line.me/v2/bot"

# ヘッダー
headers = {
    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}


def create_richmenu():
    """リッチメニューを作成"""

    # リッチメニュー設定
    richmenu_data = {
        "size": {
            "width": 2500,
            "height": 843
        },
        "selected": True,  # デフォルトで表示
        "name": "三姉妹選択メニュー",
        "chatBarText": "キャラクターを選択",
        "areas": [
            {
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "postback",
                    "data": "character=botan",
                    "displayText": "牡丹を選択"
                }
            },
            {
                "bounds": {
                    "x": 833,
                    "y": 0,
                    "width": 834,
                    "height": 843
                },
                "action": {
                    "type": "postback",
                    "data": "character=kasho",
                    "displayText": "Kashoを選択"
                }
            },
            {
                "bounds": {
                    "x": 1667,
                    "y": 0,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "postback",
                    "data": "character=yuri",
                    "displayText": "ユリを選択"
                }
            }
        ]
    }

    # リッチメニュー作成API
    url = f"{API_BASE}/richmenu"

    print("📝 リッチメニューを作成中...")
    response = requests.post(url, headers=headers, json=richmenu_data)

    if response.status_code == 200:
        richmenu_id = response.json()['richMenuId']
        print(f"✅ リッチメニュー作成成功！")
        print(f"   Rich Menu ID: {richmenu_id}")
        return richmenu_id
    else:
        print(f"❌ リッチメニュー作成失敗")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def upload_richmenu_image(richmenu_id, image_path):
    """リッチメニュー画像をアップロード"""

    if not os.path.exists(image_path):
        print(f"⚠️  画像ファイルが見つかりません: {image_path}")
        print(f"   画像なしでリッチメニューを作成します")
        return False

    # 画像アップロードは api-data.line.me を使用
    url = f"https://api-data.line.me/v2/bot/richmenu/{richmenu_id}/content"

    with open(image_path, 'rb') as f:
        image_data = f.read()

    headers_image = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "image/png"
    }

    print("🖼️  リッチメニュー画像をアップロード中...")
    response = requests.post(url, headers=headers_image, data=image_data)

    if response.status_code == 200:
        print("✅ 画像アップロード成功！")
        return True
    else:
        print(f"❌ 画像アップロード失敗")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def set_default_richmenu(richmenu_id):
    """デフォルトリッチメニューに設定"""

    url = f"{API_BASE}/user/all/richmenu/{richmenu_id}"

    print("🔧 デフォルトリッチメニューに設定中...")
    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        print("✅ デフォルトリッチメニュー設定成功！")
        return True
    else:
        print(f"❌ デフォルトリッチメニュー設定失敗")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def list_richmenus():
    """既存のリッチメニュー一覧を取得"""

    url = f"{API_BASE}/richmenu/list"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        richmenus = response.json().get('richmenus', [])
        print(f"\n📋 既存のリッチメニュー: {len(richmenus)}件")
        for rm in richmenus:
            print(f"   - {rm['name']} (ID: {rm['richMenuId']})")
        return richmenus
    else:
        print(f"❌ リッチメニュー一覧取得失敗")
        return []


def delete_richmenu(richmenu_id):
    """リッチメニューを削除"""

    url = f"{API_BASE}/richmenu/{richmenu_id}"

    response = requests.delete(url, headers=headers)

    if response.status_code == 200:
        print(f"✅ リッチメニュー削除成功: {richmenu_id}")
        return True
    else:
        print(f"❌ リッチメニュー削除失敗: {richmenu_id}")
        return False


def main():
    """メイン処理"""

    print("=" * 60)
    print("🎨 Café Trois Fleurs - リッチメニュー作成")
    print("=" * 60)
    print()

    # 既存のリッチメニューを確認
    existing_menus = list_richmenus()

    # 既存のリッチメニューを削除するか確認
    if existing_menus:
        print("\n⚠️  既存のリッチメニューがあります。削除しますか？")
        response = input("削除する場合は 'y' を入力: ")
        if response.lower() == 'y':
            for menu in existing_menus:
                delete_richmenu(menu['richMenuId'])

    print()

    # リッチメニューを作成
    richmenu_id = create_richmenu()

    if not richmenu_id:
        print("\n❌ リッチメニュー作成に失敗しました")
        sys.exit(1)

    print()

    # 画像パス
    image_path = "/home/koshikawa/AI-Vtuber-Project/assets/richmenu_sisters.png"

    # 画像をアップロード（画像がある場合のみ）
    upload_richmenu_image(richmenu_id, image_path)

    print()

    # デフォルトリッチメニューに設定
    set_default_richmenu(richmenu_id)

    print()
    print("=" * 60)
    print("✅ リッチメニュー設定完了！")
    print("=" * 60)
    print()
    print("📱 LINEアプリで確認してください。")
    print("   画面下部にリッチメニューが表示されます。")
    print()


if __name__ == "__main__":
    main()
