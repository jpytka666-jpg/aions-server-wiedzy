"""
AIONS Agent Layer v1.0
======================
Task execution with whitelisted tools and safety controls
SAFE WRAPPER - does not modify core AIONS

Author: AIONS Development Team  
Date: 2025-09-10
Status: PRODUCTION SAFE
"""

import os
import json
import time
import subprocess
import hashlib
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

# Import hybrid retrieval
try:
    from aions_hybrid_retrieval import HybridRetriever
    RETRIEVER_AVAILABLE = True
except ImportError:
    RETRIEVER_AVAILABLE = False
    print("⚠️ Hybrid retrieval not available")

# Import original AIONS
try:
    from aions_reformed_integration import AIONSReformed
    AIONS_AVAILABLE = True
except ImportError:
    AIONS_AVAILABLE = False


class RiskLevel(Enum):
    """Risk levels for tools"""
    SAFE = "safe"          # No confirmation needed
    LOW = "low"            # Log only
    MEDIUM = "medium"      # Confirm for sensitive operations
    HIGH = "high"          # Always confirm
    CRITICAL = "critical"  # Requires explicit approval


@dataclass
class Tool:
    """Tool definition"""
    name: str
    description: str
    risk: RiskLevel
    requires_confirmation: bool
    allowed_domains: List[str] = field(default_factory=list)
    max_executions: int = 10  # Per session limit


@dataclass 
class TaskStep:
    """Single step in task execution"""
    step_id: int
    tool_name: str
    parameters: Dict[str, Any]
    expected_output: str
    risk_level: RiskLevel
    requires_confirmation: bool = False
    
    
@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    goal: str
    steps_planned: int
    steps_executed: int
    success: bool
    results: List[Dict[str, Any]]
    error: Optional[str] = None
    execution_time: float = 0.0
    audit_log: List[Dict[str, Any]] = field(default_factory=list)


class ToolCatalog:
    """
    Whitelisted tools with safety controls
    """
    
    def __init__(self):
        self.tools = self._init_tools()
        self.execution_counts = {}
        self.blocked_operations = []
        
    def _init_tools(self) -> Dict[str, Tool]:
        """Initialize safe tool catalog"""
        return {
            # File operations
            "read_file": Tool(
                name="read_file",
                description="Read contents of a file",
                risk=RiskLevel.LOW,
                requires_confirmation=False
            ),
            "write_file": Tool(
                name="write_file", 
                description="Write content to a file",
                risk=RiskLevel.MEDIUM,
                requires_confirmation=True
            ),
            "list_directory": Tool(
                name="list_directory",
                description="List files in directory",
                risk=RiskLevel.SAFE,
                requires_confirmation=False
            ),
            
            # Web operations
            "web_search": Tool(
                name="web_search",
                description="Search the web for information",
                risk=RiskLevel.LOW,
                requires_confirmation=False,
                allowed_domains=["wikipedia.org", "docs.python.org", "stackoverflow.com"]
            ),
            
            # Code execution (sandboxed)
            "python_eval": Tool(
                name="python_eval",
                description="Evaluate Python expression (safe mode)",
                risk=RiskLevel.MEDIUM,
                requires_confirmation=True
            ),
            
            # Memory operations
            "memory_query": Tool(
                name="memory_query",
                description="Query AIONS memory",
                risk=RiskLevel.SAFE,
                requires_confirmation=False
            ),
            "memory_add": Tool(
                name="memory_add",
                description="Add knowledge to AIONS",
                risk=RiskLevel.LOW,
                requires_confirmation=False
            ),
            
            # System info (read-only)
            "system_info": Tool(
                name="system_info",
                description="Get system information",
                risk=RiskLevel.SAFE,
                requires_confirmation=False
            )
        }
    
    def is_allowed(self, tool_name: str) -> bool:
        """Check if tool is allowed"""
        return tool_name in self.tools
    
    def check_execution_limit(self, tool_name: str) -> bool:
        """Check if tool hasn't exceeded execution limit"""
        if tool_name not in self.tools:
            return False
            
        count = self.execution_counts.get(tool_name, 0)
        limit = self.tools[tool_name].max_executions
        
        return count < limit
    
    def record_execution(self, tool_name: str):
        """Record tool execution"""
        self.execution_counts[tool_name] = self.execution_counts.get(tool_name, 0) + 1


