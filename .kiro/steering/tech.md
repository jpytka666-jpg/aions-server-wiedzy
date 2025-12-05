---
inclusion: always
---

# AIONS Technology Stack

## Core Technologies

### Python 3.11+
- **Primary language** dla całego backendu
- **Type hints** wymagane dla wszystkich funkcji
- **Async/await** dla operacji I/O
- **Virtual environment** w `venv/`

### ChromaDB
- **Vector database** dla semantycznego wyszukiwania
- **Persist path**: `E:/server wiedzy/data/chroma`
- **Collections**: per-session storage
- **Embeddings**: default (all-MiniLM-L6-v2)

### MCP (Model Context Protocol)
- **FastMCP** framework dla serwerów
- **stdio** transport
- **JSON-RPC** komunikacja
- **Auto-approve** dla zaufanych narzędzi

### AWS Services
- **Aurora DSQL** - PostgreSQL-compatible serverless database
- **Region**: eu-west-2
- **Profile**: 125140434314
- **IAM auth** z 15-minutowymi tokenami

## Development Tools

### IDE
- **Kiro IDE** - główne środowisko z AI assistance
- **VS Code** - backup dla szybkich edycji

### Version Control
- **Git** - C:/Program Files/Git/bin/git.exe
- **GitHub** - remote repository (PRIVATE)
- **Auto-commit** - hook na zapis pliku

### Search
- **Everything** - C:/Program Files/Everything/es.exe
- **Blazing fast** file search na Windows

### Containers
- **Docker** - dla izolowanych środowisk
- **WSL2/Ubuntu** - Linux environment na Windows

## Code Conventions

### Python Style
```python
# Type hints required
def function_name(param: str, count: int = 10) -> Dict[str, Any]:
    """Docstring required for public functions."""
    pass

# Constants in UPPER_SNAKE_CASE
MAX_RESULTS = 100
REPO_ROOT = Path(__file__).resolve().parents[3]

# Classes in PascalCase
class VectorStore:
    pass

# Functions/variables in snake_case
def get_vector_store():
    pass
```

### File Organization
```
module/
├── __init__.py
├── models.py      # Data models
├── store.py       # Storage logic
├── utils.py       # Helper functions
└── tests/
    └── test_*.py  # Tests mirror source
```

### Error Handling
```python
# Always use explicit exceptions
try:
    result = risky_operation()
except SpecificError as e:
    log(f"Operation failed: {e}")
    return _error(str(e))
```

## Dependencies

### Core (requirements.txt)
- chromadb
- fastmcp
- pydantic
- httpx
- python-dotenv

### Development
- pytest
- ruff (linting)
- mypy (type checking)

## Environment Variables

### Required
- `CHROMA_PATH` - ChromaDB storage path
- `PYTHONPATH` - Python module paths
- `AWS_PROFILE` - AWS credentials profile

### Optional
- `FASTMCP_LOG_LEVEL` - MCP logging level (ERROR/INFO/DEBUG)

## Security

### Never commit
- API keys (sk-proj-*, ghp_*, AKIA*)
- Passwords
- .env files with secrets
- AWS credentials

### Always use
- Environment variables for secrets
- .gitignore for sensitive files
- IAM roles for AWS access

## Performance Guidelines

### ChromaDB
- Batch operations for multiple items
- Limit query results (n_results=10)
- Use metadata filtering

### MCP Tools
- Timeout: 30s default
- Max results: 50-100
- Streaming for large outputs

### File Operations
- Use Everything for search (not os.walk)
- Partial reads for large files
- Async for I/O operations
