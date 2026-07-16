#!/usr/bin/env python3
"""
AGI Unified System
Complete integration of all AGI components with CBMS
"""

import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import threading
import queue
import numpy as np

# Import all AGI components
try:
    from agi_core import AGICore
    from agi_learning import AGILearning
    from agi_evolution import AGIEvolution
    from agi_neural_backprop import AGINeuralBackprop
    from server.cbms_memory import CBMSMemory
    from server.korean_keys import build_keys
    from server.crla_core import run_crla
    import torch
    NEURAL_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some components not available: {e}")
    NEURAL_AVAILABLE = False
    import sys
    sys.path.append(str(Path(__file__).parent))


@dataclass
class AGIState:
    """Global state of AGI system"""
    mode: str = "hybrid"  # symbolic, neural, hybrid
    active_components: Dict[str, bool] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    session_history: List[Dict] = field(default_factory=list)
    learning_enabled: bool = True
    evolution_enabled: bool = True
    neural_enabled: bool = NEURAL_AVAILABLE
    current_confidence: float = 0.5
    total_interactions: int = 0


class AGIUnified:
    """Unified AGI system combining all components"""

    def __init__(self, memory_dir: str = None, config: Dict = None):
        self.memory_dir = Path(memory_dir) if memory_dir else Path("memory")
        self.config = config or self._default_config()
        self.state = AGIState()

        # Initialize components
        self._init_components()

        # Communication queues
        self.reasoning_queue = queue.Queue()
        self.learning_queue = queue.Queue()
        self.evolution_queue = queue.Queue()

        # Thread pool for parallel processing
        self.executor_threads = []
        self.running = False

        print("AGI Unified System initialized")
        self._report_status()

    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            "reasoning_depth": 3,
            "learning_threshold": 0.7,
            "evolution_interval": 10,
            "neural_weight": 0.5,
            "symbolic_weight": 0.5,
            "max_response_time": 5000,  # ms
            "enable_parallel": True,
            "auto_optimize": True
        }

    def _init_components(self):
        """Initialize all AGI components"""
        print("Initializing AGI components...")

        # Core reasoning
        try:
            self.reasoning_core = AGICore(memory_dir=str(self.memory_dir))
            self.state.active_components["reasoning"] = True
            print("✓ Reasoning core initialized")
        except Exception as e:
            print(f"✗ Reasoning core failed: {e}")
            self.state.active_components["reasoning"] = False

        # Learning pipeline
        try:
            self.learning_pipeline = AGILearning(memory_dir=str(self.memory_dir))
            self.state.active_components["learning"] = True
            print("✓ Learning pipeline initialized")
        except Exception as e:
            print(f"✗ Learning pipeline failed: {e}")
            self.state.active_components["learning"] = False

        # Evolution system
        try:
            self.evolution_system = AGIEvolution()
            self.state.active_components["evolution"] = True
            print("✓ Evolution system initialized")
        except Exception as e:
            print(f"✗ Evolution system failed: {e}")
            self.state.active_components["evolution"] = False

        # Neural backprop (if available)
        if NEURAL_AVAILABLE:
            try:
                self.neural_system = AGINeuralBackprop(memory_dir=str(self.memory_dir))
                self.state.active_components["neural"] = True
                print("✓ Neural backprop system initialized")
            except Exception as e:
                print(f"✗ Neural system failed: {e}")
                self.state.active_components["neural"] = False
                self.state.neural_enabled = False
        else:
            self.state.active_components["neural"] = False
            self.state.neural_enabled = False

        # CBMS memory
        try:
            self.cbms = CBMSMemory(memory_dir=str(self.memory_dir))
            self.state.active_components["cbms"] = True
            print(f"✓ CBMS memory initialized with {len(self.cbms.manifest.get('chunk_index', {}))} chunks")
        except Exception as e:
            print(f"✗ CBMS memory failed: {e}")
            self.state.active_components["cbms"] = False

    def process(self, query: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """Main processing entry point"""
        start_time = time.time()
        mode = mode or self.state.mode

        # Initialize response structure
        response = {
            "query": query,
            "mode": mode,
            "timestamp": start_time,
            "components_used": []
        }

        # Route to appropriate processing mode
        if mode == "symbolic":
            result = self._process_symbolic(query)
        elif mode == "neural" and self.state.neural_enabled:
            result = self._process_neural(query)
        elif mode == "hybrid":
            result = self._process_hybrid(query)
        else:
            result = self._process_fallback(query)

        # Add timing
        result["latency_ms"] = (time.time() - start_time) * 1000

        # Update state
        self.state.total_interactions += 1
        self.state.current_confidence = result.get("confidence", 0.5)

        # Trigger learning if enabled
        if self.state.learning_enabled and result.get("confidence", 0) > self.config["learning_threshold"]:
            self._trigger_learning(query, result)

        # Trigger evolution periodically
        if self.state.evolution_enabled and self.state.total_interactions % self.config["evolution_interval"] == 0:
            self._trigger_evolution()

        # Add to session history
        self.state.session_history.append({
            "query": query,
            "response": result.get("response", ""),
            "confidence": result.get("confidence", 0),
            "mode": mode,
            "timestamp": time.time()
        })

        return result

    def _process_symbolic(self, query: str) -> Dict[str, Any]:
        """Pure symbolic reasoning"""
        result = {"components_used": ["symbolic"]}

        if not self.state.active_components.get("reasoning"):
            return self._error_response("Reasoning component not available")

        # Use reasoning core
        reasoning_result = self.reasoning_core.reason(query, depth=self.config["reasoning_depth"])

        result.update({
            "response": reasoning_result["response"],
            "confidence": reasoning_result["confidence"],
            "reasoning_chain": reasoning_result["reasoning_chain"],
            "reflection": reasoning_result.get("reflection", {})
        })

        return result

    def _process_neural(self, query: str) -> Dict[str, Any]:
        """Pure neural processing"""
        result = {"components_used": ["neural"]}

        if not self.state.active_components.get("neural"):
            return self._error_response("Neural component not available")

        # Get knowledge chunks
        chunks = self._retrieve_chunks(query)

        # Process with neural system
        neural_result = self.neural_system.forward(query, chunks)

        # Extract response
        result.update({
            "response": self._decode_neural_response(neural_result),
            "confidence": neural_result["confidence"].item() if hasattr(neural_result["confidence"], "item") else neural_result["confidence"],
            "embeddings": neural_result.get("embeddings"),
            "reasoning_chain": neural_result.get("reasoning_chain", [])
        })

        return result

    def _process_hybrid(self, query: str) -> Dict[str, Any]:
        """Hybrid symbolic-neural processing"""
        result = {"components_used": ["hybrid"]}

        # Parallel processing of both approaches
        symbolic_result = None
        neural_result = None

        # Get symbolic result
        if self.state.active_components.get("reasoning"):
            symbolic_result = self.reasoning_core.reason(query, depth=self.config["reasoning_depth"])

        # Get neural result
        if self.state.active_components.get("neural"):
            chunks = self._retrieve_chunks(query)
            neural_result = self.neural_system.forward(query, chunks)

        # Combine results
        if symbolic_result and neural_result:
            # Weighted combination
            symbolic_weight = self.config["symbolic_weight"]
            neural_weight = self.config["neural_weight"]

            combined_confidence = (
                symbolic_result["confidence"] * symbolic_weight +
                neural_result["confidence"].item() * neural_weight
            )

            # Select response based on confidence
            if symbolic_result["confidence"] > neural_result["confidence"].item():
                primary_response = symbolic_result["response"]
                reasoning_type = "symbolic_dominant"
            else:
                primary_response = self._decode_neural_response(neural_result)
                reasoning_type = "neural_dominant"

            result.update({
                "response": primary_response,
                "confidence": combined_confidence,
                "reasoning_type": reasoning_type,
                "symbolic_confidence": symbolic_result["confidence"],
                "neural_confidence": neural_result["confidence"].item(),
                "reasoning_chain": symbolic_result.get("reasoning_chain", [])
            })

            result["components_used"].extend(["symbolic", "neural"])

        elif symbolic_result:
            result.update({
                "response": symbolic_result["response"],
                "confidence": symbolic_result["confidence"],
                "reasoning_chain": symbolic_result["reasoning_chain"]
            })
            result["components_used"].append("symbolic")

        elif neural_result:
            result.update({
                "response": self._decode_neural_response(neural_result),
                "confidence": neural_result["confidence"].item(),
                "reasoning_chain": neural_result.get("reasoning_chain", [])
            })
            result["components_used"].append("neural")

        else:
            return self._process_fallback(query)

        return result

    def _process_fallback(self, query: str) -> Dict[str, Any]:
        """Fallback processing when primary methods unavailable"""
        result = {"components_used": ["fallback"]}

        # Try direct CBMS retrieval
        if self.state.active_components.get("cbms"):
            chunks = self._retrieve_chunks(query)
            if chunks:
                response = self._synthesize_from_chunks(chunks)
                result.update({
                    "response": response,
                    "confidence": 0.3,
                    "method": "direct_retrieval"
                })
            else:
                result.update({
                    "response": "Unable to process query with available components",
                    "confidence": 0.1,
                    "method": "no_retrieval"
                })
        else:
            result.update({
                "response": "System components not available",
                "confidence": 0.0,
                "method": "system_error"
            })

        return result

    def _retrieve_chunks(self, query: str) -> List[Dict]:
        """Retrieve relevant chunks from CBMS"""
        if not self.state.active_components.get("cbms"):
            return []

        # Build Korean keys
        keys = build_keys(query)

        # Search chunks
        chunks = self.cbms.search_chunks(keys)

        return chunks[:10]  # Limit to top 10

    def _decode_neural_response(self, neural_output: Dict) -> str:
        """Decode neural output to text response"""
        # Simple placeholder - in production would use proper decoder
        if "response" in neural_output:
            return neural_output["response"]

        confidence = neural_output.get("confidence", 0)
        if hasattr(confidence, "item"):
            confidence = confidence.item()

        return f"Neural processing complete (confidence: {confidence:.2f})"

    def _synthesize_from_chunks(self, chunks: List[Dict]) -> str:
        """Synthesize response from chunks"""
        if not chunks:
            return "No relevant information found"

        # Extract content
        contents = [chunk.get("content", "") for chunk in chunks[:3]]

        # Simple synthesis
        return " ".join(contents[:2]) if contents else "Information retrieved but synthesis failed"

    def _trigger_learning(self, query: str, result: Dict):
        """Trigger learning from interaction"""
        if not self.state.active_components.get("learning"):
            return

        # Prepare learning task
        learning_task = {
            "query": query,
            "result": result,
            "timestamp": time.time()
        }

        # Queue for async processing
        self.learning_queue.put(learning_task)

        # Process immediately if not parallel
        if not self.config["enable_parallel"]:
            self._process_learning_queue()

    def _trigger_evolution(self):
        """Trigger evolution cycle"""
        if not self.state.active_components.get("evolution"):
            return

        # Prepare evolution task
        evolution_task = {
            "metrics": self.state.performance_metrics,
            "history": self.state.session_history[-100:],  # Last 100 interactions
            "timestamp": time.time()
        }

        # Queue for async processing
        self.evolution_queue.put(evolution_task)

        # Process immediately if not parallel
        if not self.config["enable_parallel"]:
            self._process_evolution_queue()

    def _process_learning_queue(self):
        """Process learning tasks"""
        while not self.learning_queue.empty():
            task = self.learning_queue.get()

            try:
                # Learn from interaction
                learning_result = self.learning_pipeline.learn_from_interaction(
                    task["query"],
                    task["result"],
                    task["result"].get("confidence", 0.5)
                )

                # Update neural system if available
                if self.state.active_components.get("neural") and task["result"].get("confidence", 0) > 0.7:
                    chunks = self._retrieve_chunks(task["query"])
                    self.neural_system.train_on_interaction(
                        task["query"],
                        chunks,
                        task["result"]["confidence"]
                    )

                print(f"Learning: {len(learning_result.get('patterns_extracted', []))} patterns extracted")

            except Exception as e:
                print(f"Learning error: {e}")

    def _process_evolution_queue(self):
        """Process evolution tasks"""
        while not self.evolution_queue.empty():
            task = self.evolution_queue.get()

            try:
                # Analyze performance
                analysis = self.evolution_system.analyze_performance({
                    "reasoning_quality": self.state.current_confidence,
                    "latency_ms": task.get("metrics", {}).get("latency", 100)
                })

                # Generate improvement plan
                plan = self.evolution_system.generate_improvement_plan()

                # Execute improvements
                if plan and self.config["auto_optimize"]:
                    improvements = self.evolution_system.execute_improvement(
                        plan,
                        self.reasoning_core,
                        self.learning_pipeline
                    )
                    print(f"Evolution: {len(improvements.get('improvements_applied', []))} improvements applied")

                # Adapt strategies
                self.evolution_system.adapt_strategies()

            except Exception as e:
                print(f"Evolution error: {e}")

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "response": message,
            "confidence": 0.0,
            "error": True,
            "components_used": ["error_handler"]
        }

    def _report_status(self):
        """Report system status"""
        print("\nSystem Status:")
        print("-" * 40)
        for component, active in self.state.active_components.items():
            status = "✓" if active else "✗"
            print(f"{status} {component.capitalize()}")
        print("-" * 40)
        print(f"Mode: {self.state.mode}")
        print(f"Neural available: {self.state.neural_enabled}")
        print(f"Learning enabled: {self.state.learning_enabled}")
        print(f"Evolution enabled: {self.state.evolution_enabled}")

    def start_parallel_processing(self):
        """Start parallel processing threads"""
        if self.running:
            return

        self.running = True

        # Learning thread
        if self.state.active_components.get("learning"):
            learning_thread = threading.Thread(target=self._learning_worker, daemon=True)
            learning_thread.start()
            self.executor_threads.append(learning_thread)

        # Evolution thread
        if self.state.active_components.get("evolution"):
            evolution_thread = threading.Thread(target=self._evolution_worker, daemon=True)
            evolution_thread.start()
            self.executor_threads.append(evolution_thread)

        print(f"Started {len(self.executor_threads)} parallel processing threads")

    def _learning_worker(self):
        """Worker thread for learning"""
        while self.running:
            try:
                task = self.learning_queue.get(timeout=1)
                # Process learning task
                self._process_learning_queue()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Learning worker error: {e}")

    def _evolution_worker(self):
        """Worker thread for evolution"""
        while self.running:
            try:
                task = self.evolution_queue.get(timeout=1)
                # Process evolution task
                self._process_evolution_queue()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Evolution worker error: {e}")

    def stop_parallel_processing(self):
        """Stop parallel processing threads"""
        self.running = False
        for thread in self.executor_threads:
            thread.join(timeout=2)
        self.executor_threads.clear()
        print("Parallel processing stopped")

    def set_mode(self, mode: str):
        """Set processing mode"""
        if mode in ["symbolic", "neural", "hybrid"]:
            self.state.mode = mode
            print(f"Mode set to: {mode}")
        else:
            print(f"Invalid mode: {mode}")

    def get_insights(self) -> Dict[str, Any]:
        """Get system insights"""
        insights = {
            "total_interactions": self.state.total_interactions,
            "current_confidence": self.state.current_confidence,
            "active_components": sum(self.state.active_components.values()),
            "mode": self.state.mode
        }

        # Add learning insights
        if self.state.active_components.get("learning"):
            insights["learning"] = self.learning_pipeline.generate_insights()

        # Add evolution assessment
        if self.state.active_components.get("evolution"):
            insights["evolution"] = self.evolution_system.generate_self_assessment()

        # Add neural statistics
        if self.state.active_components.get("neural"):
            insights["neural"] = {
                "parameters": sum(p.numel() for p in self.neural_system.parameters()),
                "device": str(next(self.neural_system.parameters()).device)
            }

        return insights

    def save_state(self, path: str = None):
        """Save system state"""
        path = path or str(self.memory_dir / "agi_unified_state.json")

        state_dict = {
            "mode": self.state.mode,
            "total_interactions": self.state.total_interactions,
            "performance_metrics": self.state.performance_metrics,
            "config": self.config,
            "timestamp": time.time()
        }

        with open(path, 'w') as f:
            json.dump(state_dict, f, indent=2)

        # Save component states
        if self.state.active_components.get("evolution"):
            self.evolution_system.save_state()

        if self.state.active_components.get("neural"):
            self.neural_system.save_checkpoint(str(self.memory_dir / "agi_neural.pth"))

        print(f"State saved to {path}")

    def load_state(self, path: str = None) -> bool:
        """Load system state"""
        path = path or str(self.memory_dir / "agi_unified_state.json")

        if Path(path).exists():
            with open(path, 'r') as f:
                state_dict = json.load(f)

            self.state.mode = state_dict.get("mode", "hybrid")
            self.state.total_interactions = state_dict.get("total_interactions", 0)
            self.state.performance_metrics = state_dict.get("performance_metrics", {})
            self.config.update(state_dict.get("config", {}))

            # Load component states
            if self.state.active_components.get("neural"):
                self.neural_system.load_checkpoint(str(self.memory_dir / "agi_neural.pth"))

            print(f"State loaded from {path}")
            return True

        return False


