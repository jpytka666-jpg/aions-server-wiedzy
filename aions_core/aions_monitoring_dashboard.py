"""
AIONS Monitoring Dashboard v1.0
===============================
Complete monitoring and testing suite for AIONS v2.0
Tracks performance, validates enhancements, ensures stability

Author: AIONS Development Team
Date: 2025-09-10
Status: PRODUCTION READY
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import statistics

# Import all AIONS components
try:
    from aions_reformed_integration import ReformedAIONS as AIONSReformed
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

try:
    from aions_vector_enhancement import VectorEnhancement
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False

try:
    from aions_hybrid_retrieval import HybridRetriever
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False

try:
    from aions_agent_layer import TaskPlanner
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

try:
    from aions_style_parameters import StyleController, StyleProfile
    STYLE_AVAILABLE = True
except ImportError:
    STYLE_AVAILABLE = False


@dataclass
class TestResult:
    """Individual test result"""
    test_name: str
    category: str
    passed: bool
    execution_time: float
    expected: Any
    actual: Any
    error: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    total_queries: int
    success_rate: float
    memory_usage_mb: float


class AIONSMonitor:
    """
    Comprehensive monitoring system for AIONS
    """
    
    def __init__(self, log_dir: str = "E:/AIONS_COMPLETE/monitoring"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize components
        self.components = {
            'core': CORE_AVAILABLE,
            'vector': VECTOR_AVAILABLE,
            'hybrid': HYBRID_AVAILABLE,
            'agent': AGENT_AVAILABLE,
            'style': STYLE_AVAILABLE
        }
        
        # Metrics storage
        self.response_times = []
        self.test_results = []
        self.errors = []
        self.query_log = []
        
    def health_check(self) -> Dict[str, Any]:
        """Check health of all components"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'status': 'healthy'
        }
        
        # Check each component
        for name, available in self.components.items():
            status = 'operational' if available else 'unavailable'
            health['components'][name] = {
                'status': status,
                'available': available
            }
            
            if not available and name == 'core':
                health['status'] = 'critical'
            elif not available:
                health['status'] = 'degraded' if health['status'] == 'healthy' else health['status']
        
        # Test core functionality if available
        if CORE_AVAILABLE:
            try:
                aions = AIONSReformed()
                result = aions.process("test")
                health['components']['core']['response_time'] = result.get('time', 'unknown')
            except Exception as e:
                health['components']['core']['status'] = 'error'
                health['components']['core']['error'] = str(e)
                health['overall_status'] = 'critical'
        
        return health
    
    def run_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("\n" + "="*60)
        print("AIONS COMPREHENSIVE TEST SUITE")
        print("="*60)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'categories': {}
        }
        
        # Core tests
        if CORE_AVAILABLE:
            core_results = self._test_core()
            test_results['categories']['core'] = core_results
            test_results['tests_run'] += len(core_results)
            test_results['tests_passed'] += sum(1 for r in core_results if r.passed)
            test_results['tests_failed'] += sum(1 for r in core_results if not r.passed)
        
        # Vector tests
        if VECTOR_AVAILABLE:
            vector_results = self._test_vector()
            test_results['categories']['vector'] = vector_results
            test_results['tests_run'] += len(vector_results)
            test_results['tests_passed'] += sum(1 for r in vector_results if r.passed)
            test_results['tests_failed'] += sum(1 for r in vector_results if not r.passed)
        
        # Hybrid tests
        if HYBRID_AVAILABLE:
            hybrid_results = self._test_hybrid()
            test_results['categories']['hybrid'] = hybrid_results
            test_results['tests_run'] += len(hybrid_results)
            test_results['tests_passed'] += sum(1 for r in hybrid_results if r.passed)
            test_results['tests_failed'] += sum(1 for r in hybrid_results if not r.passed)
        
        # Calculate success rate
        if test_results['tests_run'] > 0:
            test_results['success_rate'] = test_results['tests_passed'] / test_results['tests_run']
        else:
            test_results['success_rate'] = 0.0
        
        # Save results
        self._save_test_results(test_results)
        
        return test_results
    
    def _test_core(self) -> List[TestResult]:
        """Test core AIONS functionality"""
        results = []
        aions = AIONSReformed()
        
        # Test cases
        test_cases = [
            ("Math", "What is 5+7?", "12"),
            ("Geography", "Capital of France?", "Paris"),
            ("Polish", "Cześć!", "Cześć"),
            ("Code", "Hello world Python", "print"),
            ("Knowledge", "What is DNA?", "acid")
        ]
        
        for category, query, expected_keyword in test_cases:
            start = time.time()
            try:
                response = aions.process(query)
                answer = response.get('answer', '')
                passed = expected_keyword.lower() in answer.lower()
                
                results.append(TestResult(
                    test_name=f"Core_{category}",
                    category="core",
                    passed=passed,
                    execution_time=time.time() - start,
                    expected=expected_keyword,
                    actual=answer[:100]
                ))
            except Exception as e:
                results.append(TestResult(
                    test_name=f"Core_{category}",
                    category="core",
                    passed=False,
                    execution_time=time.time() - start,
                    expected=expected_keyword,
                    actual=None,
                    error=str(e)
                ))
        
        return results
    
    def _test_vector(self) -> List[TestResult]:
        """Test vector enhancement"""
        results = []
        vector = VectorEnhancement()
        
        # Test vector search
        test_queries = [
            ("Semantic_Search", "programming language", "Python"),
            ("Similar_Meaning", "country capital", "capital"),
            ("Knowledge_Retrieval", "mathematical operation", "calculate")
        ]
        
        for test_name, query, expected in test_queries:
            start = time.time()
            try:
                response = vector.search(query, k=5)
                success = response.get('status') == 'success'
                
                results.append(TestResult(
                    test_name=f"Vector_{test_name}",
                    category="vector",
                    passed=success,
                    execution_time=time.time() - start,
                    expected="success",
                    actual=response.get('status')
                ))
            except Exception as e:
                results.append(TestResult(
                    test_name=f"Vector_{test_name}",
                    category="vector",
                    passed=False,
                    execution_time=time.time() - start,
                    expected="success",
                    actual=None,
                    error=str(e)
                ))
        
        return results
    
    def _test_hybrid(self) -> List[TestResult]:
        """Test hybrid retrieval"""
        results = []
        hybrid = HybridRetriever()
        
        # Test different retrieval modes
        test_configs = [
            ("Keyword_Only", {"use_keyword": True, "use_vector": False}),
            ("Vector_Only", {"use_keyword": False, "use_vector": True}),
            ("Hybrid_Mode", {"use_keyword": True, "use_vector": True})
        ]
        
        for test_name, config in test_configs:
            start = time.time()
            try:
                query_results = hybrid.retrieve("Python programming", k=5, **config)
                passed = len(query_results) > 0
                
                results.append(TestResult(
                    test_name=f"Hybrid_{test_name}",
                    category="hybrid",
                    passed=passed,
                    execution_time=time.time() - start,
                    expected=">0 results",
                    actual=len(query_results)
                ))
            except Exception as e:
                results.append(TestResult(
                    test_name=f"Hybrid_{test_name}",
                    category="hybrid",
                    passed=False,
                    execution_time=time.time() - start,
                    expected=">0 results",
                    actual=None,
                    error=str(e)
                ))
        
        return results
    
    def benchmark_performance(self, queries: List[str], iterations: int = 10) -> PerformanceMetrics:
        """Benchmark system performance"""
        print("\n" + "="*60)
        print("PERFORMANCE BENCHMARK")
        print("="*60)
        
        if not CORE_AVAILABLE:
            print("❌ Core AIONS not available for benchmarking")
            return None
        
        aions = AIONSReformed()
        times = []
        successes = 0
        
        print(f"Running {iterations} iterations with {len(queries)} queries each...")
        
        for i in range(iterations):
            for query in queries:
                start = time.time()
                try:
                    response = aions.process(query)
                    elapsed = time.time() - start
                    times.append(elapsed)
                    
                    if response.get('status') == 'success' or 'answer' in response:
                        successes += 1
                        
                except Exception as e:
                    self.errors.append({
                        'timestamp': datetime.now().isoformat(),
                        'query': query,
                        'error': str(e)
                    })
            
            print(f"  Iteration {i+1}/{iterations} complete")
        
        # Calculate metrics
        if times:
            metrics = PerformanceMetrics(
                avg_response_time=statistics.mean(times),
                p95_response_time=sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0],
                p99_response_time=sorted(times)[int(len(times) * 0.99)] if len(times) > 1 else times[0],
                min_response_time=min(times),
                max_response_time=max(times),
                total_queries=len(times),
                success_rate=successes / len(times) if times else 0,
                memory_usage_mb=self._get_memory_usage()
            )
            
            # Save metrics
            self._save_metrics(metrics)
            
            return metrics
        
        return None
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def _save_test_results(self, results: Dict[str, Any]):
        """Save test results to file"""
        filename = os.path.join(
            self.log_dir,
            f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
    
    def _save_metrics(self, metrics: PerformanceMetrics):
        """Save performance metrics"""
        filename = os.path.join(
            self.log_dir,
            f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(metrics), f, indent=2)
    
    def generate_report(self) -> str:
        """Generate comprehensive monitoring report"""
        report = []
        report.append("="*60)
        report.append("AIONS v2.0 MONITORING REPORT")
        report.append("="*60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Health status
        health = self.health_check()
        report.append("SYSTEM HEALTH")
        report.append("-" * 40)
        report.append(f"Overall Status: {health['overall_status'].upper()}")
        report.append("\nComponent Status:")
        
        for component, status in health['components'].items():
            icon = "✅" if status['available'] else "❌"
            report.append(f"  {icon} {component}: {status['status']}")
        
        # Test results
        if self.test_results:
            latest_test = self.test_results[-1] if isinstance(self.test_results, list) else self.test_results
            report.append("\nLATEST TEST RESULTS")
            report.append("-" * 40)
            
            if isinstance(latest_test, dict):
                report.append(f"Tests Run: {latest_test.get('tests_run', 0)}")
                report.append(f"Tests Passed: {latest_test.get('tests_passed', 0)}")
                report.append(f"Tests Failed: {latest_test.get('tests_failed', 0)}")
                report.append(f"Success Rate: {latest_test.get('success_rate', 0):.1%}")
        
        # Performance metrics
        if self.response_times:
            report.append("\nPERFORMANCE METRICS")
            report.append("-" * 40)
            report.append(f"Average Response: {statistics.mean(self.response_times):.3f}s")
            report.append(f"Min Response: {min(self.response_times):.3f}s")
            report.append(f"Max Response: {max(self.response_times):.3f}s")
        
        # Errors
        if self.errors:
            report.append("\nRECENT ERRORS")
            report.append("-" * 40)
            for error in self.errors[-5:]:  # Last 5 errors
                report.append(f"  - {error.get('timestamp', 'N/A')}: {error.get('error', 'Unknown')[:50]}")
        
        report.append("\n" + "="*60)
        
        return "\n".join(report)


def main_monitoring():
    """Main monitoring dashboard"""
    print("\n" + "="*70)
    print(" "*20 + "AIONS v2.0 MONITORING DASHBOARD")
    print("="*70)
    
    monitor = AIONSMonitor()
    
    # 1. Health check
    print("\n[1/4] Running health check...")
    health = monitor.health_check()
    print(f"Overall status: {health['overall_status'].upper()}")
    
    # 2. Test suite
    print("\n[2/4] Running test suite...")
    test_results = monitor.run_test_suite()
    print(f"Tests passed: {test_results['tests_passed']}/{test_results['tests_run']}")
    
    # 3. Performance benchmark
    print("\n[3/4] Running performance benchmark...")
    test_queries = [
        "What is 5+7?",
        "Capital of France?",
        "Hello world in Python",
        "What is DNA?",
        "Cześć!"
    ]
    
    metrics = monitor.benchmark_performance(test_queries, iterations=3)
    
    if metrics:
        print(f"\nPerformance Results:")
        print(f"  Average response: {metrics.avg_response_time*1000:.1f}ms")
        print(f"  P95 response: {metrics.p95_response_time*1000:.1f}ms")
        print(f"  Success rate: {metrics.success_rate:.1%}")
        print(f"  Memory usage: {metrics.memory_usage_mb:.1f}MB")
    
    # 4. Generate report
    print("\n[4/4] Generating report...")
    report = monitor.generate_report()
    
    # Save report
    report_file = f"E:/AIONS_COMPLETE/monitoring/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Report saved to: {report_file}")
    
    # Display summary
    print("\n" + "="*70)
    print("MONITORING COMPLETE")
    print("="*70)
    print(report)
    
    return monitor


if __name__ == "__main__":
    main_monitoring()