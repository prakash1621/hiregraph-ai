# HireGraph - How to Run

## Quick Start (CLI)

```bash
# 1. Install dependencies
pip install -r requirements.txt
# or with uv:
uv sync

# 2. Set your LLM API key in .env
#    Copy .env.example to .env and fill in your key:
#    OPENAI_API_KEY=sk-...
#    or
#    ANTHROPIC_API_KEY=sk-ant-...

# 3. Run the demo (3 scenarios end-to-end)
python main.py
```

This will:
1. Compile the LangGraph graph
2. Generate `graph_out/graph.png`
3. Run three scenarios (Priya=advance, Mira=reject, Eitan=borderline/reject)
4. Print a scoreboard summary

---

## Run the API + Web UI

```bash
# Start the FastAPI server
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload

# Open browser to:
# http://localhost:8000
```

The UI lets you:
- Select sample resumes (including .docx) and JDs from dropdowns
- Paste custom resume/JD text
- Click "Evaluate Candidate" and see results (takes 15-30 seconds)
- View scorecard, email draft, and audit trail

---

## Run the Notebook

```bash
# From the project root:
jupyter notebook notebooks/walkthrough.ipynb

# Or with VS Code: open notebooks/walkthrough.ipynb directly
```

The notebook walks through:
- Building and visualizing the graph
- Inspecting the state schema
- Running all 3 scenarios step by step
- Examining scorecards, email drafts, and audit trails

Note: The notebook uses `os.chdir("..")` to set the working directory to the project root, so it works when launched from the `notebooks/` folder.

---

## Run Tests

```bash
# All tests (22 pass, 4 skip without LLM key)
pytest tests/ -v

# By category:
pytest tests/test_state.py -v      # State schema tests
pytest tests/test_nodes.py -v      # Node tests with mocked LLM
pytest tests/test_parser.py -v     # File parser tests
pytest tests/test_e2e.py -v        # End-to-end tests (need LLM key)
```

---

## Project Structure

```
agent_HireGraph/
  main.py                    CLI entry point (runs 3 scenarios)
  pyproject.toml             Dependencies
  .env.example               Required environment variables
  .env                       Your API keys (not committed)

  src/hiregraph/
    __init__.py
    types.py                 HireGraphState TypedDict, Decision dataclass
    nodes.py                 All node functions (classify, score, draft, evaluate)
    graph.py                 Graph builder with StateGraph + MemorySaver
    parser.py                File parser (PDF, DOCX, MD, TXT)

  api/
    __init__.py
    server.py                FastAPI server with /evaluate, /sample-data, /health

  ui/
    index.html               Single-page web UI

  tests/
    test_state.py            State schema tests
    test_nodes.py            Node tests with mocked LLM
    test_parser.py           File parser tests
    test_e2e.py              End-to-end graph tests

  notebooks/
    walkthrough.ipynb        Jupyter notebook walkthrough

  sample_data/
    resumes/                 resume_priya.md, resume_eitan.md, resume_mira.md, PRAKASH_D_Data_Engineer_CV.docx
    jds/                     jd_senior_backend.md, jd_junior_data.md, jd_senior.md
    expected_outcomes.md     Truth table for grading

  graph_out/
    graph.png                Compiled graph visualization

  docs/architecture/
    hiregraph_architecture.png      Reference architecture diagram
    hiregraph_architecture.drawio   Editable source
```

---

## What's Implemented

| Pattern | Status | Where |
|---------|--------|-------|
| TypedDict state with raw data | Done | `src/hiregraph/types.py` - `HireGraphState` |
| Structured output (Pydantic) | Done | `nodes.py` - `SeniorityClassification` with `with_structured_output` |
| Parallelization with reducer | Done | `graph.py` - 4 scoring nodes fan-out/fan-in, `Annotated` reducers |
| Conditional routing | Done | `graph.py` - `route_after_evaluation` (advance/reject/borderline) |
| Checkpointer | Done | `graph.py` - `MemorySaver` compiled in |
| Audit trail | Done | Every node appends to `audit_trail` via `operator.add` reducer |
| Email drafting | Done | `nodes.py` - `draft_email` with personalized LLM output |
| Email evaluation (critic) | Done | `nodes.py` - `evaluate_email` grades the draft |
| File parsing (PDF, DOCX, MD) | Done | `parser.py` - supports multiple formats |

---

## What's Not Yet Implemented

| Pattern | Notes |
|---------|-------|
| `Command(goto=...)` self-routing | Using `add_conditional_edges` instead |
| `RetryPolicy` | Not attached to any node |
| `interrupt()` for human review | Checkpointer wired but interrupt never called |
| Saga / compensation | `end_error` node exists but unreachable |
| Orchestrator + Worker with `Send` | Parallel scoring uses static edges, not `Send` |
| Research agent with `ToolNode` | No tools defined |
| Tool calling (`@tool` functions) | Not implemented |
| `MessagesState` / short-term memory | All LLM calls are single-shot |
| Prompt chaining (multi-step LLM) | Each node makes 1 LLM call |
| LLM-based routing by seniority | Seniority classified but not used to branch |
| Evaluator-optimizer retry loop | Critic runs once, no redraft loop |
| LLM-recoverable loopback | Errors silently default, not routed back |
| `services.py` with mock toggle | Not implemented |

---

## LLM Calls Per Run

7 total per candidate evaluation:
1. `classify_seniority` - structured output classification
2. `score_skills` - skills dimension scoring
3. `score_experience` - experience dimension scoring
4. `score_education` - education dimension scoring
5. `score_public_signals` - public signals scoring
6. `draft_email` - personalized email generation
7. `evaluate_email` - email quality assessment

---

## Environment Variables

```bash
# Required (one of these):
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional:
LLM_PROVIDER=openai          # or "anthropic"
```
