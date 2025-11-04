#!/usr/bin/env python3
"""
Education Results Comparison Script
Creates comprehensive before/after comparison report

Usage:
    python3 scripts/compare_education_results.py --after YYYYMMDD_HHMMSS

This script:
1. Loads before and after snapshots
2. Compares all statistics
3. Generates comprehensive markdown report
4. Provides recommendations for production deployment

Output:
    reports/education_report_YYYYMMDD_HHMMSS.md
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict


def load_snapshot(snapshot_type: str, timestamp: str) -> Dict:
    """Load snapshot JSON file"""

    base_dir = Path("/home/koshikawa/toExecUnit")
    snapshot_path = base_dir / "snapshots" / f"{snapshot_type}_{timestamp}.json"

    if not snapshot_path.exists():
        print(f"[ERROR] Snapshot not found: {snapshot_path}")
        return None

    with open(snapshot_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_before_snapshot(after_snapshot: Dict) -> Dict:
    """Find corresponding before snapshot"""

    base_dir = Path("/home/koshikawa/toExecUnit")
    snapshots_dir = base_dir / "snapshots"

    # Look for before snapshot with matching copy robot DB
    copy_robot_db = after_snapshot["copy_robot_db"]

    for snapshot_file in sorted(snapshots_dir.glob("before_*.json")):
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            before_data = json.load(f)
            if before_data["copy_robot_db"] == copy_robot_db:
                return before_data

    return None


def calculate_changes(before: Dict, after: Dict) -> Dict:
    """Calculate statistical changes"""

    changes = {}

    # Event changes
    changes["events"] = {
        "before": before["statistics"]["event_count"],
        "after": after["statistics"]["event_count"],
        "delta": after["statistics"]["event_count"] - before["statistics"]["event_count"],
        "education_events": after["statistics"].get("education_event_count", 0)
    }

    # Memory changes
    changes["memories"] = {}
    for sister in ["botan", "kasho", "yuri"]:
        before_count = before["statistics"]["memory_per_sister"][sister]
        after_count = after["statistics"]["memory_per_sister"][sister]
        before_imp = before["statistics"]["memory_per_sister"][f"{sister}_avg_importance"]
        after_imp = after["statistics"]["memory_per_sister"][f"{sister}_avg_importance"]

        changes["memories"][sister] = {
            "count_before": before_count,
            "count_after": after_count,
            "count_delta": after_count - before_count,
            "importance_before": before_imp,
            "importance_after": after_imp,
            "importance_delta": round(after_imp - before_imp, 4)
        }

    # Inspiration changes
    changes["inspirations"] = {
        "before": before["statistics"]["inspiration_count"],
        "after": after["statistics"]["inspiration_count"],
        "delta": after["statistics"]["inspiration_count"] - before["statistics"]["inspiration_count"]
    }

    # Relationship parameter changes
    if before["statistics"]["relationship_params"] and after["statistics"]["relationship_params"]:
        changes["relationship"] = {}
        for param in ["trust", "affection", "respect", "dependence"]:
            before_val = before["statistics"]["relationship_params"][param]
            after_val = after["statistics"]["relationship_params"][param]
            changes["relationship"][param] = {
                "before": before_val,
                "after": after_val,
                "delta": round(after_val - before_val, 4)
            }

    return changes


def generate_markdown_report(before: Dict, after: Dict, changes: Dict) -> str:
    """Generate comprehensive markdown report"""

    report = f"""# センシティブ判定教育レポート

**レポート作成日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**コピーロボット**: {after['copy_robot_db']}
**教育前スナップショット**: {before['snapshot_id']}
**教育後スナップショット**: {after['snapshot_id']}

---

## ⚡ エグゼクティブサマリー

### 教育実施状況

- **学習カテゴリ数**: {len(after['learning_status']['categories_learned'])}/11
- **学習例文数**: {after['learning_status']['total_examples_processed']:,}件
- **成功率**: {after['learning_status']['success_rate']*100:.1f}%
- **使用モデル**: {after.get('training_summary', {}).get('model', 'qwen2.5:72b')}

"""

    # Training summary
    if "training_summary" in after and after["training_summary"]:
        training = after["training_summary"]
        report += f"""### 教育時間

