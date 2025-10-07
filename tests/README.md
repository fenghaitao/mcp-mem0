# Tests

This directory contains tests for the mem0-mcp server with GitHub Copilot integration.

## Test Files

### `test_simple.py`
Tests the core mem0 functionality with GitHub Copilot models.

**What it tests:**
- mem0 client creation with GitHub Copilot configuration
- Memory save operations
- Memory search operations  
- Memory retrieval operations
- Database connectivity

**Run:**
```bash
cd ..
.venv/bin/python3 tests/test_simple.py
```

### `test_mcp_proper.py`
Tests the MCP server protocol compliance and tool functionality.

**What it tests:**
- MCP server initialization
- Protocol compliance (JSON-RPC 2.0)
- Tool registration and listing
- Tool calling interface

**Run:**
```bash
cd ..
.venv/bin/python3 tests/test_mcp_proper.py
```

## Prerequisites

1. Make sure the virtual environment is activated and dependencies are installed:
   ```bash
   source .venv/bin/activate
   uv pip install -e .
   ```

2. Ensure your `.env` file is configured with:
   ```bash
   LLM_PROVIDER=github_copilot
   LLM_CHOICE=github_copilot/gpt-4o-mini
   EMBEDDING_MODEL_CHOICE=github_copilot/text-embedding-3-small
   DATABASE_URL=your_supabase_url
   ```

## Expected Results

Both tests should pass without errors, confirming that:
- ✅ GitHub Copilot models are working
- ✅ Memory operations are functional
- ✅ MCP server starts correctly
- ✅ Database connections are established