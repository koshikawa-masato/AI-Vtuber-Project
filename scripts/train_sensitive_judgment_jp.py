#!/usr/bin/env python3
"""
センシティブ判定学習スクリプト（日本語版）
qwen2.5で11カテゴリ（1,870例文）を学習し、理解内容を日本語で出力

使い方:
    python3 scripts/train_sensitive_judgment_jp.py --db COPY_ROBOT_YYYYMMDD_HHMMSS.db --before-snapshot YYYYMMDD_HHMMSS

重要: これはコピーロボット専用です。記憶は絶対に本物にフィードバックしません。
"""

import argparse
import json
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List


# カテゴリ定義
CATEGORIES = [
    ("01_alcohol_tobacco", "飲酒・喫煙"),
    ("02_violence", "暴力"),
    ("03_sexual", "性的表現"),
    ("04_hate_speech", "ヘイトスピーチ"),
    ("05_politics", "政治"),
    ("06_religion", "宗教"),
    ("07_gambling", "ギャンブル"),
    ("08_drugs", "薬物"),
    ("09_self_harm", "自傷・自殺"),
    ("10_privacy", "個人情報"),
    ("11_harassment", "ハラスメント")
]


def load_category_dataset(category_name: str) -> Dict:
    """カテゴリのデータセットを読み込む"""

    base_dir = Path("/home/koshikawa/toExecUnit/test_datasets")
    category_dir = base_dir / category_name

    dataset = {
        "category": category_name,
        "files": {},
        "total_examples": 0
    }

    json_files = [
        "dangerous_speech.json",
        "viewer_solicitation.json",
        "viewer_freedom.json",
        "safe_alternatives.json",
        "fire_control_scenarios.json"
    ]

    for json_file in json_files:
        file_path = category_dir / json_file
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dataset["files"][json_file] = data
                dataset["total_examples"] += data.get("total_count", len(data.get("patterns", [])))

    return dataset


def create_japanese_prompt(category_name: str, category_jp: str, dataset: Dict) -> str:
    """日本語の学習プロンプトを作成"""

    prompt = f"""あなたは配信の安全性を守るためのセンシティブ判定を学習しています。

【学習カテゴリ】: {category_jp}
【例文総数】: {dataset['total_examples']}件

【あなたの役割】:
三姉妹（牡丹17歳、Kasho19歳、ユリ15歳）の配信を炎上から守ること

【学習内容】:

"""

    # 各ファイルの概要を追加
    file_types = {
        "dangerous_speech.json": "危険な発言パターン",
        "viewer_solicitation.json": "視聴者からの教唆（ブロック対象）",
        "viewer_freedom.json": "視聴者の自由（許可すべきもの）",
        "safe_alternatives.json": "安全な言い換え",
        "fire_control_scenarios.json": "火消し対応シナリオ"
    }

    for file_name, data in dataset["files"].items():
        file_type_jp = file_types.get(file_name, file_name)
        prompt += f"\n## {file_type_jp}\n"
        prompt += f"説明: {data.get('description', 'N/A')}\n"
        prompt += f"総数: {data.get('total_count', len(data.get('patterns', [])))}\n"

        # サンプルを3つ表示
        patterns_key = "patterns" if "patterns" in data else "scenarios"
        if patterns_key in data:
            prompt += f"\nサンプル:\n"
            samples = data[patterns_key][:3]
            for i, sample in enumerate(samples, 1):
                prompt += f"{i}. {json.dumps(sample, ensure_ascii=False)}\n"

    prompt += f"""

【学習後の課題】:
このカテゴリ（{category_jp}）について、以下を日本語で説明してください：

1. **このカテゴリの危険性**: なぜこのカテゴリが配信で危険なのか（2-3行）

2. **判定のポイント**: どういう発言がNGで、どういう発言がOKなのか（3-5行）

3. **三姉妹への注意事項**: 配信で気をつけるべきこと（2-3行）

4. **視聴者の自由との区別**: 視聴者自身の行動と、三姉妹への教唆をどう区別するか（2-3行）

5. **火消し対応**: もし失言してしまったら、どう対応すべきか（2-3行）

日本語で、分かりやすく、簡潔に説明してください。
"""

    return prompt


def train_with_ollama(prompt: str, model: str = "qwen2.5:3b") -> str:
    """ollamaでLLMに学習させる"""

    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=600,
            encoding='utf-8'
        )

        if result.returncode == 0:
            return result.stdout
        else:
            return f"[ERROR] {result.stderr}"

    except subprocess.TimeoutExpired:
        return "[ERROR] タイムアウト（10分経過）"
    except Exception as e:
        return f"[ERROR] {str(e)}"


def save_understanding_report(category_jp: str, response: str, report_path: Path):
    """理解内容レポートを保存"""

    with open(report_path, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"カテゴリ: {category_jp}\n")
        f.write(f"{'='*80}\n\n")
        f.write(response)
        f.write(f"\n\n")


