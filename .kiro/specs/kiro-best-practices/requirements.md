# Requirements Document

## Introduction

Implementacja Kiro Best Practices Boilerplate - kompletna konfiguracja Kiro Autonomous Agent z pełną funkcjonalnością, obejmująca 14 brakujących Agent Hooks, Master Config MCP bez duplikatów, oraz 2 brakujące Steering Rules.

## Glossary

- **Agent Hook**: Automatyczna akcja wyzwalana przez zdarzenie w IDE (zapis pliku, zakończenie agenta, nowa sesja)
- **Steering Rule**: Dokument markdown definiujący zachowanie agenta AI
- **MCP Server**: Model Context Protocol server dostarczający narzędzia dla agenta
- **Master Config**: Jednolita konfiguracja MCP bez duplikatów i konfliktów
- **AIONS-CONTEXT**: Główny lokalny MCP server użytkownika
- **Kiro Power**: Pakiet MCP servers + steering files dostarczany przez Kiro

## Requirements

### Requirement 1: Master MCP Configuration

**User Story:** As a developer, I want a unified MCP configuration without duplicates, so that there are no conflicts between AIONS-CONTEXT, Kiro Powers, and external services.

#### Acceptance Criteria

1. WHEN the MCP configuration is loaded THEN the system SHALL have AIONS-CONTEXT as the primary server with highest priority
2. WHEN duplicate MCP servers exist in both mcp.json and Powers THEN the system SHALL disable duplicates in mcp.json and use Powers instead
3. WHEN aurora-dsql is configured THEN the system SHALL keep it in mcp.json for direct connection (not through Power)
4. WHEN external services (fetch, stripe) are configured THEN the system SHALL register them as optional addons
5. IF a tool name conflict occurs THEN the system SHALL prioritize AIONS-CONTEXT tools over Power tools

### Requirement 2: Tier 1 Agent Hooks (Auto on Save)

**User Story:** As a developer, I want automatic validation when I save files, so that I catch errors immediately.

#### Acceptance Criteria

1. WHEN a Python file is saved THEN the system SHALL run pytest for that file automatically
2. WHEN a Python file is saved THEN the system SHALL run linting (flake8/ruff) automatically
3. WHEN any code file is saved THEN the system SHALL scan for security issues (API keys, secrets)
4. WHEN a JSON/YAML config file is saved THEN the system SHALL validate its syntax

### Requirement 3: Tier 2 Agent Hooks (Manual Buttons)

**User Story:** As a developer, I want manual validation buttons in the Kiro panel, so that I can run checks on demand.

#### Acceptance Criteria

1. WHEN user clicks "Validate MCP" button THEN the system SHALL check all MCP server connections
2. WHEN user clicks "Validate Env" button THEN the system SHALL check environment variables and .env files
3. WHEN user clicks "API Schema Check" button THEN the system SHALL validate OpenAPI/GraphQL schemas
4. WHEN user clicks "Commit Helper" button THEN the system SHALL generate a commit message based on changes
5. WHEN user clicks "Spell Check README" button THEN the system SHALL check spelling in README files

### Requirement 4: Tier 3 Agent Hooks (Optional)

**User Story:** As a developer, I want optional advanced hooks for deeper analysis, so that I can run them when needed.

#### Acceptance Criteria

1. WHEN user clicks "Test MCP Server" button THEN the system SHALL test each MCP server with sample calls
2. WHEN user clicks "Check Dependencies" button THEN the system SHALL check for outdated packages
3. WHEN user clicks "Coverage Analysis" button THEN the system SHALL run test coverage report
4. WHEN user clicks "Performance Check" button THEN the system SHALL analyze code for performance issues

### Requirement 5: Missing Steering Rules

**User Story:** As a developer, I want complete steering documentation, so that the agent understands my project fully.

#### Acceptance Criteria

1. WHEN the agent starts THEN the system SHALL load product.md with project vision and goals
2. WHEN the agent starts THEN the system SHALL load tech.md with technology stack information
