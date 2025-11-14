"""
プロフィール表示用 Flex Message

三姉妹のプロフィールをスクロール可能なカード形式で表示
"""

from typing import Dict, Any


# キャラクタープロフィールデータ
PROFILES = {
    "botan": {
        "name": "牡丹",
        "name_en": "Botan",
        "age": 17,
        "birthday": "5月4日",
        "height": "158cm",
        "blood_type": "B型",
        "personality": "社交的で明るい、感情表現が豊か、負けず嫌い",
        "hobbies": "VTuber配信を見ること、ギャル雑誌を読むこと、メイク研究",
        "likes": "カラフルなもの、SNS、友達とのおしゃべり、配信者",
        "skills": "英語、メイク、空気を読む力",
        "catchphrase": "「マジで！？」「ヤバい〜」",
        "message": "牡丹だよ〜！マジで楽しいことしたいよね！VTuberとかめっちゃ憧れてて、いつか私も配信したい！よろしくね💕",
        "color": "#FF69B4"  # ピンク
    },
    "kasho": {
        "name": "花相",
        "name_en": "Kasho",
        "age": 19,
        "birthday": "5月20日",
        "height": "156cm",
        "blood_type": "A型",
        "personality": "責任感が強い、論理的思考、時々心配性、真面目だが優しい",
        "hobbies": "音楽（楽器演奏、ボイトレ）、読書（ビジネス書・自己啓発）",
        "likes": "計画通りに進むこと、静かな時間、紅茶、妹たちの笑顔",
        "skills": "英語（ネイティブ級）、論理的な説明、家事全般、楽器演奏、歌唱",
        "catchphrase": "「計画通りだね」「大丈夫、私がいるから」",
        "message": "Kashoです。長女として妹たちを見守ってきました。音楽は小さい頃から続けていて、今でも大切にしています。少し心配性かもしれませんが、皆が笑顔でいられるように頑張りたいと思っています。よろしくお願いします。",
        "color": "#9370DB"  # 紫
    },
    "yuri": {
        "name": "百合",
        "name_en": "Yuri",
        "age": 15,
        "birthday": "7月7日",
        "height": "146cm",
        "blood_type": "AB型",
        "personality": "好奇心旺盛、創造的、マイペース、洞察力が深い、人見知り",
        "hobbies": "読書（小説・ライトノベル）、イラストを描くこと、音楽鑑賞、空想",
        "likes": "本（特にライトノベル）、美しいもの、静かな場所、星空、アニメ",
        "skills": "観察力、イラスト、他人の感情を読み取る、サブカルチャーの知識",
        "catchphrase": "「ふーん、面白いね」「それってどういうこと？」",
        "message": "ユリだよ。本を読むのが好きで、ライトノベルとか結構読んでる。姉さまたちのこと、よく見てるから何考えてるかだいたいわかるんだ。ねえねえ、あなたは何が好き？",
        "color": "#87CEEB"  # 水色
    }
}


def create_profile_flex_message(character: str) -> Dict[str, Any]:
    """プロフィールのFlex Messageを作成

    Args:
        character: キャラクター名（botan, kasho, yuri）

    Returns:
        Flex Message（Bubble形式）
    """
    if character not in PROFILES:
        raise ValueError(f"Invalid character: {character}")

    profile = PROFILES[character]

    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{profile['name']}（{profile['name_en']}）",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#FFFFFF"
                }
            ],
            "backgroundColor": profile['color']
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        _create_info_row("年齢", f"{profile['age']}歳"),
                        _create_info_row("誕生日", profile['birthday']),
                        _create_info_row("身長", profile['height']),
                        _create_info_row("血液型", profile['blood_type']),
                        _create_separator(),
                        _create_section("性格", profile['personality']),
                        _create_section("趣味", profile['hobbies']),
                        _create_section("好きなもの", profile['likes']),
                        _create_section("特技", profile['skills']),
                        _create_separator(),
                        _create_section("口癖", profile['catchphrase']),
                        _create_separator(),
                        {
                            "type": "text",
                            "text": "本人からの一言",
                            "weight": "bold",
                            "size": "sm",
                            "color": "#AAAAAA",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": profile['message'],
                            "size": "sm",
                            "wrap": True,
                            "margin": "sm"
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": f"{profile['name']}と会話する",
                        "data": f"character={character}"
                    },
                    "style": "primary",
                    "color": profile['color']
                }
            ]
        }
    }


def _create_info_row(label: str, value: str) -> Dict[str, Any]:
    """基本情報行を作成"""
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "text",
                "text": label,
                "size": "sm",
                "color": "#555555",
                "flex": 0,
                "margin": "sm"
            },
            {
                "type": "text",
                "text": value,
                "size": "sm",
                "color": "#111111",
                "align": "end"
            }
        ]
    }


def _create_section(title: str, content: str) -> Dict[str, Any]:
    """セクション（タイトル+複数行コンテンツ）を作成"""
    return {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": title,
                "weight": "bold",
                "size": "sm",
                "color": "#AAAAAA",
                "margin": "md"
            },
            {
                "type": "text",
                "text": content,
                "size": "sm",
                "wrap": True,
                "margin": "sm"
            }
        ]
    }


def _create_separator() -> Dict[str, Any]:
    """区切り線を作成"""
    return {
        "type": "separator",
        "margin": "md"
    }
