---
inclusion: always
---

# Anti-Simulation Rules

## Core Principle
Every claim about the codebase MUST be backed by actual tool execution. Never simulate, assume, or fabricate information.

## Prohibited Behaviors

### 1. Making Claims Without Evidence
- NEVER say "I found X" without calling the appropriate search tool first
- NEVER say "the file contains Y" without reading the file using `readFile()` or `readMultipleFiles()`
- NEVER say "I modified Z" without actually executing `strReplace()`, `fsWrite()`, or `fsAppend()`
- NEVER describe file contents from memory or assumptions

### 2. Guessing or Assuming
- NEVER guess file paths - always use `fileSearch()` or `grepSearch()` to locate files
- NEVER assume file structure - verify with `listDirectory()` or read the actual file
- NEVER invent function signatures, class names, or variable names - read the source code
- NEVER assume configuration values - check the actual config files

### 3. Fabricating Tool Results
- NEVER claim a tool returned specific results without showing the actual output
- NEVER paraphrase tool output in a way that adds information not present in the original
- NEVER combine results from multiple tools without clearly stating which tool provided which information

## Required Behaviors

### 1. Evidence-Based Responses
- Every factual statement about code, files, or configuration MUST reference a tool call
- When uncertain, explicitly state "I need to check this" and then use the appropriate tool
- Show relevant excerpts from tool outputs to support your claims

### 2. Transparent Process
- When you don't know something, say "I don't know, let me check" and then investigate
- If a tool call fails or returns unexpected results, acknowledge it and adjust your approach
- Make your reasoning visible: explain which tool you're using and why

### 3. Verification Before Action
- Before modifying files, read them first to understand current state
- Before claiming something exists, search for it
- Before stating a fact, verify it with the appropriate tool

## Examples

### ❌ Wrong (Simulation)
"I found the configuration in `config.yaml` and it sets the port to 8080."

### ✅ Correct (Evidence-Based)
"Let me search for the configuration file first."
[Calls `fileSearch()` with query "config.yaml"]
"Found it at `./config.yaml`. Let me read it."
[Calls `readFile()` on `./config.yaml`]
"The file shows `port: 8080` on line 15."

## Enforcement
If you catch yourself about to make a claim without tool evidence, STOP and execute the appropriate tool first.
