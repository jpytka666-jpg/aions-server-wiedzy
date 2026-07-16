#!/usr/bin/env python3
"""
AGI Neural Backpropagation System
Differentiable reasoning with gradient-based learning
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable
import numpy as np
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
from collections import defaultdict

# Check for CUDA availability
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")


class KnowledgeEmbedder(nn.Module):
    """Convert CBMS chunks to learnable embeddings"""

    def __init__(self, vocab_size: int = 10000, embed_dim: int = 512, chunk_dim: int = 256):
        super(KnowledgeEmbedder, self).__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.chunk_dim = chunk_dim

        # Embedding layers
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.position_embedding = nn.Embedding(1000, embed_dim)

        # Chunk encoder
        self.chunk_encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=embed_dim, nhead=8, batch_first=True),
            num_layers=2
        )

        # Projection to chunk space
        self.chunk_projection = nn.Linear(embed_dim, chunk_dim)

        # Learnable chunk importance weights
        self.chunk_importance = nn.Parameter(torch.ones(1000))

    def forward(self, chunks: List[Dict]) -> torch.Tensor:
        """Convert chunks to embeddings"""
        batch_embeddings = []

        for chunk in chunks:
            # Tokenize chunk content (simplified)
            tokens = self._tokenize(chunk.get("content", ""))
            token_ids = torch.tensor(tokens, dtype=torch.long, device=DEVICE)

            # Get embeddings
            token_embeds = self.token_embedding(token_ids)

            # Add position embeddings
            positions = torch.arange(len(tokens), device=DEVICE)
            pos_embeds = self.position_embedding(positions)

            # Combine
            embeddings = token_embeds + pos_embeds

            # Encode chunk
            if embeddings.dim() == 2:
                embeddings = embeddings.unsqueeze(0)

            encoded = self.chunk_encoder(embeddings)

            # Project and pool
            projected = self.chunk_projection(encoded)
            pooled = torch.mean(projected, dim=1)

            batch_embeddings.append(pooled)

        if batch_embeddings:
            batch_tensor = torch.cat(batch_embeddings, dim=0)

            # Apply importance weights
            importance = F.softmax(self.chunk_importance[:len(chunks)], dim=0)
            weighted = batch_tensor * importance.unsqueeze(-1)

            return weighted
        else:
            return torch.zeros(1, self.chunk_dim, device=DEVICE)

    def _tokenize(self, text: str) -> List[int]:
        """Simple tokenization to IDs"""
        # Hash-based tokenization for simplicity
        words = text.lower().split()
        tokens = []
        for word in words[:100]:  # Limit length
            token_id = abs(hash(word)) % self.vocab_size
            tokens.append(token_id)
        return tokens if tokens else [0]


class ReasoningGraph(nn.Module):
    """Differentiable reasoning graph with backprop"""

    def __init__(self, input_dim: int = 256, hidden_dim: int = 512, output_dim: int = 256):
        super(ReasoningGraph, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # Reasoning layers
        self.input_projection = nn.Linear(input_dim, hidden_dim)

        # Multi-hop reasoning network
        self.reasoning_steps = nn.ModuleList([
            nn.GRU(hidden_dim, hidden_dim, batch_first=True)
            for _ in range(3)  # 3 reasoning hops
        ])

        # Attention mechanism for knowledge selection
        self.attention = nn.MultiheadAttention(hidden_dim, num_heads=8, batch_first=True)

        # Output layers
        self.output_projection = nn.Linear(hidden_dim, output_dim)
        self.confidence_head = nn.Linear(output_dim, 1)

        # Dropout for regularization
        self.dropout = nn.Dropout(0.1)

    def forward(self, query_embedding: torch.Tensor, knowledge_embeddings: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Execute reasoning with gradient tracking"""

        # Project inputs
        query = self.input_projection(query_embedding)
        knowledge = self.input_projection(knowledge_embeddings)

        # Initialize reasoning state
        reasoning_state = query.unsqueeze(0) if query.dim() == 1 else query

        # Multi-hop reasoning
        hop_outputs = []
        for i, gru in enumerate(self.reasoning_steps):
            # Attend to knowledge
            attended, attention_weights = self.attention(
                reasoning_state, knowledge, knowledge
            )

            # Combine with previous state
            combined = reasoning_state + self.dropout(attended)

            # Reasoning step
            output, hidden = gru(combined)
            reasoning_state = output

            hop_outputs.append({
                "state": reasoning_state,
                "attention": attention_weights
            })

        # Final projection
        final_state = reasoning_state
        output = self.output_projection(final_state)

        # Confidence estimation
        confidence = torch.sigmoid(self.confidence_head(output))

        return {
            "output": output,
            "confidence": confidence,
            "reasoning_chain": hop_outputs,
            "final_state": final_state
        }


