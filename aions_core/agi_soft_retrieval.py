#!/usr/bin/env python3
"""
AGI Soft Retrieval with Gradient Flow
Differentiable retrieval for end-to-end learning
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import random
from collections import defaultdict

# BM25 implementation for initial filtering
class BM25:
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.doc_lengths = [len(doc.split()) for doc in corpus]
        self.avgdl = sum(self.doc_lengths) / len(self.doc_lengths)
        self.doc_freqs = []
        self.idf = {}
        self.N = len(corpus)

        # Build index
        self._build_index()

    def _build_index(self):
        df = defaultdict(int)

        for doc in self.corpus:
            tokens = set(doc.lower().split())
            doc_freq = defaultdict(int)

            for token in doc.lower().split():
                doc_freq[token] += 1

            self.doc_freqs.append(doc_freq)

            for token in tokens:
                df[token] += 1

        # Calculate IDF
        for token, freq in df.items():
            self.idf[token] = np.log((self.N - freq + 0.5) / (freq + 0.5))

    def score(self, query: str, doc_idx: int) -> float:
        query_tokens = query.lower().split()
        doc_freq = self.doc_freqs[doc_idx]
        doc_len = self.doc_lengths[doc_idx]

        score = 0.0
        for token in query_tokens:
            if token not in self.idf:
                continue

            freq = doc_freq.get(token, 0)
            numerator = self.idf[token] * freq * (self.k1 + 1)
            denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += numerator / denominator

        return score

    def search(self, query: str, k: int = 10) -> List[Tuple[int, float]]:
        scores = [(i, self.score(query, i)) for i in range(self.N)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


class ChunkEmbedder(nn.Module):
    """Learnable chunk embeddings"""

    def __init__(self, vocab_size: int = 10000, embed_dim: int = 768, max_length: int = 512):
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.max_length = max_length

        # Token embeddings
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.position_embedding = nn.Embedding(max_length, embed_dim)

        # Transformer encoder for contextual embeddings
        self.encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=embed_dim,
                nhead=8,
                dim_feedforward=2048,
                dropout=0.1,
                batch_first=True
            ),
            num_layers=2
        )

        # Layer norm
        self.layer_norm = nn.LayerNorm(embed_dim)

    def forward(self, chunk_texts: List[str]) -> torch.Tensor:
        """Convert chunk texts to embeddings"""
        batch_embeddings = []

        for text in chunk_texts:
            # Simple tokenization (hash-based for demo)
            tokens = text.lower().split()[:self.max_length]
            token_ids = [abs(hash(token)) % self.vocab_size for token in tokens]

            if not token_ids:
                token_ids = [0]  # Empty text handling

            # Convert to tensor
            token_tensor = torch.tensor(token_ids, dtype=torch.long, device=self.token_embedding.weight.device)

            # Get embeddings
            token_emb = self.token_embedding(token_tensor)

            # Add position embeddings
            positions = torch.arange(len(token_ids), device=token_tensor.device)
            pos_emb = self.position_embedding(positions)

            # Combine
            embeddings = token_emb + pos_emb
            embeddings = embeddings.unsqueeze(0)  # Add batch dimension

            # Encode
            encoded = self.encoder(embeddings)

            # Pool (mean pooling)
            pooled = torch.mean(encoded, dim=1)

            batch_embeddings.append(pooled)

        # Stack all embeddings
        if batch_embeddings:
            batch_tensor = torch.cat(batch_embeddings, dim=0)
            return self.layer_norm(batch_tensor)
        else:
            return torch.zeros(1, self.embed_dim, device=self.token_embedding.weight.device)


class SoftRetriever(nn.Module):
    """Differentiable soft retrieval with gradient flow"""

    def __init__(self,
                 chunks: List[Dict],
                 embed_dim: int = 768,
                 num_candidates: int = 192,
                 num_negatives: int = 64,
                 temperature: float = 0.07):
        super().__init__()

        self.chunks = chunks
        self.num_candidates = num_candidates
        self.num_negatives = num_negatives
        self.temperature = temperature
        self.embed_dim = embed_dim

        # Initialize embedder
        self.embedder = ChunkEmbedder(embed_dim=embed_dim)

        # Query projection
        self.query_projection = nn.Linear(embed_dim, embed_dim)

        # Initialize BM25
        chunk_texts = [c.get("content", "") for c in chunks]
        self.bm25 = BM25(chunk_texts)

        # Cache for chunk embeddings (computed once)
        self.register_buffer('chunk_embeddings_cache', torch.zeros(len(chunks), embed_dim))
        self.cache_initialized = False

    def initialize_cache(self):
        """Pre-compute all chunk embeddings"""
        if not self.cache_initialized:
            with torch.no_grad():
                chunk_texts = [c.get("content", "") for c in self.chunks]

                # Process in batches
                batch_size = 32
                all_embeddings = []

                for i in range(0, len(chunk_texts), batch_size):
                    batch = chunk_texts[i:i+batch_size]
                    batch_emb = self.embedder(batch)
                    all_embeddings.append(batch_emb)

                self.chunk_embeddings_cache = torch.cat(all_embeddings, dim=0)
                self.cache_initialized = True

    def forward(self,
                query: str,
                query_embedding: Optional[torch.Tensor] = None,
                return_gradients: bool = False) -> Dict[str, torch.Tensor]:
        """
        Soft retrieval with full gradient flow

        Args:
            query: Query string
            query_embedding: Optional pre-computed query embedding
            return_gradients: Whether to compute and return gradient info

        Returns:
            Dictionary with context embedding, attention weights, and selected chunks
        """

        # Initialize cache if needed
        if not self.cache_initialized:
            self.initialize_cache()

        # Get query embedding
        if query_embedding is None:
            query_embedding = self.embedder([query])[0]

        # Project query
        query_emb = self.query_projection(query_embedding)

        # Step 1: BM25 pre-filtering (non-differentiable, but fast)
        bm25_results = self.bm25.search(query, k=self.num_candidates - self.num_negatives)
        bm25_indices = [idx for idx, _ in bm25_results]

        # Step 2: Add random negatives for contrastive learning
        all_indices = list(range(len(self.chunks)))
        remaining_indices = [i for i in all_indices if i not in bm25_indices]

        if len(remaining_indices) >= self.num_negatives:
            negative_indices = random.sample(remaining_indices, self.num_negatives)
        else:
            negative_indices = remaining_indices

        # Combine candidates
        candidate_indices = bm25_indices + negative_indices

        # Step 3: Get candidate embeddings (differentiable from here!)
        candidate_embeddings = self.chunk_embeddings_cache[candidate_indices]

        # If training, recompute embeddings for gradient flow
        if self.training:
            candidate_texts = [self.chunks[i]["content"] for i in candidate_indices]
            candidate_embeddings = self.embedder(candidate_texts)

        # Step 4: Compute attention scores (differentiable)
        scores = torch.matmul(query_emb.unsqueeze(0), candidate_embeddings.T).squeeze(0)
        scores = scores / self.temperature

        # Step 5: Soft attention weights (differentiable softmax)
        attention_weights = F.softmax(scores, dim=-1)

        # Step 6: Weighted mixture of embeddings (differentiable)
        context_embedding = torch.matmul(attention_weights.unsqueeze(0), candidate_embeddings)
        context_embedding = context_embedding.squeeze(0)

        # Prepare output
        output = {
            "context_embedding": context_embedding,
            "attention_weights": attention_weights,
            "candidate_indices": candidate_indices,
            "candidate_embeddings": candidate_embeddings,
            "scores": scores
        }

        # Optional: Compute gradient information for verification
        if return_gradients and self.training:
            output["gradients"] = self._compute_gradient_info(
                context_embedding,
                candidate_embeddings
            )

        return output

    def _compute_gradient_info(self, context_emb: torch.Tensor, candidate_emb: torch.Tensor) -> Dict:
        """Compute gradient flow information for debugging"""
        grad_info = {}

        # Check if gradients can flow
        grad_info["context_requires_grad"] = context_emb.requires_grad
        grad_info["candidates_require_grad"] = candidate_emb.requires_grad

        # Create dummy loss to test gradient flow
        if context_emb.requires_grad:
            dummy_loss = context_emb.sum()

            # Compute gradients
            grads = torch.autograd.grad(
                dummy_loss,
                candidate_emb,
                retain_graph=True,
                allow_unused=True
            )[0]

            if grads is not None:
                grad_info["gradient_norm"] = grads.norm().item()
                grad_info["gradient_mean"] = grads.mean().item()
                grad_info["gradient_std"] = grads.std().item()
                grad_info["gradient_flow"] = True
            else:
                grad_info["gradient_flow"] = False
        else:
            grad_info["gradient_flow"] = False

        return grad_info

    def get_entropy(self, attention_weights: torch.Tensor) -> torch.Tensor:
        """Compute entropy of attention distribution for regularization"""
        # Add small epsilon to avoid log(0)
        entropy = -torch.sum(attention_weights * torch.log(attention_weights + 1e-8))
        return entropy

    def get_top_chunks(self, attention_weights: torch.Tensor,
                      candidate_indices: List[int],
                      k: int = 5) -> List[Tuple[int, float]]:
        """Get top-k attended chunks with scores"""
        weights_np = attention_weights.detach().cpu().numpy()
        top_k_idx = np.argsort(weights_np)[-k:][::-1]

        results = []
        for idx in top_k_idx:
            chunk_idx = candidate_indices[idx]
            weight = weights_np[idx]
            results.append((chunk_idx, weight))

        return results


class CitationCoverageLoss(nn.Module):
    """Loss function to enforce citation coverage"""

    def __init__(self, min_coverage: float = 0.3, tokenizer=None):
        super().__init__()
        self.min_coverage = min_coverage
        self.tokenizer = tokenizer

    def forward(self,
                generated_text: str,
                source_texts: List[str],
                attention_weights: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Compute citation coverage loss

        Args:
            generated_text: Generated response text
            source_texts: List of source chunk texts
            attention_weights: Optional attention weights for weighted coverage

        Returns:
            Citation coverage loss (0 if coverage is sufficient)
        """

        # Tokenize (simple word-level for now)
        gen_tokens = set(generated_text.lower().split())

        if not gen_tokens:
            return torch.tensor(0.0, device=attention_weights.device if attention_weights is not None else 'cpu')

        # Compute coverage for each source
        coverages = []
        for source in source_texts:
            source_tokens = set(source.lower().split())
            overlap = len(gen_tokens & source_tokens)
            coverage = overlap / len(gen_tokens) if gen_tokens else 0.0
            coverages.append(coverage)

        # Weight by attention if provided
        if attention_weights is not None:
            coverages = torch.tensor(coverages, device=attention_weights.device)
            weighted_coverage = torch.sum(coverages * attention_weights)
        else:
            weighted_coverage = torch.tensor(max(coverages) if coverages else 0.0)

        # Compute loss (penalty if below threshold)
        loss = F.relu(self.min_coverage - weighted_coverage)

        return loss

    def get_coverage_stats(self,
                           generated_text: str,
                           source_texts: List[str]) -> Dict[str, float]:
        """Get detailed coverage statistics"""
        gen_tokens = set(generated_text.lower().split())

        stats = {
            "max_coverage": 0.0,
            "mean_coverage": 0.0,
            "covered_tokens": 0,
            "total_tokens": len(gen_tokens)
        }

        if not gen_tokens:
            return stats

        coverages = []
        all_covered = set()

        for source in source_texts:
            source_tokens = set(source.lower().split())
            overlap = gen_tokens & source_tokens
            all_covered.update(overlap)
            coverage = len(overlap) / len(gen_tokens)
            coverages.append(coverage)

        stats["max_coverage"] = max(coverages) if coverages else 0.0
        stats["mean_coverage"] = np.mean(coverages) if coverages else 0.0
        stats["covered_tokens"] = len(all_covered)

        return stats


