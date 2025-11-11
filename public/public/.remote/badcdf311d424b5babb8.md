---
title: RAG実装比較：カスタム実装 vs LangChain - 判断力を示す技術選定
tags:
  - Python
  - AI
  - rag
  - LangChain
  - ollama
private: false
updated_at: '2025-11-07T12:49:08+09:00'
id: badcdf311d424b5babb8
organization_url_name: null
slide: false
ignorePublish: false
---

## はじめに

転職活動中のエンジニアです。AI VTuberプロジェクト「牡丹」で、独自のRAG（Retrieval-Augmented Generation）システムを実装してきました。

しかし、求人を見ると「LangChain経験必須」という文言が目立ちます。

**疑問**: 既にRAGを実装できているのに、なぜLangChainが必要なのか？

**答え**: LangChainの価値は「技術」ではなく「社会的シグナル」にあります。

この記事では、カスタムRAGとLangChain RAGを**デュアル実装**で比較し、「フレームワークを理解した上で判断できる」技術力を示します。

## TL;DR（3行まとめ）

- ✅ カスタムRAGとLangChain RAGをデュアル実装で比較
- ✅ LangChainの価値は「技術優位性」より「業界標準への適応力」
- ✅ 「使える」ではなく「判断できる」が真の技術力

---

## 背景：転職市場とLangChainの関係

### 求人で見かける「LangChain経験必須」

AI系求人の多くが「LangChain経験」を必須条件としています。

**例**:
```
必須スキル:
- LangChain/LlamaIndexを用いたRAGシステム開発経験
- OpenAI API / Claude APIの実務経験
```

### 既にRAGは実装できている

私の「牡丹プロジェクト」では、独自のRAGシステムを実装済みです：

**特徴**:
- ✅ 記憶強化メカニズム（mentioned_countで語るほど鮮明に）
- ✅ 記憶の濃淡（importance × mentioned_countで重み付け）
- ✅ 主観的記憶（三姉妹で異なる視点）
- ✅ 5軸スコアリング（keyword, emotion, temporal, importance, personality）

技術的には十分ですが、**採用担当者に伝わるか?**という問題があります。

### LangChainの本質的価値

調査の結果、LangChainの価値は以下だと理解しました：

| 観点 | カスタム実装 | LangChain |
|------|-------------|-----------|
|**技術的優位性**| ⭕ 高い（牡丹専用最適化） | △ 汎用的 |
|**社会的シグナル**| ❌ 採用担当に伝わらない | ⭕ 「業界標準を理解」 |
|**コード量**| ❌ 多い（~450行） | ⭕ 少ない（~150行） |
|**カスタマイズ性**| ⭕ 完全自由 | △ フレームワークの制約 |

**結論**: LangChainは「資格」のようなもの。技術的優位性ではなく、**業界標準に適応できる**ことの証明。

---

## 戦略：デュアル実装による比較

### なぜデュアル実装か？

単に「LangChainを使いました」では不十分です。

**採用担当者が知りたいのは**:
- ❌ 「LangChainが使えます」（チュートリアルレベル）
- ✅ 「カスタムとLangChainの違いを理解し、適切に判断できます」（深い理解）

デュアル実装により、**判断力**を示します。

### 実装アプローチ

**1つのクラスに2つの実装を持たせる**:

```python
class MemoryRetrievalLogicDual:
    """
    Dual Memory Retrieval Logic

    Supports two implementations:
    1. Original (use_langchain=False): Custom scoring
    2. LangChain (use_langchain=True): VectorStore-based
    """

    def __init__(
        self,
        db_path: str = "/path/to/sisters_memory.db",
        character: str = "botan",
        use_langchain: bool = False  # Toggle implementation
    ):
        self.use_langchain = use_langchain

        if use_langchain:
            self._init_langchain()
        else:
            self._init_original()
```

**切り替え可能な設計**:
```python
def retrieve_relevant_memories(self, context: str, top_k: int = 5):
    if self.use_langchain:
        return self._retrieve_with_langchain(context, top_k)
    else:
        return self._retrieve_with_original(context, top_k)
```

---

## 実装詳細

### Original実装（カスタムRAG）

**5軸スコアリング**:

