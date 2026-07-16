#!/usr/bin/env python3
"""
AGI Dynamic Learning Pipeline
Self-improving knowledge acquisition and pattern extraction
"""

import json
import hashlib
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
import re
import pickle
import sqlite3
from datetime import datetime

# Import existing components
try:
    from agi_core import AGICore, Thought, WorkingMemory
    from server.cbms_memory import CBMSMemory
    from server.korean_keys import build_keys
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent))
    from cbms_memory import CBMSMemory
    from korean_keys import build_keys


@dataclass
class KnowledgePattern:
    """Represents a learned pattern"""
    pattern_type: str
    content: str
    frequency: int = 1
    confidence: float = 0.5
    context_examples: List[str] = field(default_factory=list)
    last_used: float = field(default_factory=time.time)
    success_rate: float = 0.5


@dataclass
class LearningMemory:
    """Memory for tracking learning progress"""
    learned_patterns: List[KnowledgePattern] = field(default_factory=list)
    concept_graph: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    interaction_history: deque = field(default_factory=lambda: deque(maxlen=1000))
    performance_tracking: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    knowledge_gaps: Set[str] = field(default_factory=set)


class AGILearning:
    """Dynamic learning pipeline for knowledge acquisition and improvement"""

    def __init__(self, memory_dir: str = None, db_path: str = None):
        self.memory_dir = Path(memory_dir) if memory_dir else Path("memory")
        self.db_path = db_path or str(self.memory_dir / "learning.db")
        self.cbms = CBMSMemory(str(self.memory_dir))
        self.learning_memory = LearningMemory()
        self.pattern_threshold = 3  # Minimum occurrences to establish pattern
        self.confidence_decay = 0.95  # Confidence decay rate
        self._init_database()
        self._load_existing_knowledge()

    def _init_database(self):
        """Initialize SQLite database for persistent learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables for persistent storage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                content TEXT,
                frequency INTEGER,
                confidence REAL,
                success_rate REAL,
                created_at TIMESTAMP,
                last_used TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                response TEXT,
                confidence REAL,
                quality_score REAL,
                timestamp TIMESTAMP,
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concept_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_from TEXT,
                concept_to TEXT,
                strength REAL,
                evidence_count INTEGER,
                created_at TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id TEXT PRIMARY KEY,
                content TEXT,
                concept TEXT,
                references TEXT,
                confidence REAL,
                access_count INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def _load_existing_knowledge(self):
        """Load existing knowledge from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Load patterns
        cursor.execute("""
            SELECT pattern_type, content, frequency, confidence, success_rate, last_used
            FROM patterns
            WHERE confidence > 0.3
            ORDER BY frequency DESC
            LIMIT 1000
        """)

        for row in cursor.fetchall():
            pattern = KnowledgePattern(
                pattern_type=row[0],
                content=row[1],
                frequency=row[2],
                confidence=row[3],
                success_rate=row[4],
                last_used=row[5] if isinstance(row[5], float) else time.time()
            )
            self.learning_memory.learned_patterns.append(pattern)

        # Load concept links
        cursor.execute("""
            SELECT concept_from, concept_to, strength
            FROM concept_links
            WHERE strength > 0.2
        """)

        for row in cursor.fetchall():
            self.learning_memory.concept_graph[row[0]].add(row[1])

        conn.close()

    def learn_from_interaction(self, query: str, response: Dict, feedback: Optional[float] = None) -> Dict:
        """Learn from a single interaction"""
        learning_result = {
            "patterns_extracted": [],
            "concepts_linked": [],
            "knowledge_created": [],
            "gaps_identified": []
        }

        # Record interaction
        self._record_interaction(query, response, feedback)

        # Extract patterns
        patterns = self._extract_patterns(query, response)
        learning_result["patterns_extracted"] = patterns

        # Update concept graph
        new_links = self._update_concept_graph(query, response)
        learning_result["concepts_linked"] = new_links

        # Generate new knowledge
        if feedback and feedback > 0.7:
            new_knowledge = self._generate_knowledge_chunk(query, response)
            if new_knowledge:
                learning_result["knowledge_created"].append(new_knowledge)

        # Identify gaps
        gaps = self._identify_knowledge_gaps(query, response)
        learning_result["gaps_identified"] = gaps

        # Active learning - generate questions to fill gaps
        if gaps:
            learning_result["suggested_queries"] = self._generate_learning_queries(gaps)

        # Update persistent storage
        self._persist_learning(learning_result)

        return learning_result

    def _record_interaction(self, query: str, response: Dict, feedback: Optional[float]):
        """Record interaction in history"""
        interaction = {
            "query": query,
            "response": response.get("response", ""),
            "confidence": response.get("confidence", 0.5),
            "timestamp": time.time(),
            "feedback": feedback
        }

        self.learning_memory.interaction_history.append(interaction)

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO interactions (query, response, confidence, quality_score, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            query,
            response.get("response", ""),
            response.get("confidence", 0.5),
            feedback or 0.5,
            datetime.now(),
            json.dumps({"reasoning_chain": len(response.get("reasoning_chain", []))})
        ))

        conn.commit()
        conn.close()

    def _extract_patterns(self, query: str, response: Dict) -> List[KnowledgePattern]:
        """Extract reusable patterns from interaction"""
        patterns = []

        # Query-Response patterns
        query_type = self._classify_query_type(query)
        response_structure = self._analyze_response_structure(response)

        # Check if this pattern exists
        pattern_key = f"{query_type}:{response_structure}"
        existing_pattern = self._find_pattern(pattern_key)

        if existing_pattern:
            existing_pattern.frequency += 1
            existing_pattern.last_used = time.time()
            if response.get("confidence", 0) > 0.7:
                existing_pattern.success_rate = (existing_pattern.success_rate * 0.9 + 0.1)
        else:
            # Create new pattern
            new_pattern = KnowledgePattern(
                pattern_type="query_response",
                content=pattern_key,
                confidence=response.get("confidence", 0.5),
                context_examples=[query]
            )
            self.learning_memory.learned_patterns.append(new_pattern)
            patterns.append(new_pattern)

        # Reasoning patterns
        if "reasoning_chain" in response:
            reasoning_patterns = self._extract_reasoning_patterns(response["reasoning_chain"])
            patterns.extend(reasoning_patterns)

        return patterns

    def _update_concept_graph(self, query: str, response: Dict) -> List[Tuple[str, str]]:
        """Update concept relationships"""
        new_links = []

        # Extract concepts from query and response
        query_concepts = self._extract_concepts(query)
        response_concepts = self._extract_concepts(response.get("response", ""))

        # Link query concepts to response concepts
        for q_concept in query_concepts:
            for r_concept in response_concepts:
                if q_concept != r_concept:
                    self.learning_memory.concept_graph[q_concept].add(r_concept)
                    new_links.append((q_concept, r_concept))

                    # Update database
                    self._update_concept_link(q_concept, r_concept)

        # Extract and link concepts from reasoning chain
        if "reasoning_chain" in response:
            chain_concepts = []
            for item in response["reasoning_chain"]:
                if isinstance(item, dict) and "concepts" in item:
                    chain_concepts.extend(item["concepts"])

            # Link sequential concepts in chain
            for i in range(len(chain_concepts) - 1):
                self.learning_memory.concept_graph[chain_concepts[i]].add(chain_concepts[i + 1])
                new_links.append((chain_concepts[i], chain_concepts[i + 1]))

        return new_links

    def _generate_knowledge_chunk(self, query: str, response: Dict) -> Optional[Dict]:
        """Generate new knowledge chunk from successful interaction"""
        if response.get("confidence", 0) < 0.7:
            return None

        # Create unique ID for chunk
        content = f"{query}:{response.get('response', '')}"
        chunk_id = "K" + hashlib.sha256(content.encode()).hexdigest()[:12].upper()

        # Extract key information
        concepts = self._extract_concepts(query + " " + response.get("response", ""))

        # Find related chunks
        related_chunks = []
        for concept in concepts[:3]:  # Top 3 concepts
            keys = build_keys(concept)
            matches = self.cbms.search_chunks(keys)
            for match in matches[:2]:  # Top 2 matches per concept
                if match.get("id") and match["id"] != chunk_id:
                    related_chunks.append(match["id"])

        # Create new chunk
        new_chunk = {
            "id": chunk_id,
            "content": response.get("response", ""),
            "concept": self._classify_concept(concepts),
            "created": datetime.now().isoformat(),
            "confidence": response.get("confidence", 0.5),
            "query": query,
            "references": list(set(related_chunks)),
            "learned_from": "interaction",
            "access_count": 0
        }

        # Save to CBMS
        chunk_path = self.memory_dir / "chunks" / f"{chunk_id}.json"
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(new_chunk, f, indent=2, ensure_ascii=False)

        # Update manifest
        self._update_manifest(new_chunk)

        # Store in database
        self._store_knowledge_chunk(new_chunk)

        return new_chunk

    def _identify_knowledge_gaps(self, query: str, response: Dict) -> List[str]:
        """Identify gaps in knowledge based on interaction"""
        gaps = []

        # Low confidence indicates potential gap
        if response.get("confidence", 1.0) < 0.5:
            gaps.append(f"Low confidence for: {query[:50]}")

        # Check for missing concepts
        query_concepts = self._extract_concepts(query)
        covered_concepts = set()

        if "reasoning_chain" in response:
            for item in response["reasoning_chain"]:
                if isinstance(item, dict) and "concepts" in item:
                    covered_concepts.update(item["concepts"])

        missing_concepts = set(query_concepts) - covered_concepts
        for concept in missing_concepts:
            gaps.append(f"Missing knowledge about: {concept}")
            self.learning_memory.knowledge_gaps.add(concept)

        # Analyze reflection for gaps
        if "reflection" in response and "identified_gaps" in response["reflection"]:
            gaps.extend(response["reflection"]["identified_gaps"])

        return gaps

    def _generate_learning_queries(self, gaps: List[str]) -> List[str]:
        """Generate queries to fill knowledge gaps"""
        queries = []

        for gap in gaps:
            if "Missing knowledge about:" in gap:
                concept = gap.replace("Missing knowledge about:", "").strip()
                queries.extend([
                    f"What is {concept}?",
                    f"How does {concept} work?",
                    f"What are examples of {concept}?"
                ])
            elif "Low confidence for:" in gap:
                original = gap.replace("Low confidence for:", "").strip()
                queries.append(f"Can you explain more about: {original}")

        return queries[:5]  # Limit to 5 queries

    def consolidate_knowledge(self) -> Dict:
        """Consolidate and optimize learned knowledge"""
        consolidation_result = {
            "patterns_consolidated": 0,
            "concepts_strengthened": 0,
            "chunks_merged": 0,
            "gaps_prioritized": []
        }

        # Consolidate similar patterns
        consolidated = self._consolidate_patterns()
        consolidation_result["patterns_consolidated"] = consolidated

        # Strengthen concept links
        strengthened = self._strengthen_concept_links()
        consolidation_result["concepts_strengthened"] = strengthened

        # Merge similar knowledge chunks
        merged = self._merge_similar_chunks()
        consolidation_result["chunks_merged"] = merged

        # Prioritize knowledge gaps
        prioritized = self._prioritize_gaps()
        consolidation_result["gaps_prioritized"] = prioritized

        return consolidation_result

    def _consolidate_patterns(self) -> int:
        """Merge similar patterns"""
        consolidated = 0
        patterns_by_type = defaultdict(list)

        for pattern in self.learning_memory.learned_patterns:
            patterns_by_type[pattern.pattern_type].append(pattern)

        for pattern_type, patterns in patterns_by_type.items():
            if len(patterns) < 2:
                continue

            # Find similar patterns
            to_merge = []
            for i in range(len(patterns)):
                for j in range(i + 1, len(patterns)):
                    similarity = self._pattern_similarity(patterns[i], patterns[j])
                    if similarity > 0.8:
                        to_merge.append((i, j))

            # Merge similar patterns
            merged_indices = set()
            for i, j in to_merge:
                if i not in merged_indices and j not in merged_indices:
                    # Merge j into i
                    patterns[i].frequency += patterns[j].frequency
                    patterns[i].confidence = max(patterns[i].confidence, patterns[j].confidence)
                    patterns[i].context_examples.extend(patterns[j].context_examples[:3])
                    merged_indices.add(j)
                    consolidated += 1

            # Remove merged patterns
            self.learning_memory.learned_patterns = [
                p for i, p in enumerate(self.learning_memory.learned_patterns)
                if i not in merged_indices
            ]

        return consolidated

    def _strengthen_concept_links(self) -> int:
        """Strengthen frequently co-occurring concepts"""
        strengthened = 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for concept, related in self.learning_memory.concept_graph.items():
            for related_concept in related:
                # Count co-occurrences
                cursor.execute("""
                    SELECT COUNT(*) FROM interactions
                    WHERE query LIKE ? AND response LIKE ?
                """, (f"%{concept}%", f"%{related_concept}%"))

                count = cursor.fetchone()[0]
                if count > self.pattern_threshold:
                    # Strengthen link
                    strength = min(1.0, count / 10.0)
                    self._update_concept_link(concept, related_concept, strength)
                    strengthened += 1

        conn.close()
        return strengthened

    def _merge_similar_chunks(self) -> int:
        """Merge highly similar knowledge chunks"""
        merged = 0

        # Load all chunks
        chunks = []
        chunk_dir = self.memory_dir / "chunks"
        if chunk_dir.exists():
            for chunk_file in chunk_dir.glob("K*.json"):
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunks.append(json.load(f))

        # Find similar chunks
        to_merge = []
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                similarity = self._chunk_similarity(chunks[i], chunks[j])
                if similarity > 0.9:
                    to_merge.append((i, j))

        # Merge similar chunks
        for i, j in to_merge:
            # Merge j into i
            chunks[i]["references"] = list(set(
                chunks[i].get("references", []) + chunks[j].get("references", [])
            ))
            chunks[i]["access_count"] = chunks[i].get("access_count", 0) + chunks[j].get("access_count", 0)

            # Delete chunk j
            chunk_path = self.memory_dir / "chunks" / f"{chunks[j]['id']}.json"
            if chunk_path.exists():
                chunk_path.unlink()
                merged += 1

        return merged

    def _prioritize_gaps(self) -> List[str]:
        """Prioritize knowledge gaps by importance"""
        gap_importance = {}

        for gap in self.learning_memory.knowledge_gaps:
            # Count how often this gap appears
            frequency = sum(1 for interaction in self.learning_memory.interaction_history
                          if gap.lower() in str(interaction).lower())
            gap_importance[gap] = frequency

        # Sort by importance
        prioritized = sorted(gap_importance.items(), key=lambda x: x[1], reverse=True)

        return [gap for gap, _ in prioritized[:10]]

    def generate_insights(self) -> List[str]:
        """Generate insights from learned patterns"""
        insights = []

        # Most successful patterns
        successful_patterns = sorted(
            self.learning_memory.learned_patterns,
            key=lambda p: p.success_rate * p.frequency,
            reverse=True
        )[:5]

        for pattern in successful_patterns:
            insights.append(f"Effective pattern: {pattern.content} (success: {pattern.success_rate:.2f})")

        # Strong concept relationships
        strong_links = []
        for concept, related in self.learning_memory.concept_graph.items():
            if len(related) > 3:
                strong_links.append(f"{concept} strongly connected to {len(related)} concepts")

        insights.extend(strong_links[:3])

        # Performance trends
        if self.learning_memory.performance_tracking:
            for metric, values in self.learning_memory.performance_tracking.items():
                if len(values) > 5:
                    trend = "improving" if values[-1] > values[0] else "declining"
                    insights.append(f"{metric} is {trend}")

        return insights

    # Helper methods

    def _classify_query_type(self, query: str) -> str:
        """Classify query into type"""
        query_lower = query.lower()

        if any(q in query_lower for q in ["what", "which", "who", "where", "when"]):
            return "factual"
        elif any(q in query_lower for q in ["how", "explain", "describe"]):
            return "explanatory"
        elif any(q in query_lower for q in ["why", "because", "reason"]):
            return "causal"
        else:
            return "general"

    def _analyze_response_structure(self, response: Dict) -> str:
        """Analyze response structure"""
        if "reasoning_chain" in response and len(response["reasoning_chain"]) > 2:
            return "complex_reasoning"
        elif response.get("confidence", 0) > 0.8:
            return "confident_direct"
        else:
            return "uncertain"

    def _find_pattern(self, pattern_key: str) -> Optional[KnowledgePattern]:
        """Find existing pattern by key"""
        for pattern in self.learning_memory.learned_patterns:
            if pattern.content == pattern_key:
                return pattern
        return None

    def _extract_reasoning_patterns(self, chain: List) -> List[KnowledgePattern]:
        """Extract patterns from reasoning chain"""
        patterns = []

        # Look for sequence patterns
        if len(chain) > 2:
            sequence = []
            for item in chain:
                if isinstance(item, dict):
                    if "synthesis" in item:
                        sequence.append("synthesis")
                    elif "validation" in item:
                        sequence.append("validation")
                    elif "hop" in item:
                        sequence.append("hop")

            if len(sequence) > 1:
                pattern_content = "->".join(sequence)
                pattern = KnowledgePattern(
                    pattern_type="reasoning_sequence",
                    content=pattern_content
                )
                patterns.append(pattern)

        return patterns

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract concepts from text"""
        words = re.findall(r'\b[A-Za-z]+\b', text.lower())
        stopwords = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were', 'to', 'of', 'for', 'in', 'with'}
        concepts = [w for w in words if w not in stopwords and len(w) > 2]
        return list(set(concepts))

    def _classify_concept(self, concepts: List[str]) -> str:
        """Classify main concept category"""
        if any(c in concepts for c in ["python", "code", "programming", "function", "class"]):
            return "programming"
        elif any(c in concepts for c in ["ai", "machine", "learning", "neural", "model"]):
            return "ai_ml"
        elif any(c in concepts for c in ["cbms", "chunk", "memory", "korean", "compression"]):
            return "cbms_system"
        else:
            return "general"

    def _update_concept_link(self, from_concept: str, to_concept: str, strength: float = None):
        """Update concept link in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if strength is None:
            # Increment evidence count
            cursor.execute("""
                INSERT INTO concept_links (concept_from, concept_to, strength, evidence_count, created_at)
                VALUES (?, ?, 0.5, 1, ?)
                ON CONFLICT(concept_from, concept_to) DO UPDATE SET
                    evidence_count = evidence_count + 1,
                    strength = MIN(1.0, strength + 0.1)
            """, (from_concept, to_concept, datetime.now()))
        else:
            cursor.execute("""
                UPDATE concept_links SET strength = ?
                WHERE concept_from = ? AND concept_to = ?
            """, (strength, from_concept, to_concept))

        conn.commit()
        conn.close()

    def _update_manifest(self, chunk: Dict):
        """Update CBMS manifest with new chunk"""
        manifest_path = self.memory_dir / "knowledge_manifest.json"

        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        else:
            manifest = {
                "version": "2.0",
                "total_chunks": 0,
                "chunk_index": {},
                "concepts": {}
            }

        # Update manifest
        manifest["chunk_index"][chunk["id"]] = {
            "concept": chunk["concept"],
            "created": chunk["created"],
            "confidence": chunk["confidence"]
        }

        if chunk["concept"] not in manifest["concepts"]:
            manifest["concepts"][chunk["concept"]] = []
        manifest["concepts"][chunk["concept"]].append(chunk["id"])

        manifest["total_chunks"] = len(manifest["chunk_index"])

        # Save updated manifest
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def _store_knowledge_chunk(self, chunk: Dict):
        """Store knowledge chunk in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO knowledge_chunks
            (id, content, concept, references, confidence, access_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk["id"],
            chunk["content"],
            chunk["concept"],
            json.dumps(chunk.get("references", [])),
            chunk["confidence"],
            chunk.get("access_count", 0),
            chunk["created"],
            datetime.now()
        ))

        conn.commit()
        conn.close()

    def _persist_learning(self, learning_result: Dict):
        """Persist learning results to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Store patterns
        for pattern in learning_result.get("patterns_extracted", []):
            cursor.execute("""
                INSERT OR REPLACE INTO patterns
                (pattern_type, content, frequency, confidence, success_rate, created_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern.pattern_type,
                pattern.content,
                pattern.frequency,
                pattern.confidence,
                pattern.success_rate,
                datetime.now(),
                pattern.last_used
            ))

        conn.commit()
        conn.close()

    def _pattern_similarity(self, p1: KnowledgePattern, p2: KnowledgePattern) -> float:
        """Calculate similarity between patterns"""
        if p1.pattern_type != p2.pattern_type:
            return 0.0

        # Simple string similarity
        content_sim = len(set(p1.content) & set(p2.content)) / max(len(p1.content), len(p2.content))

        # Context similarity
        context_sim = 0.0
        if p1.context_examples and p2.context_examples:
            common = set(p1.context_examples) & set(p2.context_examples)
            context_sim = len(common) / max(len(p1.context_examples), len(p2.context_examples))

        return 0.7 * content_sim + 0.3 * context_sim

    def _chunk_similarity(self, c1: Dict, c2: Dict) -> float:
        """Calculate similarity between chunks"""
        if c1.get("concept") != c2.get("concept"):
            return 0.0

        # Content similarity
        content1 = c1.get("content", "")
        content2 = c2.get("content", "")

        if content1 == content2:
            return 1.0

        # Simple word overlap
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 or not words2:
            return 0.0

        overlap = len(words1 & words2) / min(len(words1), len(words2))
        return overlap


if __name__ == "__main__":
    # Initialize learning pipeline
    learner = AGILearning(memory_dir=r"C:\Users\User\Desktop\AIONS_CBMS_RELEASE\memory")

    # Test learning from interaction
    test_query = "How does Korean compression improve CBMS performance?"
    test_response = {
        "response": "Korean compression reduces storage by 69.6% through syllable-like patterns",
        "confidence": 0.85,
        "reasoning_chain": [
            {"concepts": ["korean", "compression", "cbms"]},
            {"synthesis": "Key pattern matching enables efficient retrieval"}
        ]
    }

    print("Learning from interaction...")
    result = learner.learn_from_interaction(test_query, test_response, feedback=0.9)

    print(f"\nPatterns extracted: {len(result['patterns_extracted'])}")
    print(f"Concepts linked: {len(result['concepts_linked'])}")
    print(f"Knowledge created: {len(result['knowledge_created'])}")
    print(f"Gaps identified: {result['gaps_identified']}")

    # Consolidate knowledge
    print("\nConsolidating knowledge...")
    consolidation = learner.consolidate_knowledge()
    print(f"Patterns consolidated: {consolidation['patterns_consolidated']}")
    print(f"Concepts strengthened: {consolidation['concepts_strengthened']}")

    # Generate insights
    print("\nInsights:")
    insights = learner.generate_insights()
    for insight in insights:
        print(f"- {insight}")