def verify_gradient_flow(model: nn.Module,
                         loss: torch.Tensor,
                         check_params: List[str] = None) -> Dict[str, bool]:
    """
    Verify that gradients flow through specified model parameters

    Args:
        model: Model to check
        loss: Loss tensor to backpropagate from
        check_params: List of parameter names to check (None = check all)

    Returns:
        Dictionary mapping parameter names to gradient flow status
    """

    # Retain graph for multiple gradient computations
    loss.backward(retain_graph=True)

    gradient_status = {}

    for name, param in model.named_parameters():
        if check_params is None or name in check_params:
            if param.grad is not None:
                has_gradient = (param.grad.abs().sum() > 0).item()
                gradient_status[name] = has_gradient
            else:
                gradient_status[name] = False

    return gradient_status


# Test functions
def test_soft_retrieval():
    """Test soft retrieval with gradient flow"""
    print("Testing Soft Retrieval with Gradient Flow...")

    # Create dummy chunks
    chunks = [
        {"id": f"chunk_{i}", "content": f"This is test chunk number {i} with some content about topic {i%5}"}
        for i in range(100)
    ]

    # Initialize retriever
    retriever = SoftRetriever(chunks, num_candidates=20, num_negatives=10)
    retriever.train()  # Enable training mode

    # Test query
    query = "Tell me about topic 2"

    # Forward pass
    result = retriever(query, return_gradients=True)

    # Check outputs
    print(f"Context embedding shape: {result['context_embedding'].shape}")
    print(f"Attention weights shape: {result['attention_weights'].shape}")
    print(f"Number of candidates: {len(result['candidate_indices'])}")

    # Check gradient flow
    if result.get("gradients"):
        print(f"Gradient flow: {result['gradients'].get('gradient_flow', False)}")
        if result['gradients'].get('gradient_flow'):
            print(f"Gradient norm: {result['gradients'].get('gradient_norm', 0):.6f}")

    # Get top attended chunks
    top_chunks = retriever.get_top_chunks(
        result['attention_weights'],
        result['candidate_indices'],
        k=5
    )

    print("\nTop 5 attended chunks:")
    for chunk_idx, weight in top_chunks:
        print(f"  Chunk {chunk_idx}: {weight:.4f} - {chunks[chunk_idx]['content'][:50]}...")

    # Test citation coverage loss
    citation_loss = CitationCoverageLoss(min_coverage=0.3)

    generated = "This is about topic 2 and contains some content"
    source_texts = [chunks[idx]["content"] for idx in result['candidate_indices']]

    loss = citation_loss(generated, source_texts, result['attention_weights'])
    print(f"\nCitation coverage loss: {loss.item():.4f}")

    # Get coverage stats
    stats = citation_loss.get_coverage_stats(generated, source_texts)
    print(f"Coverage stats: {stats}")

    # Verify gradient flow
    total_loss = result['context_embedding'].sum() + loss
    grad_status = verify_gradient_flow(retriever, total_loss)

    print(f"\nGradient flow verification:")
    for param_name, has_gradient in list(grad_status.items())[:5]:
        status = "✓" if has_gradient else "✗"
        print(f"  {status} {param_name}")

    print("\n✅ Soft retrieval test completed!")
    return True


if __name__ == "__main__":
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Run test
    test_soft_retrieval()