```python
def _calculate_relevance_score(self, memory: Memory, context: str, current_emotion: str) -> MemoryRelevanceScore:
    """
    Calculate weighted relevance score

    Weights:
    - Keyword: 30%
    - Emotional: 25%
    - Temporal: 15%
    - Importance: 15%
    - Personality: 15%
    """
    keyword_score = self._calculate_keyword_match(memory, context)
    emotional_score = self._calculate_emotional_similarity(memory, current_emotion)
    temporal_score = self._calculate_temporal_relevance(memory)
    importance_score = memory.memory_importance / 10.0
    personality_score = self._calculate_personality_affinity(memory, context)

    total_score = (
        keyword_score * 0.30 +
        emotional_score * 0.25 +
        temporal_score * 0.15 +
        importance_score * 0.15 +
        personality_score * 0.15
    )

    return MemoryRelevanceScore(
        memory=memory,
        total_score=total_score,
        keyword_match_score=keyword_score,
        emotional_similarity_score=emotional_score,
        temporal_relevance_score=temporal_score,
        importance_score=importance_score,
        personality_affinity_score=personality_score
    )
```

**特徴**:
- ✅ 牡丹専用の性格パラメータ（emotional, analytical, relationship）
- ✅ 時間的関連性（exponential decay: `exp(-days / 30)`）
- ✅ 記憶強化（mentioned_count）

**コード量**: 約450行

### LangChain実装

**VectorStore + Embeddings**:

```python
def _init_langchain(self):
    """Initialize LangChain VectorStore"""
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings
    from langchain_core.documents import Document

    # Ollama embeddings
    self.embeddings = OllamaEmbeddings(
        model="qwen2.5:3b",
        base_url="http://localhost:11434"
    )

    # ChromaDB VectorStore
    collection_name = f"{self.character}_memories"
    self.vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=self.embeddings,
        persist_directory=f"./{collection_name}_chroma"
    )

    # Populate if empty
    if self.vectorstore._collection.count() == 0:
        self._populate_vectorstore()

def _retrieve_with_langchain(self, context: str, top_k: int) -> List[MemoryRelevanceScore]:
    """Retrieve using LangChain VectorStore"""
    # Similarity search
    docs = self.vectorstore.similarity_search(context, k=top_k * 2)

    # Convert to MemoryRelevanceScore (with custom scoring)
    results = []
    for doc in docs:
        event_id = int(doc.metadata["event_id"])
        memory = self._load_memory_by_event_id(event_id)
        score = self._calculate_relevance_score(memory, context, None)
        results.append(score)

    # Re-rank with custom scoring
    results.sort(key=lambda x: x.total_score, reverse=True)
    return results[:top_k]
```

**特徴**:
- ✅ VectorStoreによる高速類似度検索
- ✅ 標準的なRAGパターン
- ✅ カスタムスコアリングも併用可能

**コード量**: 約150行（LangChain部分のみ）

---

## ベンチマーク結果

**実行環境**:
- CPU: AMD Ryzen 9 9950X
- メモリ: DDR5-5600 128GB
- LLM: Ollama qwen2.5 (3b / 7b / 14b - ローカル)
- データセット: 110メモリ（牡丹の記憶）

### モデルサイズ別スケーリング特性

3種類のモデルサイズでベンチマークを実施し、実装方式のスケーリング特性を検証：

**📊 モデルサイズ別Query速度**:

| モデルサイズ | Original実装 | LangChain実装 | 速度差 |
|------------|-------------|--------------|--------|
|**qwen2.5:3b**(2GB) | 0.0011 s/query | 0.0616 s/query |**53倍速い**|
|**qwen2.5:7b**(5GB) | 0.0011 s/query | 0.0718 s/query |**62倍速い**|
|**qwen2.5:14b**(9GB) | 0.0011 s/query | 0.0949 s/query |**85倍速い**|

**重要な発見**：
- ✅**Original実装**：モデルサイズに依存しない一定速度（0.0011s）
- ⚠️**LangChain実装**：モデルサイズに比例して遅延増加（0.0616s → 0.0718s → 0.0949s）

**💾 メモリ使用量**:

| モデルサイズ | Original実装 | LangChain実装 | 差分 |
|------------|-------------|--------------|------|
|**qwen2.5:3b**| 78.5 MB | 137.4 MB | +75% |
|**qwen2.5:7b**| 93.4 MB | 140.2 MB | +50% |
|**qwen2.5:14b**| 93.5 MB | 146.8 MB | +57% |

**📝 その他の比較**:

| 項目 | Original実装 | LangChain実装 | 評価 |
|-----|-------------|--------------|-----|
|**コード行数**| ~450 lines | ~150 lines |**LangChainは67%削減**|
|**実装複雑度**| 高（カスタムロジック） | 低（標準API） | LangChainが有利 |
|**保守性**| 独自理解が必要 | 業界標準で共有しやすい | LangChainが有利 |

