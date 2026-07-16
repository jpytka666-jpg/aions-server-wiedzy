#!/usr/bin/env python3
"""
Memory Graph Engine - Concept relationship mapping for enhanced CBMS retrieval
"""

import json
import os
from pathlib import Path
from typing import Set, Dict, List, Tuple

class MemoryGraph:
    """Graph-based concept relationship system"""
    
    def __init__(self, graph_path="graphs/memory_graph.json"):
        self.graph_path = Path(graph_path)
        self.nodes = set()
        self.edges = []
        self.adjacency = {}
        self.concept_weights = {}
        self.expansion_rules = {}
        
        if self.graph_path.exists():
            self.load_graph()
        
    def load_graph(self):
        """Load graph from JSON file"""
        with open(self.graph_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.nodes = set(data.get("nodes", []))
        self.edges = data.get("edges", [])
        self.concept_weights = data.get("concept_weights", {})
        self.expansion_rules = data.get("expansion_rules", {
            "max_depth": 2,
            "min_weight": 0.5,
            "expansion_factor": 0.8
        })
        
        # Build adjacency list
        self.adjacency = {node: set() for node in self.nodes}
        for edge in self.edges:
            if len(edge) == 2:
                node1, node2 = edge
                self.adjacency[node1].add(node2)
                self.adjacency[node2].add(node1)  # Undirected graph
    
    def find_related_concepts(self, concept: str, max_depth: int = None) -> Set[str]:
        """Find concepts related to given concept within max_depth"""
        if max_depth is None:
            max_depth = self.expansion_rules.get("max_depth", 2)
        
        if concept not in self.nodes:
            # Try partial matching
            concept = self.find_closest_concept(concept)
            if not concept:
                return set()
        
        visited = set()
        queue = [(concept, 0)]
        related = set()
        
        while queue:
            current_concept, depth = queue.pop(0)
            
            if current_concept in visited or depth > max_depth:
                continue
                
            visited.add(current_concept)
            related.add(current_concept)
            
            # Add neighbors
            if current_concept in self.adjacency:
                for neighbor in self.adjacency[current_concept]:
                    if neighbor not in visited:
                        # Apply weight filtering
                        neighbor_weight = self.concept_weights.get(neighbor, 0.5)
                        min_weight = self.expansion_rules.get("min_weight", 0.5)
                        
                        if neighbor_weight >= min_weight:
                            queue.append((neighbor, depth + 1))
        
        return related
    
    def find_closest_concept(self, query: str) -> str:
        """Find closest matching concept using fuzzy matching"""
        query_lower = query.lower()
        
        # Exact match first
        for node in self.nodes:
            if node.lower() == query_lower:
                return node
        
        # Substring match
        for node in self.nodes:
            if query_lower in node.lower() or node.lower() in query_lower:
                return node
        
        return ""
    
    def expand_query_concepts(self, query: str) -> Set[str]:
        """Expand query to related concepts for better CBMS retrieval"""
        # Extract potential concepts from query
        query_words = query.lower().split()
        expanded_concepts = set()
        
        for word in query_words:
            # Find related concepts for each word
            related = self.find_related_concepts(word)
            expanded_concepts.update(related)
            
            # Also try multi-word combinations
            for other_word in query_words:
                if word != other_word:
                    combined = f"{word}_{other_word}"
                    related_combined = self.find_related_concepts(combined)
                    expanded_concepts.update(related_combined)
        
        return expanded_concepts
    
    def get_concept_cluster(self, concepts: List[str]) -> Set[str]:
        """Get unified cluster of concepts that are interconnected"""
        all_concepts = set()
        
        for concept in concepts:
            related = self.find_related_concepts(concept)
            all_concepts.update(related)
        
        # Filter by minimum cluster size and connectivity
        cluster_concepts = set()
        for concept in all_concepts:
            connections = len(self.adjacency.get(concept, set()))
            if connections >= 2:  # Minimum 2 connections to be in cluster
                cluster_concepts.add(concept)
        
        return cluster_concepts
    
    def suggest_skill_tags(self, skill_content: str) -> List[str]:
        """Suggest tags for skill based on content analysis"""
        expanded_concepts = self.expand_query_concepts(skill_content)
        
        # Sort by weight and connectivity
        concept_scores = []
        for concept in expanded_concepts:
            weight = self.concept_weights.get(concept, 0.5)
            connections = len(self.adjacency.get(concept, set()))
            score = weight * (1 + connections * 0.1)
            concept_scores.append((concept, score))
        
        # Return top concepts as tags
        concept_scores.sort(key=lambda x: x[1], reverse=True)
        return [concept for concept, score in concept_scores[:8]]
    
    def add_concept(self, concept: str, related_concepts: List[str] = None):
        """Add new concept to graph"""
        self.nodes.add(concept)
        self.adjacency[concept] = set()
        
        if related_concepts:
            for related in related_concepts:
                if related in self.nodes:
                    self.adjacency[concept].add(related)
                    self.adjacency[related].add(concept)
                    self.edges.append([concept, related])
        
        # Set default weight
        if concept not in self.concept_weights:
            self.concept_weights[concept] = 0.5
    
    def save_graph(self):
        """Save graph back to JSON file"""
        data = {
            "nodes": list(self.nodes),
            "edges": self.edges,
            "concept_weights": self.concept_weights,
            "expansion_rules": self.expansion_rules
        }
        
        self.graph_path.parent.mkdir(exist_ok=True)
        with open(self.graph_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

class EnhancedCBMSRetrieval:
    """CBMS retrieval enhanced with Memory Graph"""
    
    def __init__(self, memory_graph: MemoryGraph):
        self.memory_graph = memory_graph
        
        # Import CBMS if available
        try:
            from cbms_memory import CBMSMemory
            self.cbms = CBMSMemory()
        except ImportError:
            print("[WARNING] CBMSMemory not available - using mock")
            self.cbms = None
    
    def enhanced_retrieve(self, query: str, max_chunks: int = 10) -> List[str]:
        """Retrieve chunks using graph-enhanced concept expansion"""
        
        # Step 1: Expand query using memory graph
        expanded_concepts = self.memory_graph.expand_query_concepts(query)
        
        print(f"[GRAPH] Original query: {query}")
        print(f"[GRAPH] Expanded concepts: {list(expanded_concepts)[:10]}")
        
        # Step 2: Build enhanced query with related concepts
        enhanced_query_parts = [query]
        for concept in list(expanded_concepts)[:5]:  # Top 5 concepts
            enhanced_query_parts.append(concept)
        
        enhanced_query = " ".join(enhanced_query_parts)
        
        # Step 3: Retrieve using enhanced query
        if self.cbms:
            try:
                chunks = self.cbms.retrieve_relevant_chunks(enhanced_query, max_chunks)
                print(f"[GRAPH] Retrieved {len(chunks)} chunks using enhanced query")
                return chunks
            except Exception as e:
                print(f"[GRAPH] CBMS retrieval failed: {e}")
        
        # Fallback - return concept list as mock chunks
        return [f"Concept chunk: {concept}" for concept in list(expanded_concepts)[:max_chunks]]
    
    def smart_cbms_with_graph(self, query: str) -> str:
        """Enhanced smart_cbms_response with graph expansion"""
        try:
            from smart_cbms import smart_cbms_response
            
            # Get expanded concepts first
            expanded_concepts = self.memory_graph.expand_query_concepts(query)
            concept_context = " ".join(list(expanded_concepts)[:5])
            
            # Enhance original query with concept context
            enhanced_query = f"{query} (context: {concept_context})"
            
            response = smart_cbms_response(enhanced_query)
            
            if response and len(response.strip()) > 50:
                print(f"[GRAPH] Enhanced CBMS response with {len(expanded_concepts)} concepts")
                return response
            else:
                return smart_cbms_response(query)  # Fallback to original
                
        except Exception as e:
            print(f"[GRAPH] Enhanced CBMS failed: {e}")
            return f"Graph-enhanced analysis for: {query}"

def test_memory_graph():
    """Test memory graph functionality"""
    print("[TEST] Testing Memory Graph Engine...")
    
    graph = MemoryGraph()
    
    # Test concept expansion
    test_queries = [
        "RSI trading strategy",
        "risk management",
        "breakout signals",
        "portfolio optimization"
    ]
    
    for query in test_queries:
        print(f"\n[TEST] Query: {query}")
        concepts = graph.expand_query_concepts(query)
        print(f"[TEST] Expanded to: {list(concepts)[:10]}")
    
    # Test enhanced retrieval
    enhanced_retrieval = EnhancedCBMSRetrieval(graph)
    
    for query in test_queries:
        print(f"\n[TEST] Enhanced retrieval for: {query}")
        chunks = enhanced_retrieval.enhanced_retrieve(query, max_chunks=5)
        print(f"[TEST] Retrieved {len(chunks)} chunks")

if __name__ == "__main__":
    test_memory_graph()