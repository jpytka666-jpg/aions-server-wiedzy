# Implementation Plan

## Phase 1: Master MCP Config (bez duplikatów)

- [x] 1. Update MCP configuration








  - [ ] 1.1 Backup current mcp.json
  - [ ] 1.2 Remove duplicate servers (aws-knowledge, dynamodb, serverless, playwright)
  - [ ] 1.3 Keep AIONS-CONTEXT as primary (startupDelay: 0)
  - [ ] 1.4 Keep aurora-dsql for direct AWS connection
  - [ ] 1.5 Keep fetch for web requests
  - [ ] 1.6 Disable stripe (optional, needs API key)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

## Phase 2: Tier 1 Agent Hooks (Auto on Save)


- [ ] 2. Create auto-test-python hook
  - [ ] 2.1 Create auto-test-python.json with onFileSave trigger for *.py
  - [ ] 2.2 Action: sendMessage to run pytest for saved file
  - _Requirements: 2.1_

- [ ] 3. Create auto-lint-python hook
  - [ ] 3.1 Create auto-lint-python.json with onFileSave trigger for *.py
  - [ ] 3.2 Action: sendMessage to run ruff/flake8 linting
  - _Requirements: 2.2_

- [ ] 4. Create auto-security-scan hook
  - [ ] 4.1 Create auto-security-scan.json with onFileSave trigger for code files
  - [ ] 4.2 Action: sendMessage to scan for API keys and secrets
  - _Requirements: 2.3_

- [ ] 5. Create auto-validate-config hook
  - [ ] 5.1 Create auto-validate-config.json with onFileSave trigger for *.json/*.yaml
  - [ ] 5.2 Action: sendMessage to validate JSON/YAML syntax
  - _Requirements: 2.4_

## Phase 3: Tier 2 Agent Hooks (Manual Buttons)

- [ ] 6. Create manual-validate-mcp hook
  - [ ] 6.1 Create manual-validate-mcp.json with manual trigger
  - [ ] 6.2 Action: sendMessage to test all MCP server connections
  - _Requirements: 3.1_

- [ ] 7. Create manual-validate-env hook
  - [ ] 7.1 Create manual-validate-env.json with manual trigger
  - [ ] 7.2 Action: sendMessage to check .env files and environment variables
  - _Requirements: 3.2_

- [ ] 8. Create manual-api-schema hook
  - [ ] 8.1 Create manual-api-schema.json with manual trigger
  - [ ] 8.2 Action: sendMessage to validate OpenAPI/GraphQL schemas
  - _Requirements: 3.3_

- [ ] 9. Create manual-commit-helper hook
  - [ ] 9.1 Create manual-commit-helper.json with manual trigger
  - [ ] 9.2 Action: sendMessage to generate commit message from git diff
  - _Requirements: 3.4_

- [ ] 10. Create manual-spell-check hook
  - [ ] 10.1 Create manual-spell-check.json with manual trigger
  - [ ] 10.2 Action: sendMessage to check spelling in README files
  - _Requirements: 3.5_

## Phase 4: Tier 3 Agent Hooks (Optional/Advanced)

- [ ] 11. Create optional-test-mcp hook
  - [ ] 11.1 Create optional-test-mcp.json with manual trigger
  - [ ] 11.2 Action: sendMessage to test each MCP server with sample calls
  - _Requirements: 4.1_

- [ ] 12. Create optional-check-deps hook
  - [ ] 12.1 Create optional-check-deps.json with manual trigger
  - [ ] 12.2 Action: sendMessage to check for outdated packages in requirements.txt
  - _Requirements: 4.2_

- [ ] 13. Create optional-coverage hook
  - [ ] 13.1 Create optional-coverage.json with manual trigger
  - [ ] 13.2 Action: sendMessage to run pytest with coverage report
  - _Requirements: 4.3_

- [ ] 14. Create optional-performance hook
  - [ ] 14.1 Create optional-performance.json with manual trigger
  - [ ] 14.2 Action: sendMessage to analyze code for performance issues
  - _Requirements: 4.4_

## Phase 5: Missing Steering Rules

- [ ] 15. Create product.md steering rule
  - [ ] 15.1 Create product.md with AIONS project vision, goals, target users
  - [ ] 15.2 Include feature list and roadmap
  - _Requirements: 5.1_

- [ ] 16. Create tech.md steering rule
  - [ ] 16.1 Create tech.md with technology stack (Python, FastAPI, ChromaDB, MCP, AWS)
  - [ ] 16.2 Include development tools and conventions
  - _Requirements: 5.2_

## Phase 6: Verification

- [ ] 17. Verify implementation
  - [ ] 17.1 Test MCP config by checking server connections
  - [ ] 17.2 Test hooks by triggering each one
  - [ ] 17.3 Verify steering rules are loaded by agent
  - _Requirements: All_