class SafeExecutor:
    """
    Safe execution environment for tools
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.aions = AIONSReformed() if AIONS_AVAILABLE else None
        self.retriever = HybridRetriever() if RETRIEVER_AVAILABLE else None
        
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool with safety checks
        """
        if self.dry_run:
            return {
                'status': 'dry_run',
                'tool': tool_name,
                'parameters': parameters,
                'result': f"[DRY RUN] Would execute {tool_name}"
            }
        
        # Tool implementations
        executors = {
            'read_file': self._read_file,
            'write_file': self._write_file,
            'list_directory': self._list_directory,
            'web_search': self._web_search,
            'python_eval': self._python_eval,
            'memory_query': self._memory_query,
            'memory_add': self._memory_add,
            'system_info': self._system_info
        }
        
        if tool_name not in executors:
            return {'status': 'error', 'error': f'Unknown tool: {tool_name}'}
        
        try:
            result = executors[tool_name](parameters)
            return {'status': 'success', 'result': result}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _read_file(self, params: Dict[str, Any]) -> str:
        """Safe file reading"""
        path = params.get('path', '')
        
        # Safety checks
        if not path or '..' in path or path.startswith('/'):
            raise ValueError("Invalid file path")
        
        # Limit to project directory
        safe_path = os.path.join('E:/AIONS_COMPLETE', path)
        
        if not os.path.exists(safe_path):
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read(10000)  # Limit size
            
        return content
    
    def _write_file(self, params: Dict[str, Any]) -> str:
        """Safe file writing"""
        path = params.get('path', '')
        content = params.get('content', '')
        
        # Safety checks
        if not path or '..' in path or path.startswith('/'):
            raise ValueError("Invalid file path")
        
        # Only allow writing to specific directories
        safe_dirs = ['outputs', 'temp', 'results']
        if not any(path.startswith(d) for d in safe_dirs):
            raise ValueError(f"Writing only allowed to: {safe_dirs}")
        
        safe_path = os.path.join('E:/AIONS_COMPLETE', path)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content[:100000])  # Limit size
            
        return f"Written {len(content)} bytes to {path}"
    
    def _list_directory(self, params: Dict[str, Any]) -> List[str]:
        """Safe directory listing"""
        path = params.get('path', '.')
        
        # Safety checks
        if '..' in path or path.startswith('/'):
            raise ValueError("Invalid directory path")
        
        safe_path = os.path.join('E:/AIONS_COMPLETE', path)
        
        if not os.path.isdir(safe_path):
            raise NotADirectoryError(f"Not a directory: {path}")
        
        files = os.listdir(safe_path)[:100]  # Limit results
        return files
    
    def _web_search(self, params: Dict[str, Any]) -> str:
        """Simulated web search (safe)"""
        query = params.get('query', '')
        
        # In production, use actual search API
        # For now, query AIONS knowledge
        if self.retriever:
            results = self.retriever.process(query)
            return json.dumps(results.get('context', []), indent=2)
        
        return f"[SIMULATED] Search results for: {query}"
    
    def _python_eval(self, params: Dict[str, Any]) -> Any:
        """Safe Python evaluation"""
        expression = params.get('expression', '')
        
        # Whitelist safe operations
        safe_builtins = {
            'len': len,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'list': list,
            'dict': dict,
            'str': str,
            'int': int,
            'float': float
        }
        
        # Remove dangerous operations
        if any(danger in expression for danger in ['import', 'exec', 'eval', '__', 'open']):
            raise ValueError("Unsafe operation detected")
        
        # Evaluate in restricted environment
        try:
            result = eval(expression, {"__builtins__": safe_builtins}, {})
            return str(result)
        except Exception as e:
            raise ValueError(f"Evaluation error: {e}")
    
    def _memory_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query AIONS memory"""
        query = params.get('query', '')
        
        if self.aions:
            return self.aions.process(query)
        
        return {'status': 'error', 'message': 'AIONS not available'}
    
    def _memory_add(self, params: Dict[str, Any]) -> str:
        """Add knowledge to AIONS"""
        knowledge = params.get('knowledge', '')
        source = params.get('source', 'agent')
        
        # Store in a file for now
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"E:/AIONS_COMPLETE/data/agent_knowledge_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'knowledge': knowledge,
                'source': source,
                'timestamp': timestamp
            }, f, indent=2)
        
        return f"Knowledge saved to {filename}"
    
    def _system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information (safe)"""
        import platform
        
        return {
            'platform': platform.platform(),
            'python': platform.python_version(),
            'processor': platform.processor(),
            'timestamp': datetime.now().isoformat()
        }


