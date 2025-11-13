#!/usr/bin/env python3
"""
VPS用リッチメニューセットアップスクリプト

3姉妹キャラクター選択用のリッチメニューを作成・設定します
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.line_bot_vps.rich_menu_manager import RichMenuManager

# .envファイルを読み込み
load_dotenv()

def main():
    """メイン処理"""
    print("=" * 60)
    print("🎨 VPS用リッチメニューセットアップ")
    print("=" * 60)

    # 環境変数から認証情報を取得
    channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

    if not channel_access_token:
        print("❌ LINE_CHANNEL_ACCESS_TOKEN が設定されていません")
        print("   .env ファイルに設定してください")
        sys.exit(1)

    # リッチメニュー画像のパス
    menu_image_path = project_root / "assets" / "richmenu_sisters.png"

    if not menu_image_path.exists():
        print(f"❌ リッチメニュー画像が見つかりません: {menu_image_path}")
        sys.exit(1)

    print(f"📁 リッチメニュー画像: {menu_image_path}")
    print()

    # RichMenuManager初期化
    rich_menu_manager = RichMenuManager(
        channel_access_token=channel_access_token,
        mock_mode=False  # 本番モード
    )

    print()
    print("🎨 3姉妹キャラクター選択メニューを作成中...")

    # リッチメニュー作成
    rich_menu_id = rich_menu_manager.create_3sisters_menu(
        menu_image_path=str(menu_image_path),
        menu_name="Café Trois Fleurs - 3姉妹選択"
    )

    if not rich_menu_id:
        print("❌ リッチメニューの作成に失敗しました")
        sys.exit(1)

    print(f"✅ リッチメニュー作成完了: {rich_menu_id}")
    print()

    # デフォルトリッチメニューに設定
    print("🔧 デフォルトリッチメニューに設定中...")
    if rich_menu_manager.set_default_rich_menu(rich_menu_id):
        print("✅ デフォルトリッチメニューに設定完了")
    else:
        print("❌ デフォルトリッチメニューの設定に失敗しました")
        sys.exit(1)

    print()
    print("=" * 60)
    print("✅ リッチメニューセットアップ完了")
    print("=" * 60)
    print()
    print("📱 LINEアプリで確認してください")
    print("   - チャットバーに「キャラクター選択」が表示されます")
    print("   - タップすると3姉妹から選択できます")
    print()
    print("🎯 リッチメニューID: " + rich_menu_id)
    print()


if __name__ == "__main__":
    main()
