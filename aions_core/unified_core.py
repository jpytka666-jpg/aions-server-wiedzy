"""
AIONS v2.0 - INTEGRATED SYSTEM
==============================
Complete integration of all AIONS v2.0 components
Maintains backward compatibility with v1.0

Author: AIONS Development Team
Date: 2025-09-10
Status: PRODUCTION READY
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

# Component availability flags
COMPONENTS_STATUS = {
    'core': False,
    'vector': False,
    'hybrid': False,
    'agent': False,
    'style': False,
    'monitor': False
}

# Try importing all components
try:
    from aions_reformed_integration import ReformedAIONS as AIONSReformed
    COMPONENTS_STATUS['core'] = True
except ImportError:
    print("⚠️ Core AIONS not available")

try:
    from aions_vector_enhancement import VectorEnhancement
    COMPONENTS_STATUS['vector'] = True
except ImportError as e:
    print(f"⚠️ Vector enhancement not available: {e}")
except Exception as e:
    print(f"⚠️ Vector enhancement error: {e}")

try:
    from aions_hybrid_retrieval import HybridRetriever
    COMPONENTS_STATUS['hybrid'] = True
except ImportError:
    print("⚠️ Hybrid retrieval not available")

try:
    from claude_aions_bridge import ClaudeAionsBridge
    COMPONENTS_STATUS['bridge'] = True
except ImportError:
    print("⚠️ Claude-AIONS Bridge not available")

try:
    from aions_agent_layer import TaskPlanner
    COMPONENTS_STATUS['agent'] = True
except ImportError:
    print("⚠️ Agent layer not available")

try:
    from aions_style_parameters import StyleController, StyleProfile
    COMPONENTS_STATUS['style'] = True
except ImportError:
    print("⚠️ Style parameters not available")

try:
    from aions_monitoring_dashboard import AIONSMonitor
    COMPONENTS_STATUS['monitor'] = True
except ImportError:
    print("⚠️ Monitoring dashboard not available")

try:
    from agi_existing_models import AGIExistingModels
    COMPONENTS_STATUS['gen_ai'] = True
except ImportError:
    print("⚠️ Generative AI models not available")
#     COMPONENTS_STATUS['monitor'] = True
# except ImportError:
#     print("⚠️ Monitoring dashboard not available")


class AIONSv2:
    """
    AIONS v2.0 - Unified Interface
    Integrates all enhancements while maintaining v1.0 compatibility
    """
    
    def __init__(self, 
                 enable_vector: bool = True,
                 enable_hybrid: bool = True,
                 enable_agent: bool = True,
                 enable_style: bool = True,
                 enable_monitoring: bool = True,
                 fallback_to_v1: bool = True):
        """
        Initialize AIONS v2.0
        
        Args:
            enable_vector: Enable vector search enhancement
            enable_hybrid: Enable hybrid retrieval
            enable_agent: Enable agent task execution
            enable_style: Enable style parameters
            enable_monitoring: Enable monitoring dashboard
            fallback_to_v1: Always fallback to v1.0 if v2.0 components fail
        """
        
        self.version = "2.0"
        self.fallback_to_v1 = fallback_to_v1
        self.components = {}
        
        # Initialize core (REQUIRED)
        if COMPONENTS_STATUS['core']:
            self.components['core'] = AIONSReformed()
            print("✅ Core AIONS v1.0 loaded")
        else:
            raise RuntimeError("AIONS v1.0 core is required but not available")
            
        # Initialize Phase 5: Smart Guardrail (Anti-Hallucination)
        try:
            from aions_smart_guardrail import SmartGuardrail
            self.components['guardrail'] = SmartGuardrail()
            print("✅ Smart Guardrail (CBMS-KR) loaded")
        except ImportError:
            print("⚠️ Smart Guardrail module missing")
        except Exception as e:
            print(f"⚠️ Smart Guardrail failed to load: {e}")
           # Initialize components
        self.components = {}
        
        # 1. Monitoring (First for logging)
        if enable_monitoring and COMPONENTS_STATUS['monitor']:
            try:
                self.components['monitor'] = AIONSMonitor()
                print("✅ Monitoring dashboard loaded")
            except Exception as e:
                print(f"❌ Failed to load monitor: {e}")
        
        # 2. Core (reformed v1.0)
        if COMPONENTS_STATUS['core']:
            try:
                self.components['core'] = AIONSReformed()
                print("✅ Core AIONS v1.0 loaded")
            except Exception as e:
                print(f"❌ Failed to load core: {e}")
                
        # 3. Vector Enhancement
        if enable_vector and COMPONENTS_STATUS['vector']:
            try:
                self.components['vector'] = VectorEnhancement()
                print("✅ Vector enhancement loaded")
            except Exception as e:
                print(f"❌ Failed to load vector: {e}")
                
        # 4. Hybrid Retrieval
        if enable_hybrid and COMPONENTS_STATUS['hybrid']:
            try:
                self.components['hybrid'] = HybridRetriever()
                print("✅ Hybrid retrieval loaded")
            except Exception as e:
                print(f"❌ Failed to load hybrid: {e}")

        # 5. Hybrid Bridge (Claude/Local LLM)
        if COMPONENTS_STATUS.get('bridge', False):
            try:
                self.components['bridge'] = ClaudeAionsBridge()
                print("✅ Claude-AIONS Bridge loaded")
            except Exception as e:
                print(f"❌ Failed to load bridge: {e}")
                
        # 6. Agent Layer
        if enable_agent and COMPONENTS_STATUS['agent']:
            try:
                self.components['agent'] = TaskPlanner()
                print("✅ Agent layer loaded")
            except Exception as e:
                print(f"❌ Failed to load agent: {e}")
                
        # 7. Generative AI
        if COMPONENTS_STATUS.get('gen_ai', False):
            try:
                # Use Singleton instance from hub if possible, otherwise create new
                from agi_existing_models import AGIExistingModels
                self.components['gen_ai'] = AGIExistingModels()
                print("✅ Generative AI (Modified Phi-3/Mistral) loaded")
            except Exception as e:
                print(f"❌ Failed to load Generative AI: {e}")
        
        # Statistics
        self.stats = {
            'total_queries': 0,
            'v1_fallbacks': 0,
            'vector_hits': 0,
            'hybrid_hits': 0,
            'agent_tasks': 0,
            'styled_responses': 0,
            'errors': []
        }
        
        print(f"\n{'='*50}")
        print(f"AIONS v{self.version} INITIALIZED")
        print(f"Components: {len(self.components)}/{len(COMPONENTS_STATUS)}")
        print(f"Fallback to v1.0: {'Enabled' if fallback_to_v1 else 'Disabled'}")
        print(f"{'='*50}\n")
    
    def process(self,
                query: str,
                mode: str = 'auto',
                style: Optional[StyleProfile] = None,
                task_mode: bool = False,
                **kwargs) -> Dict[str, Any]:
        """
        Process query with AIONS v2.0
        
        Args:
            query: User query
            mode: Processing mode ('auto', 'core', 'vector', 'hybrid')
            style: Optional style profile
            task_mode: Execute as task with agent
            **kwargs: Additional parameters
            
        Returns:
            Response dictionary
        """
        self.stats['total_queries'] += 1
        start_time = time.time()
        
        response = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'version': self.version,
            'mode': mode
        }
        
        try:
            # Task mode - use agent
            if task_mode and 'agent' in self.components:
                self.stats['agent_tasks'] += 1
                task_result = self.components['agent'].execute_task(query)
                
                response.update({
                    'status': 'success' if task_result.success else 'error',
                    'source': 'agent',
                    'task_id': task_result.task_id,
                    'steps_executed': task_result.steps_executed,
                    'results': task_result.results,
                    'execution_time': task_result.execution_time
                })
                
                return response
            
            # PHASE 5: GUARDRAIL CHECK (The Final Link)
            # Enforce deterministic grounding before any processing
            evidence_context = ""
            if 'guardrail' in self.components:
                check = self.components['guardrail'].check(query)
                if not check['allowed']:
                    # STRICT REFUSAL
                    response['status'] = 'refused'
                    response['error'] = 'Guardrail Block: No deterministic evidence found.'
                    response['answer'] = check['reason']
                    self.stats['errors'].append({'query': query, 'error': 'Guardrail Refusal'})
                    return response
                else:
                    # Inject evidence into context
                    evidence_context = check['evidence']
                    response['evidence_ids'] = check['evidence_ids']
                    response['evidence'] = evidence_context
                    # Pass evidence to downstream components via kwargs or context injection
                    # For now we append it to query if using purely core, 
                    # or handle it in specific components if they support it.
                    # Simple strategy: Prepend to query for the LLM
                    # query = f"CONTEXT:\n{evidence_context}\n\nQUERY: {query}" 
                    # (But this might confuse vector search? Better to keep separate)
                    kwargs['evidence'] = evidence_context

            # Select processing mode
            
            # Process with selected mode
            if mode == 'hybrid' and 'hybrid' in self.components:
                self.stats['hybrid_hits'] += 1
                result = self.components['hybrid'].process(query)
                response.update(result)
                
            elif mode == 'vector' and 'vector' in self.components:
                self.stats['vector_hits'] += 1
                result = self.components['vector'].search(query, hybrid=True)
                response.update(result)
                
            else:
                # Fallback to core
                if self.fallback_to_v1 or mode == 'core':
                    self.stats['v1_fallbacks'] += 1
                    
                    # Try Generative AI first if available (The Voice)
                    if 'gen_ai' in self.components:
                         # Use generated response
                         gen_result = self.components['gen_ai'].process(query)
                         response['answer'] = gen_result['response']
                         response['model'] = gen_result['model']
                         response['latency_ms'] = gen_result['latency_ms']
                         response['gen_ai_used'] = True
                    else:
                        # Fallback to legacy rule-based system
                        if hasattr(self.components['core'], 'process'):
                            result = self.components['core'].process(query)
                        else:
                            result = self.components['core'].query(query)
                        response.update(result)
                else:
                    response['status'] = 'error'
                    response['error'] = f"Mode '{mode}' not available"
            
            # Apply style if requested
            if style and 'style' in self.components and 'answer' in response:
                self.stats['styled_responses'] += 1
                self.components['style'].set_profile(style)
                original_answer = response['answer']
                styled_answer = self.components['style'].apply_style(original_answer)
                
                response['answer'] = styled_answer
                response['style_applied'] = style.value
                response['original_answer'] = original_answer
            
        except Exception as e:
            self.stats['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'error': str(e)
            })
            
            # Fallback to v1.0 on error
            if self.fallback_to_v1:
                try:
                    self.stats['v1_fallbacks'] += 1
                    if hasattr(self.components['core'], 'process'):
                        result = self.components['core'].process(query)
                    else:
                        result = self.components['core'].query(query)
                    response.update(result)
                    response['fallback_used'] = True
                except Exception as fallback_error:
                    response['status'] = 'error'
                    response['error'] = str(fallback_error)
            else:
                response['status'] = 'error'
                response['error'] = str(e)
        
        # Add timing
        response['response_time'] = time.time() - start_time
        
        # Log if monitoring enabled
        if 'monitor' in self.components:
            self.components['monitor'].query_log.append({
                'timestamp': response['timestamp'],
                'query': query,
                'mode': mode,
                'response_time': response['response_time'],
                'status': response.get('status', 'unknown')
            })
        
        return response
    
    def _should_use_hybrid(self, query: str) -> bool:
        """Determine if hybrid retrieval should be used"""
        # Use hybrid for complex or research queries
        indicators = ['explain', 'describe', 'how does', 'what is the relationship',
                     'compare', 'difference between', 'research', 'find information']
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in indicators)
    
    def _should_use_vector(self, query: str) -> bool:
        """Determine if vector search should be used"""
        # Use vector for semantic similarity queries
        indicators = ['similar to', 'like', 'related to', 'about',
                     'concerning', 'regarding', 'find', 'search']
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in indicators)
    
    def execute_task(self, goal: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute task using agent layer"""
        if 'agent' not in self.components:
            return {
                'status': 'error',
                'error': 'Agent layer not available'
            }
        
        self.stats['agent_tasks'] += 1
        task_result = self.components['agent'].execute_task(goal, context)
        
        return {
            'task_id': task_result.task_id,
            'goal': task_result.goal,
            'success': task_result.success,
            'steps_executed': task_result.steps_executed,
            'results': task_result.results,
            'execution_time': task_result.execution_time,
            'audit_log': task_result.audit_log
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Get system health status"""
        if 'monitor' in self.components:
            return self.components['monitor'].health_check()
        
        # Basic health check without monitor
        return {
            'timestamp': datetime.now().isoformat(),
            'version': self.version,
            'components_loaded': list(self.components.keys()),
            'stats': self.stats,
            'status': 'operational'
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        stats = self.stats.copy()
        
        # Add component-specific stats
        if 'vector' in self.components:
            stats['vector_stats'] = self.components['vector'].get_stats()
        
        if 'hybrid' in self.components:
            stats['hybrid_stats'] = self.components['hybrid'].get_stats()
        
        if 'style' in self.components:
            stats['style_stats'] = self.components['style'].get_stats()
        
        return stats
    
    def benchmark(self, queries: List[str] = None) -> Dict[str, Any]:
        """Run performance benchmark"""
        if 'monitor' not in self.components:
            return {'error': 'Monitoring not available'}
        
        if queries is None:
            queries = [
                "What is the capital of France?",
                "How to write hello world in Python?",
                "What's 25 * 4?",
                "Explain DNA structure",
                "Cześć, jak się masz?"
            ]
        
        metrics = self.components['monitor'].benchmark_performance(queries)
        
        if metrics:
            return {
                'avg_response_time_ms': metrics.avg_response_time * 1000,
                'p95_response_time_ms': metrics.p95_response_time * 1000,
                'p99_response_time_ms': metrics.p99_response_time * 1000,
                'success_rate': metrics.success_rate,
                'total_queries': metrics.total_queries
            }
        
        return {'error': 'Benchmark failed'}


def interactive_demo():
    """Interactive demonstration of AIONS v2.0"""
    print("\n" + "="*70)
    print(" "*25 + "AIONS v2.0 DEMO")
    print("="*70)
    
    # Initialize AIONS v2.0
    print("\nInitializing AIONS v2.0...")
    aions = AIONSv2()
    
    # Demo queries
    demo_queries = [
        ("Basic Math", "What is 15 + 27?", {}),
        ("Geography", "What is the capital of Poland?", {}),
        ("Code Generation", "Write a Python function to calculate factorial", {}),
        ("Polish Language", "Cześć! Jak się masz?", {}),
        ("Styled Response", "Explain what DNA is", {'style': StyleProfile.FRIENDLY}),
        ("Task Execution", "Search for information about Python", {'task_mode': True})
    ]
    
    print("\n" + "-"*70)
    print("RUNNING DEMO QUERIES")
    print("-"*70)
    
    for category, query, options in demo_queries:
        print(f"\n📝 {category}: {query}")
        
        response = aions.process(query, **options)
        
        print(f"   Mode: {response.get('mode', 'unknown')}")
        print(f"   Source: {response.get('source', 'unknown')}")
        print(f"   Time: {response.get('response_time', 0)*1000:.1f}ms")
        
        if 'answer' in response:
            answer = response['answer'][:200]
            print(f"   Answer: {answer}...")
        elif 'results' in response:
            print(f"   Results: {len(response['results'])} items")
    
    # Show statistics
    print("\n" + "-"*70)
    print("SYSTEM STATISTICS")
    print("-"*70)
    
    stats = aions.get_stats()
    print(f"Total Queries: {stats['total_queries']}")
    print(f"V1 Fallbacks: {stats['v1_fallbacks']}")
    print(f"Vector Hits: {stats['vector_hits']}")
    print(f"Hybrid Hits: {stats['hybrid_hits']}")
    print(f"Agent Tasks: {stats['agent_tasks']}")
    print(f"Styled Responses: {stats['styled_responses']}")
    
    # Health check
    print("\n" + "-"*70)
    print("HEALTH CHECK")
    print("-"*70)
    
    health = aions.health_check()
    print(f"Status: {health.get('status', 'unknown').upper()}")
    print(f"Components: {', '.join(health.get('components_loaded', []))}")
    
    print("\n✅ AIONS v2.0 Demo Complete!")
    print("="*70)
    
    return aions


if __name__ == "__main__":
    # Run interactive demo
    aions = interactive_demo()
    
    # Optional: Interactive mode
    print("\n💡 Enter 'quit' to exit, or type your queries:")
    
    while True:
        try:
            user_input = input("\n> ")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            # Process query
            response = aions.process(user_input, mode='auto')
            
            if 'answer' in response:
                print(f"\n{response['answer']}")
            else:
                print(f"\nResponse: {json.dumps(response, indent=2)}")
            
            print(f"\n[Time: {response.get('response_time', 0)*1000:.1f}ms]")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")