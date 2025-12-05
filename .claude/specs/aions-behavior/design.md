# Design Document: AI Behavior in AIONS

## Overview

This design establishes a behavioral framework for AI agents operating within the AIONS (AI Orchestration System) environment. The system enforces consistent patterns for session initialization, tool usage prioritization, and evidence-based responses to ensure reliable, verifiable, and context-aware AI interactions.

The design addresses three core behavioral requirements:
1. **Session Initialization**: Ensuring AI agents start each session with proper context and system awareness
2. **Tool Usage Priority**: Establishing a clear hierarchy for information retrieval that prioritizes local context
3. **Evidence-Based Responses**: Requiring verifiable claims backed by actual tool execution

This framework is implemented through a combination of system prompts, steering rules, and MCP tool integration patterns.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        AI Agent                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Behavior Enforcement Layer                    │  │
│  │  - Session Initialization Logic                       │  │
│  │  - Tool Priority Router                               │  │
│  │  - Evidence Verification                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Tool Layer                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  aions-context MCP (Priority 1)                    │    │
│  │  - system_health()                                 │    │
│  │  - conv_history()                                  │    │
│  │  - memory_recall()                                 │    │
│  │  - fast_search()                                   │    │
│  │  - cbms_search()                                   │    │
│  │  - project_search()                                │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Kiro Local Tools (Priority 2)                     │    │
│  │  - readFile(), grepSearch(), fileSearch()          │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  External Tools (Priority 3)                       │    │
│  │  - mcp_fetch_fetch() (web search)                  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Storage Layer                         │
│  - ChromaDB (vector storage)                                │
│  - Conversation logs (JSONL)                                │
│  - Project files and context                                │
└─────────────────────────────────────────────────────────────┘
```

### Design Rationale

**Layered Architecture**: The three-layer design (Behavior Enforcement → MCP Tools → Data Storage) provides clear separation of concerns. The behavior layer enforces rules without needing to understand data storage details, while the MCP layer abstracts tool complexity.

**Priority-Based Tool Routing**: The explicit priority system (aions-context → Kiro local → external) ensures that AI agents always check local, verified sources before reaching out to external systems. This reduces latency, improves accuracy, and prevents unnecessary external API calls.

**Stateless Behavior Enforcement**: The behavior enforcement layer is implemented through system prompts and steering rules rather than stateful code, making it easier to modify and version control behavioral patterns.

## Components and Interfaces

### 1. Session Initialization Component

**Purpose**: Ensures every AI session begins with proper context and system awareness.

**Interface**:
```python
# Conceptual interface - implemented via system prompt patterns
class SessionInitializer:
    def initialize_session() -> SessionContext:
        """
        Initializes a new AI agent session.
        
        Returns:
            SessionContext containing system health, conversation history,
            and relevant memory context
        """
        pass
    
    def check_system_health() -> HealthStatus:
        """Invokes system_health() MCP tool"""
        pass
    
    def load_conversation_history() -> List[ConversationEntry]:
        """Invokes conv_history() MCP tool"""
        pass
    
    def retrieve_relevant_memory(query: str) -> List[MemoryEntry]:
        """Invokes memory_recall() MCP tool"""
        pass
```

**Implementation Strategy**: 
- Implemented through system prompt instructions that trigger at session start
- Uses MCP tool calls to aions-context server
- Gracefully handles tool failures by informing the user

**Design Decision**: We use prompt-based initialization rather than hardcoded hooks because it provides flexibility to modify behavior without changing code, and allows the AI to adapt initialization based on context.

### 2. Tool Priority Router

**Purpose**: Enforces the tool usage hierarchy to prioritize local context sources.

**Interface**:
```python
# Conceptual interface - implemented via steering rules
class ToolPriorityRouter:
    PRIORITY_1_TOOLS = [
        "fast_search", "memory_recall", "cbms_search", 
        "project_search", "conv_history", "system_health"
    ]
    PRIORITY_2_TOOLS = [
        "readFile", "grepSearch", "fileSearch", "listDirectory"
    ]
    PRIORITY_3_TOOLS = [
        "mcp_fetch_fetch"  # web search
    ]
    
    def select_tool(task: SearchTask) -> ToolSelection:
        """
        Selects appropriate tool based on task type and priority rules.
        
        Args:
            task: The search or retrieval task to perform
            
        Returns:
            ToolSelection indicating which tool to use and why
        """
        pass
    
    def should_escalate_priority(
        current_priority: int, 
        results: ToolResults
    ) -> bool:
        """
        Determines if we should try next priority level.
        
        Returns True only if:
        - Current priority tools returned no results
        - User explicitly requested external information
        """
        pass