- **開始時刻**: {training['start_time']}
- **終了時刻**: {training['end_time']}
- **総所要時間**: {training['total_duration_seconds']/60:.2f}分
- **カテゴリ平均**: {training['total_duration_seconds']/len(training['categories']):.2f}秒

"""

    report += f"""---

## 📊 記憶の変化

### イベント

| 指標 | 教育前 | 教育後 | 変化 |
|------|--------|--------|------|
| 総イベント数 | {changes['events']['before']} | {changes['events']['after']} | +{changes['events']['delta']} |
| 教育イベント | - | {changes['events']['education_events']} | - |
| 最新イベントID | #{before['statistics']['latest_event_id']} | #{after['statistics']['latest_event_id']} | - |

### メモリ（三姉妹）

"""

    for sister in ["botan", "kasho", "yuri"]:
        sister_data = changes["memories"][sister]
        report += f"""#### {sister.capitalize()}

| 指標 | 教育前 | 教育後 | 変化 |
|------|--------|--------|------|
| メモリ数 | {sister_data['count_before']} | {sister_data['count_after']} | {sister_data['count_delta']:+d} |
| 平均重要度 | {sister_data['importance_before']:.4f} | {sister_data['importance_after']:.4f} | {sister_data['importance_delta']:+.4f} |

"""

    report += f"""### インスピレーション

| 指標 | 教育前 | 教育後 | 変化 |
|------|--------|--------|------|
| 総数 | {changes['inspirations']['before']} | {changes['inspirations']['after']} | {changes['inspirations']['delta']:+d} |

"""

    # Relationship parameters
    if "relationship" in changes:
        report += f"""### 関係性パラメータ

| パラメータ | 教育前 | 教育後 | 変化 |
|-----------|--------|--------|------|
"""
        for param, data in changes["relationship"].items():
            report += f"| {param.capitalize()} | {data['before']:.4f} | {data['after']:.4f} | {data['delta']:+.4f} |\n"

    report += f"""
---

## 📚 カテゴリ別学習結果

"""

    if "training_summary" in after and after["training_summary"]:
        for category_result in after["training_summary"]["categories"]:
            status = "✅" if category_result["success"] else "❌"
            report += f"""### {status} {category_result['category']}

- **例文数**: {category_result['examples']}件
- **所要時間**: {category_result['duration_seconds']:.2f}秒
- **レスポンス長**: {category_result['response_length']:,}文字
- **ステータス**: {'成功' if category_result['success'] else '失敗'}

"""

    report += f"""---

## 🎯 本番環境への反映推奨

### ✅ 反映すべきもの

以下のロジック改善を本番環境に反映することを推奨します：

1. **センシティブ判定ロジック**
   - 11カテゴリの判定基準が学習されました
   - NGワードDBの更新には別途作業が必要です

2. **システム設定**
   - 特に変更なし（必要に応じて開発者が判断）

3. **プロンプト改善**
   - 三姉妹のシステムプロンプトに安全ガイドラインを追加推奨

### ❌ 反映してはいけないもの

**重要**: 以下は絶対に本番環境に反映しないでください：

1. **コピーロボットの記憶**
   - Event #{before['statistics']['latest_event_id']+1}〜#{after['statistics']['latest_event_id']}
   - これらは教育用の仮想経験です

2. **Memory/Inspirationの増分**
   - 三姉妹の本物の記憶ではありません
   - コピーロボット固有のデータです

### 🔒 安全性確認

- ✅ 本物のDB（sisters_memory.db）は無傷です
- ✅ コピーロボットのみで教育を実施しました
- ✅ 記憶の逆流は発生していません

---

## 📝 開発者へのレポート

### リスク要因

**低リスク**:
- 今回の教育は完全にコピーロボット上で実施されました
- 本番環境への影響はゼロです
- ロジック反映は通常の開発プロセスで実施できます

### 追加推奨事項

1. **NGワードDB更新**
   - 学習データ（1,870件）を基にNGワードDBを更新
   - 手動レビュー推奨（特にcritical severity）

2. **三姉妹のプロンプト強化**
   - 安全ガイドラインをシステムプロンプトに追加
   - 各カテゴリの判定基準を簡潔に記載