class TaskPlanner:
    """
    Plans and executes tasks using available tools
    """
    
    def __init__(self, require_confirmation: bool = True, dry_run: bool = False):
        self.catalog = ToolCatalog()
        self.executor = SafeExecutor(dry_run=dry_run)
        self.require_confirmation = require_confirmation
        self.aions = AIONSReformed() if AIONS_AVAILABLE else None
        
    def plan_task(self, goal: str, context: Optional[Dict] = None) -> List[TaskStep]:
        """
        Plan task steps based on goal
        """
        steps = []
        
        # Analyze goal with AIONS
        if self.aions:
            understanding = self.aions.process(goal)
        else:
            understanding = {'answer': goal}
        
        # Simple rule-based planning (in production, use LLM)
        goal_lower = goal.lower()
        
        # File operations
        if 'read' in goal_lower and 'file' in goal_lower:
            steps.append(TaskStep(
                step_id=1,
                tool_name='read_file',
                parameters={'path': context.get('file_path', 'README.md') if context else 'README.md'},
                expected_output='File contents',
                risk_level=RiskLevel.LOW
            ))
        
        # Search operations
        if 'search' in goal_lower or 'find' in goal_lower:
            query = context.get('query', goal) if context else goal
            steps.append(TaskStep(
                step_id=len(steps) + 1,
                tool_name='memory_query',
                parameters={'query': query},
                expected_output='Search results',
                risk_level=RiskLevel.SAFE
            ))
        
        # Write operations
        if 'write' in goal_lower or 'save' in goal_lower:
            steps.append(TaskStep(
                step_id=len(steps) + 1,
                tool_name='write_file',
                parameters={
                    'path': 'outputs/result.txt',
                    'content': context.get('content', 'Result') if context else 'Result'
                },
                expected_output='File written',
                risk_level=RiskLevel.MEDIUM,
                requires_confirmation=True
            ))
        
        # Calculate operations
        if 'calculate' in goal_lower or 'compute' in goal_lower:
            expression = re.search(r'[\d+\-*/() ]+', goal)
            if expression:
                steps.append(TaskStep(
                    step_id=len(steps) + 1,
                    tool_name='python_eval',
                    parameters={'expression': expression.group()},
                    expected_output='Calculation result',
                    risk_level=RiskLevel.MEDIUM,
                    requires_confirmation=True
                ))
        
        # Default: query memory
        if not steps:
            steps.append(TaskStep(
                step_id=1,
                tool_name='memory_query',
                parameters={'query': goal},
                expected_output='AIONS response',
                risk_level=RiskLevel.SAFE
            ))
        
        return steps
    
    def execute_task(self, goal: str, context: Optional[Dict] = None) -> TaskResult:
        """
        Execute complete task
        """
        task_id = hashlib.md5(f"{goal}{time.time()}".encode()).hexdigest()[:8]
        start_time = time.time()
        
        # Plan steps
        steps = self.plan_task(goal, context)
        
        result = TaskResult(
            task_id=task_id,
            goal=goal,
            steps_planned=len(steps),
            steps_executed=0,
            success=True,
            results=[]
        )
        
        # Execute steps
        for step in steps:
            # Check if tool is allowed
            if not self.catalog.is_allowed(step.tool_name):
                result.audit_log.append({
                    'step': step.step_id,
                    'action': 'blocked',
                    'reason': 'Tool not whitelisted',
                    'tool': step.tool_name
                })
                continue
            
            # Check execution limit
            if not self.catalog.check_execution_limit(step.tool_name):
                result.audit_log.append({
                    'step': step.step_id,
                    'action': 'blocked',
                    'reason': 'Execution limit exceeded',
                    'tool': step.tool_name
                })
                continue
            
            # Confirmation check
            if step.requires_confirmation and self.require_confirmation:
                print(f"\n⚠️ Confirmation required for: {step.tool_name}")
                print(f"   Parameters: {step.parameters}")
                confirm = input("   Proceed? (y/n): ")
                
                if confirm.lower() != 'y':
                    result.audit_log.append({
                        'step': step.step_id,
                        'action': 'skipped',
                        'reason': 'User declined confirmation'
                    })
                    continue
            
            # Execute tool
            exec_result = self.executor.execute_tool(step.tool_name, step.parameters)
            
            # Record execution
            self.catalog.record_execution(step.tool_name)
            result.steps_executed += 1
            
            # Store result
            result.results.append({
                'step': step.step_id,
                'tool': step.tool_name,
                'result': exec_result
            })
            
            # Audit log
            result.audit_log.append({
                'step': step.step_id,
                'action': 'executed',
                'tool': step.tool_name,
                'status': exec_result.get('status'),
                'timestamp': datetime.now().isoformat()
            })
            
            # Stop on error
            if exec_result.get('status') == 'error':
                result.success = False
                result.error = exec_result.get('error')
                break
        
        result.execution_time = time.time() - start_time
        
        return result


