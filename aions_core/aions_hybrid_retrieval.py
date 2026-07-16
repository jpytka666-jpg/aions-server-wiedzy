"""
AIONS Hybrid Retrieval System v1.0
===================================
Combines keyword search (BM25) + vector search + reranking
SAFE ADDITION - works alongside existing AIONS without modifications

Author: AIONS Development Team
Date: 2025-09-10
Status: PRODUCTION READY
"""

import re
import math
import json
import time
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from dataclasses import dataclass
import numpy as np

# Import vector enhancement
try:
    from aions_vector_enhancement import VectorEnhancement, VectorSearchResult
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    print("⚠️ Vector enhancement not available - using keyword search only")

# Import original AIONS
try:
    from aions_reformed_integration import ReformedAIONS
    AIONS_AVAILABLE = True
except ImportError:
    AIONS_AVAILABLE = False
    print("❌ Original AIONS not found")

# Safe import for reranker
try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    print("⚠️ CrossEncoder not available - reranking disabled")


@dataclass
class SearchResult:
    """Unified search result"""
    text: str
    score: float
    source: str
    method: str  # 'keyword', 'vector', or 'hybrid'
    metadata: Dict[str, Any]


class BM25Scorer:
    """
    BM25 scoring for keyword search
    Lightweight alternative to external libraries
    """
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = {}
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.documents = []
        self.N = 0
        
    def fit(self, documents: List[str]):
        """Fit BM25 on documents"""
        self.documents = documents
        self.N = len(documents)
        
        # Calculate document frequencies
        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_lengths.append(len(tokens))
            
            seen = set()
            for token in tokens:
                if token not in seen:
                    self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
                    seen.add(token)
        
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def score(self, query: str, doc_idx: int) -> float:
        """Calculate BM25 score for a document"""
        query_tokens = self._tokenize(query)
        doc = self.documents[doc_idx]
        doc_tokens = self._tokenize(doc)
        doc_length = self.doc_lengths[doc_idx]
        
        score = 0.0
        token_counts = Counter(doc_tokens)
        
        for token in query_tokens:
            if token not in self.doc_freqs:
                continue
                
            # IDF calculation
            df = self.doc_freqs[token]
            idf = math.log((self.N - df + 0.5) / (df + 0.5) + 1)
            
            # Term frequency
            tf = token_counts.get(token, 0)
            
            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
            
            score += idf * (numerator / denominator)
        
        return score
    
    def search(self, query: str, k: int = 10) -> List[Tuple[int, float]]:
        """Search and return top-k documents"""
        scores = [(i, self.score(query, i)) for i in range(len(self.documents))]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


