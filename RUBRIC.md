# Assignment 2: Grading Rubric (100 points)

Every line item lists the points available and what the grader will look for. The grader will run your `main.py` on a clean clone first, then read the code.

If your project does not run from `uv sync && uv run python main.py` on a fresh clone, you start at 0 and we work back up from what we can verify by reading the code. **Make sure it runs.**

---

## A. LangGraph correctness and design: 30 points

| # | Criterion | Points | What we look for |
|---|---|---:|---|
| A1 | Graph compiles and produces `graph_out/graph.png` | 4 | The PNG is committed and reasonably current with the code |
| A2 | State is a TypedDict storing raw data only | 4 | No prompt strings, no derived booleans, no formatted text in state. Format on demand inside nodes. |
| A3 | Nodes are small, single-purpose, and type-annotated | 4 | Each node has a clear name, a docstring, and a `Command[Literal[...]]` return annotation where routing happens |
| A4 | Static edges are minimal, routing happens inside nodes | 4 | Most decisions use `Command(goto=...)`, not `add_conditional_edges` everywhere |
| A5 | Checkpointer is wired correctly | 4 | `InMemorySaver()` (or production checkpointer) is used; runs can resume by `thread_id` |
| A6 | Compiled graph reflects the design in your README | 5 | We can read the README, then the PNG, then the code, and they agree |
| A7 | No prompts in state | 5 | Inspecting `state.py` shows zero prompt-shaped strings |

---

## B. Pattern coverage: 25 points (the heart of the grade)

You **must** demonstrably implement every row. Each row is worth a small slice. Grader will ask you to point at the node, the line, or the edge during the demo.

| # | Pattern | Points | Hint to show it |
|---|---|---:|---|
| B1 | Structured output | 2 | `with_structured_output(SomeSchema)` for the seniority classifier |
| B2 | Tool calling | 2 | At least two `@tool` functions bound to an LLM |
| B3 | `MessagesState` short-term memory | 2 | Multi-turn agent or critic loop preserves history |
| B4 | Prompt chaining | 2 | A sub-pipeline runs two or more sequential LLM calls |
| B5 | Parallelization with reducer | 3 | Three scoring nodes write to the same key, reducer concatenates |
| B6 | Routing (LLM-based) | 2 | Seniority classifier branches the graph |
| B7 | Orchestrator-worker with `Send` | 3 | One worker per required skill in the JD |
| B8 | Evaluator-optimizer loop | 3 | Critic LLM grades the email; loop retries; bounded with attempt counter |
| B9 | Agent with tools | 2 | A research agent decides when to call tools and when to stop |
| B10 | `RetryPolicy` on at least two external calls | 1 | Attached at `add_node` with `retry_on=...` to limit blast radius |
| B11 | LLM-recoverable loopback | 1 | A tool failure becomes data, agent reasons about it |
| B12 | `interrupt()` for human review | 1 | Borderline candidates pause; resume works |
| B13 | Saga / compensation | 1 | Failure in `send_email` or `update_ats` routes to a compensation node |

Total: 25.

If a pattern is present but obviously contrived (e.g. orchestrator-worker that always spawns one worker), expect partial credit.

---

## C. Project structure and code quality: 15 points

| # | Criterion | Points | What we look for |
|---|---|---:|---|
| C1 | Multi-file layout with clean separation | 3 | `state.py`, `nodes/`, `graph.py`, `services.py`, `prompts.py` or similar. Not one mega-file. |
| C2 | Dependency hygiene | 3 | `pyproject.toml` with pinned major versions; `uv sync` works first try |
| C3 | Configuration via env vars | 2 | API keys come from `.env`; `.env.example` lists every var the code reads |
| C4 | Mock fallback for every external service | 3 | Project runs end to end with `USE_MOCKS=true` and no third-party keys |
| C5 | Readable code | 2 | Functions under ~30 lines, clear names, no dead code |
| C6 | Style consistency | 2 | One LLM provider (OpenAI or Anthropic) chosen consistently; no leftover demo code |

---

## D. Tests: 10 points

