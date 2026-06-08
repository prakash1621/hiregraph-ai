# Submission Checklist

Tick every box before you tag `v1.0`. The grader will check each one.

## Repository hygiene

- [ ] Repo is public, or private and shared with the instructor
- [ ] `README.md` at the root explains setup, run, and design
- [ ] `.env.example` lists every variable the code reads
- [ ] `.env` is **not** committed
- [ ] No API keys anywhere in the repo (search the diff before pushing)
- [ ] `uv sync` works on a fresh clone
- [ ] `uv run python main.py` runs end to end on a fresh clone with mocks (`HIREGRAPH_USE_MOCKS=true`)

## Functionality

- [ ] At least three scenarios run from `main.py` (strong, weak, borderline)
- [ ] The borderline scenario pauses at `interrupt()` and resumes cleanly
- [ ] `graph_out/graph.png` is committed and reflects the current code

## Patterns (point at each one in your demo)

- [ ] Structured output with `with_structured_output`
- [ ] Tool calling with at least two `@tool` functions
- [ ] `MessagesState` short-term memory
- [ ] Prompt chaining sub-pipeline
- [ ] Parallel scoring with a reducer
- [ ] Routing based on the classifier
- [ ] Orchestrator-worker with `Send`
- [ ] Evaluator-optimizer loop with attempt cap
- [ ] Agent with tools
- [ ] `RetryPolicy` on at least two nodes with `retry_on=...`
- [ ] LLM-recoverable loopback (error becomes data, agent re-tries)
- [ ] `interrupt()` works with the checkpointer
- [ ] Saga / compensation path

## Tests

- [ ] State test
- [ ] One node test with the LLM mocked
- [ ] One end-to-end test with the checkpointer
- [ ] `pytest -q` passes

## UI and CLI

- [ ] `main.py` prints a readable trace and a final scoreboard
- [ ] UI lets a reviewer trigger a run, approve an interrupt, and see the final scorecard
- [ ] UI displays the rendered graph PNG

## Docs

- [ ] README has a Setup section
- [ ] README has a Design section with the graph PNG embedded
- [ ] README has a Trade-offs section
- [ ] README has a "Mocks vs real APIs" table

## Presentation

- [ ] 10-minute deck under `presentation/`
- [ ] Live demo planned (which scenario, which pause, which trace)
- [ ] Reflection slide: one thing that was hard, one thing you learned

## Submission

- [ ] Tag the submission commit `v1.0`
- [ ] Open the submission issue with the commit link, optional LangSmith trace, and reflection paragraph
