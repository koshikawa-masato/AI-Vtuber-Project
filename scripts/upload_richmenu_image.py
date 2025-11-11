#!/usr/bin/env python3
"""
リッチメニュー画像アップロードスクリプト

既存のリッチメニューに画像をアップロードします。
"""

import os
import sys
import requests
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


def upload_image(richmenu_id, image_path):
    """リッチメニュー画像をアップロード"""

    if not os.path.exists(image_path):
        print(f"❌ 画像ファイルが見つかりません: {image_path}")
        sys.exit(1)

    # 画像アップロードAPIエンドポイント（api-data.line.me）
    url = f"https://api-data.line.me/v2/bot/richmenu/{richmenu_id}/content"

    with open(image_path, 'rb') as f:
        image_data = f.read()

    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "image/png"
    }

    print(f"🖼️  リッチメニュー画像をアップロード中...")
    print(f"   Rich Menu ID: {richmenu_id}")
    print(f"   Image Path: {image_path}")
    print(f"   Image Size: {len(image_data)} bytes")

    response = requests.post(url, headers=headers, data=image_data)

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

    url = f"https://api.line.me/v2/bot/user/all/richmenu/{richmenu_id}"

    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

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


def main():
    """メイン処理"""

    # リッチメニューID（既存）
    richmenu_id = "richmenu-6a4c8989e3ee2d443200de0a825ce1c3"

    # 画像パス
    image_path = "/home/koshikawa/AI-Vtuber-Project/assets/richmenu_sisters.png"

    print("=" * 60)
    print("🖼️  リッチメニュー画像アップロード")
    print("=" * 60)
    print()

    # 画像をアップロード
    success = upload_image(richmenu_id, image_path)

    if not success:
        print("\n❌ 画像アップロードに失敗しました")
        sys.exit(1)

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
