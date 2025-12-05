# Claude Code - Quick Start Guide

## ✅ Configuration Complete!

Your Claude Code extension is now fully configured and ready to use with the AIONS project.

## 🚀 Getting Started (3 Steps)

### Step 1: Open Claude Code
Press `Ctrl+Escape` in VS Code/Kiro

### Step 2: Verify MCP Servers
Type in Claude Code:
```
Check system health and verify all MCP servers are running
```

### Step 3: Try Your First Command
```
Use fast_search to find all Python files in the mcpServers directory
```

## 🎯 What's Configured

### ✓ MCP Servers (3 Active)
1. **aions-context** - Your main AIONS tools
   - Fast file search
   - Memory recall
   - CBMS knowledge search
   - Project scanning
   - Git operations
   - Browser automation

2. **aurora-dsql** - Database access
   - SQL queries
   - Schema inspection
   - Transaction management

3. **aws-core** - AWS services
   - AWS operations via prompt understanding

### ✓ Permissions
- Full file read/write access
- Git operations allowed
- Python and WSL commands enabled
- AWS CLI operations permitted
- Destructive commands blocked

### ✓ Environment
- ChromaDB path configured
- Python path set correctly
- AWS profile active
- All workspace directories accessible

## 📋 Essential Commands

### System Check
```
Check system health
```

### File Operations
```
Use fast_search to find all .json files
```

### Memory Search
```
Search my conversation history for "MCP configuration"
```

### Database Query
```
List all tables in Aurora DSQL
```

### Git Status
```
Show me git status and recent commits
```

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Escape` | Toggle Claude Code focus |
| `Ctrl+Shift+Escape` | Open in new tab |
| `Alt+K` | Insert @-mention |
| `Ctrl+N` | New conversation (when focused) |

## 🎨 Using @-Mentions

Reference context directly:
- `@file` - Specific file
- `@folder` - Directory
- `@aions-context` - AIONS tools
- `@aurora-dsql` - Database tools
- `@aws-core` - AWS tools

Example:
```
@aions-context Use fast_search to find all Python files, then analyze @folder mcpServers
```

## 🔧 Common Tasks

### 1. Search Project
```
Use project_search to find all references to "ChromaDB"
```

### 2. Check Code Quality
```
Analyze @file server/context_schema.py for PEP 8 compliance
```

### 3. Database Operations
```
Query Aurora DSQL: SELECT * FROM conversations LIMIT 10
```

### 4. Git Workflow
```
Show git status, then create a commit message for my changes
```

### 5. Documentation
```
Generate API documentation for @folder mcpServers/VS_CODE_MCP_CODEX
```

## 📚 More Examples

See `.claude/EXAMPLE_PROMPTS.md` for 50+ example prompts organized by category.

## 🐛 Troubleshooting

### MCP Server Not Responding
```
Show me the logs for aions-context MCP server
```

### Permission Denied
Check `.claude/settings.local.json` and add the command pattern to the "allow" list.

### Environment Variable Issues
Verify in Claude Code:
```
Check if CHROMA_PATH and PYTHONPATH environment variables are set correctly
```

## 📖 Full Documentation

- **Setup Details**: `.claude/CLAUDE_CODE_SETUP.md`
- **Example Prompts**: `.claude/EXAMPLE_PROMPTS.md`
- **Project Overview**: `AIONS_MASTER_INSTRUCTIONS.md`
- **Kiro Config**: `KIRO_CONFIGURATION_GUIDE.md`

## 🎉 You're Ready!

Claude Code is configured with:
- ✅ All 3 MCP servers active
- ✅ Full AIONS integration
- ✅ Comprehensive permissions
- ✅ Environment variables set
- ✅ Documentation complete

**Press `Ctrl+Escape` and start coding with Claude!**

---

*Configuration verified: 2025-12-05*
*Extension version: 2.0.59*