class HybridRetriever:
    """
    Hybrid Retrieval System
    Combines BM25 keyword search + vector search + cross-encoder reranking
    """
    
    def __init__(self, 
                 reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
                 use_reranker: bool = True):
        """
        Initialize hybrid retriever
        
        Args:
            reranker_model: Model for reranking
            use_reranker: Whether to use reranking
        """
        # Initialize components
        self.original_aions = ReformedAIONS() if AIONS_AVAILABLE else None
        self.vector_search = VectorEnhancement() if VECTOR_AVAILABLE else None
        self.bm25 = BM25Scorer()
        
        # Initialize reranker if available
        self.reranker = None
        if use_reranker and RERANKER_AVAILABLE:
            try:
                print(f"Loading reranker model: {reranker_model}")
                self.reranker = CrossEncoder(reranker_model)
                print("✅ Reranker loaded successfully")
            except Exception as e:
                print(f"⚠️ Failed to load reranker: {e}")
        
        # Initialize BM25 with existing knowledge
        self._init_bm25()
        
        # Statistics
        self.stats = {
            'total_searches': 0,
            'keyword_hits': 0,
            'vector_hits': 0,
            'reranked': 0,
            'avg_retrieval_time': 0,
            'avg_rerank_time': 0
        }
    
    def _init_bm25(self):
        """Initialize BM25 with existing knowledge"""
        documents = []
        
        if self.original_aions and hasattr(self.original_aions, 'seeds'):
            # Extract all text from seeds
            for category, items in self.original_aions.seeds.items():
                if not items or category not in {'capitals','capitals_ext','universal','programming','programming_ext','code','science','history','practical','algorithms'}:
                    continue
                    
                for item in items:
                    if isinstance(item, dict):
                        if 's' in item and 'o' in item:
                            documents.append(f"{item['s']}: {item['o']}")
                        elif 'query' in item and 'code' in item:
                            documents.append(f"{item['query']}\n{item['code']}")
                        else:
                            documents.append(json.dumps(item))
                    else:
                        documents.append(str(item))
        
        if documents:
            self.bm25.fit(documents)
            print(f"✅ BM25 initialized with {len(documents)} documents")
        else:
            print("⚠️ No documents for BM25 initialization")
    
    def retrieve(self, 
                 query: str, 
                 k: int = 20,
                 use_keyword: bool = True,
                 use_vector: bool = True,
                 use_reranker: bool = True) -> List[SearchResult]:
        """
        Hybrid retrieval with multiple methods
        
        Args:
            query: Search query
            k: Number of results to return
            use_keyword: Use BM25 keyword search
            use_vector: Use vector similarity search
            use_reranker: Use cross-encoder reranking
            
        Returns:
            List of search results
        """
        self.stats['total_searches'] += 1
        start_time = time.time()
        
        all_results = []
        
        # 1. Keyword Search (BM25)
        if use_keyword and self.bm25.documents:
            keyword_results = self._keyword_search(query, k * 2)
            all_results.extend(keyword_results)
            if keyword_results:
                self.stats['keyword_hits'] += 1
        
        # 2. Vector Search
        if use_vector and self.vector_search and self.vector_search.vector_enabled:
            vector_results = self._vector_search(query, k * 2)
            all_results.extend(vector_results)
            if vector_results:
                self.stats['vector_hits'] += 1
        
        # 3. Merge and deduplicate
        merged_results = self._merge_results(all_results)
        
        retrieval_time = time.time() - start_time
        self.stats['avg_retrieval_time'] = (
            (self.stats['avg_retrieval_time'] * (self.stats['total_searches'] - 1) + retrieval_time)
            / self.stats['total_searches']
        )
        
        # 4. Reranking
        if use_reranker and self.reranker and len(merged_results) > 1:
            rerank_start = time.time()
            reranked = self._rerank(query, merged_results, k)
            
            rerank_time = time.time() - rerank_start
            self.stats['reranked'] += 1
            self.stats['avg_rerank_time'] = (
                (self.stats['avg_rerank_time'] * (self.stats['reranked'] - 1) + rerank_time)
                / self.stats['reranked']
            )
            
            return reranked
        
        # Return top-k without reranking
        return merged_results[:k]
    
    def _keyword_search(self, query: str, k: int) -> List[SearchResult]:
        """Perform BM25 keyword search"""
        if not self.bm25.documents:
            return []
        
        results = []
        top_docs = self.bm25.search(query, k)
        
        for doc_idx, score in top_docs:
            if score > 0:  # Only include relevant results
                results.append(SearchResult(
                    text=self.bm25.documents[doc_idx],
                    score=score,
                    source='bm25',
                    method='keyword',
                    metadata={'doc_idx': doc_idx}
                ))
        
        return results
    
    def _vector_search(self, query: str, k: int) -> List[SearchResult]:
        """Perform vector similarity search"""
        try:
            vector_results = self.vector_search._vector_search(query, k)
            
            return [
                SearchResult(
                    text=r.text,
                    score=r.score,
                    source=r.source,
                    method='vector',
                    metadata=r.metadata
                )
                for r in vector_results
            ]
        except Exception as e:
            print(f"Vector search failed: {e}")
            return []
    
    def _merge_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Merge and deduplicate results using Reciprocal Rank Fusion
        """
        if not results:
            return []
        
        # Group by text (deduplicate)
        text_to_results = {}
        for r in results:
            key = r.text[:100]  # Use first 100 chars as key
            if key not in text_to_results:
                text_to_results[key] = []
            text_to_results[key].append(r)
        
        # Calculate fusion scores
        fusion_results = []
        k = 60  # RRF constant
        
        for text_key, result_group in text_to_results.items():
            # Calculate RRF score
            rrf_score = 0
            best_result = result_group[0]
            
            for r in result_group:
                # Get rank in original result list
                method_results = [x for x in results if x.method == r.method]
                rank = method_results.index(r) + 1 if r in method_results else len(method_results)
                rrf_score += 1.0 / (k + rank)
            
            # Use the best scoring result from the group
            best_result.score = rrf_score
            fusion_results.append(best_result)
        
        # Sort by fusion score
        fusion_results.sort(key=lambda x: x.score, reverse=True)
        
        return fusion_results
    
    def _rerank(self, query: str, results: List[SearchResult], k: int) -> List[SearchResult]:
        """
        Rerank results using cross-encoder
        """
        if not self.reranker or not results:
            return results[:k]
        
        # Prepare pairs for reranking
        pairs = [[query, r.text] for r in results]
        
        # Get reranking scores
        try:
            scores = self.reranker.predict(pairs)
            
            # Update scores and sort
            for i, score in enumerate(scores):
                results[i].score = float(score)
            
            results.sort(key=lambda x: x.score, reverse=True)
            
        except Exception as e:
            print(f"Reranking failed: {e}")
        
        return results[:k]
    
    def process(self, query: str, k: int = 10) -> Dict[str, Any]:
        """
        Process query and return formatted response
        """
        # Get hybrid results
        results = self.retrieve(query, k=k)
        
        # Try to get answer from original AIONS
        original_answer = ""
        if self.original_aions:
            try:
                original_response = self.original_aions.process(query)
                original_answer = original_response.get('answer', '')
            except:
                pass
        
        # Format response
        response = {
            'status': 'success',
            'source': 'hybrid_retrieval',
            'answer': original_answer,
            'context': [
                {
                    'text': r.text[:500],
                    'score': r.score,
                    'method': r.method,
                    'source': r.source
                }
                for r in results[:5]  # Top 5 for context
            ],
            'stats': self.get_stats()
        }
        
        return response
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        return {
            **self.stats,
            'bm25_docs': len(self.bm25.documents),
            'vector_enabled': self.vector_search.vector_enabled if self.vector_search else False,
            'reranker_enabled': self.reranker is not None
        }


def test_hybrid_retrieval():
    """Test hybrid retrieval system"""
    print("\n" + "="*60)
    print("AIONS HYBRID RETRIEVAL TEST")
    print("="*60)
    
    # Initialize
    print("\nInitializing hybrid retriever...")
    retriever = HybridRetriever(use_reranker=True)
    
    # Test queries
    test_queries = [
        "What is the capital of France?",
        "How to write hello world in Python?",
        "What's 15 divided by 3?",
        "Cześć, jak się masz?",
        "Explain quicksort algorithm"
    ]
    
    print("\nTesting hybrid retrieval:")
    print("-" * 40)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        
        # Test different configurations
        configs = [
            ("Keyword only", {"use_keyword": True, "use_vector": False, "use_reranker": False}),
            ("Vector only", {"use_keyword": False, "use_vector": True, "use_reranker": False}),
            ("Hybrid + Rerank", {"use_keyword": True, "use_vector": True, "use_reranker": True})
        ]
        
        for config_name, config in configs:
            results = retriever.retrieve(query, k=3, **config)
            print(f"\n  {config_name}:")
            for i, r in enumerate(results[:2], 1):
                print(f"    {i}. [{r.method}] Score: {r.score:.3f}")
                print(f"       {r.text[:80]}...")
    
    # Show statistics
    print("\n" + "="*60)
    print("PERFORMANCE STATISTICS:")
    print("-" * 40)
    stats = retriever.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
    
    print("\n✅ Hybrid retrieval test completed!")


if __name__ == "__main__":
    test_hybrid_retrieval()