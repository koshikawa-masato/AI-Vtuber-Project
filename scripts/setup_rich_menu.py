#!/usr/bin/env python3
"""
LINE Rich Menu Setup Script

リッチメニューを作成してLINE Botに設定する
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.line_bot.rich_menu_manager import RichMenuManager, SimpleMockRichMenuManager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 設定
CHANNEL_ACCESS_TOKEN = "dummy_token_for_mock"
MOCK_MODE = True
RICH_MENU_IMAGE_PATH = "/home/koshikawa/AI-Vtuber-Project/screenshots/rich_menu_3sisters.png"


def main():
    """メイン処理"""
    logger.info("=" * 50)
    logger.info("LINE Rich Menu Setup")
    logger.info("=" * 50)

    # RichMenuManager初期化
    if MOCK_MODE:
        logger.info("モックモードで実行")
        manager = RichMenuManager(
            channel_access_token=CHANNEL_ACCESS_TOKEN,
            mock_mode=True
        )
    else:
        logger.info("実モードで実行（要: LINE Channel Access Token）")
        # 本番環境では環境変数からトークンを取得
        manager = RichMenuManager(
            channel_access_token=CHANNEL_ACCESS_TOKEN,
            mock_mode=False
        )

    # 既存のリッチメニューを確認
    logger.info("\n既存のリッチメニューを確認中...")
    existing_menus = manager.list_rich_menus()
    logger.info(f"  既存メニュー数: {len(existing_menus)}")

    # 3姉妹メニューを作成
    logger.info("\n3姉妹キャラクター選択メニューを作成中...")
    rich_menu_id = manager.create_3sisters_menu(
        menu_image_path=RICH_MENU_IMAGE_PATH,
        menu_name="3姉妹キャラクター選択"
    )

    if rich_menu_id:
        logger.info(f"✅ リッチメニュー作成成功: {rich_menu_id}")

        # デフォルトメニューに設定
        logger.info("\nデフォルトメニューに設定中...")
        if manager.set_default_rich_menu(rich_menu_id):
            logger.info("✅ デフォルトメニュー設定成功")
        else:
            logger.error("❌ デフォルトメニュー設定失敗")
    else:
        logger.error("❌ リッチメニュー作成失敗")

    logger.info("\n" + "=" * 50)
    logger.info("セットアップ完了")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