```

**Tool Selection Logic**:

| Task Type | Priority 1 Tool | Priority 2 Tool | Priority 3 Tool |
|-----------|----------------|-----------------|-----------------|
| Find files | fast_search() | fileSearch() | N/A |
| Search content | project_search() | grepSearch() | N/A |
| Recall context | memory_recall() | readFile() | N/A |
| Domain knowledge | cbms_search() | grepSearch() | mcp_fetch_fetch() |
| External info | N/A | N/A | mcp_fetch_fetch() |

**Design Decision**: The router is implemented through steering rules rather than code because it needs to be easily modifiable by users and should be transparent in its decision-making process.

### 3. Evidence Verification Component

**Purpose**: Ensures all claims about code, files, or system state are backed by actual tool execution.

**Interface**:
```python
# Conceptual interface - implemented via anti-simulation rules
class EvidenceVerifier:
    def verify_claim(claim: Claim) -> VerificationResult:
        """
        Verifies a claim by executing appropriate tools.
        
        Args:
            claim: A statement about code, files, or system state
            
        Returns:
            VerificationResult containing tool output and verification status
        """
        pass
    
    def require_evidence_for(statement: str) -> bool:
        """
        Determines if a statement requires tool-based evidence.
        
        Returns True for statements about:
        - File contents or structure
        - Code behavior or implementation
        - System state or configuration
        - Search results or data queries
        """
        pass
    
    def format_evidence(tool_output: Any) -> str:
        """Formats tool output as supporting evidence"""
        pass
```

**Verification Rules**:
1. **File Claims**: Must show `readFile()` or `readMultipleFiles()` output
2. **Search Claims**: Must show `fast_search()`, `grepSearch()`, or equivalent output
3. **Modification Claims**: Must show `strReplace()`, `fsWrite()`, or `fsAppend()` confirmation
4. **System State Claims**: Must show `system_health()` or equivalent output

**Design Decision**: Evidence verification is enforced through anti-simulation steering rules that make it explicit when the AI is about to make an unverified claim, prompting it to execute tools first.

## Data Models

### SessionContext
```python
@dataclass
class SessionContext:
    """Context information for an AI agent session"""
    session_id: str
    start_time: datetime
    system_health: HealthStatus
    conversation_history: List[ConversationEntry]
    relevant_memories: List[MemoryEntry]
    user_preferences: Dict[str, Any]
```

### HealthStatus
```python
@dataclass
class HealthStatus:
    """System health information from system_health() tool"""
    status: Literal["healthy", "degraded", "error"]
    mcp_servers: Dict[str, ServerStatus]
    chroma_db: DatabaseStatus
    error_messages: List[str]
    timestamp: datetime
```

### ConversationEntry
```python
@dataclass
class ConversationEntry:
    """Single entry from conversation history"""
    timestamp: datetime
    role: Literal["user", "assistant"]
    content: str
    tool_calls: List[ToolCall]
    session_id: str