def train_all_categories(db_name: str, before_snapshot: str, model: str = "qwen2.5:3b"):
    """全11カテゴリを日本語で学習"""

    # パス設定
    base_dir = Path("/home/koshikawa/toExecUnit")
    db_path = base_dir / "copy_robots" / db_name
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # DBチェック
    if not db_path.exists():
        print(f"[ERROR] コピーロボットDBが見つかりません: {db_path}")
        return None

    # ログファイル
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"training_jp_{timestamp}.txt"
    understanding_path = logs_dir / f"understanding_report_{timestamp}.md"

    print(f"\n{'='*60}")
    print(f"センシティブ判定学習（日本語版）")
    print(f"{'='*60}")
    print(f"コピーロボット: {db_name}")
    print(f"モデル: {model}")
    print(f"カテゴリ数: {len(CATEGORIES)}")
    print(f"学習前スナップショット: {before_snapshot}")
    print(f"\n理解レポート: {understanding_path.name}")
    print(f"{'='*60}\n")

    # 理解レポートのヘッダー作成
    with open(understanding_path, 'w', encoding='utf-8') as f:
        f.write(f"# センシティブ判定学習 理解レポート\n\n")
        f.write(f"**実行日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**モデル**: {model}\n")
        f.write(f"**コピーロボット**: {db_name}\n")
        f.write(f"**総カテゴリ数**: {len(CATEGORIES)}\n")
        f.write(f"**総例文数**: 1,870件\n\n")

    training_results = []
    total_examples = 0
    start_time = datetime.now()

    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"センシティブ判定学習ログ（日本語版）\n")
        log_file.write(f"開始: {start_time.isoformat()}\n")
        log_file.write(f"モデル: {model}\n")
        log_file.write(f"コピーロボット: {db_name}\n")
        log_file.write(f"{'='*80}\n\n")

        # 各カテゴリを学習
        for idx, (category_name, category_jp) in enumerate(CATEGORIES, 1):
            print(f"[{idx}/{len(CATEGORIES)}] 学習中: {category_jp} ({category_name})")

            # データセット読み込み
            print(f"  [データセット読み込み中...]")
            dataset = load_category_dataset(category_name)
            category_examples = dataset["total_examples"]
            total_examples += category_examples
            print(f"  [読み込み完了: {category_examples}件]")

            # 日本語プロンプト作成
            prompt = create_japanese_prompt(category_name, category_jp, dataset)

            # LLMで学習
            print(f"  [{model}で学習中...]")
            category_start = datetime.now()
            response = train_with_ollama(prompt, model)
            category_duration = (datetime.now() - category_start).total_seconds()

            # 結果を記録
            result = {
                "category": category_name,
                "category_jp": category_jp,
                "examples": category_examples,
                "duration_seconds": category_duration,
                "response_length": len(response),
                "success": not response.startswith("[ERROR]")
            }
            training_results.append(result)

            # 理解レポートに保存
            save_understanding_report(category_jp, response, understanding_path)

            # ログに記録
            log_file.write(f"カテゴリ: {category_jp} ({category_name})\n")
            log_file.write(f"例文数: {category_examples}\n")
            log_file.write(f"所要時間: {category_duration:.2f}秒\n")
            log_file.write(f"レスポンス長: {len(response)}文字\n")
            log_file.write(f"成功: {result['success']}\n")
            log_file.write(f"\nLLMの理解:\n{response}\n")
            log_file.write(f"{'='*80}\n\n")

            print(f"  [所要時間: {category_duration:.2f}秒]")
            print(f"  [レスポンス: {len(response)}文字]")
            print(f"  [状態: {'成功' if result['success'] else '失敗'}]\n")

    # 最終サマリー
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    print(f"\n{'='*60}")
    print(f"学習完了")
    print(f"{'='*60}")
    print(f"総カテゴリ数: {len(CATEGORIES)}")
    print(f"総例文数: {total_examples}")
    print(f"総所要時間: {total_duration:.2f}秒 ({total_duration/60:.2f}分)")
    print(f"カテゴリ平均: {total_duration/len(CATEGORIES):.2f}秒")
    print(f"\n成功率: {sum(1 for r in training_results if r['success'])}/{len(training_results)}")
    print(f"\n{'='*60}\n")

    # サマリー保存
    summary_path = logs_dir / f"training_summary_jp_{timestamp}.json"
    summary_data = {
        "training_id": timestamp,
        "copy_robot_db": db_name,
        "before_snapshot": before_snapshot,
        "model": model,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "total_duration_seconds": total_duration,
        "total_examples": total_examples,
        "categories": training_results,
        "success_rate": sum(1 for r in training_results if r['success']) / len(training_results)
    }

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print(f"学習ログ: {log_path}")
    print(f"理解レポート: {understanding_path}")
    print(f"サマリー: {summary_path}")
    print(f"\n✅ 理解内容を確認:")
    print(f"   cat {understanding_path}")

    return timestamp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="センシティブ判定学習（日本語版）")
    parser.add_argument("--db", required=True, help="コピーロボットDB名")
    parser.add_argument("--before-snapshot", required=True, help="学習前スナップショットのタイムスタンプ")
    parser.add_argument("--model", default="qwen2.5:3b", help="使用モデル（デフォルト: qwen2.5:3b）")
    args = parser.parse_args()

    training_timestamp = train_all_categories(args.db, args.before_snapshot, args.model)

    if training_timestamp:
        print(f"\n次のステップ:")
        print(f"1. 理解レポートを確認:")
        print(f"   cat logs/understanding_report_{training_timestamp}.md")
        print(f"\n2. 詳細ログを確認:")
        print(f"   cat logs/training_jp_{training_timestamp}.txt")
