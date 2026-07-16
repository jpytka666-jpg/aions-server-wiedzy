# Design: Claude/AI Behavior System

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SESSION INITIALIZATION                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │system_health│→ │conv_history │→ │memory_recall(topic)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TOOL SELECTION                               │
│                                                                  │
│  Priority 1: aions-context MCP                                   │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │ fast_search  │memory_recall │ cbms_search  │project_search│ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                              │                                   │
│  Priority 2: Local Tools (if MCP insufficient)                  │
│  ┌──────────────┬──────────────┬──────────────┐                │
│  │    Read      │    Write     │    Edit      │                │
│  └──────────────┴──────────────┴──────────────┘                │
│                              │                                   │
│  Priority 3: Web Search (last resort)                           │
│  ┌──────────────────────────────────────────┐                  │
│  │         Only if user explicitly asks     │                  │
│  └──────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION & LOGGING                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  1. Execute tool                                            ││
│  │  2. Show ACTUAL result (no simulation)                      ││
│  │  3. conv_log() automatically via @auto_logged decorator     ││
│  │  4. Buffer fills → auto conv_dump() at threshold            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RESPONSE                                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  - Based on ACTUAL tool results                             ││
│  │  - With evidence/proof                                      ││
│  │  - No fabrication                                           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Session Initializer

```typescript
interface SessionInit {
  // Called at start of every session
  async initialize(): Promise<SessionContext> {
    const health = await mcp.system_health();
    const history = await mcp.conv_history();
    const context = await mcp.memory_recall(currentSession, topic);

    return { health, history, context };
  }
}
```

### 2. Tool Router

```typescript
interface ToolRouter {
  // Determines which tool to use
  route(need: UserNeed): Tool {
    // Priority 1: MCP tools
    if (need.type === 'file_search') return 'fast_search';
    if (need.type === 'memory_query') return 'memory_recall';
    if (need.type === 'domain_knowledge') return 'cbms_search';
    if (need.type === 'project_search') return 'project_search';

    // Priority 2: Local tools (only if MCP insufficient)
    if (need.type === 'read_specific_file') return 'Read';
    if (need.type === 'modify_file') return 'Edit';

    // Priority 3: Web (last resort)
    if (need.type === 'external_info' && need.explicit) return 'WebSearch';

    throw new Error('Use MCP tools first!');
  }
}
```

### 3. Anti-Simulation Guard

```typescript
interface AntiSimulationGuard {
  // Validates that AI shows actual results
  validate(claim: AIClaim, evidence: ToolResult): boolean {
    // Claim "I found file X" must have fast_search result
    // Claim "I modified Y" must have Edit result
    // Claim "File contains Z" must have Read result

    if (!evidence) {
      throw new Error('SIMULATION DETECTED: No tool evidence for claim');
    }

    return true;
  }
}
```

### 4. Logging Pipeline

```typescript
interface LoggingPipeline {
  // Automatic logging via decorator
  @auto_logged
  async anyToolCall(tool: string, args: object): Promise<Result> {
    const result = await execute(tool, args);

    // Automatically logged by decorator:
    // - tool name
    // - args
    // - result preview
    // - timestamp

    // Auto-dump when threshold reached
    if (buffer.length >= threshold) {
      await conv_dump();
    }

    return result;
  }
}
```

## Data Flow

### Search Flow
```
User: "Znajdź plik z Korean compression"
  │
  ├─► fast_search("korean compression")
  │     └─► Returns: ["E:/server wiedzy/server/korean_keys.py", ...]
  │
  ├─► memory_recall("session", "korean compression")
  │     └─► Returns: Previous context about Korean compression
  │
  └─► Response with ACTUAL paths and context
```

### Modification Flow
```
User: "Dodaj funkcję do server.py"
  │
  ├─► project_file_deps("server.py")
  │     └─► Returns: Dependencies, imported_by
  │
  ├─► Read("E:/server wiedzy/server/server.py")
  │     └─► Returns: Actual file content
  │
  ├─► Edit(file, old_string, new_string)
  │     └─► Returns: Confirmation
  │
  ├─► conv_log("assistant", "Added function X to server.py")
  │     └─► Logged automatically
  │
  └─► Response with proof of change
```

## State Management

```typescript
interface AIState {
  session: {
    initialized: boolean;
    lastHealthCheck: Date;
    contextLoaded: boolean;
  };

  logging: {
    buffer: LogEntry[];
    threshold: number;
    lastDump: Date;
  };

  tools: {
    mcpAvailable: boolean;
    lastUsed: Map<string, Date>;
  };
}
```

## Error Handling

| Error | Action |
|-------|--------|
| MCP not available | Fallback to local tools, log warning |
| Tool timeout | Retry once, then inform user |
| Simulation detected | Stop, show error, require real tool call |
| File not found | Use fast_search to locate, don't guess |

## Interfaces

### MCP Tool Interface
```typescript
interface MCPTools {
  // Search
  fast_search(query: string, max_results?: number): FileList;
  fast_search_ext(ext: string, folder?: string): FileList;
  memory_recall(session: string, query: string, top_k?: number): MemoryResults;
  cbms_search(query: string): CBMSResults;
  project_search(query: string, scan_id?: string): ProjectResults;

  // Logging
  conv_log(role: string, content: string, save_now?: boolean): LogResult;
  conv_dump(summary?: string): DumpResult;
  conv_status(): StatusResult;
  conv_history(date?: string): HistoryResult;

  // System
  system_health(): HealthResult;
  project_file_deps(file_path: string): DepsResult;
  git_status(repo_path?: string): GitResult;
}
```
