#!/usr/bin/env python3
"""
AGI Core Reasoning Engine
Advanced General Intelligence implementation with multi-layer reasoning
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
import math

# Import existing CBMS components
try:
    from server.cbms_memory import CBMSMemory
    from server.korean_keys import build_keys
    from server.crla_core import run_crla
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent))
    from cbms_memory import CBMSMemory
    from korean_keys import build_keys
    from crla_core import run_crla


@dataclass
class Thought:
    """Represents a single reasoning step"""
    content: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    reasoning_type: str = "deductive"
    parent_thought: Optional['Thought'] = None
    child_thoughts: List['Thought'] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def add_child(self, thought: 'Thought'):
        self.child_thoughts.append(thought)
        thought.parent_thought = self


@dataclass
class Goal:
    """Represents a goal or subgoal in planning"""
    description: str
    priority: float
    status: str = "pending"  # pending, active, completed, failed
    prerequisites: List['Goal'] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    attempts: int = 0
    max_attempts: int = 3


@dataclass
class WorkingMemory:
    """Short-term memory for current reasoning context"""
    current_goal: Optional[Goal] = None
    active_thoughts: List[Thought] = field(default_factory=list)
    context_stack: List[Dict] = field(default_factory=list)
    attention_focus: Set[str] = field(default_factory=set)
    hypothesis_space: List[Dict] = field(default_factory=list)

    def push_context(self, context: Dict):
        self.context_stack.append(context)
        if len(self.context_stack) > 10:
            self.context_stack.pop(0)

    def get_recent_context(self, n: int = 3) -> List[Dict]:
        return self.context_stack[-n:] if self.context_stack else []


class AGICore:
    """Core AGI reasoning engine with multi-layer cognitive architecture"""

    def __init__(self, memory_dir: str = None):
        self.cbms = CBMSMemory(memory_dir) if memory_dir else CBMSMemory()
        self.working_memory = WorkingMemory()
        self.long_term_insights = []
        self.reasoning_chains = []
        self.meta_knowledge = self._load_meta_knowledge()
        self.performance_metrics = defaultdict(list)

    def _load_meta_knowledge(self) -> Dict:
        """Load meta-reasoning patterns and strategies"""
        return {
            "reasoning_strategies": [
                "deductive", "inductive", "abductive",
                "analogical", "causal", "counterfactual"
            ],
            "problem_decomposition": {
                "divide_conquer": self._divide_and_conquer,
                "means_end": self._means_end_analysis,
                "constraint_satisfaction": self._constraint_satisfaction
            },
            "uncertainty_handling": {
                "low": (0.0, 0.3),
                "medium": (0.3, 0.7),
                "high": (0.7, 1.0)
            }
        }

    def reason(self, query: str, depth: int = 3) -> Dict[str, Any]:
        """Main reasoning entry point with multi-layer processing"""
        start_time = time.time()

        # Initialize working memory for this query
        self.working_memory.push_context({
            "query": query,
            "timestamp": start_time,
            "depth": depth
        })

        # Phase 1: Understanding
        understanding = self._understand_query(query)

        # Phase 2: Planning
        plan = self._create_reasoning_plan(understanding)

        # Phase 3: Execution
        result = self._execute_reasoning_plan(plan, depth)

        # Phase 4: Reflection
        reflection = self._reflect_on_reasoning(result)

        # Phase 5: Learning
        self._learn_from_interaction(query, result, reflection)

        # Record performance
        self.performance_metrics["latency"].append(time.time() - start_time)
        self.performance_metrics["depth"].append(depth)

        return {
            "response": result["conclusion"],
            "reasoning_chain": result["chain"],
            "confidence": result["confidence"],
            "reflection": reflection,
            "latency_ms": (time.time() - start_time) * 1000
        }

    def _understand_query(self, query: str) -> Dict[str, Any]:
        """Deep understanding of query intent and context"""
        # Extract key concepts
        concepts = self._extract_concepts(query)

        # Identify query type
        query_type = self._classify_query_type(query)

        # Determine required reasoning depth
        complexity = self._assess_complexity(query)

        # Check for implicit assumptions
        assumptions = self._identify_assumptions(query)

        return {
            "concepts": concepts,
            "type": query_type,
            "complexity": complexity,
            "assumptions": assumptions,
            "original": query
        }

    def _create_reasoning_plan(self, understanding: Dict) -> List[Goal]:
        """Create execution plan based on understanding"""
        main_goal = Goal(
            description=f"Answer: {understanding['original']}",
            priority=1.0
        )

        subgoals = []

        # Decompose based on complexity
        if understanding["complexity"] > 0.7:
            # Complex query needs decomposition
            subgoals = self._decompose_complex_goal(main_goal, understanding)
        else:
            # Simple query - direct approach
            subgoals = [
                Goal(description="Retrieve relevant knowledge", priority=0.9),
                Goal(description="Synthesize response", priority=0.8)
            ]

        return [main_goal] + subgoals

    def _execute_reasoning_plan(self, plan: List[Goal], depth: int) -> Dict:
        """Execute reasoning plan with multi-hop inference"""
        reasoning_chain = []
        current_evidence = []

        for goal in plan:
            if goal.status == "completed":
                continue

            goal.status = "active"
            self.working_memory.current_goal = goal

            # Execute goal-specific reasoning
            if "retrieve" in goal.description.lower():
                evidence = self._retrieve_knowledge(goal)
                current_evidence.extend(evidence)

            elif "synthesize" in goal.description.lower():
                synthesis = self._synthesize_knowledge(current_evidence)
                reasoning_chain.append(synthesis)

            elif "hypothesize" in goal.description.lower():
                hypotheses = self._generate_hypotheses(current_evidence)
                self.working_memory.hypothesis_space = hypotheses

            elif "validate" in goal.description.lower():
                validation = self._validate_hypotheses()
                reasoning_chain.append(validation)

            goal.status = "completed"

        # Multi-hop reasoning if depth > 1
        if depth > 1:
            extended_chain = self._multi_hop_reasoning(reasoning_chain, depth)
            reasoning_chain.extend(extended_chain)

        # Calculate final confidence
        confidence = self._calculate_confidence(reasoning_chain)

        return {
            "chain": reasoning_chain,
            "conclusion": self._form_conclusion(reasoning_chain),
            "confidence": confidence,
            "evidence": current_evidence
        }

    def _multi_hop_reasoning(self, initial_chain: List, depth: int) -> List:
        """Perform multi-hop reasoning over knowledge graph"""
        extended_chain = []
        current_concepts = set()

        # Extract concepts from initial chain
        for item in initial_chain:
            if isinstance(item, dict) and "concepts" in item:
                current_concepts.update(item["concepts"])

        # Hop through related concepts
        for hop in range(depth - 1):
            related = self._find_related_concepts(current_concepts)
            if not related:
                break

            # Reason about relationships
            relationship_thought = Thought(
                content=f"Exploring relationships: {related}",
                confidence=0.7 - (hop * 0.1),
                reasoning_type="relational"
            )

            extended_chain.append({
                "hop": hop + 1,
                "thought": relationship_thought,
                "concepts": list(related)
            })

            current_concepts.update(related)

        return extended_chain

    def _reflect_on_reasoning(self, result: Dict) -> Dict:
        """Meta-cognitive reflection on reasoning process"""
        reflection = {
            "quality_assessment": self._assess_reasoning_quality(result),
            "identified_gaps": self._identify_knowledge_gaps(result),
            "alternative_paths": self._consider_alternatives(result),
            "confidence_factors": self._analyze_confidence_factors(result)
        }

        # Check for potential errors or biases
        if reflection["quality_assessment"] < 0.5:
            reflection["improvement_suggestions"] = self._suggest_improvements(result)

        return reflection

    def _learn_from_interaction(self, query: str, result: Dict, reflection: Dict):
        """Update knowledge and strategies based on interaction"""
        # Create new insight
        insight = {
            "query": query,
            "timestamp": time.time(),
            "reasoning_quality": reflection["quality_assessment"],
            "successful_strategies": self._extract_successful_strategies(result),
            "knowledge_gaps": reflection["identified_gaps"]
        }

        self.long_term_insights.append(insight)

        # Update performance metrics
        if reflection["quality_assessment"] > 0.7:
            self.performance_metrics["successful_queries"].append(query)

        # Identify patterns in failures
        if reflection["quality_assessment"] < 0.3:
            self._analyze_failure_patterns(query, result, reflection)

    # Helper methods for reasoning strategies

    def _divide_and_conquer(self, problem: Dict) -> List[Dict]:
        """Divide complex problem into subproblems"""
        subproblems = []

        # Simple heuristic division based on conjunctions
        if "and" in problem.get("query", ""):
            parts = problem["query"].split("and")
            for part in parts:
                subproblems.append({"query": part.strip(), "type": "subproblem"})
        else:
            # Single problem - no division needed
            subproblems = [problem]

        return subproblems

    def _means_end_analysis(self, current_state: Dict, goal_state: Dict) -> List[str]:
        """Analyze means to achieve end goal"""
        steps = []

        # Identify differences
        differences = self._identify_differences(current_state, goal_state)

        # Create steps to reduce differences
        for diff in differences:
            steps.append(f"Reduce difference: {diff}")

        return steps

    def _constraint_satisfaction(self, constraints: List[str]) -> Dict:
        """Satisfy given constraints"""
        satisfied = []
        violated = []

        for constraint in constraints:
            if self._check_constraint(constraint):
                satisfied.append(constraint)
            else:
                violated.append(constraint)

        return {
            "satisfied": satisfied,
            "violated": violated,
            "satisfaction_rate": len(satisfied) / len(constraints) if constraints else 0
        }

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[A-Za-z]+\b', text.lower())

        # Filter common words
        stopwords = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were', 'to', 'of', 'for', 'in', 'with'}
        concepts = [w for w in words if w not in stopwords and len(w) > 2]

        return list(set(concepts))

    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()

        if any(q in query_lower for q in ["what", "which", "who", "where", "when"]):
            return "factual"
        elif any(q in query_lower for q in ["how", "explain", "describe"]):
            return "explanatory"
        elif any(q in query_lower for q in ["why", "because", "reason"]):
            return "causal"
        elif any(q in query_lower for q in ["if", "would", "could", "should"]):
            return "hypothetical"
        elif any(q in query_lower for q in ["compare", "difference", "similar"]):
            return "comparative"
        else:
            return "general"

    def _assess_complexity(self, query: str) -> float:
        """Assess query complexity (0-1 scale)"""
        factors = {
            "length": len(query) / 500,  # Normalize by typical max length
            "clauses": len(re.findall(r'[,;]', query)) * 0.1,
            "technical_terms": len(re.findall(r'\b[A-Z][a-z]+[A-Z]\w*\b', query)) * 0.2,
            "nested_questions": len(re.findall(r'\?', query)) * 0.3
        }

        complexity = min(1.0, sum(factors.values()))
        return complexity

    def _identify_assumptions(self, query: str) -> List[str]:
        """Identify implicit assumptions in query"""
        assumptions = []

        # Check for existence assumptions
        if "the" in query.lower():
            entities = re.findall(r'the (\w+)', query.lower())
            for entity in entities:
                assumptions.append(f"Assumes existence of {entity}")

        # Check for causal assumptions
        if "because" in query.lower() or "since" in query.lower():
            assumptions.append("Contains causal assumptions")

        return assumptions

    def _decompose_complex_goal(self, goal: Goal, understanding: Dict) -> List[Goal]:
        """Decompose complex goal into subgoals"""
        subgoals = []

        # Based on query type
        if understanding["type"] == "comparative":
            subgoals.append(Goal(description="Retrieve first entity information", priority=0.9))
            subgoals.append(Goal(description="Retrieve second entity information", priority=0.9))
            subgoals.append(Goal(description="Compare entities", priority=0.8))

        elif understanding["type"] == "causal":
            subgoals.append(Goal(description="Identify cause candidates", priority=0.9))
            subgoals.append(Goal(description="Trace causal chain", priority=0.8))
            subgoals.append(Goal(description="Validate causation", priority=0.7))

        elif understanding["type"] == "hypothetical":
            subgoals.append(Goal(description="Generate hypotheses", priority=0.9))
            subgoals.append(Goal(description="Evaluate hypotheses", priority=0.8))
            subgoals.append(Goal(description="Select best hypothesis", priority=0.7))

        else:
            # Default decomposition
            subgoals.append(Goal(description="Gather relevant information", priority=0.9))
            subgoals.append(Goal(description="Analyze information", priority=0.8))
            subgoals.append(Goal(description="Synthesize conclusion", priority=0.7))

        return subgoals

    def _retrieve_knowledge(self, goal: Goal) -> List[str]:
        """Retrieve relevant knowledge from CBMS"""
        # Extract search terms from goal
        search_terms = self._extract_concepts(goal.description)

        evidence = []
        for term in search_terms:
            # Use CBMS to find relevant chunks
            keys = build_keys(term)
            matches = self.cbms.search_chunks(keys)

            for match in matches[:3]:  # Top 3 matches
                evidence.append(match.get("content", ""))

        return evidence

    def _synthesize_knowledge(self, evidence: List[str]) -> Dict:
        """Synthesize knowledge from evidence"""
        if not evidence:
            return {
                "synthesis": "Insufficient evidence for synthesis",
                "confidence": 0.1,
                "concepts": []
            }

        # Extract common themes
        all_concepts = []
        for item in evidence:
            all_concepts.extend(self._extract_concepts(item))

        # Find most frequent concepts
        concept_freq = defaultdict(int)
        for concept in all_concepts:
            concept_freq[concept] += 1

        top_concepts = sorted(concept_freq.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "synthesis": f"Key themes: {', '.join([c[0] for c in top_concepts])}",
            "confidence": min(1.0, len(evidence) * 0.2),
            "concepts": [c[0] for c in top_concepts],
            "evidence_count": len(evidence)
        }

    def _generate_hypotheses(self, evidence: List[str]) -> List[Dict]:
        """Generate hypotheses based on evidence"""
        hypotheses = []

        # Simple pattern-based hypothesis generation
        patterns = [
            "If {A} then {B}",
            "{A} causes {B}",
            "{A} is related to {B}",
            "{A} implies {B}"
        ]

        concepts = self._extract_concepts(" ".join(evidence))

        if len(concepts) >= 2:
            for i in range(min(3, len(concepts) - 1)):
                hypothesis = {
                    "statement": f"{concepts[i]} is related to {concepts[i+1]}",
                    "confidence": 0.5,
                    "supporting_evidence": len(evidence)
                }
                hypotheses.append(hypothesis)

        return hypotheses

    def _validate_hypotheses(self) -> Dict:
        """Validate hypotheses in working memory"""
        if not self.working_memory.hypothesis_space:
            return {"validation": "No hypotheses to validate", "confidence": 0}

        validated = []
        for hyp in self.working_memory.hypothesis_space:
            # Simple validation based on evidence count
            if hyp.get("supporting_evidence", 0) > 1:
                validated.append(hyp)

        return {
            "validation": f"Validated {len(validated)} of {len(self.working_memory.hypothesis_space)} hypotheses",
            "confidence": len(validated) / len(self.working_memory.hypothesis_space) if self.working_memory.hypothesis_space else 0,
            "validated_hypotheses": validated
        }

    def _form_conclusion(self, reasoning_chain: List) -> str:
        """Form final conclusion from reasoning chain"""
        if not reasoning_chain:
            return "Unable to form conclusion - no reasoning chain"

        # Collect all synthesis and validation results
        conclusions = []
        for item in reasoning_chain:
            if isinstance(item, dict):
                if "synthesis" in item:
                    conclusions.append(item["synthesis"])
                elif "validation" in item:
                    conclusions.append(item["validation"])

        if conclusions:
            return " ".join(conclusions)
        else:
            return "Reasoning complete but no definitive conclusion reached"

    def _calculate_confidence(self, reasoning_chain: List) -> float:
        """Calculate overall confidence in reasoning"""
        if not reasoning_chain:
            return 0.0

        confidences = []
        for item in reasoning_chain:
            if isinstance(item, dict) and "confidence" in item:
                confidences.append(item["confidence"])

        if confidences:
            # Weighted average with recency bias
            weights = [0.5 + 0.5 * (i / len(confidences)) for i in range(len(confidences))]
            weighted_sum = sum(c * w for c, w in zip(confidences, weights))
            return min(1.0, weighted_sum / sum(weights))

        return 0.5  # Default confidence

    def _find_related_concepts(self, concepts: Set[str]) -> Set[str]:
        """Find concepts related to given set"""
        related = set()

        for concept in concepts:
            # Search CBMS for related concepts
            keys = build_keys(concept)
            matches = self.cbms.search_chunks(keys)

            for match in matches[:2]:
                # Extract new concepts from matches
                new_concepts = self._extract_concepts(match.get("content", ""))
                related.update(new_concepts)

        # Remove already known concepts
        related -= concepts

        return related

    def _assess_reasoning_quality(self, result: Dict) -> float:
        """Assess quality of reasoning process"""
        factors = {
            "chain_length": min(1.0, len(result.get("chain", [])) / 5),
            "confidence": result.get("confidence", 0),
            "evidence_count": min(1.0, len(result.get("evidence", [])) / 3),
            "conclusion_quality": 0.7 if result.get("conclusion") and result["conclusion"] != "Unable to form conclusion" else 0.2
        }

        return sum(factors.values()) / len(factors)

    def _identify_knowledge_gaps(self, result: Dict) -> List[str]:
        """Identify gaps in knowledge that affected reasoning"""
        gaps = []

        if result.get("confidence", 1.0) < 0.5:
            gaps.append("Low confidence suggests missing knowledge")

        if len(result.get("evidence", [])) < 2:
            gaps.append("Insufficient evidence available")

        # Check for failed goals in working memory
        if self.working_memory.current_goal and self.working_memory.current_goal.status == "failed":
            gaps.append(f"Failed goal: {self.working_memory.current_goal.description}")

        return gaps

    def _consider_alternatives(self, result: Dict) -> List[str]:
        """Consider alternative reasoning paths"""
        alternatives = []

        # Could try different reasoning strategies
        used_strategies = set()
        for item in result.get("chain", []):
            if isinstance(item, dict) and "thought" in item:
                used_strategies.add(item["thought"].reasoning_type if hasattr(item["thought"], "reasoning_type") else "unknown")

        unused_strategies = set(self.meta_knowledge["reasoning_strategies"]) - used_strategies

        for strategy in unused_strategies:
            alternatives.append(f"Could try {strategy} reasoning")

        return alternatives

    def _analyze_confidence_factors(self, result: Dict) -> Dict:
        """Analyze factors affecting confidence"""
        return {
            "positive_factors": [
                f for f in ["multiple_evidence", "consistent_chain", "validated_hypotheses"]
                if self._check_positive_factor(f, result)
            ],
            "negative_factors": [
                f for f in ["insufficient_evidence", "contradictions", "high_uncertainty"]
                if self._check_negative_factor(f, result)
            ]
        }

    def _suggest_improvements(self, result: Dict) -> List[str]:
        """Suggest improvements for reasoning"""
        suggestions = []

        if len(result.get("evidence", [])) < 3:
            suggestions.append("Gather more evidence")

        if result.get("confidence", 0) < 0.5:
            suggestions.append("Validate reasoning with additional methods")

        if len(result.get("chain", [])) < 2:
            suggestions.append("Deepen reasoning with multi-hop inference")

        return suggestions

    def _extract_successful_strategies(self, result: Dict) -> List[str]:
        """Extract strategies that worked well"""
        successful = []

        for item in result.get("chain", []):
            if isinstance(item, dict) and item.get("confidence", 0) > 0.7:
                if "thought" in item and hasattr(item["thought"], "reasoning_type"):
                    successful.append(item["thought"].reasoning_type)

        return list(set(successful))

    def _analyze_failure_patterns(self, query: str, result: Dict, reflection: Dict):
        """Analyze patterns in reasoning failures"""
        failure_entry = {
            "query": query,
            "timestamp": time.time(),
            "quality": reflection["quality_assessment"],
            "gaps": reflection["identified_gaps"],
            "result_confidence": result.get("confidence", 0)
        }

        # Store for pattern analysis
        self.performance_metrics["failures"].append(failure_entry)

        # Look for patterns
        if len(self.performance_metrics["failures"]) >= 5:
            # Simple pattern: repeated knowledge gaps
            all_gaps = []
            for failure in self.performance_metrics["failures"][-5:]:
                all_gaps.extend(failure["gaps"])

            # Count gap frequencies
            gap_freq = defaultdict(int)
            for gap in all_gaps:
                gap_freq[gap] += 1

            # Identify recurring issues
            recurring = [gap for gap, freq in gap_freq.items() if freq >= 3]
            if recurring:
                print(f"WARNING: Recurring issues detected: {recurring}")

    def _identify_differences(self, current: Dict, goal: Dict) -> List[str]:
        """Identify differences between current and goal states"""
        differences = []

        for key in goal:
            if key not in current:
                differences.append(f"Missing: {key}")
            elif current[key] != goal[key]:
                differences.append(f"Mismatch: {key}")

        return differences

    def _check_constraint(self, constraint: str) -> bool:
        """Check if a constraint is satisfied"""
        # Simplified constraint checking
        return True  # Placeholder

    def _check_positive_factor(self, factor: str, result: Dict) -> bool:
        """Check for positive confidence factors"""
        if factor == "multiple_evidence":
            return len(result.get("evidence", [])) > 2
        elif factor == "consistent_chain":
            return len(result.get("chain", [])) > 1
        elif factor == "validated_hypotheses":
            for item in result.get("chain", []):
                if isinstance(item, dict) and "validated_hypotheses" in item:
                    return len(item["validated_hypotheses"]) > 0
        return False

    def _check_negative_factor(self, factor: str, result: Dict) -> bool:
        """Check for negative confidence factors"""
        if factor == "insufficient_evidence":
            return len(result.get("evidence", [])) < 2
        elif factor == "high_uncertainty":
            return result.get("confidence", 1.0) < 0.3
        return False


if __name__ == "__main__":
    # Initialize AGI Core using env or repo-local memory
    import os
    from pathlib import Path
    default_root = Path(__file__).resolve().parent
    mem_dir = os.environ.get('CBMS_MEMORY_DIR', str(default_root / 'memory'))
    agi = AGICore(memory_dir=mem_dir)

    # Test queries
    test_queries = [
        "What is the relationship between Korean compression and CBMS?",
        "How does the CRLA tournament system work?",
        "Explain the chain reaction learning mechanism"
    ]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")

        result = agi.reason(query, depth=3)

        print(f"\nResponse: {result['response']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Latency: {result['latency_ms']:.2f}ms")

        if result.get("reflection"):
            print(f"\nReflection:")
            print(f"- Quality: {result['reflection']['quality_assessment']:.2f}")
            print(f"- Gaps: {result['reflection']['identified_gaps']}")