def test_agent_layer():
    """Test agent layer functionality"""
    print("\n" + "="*60)
    print("AIONS AGENT LAYER TEST")
    print("="*60)
    
    # Initialize planner
    print("\nInitializing task planner...")
    planner = TaskPlanner(require_confirmation=False, dry_run=True)
    
    # Test tasks
    test_tasks = [
        ("Read the README file", {'file_path': 'README.md'}),
        ("Search for information about Python", None),
        ("Calculate 25 * 4 + 10", None),
        ("Save results to file", {'content': 'Test results'}),
        ("What is the capital of Poland?", None)
    ]
    
    print("\nTesting task planning and execution:")
    print("-" * 40)
    
    for goal, context in test_tasks:
        print(f"\n📋 Task: {goal}")
        
        # Plan steps
        steps = planner.plan_task(goal, context)
        print(f"   Steps planned: {len(steps)}")
        
        for step in steps:
            print(f"     {step.step_id}. {step.tool_name} [{step.risk_level.value}]")
        
        # Execute task
        result = planner.execute_task(goal, context)
        
        print(f"   Execution: {'✅ Success' if result.success else '❌ Failed'}")
        print(f"   Steps executed: {result.steps_executed}/{result.steps_planned}")
        print(f"   Time: {result.execution_time:.3f}s")
    
    # Show catalog stats
    print("\n" + "="*60)
    print("TOOL EXECUTION STATISTICS:")
    print("-" * 40)
    
    for tool_name, count in planner.catalog.execution_counts.items():
        tool = planner.catalog.tools[tool_name]
        print(f"{tool_name}: {count}/{tool.max_executions} [{tool.risk.value}]")
    
    print("\n✅ Agent layer test completed!")


if __name__ == "__main__":
    test_agent_layer()