#!/usr/bin/env python3
"""
Evaluator Engine - Performance scoring and quality assessment for AIONS Reactor
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import statistics

class PerformanceEvaluator:
    """Evaluates and scores AIONS Reactor performance"""
    
    def __init__(self, reports_path="reports"):
        self.reports_path = Path(reports_path)
        self.reports_path.mkdir(exist_ok=True)
        self.scoreboard_file = self.reports_path / "scoreboard.csv"
        self.initialize_scoreboard()
    
    def initialize_scoreboard(self):
        """Initialize scoreboard CSV if it doesn't exist"""
        if not self.scoreboard_file.exists():
            with open(self.scoreboard_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'goal_id', 'round', 'latency_ms', 'direct_rate', 
                    'quality_score', 'concepts_used', 'skills_created', 'enhancement_score', 
                    'notes', 'total_score'
                ])
    
    def evaluate_reactor_run(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate complete reactor run and generate scores"""
        
        evaluation = {
            "timestamp": datetime.now().isoformat(),
            "goal_id": results.get("goal_id", "unknown"),
            "total_rounds": len(results.get("rounds", [])),
            "skills_created": len(results.get("skills_created", [])),
            "metrics": {}
        }
        
        # Analyze all rounds
        round_metrics = []
        for round_result in results.get("rounds", []):
            round_eval = self.evaluate_round(round_result)
            round_metrics.append(round_eval)
        
        if round_metrics:
            # Calculate aggregate metrics
            evaluation["metrics"] = {
                "avg_latency_ms": statistics.mean([r["avg_task_latency"] for r in round_metrics]),
                "direct_cbms_rate": statistics.mean([r["direct_rate"] for r in round_metrics]),
                "avg_quality_score": statistics.mean([r["avg_quality"] for r in round_metrics]),
                "total_concepts_used": sum([r["concepts_used"] for r in round_metrics]),
                "enhancement_effectiveness": statistics.mean([r["enhancement_score"] for r in round_metrics]),
                "consistency_score": 1.0 - statistics.stdev([r["avg_quality"] for r in round_metrics]) if len(round_metrics) > 1 else 1.0
            }
        
        # Calculate overall score (0-100)
        overall_score = self.calculate_overall_score(evaluation["metrics"])
        evaluation["overall_score"] = overall_score
        evaluation["grade"] = self.get_performance_grade(overall_score)
        
        return evaluation
    
    def evaluate_round(self, round_result: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate single round performance"""
        tasks = round_result.get("tasks", [])
        
        if not tasks:
            return {"avg_task_latency": 0, "direct_rate": 0, "avg_quality": 0, "concepts_used": 0, "enhancement_score": 0}
        
        # Calculate task metrics
        latencies = []
        direct_responses = 0
        quality_scores = []
        total_concepts = 0
        enhancement_scores = []
        
        for task in tasks:
            # Parse timestamp to calculate latency
            start = datetime.fromisoformat(task["start_time"])
            end = datetime.fromisoformat(task["end_time"])
            latency_ms = (end - start).total_seconds() * 1000
            latencies.append(latency_ms)
            
            result = task.get("result", {})
            
            # Check if response was direct from CBMS
            if result.get("source") in ["smart_cbms", "graph_enhanced_cbms"]:
                direct_responses += 1
            
            # Quality scoring
            quality = self.score_task_quality(result)
            quality_scores.append(quality)
            
            # Count concepts used
            concepts_used = len(result.get("concepts_used", []))
            total_concepts += concepts_used
            
            # Enhancement score
            enhancement = result.get("enhancement_score", 0)
            enhancement_scores.append(enhancement)
        
        return {
            "avg_task_latency": statistics.mean(latencies) if latencies else 0,
            "direct_rate": direct_responses / len(tasks),
            "avg_quality": statistics.mean(quality_scores) if quality_scores else 0,
            "concepts_used": total_concepts,
            "enhancement_score": statistics.mean(enhancement_scores) if enhancement_scores else 0
        }
    
    def score_task_quality(self, task_result: Dict[str, Any]) -> float:
        """Score individual task quality (0-1)"""
        score = 0.0
        
        # Base score from source quality
        quality = task_result.get("quality", "basic")
        if quality == "enhanced":
            score += 0.4
        elif quality == "direct":
            score += 0.3
        elif quality == "basic_enhanced":
            score += 0.25
        else:
            score += 0.1
        
        # Content length bonus
        content = task_result.get("content", "")
        if len(content) > 200:
            score += 0.2
        elif len(content) > 100:
            score += 0.1
        
        # Concepts usage bonus
        concepts_used = len(task_result.get("concepts_used", []))
        if concepts_used >= 5:
            score += 0.2
        elif concepts_used >= 3:
            score += 0.15
        elif concepts_used >= 1:
            score += 0.1
        
        # Enhancement bonus
        enhancement_score = task_result.get("enhancement_score", 0)
        score += enhancement_score * 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall performance score (0-100)"""
        if not metrics:
            return 0.0
        
        # Weighted scoring components
        latency_score = max(0, 100 - metrics.get("avg_latency_ms", 1000) / 10)  # Lower is better
        direct_rate_score = metrics.get("direct_cbms_rate", 0) * 100
        quality_score = metrics.get("avg_quality_score", 0) * 100
        concepts_score = min(metrics.get("total_concepts_used", 0) * 2, 100)  # Up to 50 concepts = 100 points
        enhancement_score = metrics.get("enhancement_effectiveness", 0) * 100
        consistency_score = metrics.get("consistency_score", 0) * 100
        
        # Weighted average
        weights = {
            "latency": 0.15,
            "direct_rate": 0.25,
            "quality": 0.25,
            "concepts": 0.15,
            "enhancement": 0.10,
            "consistency": 0.10
        }
        
        overall = (
            latency_score * weights["latency"] +
            direct_rate_score * weights["direct_rate"] +
            quality_score * weights["quality"] +
            concepts_score * weights["concepts"] +
            enhancement_score * weights["enhancement"] +
            consistency_score * weights["consistency"]
        )
        
        return min(overall, 100.0)
    
    def get_performance_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 95:
            return "A+ EXCELLENT"
        elif score >= 90:
            return "A VERY GOOD"
        elif score >= 85:
            return "B+ GOOD"
        elif score >= 80:
            return "B SATISFACTORY"
        elif score >= 70:
            return "C+ ACCEPTABLE"
        elif score >= 60:
            return "C NEEDS IMPROVEMENT"
        else:
            return "F POOR"
    
    def save_to_scoreboard(self, evaluation: Dict[str, Any]):
        """Save evaluation results to scoreboard CSV"""
        metrics = evaluation.get("metrics", {})
        
        # Determine notes based on performance
        notes = []
        if evaluation.get("overall_score", 0) >= 90:
            notes.append("High performance")
        if metrics.get("direct_cbms_rate", 0) >= 0.9:
            notes.append("Excellent CBMS utilization")
        if metrics.get("enhancement_effectiveness", 0) >= 0.8:
            notes.append("Strong graph enhancement")
        if evaluation.get("skills_created", 0) >= 4:
            notes.append("Good skill generation")
        
        notes_str = "; ".join(notes) if notes else "Standard run"
        
        # Write to CSV
        with open(self.scoreboard_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                evaluation["timestamp"],
                evaluation["goal_id"],
                evaluation["total_rounds"],
                round(metrics.get("avg_latency_ms", 0), 2),
                round(metrics.get("direct_cbms_rate", 0), 3),
                round(metrics.get("avg_quality_score", 0), 3),
                metrics.get("total_concepts_used", 0),
                evaluation["skills_created"],
                round(metrics.get("enhancement_effectiveness", 0), 3),
                notes_str,
                round(evaluation["overall_score"], 2)
            ])
    
    def generate_performance_report(self, evaluation: Dict[str, Any]) -> str:
        """Generate human-readable performance report"""
        metrics = evaluation.get("metrics", {})
        
        report = f"""
=== AIONS REACTOR PERFORMANCE REPORT ===
Timestamp: {evaluation['timestamp']}
Goal ID: {evaluation['goal_id']}
Overall Score: {evaluation['overall_score']:.1f}/100 ({evaluation['grade']})

PERFORMANCE METRICS:
- Average Latency: {metrics.get('avg_latency_ms', 0):.1f}ms
- Direct CBMS Rate: {metrics.get('direct_cbms_rate', 0):.1%}
- Quality Score: {metrics.get('avg_quality_score', 0):.1%}
- Concepts Used: {metrics.get('total_concepts_used', 0)}
- Enhancement Effectiveness: {metrics.get('enhancement_effectiveness', 0):.1%}
- Consistency Score: {metrics.get('consistency_score', 0):.1%}

DELIVERABLES:
- Rounds Completed: {evaluation['total_rounds']}
- Skills Created: {evaluation['skills_created']}

PERFORMANCE ANALYSIS:
"""
        
        # Add analysis based on scores
        if evaluation["overall_score"] >= 90:
            report += "- EXCELLENT: System performing at optimal levels\n"
        elif evaluation["overall_score"] >= 80:
            report += "- GOOD: System performing well with minor optimization opportunities\n"
        else:
            report += "- NEEDS IMPROVEMENT: System requires optimization\n"
        
        if metrics.get("direct_cbms_rate", 0) >= 0.9:
            report += "- CBMS utilization is excellent (>90% direct responses)\n"
        elif metrics.get("direct_cbms_rate", 0) >= 0.7:
            report += "- CBMS utilization is good (>70% direct responses)\n"
        else:
            report += "- CBMS utilization needs improvement (<70% direct responses)\n"
        
        if metrics.get("enhancement_effectiveness", 0) >= 0.8:
            report += "- Graph enhancement is highly effective\n"
        elif metrics.get("enhancement_effectiveness", 0) >= 0.5:
            report += "- Graph enhancement shows moderate effectiveness\n"
        else:
            report += "- Graph enhancement needs optimization\n"
        
        report += "\n=== END REPORT ===\n"
        
        return report

def test_evaluator():
    """Test evaluator with mock data"""
    evaluator = PerformanceEvaluator()
    
    # Mock results data
    mock_results = {
        "goal_id": "TRADING_2025_BOOTSTRAP",
        "start_time": "2025-09-09T10:00:00",
        "end_time": "2025-09-09T10:30:00",
        "rounds": [
            {
                "round": 1,
                "start_time": "2025-09-09T10:00:00",
                "end_time": "2025-09-09T10:02:00",
                "tasks": [
                    {
                        "name": "Test task",
                        "start_time": "2025-09-09T10:00:00",
                        "end_time": "2025-09-09T10:00:01.500",
                        "result": {
                            "source": "graph_enhanced_cbms",
                            "content": "Test content with comprehensive analysis of trading strategies including RSI, MACD, and risk management techniques.",
                            "quality": "enhanced",
                            "concepts_used": ["trading", "rsi", "risk", "strategy"],
                            "enhancement_score": 0.8
                        }
                    }
                ]
            }
        ],
        "skills_created": ["skill1.json", "skill2.json"]
    }
    
    evaluation = evaluator.evaluate_reactor_run(mock_results)
    evaluator.save_to_scoreboard(evaluation)
    
    report = evaluator.generate_performance_report(evaluation)
    print("[TEST] Performance Report:")
    print(report)
    
    return evaluation

if __name__ == "__main__":
    test_evaluator()