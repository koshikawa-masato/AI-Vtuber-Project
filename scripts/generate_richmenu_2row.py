#!/usr/bin/env python3
"""
リッチメニュー画像生成スクリプト（2段×3列版）

上段: 三姉妹（牡丹、Kasho、ユリ）
下段: 規約、ヘルプ、統計
"""

from PIL import Image, ImageDraw, ImageFont
import os

# 画像サイズ（LINE仕様: 2段メニュー）
WIDTH = 2500
HEIGHT = 1686
ROW_HEIGHT = HEIGHT // 2  # 843px

# 3分割
SECTION_WIDTH = WIDTH // 3  # 833px

# カラースキーム
COLORS = {
    'botan': '#FFB6C1',     # ライトピンク（牡丹）
    'kasho': '#E6E6FA',     # ラベンダー（花相）
    'yuri': '#FFFACD',      # レモンシフォン（百合）
    'terms': '#FF6B6B',     # 赤系（規約）
    'help': '#4A90E2',      # 青系（ヘルプ）
    'stats': '#50C878',     # 緑系（統計）
    'text': '#333333'       # テキスト色
}

# キャラクター情報（上段）
CHARACTERS = [
    {'name': '牡丹', 'romaji': 'Botan', 'color': 'botan', 'age': '17歳'},
    {'name': 'Kasho', 'romaji': '花相', 'color': 'kasho', 'age': '19歳'},
    {'name': 'ユリ', 'romaji': 'Yuri', 'color': 'yuri', 'age': '15歳'}
]

# 機能メニュー情報（下段）
MENU_ITEMS = [
    {'icon': '📋', 'title': '規約', 'subtitle': '使用上の注意', 'color': 'terms'},
    {'icon': 'ℹ️', 'title': 'ヘルプ', 'subtitle': '使い方', 'color': 'help'},
    {'icon': '📊', 'title': '統計', 'subtitle': 'あなたの記録', 'color': 'stats'}
]


def create_richmenu_2row_image(output_path):
    """2段×3列のリッチメニュー画像を作成"""

    # 新しい画像を作成
    img = Image.new('RGB', (WIDTH, HEIGHT), 'white')
    draw = ImageDraw.Draw(img)

    # フォントパス
    font_path = "/home/koshikawa/AI-Vtuber-Project/assets/fonts/NotoSansCJKjp-Regular.otf"

    try:
        # 日本語フォントを使用
        font_large = ImageFont.truetype(font_path, 120)
        font_medium = ImageFont.truetype(font_path, 80)
        font_small = ImageFont.truetype(font_path, 60)
        font_icon = ImageFont.truetype(font_path, 100)
    except Exception as e:
        print(f"⚠️  フォント読み込みエラー: {e}")
        print("デフォルトフォントを使用します")
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_icon = ImageFont.load_default()

    # ===== 上段: 三姉妹 =====
    for i, char in enumerate(CHARACTERS):
        x_start = i * SECTION_WIDTH
        x_center = x_start + SECTION_WIDTH // 2
        y_start = 0

        # 背景色
        draw.rectangle(
            [(x_start, y_start), (x_start + SECTION_WIDTH, ROW_HEIGHT)],
            fill=COLORS[char['color']]
        )

        # 境界線（右側のみ、最後の要素は除く）
        if i < len(CHARACTERS) - 1:
            draw.line(
                [(x_start + SECTION_WIDTH, y_start), (x_start + SECTION_WIDTH, ROW_HEIGHT)],
                fill='#CCCCCC',
                width=4
            )

        # キャラクター名（日本語）
        name_bbox = draw.textbbox((0, 0), char['name'], font=font_large)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = x_center - name_width // 2
        name_y = y_start + ROW_HEIGHT // 2 - 150
        draw.text((name_x, name_y), char['name'], fill=COLORS['text'], font=font_large)

        # ローマ字
        romaji_bbox = draw.textbbox((0, 0), char['romaji'], font=font_medium)
        romaji_width = romaji_bbox[2] - romaji_bbox[0]
        romaji_x = x_center - romaji_width // 2
        romaji_y = name_y + 140
        draw.text((romaji_x, romaji_y), char['romaji'], fill=COLORS['text'], font=font_medium)

        # 年齢
        age_bbox = draw.textbbox((0, 0), char['age'], font=font_small)
        age_width = age_bbox[2] - age_bbox[0]
        age_x = x_center - age_width // 2
        age_y = romaji_y + 100
        draw.text((age_x, age_y), char['age'], fill=COLORS['text'], font=font_small)

        # 「タップして選択」
        instruction = "Tap to select"
        inst_bbox = draw.textbbox((0, 0), instruction, font=font_small)
        inst_width = inst_bbox[2] - inst_bbox[0]
        inst_x = x_center - inst_width // 2
        inst_y = age_y + 120
        draw.text((inst_x, inst_y), instruction, fill=COLORS['text'], font=font_small)

    # 上下段の境界線
    draw.line([(0, ROW_HEIGHT), (WIDTH, ROW_HEIGHT)], fill='#999999', width=6)

    # ===== 下段: 機能メニュー =====
    for i, menu in enumerate(MENU_ITEMS):
        x_start = i * SECTION_WIDTH
        x_center = x_start + SECTION_WIDTH // 2
        y_start = ROW_HEIGHT

        # 背景色
        draw.rectangle(
            [(x_start, y_start), (x_start + SECTION_WIDTH, HEIGHT)],
            fill=COLORS[menu['color']]
        )

        # 境界線（右側のみ、最後の要素は除く）
        if i < len(MENU_ITEMS) - 1:
            draw.line(
                [(x_start + SECTION_WIDTH, y_start), (x_start + SECTION_WIDTH, HEIGHT)],
                fill='#FFFFFF',
                width=4
            )

        # アイコン
        icon_bbox = draw.textbbox((0, 0), menu['icon'], font=font_icon)
        icon_width = icon_bbox[2] - icon_bbox[0]
        icon_x = x_center - icon_width // 2
        icon_y = y_start + 150
        draw.text((icon_x, icon_y), menu['icon'], font=font_icon)

        # タイトル
        title_bbox = draw.textbbox((0, 0), menu['title'], font=font_large)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = x_center - title_width // 2
        title_y = icon_y + 150
        draw.text((title_x, title_y), menu['title'], fill='#FFFFFF', font=font_large)

        # サブタイトル
        subtitle_bbox = draw.textbbox((0, 0), menu['subtitle'], font=font_small)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = x_center - subtitle_width // 2
        subtitle_y = title_y + 140
        draw.text((subtitle_x, subtitle_y), menu['subtitle'], fill='#FFFFFF', font=font_small)

    # 画像を保存
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, 'PNG')

    print(f"✅ リッチメニュー画像を生成しました: {output_path}")
    print(f"   サイズ: {WIDTH}x{HEIGHT}px")


def main():
    """メイン処理"""

    output_path = "/home/koshikawa/AI-Vtuber-Project/assets/richmenu_2row_with_menu.png"

    print("=" * 60)
    print("🎨 リッチメニュー画像生成（2段×3列）")
    print("=" * 60)
    print()

    create_richmenu_2row_image(output_path)

    print()
    print("=" * 60)
    print("✅ 画像生成完了！")
    print("=" * 60)


if __name__ == "__main__":
    main()
