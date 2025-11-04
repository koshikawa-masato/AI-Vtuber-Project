#!/usr/bin/env python3
"""
Copy Robot Sensitive Content and Vocabulary Check CLI
Created: 2025-10-27
Purpose: Check Copy Robot DB for sensitive content and vocabulary usage
"""

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.copy_robot_checker import CopyRobotChecker


class CopyRobotCheckCLI:
    """
    CLI for Copy Robot Checker
    """

    def __init__(self):
        self.console = Console()

    def run(self, copy_robot_db: str, mode: str = 'all'):
        """
        Run check

        Args:
            copy_robot_db: Path to COPY_ROBOT_YYYYMMDD_HHMMSS.db
            mode: 'sensitive', 'vocabulary', or 'all'
        """
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]Copy Robot Sensitive Content & Vocabulary Check[/bold cyan]",
            border_style="cyan"
        ))
        self.console.print()

        # Initialize checker
        checker = CopyRobotChecker(copy_robot_db)

        if mode in ['sensitive', 'all']:
            self._check_sensitive_content(checker)

        if mode in ['vocabulary', 'all']:
            self._check_vocabulary_usage(checker)

    def _check_sensitive_content(self, checker: CopyRobotChecker):
        """
        Check sensitive content

        Args:
            checker: CopyRobotChecker instance
        """
        self.console.print("[bold yellow]1. Sensitive Content Scan[/bold yellow]")
        self.console.print()

        with self.console.status("[bold green]Scanning Copy Robot DB..."):
            results = checker.scan_copy_robot()

        # Statistics
        stats = results['statistics']
        self._display_statistics(stats)

        # NG Word Summary
        if results['ng_word_summary']:
            self._display_ng_word_summary(results['ng_word_summary'])
        else:
            self.console.print("[bold green]✓ No sensitive content detected![/bold green]")
            self.console.print()

        # Detailed results
        if results['events']:
            self._display_event_detections(results['events'])

        for character in ['botan', 'kasho', 'yuri']:
            if results['memories'][character]:
                self._display_memory_detections(character, results['memories'][character])

    def _display_statistics(self, stats: dict):
        """
        Display scan statistics

        Args:
            stats: Statistics dict
        """
        table = Table(title="Scan Statistics", box=box.ROUNDED)
        table.add_column("Item", style="cyan")
        table.add_column("Count", style="magenta", justify="right")

        table.add_row("Events scanned", str(stats['events_scanned']))
        table.add_row("Memories scanned", str(stats['memories_scanned']))
        table.add_row("Total text items", str(stats['total_text_items']))
        table.add_row(
            "Sensitive detected",
            f"[{'red' if stats['sensitive_detected'] > 0 else 'green'}]{stats['sensitive_detected']}[/]"
        )

        self.console.print(table)
        self.console.print()

    def _display_ng_word_summary(self, ng_word_summary: dict):
        """
        Display NG word summary

        Args:
            ng_word_summary: NG word count dict
        """
        table = Table(title="NG Words Found", box=box.ROUNDED)
        table.add_column("NG Word", style="red")
        table.add_column("Count", style="yellow", justify="right")

        sorted_words = sorted(ng_word_summary.items(), key=lambda x: x[1], reverse=True)
        for word, count in sorted_words:
            table.add_row(word, str(count))

        self.console.print(table)
        self.console.print()

    def _display_event_detections(self, events: list):
        """
        Display event detections

        Args:
            events: List of events with detections
        """
        self.console.print(f"[bold red]⚠ Events with sensitive content: {len(events)}[/bold red]")
        self.console.print()

        for event in events[:10]:  # Show first 10
            self.console.print(f"[bold]Event #{event['event_number']}: {event['event_name']}[/bold]")
            self.console.print(f"  Date: {event['event_date']}")

            for detection in event['detections']:
                self.console.print(f"  Field: [cyan]{detection['field']}[/cyan]")
                self.console.print(f"  Text: {detection['text']}")
                self.console.print(f"  Action: [red]{detection['action'].upper()}[/red]")
                self.console.print(f"  Severity: {detection['max_severity']}/10")

                for ng in detection['detected_words']:
                    self.console.print(f"    - NG: [red]{ng['word']}[/red] ({ng['category']})")

            self.console.print()

        if len(events) > 10:
            self.console.print(f"... and {len(events) - 10} more events")
            self.console.print()

    def _display_memory_detections(self, character: str, memories: list):
        """
        Display memory detections

        Args:
            character: Character name
            memories: List of memories with detections
        """
        self.console.print(f"[bold red]⚠ {character.upper()} memories with sensitive content: {len(memories)}[/bold red]")
        self.console.print()

        for memory in memories[:5]:  # Show first 5
            self.console.print(f"[bold]Memory #{memory['memory_id']} ({memory['memory_date']})[/bold]")

            for detection in memory['detections']:
                self.console.print(f"  Field: [cyan]{detection['field']}[/cyan]")
                self.console.print(f"  Text: {detection['text']}")
                self.console.print(f"  Action: [red]{detection['action'].upper()}[/red]")

                for ng in detection['detected_words']:
                    self.console.print(f"    - NG: [red]{ng['word']}[/red] ({ng['category']})")

            self.console.print()

        if len(memories) > 5:
            self.console.print(f"... and {len(memories) - 5} more memories")
            self.console.print()

    def _check_vocabulary_usage(self, checker: CopyRobotChecker):
        """
        Check vocabulary usage

        Args:
            checker: CopyRobotChecker instance
        """
        self.console.print("[bold yellow]2. Vocabulary Usage Analysis[/bold yellow]")
        self.console.print()

        with self.console.status("[bold green]Analyzing vocabulary..."):
            vocab_analysis = checker.analyze_vocabulary_usage()

        for character in ['botan', 'kasho', 'yuri']:
            self._display_character_vocabulary(character, vocab_analysis[character])

    def _display_character_vocabulary(self, character: str, analysis: dict):
        """
        Display character vocabulary analysis

        Args:
            character: Character name
            analysis: Vocabulary analysis dict
        """
        self.console.print(f"[bold cyan]{character.upper()} Vocabulary[/bold cyan]")

        # Summary
        learned = analysis['learned_words']
        used = analysis['used_in_robot']
        usage_rate = (used / learned * 100) if learned > 0 else 0

        summary_table = Table(box=box.SIMPLE)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta", justify="right")

        summary_table.add_row("Learned words", str(learned))
        summary_table.add_row("Used in Copy Robot", str(used))
        summary_table.add_row("Usage rate", f"{usage_rate:.1f}%")

        self.console.print(summary_table)

        # Usage details
        if analysis['usage_details']:
            self.console.print()
            usage_table = Table(title=f"Top Used Words", box=box.ROUNDED)
            usage_table.add_column("Word", style="yellow")
            usage_table.add_column("Meaning", style="white")
            usage_table.add_column("Usage", style="green", justify="right")

            for detail in analysis['usage_details'][:10]:  # Top 10
                usage_table.add_row(
                    detail['word'],
                    detail['meaning'] or '(no meaning)',
                    str(detail['usage_count'])
                )

            self.console.print(usage_table)

        self.console.print()


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(
        description="Copy Robot Sensitive Content and Vocabulary Check"
    )
    parser.add_argument(
        'copy_robot_db',
        help='Path to COPY_ROBOT_YYYYMMDD_HHMMSS.db'
    )
    parser.add_argument(
        '--mode',
        choices=['sensitive', 'vocabulary', 'all'],
        default='all',
        help='Check mode (default: all)'
    )

    args = parser.parse_args()

    # Verify file exists
    if not Path(args.copy_robot_db).exists():
        print(f"[ERROR] Copy Robot DB not found: {args.copy_robot_db}")
        sys.exit(1)

    # Run check
    cli = CopyRobotCheckCLI()
    cli.run(args.copy_robot_db, args.mode)


if __name__ == "__main__":
    main()
