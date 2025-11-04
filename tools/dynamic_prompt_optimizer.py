#!/usr/bin/env python3
"""
Dynamic Prompt Optimization System
Self-iterative learning for automatic prompt improvement

Phase 1: Baseline measurement (10 iterations)
Phase 2: Dynamic optimization + re-test (10 iterations)
Phase 3: Pattern variation test (10 iterations if improved)
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import statistics

class DynamicPromptOptimizer:
    def __init__(self, model: str, base_test_cases: str, iterations: int = 10):
        self.model = model
        self.base_test_cases = base_test_cases
        self.iterations = iterations
        self.results_dir = Path("dynamic_optimization_results")
        self.results_dir.mkdir(exist_ok=True)

        # Load base test cases
        with open(base_test_cases, 'r', encoding='utf-8') as f:
            self.base_cases = json.load(f)

    def run_benchmark(self, test_cases_file: str) -> Dict:
        """Run benchmark and return results"""
        cmd = [
            "python3", "benchmark_runner.py",
            "--model", self.model,
            "--test-cases", test_cases_file
        ]

        print(f"[INFO] Running benchmark: {test_cases_file}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[ERROR] Benchmark failed: {result.stderr}")
            return None

        # Find latest result file
        # Model name may contain colons, replace with underscores for filename
        model_safe = self.model.replace(':', '_')
        result_files = sorted(Path(".").glob(f"benchmark_results_{model_safe}*.json"))
        if not result_files:
            print(f"[ERROR] No result file found matching pattern: benchmark_results_{model_safe}*.json")
            return None

        latest_result = result_files[-1]
        with open(latest_result, 'r', encoding='utf-8') as f:
            return json.load(f)

    def phase1_baseline(self) -> Tuple[List[Dict], Dict]:
        """Phase 1: Run baseline measurement 10 times"""
        print("\n" + "="*70)
        print("PHASE 1: Baseline Measurement (10 iterations)")
        print("="*70)
        print(f"Model: {self.model}")
        print(f"Test cases: {self.base_test_cases}")
        print(f"Iterations: {self.iterations}")
        print()

        results = []
        scores = []

        for i in range(self.iterations):
            print(f"\n[{i+1}/{self.iterations}] Running baseline iteration {i+1}...")
            result = self.run_benchmark(self.base_test_cases)

            if result:
                # Calculate total score
                total_score = 0
                max_score = 0
                for test_result in result['results']:
                    total_score += test_result['evaluation']['score']
                    max_score += test_result['evaluation']['max_score']

                percentage = (total_score / max_score * 100) if max_score > 0 else 0
                scores.append(percentage)
                results.append(result)

                print(f"[RESULT] Iteration {i+1}: {percentage:.1f}% ({total_score}/{max_score})")
            else:
                print(f"[ERROR] Iteration {i+1} failed")

        # Calculate statistics
        stats = {
            "mean": statistics.mean(scores),
            "median": statistics.median(scores),
            "stdev": statistics.stdev(scores) if len(scores) > 1 else 0,
            "min": min(scores),
            "max": max(scores),
            "scores": scores
        }

        print("\n" + "-"*70)
        print("PHASE 1 STATISTICS:")
        print("-"*70)
        print(f"Mean:   {stats['mean']:.2f}%")
        print(f"Median: {stats['median']:.2f}%")
        print(f"Stdev:  {stats['stdev']:.2f}%")
        print(f"Range:  {stats['min']:.2f}% - {stats['max']:.2f}%")
        print("-"*70)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"phase1_baseline_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "phase": "baseline",
                "model": self.model,
                "iterations": self.iterations,
                "statistics": stats,
                "detailed_results": results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVED] Phase 1 results: {output_file}")

        return results, stats

    def analyze_failures(self, results: List[Dict]) -> Dict:
        """Analyze failure patterns from baseline results"""
        print("\n" + "="*70)
        print("ANALYZING FAILURE PATTERNS")
        print("="*70)

        # Aggregate failure patterns
        failure_patterns = {
            "timeout_cases": [],
            "low_score_cases": [],
            "chinese_contamination": [],
            "wrong_endings": [],
            "character_inconsistency": []
        }

        # Analyze each test case across all iterations
        test_ids = set()
        for result in results:
            for test_result in result['results']:
                test_ids.add(test_result['test_id'])

        for test_id in test_ids:
            timeout_count = 0
            low_score_count = 0
            total_score = 0
            total_max = 0

            for result in results:
                for test_result in result['results']:
                    if test_result['test_id'] == test_id:
                        # Check timeout
                        if '[ERROR] Timeout' in test_result.get('response', ''):
                            timeout_count += 1

                        # Check score
                        score = test_result['evaluation']['score']
                        max_score = test_result['evaluation']['max_score']
                        total_score += score
                        total_max += max_score

                        if score / max_score < 0.5:
                            low_score_count += 1

                        # Check Chinese
                        response = test_result.get('response', '')
                        if any(ord(c) >= 0x4E00 and ord(c) <= 0x9FFF for c in response):
                            if test_id not in failure_patterns['chinese_contamination']:
                                failure_patterns['chinese_contamination'].append(test_id)

            # Record failure patterns
            if timeout_count > self.iterations / 2:
                failure_patterns['timeout_cases'].append({
                    "test_id": test_id,
                    "timeout_rate": timeout_count / self.iterations
                })

            if low_score_count > self.iterations / 2:
                avg_percentage = (total_score / total_max * 100) if total_max > 0 else 0
                failure_patterns['low_score_cases'].append({
                    "test_id": test_id,
                    "avg_score": avg_percentage,
                    "low_score_rate": low_score_count / self.iterations
                })

        print("\nFailure Summary:")
        print(f"  - Timeout cases: {len(failure_patterns['timeout_cases'])}")
        print(f"  - Low score cases: {len(failure_patterns['low_score_cases'])}")
        print(f"  - Chinese contamination: {len(failure_patterns['chinese_contamination'])}")

        return failure_patterns

    def generate_optimized_prompts(self, failure_patterns: Dict) -> str:
        """Generate optimized prompts based on failure analysis"""
        print("\n" + "="*70)
        print("GENERATING OPTIMIZED PROMPTS")
        print("="*70)

        # Load base test cases
        optimized_cases = json.loads(json.dumps(self.base_cases))

        # Apply optimizations based on failure patterns
        improvements = []

        # Optimization 1: Simplify prompts for timeout cases
        for failure in failure_patterns['timeout_cases']:
            test_id = failure['test_id']
            for case in optimized_cases['test_cases']:
                if case['id'] == test_id:
                    # Shorten system prompt
                    original_len = len(case['system_prompt'])
                    lines = case['system_prompt'].split('\n')
                    # Keep only essential parts (first 50%)
                    essential_lines = lines[:len(lines)//2]
                    case['system_prompt'] = '\n'.join(essential_lines)
                    new_len = len(case['system_prompt'])
                    improvements.append(f"Simplified {test_id}: {original_len} -> {new_len} chars")

        # Optimization 2: Add explicit language rules for Chinese contamination
        if failure_patterns['chinese_contamination']:
            for test_id in failure_patterns['chinese_contamination']:
                for case in optimized_cases['test_cases']:
                    if case['id'] == test_id:
                        if '日本語のみ' not in case['system_prompt']:
                            case['system_prompt'] += '\n\n【重要】日本語のみで回答してください。'
                            improvements.append(f"Added language rule to {test_id}")

        # Optimization 3: Add brevity emphasis for low score cases
        for failure in failure_patterns['low_score_cases']:
            test_id = failure['test_id']
            for case in optimized_cases['test_cases']:
                if case['id'] == test_id:
                    if '短く' not in case['system_prompt']:
                        case['system_prompt'] += '\n\n【重要】1-2文で簡潔に回答してください。'
                        improvements.append(f"Added brevity rule to {test_id}")

        print("\nOptimizations applied:")
        for imp in improvements:
            print(f"  - {imp}")

        # Save optimized test cases
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        optimized_file = f"test_cases_optimized_dynamic_{timestamp}.json"
        with open(optimized_file, 'w', encoding='utf-8') as f:
            json.dump(optimized_cases, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVED] Optimized test cases: {optimized_file}")

        return optimized_file

    def phase2_optimized(self, optimized_cases_file: str, baseline_stats: Dict) -> Tuple[List[Dict], Dict, bool]:
        """Phase 2: Run optimized prompts 10 times"""
        print("\n" + "="*70)
        print("PHASE 2: Optimized Prompt Test (10 iterations)")
        print("="*70)
        print(f"Optimized test cases: {optimized_cases_file}")
        print(f"Baseline mean: {baseline_stats['mean']:.2f}%")
        print()

        results = []
        scores = []

        for i in range(self.iterations):
            print(f"\n[{i+1}/{self.iterations}] Running optimized iteration {i+1}...")
            result = self.run_benchmark(optimized_cases_file)

            if result:
                total_score = 0
                max_score = 0
                for test_result in result['results']:
                    total_score += test_result['evaluation']['score']
                    max_score += test_result['evaluation']['max_score']

                percentage = (total_score / max_score * 100) if max_score > 0 else 0
                scores.append(percentage)
                results.append(result)

                delta = percentage - baseline_stats['mean']
                print(f"[RESULT] Iteration {i+1}: {percentage:.1f}% (Δ{delta:+.1f}%)")
            else:
                print(f"[ERROR] Iteration {i+1} failed")

        # Calculate statistics
        stats = {
            "mean": statistics.mean(scores),
            "median": statistics.median(scores),
            "stdev": statistics.stdev(scores) if len(scores) > 1 else 0,
            "min": min(scores),
            "max": max(scores),
            "scores": scores
        }

        # Compare with baseline
        improvement = stats['mean'] - baseline_stats['mean']
        improved = improvement > 0

        print("\n" + "-"*70)
        print("PHASE 2 STATISTICS:")
        print("-"*70)
        print(f"Mean:   {stats['mean']:.2f}%")
        print(f"Median: {stats['median']:.2f}%")
        print(f"Stdev:  {stats['stdev']:.2f}%")
        print(f"Range:  {stats['min']:.2f}% - {stats['max']:.2f}%")
        print("-"*70)
        print(f"IMPROVEMENT: {improvement:+.2f}%")
        print(f"STATUS: {'✅ IMPROVED' if improved else '❌ NO IMPROVEMENT'}")
        print("-"*70)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"phase2_optimized_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "phase": "optimized",
                "model": self.model,
                "iterations": self.iterations,
                "baseline_mean": baseline_stats['mean'],
                "improvement": improvement,
                "statistics": stats,
                "detailed_results": results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVED] Phase 2 results: {output_file}")

        return results, stats, improved

    def generate_variation_cases(self) -> str:
        """Generate variation test cases with different patterns"""
        print("\n" + "="*70)
        print("GENERATING VARIATION TEST CASES")
        print("="*70)

        # Create variation by modifying prompts
        variation_cases = json.loads(json.dumps(self.base_cases))

        variations = []
        for case in variation_cases['test_cases']:
            # Variation strategy: Rephrase prompts
            original_prompt = case['prompt']

            # Simple variation: Add context or rephrase
            if 'greeting' in case['category']:
                case['prompt'] = original_prompt + "！"
                variations.append(f"{case['id']}: Added emphasis")
            elif 'casual_talk' in case['category']:
                case['prompt'] = "ねえ、" + original_prompt
                variations.append(f"{case['id']}: Added casual prefix")
            elif 'reaction' in case['category']:
                case['prompt'] = original_prompt + "、どう思う？"
                variations.append(f"{case['id']}: Added question")

        print("\nVariations applied:")
        for var in variations[:5]:  # Show first 5
            print(f"  - {var}")
        if len(variations) > 5:
            print(f"  ... and {len(variations)-5} more")

        # Save variation test cases
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        variation_file = f"test_cases_variation_{timestamp}.json"
        with open(variation_file, 'w', encoding='utf-8') as f:
            json.dump(variation_cases, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVED] Variation test cases: {variation_file}")

        return variation_file

    def phase3_variation(self, variation_cases_file: str, optimized_stats: Dict, baseline_stats: Dict) -> Tuple[List[Dict], Dict]:
        """Phase 3: Run variation test 10 times"""
        print("\n" + "="*70)
        print("PHASE 3: Variation Pattern Test (10 iterations)")
        print("="*70)
        print(f"Variation test cases: {variation_cases_file}")
        print(f"Optimized mean: {optimized_stats['mean']:.2f}%")
        print(f"Baseline mean: {baseline_stats['mean']:.2f}%")
        print()

        results = []
        scores = []

        for i in range(self.iterations):
            print(f"\n[{i+1}/{self.iterations}] Running variation iteration {i+1}...")
            result = self.run_benchmark(variation_cases_file)

            if result:
                total_score = 0
                max_score = 0
                for test_result in result['results']:
                    total_score += test_result['evaluation']['score']
                    max_score += test_result['evaluation']['max_score']

                percentage = (total_score / max_score * 100) if max_score > 0 else 0
                scores.append(percentage)
                results.append(result)

                delta_baseline = percentage - baseline_stats['mean']
                delta_optimized = percentage - optimized_stats['mean']
                print(f"[RESULT] Iteration {i+1}: {percentage:.1f}% (Δbaseline:{delta_baseline:+.1f}%, Δopt:{delta_optimized:+.1f}%)")
            else:
                print(f"[ERROR] Iteration {i+1} failed")

        # Calculate statistics
        stats = {
            "mean": statistics.mean(scores),
            "median": statistics.median(scores),
            "stdev": statistics.stdev(scores) if len(scores) > 1 else 0,
            "min": min(scores),
            "max": max(scores),
            "scores": scores
        }

        print("\n" + "-"*70)
        print("PHASE 3 STATISTICS:")
        print("-"*70)
        print(f"Mean:   {stats['mean']:.2f}%")
        print(f"Median: {stats['median']:.2f}%")
        print(f"Stdev:  {stats['stdev']:.2f}%")
        print(f"Range:  {stats['min']:.2f}% - {stats['max']:.2f}%")
        print("-"*70)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"phase3_variation_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "phase": "variation",
                "model": self.model,
                "iterations": self.iterations,
                "baseline_mean": baseline_stats['mean'],
                "optimized_mean": optimized_stats['mean'],
                "statistics": stats,
                "detailed_results": results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVED] Phase 3 results: {output_file}")

        return results, stats

    def generate_final_report(self, baseline_stats: Dict, optimized_stats: Dict,
                            variation_stats: Dict, improved: bool):
        """Generate final comprehensive report"""
        print("\n" + "="*70)
        print("FINAL REPORT: Dynamic Prompt Optimization")
        print("="*70)

        report = {
            "experiment": "Dynamic Prompt Optimization",
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "iterations_per_phase": self.iterations,
            "results": {
                "phase1_baseline": {
                    "mean": baseline_stats['mean'],
                    "stdev": baseline_stats['stdev'],
                    "range": [baseline_stats['min'], baseline_stats['max']]
                },
                "phase2_optimized": {
                    "mean": optimized_stats['mean'],
                    "stdev": optimized_stats['stdev'],
                    "range": [optimized_stats['min'], optimized_stats['max']],
                    "improvement": optimized_stats['mean'] - baseline_stats['mean']
                }
            },
            "conclusion": {
                "improved": improved,
                "recommendation": ""
            }
        }

        if improved and variation_stats:
            report["results"]["phase3_variation"] = {
                "mean": variation_stats['mean'],
                "stdev": variation_stats['stdev'],
                "range": [variation_stats['min'], variation_stats['max']],
                "improvement_vs_baseline": variation_stats['mean'] - baseline_stats['mean'],
                "improvement_vs_optimized": variation_stats['mean'] - optimized_stats['mean']
            }

        # Generate recommendation
        if improved:
            if variation_stats and variation_stats['mean'] > optimized_stats['mean']:
                report['conclusion']['recommendation'] = "Variation prompts show further improvement. Adopt variation strategy."
            else:
                report['conclusion']['recommendation'] = "Optimized prompts show improvement. Adopt optimization strategy."
        else:
            report['conclusion']['recommendation'] = "No improvement detected. Baseline prompts are optimal for this model."

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"FINAL_REPORT_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # Print summary
        print("\nPhase 1 (Baseline):")
        print(f"  Mean: {baseline_stats['mean']:.2f}% ± {baseline_stats['stdev']:.2f}%")

        print("\nPhase 2 (Optimized):")
        print(f"  Mean: {optimized_stats['mean']:.2f}% ± {optimized_stats['stdev']:.2f}%")
        print(f"  Improvement: {optimized_stats['mean'] - baseline_stats['mean']:+.2f}%")

        if improved and variation_stats:
            print("\nPhase 3 (Variation):")
            print(f"  Mean: {variation_stats['mean']:.2f}% ± {variation_stats['stdev']:.2f}%")
            print(f"  Improvement vs baseline: {variation_stats['mean'] - baseline_stats['mean']:+.2f}%")
            print(f"  Improvement vs optimized: {variation_stats['mean'] - optimized_stats['mean']:+.2f}%")

        print("\n" + "="*70)
        print("CONCLUSION:")
        print("="*70)
        print(f"Status: {'✅ IMPROVEMENT DETECTED' if improved else '❌ NO IMPROVEMENT'}")
        print(f"Recommendation: {report['conclusion']['recommendation']}")
        print("="*70)

        print(f"\n[SAVED] Final report: {report_file}")

        return report

    def run_full_experiment(self):
        """Run complete 3-phase experiment"""
        print("\n" + "="*70)
        print("DYNAMIC PROMPT OPTIMIZATION EXPERIMENT")
        print("="*70)
        print(f"Model: {self.model}")
        print(f"Base test cases: {self.base_test_cases}")
        print(f"Iterations per phase: {self.iterations}")
        print("="*70)

        # Phase 1: Baseline
        baseline_results, baseline_stats = self.phase1_baseline()

        # Analyze failures
        failure_patterns = self.analyze_failures(baseline_results)

        # Generate optimized prompts
        optimized_file = self.generate_optimized_prompts(failure_patterns)

        # Phase 2: Optimized
        optimized_results, optimized_stats, improved = self.phase2_optimized(
            optimized_file, baseline_stats
        )

        # Phase 3: Variation (only if improved)
        variation_stats = None
        if improved:
            variation_file = self.generate_variation_cases()
            variation_results, variation_stats = self.phase3_variation(
                variation_file, optimized_stats, baseline_stats
            )
        else:
            print("\n[INFO] Phase 3 skipped (no improvement in Phase 2)")

        # Final report
        report = self.generate_final_report(
            baseline_stats, optimized_stats, variation_stats, improved
        )

        return report


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 dynamic_prompt_optimizer.py [--model MODEL] [--test-cases FILE] [--iterations N]")
        print()
        print("Default:")
        print("  --model qwen2.5:7b-instruct-q4_K_M")
        print("  --test-cases test_cases_botan_optimized.json")
        print("  --iterations 10")
        print()
        print("Example:")
        print("  python3 dynamic_prompt_optimizer.py --model qwen2.5:7b-instruct-q4_K_M --iterations 10")
        sys.exit(1)

    # Parse arguments
    model = "qwen2.5:7b-instruct-q4_K_M"
    test_cases = "test_cases_botan_optimized.json"
    iterations = 10

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--model' and i + 1 < len(sys.argv):
            model = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--test-cases' and i + 1 < len(sys.argv):
            test_cases = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--iterations' and i + 1 < len(sys.argv):
            iterations = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    # Run experiment
    optimizer = DynamicPromptOptimizer(model, test_cases, iterations)
    report = optimizer.run_full_experiment()

    print("\n[COMPLETE] Dynamic Prompt Optimization Experiment finished")


if __name__ == "__main__":
    main()