| # | Criterion | Points | What we look for |
|---|---|---:|---|
| D1 | State test | 2 | Construct a `HireGraphState`; assert defaults and required fields |
| D2 | One node test with the LLM mocked | 3 | A node runs with a fake LLM; you assert on the returned `Command(update=..., goto=...)` |
| D3 | End-to-end test with the in-memory checkpointer | 3 | One borderline scenario; the test invokes, asserts pause, resumes with a fake decision, asserts final state |
| D4 | `pytest -q` passes on a clean clone | 2 | We will run it |

---

## E. User-facing demo (UI + CLI): 10 points

| # | Criterion | Points | What we look for |
|---|---|---:|---|
| E1 | `main.py` runs three scenarios end to end | 4 | Includes the borderline scenario with auto-approval at the interrupt |
| E2 | Output is readable | 2 | Pretty trace lines, a final scoreboard table, no raw dict dumps |
| E3 | UI lets a reviewer trigger a run and approve an interrupt | 3 | Vibecoded UI is fine; what matters is it works end to end |
| E4 | UI shows the rendered graph PNG | 1 | A small section of the page displays `graph_out/graph.png` |

---

## F. Documentation: 5 points

| # | Criterion | Points | What we look for |
|---|---|---:|---|
| F1 | README setup section is correct | 1 | A grader on a fresh laptop can follow it |
| F2 | README design section | 2 | Short. Explains state, routing, where each pattern lives. Embeds the graph PNG. |
| F3 | Design trade-offs called out | 1 | One paragraph on what you chose and why (model, retry counts, attempt cap) |
| F4 | Mocks vs real APIs clearly documented | 1 | A table of which services you used real and which you mocked |

---

## G. Presentation: 10 points (graded in class)

| # | Criterion | Points | What we look for |
|---|---|---:|---|
| G1 | Clear problem statement | 1 | 90 seconds, no fluff |
| G2 | Live demo through your UI | 3 | At least one borderline scenario that triggers the interrupt |
| G3 | Walk through the graph PNG | 2 | Point at each pattern from Section B |
| G4 | Show one trace (LangSmith or printed) | 2 | Demonstrate the flow with real data |
| G5 | Reflection: what was hard, what you learned | 2 | Honest, specific. We want to know what stuck. |

---

## H. Bonus (up to +10 points, optional)

Pick at most two. We will not award more than 10 bonus points total.

| Bonus | Points | What it takes |
|---|---:|---|
| Real GitHub API integration with caching | +3 | Hit the GitHub REST API with auth, cache responses; degrade to mock on rate limit |
| Real Tavily web search wired up | +2 | The research agent actually uses it; document one trace where it changed the decision |
| Mailtrap sandbox integration | +2 | `send_email` posts to a sandbox inbox; include a screenshot |
| Postgres checkpointer instead of `InMemorySaver` | +3 | Resume across a process restart; show that the same `thread_id` continues from disk |
| Confidence-vote ensemble for the classifier | +2 | Run the classifier three times and take a majority vote with a custom reducer |
| Streaming UI | +2 | The web UI streams node updates as they happen |
| LangSmith traces with custom run names | +1 | Every node has a sensible name in the trace tree |
| Cost dashboard | +2 | Print or surface per-run token cost and wall time |
| Multi-language resumes | +1 | English plus one non-English resume, gracefully handled |
| Public deploy | +1 | Deploy to Render / Railway / Fly and share the link |

---

## What will lose you points fast

- The graph compiles but `main.py` raises on import (`-15`).
- State holds prompt strings (`-5`).
- One mega-file with all nodes and the graph in it (`-3`).
- No mock fallback, requires multiple paid API keys to run (`-5`).
- Project uses LangChain LCEL or plain `asyncio` instead of LangGraph for the orchestration (`-25`).
- AI-generated code that you cannot explain in the demo (`-10`).
- Hidden API keys committed to the repo (immediate `0` for the assignment).

---

## Final note

The rubric is harsh on purpose. The point of Assignment 2 is to leave the course with one **real** LangGraph project on your GitHub. Treat the code like something you would link from your CV. We will read it that way.
