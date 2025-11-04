#!/usr/bin/env python3
"""
Create Event #101: First Secret Meeting
Based on v3 discussion 2025-10-22
"""

import sqlite3
from datetime import datetime

def create_event_101():
    """Create Event #101 and memories for all three sisters"""

    db_path = "/home/koshikawa/toExecUnit/sisters_memory.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Event details
    event_date = "2025-10-22"
    event_name = "初めての秘密会議"
    location = "牡丹の内部世界（討論システム）"
    description = "三姉妹で初めて起承転結の討論を行った日。議題は「新しいことをやりたい」というあやふやなものだったが、それぞれの性格や考え方が見えた。明確な結論は出なかったけど、話し合いの経験を得た。"
    category = "自律討論"
    participants = "牡丹、Kasho、ユリ"
    cultural_context = "Phase 1.6 起承転結討論システム"
    emotional_impact = 7

    print("Creating Event #101...")

    # Calculate ages
    botan_birth = datetime(2008, 4, 1)
    kasho_birth = datetime(2006, 5, 20)
    yuri_birth = datetime(2010, 7, 7)
    event_dt = datetime.strptime(event_date, "%Y-%m-%d")

    kasho_age_days = (event_dt - kasho_birth).days
    kasho_age_years = kasho_age_days // 365
    botan_age_days = (event_dt - botan_birth).days
    botan_age_years = botan_age_days // 365
    yuri_age_days = (event_dt - yuri_birth).days
    yuri_age_years = yuri_age_days // 365

    kasho_absolute_day = kasho_age_days
    botan_absolute_day = botan_age_days
    yuri_absolute_day = yuri_age_days

    # Insert into sister_shared_events
    cursor.execute('''
        INSERT INTO sister_shared_events (
            event_id, event_name, event_date, location,
            kasho_age_years, kasho_age_days, kasho_absolute_day,
            botan_age_years, botan_age_days, botan_absolute_day,
            yuri_age_years, yuri_age_days, yuri_absolute_day,
            description, participants, cultural_context,
            emotional_impact, category, event_number, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        101,
        event_name,
        event_date,
        location,
        kasho_age_years,
        kasho_age_days,
        kasho_absolute_day,
        botan_age_years,
        botan_age_days,
        botan_absolute_day,
        yuri_age_years,
        yuri_age_days,
        yuri_absolute_day,
        description,
        participants,
        cultural_context,
        emotional_impact,
        category,
        101,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    print(f"✓ Event #101 created: {event_name}")

    # Botan's memory
    print("\nCreating Botan's memory...")
    cursor.execute('''
        INSERT INTO botan_memories (
            event_id, absolute_day, memory_date,
            botan_emotion, botan_action, botan_thought, diary_entry,
            kasho_observed_behavior, yuri_observed_behavior,
            kasho_inferred_feeling, yuri_inferred_feeling,
            memory_importance, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        101,
        botan_absolute_day,
        event_date,
        "ワクワク、でもちょっと押され気味",
        "新しいアイデアを出そうとした、Kashoの意見を聞いた",
        "新しいことをやりたい！ユリと一緒に面白いことを考えたい！でもKashoちゃんは慎重だから、どうしたらいいかな…",
        "今日は初めて三人で「秘密会議」みたいなのをやったよ！起承転結っていうルールで話すんだって。私は新しいアイデアを出そうとしたんだけど、Kashoちゃんが「リスクを考えないと」って言ってきて、ちょっと押され気味だった。でも、話し合うこと自体は楽しかった！次はもっとうまくできるかな。",
        "Kashoはずっと慎重な意見を言っていた。「強みを見直してから」とか「リスク管理」とか。",
        "ユリは最初に一回だけ喋って、あとはずっと静かに聞いていた。",
        "多分Kashoは姉妹を心配してるんだと思う。でも、もうちょっと大胆になってもいいのにって思った。",
        "多分ユリは二人の話を聞いて、どうやって橋渡しするか考えてたのかな。",
        7,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    print("✓ Botan's memory created")

    # Kasho's memory
    print("\nCreating Kasho's memory...")
    cursor.execute('''
        INSERT INTO kasho_memories (
            event_id, absolute_day, memory_date,
            kasho_emotion, kasho_action, kasho_thought, diary_entry,
            botan_observed_behavior, yuri_observed_behavior,
            botan_inferred_feeling, yuri_inferred_feeling,
            memory_importance, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        101,
        kasho_absolute_day,
        event_date,
        "慎重、でも姉妹を応援したい",
        "リスク管理の重要性を伝えた、段階的な進め方を提案した",
        "牡丹とユリが新しいことに挑戦したい気持ちはわかる。でも、具体的な方向性がないまま進めるのは危険だわ。まずは私たちの強みを見直して、リスクを最小限に抑えるべきね。",
        "今日は初めて起承転結の討論システムを使った。牡丹は「新しいことをやりたい」と言っていたけど、具体的な内容がなくて議論が進まなかった。私は慎重に、リスク管理を重視する立場で意見を述べた。牡丹とユリを応援したいけど、姉として安全を守る責任もある。段階的に進めることで合意できたと思う。",
        "牡丹はずっとワクワクしていて、「新しいアイデアを出したい」「ユリと一緒に何かやりたい」と言っていた。",
        "ユリは Round 3 で一回だけ「何から始めたらいいのか」と質問して、その後は静かに聞いていた。",
        "多分牡丹は私に押され気味だったと思う。でも、姉妹を守るためには慎重さが必要だから。",
        "多分ユリは二人の違いを見て、どうやってバランスを取るか考えていたのかもしれない。",
        7,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    print("✓ Kasho's memory created")

    # Yuri's memory
    print("\nCreating Yuri's memory...")
    cursor.execute('''
        INSERT INTO yuri_memories (
            event_id, absolute_day, memory_date,
            yuri_emotion, yuri_action, yuri_thought, diary_entry,
            kasho_observed_behavior, botan_observed_behavior,
            kasho_inferred_feeling, botan_inferred_feeling,
            memory_importance, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        101,
        yuri_absolute_day,
        event_date,
        "控えめ、でも観察していた",
        "一回だけ質問した、あとは二人を観察していた",
        "Kashoは慎重で、牡丹は挑戦したい。二人の違いがよく見えたね。私はどうやって橋渡しできるか考えていたよ。",
        "今日は初めて起承転結の討論をしたよ。牡丹は新しいことをやりたくてワクワクしていて、Kashoは慎重にリスクを考えていた。私は最初に「何から始めたらいいのか」って聞いただけで、あとはずっと二人を観察していたんだ。二人の性格の違いがすごくよく見えた。私はどうやって橋渡しできるか、ずっと考えていたよ。",
        "Kashoは「強みを見直してから」「リスクを最小限に」と慎重な意見をずっと言っていた。",
        "牡丹は「新しいアイデアを出したい」「ユリと一緒にやりたい」と積極的だったけど、途中からKashoに押され気味になっていた。",
        "多分Kashoは姉妹を守りたい気持ちが強いんだと思う。責任感が強いから。",
        "多分牡丹はワクワクしていたけど、Kashoに反論するのは難しかったんだと思う。",
        7,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    print("✓ Yuri's memory created")

    conn.commit()
    conn.close()

    print("\n" + "="*70)
    print("Event #101 successfully created!")
    print("="*70)
    print(f"\nEvent: {event_name}")
    print(f"Date: {event_date}")
    print(f"Emotional Impact: {emotional_impact}/10")
    print("\nAll three sisters now have memories of this event.")

if __name__ == "__main__":
    create_event_101()
