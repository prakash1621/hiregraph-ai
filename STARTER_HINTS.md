# Starter hints (read after the README)

Stuck? These are guardrails, not a solution. Most students need them only after Day 3.

## A suggested state schema

You may diverge. The point of the schema below is that *every* field stores raw data.

```python
from typing import TypedDict, Annotated, Literal
import operator

class Skill(BaseModel):
    name: str
    required_years: int | None = None

class Classification(BaseModel):
    seniority: Literal["junior", "mid", "senior", "executive"]
    role_family: str   # "backend", "frontend", "data", ...
    confidence: float

class SkillScore(BaseModel):
    skill: str
    score: int   # 0 to 100
    evidence: str

class HireGraphState(TypedDict):
    # Inputs
    candidate_id: str
    resume_text: str
    jd_text: str

    # Classification
    classification: Classification | None

    # JD-derived plan
    required_skills: list[Skill] | None

    # Parallel scoring
    skill_scores: Annotated[list[SkillScore], operator.add]
    experience_score: int | None
    education_score: int | None
    signal_score: int | None   # github / writing / etc

    # Aggregate
    final_score: int | None
    recommendation: Literal["advance", "reject", "borderline"] | None

    # Drafting + critic
    email_draft: str | None
    critic_feedback: list[dict] | None   # full history of critic passes
    draft_attempts: int

    # Outcome
    sent_status: Literal["sent", "failed", "pending"] | None
    audit_trail: Annotated[list[str], operator.add]
```

## A suggested graph shape

```
                   START
                     v
                 ingest
                     v
            classify_seniority           (LLM, with_structured_output -> Classification)
                     v
            plan_required_skills          (LLM, returns list[Skill])
            +--------+--------+--------+--------+
            v        v        v        v
   per_skill_worker  ... (Send fan out, one per required_skill)
            +--------+--------+--------+--------+
                            v
                   experience_scorer  ----+
                   education_scorer  ----+----> all parallel,
                   signal_scorer    -----+      reducer on skill_scores
                            v
                    aggregate_scores                (computes final_score, recommendation)
                            v
                +-----------+-----------+
                v           v           v
            reject_path  borderline   advance_path
                            v
                      (interrupt for human review)
                            v
                  draft_email (LLM)
                            v
                  critic_loop (evaluator-optimizer; up to 3 attempts)
                            v
                  send_email + update_ats   (RetryPolicy + saga)
                            v
                  on_failure -> compensate -> finalize
                            v
                           END
```

## Mocks vs real services

Keep one `services.py` with the same function names regardless of provider. Inside each function, branch on `HIREGRAPH_USE_MOCKS`. Example:

```python
def tavily_search(query: str) -> list[dict]:
    if get_settings().use_mocks:
        return _mock_search(query)
    return _real_tavily(query)
```

Wrap both behind a single `@tool` decorator on the public function. Your nodes never know which one ran.

## Tool tip

Pydantic catches most LLM tool-call mistakes for you. Define your tool args with types and the SDK will validate them. The LLM will see the schema and adjust.

```python
@tool
def github_profile(username: str) -> dict:
    """Look up a public GitHub profile by username."""
    ...
```

The LLM also sees the docstring. Make it short and concrete.

## Critic loop tip

The most common failure of the evaluator-optimizer is an evaluator that is too strict and never accepts. Two ways out:

1. **Bound the loop** with an attempt counter and route to `human_review` after the cap.
2. **Force the evaluator to be specific** by requiring an actionable feedback string. If the schema asks `feedback: str = Field(min_length=20)`, vague verdicts fail validation.

## Interrupt tip

Put `interrupt()` first in the node. Anything before it re-runs on resume. If you need to print a "now paused" log line, do it *after* the interrupt:

```python
def human_review(state):
    decision = interrupt({...})   # <-- always first
    print("[review] resumed")
    ...
```

## Saga tip

A clean saga uses three nodes: the action, the compensation, and a `finalize`. Always route to `finalize` from both the success and the compensation path, so every run reaches a terminal state. Otherwise your run snapshot stays "in progress" forever.

## Test tip

The hardest test to write is the end-to-end one. The trick: monkeypatch the LLM. Replace `ChatOpenAI` with a stub that returns canned responses keyed on the prompt. Then assert on the graph's behaviour, not the model's words.

```python
class StubLLM:
    def invoke(self, prompt): return type("Msg", (), {"content": "ok"})()
    def with_structured_output(self, schema): return _StubStructured(schema)
```

That gives you fast, deterministic, free tests.

## UI tip

Smallest UI that gets full marks:

- `index.html` with two `<textarea>`s (resume, JD) and a Run button.
- A `<pre>` that streams trace lines from `POST /run` via SSE.
- A modal that pops up when the graph pauses, with Approve / Reject / Edit buttons that call `POST /resume/<thread_id>`.
- An `<img src="/graph.png">` at the bottom.

You can vibecode the whole thing in 30 minutes with Claude or Cursor. Keep it ugly. Keep it working.

## When to stop optimizing

Once the rubric is satisfied, stop. The bonus points exist to reward extra effort but the assignment is *gradable* without any of them. Polish your code, write your README, prepare the demo. Submit.
