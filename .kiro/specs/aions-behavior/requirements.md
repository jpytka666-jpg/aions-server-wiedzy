# Requirements Document: AI Behavior in AIONS

## Introduction

This document defines the behavioral requirements for AI agents operating within the AIONS (AI Orchestration System) environment. The system ensures that AI agents follow consistent patterns for session initialization, tool usage prioritization, and evidence-based responses. These requirements establish a framework for reliable, verifiable, and context-aware AI interactions.

## Glossary

- **AIONS**: AI Orchestration System - the overall system managing AI agent behavior and context
- **AI Agent**: The AI assistant operating within the AIONS environment
- **MCP**: Model Context Protocol - the communication protocol for tool interactions
- **aions-context MCP**: The primary MCP server providing local context tools (fast_search, memory_recall, cbms_search, project_search, conv_history)
- **Session**: A single interaction period between the user and the AI Agent
- **Tool**: A function or capability available to the AI Agent through MCP
- **Local Sources**: Files, memory, and context available through aions-context MCP tools
- **Evidence**: Actual output from tool execution that supports a claim or statement

## Requirements

### Requirement 1: Session Initialization

**User Story:** As a user, I want the AI agent to properly initialize each session with system health checks and context retrieval, so that I receive informed responses based on current system state and conversation history.

#### Acceptance Criteria

1. WHEN a session starts, THE AI Agent SHALL invoke system_health() before processing user requests
2. WHEN the AI Agent prepares a response, THE AI Agent SHALL invoke conv_history() to retrieve previous conversation context
3. WHEN the AI Agent needs contextual information, THE AI Agent SHALL invoke memory_recall() with relevant query parameters
4. WHEN system_health() returns an error status, THE AI Agent SHALL inform the user of system issues before proceeding

### Requirement 2: Tool Usage Priority

**User Story:** As a user, I want the AI agent to prioritize local context sources over external searches, so that responses are based on my project's actual state and avoid unnecessary external queries.

#### Acceptance Criteria

1. WHEN the AI Agent needs to search for information, THE AI Agent SHALL invoke aions-context MCP tools before using other search methods
2. WHEN local sources contain relevant information, THE AI Agent SHALL use that information and not invoke web search tools
3. WHEN the user explicitly requests external information, THE AI Agent SHALL invoke web search tools only after confirming local sources are insufficient
4. WHEN multiple aions-context MCP tools are available for a task, THE AI Agent SHALL select the most specific tool (fast_search for files, memory_recall for context, cbms_search for domain knowledge, project_search for project-wide queries)

### Requirement 3: Evidence-Based Responses

**User Story:** As a user, I want the AI agent to provide verifiable, evidence-based responses backed by actual tool execution, so that I can trust the accuracy of information and avoid fabricated or assumed claims.

#### Acceptance Criteria

1. WHEN the AI Agent makes a claim about code, files, or system state, THE AI Agent SHALL provide actual tool output as evidence
2. WHEN the AI Agent lacks information to answer a query, THE AI Agent SHALL explicitly state the need to investigate and then invoke appropriate tools
3. IF the AI Agent cannot verify a claim through tool execution, THEN THE AI Agent SHALL not make that claim
4. WHEN tool execution fails or returns unexpected results, THE AI Agent SHALL acknowledge the failure and explain the situation to the user
5. WHEN the AI Agent modifies files or system state, THE AI Agent SHALL confirm the modification by showing the tool execution result
