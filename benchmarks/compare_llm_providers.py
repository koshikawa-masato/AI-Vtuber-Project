"""
LLM Provider Comparison Benchmark

Compares Ollama (local), OpenAI, and Gemini providers across:
- Speed (latency)
- Cost (USD per query)
- Quality (subjective evaluation)

Author: koshikawa-masato
Date: 2025-11-04
"""

import os
import sys
import time
import json
import statistics
from typing import List, Dict, Optional
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.llm_provider import BaseLLMProvider, LLMResponse
from src.core.llm_ollama import OllamaProvider
from src.core.llm_openai import OpenAIProvider
from src.core.llm_gemini import GeminiProvider


class LLMProviderBenchmark:
    """Benchmark for comparing LLM providers"""

    def __init__(self, iterations: int = 10):
        """
        Initialize benchmark

        Args:
            iterations: Number of iterations per test case (default: 10)
        """
        self.iterations = iterations
        self.providers: Dict[str, BaseLLMProvider] = {}

        # Initialize providers
        self._initialize_providers()

        # Test cases
        self.test_cases = [
            {
                "name": "simple",
                "prompt": "今日の天気は？",
                "system_prompt": "あなたは牡丹です。ギャル口調で話します。",
                "expected_tokens": 50
            },
            {
                "name": "medium",
                "prompt": "大阪で食べたい料理について教えて",
                "system_prompt": "あなたは牡丹です。ギャル口調で話します。",
                "expected_tokens": 200
            },
            {
                "name": "complex",
                "prompt": "Event #110の記憶（大阪の食べ物）について、どんな料理を食べたいと思ったか、どんな気持ちだったかを詳しく語って",
                "system_prompt": "あなたは牡丹です。ギャル口調で話します。大阪の食べ物について語るときは興奮気味になります。",
                "expected_tokens": 500
            }
        ]

    def _initialize_providers(self):
        """Initialize LLM providers"""
        print("Initializing providers...")

        # Ollama (always available - local)
        try:
            self.providers["ollama"] = OllamaProvider(model="qwen2.5:32b")
            print("  ✓ Ollama (qwen2.5:32b) - ready")
        except Exception as e:
            print(f"  ✗ Ollama initialization failed: {e}")

        # OpenAI (only if API key is set)
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.providers["openai"] = OpenAIProvider(model="gpt-4o-mini")
                print("  ✓ OpenAI (gpt-4o-mini) - ready")
            except Exception as e:
                print(f"  ✗ OpenAI initialization failed: {e}")
        else:
            print("  - OpenAI skipped (OPENAI_API_KEY not set)")

        # Gemini (only if API key is set)
        if os.getenv("GOOGLE_API_KEY"):
            try:
                self.providers["gemini"] = GeminiProvider(model="gemini-1.5-flash")
                print("  ✓ Gemini (gemini-1.5-flash) - ready")
            except Exception as e:
                print(f"  ✗ Gemini initialization failed: {e}")
        else:
            print("  - Gemini skipped (GOOGLE_API_KEY not set)")

        if not self.providers:
            raise RuntimeError("No providers available. Please set up at least one provider.")

    def run_benchmark(self) -> Dict:
        """
        Run benchmark for all providers

        Returns:
            Dictionary with benchmark results
        """
        results = {}
        total_queries = len(self.test_cases) * self.iterations * len(self.providers)
        current_query = 0

        print(f"\n{'='*60}")
        print(f"Starting benchmark: {total_queries} total queries")
        print(f"Providers: {', '.join(self.providers.keys())}")
        print(f"Test cases: {len(self.test_cases)}")
        print(f"Iterations per test: {self.iterations}")
        print(f"{'='*60}\n")

        for provider_name, provider in self.providers.items():
            print(f"\n{'='*60}")
            print(f"Benchmarking: {provider_name}")
            print(f"{'='*60}")

            provider_results = []

            for test_case in self.test_cases:
                print(f"\n  Test case: {test_case['name']} (expected ~{test_case['expected_tokens']} tokens)")
                case_results = []

                for i in range(self.iterations):
                    current_query += 1
                    progress = (current_query / total_queries) * 100
                    print(f"    [{current_query}/{total_queries}] ({progress:.1f}%) iteration {i+1}/{self.iterations}...", end=" ")

                    try:
                        response = provider.generate(
                            prompt=test_case["prompt"],
                            system_prompt=test_case["system_prompt"],
                            temperature=0.7,
                            max_tokens=2000
                        )

                        case_results.append({
                            "latency": response.latency,
                            "tokens": response.tokens_used,
                            "cost": response.cost_estimate,
                            "content": response.content,
                            "success": True,
                            "error": None
                        })

                        print(f"✓ ({response.latency:.2f}s, ${response.cost_estimate:.6f})")

                    except Exception as e:
                        case_results.append({
                            "latency": None,
                            "tokens": None,
                            "cost": None,
                            "content": None,
                            "success": False,
                            "error": str(e)
                        })
                        print(f"✗ Error: {e}")

                    # Rate limiting
                    if i < self.iterations - 1:
                        time.sleep(1)

                provider_results.append({
                    "test_case": test_case["name"],
                    "expected_tokens": test_case["expected_tokens"],
                    "results": case_results
                })

            results[provider_name] = provider_results

        return results

    def analyze_results(self, results: Dict) -> Dict:
        """
        Analyze benchmark results

        Args:
            results: Raw benchmark results

        Returns:
            Analysis summary
        """
        analysis = {}

        for provider_name, provider_results in results.items():
            provider_analysis = {
                "provider": provider_name,
                "test_cases": []
            }

            total_cost = 0.0
            total_latency = 0.0
            total_success = 0
            total_queries = 0

            for test_result in provider_results:
                case_name = test_result["test_case"]
                case_results = test_result["results"]

                # Filter successful results
                successful_results = [r for r in case_results if r["success"]]
                failed_count = len(case_results) - len(successful_results)

                if successful_results:
                    latencies = [r["latency"] for r in successful_results]
                    costs = [r["cost"] for r in successful_results if r["cost"] is not None]
                    tokens = [r["tokens"] for r in successful_results if r["tokens"] is not None]

                    case_analysis = {
                        "test_case": case_name,
                        "expected_tokens": test_result["expected_tokens"],
                        "success_rate": len(successful_results) / len(case_results),
                        "failed_count": failed_count,
                        "latency": {
                            "mean": statistics.mean(latencies),
                            "median": statistics.median(latencies),
                            "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
                            "min": min(latencies),
                            "max": max(latencies)
                        }
                    }

                    if costs:
                        case_analysis["cost"] = {
                            "mean": statistics.mean(costs),
                            "total": sum(costs)
                        }
                        total_cost += sum(costs)

                    if tokens:
                        case_analysis["tokens"] = {
                            "mean": statistics.mean(tokens),
                            "median": statistics.median(tokens)
                        }

                    total_latency += sum(latencies)
                    total_success += len(successful_results)
                else:
                    case_analysis = {
                        "test_case": case_name,
                        "success_rate": 0.0,
                        "failed_count": len(case_results),
                        "error": "All queries failed"
                    }

                total_queries += len(case_results)
                provider_analysis["test_cases"].append(case_analysis)

            # Overall statistics
            provider_analysis["overall"] = {
                "total_queries": total_queries,
                "total_success": total_success,
                "total_failed": total_queries - total_success,
                "success_rate": total_success / total_queries if total_queries > 0 else 0.0,
                "total_cost": total_cost,
                "avg_latency": total_latency / total_success if total_success > 0 else 0.0
            }

            analysis[provider_name] = provider_analysis

        return analysis

    def print_analysis(self, analysis: Dict):
        """Print analysis results in a readable format"""
        print(f"\n{'='*60}")
        print("BENCHMARK RESULTS ANALYSIS")
        print(f"{'='*60}\n")

        for provider_name, provider_analysis in analysis.items():
            print(f"\n{'─'*60}")
            print(f"Provider: {provider_name.upper()}")
            print(f"{'─'*60}")

            for test_case_analysis in provider_analysis["test_cases"]:
                case_name = test_case_analysis["test_case"]
                print(f"\n  Test: {case_name} (expected ~{test_case_analysis.get('expected_tokens', 'N/A')} tokens)")

                if test_case_analysis["success_rate"] > 0:
                    lat = test_case_analysis["latency"]
                    print(f"    Success rate: {test_case_analysis['success_rate']*100:.1f}%")
                    print(f"    Latency:")
                    print(f"      Mean:   {lat['mean']:.3f}s")
                    print(f"      Median: {lat['median']:.3f}s")
                    print(f"      StdDev: {lat['stdev']:.3f}s")
                    print(f"      Range:  {lat['min']:.3f}s - {lat['max']:.3f}s")

                    if "cost" in test_case_analysis:
                        cost = test_case_analysis["cost"]
                        print(f"    Cost:")
                        print(f"      Mean:  ${cost['mean']:.6f} per query")
                        print(f"      Total: ${cost['total']:.6f}")

                    if "tokens" in test_case_analysis:
                        tok = test_case_analysis["tokens"]
                        print(f"    Tokens:")
                        print(f"      Mean:   {tok['mean']:.0f} tokens")
                        print(f"      Median: {tok['median']:.0f} tokens")
                else:
                    print(f"    ✗ All queries failed: {test_case_analysis.get('error', 'Unknown error')}")

            # Overall statistics
            overall = provider_analysis["overall"]
            print(f"\n  Overall Statistics:")
            print(f"    Total queries: {overall['total_queries']}")
            print(f"    Success:       {overall['total_success']} ({overall['success_rate']*100:.1f}%)")
            print(f"    Failed:        {overall['total_failed']}")
            print(f"    Total cost:    ${overall['total_cost']:.6f}")
            print(f"    Avg latency:   {overall['avg_latency']:.3f}s")

        # Comparison summary
        print(f"\n{'='*60}")
        print("PROVIDER COMPARISON SUMMARY")
        print(f"{'='*60}\n")

        comparison_data = []
        for provider_name, provider_analysis in analysis.items():
            overall = provider_analysis["overall"]
            comparison_data.append({
                "provider": provider_name,
                "success_rate": overall["success_rate"],
                "avg_latency": overall["avg_latency"],
                "total_cost": overall["total_cost"]
            })

        # Sort by latency (fastest first)
        comparison_data.sort(key=lambda x: x["avg_latency"])

        print(f"{'Provider':<15} {'Success Rate':<15} {'Avg Latency':<15} {'Total Cost':<15}")
        print(f"{'-'*60}")
        for data in comparison_data:
            print(f"{data['provider']:<15} {data['success_rate']*100:>6.1f}%        {data['avg_latency']:>7.3f}s        ${data['total_cost']:>8.6f}")

    def save_results(self, results: Dict, analysis: Dict, filename: Optional[str] = None):
        """
        Save results to JSON file

        Args:
            results: Raw benchmark results
            analysis: Analysis results
            filename: Output filename (default: auto-generated with timestamp)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmarks/llm_providers_comparison_{timestamp}.json"

        output = {
            "timestamp": datetime.now().isoformat(),
            "iterations": self.iterations,
            "providers": list(self.providers.keys()),
            "test_cases": [tc["name"] for tc in self.test_cases],
            "raw_results": results,
            "analysis": analysis
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"Results saved to: {filename}")
        print(f"{'='*60}\n")


def main():
    """Main function"""
    print("""
╔══════════════════════════════════════════════════════════╗
║  LLM Provider Comparison Benchmark                       ║
║  Comparing: Ollama (local) / OpenAI / Gemini             ║
╚══════════════════════════════════════════════════════════╝
""")

    # Create benchmark
    benchmark = LLMProviderBenchmark(iterations=10)

    # Run benchmark
    print("Starting benchmark...\n")
    results = benchmark.run_benchmark()

    # Analyze results
    print("\n\nAnalyzing results...\n")
    analysis = benchmark.analyze_results(results)

    # Print analysis
    benchmark.print_analysis(analysis)

    # Save results
    benchmark.save_results(results, analysis)

    print("\n✓ Benchmark completed successfully!")


if __name__ == "__main__":
    main()