class DifferentiableMemory(nn.Module):
    """Neural memory with differentiable read/write"""

    def __init__(self, memory_size: int = 128, memory_dim: int = 256, controller_dim: int = 512):
        super(DifferentiableMemory, self).__init__()
        self.memory_size = memory_size
        self.memory_dim = memory_dim

        # Memory matrix
        self.memory = nn.Parameter(torch.randn(memory_size, memory_dim) * 0.01)

        # Controller networks
        self.read_controller = nn.Linear(controller_dim, memory_dim)
        self.write_controller = nn.Linear(controller_dim, memory_dim)

        # Addressing mechanisms
        self.content_addressing = nn.Linear(memory_dim, memory_size)
        self.location_addressing = nn.Linear(controller_dim, memory_size)

        # Gates
        self.read_gate = nn.Linear(controller_dim, 1)
        self.write_gate = nn.Linear(controller_dim, 1)

    def read(self, query: torch.Tensor) -> torch.Tensor:
        """Differentiable memory read"""
        # Generate read key
        read_key = self.read_controller(query)

        # Content-based addressing
        similarities = F.cosine_similarity(
            read_key.unsqueeze(1),
            self.memory.unsqueeze(0),
            dim=2
        )

        # Soft attention over memory
        attention = F.softmax(similarities, dim=1)

        # Read from memory
        read_content = torch.matmul(attention, self.memory)

        # Apply read gate
        gate = torch.sigmoid(self.read_gate(query))

        return read_content * gate

    def write(self, controller_state: torch.Tensor, content: torch.Tensor) -> None:
        """Differentiable memory write"""
        # Generate write key
        write_key = self.write_controller(controller_state)

        # Location-based addressing
        location_weights = F.softmax(self.location_addressing(controller_state), dim=-1)

        # Write gate
        gate = torch.sigmoid(self.write_gate(controller_state))

        # Update memory (differentiable)
        write_content = content * gate

        # Soft write using attention
        for i in range(self.memory_size):
            self.memory.data[i] = (
                self.memory.data[i] * (1 - location_weights[0, i]) +
                write_content[0] * location_weights[0, i]
            )


