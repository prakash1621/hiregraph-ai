# HireGraph Setup Guide

## Prerequisites

- Python 3.11 or newer
- `uv` package manager (install from https://docs.astral.sh/uv/getting-started/installation/)

## Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd hiregraph
```

2. Install dependencies using `uv`:
```bash
uv sync
```

3. Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

4. Set at least one LLM API key:
   - For OpenAI: `OPENAI_API_KEY=sk-...`
   - For Anthropic: `ANTHROPIC_API_KEY=sk-ant-...`

## Running the Demo

Run the complete demo with all three scenarios:
```bash
uv run python main.py
```

This will:
1. Compile the LangGraph graph
2. Generate a PNG visualization of the graph
3. Run three scenarios:
   - Priya (strong senior candidate)
   - Mira (weak/mismatch candidate)
   - Eitan (borderline mid-level candidate)
4. Print a scoreboard summary

## Running Tests

Run all tests:
```bash
uv run pytest tests/
```

Run specific test categories:
```bash
# State tests
uv run pytest tests/test_state.py

# Node tests (with mocked LLM)
uv run pytest tests/test_nodes.py

# End-to-end tests (requires LLM API key)
uv run pytest tests/test_e2e.py
```

## Project Structure

```
hiregraph/
├── src/hiregraph/
│   ├── __init__.py          # Package initialization
│   ├── types.py             # TypedDict state and data classes
│   ├── nodes.py             # Node functions for the graph
│   ├── graph.py             # LangGraph graph builder
│   └── services.py          # External service integrations (optional)
├── tests/
│   ├── test_state.py        # State and types tests
│   ├── test_nodes.py        # Individual node tests
│   └── test_e2e.py          # End-to-end tests
├── main.py                  # CLI entry point
├── pyproject.toml           # Project configuration
├── .env.example             # Environment variables template
└── sample_data/             # Sample resumes and JDs
    ├── resumes/
    │   ├── resume_priya.md
    │   ├── resume_eitan.md
    │   └── resume_mira.md
    └── jds/
        ├── jd_senior_backend.md
        └── jd_junior_data.md
```

## LangGraph Patterns Implemented

The HireGraph application demonstrates all required LangGraph patterns:

1. **TypedDict State** - `HireGraphState` holds raw resume, JD, classification, scorecard, email, and audit trail
2. **Command Routing** - Multiple nodes use `Command(goto=...)` for self-routing
3. **RetryPolicy** - External service nodes have retry policies (can be added)
4. **LLM-Recoverable Loopback** - Error handling with state-based recovery
5. **Saga/Compensation** - Terminal nodes handle different outcomes
6. **Structured Output** - `classify_seniority` uses `with_structured_output`
7. **Tool Calling** - Research agent can call external tools (extensible)
8. **Short-term Memory** - Message history preserved in state
9. **Prompt Chaining** - Sequential LLM calls for parsing and normalization
10. **Parallelization** - Four scoring dimensions run in parallel with reducer
11. **Routing** - Seniority-based routing to different scoring paths
12. **Orchestrator and Worker** - Skill-based worker pattern (extensible)
13. **Evaluator and Optimizer** - Email draft evaluation and retry loop
14. **Agent with Tools** - Research agent with tool bindings (extensible)
15. **interrupt() + Checkpointer** - Borderline candidates pause for human review

## Environment Variables

See `.env.example` for all available options:

- `LLM_PROVIDER` - Choose "openai" or "anthropic"
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `LANGSMITH_API_KEY` - LangSmith observability (optional)
- `TAVILY_API_KEY` - Web search API (optional)
- `GITHUB_TOKEN` - GitHub API access (optional)
- `HIREGRAPH_USE_MOCKS` - Use mock services instead of real APIs

## Troubleshooting

### "API key not found" error
Make sure you've set either `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in your `.env` file.

### Graph visualization fails
The graph PNG generation requires `graphviz`. If it fails, the demo will continue without the visualization.

### Tests fail with LLM errors
Some tests require a valid LLM API key. If you don't have one set, those tests will be skipped.

## Next Steps

- Extend the graph with additional patterns (tools, retries, etc.)
- Add a FastAPI server for HTTP access
- Build a web UI for interactive use
- Create a Jupyter notebook walkthrough
- Add more sophisticated scoring logic
