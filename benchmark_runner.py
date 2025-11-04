#!/usr/bin/env python3
"""
Qwen Benchmark Runner
Compare qwen2.5:32b, qwen3:32b, qwen3:30b-a3b performance
Focus on Botan character quality and detailed response logging
"""

import json
import time
import subprocess
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple
import statistics

class BenchmarkRunner:
    def __init__(self, test_cases_file: str = "test_cases.json"):
        """Initialize benchmark runner"""
        with open(test_cases_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.test_cases = self.data['test_cases']
        self.results = {}
        self.baseline_model = None  # qwen2.5:32b as baseline
        self.baseline_avg_time = None  # For efficiency ratio calculation

    def check_ollama_installed(self) -> bool:
        """Check if Ollama is installed"""
        try:
            result = subprocess.run(['ollama', '--version'],
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def check_model_available(self, model_name: str) -> bool:
        """Check if model is available in Ollama"""
        try:
            result = subprocess.run(['ollama', 'list'],
                                  capture_output=True, text=True)
            return model_name in result.stdout
        except Exception as e:
            print(f"Error checking model: {e}")
            return False

    def pull_model(self, model_name: str) -> bool:
        """Pull model from Ollama library"""
        print(f"\n[INFO] Pulling model: {model_name}")
        try:
            result = subprocess.run(['ollama', 'pull', model_name],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[SUCCESS] Model {model_name} pulled successfully")
                return True
            else:
                print(f"[ERROR] Failed to pull model: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ERROR] Exception while pulling model: {e}")
            return False

    def run_inference(self, model_name: str, prompt: str,
                     system_prompt: str = "") -> Tuple[str, float, float, int]:
        """
        Run inference on Ollama model
        Returns: (response, first_token_time, total_time, token_count)
        """
        # Prepare the request
        request_data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }

        if system_prompt:
            request_data["system"] = system_prompt

        # Measure time
        start_time = time.time()

        try:
            # Run ollama via subprocess
            process = subprocess.Popen(
                ['ollama', 'run', model_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

            stdout, stderr = process.communicate(input=full_prompt, timeout=60)

            end_time = time.time()
            total_time = end_time - start_time

            # Estimate first token time (rough approximation)
            first_token_time = total_time * 0.1  # Assume 10% for first token

            # Count tokens (rough approximation: 1 token ≈ 4 characters)
            token_count = len(stdout) // 4

            return stdout.strip(), first_token_time, total_time, token_count

        except subprocess.TimeoutExpired:
            process.kill()
            return "[ERROR] Timeout", 60.0, 60.0, 0
        except Exception as e:
            return f"[ERROR] {str(e)}", 0.0, 0.0, 0

    def evaluate_response(self, test_case: Dict, response: str) -> Dict:
        """Evaluate response against test case criteria"""
        score = 0
        max_score = test_case['max_score']
        details = []

        # Check for expected keywords
        if 'expected_keywords' in test_case and len(test_case['expected_keywords']) > 0:
            found_keywords = []
            for keyword in test_case['expected_keywords']:
                if keyword in response:
                    found_keywords.append(keyword)

            keyword_score = (len(found_keywords) / len(test_case['expected_keywords'])) * (max_score * 0.5)
            score += keyword_score
            details.append(f"Keywords: {len(found_keywords)}/{len(test_case['expected_keywords'])}")

        # Check for expected answer
        if 'expected_answer' in test_case:
            if test_case['expected_answer'] in response:
                score += max_score * 0.3
                details.append("Correct answer found")
            else:
                details.append("Correct answer NOT found")

        # Response length check (not empty, not too short)
        if len(response) > 10:
            score += max_score * 0.2
            details.append("Response length OK")
        else:
            details.append("Response too short")

        # Cap score at max_score
        score = min(score, max_score)

        return {
            'score': score,
            'max_score': max_score,
            'details': details
        }

    def run_test_case(self, model_name: str, test_case: Dict) -> Dict:
        """Run a single test case"""
        test_name = test_case.get('name', test_case['id'])
        print(f"  - Running test: {test_name}")

        prompt = test_case['prompt']
        system_prompt = test_case.get('system_prompt', '')

        # Add context if exists
        if 'context' in test_case:
            full_prompt = "\n".join(test_case['context']) + "\n\n" + prompt
        else:
            full_prompt = prompt

        # Run inference
        response, first_token_time, total_time, token_count = self.run_inference(
            model_name, full_prompt, system_prompt
        )

        # Evaluate response
        evaluation = self.evaluate_response(test_case, response)

        # Performance metrics
        tokens_per_second = token_count / total_time if total_time > 0 else 0

        return {
            'test_id': test_case['id'],
            'category': test_case['category'],
            'name': test_name,
            'prompt': prompt,
            'system_prompt': system_prompt,
            'response': response,
            'evaluation': evaluation,
            'performance': {
                'first_token_time': first_token_time,
                'total_time': total_time,
                'token_count': token_count,
                'tokens_per_second': tokens_per_second
            }
        }

    def run_benchmark(self, model_name: str) -> Dict:
        """Run all test cases for a model"""
        print(f"\n{'='*60}")
        print(f"Running benchmark for: {model_name}")
        print(f"{'='*60}")

        # Check if model is available
        if not self.check_model_available(model_name):
            print(f"[WARN] Model {model_name} not found. Attempting to pull...")
            if not self.pull_model(model_name):
                print(f"[ERROR] Failed to pull model {model_name}. Skipping.")
                return None

        results = []
        category_scores = {}

        for test_case in self.test_cases:
            result = self.run_test_case(model_name, test_case)
            results.append(result)

            # Aggregate scores by category
            category = result['category']
            if category not in category_scores:
                category_scores[category] = {'score': 0, 'max_score': 0}

            category_scores[category]['score'] += result['evaluation']['score']
            category_scores[category]['max_score'] += result['evaluation']['max_score']

        # Calculate total score
        total_score = sum(r['evaluation']['score'] for r in results)
        total_max_score = sum(r['evaluation']['max_score'] for r in results)

        # Calculate average performance
        all_first_token_times = [r['performance']['first_token_time'] for r in results]
        all_total_times = [r['performance']['total_time'] for r in results]
        all_tokens_per_second = [r['performance']['tokens_per_second'] for r in results if r['performance']['tokens_per_second'] > 0]

        avg_performance = {
            'avg_first_token_time': statistics.mean(all_first_token_times),
            'avg_total_time': statistics.mean(all_total_times),
            'avg_tokens_per_second': statistics.mean(all_tokens_per_second) if all_tokens_per_second else 0
        }

        # Set baseline if this is qwen2.5:32b or first model
        if self.baseline_model is None or model_name == 'qwen2.5:32b':
            self.baseline_model = model_name
            self.baseline_avg_time = avg_performance['avg_total_time']
            efficiency_ratio = 1.0  # Baseline is 1.0x
        else:
            # Calculate efficiency ratio (how many times faster than baseline)
            if self.baseline_avg_time and self.baseline_avg_time > 0:
                efficiency_ratio = self.baseline_avg_time / avg_performance['avg_total_time']
            else:
                efficiency_ratio = 1.0

        avg_performance['efficiency_ratio'] = efficiency_ratio
        avg_performance['baseline_model'] = self.baseline_model

        return {
            'model': model_name,
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'category_scores': category_scores,
            'total_score': total_score,
            'total_max_score': total_max_score,
            'percentage': (total_score / total_max_score * 100) if total_max_score > 0 else 0,
            'avg_performance': avg_performance
        }

    def save_results(self, model_results: Dict, filename: str = None):
        """Save benchmark results to JSON file"""
        if filename is None:
            model_name = model_results['model'].replace(':', '_').replace('/', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"benchmark_results_{model_name}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(model_results, f, ensure_ascii=False, indent=2)

        print(f"\n[INFO] Results saved to: {filename}")

        # Also save detailed response log
        log_filename = filename.replace('.json', '_responses.txt')
        self.save_response_log(model_results, log_filename)
        print(f"[INFO] Response log saved to: {log_filename}")

    def save_response_log(self, model_results: Dict, filename: str):
        """Save detailed response log in readable format"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"DETAILED RESPONSE LOG: {model_results['model']}\n")
            f.write(f"Timestamp: {model_results['timestamp']}\n")
            f.write("="*80 + "\n\n")

            for result in model_results['results']:
                f.write("-"*80 + "\n")
                f.write(f"[Test ID] {result['test_id']}\n")
                f.write(f"[Category] {result['category']}\n")
                f.write(f"[Name] {result.get('name', 'N/A')}\n")
                f.write(f"[Prompt] {result['prompt']}\n")
                f.write("-"*80 + "\n")
                f.write(f"[Response]\n{result['response']}\n")
                f.write("-"*80 + "\n")
                f.write(f"[Score] {result['evaluation']['score']:.2f}/{result['evaluation']['max_score']}\n")
                f.write(f"[Details] {', '.join(result['evaluation']['details'])}\n")
                f.write(f"[Performance] First Token: {result['performance']['first_token_time']:.3f}s, ")
                f.write(f"Total: {result['performance']['total_time']:.3f}s, ")
                f.write(f"Tokens/s: {result['performance']['tokens_per_second']:.2f}\n")
                f.write("\n\n")

    def print_summary(self, model_results: Dict):
        """Print benchmark summary"""
        print(f"\n{'='*60}")
        print(f"BENCHMARK SUMMARY: {model_results['model']}")
        print(f"{'='*60}")

        print(f"\nTotal Score: {model_results['total_score']:.2f} / {model_results['total_max_score']:.2f} ({model_results['percentage']:.1f}%)")

        print("\nCategory Scores:")
        for category, scores in model_results['category_scores'].items():
            percentage = (scores['score'] / scores['max_score'] * 100) if scores['max_score'] > 0 else 0
            print(f"  - {category}: {scores['score']:.2f} / {scores['max_score']:.2f} ({percentage:.1f}%)")

        print("\nAverage Performance:")
        perf = model_results['avg_performance']
        print(f"  - First Token Time: {perf['avg_first_token_time']:.3f}s")
        print(f"  - Total Time: {perf['avg_total_time']:.3f}s")
        print(f"  - Tokens/Second: {perf['avg_tokens_per_second']:.2f}")

        # CPU-based efficiency measurement
        if 'efficiency_ratio' in perf:
            print(f"\n⚡ CPU Efficiency:")
            print(f"  - Baseline: {perf['baseline_model']}")
            if perf['efficiency_ratio'] > 1.0:
                print(f"  - Efficiency Ratio: {perf['efficiency_ratio']:.2f}x FASTER")
            elif perf['efficiency_ratio'] < 1.0:
                print(f"  - Efficiency Ratio: {1/perf['efficiency_ratio']:.2f}x SLOWER")
            else:
                print(f"  - Efficiency Ratio: {perf['efficiency_ratio']:.2f}x (baseline)")

        # Verdict
        print("\nVerdict:")
        if model_results['percentage'] >= 80:
            print("  ✅ EXCELLENT - Immediate adoption recommended")
        elif model_results['percentage'] >= 70:
            print("  ✓ GOOD - Adoption recommended")
        elif model_results['percentage'] >= 60:
            print("  ○ ACCEPTABLE - Consider adoption with improvements")
        else:
            print("  ✗ NEEDS IMPROVEMENT - Not recommended at this time")

def main():
    """Main function"""
    print("="*60)
    print("Qwen Benchmark Runner - Botan Character Quality Test")
    print("="*60)

    # Parse command line arguments
    test_cases_file = "test_cases_botan.json"  # Default
    models = [
        'qwen2.5:7b-instruct-q4_K_M',  # Only test this model
    ]
    max_cases = None  # Option to limit number of test cases

    # Allow command line arguments
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--model' and i + 1 < len(sys.argv):
            models = [sys.argv[i + 1]]
            i += 2
        elif sys.argv[i] == '--test-cases' and i + 1 < len(sys.argv):
            test_cases_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--max-cases' and i + 1 < len(sys.argv):
            max_cases = int(sys.argv[i + 1])
            i += 2
        else:
            print(f"Usage: {sys.argv[0]} [--model MODEL_NAME] [--test-cases FILE] [--max-cases N]")
            print(f"Available models: qwen2.5:7b-instruct-q4_K_M, qwen3:8b-q4_K_M, qwen3:30b-a3b-q4_K_M")
            print(f"Example: {sys.argv[0]} --test-cases test_cases_botan_optimized.json --model qwen2.5:14b --max-cases 3")
            sys.exit(1)

    # Check if test cases file exists
    if not os.path.exists(test_cases_file):
        print(f"[ERROR] Test cases file not found: {test_cases_file}")
        sys.exit(1)

    # Initialize runner with specified test cases
    runner = BenchmarkRunner(test_cases_file)

    # Limit test cases if requested
    if max_cases:
        runner.test_cases = runner.test_cases[:max_cases]
        print(f"[INFO] Limiting to {max_cases} test cases")

    # Check Ollama installation
    if not runner.check_ollama_installed():
        print("[ERROR] Ollama is not installed or not in PATH")
        sys.exit(1)
    print(f"\n[INFO] Using test cases: {test_cases_file}")
    print(f"[INFO] Testing models: {', '.join(models)}\n")

    # Run benchmarks
    all_results = []
    for model in models:
        result = runner.run_benchmark(model)
        if result:
            all_results.append(result)
            runner.save_results(result)
            runner.print_summary(result)

    # Comparison summary
    if len(all_results) > 1:
        print(f"\n{'='*60}")
        print("COMPARISON SUMMARY")
        print(f"{'='*60}")

        print(f"\n{'Model':<20} {'Score':<15} {'Percentage':<12} {'Avg Time':<12} {'Efficiency':<12}")
        print("-"*80)
        for result in all_results:
            efficiency = result['avg_performance'].get('efficiency_ratio', 1.0)
            efficiency_str = f"{efficiency:.2f}x" if efficiency >= 1.0 else f"{1/efficiency:.2f}x↓"
            print(f"{result['model']:<20} "
                  f"{result['total_score']:.2f}/{result['total_max_score']:.2f}  "
                  f"{result['percentage']:.1f}%        "
                  f"{result['avg_performance']['avg_total_time']:.3f}s     "
                  f"{efficiency_str}")

        # Winner by quality
        best_quality = max(all_results, key=lambda x: x['percentage'])
        print(f"\n🏆 Best Quality: {best_quality['model']} ({best_quality['percentage']:.1f}%)")

        # Winner by efficiency
        best_efficiency = max(all_results, key=lambda x: x['avg_performance'].get('efficiency_ratio', 1.0))
        efficiency_val = best_efficiency['avg_performance'].get('efficiency_ratio', 1.0)
        print(f"⚡ Most Efficient: {best_efficiency['model']} ({efficiency_val:.2f}x)")

        # Overall winner (balanced score)
        # Score = quality_percentage * efficiency_ratio
        for result in all_results:
            result['_balanced_score'] = result['percentage'] * result['avg_performance'].get('efficiency_ratio', 1.0)

        best_overall = max(all_results, key=lambda x: x['_balanced_score'])
        print(f"🎯 Best Overall: {best_overall['model']} (balanced score: {best_overall['_balanced_score']:.1f})")

if __name__ == '__main__':
    main()
