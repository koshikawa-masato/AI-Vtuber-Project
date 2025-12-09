"""
LINE Rich Menu Manager

リッチメニューの作成、画像アップロード、設定を管理
"""

import logging
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RichMenuArea:
    """リッチメニューのタップ領域"""
    bounds_x: int
    bounds_y: int
    bounds_width: int
    bounds_height: int
    action_type: str  # "postback", "message", "uri"
    action_data: str  # postbackデータ、メッセージテキスト、またはURI


class RichMenuManager:
    """リッチメニュー管理クラス

    モックモード時は実際のAPIを呼ばず、ログ出力のみ行う
    """

    def __init__(
        self,
        channel_access_token: str,
        mock_mode: bool = True
    ):
        """
        Args:
            channel_access_token: LINE Channel Access Token
            mock_mode: モックモード（True: API呼び出しをシミュレート）
        """
        self.channel_access_token = channel_access_token
        self.mock_mode = mock_mode
        self.base_url = "https://api.line.me/v2/bot"

        if mock_mode:
            logger.info("RichMenuManager initialized (MOCK MODE)")
        else:
            logger.info("RichMenuManager initialized (REAL MODE)")

    def create_3sisters_menu(
        self,
        menu_image_path: str,
        menu_name: str = "3姉妹キャラクター選択"
    ) -> Optional[str]:
        """3姉妹キャラクター選択用のリッチメニューを作成（2段×3列構成）

        上段: 機能メニュー（自動、FB、規約）
        下段: キャラクター選択（Kasho、牡丹、ユリ）

        Args:
            menu_image_path: メニュー画像のパス
            menu_name: メニュー名

        Returns:
            作成されたリッチメニューID（モックモード時はダミーID）
        """
        logger.info(f"Creating rich menu (2-row × 3-col layout): {menu_name}")

        # メニュー領域定義（2段×3列 = 6分割）
        menu_width = 2500
        menu_height = 1686  # 2段メニュー
        area_width = menu_width // 3  # 833px
        row_height = menu_height // 2  # 843px

        areas = [
            # 上段: 機能メニュー（自動、FB、規約）
            RichMenuArea(
                bounds_x=0,
                bounds_y=0,
                bounds_width=area_width,
                bounds_height=row_height,
                action_type="postback",
                action_data="action=auto"
            ),
            RichMenuArea(
                bounds_x=area_width,
                bounds_y=0,
                bounds_width=area_width,
                bounds_height=row_height,
                action_type="postback",
                action_data="action=feedback"
            ),
            RichMenuArea(
                bounds_x=area_width * 2,
                bounds_y=0,
                bounds_width=area_width,
                bounds_height=row_height,
                action_type="postback",
                action_data="action=terms"
            ),
            # 下段: キャラクター選択（Kasho、牡丹、ユリ）
            RichMenuArea(
                bounds_x=0,
                bounds_y=row_height,
                bounds_width=area_width,
                bounds_height=row_height,
                action_type="postback",
                action_data="character=kasho"
            ),
            RichMenuArea(
                bounds_x=area_width,
                bounds_y=row_height,
                bounds_width=area_width,
                bounds_height=row_height,
                action_type="postback",
                action_data="character=botan"
            ),
            RichMenuArea(
                bounds_x=area_width * 2,
                bounds_y=row_height,
                bounds_width=area_width,
                bounds_height=row_height,
                action_type="postback",
                action_data="character=yuri"
            ),
        ]

        # リッチメニューを作成
        rich_menu_id = self._create_rich_menu(
            name=menu_name,
            chat_bar_text="キャラクター選択",
            areas=areas,
            width=menu_width,
            height=menu_height
        )

        if not rich_menu_id:
            logger.error("Failed to create rich menu")
            return None

        # 画像をアップロード
        if not self._upload_rich_menu_image(rich_menu_id, menu_image_path):
            logger.error("Failed to upload rich menu image")
            return None

        logger.info(f"✅ Rich menu created successfully: {rich_menu_id}")
        return rich_menu_id

    def set_default_rich_menu(self, rich_menu_id: str) -> bool:
        """リッチメニューをデフォルトに設定

        Args:
            rich_menu_id: リッチメニューID

        Returns:
            成功したらTrue
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Setting default rich menu: {rich_menu_id}")
            return True

        url = f"{self.base_url}/user/all/richmenu/{rich_menu_id}"
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
        }

        try:
            response = requests.post(url, headers=headers)

            if response.status_code == 200:
                logger.info(f"✅ Default rich menu set: {rich_menu_id}")
                return True
            else:
                logger.error(f"Failed to set default rich menu: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error setting default rich menu: {e}")
            return False

    def _create_rich_menu(
        self,
        name: str,
        chat_bar_text: str,
        areas: List[RichMenuArea],
        width: int,
        height: int
    ) -> Optional[str]:
        """リッチメニューを作成（内部メソッド）

        Args:
            name: メニュー名
            chat_bar_text: チャットバーに表示されるテキスト
            areas: タップ領域のリスト
            width: メニュー幅
            height: メニュー高さ

        Returns:
            リッチメニューID
        """
        if self.mock_mode:
            mock_menu_id = "richmenu-mock-3sisters-12345"
            logger.info(f"[MOCK] Created rich menu: {mock_menu_id}")
            logger.info(f"  - Name: {name}")
            logger.info(f"  - Chat bar text: {chat_bar_text}")
            logger.info(f"  - Size: {width}x{height}px")
            logger.info(f"  - Areas: {len(areas)}")
            for i, area in enumerate(areas):
                logger.info(f"    Area {i+1}: ({area.bounds_x}, {area.bounds_y}) {area.bounds_width}x{area.bounds_height} -> {area.action_type}:{area.action_data}")
            return mock_menu_id

        # リッチメニュー作成リクエストボディ
        rich_menu_data = {
            "size": {
                "width": width,
                "height": height
            },
            "selected": True,
            "name": name,
            "chatBarText": chat_bar_text,
            "areas": [
                {
                    "bounds": {
                        "x": area.bounds_x,
                        "y": area.bounds_y,
                        "width": area.bounds_width,
                        "height": area.bounds_height
                    },
                    "action": {
                        "type": area.action_type,
                        "data": area.action_data
                    }
                }
                for area in areas
            ]
        }

        url = f"{self.base_url}/richmenu"
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=rich_menu_data, headers=headers)

            if response.status_code == 200:
                result = response.json()
                rich_menu_id = result.get("richMenuId")
                logger.info(f"✅ Rich menu created: {rich_menu_id}")
                return rich_menu_id
            else:
                logger.error(f"Failed to create rich menu: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating rich menu: {e}")
            return None

    def _upload_rich_menu_image(self, rich_menu_id: str, image_path: str) -> bool:
        """リッチメニュー画像をアップロード（内部メソッド）

        Args:
            rich_menu_id: リッチメニューID
            image_path: 画像ファイルパス

        Returns:
            成功したらTrue
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Uploading image to rich menu: {rich_menu_id}")
            logger.info(f"  - Image: {image_path}")
            return True

        # 画像アップロードはapi-data.line.meを使用
        url = f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content"
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
            "Content-Type": "image/png"
        }

        try:
            with open(image_path, 'rb') as image_file:
                response = requests.post(url, data=image_file, headers=headers)

            if response.status_code == 200:
                logger.info(f"✅ Rich menu image uploaded: {rich_menu_id}")
                return True
            else:
                logger.error(f"Failed to upload rich menu image: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error uploading rich menu image: {e}")
            return False

    def delete_rich_menu(self, rich_menu_id: str) -> bool:
        """リッチメニューを削除

        Args:
            rich_menu_id: リッチメニューID

        Returns:
            成功したらTrue
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Deleting rich menu: {rich_menu_id}")
            return True

        url = f"{self.base_url}/richmenu/{rich_menu_id}"
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
        }

        try:
            response = requests.delete(url, headers=headers)

            if response.status_code == 200:
                logger.info(f"✅ Rich menu deleted: {rich_menu_id}")
                return True
            else:
                logger.error(f"Failed to delete rich menu: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error deleting rich menu: {e}")
            return False

    def list_rich_menus(self) -> List[Dict[str, Any]]:
        """リッチメニュー一覧を取得

        Returns:
            リッチメニューのリスト
        """
        if self.mock_mode:
            logger.info("[MOCK] Listing rich menus")
            return [
                {
                    "richMenuId": "richmenu-mock-3sisters-12345",
                    "size": {"width": 2500, "height": 843},
                    "selected": True,
                    "name": "3姉妹キャラクター選択",
                    "chatBarText": "キャラクター選択",
                    "areas": []
                }
            ]

        url = f"{self.base_url}/richmenu/list"
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
        }

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                result = response.json()
                rich_menus = result.get("richmenus", [])
                logger.info(f"Found {len(rich_menus)} rich menus")
                return rich_menus
            else:
                logger.error(f"Failed to list rich menus: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error listing rich menus: {e}")
            return []


class SimpleMockRichMenuManager:
    """シンプルなモックリッチメニューマネージャー

    完全にモック動作のみ（テスト用）
    """

    def __init__(self):
        logger.info("SimpleMockRichMenuManager initialized")

    def create_3sisters_menu(self, menu_image_path: str, menu_name: str = "3姉妹キャラクター選択") -> str:
        logger.info(f"[SIMPLE MOCK] Creating rich menu: {menu_name}")
        logger.info(f"[SIMPLE MOCK] Image: {menu_image_path}")
        return "richmenu-simple-mock-12345"

    def set_default_rich_menu(self, rich_menu_id: str) -> bool:
        logger.info(f"[SIMPLE MOCK] Setting default rich menu: {rich_menu_id}")
        return True

    def delete_rich_menu(self, rich_menu_id: str) -> bool:
        logger.info(f"[SIMPLE MOCK] Deleting rich menu: {rich_menu_id}")
        return True

    def list_rich_menus(self) -> List[Dict[str, Any]]:
        logger.info("[SIMPLE MOCK] Listing rich menus")
        return []