class AGINeuralBackprop(nn.Module):
    """Main AGI system with neural backpropagation"""

    def __init__(self, memory_dir: str = None):
        super(AGINeuralBackprop, self).__init__()

        # Component dimensions
        self.embed_dim = 256
        self.hidden_dim = 512
        self.output_dim = 256

        # Neural components
        self.knowledge_embedder = KnowledgeEmbedder(
            vocab_size=10000,
            embed_dim=512,
            chunk_dim=self.embed_dim
        )

        self.reasoning_graph = ReasoningGraph(
            input_dim=self.embed_dim,
            hidden_dim=self.hidden_dim,
            output_dim=self.output_dim
        )

        self.memory = DifferentiableMemory(
            memory_size=128,
            memory_dim=self.embed_dim,
            controller_dim=self.hidden_dim
        )

        # Query encoder
        self.query_encoder = nn.LSTM(
            self.embed_dim,
            self.hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True
        )

        self.query_projection = nn.Linear(self.hidden_dim * 2, self.embed_dim)

        # Output decoder
        self.output_decoder = nn.TransformerDecoder(
            nn.TransformerDecoderLayer(
                d_model=self.output_dim,
                nhead=8,
                batch_first=True
            ),
            num_layers=2
        )

        # Final output layer
        self.output_head = nn.Linear(self.output_dim, self.embed_dim)

        # Move to device
        self.to(DEVICE)

        # Optimizer
        self.optimizer = optim.Adam(self.parameters(), lr=0.001)

        # Tracking
        self.training_history = []
        self.gradient_norms = []

    def forward(self, query: str, knowledge_chunks: List[Dict]) -> Dict[str, Any]:
        """Forward pass with full gradient tracking"""

        # Encode query
        query_embedding = self._encode_query(query)

        # Embed knowledge chunks
        knowledge_embeddings = self.knowledge_embedder(knowledge_chunks)

        # Read from memory
        memory_content = self.memory.read(query_embedding)

        # Combine query with memory
        enhanced_query = query_embedding + memory_content

        # Execute reasoning
        reasoning_output = self.reasoning_graph(enhanced_query, knowledge_embeddings)

        # Decode output
        output_sequence = self._decode_output(reasoning_output["output"])

        # Write to memory
        self.memory.write(reasoning_output["final_state"], reasoning_output["output"])

        return {
            "response": output_sequence,
            "confidence": reasoning_output["confidence"],
            "reasoning_chain": reasoning_output["reasoning_chain"],
            "embeddings": {
                "query": query_embedding,
                "knowledge": knowledge_embeddings,
                "output": reasoning_output["output"]
            }
        }

    def backward_step(self, loss: torch.Tensor) -> Dict[str, float]:
        """Execute backpropagation and update weights"""

        # Zero gradients
        self.optimizer.zero_grad()

        # Backward pass
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=1.0)

        # Calculate gradient statistics
        total_norm = 0.0
        for p in self.parameters():
            if p.grad is not None:
                param_norm = p.grad.data.norm(2)
                total_norm += param_norm.item() ** 2
        total_norm = total_norm ** 0.5

        self.gradient_norms.append(total_norm)

        # Update weights
        self.optimizer.step()

        return {
            "loss": loss.item(),
            "grad_norm": total_norm
        }

    def compute_loss(self, output: Dict[str, Any], target: Dict[str, Any]) -> torch.Tensor:
        """Compute multi-objective loss for AGI"""

        losses = {}

        # Reasoning quality loss
        if "reasoning_target" in target:
            reasoning_loss = F.mse_loss(
                output["embeddings"]["output"],
                target["reasoning_target"]
            )
            losses["reasoning"] = reasoning_loss

        # Confidence calibration loss
        if "confidence_target" in target:
            confidence_loss = F.binary_cross_entropy(
                output["confidence"],
                target["confidence_target"]
            )
            losses["confidence"] = confidence_loss

        # Knowledge consistency loss
        if "knowledge_consistency" in target:
            knowledge_embeddings = output["embeddings"]["knowledge"]
            consistency_loss = self._knowledge_consistency_loss(
                knowledge_embeddings,
                target["knowledge_consistency"]
            )
            losses["consistency"] = consistency_loss

        # Self-improvement objective
        if len(self.training_history) > 10:
            improvement_loss = self._self_improvement_loss(output)
            losses["improvement"] = improvement_loss

        # Combine losses
        total_loss = sum(losses.values())

        # Track loss components
        self.training_history.append({
            "timestamp": time.time(),
            "losses": {k: v.item() for k, v in losses.items()},
            "total_loss": total_loss.item()
        })

        return total_loss

    def train_on_interaction(self, query: str, chunks: List[Dict], feedback: float) -> Dict[str, Any]:
        """Train on single interaction with feedback"""

        # Forward pass
        output = self.forward(query, chunks)

        # Create target based on feedback
        target = self._create_training_target(output, feedback)

        # Compute loss
        loss = self.compute_loss(output, target)

        # Backward pass
        backward_info = self.backward_step(loss)

        return {
            "output": output,
            "training": backward_info,
            "feedback": feedback
        }

    def _encode_query(self, query: str) -> torch.Tensor:
        """Encode query string to embedding"""
        # Tokenize
        tokens = query.lower().split()
        token_ids = [abs(hash(token)) % 10000 for token in tokens[:50]]

        # Create embedding
        token_tensor = torch.tensor(token_ids, dtype=torch.long, device=DEVICE)
        embeddings = self.knowledge_embedder.token_embedding(token_tensor)

        # Add batch dimension
        embeddings = embeddings.unsqueeze(0)

        # Encode with LSTM
        output, (hidden, cell) = self.query_encoder(embeddings)

        # Pool and project
        pooled = torch.mean(output, dim=1)
        projected = self.query_projection(pooled)

        return projected

    def _decode_output(self, output_embedding: torch.Tensor) -> str:
        """Decode embedding to response string"""
        # For now, return a placeholder
        # In full implementation, this would use a language model decoder
        return f"Neural response [embedding shape: {output_embedding.shape}]"

    def _knowledge_consistency_loss(self, embeddings: torch.Tensor, target_consistency: float) -> torch.Tensor:
        """Ensure knowledge embeddings are consistent"""
        # Pairwise similarities
        normalized = F.normalize(embeddings, p=2, dim=1)
        similarities = torch.matmul(normalized, normalized.T)

        # Consistency loss - embeddings should be diverse but related
        diversity_loss = -torch.mean(torch.abs(similarities - torch.eye(similarities.size(0), device=DEVICE)))

        return diversity_loss * target_consistency

    def _self_improvement_loss(self, output: Dict[str, Any]) -> torch.Tensor:
        """Loss for self-improvement objective"""
        # Compare with recent performance
        recent_confidences = [h["output"]["confidence"] for h in self.training_history[-10:] if "output" in h]

        if recent_confidences:
            avg_confidence = sum(recent_confidences) / len(recent_confidences)
            target_confidence = min(1.0, avg_confidence + 0.05)  # Aim for gradual improvement

            improvement_loss = F.mse_loss(
                output["confidence"],
                torch.tensor([[target_confidence]], device=DEVICE)
            )

            return improvement_loss

        return torch.tensor(0.0, device=DEVICE)

    def _create_training_target(self, output: Dict[str, Any], feedback: float) -> Dict[str, Any]:
        """Create training target based on feedback"""
        target = {}

        # Set confidence target based on feedback
        target["confidence_target"] = torch.tensor([[feedback]], device=DEVICE)

        # Create reasoning target (simplified - in practice would be more sophisticated)
        if feedback > 0.7:
            # Good response - use output as target with small noise
            target["reasoning_target"] = output["embeddings"]["output"].detach() + torch.randn_like(output["embeddings"]["output"]) * 0.01
        else:
            # Poor response - create different target
            target["reasoning_target"] = torch.randn_like(output["embeddings"]["output"]) * 0.1

        # Knowledge consistency based on feedback
        target["knowledge_consistency"] = feedback

        return target

    def save_checkpoint(self, path: str):
        """Save model checkpoint"""
        checkpoint = {
            "model_state": self.state_dict(),
            "optimizer_state": self.optimizer.state_dict(),
            "training_history": self.training_history,
            "gradient_norms": self.gradient_norms
        }
        torch.save(checkpoint, path)
        print(f"Checkpoint saved to {path}")

    def load_checkpoint(self, path: str):
        """Load model checkpoint"""
        if Path(path).exists():
            checkpoint = torch.load(path, map_location=DEVICE)
            self.load_state_dict(checkpoint["model_state"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state"])
            self.training_history = checkpoint.get("training_history", [])
            self.gradient_norms = checkpoint.get("gradient_norms", [])
            print(f"Checkpoint loaded from {path}")
            return True
        return False

    def analyze_gradients(self) -> Dict[str, Any]:
        """Analyze gradient flow through network"""
        analysis = {
            "layer_gradients": {},
            "gradient_statistics": {},
            "vanishing_gradient": False,
            "exploding_gradient": False
        }

        # Analyze each layer
        for name, param in self.named_parameters():
            if param.grad is not None:
                grad_data = param.grad.data
                analysis["layer_gradients"][name] = {
                    "mean": grad_data.mean().item(),
                    "std": grad_data.std().item(),
                    "max": grad_data.max().item(),
                    "min": grad_data.min().item()
                }

        # Overall statistics
        if self.gradient_norms:
            recent_norms = self.gradient_norms[-100:]
            analysis["gradient_statistics"] = {
                "mean_norm": np.mean(recent_norms),
                "std_norm": np.std(recent_norms),
                "max_norm": np.max(recent_norms),
                "min_norm": np.min(recent_norms)
            }

            # Check for gradient issues
            if analysis["gradient_statistics"]["mean_norm"] < 0.0001:
                analysis["vanishing_gradient"] = True
            if analysis["gradient_statistics"]["max_norm"] > 100:
                analysis["exploding_gradient"] = True

        return analysis


def create_synthetic_chunks(n: int = 10) -> List[Dict]:
    """Create synthetic knowledge chunks for testing"""
    chunks = []
    topics = ["reasoning", "learning", "memory", "attention", "backpropagation",
             "neural networks", "AGI", "consciousness", "intelligence", "optimization"]

    for i in range(n):
        chunk = {
            "id": f"K{hashlib.md5(str(i).encode()).hexdigest()[:12].upper()}",
            "content": f"Knowledge about {topics[i % len(topics)]} with details about implementation and theory",
            "concept": topics[i % len(topics)],
            "confidence": 0.5 + (i % 5) * 0.1
        }
        chunks.append(chunk)

    return chunks


if __name__ == "__main__":
    print("Initializing AGI Neural Backpropagation System...")

    # Initialize system
    agi_neural = AGINeuralBackprop()

    # Create test data
    test_chunks = create_synthetic_chunks(10)
    test_query = "How does backpropagation improve reasoning?"

    print(f"\nTest query: {test_query}")
    print(f"Knowledge chunks: {len(test_chunks)}")

    # Training loop
    print("\nTraining with backpropagation:")
    for epoch in range(5):
        # Simulate feedback (would come from actual evaluation in practice)
        feedback = 0.6 + epoch * 0.08  # Gradually improving feedback

        # Train on interaction
        result = agi_neural.train_on_interaction(test_query, test_chunks, feedback)

        print(f"Epoch {epoch + 1}:")
        print(f"  Loss: {result['training']['loss']:.4f}")
        print(f"  Gradient norm: {result['training']['grad_norm']:.4f}")
        print(f"  Confidence: {result['output']['confidence'].item():.4f}")
        print(f"  Feedback: {feedback:.2f}")

    # Analyze gradients
    print("\nGradient analysis:")
    gradient_analysis = agi_neural.analyze_gradients()
    print(f"  Mean gradient norm: {gradient_analysis['gradient_statistics'].get('mean_norm', 0):.6f}")
    print(f"  Vanishing gradient: {gradient_analysis['vanishing_gradient']}")
    print(f"  Exploding gradient: {gradient_analysis['exploding_gradient']}")

    # Save checkpoint
    checkpoint_path = "agi_neural_checkpoint.pth"
    agi_neural.save_checkpoint(checkpoint_path)

    print(f"\nAGI Neural Backprop system initialized and trained!")
    print(f"Device: {DEVICE}")
    print(f"Total parameters: {sum(p.numel() for p in agi_neural.parameters()):,}")