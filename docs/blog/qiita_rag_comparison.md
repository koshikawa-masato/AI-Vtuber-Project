# RAG実装比較：カスタム実装 vs LangChain - 判断力を示す技術選定

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

技術的には十分ですが、**採用担当者に伝わるか？**という問題があります。

### LangChainの本質的価値

調査の結果、LangChainの価値は以下だと理解しました：

| 観点 | カスタム実装 | LangChain |
|------|-------------|-----------|
| **技術的優位性** | ⭕ 高い（牡丹専用最適化） | △ 汎用的 |
| **社会的シグナル** | ❌ 採用担当に伝わらない | ⭕ 「業界標準を理解」 |
| **コード量** | ❌ 多い（~450行） | ⭕ 少ない（~150行） |
| **カスタマイズ性** | ⭕ 完全自由 | △ フレームワークの制約 |

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
    from langchain_community.vectorstores import Chroma
    from langchain_ollama import OllamaEmbeddings
    from langchain_core.documents import Document

    # Ollama embeddings
    self.embeddings = OllamaEmbeddings(
        model="qwen2.5:32b",
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

## 比較ポイント

### 1. コード量の違い

| 実装 | コード量 | 理由 |
|------|---------|------|
| Original | ~450行 | カスタムロジック全て実装 |
| LangChain | ~150行 | フレームワークが大部分を担当 |

**削減率**: 約67%のコード削減

### 2. 保守性

**Original**:
- ❌ 全てのロジックを自前で保守
- ❌ バグ修正も自己責任
- ✅ 完全にコントロール可能

**LangChain**:
- ✅ フレームワークのバグ修正はコミュニティが担当
- ✅ 新機能が自動的に追加される
- ❌ フレームワークの変更に追従する必要

### 3. パフォーマンス（ベンチマーク結果）

> **注**: ベンチマーク実行中のため、完了後に追記予定

**測定項目**:
- Query速度（sec/query）
- メモリ使用量（MB）
- 検索品質（overlap ratio, top score）

---

## 技術的考察

### LangChainの「社会的価値」

LangChainの価値は技術的優位性ではなく、以下にあります：

#### 1. 共通言語としての価値

チーム開発では「共通理解」が重要です。

**カスタム実装の課題**:
```python
# これは何をしているのか？
score = (kw * 0.3 + em * 0.25 + tmp * 0.15 + imp * 0.15 + per * 0.15)
```
→ コードレビュー時に毎回説明が必要

**LangChain実装**:
```python
# 業界標準パターン
docs = vectorstore.similarity_search(context, k=5)
```
→ 説明不要。チームメンバー全員が理解

#### 2. 採用市場での「資格」

採用担当者（非エンジニア）にとって：
- ❌ 「独自RAGシステム実装」→ 評価が難しい
- ✅ 「LangChain経験」→ 明確な評価基準

これは技術力の問題ではなく、**採用プロセスの問題**です。

#### 3. チーム引き継ぎの容易さ

プロジェクト引き継ぎ時：

**カスタム実装**:
- 引き継ぎに1-2週間
- 独自ロジックの理解が必要
- ドキュメントが不十分だと破綻

**LangChain実装**:
- 引き継ぎに数日
- 公式ドキュメントで学習可能
- チーム内の知識共有が容易

### カスタム実装の価値

一方、カスタム実装にも明確な価値があります：

#### 1. ドメイン特化の最適化

**牡丹プロジェクトの例**:
- 性格パラメータ（emotional, analytical, relationship）
- 記憶強化メカニズム（mentioned_count）
- 主観的記憶（三姉妹で異なる視点）

これらは**汎用フレームワークでは実現困難**です。

#### 2. 完全なコントロール

**LangChainの制約例**:
- VectorStoreの選択肢が限定的
- スコアリングロジックのカスタマイズに制限
- フレームワークのバージョンアップに追従

**カスタム実装**:
- すべて自由に設計可能
- 独自のアルゴリズムを実装可能
- 依存関係を最小化

#### 3. 学習価値

カスタム実装により、RAGの本質を深く理解できます：
- Embedding生成の仕組み
- 類似度計算のアルゴリズム
- VectorStoreの内部構造

---

## 判断基準：いつカスタム、いつLangChain？

### カスタム実装を選ぶべきケース

✅ **ドメイン特化の最適化が必要**
- 例：牡丹の性格パラメータ、記憶強化メカニズム

✅ **完全なコントロールが必要**
- 例：独自のスコアリングアルゴリズム

✅ **学習目的**
- 例：RAGの仕組みを深く理解したい

✅ **依存関係を最小化したい**
- 例：軽量なシステムを構築したい

### LangChain実装を選ぶべきケース

✅ **チーム開発**
- 共通言語としてのフレームワーク

✅ **迅速なプロトタイピング**
- コード量67%削減

✅ **標準的なRAGで十分**
- 汎用的な検索システム

✅ **採用市場での評価**
- 「LangChain経験」が求められる

---

## 実装から学んだこと

### 1. 「判断力」の重要性

単に「LangChainが使える」ではなく、**いつ使うべきか判断できる**ことが重要。

デュアル実装により、以下を示せます：
- ✅ 両方の実装を理解している
- ✅ トレードオフを把握している
- ✅ 適切な選択ができる

### 2. 技術的価値 vs 社会的価値

技術選定には2つの軸があります：

| 軸 | 重視する場合 |
|----|-------------|
| **技術的価値** | ドメイン特化、パフォーマンス最適化 |
| **社会的価値** | チーム開発、採用市場、引き継ぎ |

**どちらが正しいかではなく、状況に応じて判断する**ことが重要。

### 3. フレームワークを「理解して使う」

フレームワークは便利ですが、**ブラックボックスとして使うべきではありません**。

カスタム実装の経験があることで：
- ✅ LangChainが何をしているか理解できる
- ✅ 問題が起きた時にデバッグできる
- ✅ 適切なカスタマイズができる

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
- **ブランチ**: `feature/langchain-comparison`
- **ファイル**:
  - デュアル実装: `src/core/memory_retrieval_logic_dual.py`
  - ベンチマーク: `benchmarks/compare_rag_implementations.py`

---

## 参考資料

- [LangChain公式ドキュメント](https://python.langchain.com/)
- [ChromaDB公式ドキュメント](https://www.trychroma.com/)
- [Ollama公式サイト](https://ollama.com/)

---

## 付録：ベンチマーク結果（実行中）

> **注**: 現在ベンチマーク実行中です。完了次第、結果を追記します。

**測定項目**:
- Query速度（average time per query）
- メモリ使用量（RSS in MB）
- 検索品質（overlap ratio, top scores）

**テストクエリ**:
1. VTuber配信の夢
2. 大阪旅行の思い出
3. 音楽制作の経験
4. ファッションについて
5. お姉ちゃんとの会話

---

**最終更新**: 2025-11-04
**著者**: koshikawa-masato
**プロジェクト**: 牡丹（Botan）AI VTuberプロジェクト