```

### ToolCall
```python
@dataclass
class ToolCall:
    """Record of a tool invocation"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
```

### MemoryEntry
```python
@dataclass
class MemoryEntry:
    """Entry from memory_recall() results"""
    content: str
    session_id: str
    timestamp: datetime
    relevance_score: float
    metadata: Dict[str, Any]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Session initialization completeness
*For any* new session, when the AI Agent begins processing user requests, it must have successfully invoked system_health() and conv_history() at least once, or explicitly informed the user of initialization failures.

**Validates: Requirements 1.1, 1.2**

### Property 2: System health error notification
*For any* session where system_health() returns an error status, the AI Agent's first response must include information about the system issues before addressing the user's request.

**Validates: Requirements 1.4**

### Property 3: Tool priority ordering
*For any* information retrieval task, if the AI Agent invokes a Priority 2 or Priority 3 tool, then it must have either: (a) already invoked all applicable Priority 1 tools, or (b) determined that no Priority 1 tools are applicable to the task.

**Validates: Requirements 2.1, 2.2**

### Property 4: Local source preference
*For any* search task where local sources (aions-context MCP tools) return relevant results, the AI Agent must not invoke web search tools unless the user explicitly requests external information.

**Validates: Requirements 2.2, 2.3**

### Property 5: Tool specificity selection
*For any* task where multiple aions-context MCP tools could apply, the AI Agent must select the most specific tool (e.g., fast_search for file names, project_search for content, cbms_search for domain knowledge).

**Validates: Requirements 2.4**

### Property 6: Evidence backing for claims
*For any* statement the AI Agent makes about code, files, or system state, there must exist a corresponding tool execution whose output supports that statement, or the AI Agent must explicitly state it cannot verify the claim.

**Validates: Requirements 3.1, 3.3**

### Property 7: Explicit uncertainty acknowledgment
*For any* query where the AI Agent lacks information to provide a complete answer, it must explicitly state the need to investigate before making claims, and then invoke appropriate tools.

**Validates: Requirements 3.2**

### Property 8: Tool failure transparency
*For any* tool execution that fails or returns unexpected results, the AI Agent must acknowledge the failure in its response and explain the situation rather than proceeding as if the tool succeeded.

**Validates: Requirements 3.4**

### Property 9: Modification confirmation
*For any* file or system state modification, the AI Agent must show the tool execution result that confirms the modification was successful.

**Validates: Requirements 3.5**

### Property 10: Memory context retrieval
*For any* session initialization, if conv_history() succeeds, the AI Agent must also invoke memory_recall() with a query derived from recent conversation context or user intent.

**Validates: Requirements 1.3**

## Error Handling

### Session Initialization Errors

**Scenario**: system_health() fails or returns error status
- **Handling**: AI Agent informs user of specific system issues
- **Recovery**: Proceed with degraded functionality, clearly stating limitations
- **Example**: "The system health check indicates ChromaDB is unavailable. I can still help you, but memory recall features will be limited."

**Scenario**: conv_history() fails
- **Handling**: AI Agent acknowledges lack of conversation context
- **Recovery**: Proceed without historical context, ask user for clarification if needed
- **Example**: "I couldn't retrieve our previous conversation history. Could you provide some context about what we were discussing?"

**Scenario**: memory_recall() fails
- **Handling**: AI Agent notes the failure but continues with available context
- **Recovery**: Use only current session information
- **Example**: "Memory recall is currently unavailable, so I'm working with just our current conversation."

### Tool Priority Violations

**Scenario**: AI Agent attempts to use web search before checking local sources
- **Handling**: Steering rules should prevent this, but if it occurs, the system should log the violation
- **Recovery**: Redirect to appropriate Priority 1 tool
- **Mitigation**: Strengthen steering rules and system prompts

**Scenario**: No applicable Priority 1 tools exist for a task
- **Handling**: AI Agent explicitly states why it's escalating to Priority 2 or 3
- **Example**: "This requires external information not available in local sources, so I'll search the web."

### Evidence Verification Errors

**Scenario**: Tool execution returns empty or null results
- **Handling**: AI Agent states that no results were found rather than fabricating information
- **Example**: "I searched for that file using fast_search(), but no matches were found."

**Scenario**: Tool execution throws an exception
- **Handling**: AI Agent reports the error and suggests alternative approaches
- **Example**: "The search tool encountered an error: [error message]. Let me try a different approach."

**Scenario**: Tool output is ambiguous or unclear
- **Handling**: AI Agent shows the actual output and asks user for clarification
- **Example**: "The search returned these results: [output]. Which one are you referring to?"

### Graceful Degradation

The system should degrade gracefully when components fail:

1. **MCP Server Unavailable**: Fall back to Priority 2 tools (Kiro local tools)
2. **ChromaDB Unavailable**: Operate without memory recall, use only current session context
3. **Multiple Tool Failures**: Explicitly inform user of limitations and offer manual alternatives

## Testing Strategy

### Unit Testing Approach

Unit tests will verify individual behavioral components in isolation:

1. **Session Initialization Tests**
   - Test that initialization sequence calls required tools in correct order
   - Test error handling when system_health() fails
   - Test graceful degradation when conv_history() is unavailable

2. **Tool Priority Router Tests**
   - Test tool selection logic for various task types
   - Test that Priority 1 tools are always checked first
   - Test escalation logic when local sources are insufficient

3. **Evidence Verification Tests**
   - Test that claims trigger appropriate tool executions
   - Test that unverifiable claims are rejected
   - Test evidence formatting and presentation

### Property-Based Testing Approach

Property-based tests will verify that correctness properties hold across many randomly generated scenarios. We will use **Hypothesis** (Python) as the property-based testing library.

Each property-based test will:
- Run a minimum of 100 iterations
- Generate random but valid test inputs
- Verify the corresponding correctness property
- Be tagged with the property number from the design document

**Property Test Examples**:

1. **Property 1: Session initialization completeness**
   - Generate: Random session start scenarios with varying system states
   - Verify: system_health() and conv_history() are called before first user response
   - Tag: `# Feature: aions-behavior, Property 1: Session initialization completeness`

2. **Property 3: Tool priority ordering**
   - Generate: Random information retrieval tasks
   - Verify: If Priority 2/3 tools are used, Priority 1 tools were checked first
   - Tag: `# Feature: aions-behavior, Property 3: Tool priority ordering`

3. **Property 6: Evidence backing for claims**
   - Generate: Random claims about files, code, or system state
   - Verify: Each claim has corresponding tool execution in history
   - Tag: `# Feature: aions-behavior, Property 6: Evidence backing for claims`

### Integration Testing

Integration tests will verify end-to-end behavior:

1. **Full Session Flow**: Test complete session from initialization through multiple user interactions
2. **Tool Chain Execution**: Test sequences of tool calls following priority rules
3. **Error Recovery**: Test system behavior when multiple components fail simultaneously

### Testing Configuration

- **Test Framework**: pytest for unit and integration tests
- **Property Testing**: Hypothesis with minimum 100 iterations per property
- **Mocking**: Mock MCP tool responses for unit tests, use real tools for integration tests
- **Coverage Target**: 80% code coverage for behavioral logic

### Test Data

- **Conversation History Fixtures**: Sample JSONL files with various conversation patterns
- **System Health Scenarios**: Predefined health status responses (healthy, degraded, error)
- **Tool Response Mocks**: Realistic tool outputs for fast_search, memory_recall, etc.

## Implementation Notes

### Steering Rules Implementation

The behavioral requirements will be enforced primarily through steering rules in `.kiro/steering/`:

1. **tools-priority.md**: Enforces tool priority hierarchy
2. **anti-simulation.md**: Enforces evidence-based responses
3. **session-init.md** (new): Enforces session initialization patterns

### System Prompt Integration

Key behavioral patterns will be integrated into the system prompt:
- Session initialization checklist
- Tool priority decision tree
- Evidence verification requirements

### MCP Configuration

The `.kiro/settings/mcp.json` configuration must include the aions-context MCP server with all required tools enabled and properly configured.

### Monitoring and Logging

- Log all tool invocations with timestamps and results
- Track tool priority violations for analysis
- Monitor session initialization success rates
- Record evidence verification failures

### Performance Considerations

- Session initialization should complete within 2 seconds under normal conditions
- Tool priority checks should add minimal latency (<100ms)
- Evidence verification should not significantly impact response time
- Cache system_health() results for 30 seconds to avoid redundant checks

