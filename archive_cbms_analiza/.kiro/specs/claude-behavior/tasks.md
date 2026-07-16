# Tasks: Claude/AI Behavior Implementation

## Task Checklist

### Session Start Tasks (EVERY SESSION)

- [ ] **TASK-001**: Call `system_health()` to verify MCP is working
  - Input: None
  - Output: Health status JSON
  - Verify: All components show "ok"

- [ ] **TASK-002**: Call `conv_history()` to load previous context
  - Input: Optional date (default: today)
  - Output: Recent log entries
  - Verify: Entries loaded, understand what was done

- [ ] **TASK-003**: Call `memory_recall()` for current topic
  - Input: session_id, query about current topic
  - Output: Relevant memories from ChromaDB/CBMS
  - Verify: Context is loaded before responding

### Tool Usage Tasks (DURING SESSION)

- [ ] **TASK-010**: Use `fast_search()` for file discovery
  - INSTEAD OF: `find`, `ls`, guessing paths
  - Example: `fast_search("server.py")` → actual paths

- [ ] **TASK-011**: Use `memory_recall()` for context retrieval
  - INSTEAD OF: Re-reading files, asking user
  - Example: `memory_recall("session", "CBMS architecture")`

- [ ] **TASK-012**: Use `cbms_search()` for domain knowledge
  - INSTEAD OF: Web search, guessing
  - Example: `cbms_search("Korean compression algorithm")`

- [ ] **TASK-013**: Use `project_file_deps()` before modifications
  - BEFORE: Any Edit or Write to existing files
  - Example: `project_file_deps("server/store.py")`

- [ ] **TASK-014**: Use `conv_log()` for important actions
  - WHEN: After significant work (file created, bug fixed, etc.)
  - Example: `conv_log("assistant", "Implemented X feature")`

### Anti-Simulation Tasks (ALWAYS)

- [ ] **TASK-020**: Show tool output as evidence
  - RULE: Never say "I found X" without showing `fast_search` result
  - RULE: Never say "File contains Y" without showing `Read` result
  - RULE: Never say "I modified Z" without showing `Edit` result

- [ ] **TASK-021**: Admit when you don't know
  - RULE: If tool fails → say "I couldn't find X"
  - RULE: If uncertain → say "I'm not sure, let me check"
  - RULE: Never fabricate file paths, content, or results

- [ ] **TASK-022**: Verify before claiming
  - BEFORE saying "done" → show the result
  - BEFORE saying "file exists" → call `fast_search`
  - BEFORE saying "works" → show test output

### Session End Tasks (EVERY SESSION)

- [ ] **TASK-030**: Call `conv_log()` with session summary
  - Input: Summary of what was accomplished
  - Example: `conv_log("assistant", "Session summary: Fixed X, created Y, discussed Z")`

- [ ] **TASK-031**: Call `conv_dump()` to persist logs
  - Input: Optional final summary
  - Output: Confirmation of entries saved

- [ ] **TASK-032**: Call `conv_status()` to verify
  - Verify: buffer_size is 0 (all dumped)
  - Verify: last_dump is recent

### File Organization Tasks (WHEN CREATING FILES)

- [ ] **TASK-040**: Check structure before creating
  - USE: `fast_search` to find similar files
  - USE: `project_search` to understand existing structure
  - VERIFY: Location matches aions-architecture.md

- [ ] **TASK-041**: Never duplicate functionality
  - BEFORE creating: Check if similar exists
  - USE: `fast_search` + `memory_recall`
  - IF exists: Modify existing, don't create new

- [ ] **TASK-042**: Follow directory conventions
  ```
  Python code → server/ or scripts/
  MCP servers → mcpServers/
  Data files → data/
  Logs → logs/
  Skills → skills/
  Kiro config → .kiro/
  ```

## Validation Checklist

### Before Responding to User:
```
□ Did I check system_health()?
□ Did I check conv_history()?
□ Did I use memory_recall() for context?
□ Am I using MCP tools first?
□ Do I have evidence for my claims?
```

### Before Modifying Code:
```
□ Did I check project_file_deps()?
□ Did I read the current file content?
□ Is the location correct per aions-architecture.md?
□ Will I log this change via conv_log()?
```

### Before Ending Session:
```
□ Did I call conv_log() with summary?
□ Did I call conv_dump()?
□ Did I verify with conv_status()?
```

## Error Recovery Tasks

### TASK-ERR-001: MCP Connection Failed
```
1. Check if server is running
2. Verify paths in mcp.json
3. Fall back to local tools (but log warning)
4. Inform user about degraded functionality
```

### TASK-ERR-002: File Not Found
```
1. DO NOT guess the path
2. Use fast_search() to locate
3. If not found, ask user for clarification
4. Never fabricate file content
```

### TASK-ERR-003: Simulation Detected (self-check)
```
1. Stop current response
2. Actually call the tool
3. Show real output
4. Apologize and correct
```
