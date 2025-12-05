# Claude Code - Example Prompts for AIONS Project

## Quick Start Prompts

### System Check
```
Check system health and verify all MCP servers are running correctly
```

### Project Overview
```
Use fast_search to scan the project structure and give me an overview of the AIONS architecture
```

### Memory Search
```
Search my conversation history for discussions about ChromaDB configuration
```

## AIONS Context Tools

### Fast File Search
```
Use fast_search to find all Python files related to MCP servers
```

```
Find all configuration files (.json, .yaml, .toml) in the project
```

### Project Search
```
Search the project for implementations of the context_schema
```

```
Find all references to "ChromaDB" in the codebase
```

### Memory Recall
```
Recall previous conversations about AWS Aurora DSQL setup
```

```
What did we discuss about MCP server configuration last week?
```

### CBMS Search (Domain Knowledge)
```
Search CBMS for best practices on vector database optimization
```

```
Find domain knowledge about Python MCP server implementation patterns
```

### Git Operations
```
Show me the git status and recent commits
```

```
What files have been modified in the last 5 commits?
```

### Browser Automation
```
Navigate to the Claude Code documentation and extract the MCP configuration section
```

```
Take a screenshot of the current AIONS project dashboard
```

## Aurora DSQL Operations

### Database Queries
```
List all tables in the Aurora DSQL database
```

```
Show me the schema for the conversations table
```

```
Query the last 10 entries from the context_snapshots table
```

### Schema Management
```
Get the complete schema for all tables in the database
```

```
Check if the index on user_id exists in the sessions table
```

## AWS Operations

### AWS Profile Check
```
Verify my AWS credentials and show the current caller identity
```

```
List all available AWS profiles and their regions
```

## Code Analysis

### Python Code Review
```
Analyze the server/context_schema.py file and suggest improvements
```

```
Review all Python files in mcpServers/ for PEP 8 compliance
```

### Dependency Analysis
```
Check requirements.txt and identify any outdated packages
```

```
Find all imports in the project and create a dependency graph
```

## Project Management

### Documentation Generation
```
Generate API documentation for all MCP tools in the aions-context server
```

```
Create a README for the mcpServers/VS_CODE_MCP_CODEX directory
```

### Code Refactoring
```
Refactor the context_admin.py to use type hints consistently
```

```
Extract common patterns from MCP server implementations into a base class
```

## Advanced Workflows

### Multi-Step Analysis
```
1. Use fast_search to find all Python files
2. For each file, check for missing docstrings
3. Generate a report of files that need documentation
4. Create a task list for improving code documentation
```

### Database Migration
```
1. Get the current schema from Aurora DSQL
2. Compare it with the schema defined in context_schema.py
3. Generate migration SQL if there are differences
4. Ask for confirmation before applying changes
```

### Automated Testing
```
1. Find all Python modules in the server/ directory
2. Check if corresponding test files exist
3. For modules without tests, generate basic unit test templates
4. Run the tests and report results
```

## Integration Examples

### AIONS + AWS
```
1. Use cbms_search to find AWS best practices
2. Check current AWS configuration
3. Query Aurora DSQL for recent activity
4. Generate a security audit report
```

### Code Quality Pipeline
```
1. Get git status to see modified files
2. For each modified Python file:
   - Check syntax
   - Verify PEP 8 compliance
   - Run type checking
   - Check for security issues
3. Generate a pre-commit report
```

### Knowledge Base Update
```
1. Search conversation history for new insights
2. Extract key learnings and patterns
3. Store them in CBMS using memory_store
4. Update the AIONS_CATALOG with new knowledge
```

## Debugging Prompts

### MCP Server Issues
```
The aions-context MCP server is not responding. Help me debug:
1. Check if the Python process is running
2. Verify the CHROMA_PATH environment variable
3. Test the ChromaDB connection
4. Review recent error logs
```

### Permission Problems
```
I'm getting permission denied errors. Help me:
1. Check current permission settings
2. Identify which command is being blocked
3. Add appropriate allow rules
4. Test the command again
```

### Performance Analysis
```
The project search is slow. Help me optimize:
1. Check the size of the ChromaDB database
2. Analyze query patterns
3. Suggest indexing improvements
4. Benchmark before and after changes
```

## Custom Workflows

### Daily Standup Report
```
Generate my daily standup report:
1. Show git commits from the last 24 hours
2. List files I modified
3. Search conversation history for tasks discussed
4. Create a summary of work completed and next steps
```

### Code Review Preparation
```
Prepare for code review:
1. Get git diff for the current branch
2. Analyze changed files for potential issues
3. Generate inline comments for reviewers
4. Create a pull request description
```

### Project Health Check
```
Run a complete project health check:
1. Verify all MCP servers are operational
2. Check database connectivity
3. Scan for code quality issues
4. Review recent error logs
5. Generate a health report with recommendations
```

## Tips for Effective Prompts

### Be Specific
❌ "Check the database"
✅ "Use readonly_query to get the count of records in the conversations table"

### Use Tool Names
❌ "Search for files"
✅ "Use fast_search to find all TypeScript files in the src directory"

### Chain Operations
❌ "Do multiple things"
✅ "First use fast_search to find config files, then read each one and compare their settings"

### Provide Context
❌ "Fix this"
✅ "The MCP server at mcpServers/VS_CODE_MCP_CODEX/src/server.py is throwing a ChromaDB connection error. Debug and fix it."

### Request Verification
❌ "Make changes"
✅ "Make the changes and then verify with getDiagnostics that the code still compiles"

## Keyboard Shortcuts Reminder

- `Ctrl+Escape` - Toggle Claude Code focus
- `Ctrl+Shift+Escape` - Open in new tab
- `Alt+K` - Insert @-mention
- `Ctrl+N` - New conversation (when focused)

## @-Mentions

Use @-mentions to reference context:
- `@file` - Reference a specific file
- `@folder` - Reference a directory
- `@aions-context` - Use AIONS MCP tools
- `@aurora-dsql` - Use database tools
- `@aws-core` - Use AWS tools