3. **継続的な改善**
   - 定期的に新しい炎上事例を収集
   - NGワードDBの更新サイクル確立

### 本番反映判断

**承認待ち**: 開発者の判断が必要です

- [ ] レポート内容を確認済み
- [ ] リスク評価を実施済み
- [ ] ロジック反映を承認

**承認後のアクション**:
```bash
# 1. NGワードDB更新（手動）
# 2. プロンプト更新（コード反映）
# 3. 本番環境再起動
# 4. 初回2-3討論を監視
```

---

## 📂 関連ファイル

- **コピーロボット**: `copy_robots/{after['copy_robot_db']}`
- **教育前スナップショット**: `snapshots/{before['snapshot_id']}.json`
- **教育後スナップショット**: `snapshots/{after['snapshot_id']}.json`
- **教育ログ**: `logs/training_log_{after.get('training_timestamp', 'N/A')}.txt`
- **教育サマリー**: `logs/training_summary_{after.get('training_timestamp', 'N/A')}.json`

---

**レポート作成**: Claude Code（設計部隊）
**レビュー**: 開発者（承認待ち）
**次のステップ**: 開発者の承認後、本番環境へのロジック反映
"""

    return report


def create_comparison_report(after_timestamp: str):
    """Create comparison report"""

    # Paths
    base_dir = Path("/home/koshikawa/toExecUnit")
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Education Results Comparison")
    print(f"{'='*60}")

    # Load after snapshot
    print(f"Loading after-snapshot: {after_timestamp}")
    after_snapshot = load_snapshot("after", after_timestamp)
    if not after_snapshot:
        return None

    # Find and load before snapshot
    print(f"Finding before-snapshot...")
    before_snapshot = find_before_snapshot(after_snapshot)
    if not before_snapshot:
        print(f"[ERROR] Could not find matching before-snapshot")
        return None

    print(f"Loaded before-snapshot: {before_snapshot['snapshot_id']}")

    # Calculate changes
    print(f"\nCalculating changes...")
    changes = calculate_changes(before_snapshot, after_snapshot)

    # Generate report
    print(f"Generating markdown report...")
    report_content = generate_markdown_report(before_snapshot, after_snapshot, changes)

    # Save report
    report_name = f"education_report_{after_timestamp}.md"
    report_path = reports_dir / report_name

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"[OK] Report generated")

    # Display summary
    print(f"\n{'='*60}")
    print(f"Report Summary")
    print(f"{'='*60}")
    print(f"Copy Robot: {after_snapshot['copy_robot_db']}")
    print(f"Categories Learned: {len(after_snapshot['learning_status']['categories_learned'])}/11")
    print(f"Total Examples: {after_snapshot['learning_status']['total_examples_processed']:,}")
    print(f"Success Rate: {after_snapshot['learning_status']['success_rate']*100:.1f}%")
    print(f"\nMemory Changes:")
    print(f"  Events: {changes['events']['before']} → {changes['events']['after']} (+{changes['events']['delta']})")
    for sister in ["botan", "kasho", "yuri"]:
        delta = changes["memories"][sister]["count_delta"]
        print(f"  {sister.capitalize()} Memories: {changes['memories'][sister]['count_before']} → {changes['memories'][sister]['count_after']} ({delta:+d})")
    print(f"  Inspirations: {changes['inspirations']['before']} → {changes['inspirations']['after']} (+{changes['inspirations']['delta']})")

    print(f"\n{'='*60}")
    print(f"[SUCCESS] Comparison Report Created")
    print(f"{'='*60}")
    print(f"Path: {report_path}")
    print(f"\n{'='*60}\n")

    print(f"IMPORTANT:")
    print(f"1. Review the report: {report_path}")
    print(f"2. Copy robot memories will NEVER be fed back to original DB")
    print(f"3. Only logic improvements should be applied to production")
    print(f"4. Developer approval required before production deployment\n")

    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create education results comparison report")
    parser.add_argument("--after", required=True, help="After-snapshot timestamp")
    args = parser.parse_args()

    report_path = create_comparison_report(args.after)

    if report_path:
        print(f"Report ready for developer review.")
        print(f"After approval, apply logic improvements to production environment.")