def run_interactive_session():
    """Run interactive AGI session"""
    print("\n" + "="*60)
    print("AGI UNIFIED SYSTEM - INTERACTIVE SESSION")
    print("="*60)

    # Initialize AGI
    agi = AGIUnified(memory_dir=r"C:\Users\User\Desktop\AIONS_CBMS_RELEASE\memory")

    # Start parallel processing
    if agi.config["enable_parallel"]:
        agi.start_parallel_processing()

    # Load previous state if exists
    agi.load_state()

    print("\nCommands:")
    print("  'mode [symbolic/neural/hybrid]' - Change processing mode")
    print("  'insights' - Show system insights")
    print("  'status' - Show system status")
    print("  'exit' - Exit session")
    print("\nEnter queries or commands:")

    try:
        while True:
            query = input("\n> ").strip()

            if not query:
                continue

            if query.lower() == "exit":
                break

            elif query.lower().startswith("mode "):
                mode = query.split()[1]
                agi.set_mode(mode)

            elif query.lower() == "insights":
                insights = agi.get_insights()
                print("\nSystem Insights:")
                print(json.dumps(insights, indent=2))

            elif query.lower() == "status":
                agi._report_status()

            else:
                # Process query
                print("\nProcessing...")
                result = agi.process(query)

                print(f"\nResponse: {result['response']}")
                print(f"Confidence: {result['confidence']:.2f}")
                print(f"Mode: {result['mode']}")
                print(f"Components: {', '.join(result['components_used'])}")
                print(f"Latency: {result['latency_ms']:.2f}ms")

    except KeyboardInterrupt:
        print("\nInterrupted")

    finally:
        # Save state
        agi.save_state()

        # Stop parallel processing
        if agi.config["enable_parallel"]:
            agi.stop_parallel_processing()

        print("\nSession ended")


if __name__ == "__main__":
    run_interactive_session()