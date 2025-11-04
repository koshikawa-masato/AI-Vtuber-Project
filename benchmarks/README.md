# LLM Provider Benchmarks

This directory contains benchmark results comparing different LLM providers for the AI VTuber project.

## 📊 Latest Benchmark (2025-11-04)

### LLM Provider Comparison

Comprehensive comparison of local (Ollama) and cloud (OpenAI, Gemini) LLM providers.

**Files:**
- [`llm_provider_comparison_20251104.txt`](./llm_provider_comparison_20251104.txt) - Full comparison report
- [`llm_provider_benchmark_20251104.txt`](./llm_provider_benchmark_20251104.txt) - Ollama detailed results

### Key Results

| Provider | Model | Avg Latency | Cost/Call | Success Rate |
|----------|-------|-------------|-----------|--------------|
| **Ollama (Local)** | qwen2.5:3b | **0.368s** | **$0.00** | 100% |
| Ollama (Local) | qwen2.5:7b | 0.817s | $0.00 | 100% |
| Ollama (Local) | qwen2.5:14b | 1.499s | $0.00 | 100% |
| OpenAI (Cloud) | gpt-4o-mini | 1.717s | $0.000015 | 100% |
| Gemini (Cloud) | gemini-2.5-flash | 1.692s | $0.000003 | 75% |

### Main Findings

1. **Speed Winner**: Ollama qwen2.5:3b (0.368s) - 4.7x faster than cloud providers
2. **Cost Winner**: Ollama (100% free) vs Gemini ($0.000003) vs OpenAI ($0.000015)
3. **Best Cloud Value**: Gemini is 80% cheaper than OpenAI
4. **Reliability**: Ollama and OpenAI 100%, Gemini 75% (Japanese safety filter issues)

### Recommended Architecture

```
Priority 1: Ollama qwen2.5:3b (Real-time, Free)
    ↓ Fallback
Priority 2: Gemini 2.5 Flash (Cloud backup, Ultra-low cost)
    ↓ Special cases
Priority 3: OpenAI gpt-4o-mini (Quality-critical only)
```

**Cost Savings**: 99% reduction (10k requests: $0.50 vs $150 with OpenAI-only)

## 🧪 Test Environment

- **Date**: 2025-11-04
- **OS**: WSL2 Linux
- **CPU**: AMD Ryzen 9 9950X
- **RAM**: 128GB DDR5-5600
- **GPU**: NVIDIA RTX 4060 Ti 16GB
- **Methodology**: 4 iterations per model (1st warm-up discarded, 2nd-4th measured)

## 📁 Other Benchmarks

### RAG Implementation Comparison (2025-11-04)

Comparison of LangChain vs custom RAG implementation:
- [`results_7b.txt`](./results_7b.txt) - qwen2.5:7b results
- [`results_14b.txt`](./results_14b.txt) - qwen2.5:14b results

### Character Model Benchmarks (2025-10-05)

Botan character personality model tests:
- `benchmark_results_elyza_botan_*.txt` - Various ELYZA model tests
- `benchmark_results_qwen2.5_14b_*.txt` - Qwen model tests

## 🔗 Related Articles

- [Qiita記事](https://qiita.com/koshikawa-masato) - Technical blog posts (Japanese)
- [Project Repository](https://github.com/koshikawa-masato/AI-Vtuber-Project)

## 📝 License

This benchmark data is part of the AI VTuber Project and is available under the same license as the main project.
