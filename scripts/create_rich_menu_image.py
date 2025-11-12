#!/usr/bin/env python3
"""
LINE Rich Menu Image Creator

3姉妹のキャラクターアイコンを横並びに配置したリッチメニュー画像を作成する
LINE Rich Menu Size: 2500 x 843px (half menu)
"""

from PIL import Image, ImageDraw, ImageFont
import os

# 入力画像パス
BOTAN_ICON = "/home/koshikawa/AI-Vtuber-Project/screenshots/botan.png"
KASHO_ICON = "/home/koshikawa/AI-Vtuber-Project/screenshots/kasho.png"
YURI_ICON = "/home/koshikawa/AI-Vtuber-Project/screenshots/yuri.png"

# 出力画像パス
OUTPUT_IMAGE = "/home/koshikawa/AI-Vtuber-Project/screenshots/rich_menu_3sisters.png"

# LINE Rich Menu サイズ (half menu)
MENU_WIDTH = 2500
MENU_HEIGHT = 843

# 各キャラクターエリアの幅
CHAR_AREA_WIDTH = MENU_WIDTH // 3  # 833px

# 背景色（白）
BG_COLOR = (255, 255, 255)

# テキスト色（黒）
TEXT_COLOR = (0, 0, 0)

# キャラクター情報
CHARACTERS = [
    {"name": "牡丹", "name_en": "Botan", "icon": BOTAN_ICON},
    {"name": "花相", "name_en": "Kasho", "icon": KASHO_ICON},
    {"name": "百合", "name_en": "Yuri", "icon": YURI_ICON},
]


def create_rich_menu_image():
    """リッチメニュー画像を作成"""
    print(f"Creating LINE Rich Menu image ({MENU_WIDTH}x{MENU_HEIGHT}px)...")

    # 新しい画像を作成（白背景）
    menu_image = Image.new('RGB', (MENU_WIDTH, MENU_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(menu_image)

    # 各キャラクターを配置
    for i, char in enumerate(CHARACTERS):
        x_offset = i * CHAR_AREA_WIDTH

        print(f"  Processing {char['name']} ({char['name_en']})...")

        # アイコン画像を読み込み
        icon = Image.open(char["icon"])

        # アイコンをリサイズ（正方形、高さの80%程度）
        icon_size = int(MENU_HEIGHT * 0.6)  # 約505px
        icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

        # アイコンを配置（中央揃え）
        icon_x = x_offset + (CHAR_AREA_WIDTH - icon_size) // 2
        icon_y = int(MENU_HEIGHT * 0.15)  # 上部に配置

        # アイコンが透明度を持つ場合は透過合成
        if icon.mode == 'RGBA':
            menu_image.paste(icon, (icon_x, icon_y), icon)
        else:
            menu_image.paste(icon, (icon_x, icon_y))

        # キャラクター名を描画（アイコンの下）
        try:
            # フォントサイズを大きめに（60pt）
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            # フォントが見つからない場合はデフォルト
            font = ImageFont.load_default()

        # テキストのバウンディングボックスを取得
        text = char["name"]
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # テキストを中央揃えで配置
        text_x = x_offset + (CHAR_AREA_WIDTH - text_width) // 2
        text_y = icon_y + icon_size + 20  # アイコンの下に配置

        draw.text((text_x, text_y), text, fill=TEXT_COLOR, font=font)

        # 区切り線を描画（最後のキャラクター以外）
        if i < len(CHARACTERS) - 1:
            line_x = x_offset + CHAR_AREA_WIDTH
            draw.line([(line_x, 0), (line_x, MENU_HEIGHT)], fill=(200, 200, 200), width=2)

    # 画像を保存
    menu_image.save(OUTPUT_IMAGE, "PNG")
    print(f"\n✅ Rich Menu image created: {OUTPUT_IMAGE}")
    print(f"   Size: {MENU_WIDTH}x{MENU_HEIGHT}px")
    print(f"   File size: {os.path.getsize(OUTPUT_IMAGE) / 1024:.1f} KB")

    return OUTPUT_IMAGE


if __name__ == "__main__":
    create_rich_menu_image()
