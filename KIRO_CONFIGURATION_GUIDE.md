# Kiro IDE Configuration Guide

Complete guide to configuring Kiro IDE settings, including file locations, explanations, and best practices.

---

## Table of Contents

1. [Configuration File Locations](#configuration-file-locations)
2. [Workspace vs User Settings](#workspace-vs-user-settings)
3. [Core Configuration Files](#core-configuration-files)
4. [MCP (Model Context Protocol) Configuration](#mcp-model-context-protocol-configuration)
5. [Steering Files](#steering-files)
6. [Agent Hooks](#agent-hooks)
7. [Permissions Configuration](#permissions-configuration)
8. [View Settings](#view-settings)
9. [Spec Configuration](#spec-configuration)
10. [Best Practices](#best-practices)

---

## Configuration File Locations

### Workspace-Level Configuration
Located in your project workspace under `.claude/` or `.kiro/` folder:

```
your-workspace/
├── .claude/                          # Main configuration folder
│   ├── settings.local.json          # Local workspace settings
│   ├── settings/                    # Additional settings
│   │   ├── mcp.json                # MCP server configuration
│   │   └── kfc-settings.json       # Kiro Feature Configuration
│   ├── steering/                    # Context and instructions
│   ├── agents/                      # Custom agent configurations
│   ├── specs/                       # Specification files
│   └── system-prompts/              # Custom system prompts
```

### User-Level Configuration
Located in your home directory:

```
~/.kiro/                              # User home directory
├── settings/
│   └── mcp.json                     # Global MCP configuration
└── steering/                        # Global steering files
```

**Important:** User-level configs are outside the workspace, so you need shell commands to modify them.

---

## Workspace vs User Settings

### Configuration Precedence
Settings are merged with the following priority (later overrides earlier):

1. **User config** (lowest priority) - `~/.kiro/settings/`
2. **Workspace 1** - `.claude/settings/` or `.kiro/settings/`
3. **Workspace 2** - In multi-root workspaces
4. **Workspace N** (highest priority)

### When to Use Each

**User-Level Settings:**
- Global preferences across all projects
- Personal MCP servers you use everywhere
- Default steering rules for your workflow
- API keys and credentials (use environment variables)

**Workspace-Level Settings:**
- Project-specific configurations
- Team-shared settings (commit to git)
- Project-specific MCP servers
- Custom agents for the project
- Project documentation and standards

---

## Core Configuration Files

### 1. `settings.local.json`
**Location:** `.claude/settings.local.json`

**Purpose:** Local workspace settings, typically not committed to version control.

**Structure:**
```json
{
  "permissions": {
    "allow": [],
    "deny": [],
    "ask": []
  }
}
```

**Explanation:**
- `permissions.allow`: Array of tool/command patterns that are auto-approved
- `permissions.deny`: Array of patterns that are always blocked
- `permissions.ask`: Array of patterns that require user confirmation

**Example:**
```json
{
  "permissions": {
    "allow": [
      "Bash(find:*)",           // Auto-approve all 'find' commands
      "Bash(ls:*)",             // Auto-approve 'ls' commands
      "readFile:src/**"         // Auto-approve reading files in src/
    ],
    "deny": [
      "Bash(rm:-rf:*)",         // Block dangerous delete commands
      "deleteFile:**/.git/**"   // Protect .git folder
    ],
    "ask": [
      "executePwsh:*"           // Always ask before PowerShell execution
    ]
  }
}
```

---

### 2. `kfc-settings.json` (Kiro Feature Configuration)
**Location:** `.claude/settings/kfc-settings.json`

**Purpose:** Controls Kiro IDE feature visibility and paths.

**Structure:**
```json
{
  "paths": {
    "specs": ".claude/specs",
    "steering": ".claude/steering",
    "settings": ".claude/settings"
  },
  "views": {
    "specs": { "visible": true },
    "steering": { "visible": true },
    "mcp": { "visible": true },
    "hooks": { "visible": true },
    "settings": { "visible": false }
  }
}
```

**Explanation:**

#### `paths` Object
Defines where Kiro looks for different configuration types:
- `specs`: Location of specification files for structured feature development
- `steering`: Location of context/instruction files
- `settings`: Location of additional settings files

#### `views` Object
Controls visibility of panels in Kiro IDE:
- `specs.visible`: Show/hide Specs panel (structured feature development)
- `steering.visible`: Show/hide Steering panel (context rules)
- `mcp.visible`: Show/hide MCP Servers panel
- `hooks.visible`: Show/hide Agent Hooks panel
- `settings.visible`: Show/hide Settings panel

**Customization Example:**
```json
{
  "paths": {
    "specs": "docs/specs",           // Custom location
    "steering": "docs/ai-context",   // Custom location
    "settings": ".kiro/config"       // Custom location
  },
  "views": {
    "specs": { "visible": true },    // Show specs panel
    "steering": { "visible": true }, // Show steering panel
    "mcp": { "visible": true },      // Show MCP panel
    "hooks": { "visible": false },   // Hide hooks panel
    "settings": { "visible": true }  // Show settings panel
  }
}
```

---

## MCP (Model Context Protocol) Configuration

### What is MCP?
MCP allows Kiro to connect to external servers that provide additional tools and capabilities (like databases, APIs, documentation, etc.).

### Configuration File
**Location:** 
- Workspace: `.claude/settings/mcp.json` or `.kiro/settings/mcp.json`
- User: `~/.kiro/settings/mcp.json`

### Structure
```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-to-run",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR": "value"
      },
      "disabled": false,
      "autoApprove": ["tool1", "tool2"]
    }
  }
}
```

### Field Explanations

#### `mcpServers` Object
Container for all MCP server configurations. Each key is a unique server name.

#### Per-Server Configuration

**`command`** (required)
- The executable to run the MCP server
- Common values: `"uvx"`, `"node"`, `"python"`, `"npx"`
- Example: `"uvx"` for Python-based servers

**`args`** (required)
- Array of command-line arguments
- For uvx: package name and version
- Example: `["awslabs.aws-documentation-mcp-server@latest"]`

**`env`** (optional)
- Environment variables for the server process
- Use for API keys, log levels, configuration
- Example: `{"FASTMCP_LOG_LEVEL": "ERROR", "API_KEY": "your-key"}`

**`disabled`** (optional, default: false)
- Set to `true` to disable the server without removing config
- Useful for temporarily turning off servers

**`autoApprove`** (optional)
- Array of tool names that don't require user confirmation
- Leave empty `[]` to ask for all tools
- Example: `["read_file", "list_directory"]`

### Complete MCP Example

```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\Projects"],
      "env": {},
      "disabled": false,
      "autoApprove": ["read_file", "list_directory"]
    },
    "database": {
      "command": "uvx",
      "args": ["mcp-server-sqlite"],
      "env": {
        "DB_PATH": "./data/app.db"
      },
      "disabled": true,
      "autoApprove": []
    }
  }
}
```

### Installing MCP Prerequisites

Most MCP servers use `uvx` (Python package runner):

**Installation:**
```bash
# Windows (PowerShell)
pip install uv

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

**Note:** `uvx` automatically downloads and runs packages - no separate installation needed per server.

### Managing MCP Servers

**Via Command Palette:**
1. Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Search for "MCP"
3. Available commands:
   - "MCP: Reconnect Server" - Restart a server
   - "MCP: View Servers" - See all configured servers
   - "MCP: Configure" - Open config file

**Via Kiro Panel:**
- MCP Servers view shows all configured servers
- Status indicators (running/stopped/error)
- Reconnect button for each server

---

## Steering Files

### What are Steering Files?
Markdown files that provide context, instructions, and standards to Kiro for better assistance.

### Location
**Workspace:** `.claude/steering/` or `.kiro/steering/`
**User:** `~/.kiro/steering/`

### Types of Steering Files

#### 1. Always Included (Default)
Automatically included in every conversation.

**Example:** `.claude/steering/project-standards.md`
```markdown
# Project Standards

## Code Style
- Use TypeScript for all new files
- Follow ESLint configuration
- Use functional components in React

## Testing
- Write tests for all new features
- Use Jest and React Testing Library
- Aim for 80% code coverage

## Git Workflow
- Create feature branches from `develop`
- Use conventional commits
- Squash merge to main branch
```

#### 2. Conditional (File Match)
Included only when specific files are in context.

**Example:** `.claude/steering/react-guidelines.md`
```markdown
---
inclusion: fileMatch
fileMatchPattern: '**/*.tsx'
---

# React Component Guidelines

When working with React components:
- Use functional components with hooks
- Implement proper TypeScript types
- Follow accessibility best practices
- Use CSS modules for styling
```

**Front Matter Options:**
- `inclusion: fileMatch` - Activate on file pattern match
- `fileMatchPattern: '**/*.tsx'` - Glob pattern to match

#### 3. Manual Inclusion
Included only when user references with `#` in chat.

**Example:** `.claude/steering/deployment-guide.md`
```markdown
---
inclusion: manual
---

# Deployment Guide

## Production Deployment
1. Run tests: `npm test`
2. Build: `npm run build`
3. Deploy: `npm run deploy:prod`

## Environment Variables
- `API_URL`: Backend API endpoint
- `AUTH_TOKEN`: Authentication token
```

### File References in Steering
Include external files using special syntax:

```markdown
# API Documentation

Our API follows this OpenAPI specification:

#[[file:docs/openapi.yaml]]

Use this spec when implementing API calls.
```

### Best Practices for Steering Files

1. **Keep them focused** - One topic per file
2. **Use descriptive names** - `react-patterns.md` not `rules.md`
3. **Update regularly** - Keep in sync with project changes
4. **Use conditional inclusion** - Reduce context noise
5. **Include examples** - Show, don't just tell

---

## Agent Hooks

### What are Agent Hooks?
Automated triggers that execute actions when specific events occur in the IDE.

### Location
Configured via Kiro UI, stored in workspace settings.

### Access Hooks
1. **Explorer View:** Look for "Agent Hooks" section
2. **Command Palette:** "Open Kiro Hook UI"

### Hook Types

#### Event Triggers
- **On Message Sent** - When user sends a message
- **On Agent Complete** - When Kiro finishes execution
- **On Session Created** - On first message in new session
- **On File Save** - When user saves a file
- **Manual Button** - User clicks a button

#### Actions
1. **Send Message to Agent** - Remind Kiro of something
2. **Execute Shell Command** - Run a script or command

### Hook Examples

#### Auto-Run Tests on Save
```
Trigger: On File Save
Pattern: **/*.test.ts
Action: Execute Command
Command: npm test -- ${filePath}
```

#### Update Translations
```
Trigger: On File Save
Pattern: **/locales/en.json
Action: Send Message
Message: "Translation file updated. Please check if other language files need updates."
```

#### Spell Check README
```
Trigger: Manual Button
Label: "Spell Check"
Action: Send Message
Message: "Review and fix grammar errors in README.md"
```

---

## Permissions Configuration

### Permission Patterns
Control what Kiro can do automatically vs. what requires approval.

### Pattern Syntax
```
ToolName(operation:pattern)
```

**Examples:**
- `Bash(find:*)` - All find commands
- `readFile:src/**` - Read files in src folder
- `executePwsh:*` - All PowerShell commands
- `deleteFile:**` - Delete any file

### Security Best Practices

**Always Allow (Safe Operations):**
```json
"allow": [
  "readFile:**/*.md",
  "readFile:**/*.json",
  "listDirectory:**",
  "grepSearch:**",
  "getDiagnostics:**"
]
```

**Always Deny (Dangerous Operations):**
```json
"deny": [
  "Bash(rm:-rf:*)",
  "deleteFile:**/.git/**",
  "deleteFile:**/node_modules/**",
  "executePwsh:Remove-Item:-Recurse:*"
]
```

**Ask First (Potentially Risky):**
```json
"ask": [
  "deleteFile:**",
  "executePwsh:*",
  "strReplace:**/*.config.js"
]
```

---

## View Settings

### Customizing Kiro Panels

Control which panels appear in your Kiro IDE interface.

### Available Views

**Specs Panel**
- Purpose: Structured feature development workflow
- Shows: Active specs, design docs, implementation tasks
- Recommended: `true` for complex projects

**Steering Panel**
- Purpose: Manage context and instruction files
- Shows: All steering files, inclusion status
- Recommended: `true` for team projects

**MCP Panel**
- Purpose: Manage Model Context Protocol servers
- Shows: Server status, available tools
- Recommended: `true` if using MCP servers

**Hooks Panel**
- Purpose: Manage automated agent triggers
- Shows: Configured hooks, trigger events
- Recommended: `true` for automation workflows

**Settings Panel**
- Purpose: Quick access to configuration
- Shows: Settings files, quick edit options
- Recommended: `false` (use file explorer instead)

---

## Spec Configuration

### What are Specs?
Structured workflow for building complex features with Kiro.

### Spec Workflow
1. **Requirements** - Define what to build
2. **Design** - Plan the implementation
3. **Tasks** - Break down into steps
4. **Implementation** - Build the feature
5. **Testing** - Verify it works

### Location
Defined in `kfc-settings.json`:
```json
{
  "paths": {
    "specs": ".claude/specs"
  }
}
```

### Creating a Spec
Specs use markdown with special syntax for file references:

```markdown
# Feature: User Authentication

## Requirements
- Users can log in with email/password
- JWT tokens for session management
- Password reset functionality

## Design
Follow the authentication pattern in:
#[[file:docs/auth-architecture.md]]

## Implementation Tasks
1. Create login API endpoint
2. Implement JWT middleware
3. Build login UI component
4. Add password reset flow
```

### Spec Agents
Located in `.claude/agents/kfc/`:
- `spec-requirements.md` - Gather requirements
- `spec-design.md` - Create design
- `spec-tasks.md` - Break into tasks
- `spec-impl.md` - Implement features
- `spec-test.md` - Test implementation

---

## Best Practices

### 1. Start Simple
Begin with minimal configuration and add as needed:
```json
{
  "permissions": {
    "allow": ["readFile:**"],
    "deny": ["deleteFile:**"],
    "ask": []
  }
}
```

### 2. Use Version Control
Commit workspace configs to share with team:
```
.claude/
├── settings/
│   ├── kfc-settings.json    ✓ Commit
│   └── mcp.json             ✓ Commit (without secrets)
├── steering/                ✓ Commit
└── settings.local.json      ✗ Add to .gitignore
```

### 3. Separate Secrets
Never commit API keys or tokens:
```json
{
  "mcpServers": {
    "api-server": {
      "env": {
        "API_KEY": "${API_KEY}"  // Use environment variable
      }
    }
  }
}
```

### 4. Document Your Config
Add comments in steering files explaining decisions:
```markdown
# Project Configuration

## Why We Use TypeScript
We chose TypeScript for type safety and better IDE support.
This decision was made in Q4 2024 and applies to all new code.
```

### 5. Regular Maintenance
- Review steering files monthly
- Update MCP servers to latest versions
- Remove unused hooks and permissions
- Test configurations after updates

### 6. Team Alignment
- Share configuration guide with team
- Document custom MCP servers
- Explain steering file purposes
- Review permissions together

---

## Quick Reference

### Essential Files
```
.claude/
├── settings.local.json          # Permissions
├── settings/
│   ├── kfc-settings.json       # Views and paths
│   └── mcp.json                # MCP servers
└── steering/
    └── *.md                    # Context files
```

### Common Commands
```bash
# View MCP config (workspace)
cat .claude/settings/mcp.json

# View MCP config (user)
cat ~/.kiro/settings/mcp.json

# Test MCP server
uvx package-name@latest

# Reconnect MCP servers
# Use Command Palette: "MCP: Reconnect Server"
```

### Getting Help
1. Command Palette → Search "Kiro" or "MCP"
2. Ask Kiro: "How do I configure [feature]?"
3. Check `.claude/` folder for examples
4. Review this guide

---

## Troubleshooting

### MCP Server Won't Start
1. Check `uvx` is installed: `uvx --version`
2. Test server manually: `uvx package-name@latest`
3. Check environment variables in config
4. View server logs in MCP panel

### Steering Files Not Working
1. Verify file location matches `kfc-settings.json`
2. Check front matter syntax for conditional files
3. Ensure markdown formatting is correct
4. Try manual inclusion with `#filename`

### Permissions Not Applied
1. Check pattern syntax matches tool names
2. Verify `settings.local.json` is valid JSON
3. Restart Kiro IDE
4. Check for conflicting patterns

### Hooks Not Triggering
1. Verify event type matches your use case
2. Check file patterns for file-based triggers
3. Test with manual button trigger first
4. Review hook configuration in UI

---

## Additional Resources

- **Kiro Documentation:** Check built-in help
- **MCP Servers:** https://github.com/modelcontextprotocol
- **Community Examples:** Share configs with team
- **This Guide:** Keep updated with your learnings

---

*Last Updated: December 2024*
*Version: 1.0*
