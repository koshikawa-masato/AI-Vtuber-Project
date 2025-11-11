#!/usr/bin/env python3
"""
リッチメニュー画像生成スクリプト

三姉妹（牡丹、Kasho、ユリ）のシンプルなリッチメニュー画像を生成します。
"""

from PIL import Image, ImageDraw, ImageFont
import os

# 画像サイズ（LINE仕様）
WIDTH = 2500
HEIGHT = 843

# 3分割
SECTION_WIDTH = WIDTH // 3

# カラースキーム
COLORS = {
    'botan': '#FFB6C1',     # ライトピンク（牡丹）
    'kasho': '#E6E6FA',     # ラベンダー（花相）
    'yuri': '#FFFACD',      # レモンシフォン（百合）
    'text': '#333333'       # テキスト色
}

# キャラクター情報
CHARACTERS = [
    {'name': '牡丹', 'romaji': 'Botan', 'color': 'botan', 'age': '17歳'},
    {'name': 'Kasho', 'romaji': '花相', 'color': 'kasho', 'age': '19歳'},
    {'name': 'ユリ', 'romaji': 'Yuri', 'color': 'yuri', 'age': '15歳'}
]


def create_richmenu_image(output_path):
    """リッチメニュー画像を作成"""

    # 新しい画像を作成
    img = Image.new('RGB', (WIDTH, HEIGHT), 'white')
    draw = ImageDraw.Draw(img)

    # フォントサイズ（日本語対応）
    font_path = "/home/koshikawa/AI-Vtuber-Project/assets/fonts/NotoSansCJKjp-Regular.otf"
    try:
        # 日本語フォントを使用
        font_large = ImageFont.truetype(font_path, 120)
        font_medium = ImageFont.truetype(font_path, 80)
        font_small = ImageFont.truetype(font_path, 60)
    except Exception as e:
        print(f"⚠️  フォント読み込みエラー: {e}")
        # フォントが見つからない場合はデフォルト
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 3人のキャラクターを描画
    for i, char in enumerate(CHARACTERS):
        x_start = i * SECTION_WIDTH
        x_center = x_start + SECTION_WIDTH // 2

        # 背景色
        draw.rectangle(
            [(x_start, 0), (x_start + SECTION_WIDTH, HEIGHT)],
            fill=COLORS[char['color']]
        )

        # 境界線（右側のみ、最後の要素は除く）
        if i < len(CHARACTERS) - 1:
            draw.line(
                [(x_start + SECTION_WIDTH, 0), (x_start + SECTION_WIDTH, HEIGHT)],
                fill='#CCCCCC',
                width=4
            )

        # キャラクター名（日本語）
        name_bbox = draw.textbbox((0, 0), char['name'], font=font_large)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = x_center - name_width // 2
        name_y = HEIGHT // 2 - 150
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

    # 画像を保存
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, 'PNG')

    print(f"✅ リッチメニュー画像を生成しました: {output_path}")
    print(f"   サイズ: {WIDTH}x{HEIGHT}px")


def main():
    """メイン処理"""

    output_path = "/home/koshikawa/AI-Vtuber-Project/assets/richmenu_sisters.png"

    print("=" * 60)
    print("🎨 リッチメニュー画像生成")
    print("=" * 60)
    print()

    create_richmenu_image(output_path)

    print()
    print("=" * 60)
    print("✅ 画像生成完了！")
    print("=" * 60)


if __name__ == "__main__":
    main()