**🔍 詳細分析**:

1. **速度の差**: Originalは**53倍速い**
   - Original: 5軸スコアリング（SQL + Python計算）
   - LangChain: VectorStore初期化 + 埋め込み生成 + 類似度検索

2. **メモリ使用量**: LangChainは**75%多い**
   - ChromaDB のVectorStore が追加メモリを消費
   - 埋め込みベクトルのインメモリ保持

3. **コード量**: LangChainは**67%削減**
   - フレームワークがボイラープレートを抽象化
   - 保守性・可読性が向上

4. **検索品質**: 異なるアルゴリズムで異なる結果
   - Original: ドメイン特化スコアリング（感情・時間・重要度等）
   - LangChain: 汎用的なベクトル類似度検索

**💡 実践的な考察**:

**Originalが優れる点**:
- ✅ 低レイテンシー（リアルタイム対話向き）
- ✅ メモリ効率（省リソース環境）
- ✅ ドメイン特化最適化（牡丹の性格・記憶の特性）

**LangChainが優れる点**:
- ✅ 開発速度（3分の1のコード量）
- ✅ 保守性（標準フレームワーク）
- ✅ チーム開発（共通認識）

**🎯 モデルサイズ別検証の戦略的意義**:

このベンチマークで3種類のモデルサイズ（3b/7b/14b）を検証したのは、単なる性能比較以上の意味があります。

**検証の狙い**:
- ✅ モデルが大きくなるほど、独自実装の優位性が増大することを証明
- ✅ フレームワークに頼らず、要件を深く理解して最適化した成果を実証
- ✅ 「後付けの理由」ではなく、データに基づく技術判断であることを示す

**結果が示すこと**:
```
Original実装  : モデルサイズ非依存（常に0.0011s）
LangChain実装 : モデルサイズに比例して遅延（53倍 → 62倍 → 85倍）
```

この差は、**要件を深く理解し、最適解を選択する判断力**の証明になります。

単に「LangChainが使える」ではなく、「LangChainの価値を理解した上で、要件に応じて最適な技術を選べる」エンジニアであることを示せます。

---

## 判断基準：いつカスタム、いつLangChain？

### カスタム実装を選ぶべきケース

✅**ドメイン特化の最適化が必要**
- 例：牡丹の性格パラメータ、記憶強化メカニズム

✅**完全なコントロールが必要**
- 例：独自のスコアリングアルゴリズム

✅**学習目的**
- 例：RAGの仕組みを深く理解したい

✅**依存関係を最小化したい**
- 例：軽量なシステムを構築したい

### LangChain実装を選ぶべきケース

✅**チーム開発**
- 共通言語としてのフレームワーク

✅**迅速なプロトタイピング**
- コード量67%削減

✅**標準的なRAGで十分**
- 汎用的な検索システム

✅**採用市場での評価**
- 「LangChain経験」が求められる

---

## まとめ

### 本記事のポイント

1. **LangChainの価値は「社会的シグナル」**
   - 技術的優位性ではなく、業界標準への適応力を示す

2. **デュアル実装で「判断力」を示す**
   - 「使える」ではなく「判断できる」が真の技術力

3. **状況に応じた選択が重要**
   - カスタム vs LangChainは二者択一ではない
   - トレードオフを理解し、適切に判断する

### 転職活動への示唆

**採用担当者へのメッセージ**:
- ❌ 「LangChainしか使えません」
- ✅ 「カスタムRAGも実装でき、LangChainの適切な使い所も判断できます」

**エンジニアとしての成長**:
- フレームワークを「理解して使う」
- トレードオフを把握し、適切に判断する
- 技術的価値と社会的価値のバランスを取る

---

## リポジトリ

本記事のコードは以下で公開しています：

- **GitHub**: [AI-Vtuber-Project](https://github.com/koshikawa-masato/AI-Vtuber-Project)
- **ブランチ**: `main`
- **ファイル**:
  - デュアル実装: `src/core/memory_retrieval_logic_dual.py`
  - ベンチマーク: `benchmarks/compare_rag_implementations.py`

---

## 参考資料

- [LangChain公式ドキュメント](https://python.langchain.com/)
- [ChromaDB公式ドキュメント](https://www.trychroma.com/)
- [Ollama公式サイト](https://ollama.com/)

---

**最終更新**: 2025-11-04
**著者**: koshikawa-masato
**プロジェクト**: 牡丹（Botan）AI VTuberプロジェクト
