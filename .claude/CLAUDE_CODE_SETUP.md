# Claude Code Configuration for AIONS Project

## Overview
This directory contains the complete configuration for Claude Code extension (v2.0.59) integrated with the AIONS project.

## Configuration Files

### 1. `.claude/settings.json` (Project Settings)
Main configuration file with:
- **Model**: Claude Sonnet 4.5 (latest)
- **Environment Variables**: CHROMA_PATH, PYTHONPATH, AWS_PROFILE
- **Permissions**: Comprehensive allow/deny rules for file operations and bash commands
- **MCP Servers**: Configuration for aions-context, aurora-dsql, aws-core
- **Hooks**: Pre/post write validation for Python files
- **Sandbox**: Disabled for full system access

### 2. `.claude/settings.local.json` (Local Overrides)
Local user-specific settings that override project settings:
- Additional permission rules
- Environment-specific configurations
- Auto-approval for all project MCP servers

### 3. `.mcp.json` (MCP Server Definitions)
Defines all MCP servers available to Claude Code:
- **aions-context**: Main AIONS context server with ChromaDB integration
- **aurora-dsql**: AWS Aurora DSQL database access via WSL
- **aws-core**: AWS core services MCP server

### 4. `.claude/settings/kfc-settings.json` (Kiro Integration)
Integration settings for Kiro IDE features:
- Paths to specs, steering, and settings directories
- View visibility configuration

## Features Enabled

### 1. MCP Server Integration
All three MCP servers are configured and enabled:
- **aions-context**: Fast search, memory recall, CBMS search, project scanning
- **aurora-dsql**: Database queries and schema management
- **aws-core**: AWS service interactions

### 2. Permission System
Comprehensive permission rules:
- **Allow**: Git, Python, WSL, AWS CLI, file operations
- **Deny**: Destructive system commands
- **Ask**: Docker, system services

### 3. Code Quality Hooks
Automated validation:
- **Before Write**: Python syntax checking
- **After Write**: PEP 8 compliance verification

### 4. Environment Integration
Full path configuration:
- ChromaDB data directory
- Python path for AIONS modules
- AWS profile for cloud operations
- Additional workspace directories

## Usage

### Starting Claude Code
1. Open VS Code/Kiro with this workspace
2. Press `Ctrl+Escape` to open Claude Code
3. Claude will automatically load all MCP servers
4. Use `@aions-context` to access AIONS tools

### Available Commands
- `Ctrl+Escape`: Toggle Claude Code focus
- `Ctrl+Shift+Escape`: Open Claude in new tab
- `Alt+K`: Insert @-mention reference
- `Ctrl+N`: New conversation (when Claude is focused)

### MCP Tools Available
From **aions-context**:
- `fast_search()` - Blazing fast file search
- `memory_recall()` - Semantic memory search
- `cbms_search()` - Domain knowledge search
- `project_search()` - Search in scanned projects
- `conv_history()` - Conversation history
- `git_status()`, `git_log()` - Git operations
- `browser_*()` - Browser automation
- `mcp_find()`, `mcp_list()` - MCP catalog search

From **aurora-dsql**:
- `readonly_query()` - Read-only SQL queries
- `transact()` - Write transactions
- `get_schema()` - Table schema inspection
- `dsql_search_documentation()` - DSQL docs search

From **aws-core**:
- AWS service operations (via prompt understanding)

## Verification

### Check MCP Server Status
```bash
# In Claude Code, ask:
"Check the status of all MCP servers"
```

### Test AIONS Context
```bash
# In Claude Code, ask:
"Use fast_search to find all Python files in the project"
```

### Test Aurora DSQL
```bash
# In Claude Code, ask:
"List all tables in the Aurora DSQL database"
```

## Troubleshooting

### MCP Server Not Loading
1. Check `.mcp.json` paths are correct
2. Verify Python virtual environment is activated
3. Check WSL is running for aurora-dsql
4. Review Claude Code logs: Command Palette → "Claude Code: Show Logs"

### Permission Denied Errors
1. Check `.claude/settings.local.json` permissions
2. Add specific command patterns to "allow" list
3. Restart Claude Code after permission changes

### Environment Variables Not Set
1. Verify paths in `.claude/settings.json` env section
2. Check PYTHONPATH includes both root and server directories
3. Ensure AWS_PROFILE matches your AWS configuration

## Advanced Configuration

### Adding New MCP Servers
1. Add server definition to `.mcp.json`
2. Add server name to `enabledMcpjsonServers` in `settings.json`
3. Add to `allowedMcpServers` list with command pattern
4. Restart Claude Code

### Custom Hooks
Edit `hooks` section in `settings.json`:
```json
"hooks": {
  "beforeWrite": [
    {
      "matcher": "*.ts",
      "hooks": [
        {
          "type": "command",
          "command": "tsc --noEmit \"$FILE\"",
          "timeout": 10,
          "statusMessage": "Type checking..."
        }
      ]
    }
  ]
}
```

### Permission Patterns
Use glob patterns for flexible permissions:
```json
"allow": [
  "Bash(git *)",           // All git commands
  "Write(src/**/*.py)",    // Python files in src
  "Read(*.json)"           // All JSON files
]
```

## Integration with Kiro

Claude Code is fully integrated with Kiro IDE:
- Shares MCP configuration from `.kiro/settings/mcp.json`
- Uses steering rules from `.kiro/steering/`
- Accesses specs from `.kiro/specs/`
- Synchronized settings via `.claude/settings/kfc-settings.json`

## Documentation Links

- [Claude Code Documentation](https://code.claude.com/docs/en/vs-code)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [AIONS Project Overview](../AIONS_MASTER_INSTRUCTIONS.md)
- [Kiro Configuration Guide](../KIRO_CONFIGURATION_GUIDE.md)

## Version Information

- **Claude Code Extension**: v2.0.59
- **Installation Path**: `C:\Users\User\.kiro\extensions\anthropic.claude-code-2.0.59-win32-x64`
- **VS Code Compatibility**: ^1.94.0
- **Last Updated**: 2025-12-05
