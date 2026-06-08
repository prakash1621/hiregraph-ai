# Resources: free APIs, mocks, and pointers

You do **not** have to spend money to finish this assignment. Below is a curated list of free or sandbox-friendly services and how to wire them. For each one we also include the recommended *mock* fallback so your project still runs without keys.

---

## 1. LLM provider (one is required)

| Provider | Model | Cost | Notes |
|---|---|---|---|
| OpenAI | `gpt-4o-mini` | ~$0.15 per 1M input tokens | Cheapest reliable choice. A full assignment demo costs under a dollar |
| Anthropic | `claude-3-5-haiku` | ~$0.25 per 1M input tokens | Very strong instruction following |
| OpenRouter | any | varies | If you want to A/B models without multiple accounts |

Wire-up:

```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

Mock fallback: a tiny class that returns deterministic strings keyed on substrings in the prompt. Ask the instructor for the reference implementation if you want one to study.

---

## 2. Web search: Tavily

Used by the research agent to look up the candidate's public work or the hiring company.

- Free tier: 1000 searches/month, no credit card.
- Sign up: https://tavily.com
- Python SDK: `pip install tavily-python`
- Env var: `TAVILY_API_KEY`

```python
from tavily import TavilyClient
client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
results = client.search("Senior Backend Engineer at Stripe site:github.com", max_results=5)
```

Mock fallback: a dictionary that maps a known query to a deterministic list of fake results. Wrap the real and the mock behind the same `@tool` interface so the rest of your code does not care which one it is talking to.

---

## 3. GitHub profile lookup

Free and works without auth for low volumes (60 requests/hour). With a personal access token you get 5000 requests/hour.

```python
import os, requests
def github_profile(username: str) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    r = requests.get(f"https://api.github.com/users/{username}", headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()
```

Mock fallback: hard-code a dict of `{username: profile}` for the candidates in `sample_data/`.

Tip: cache responses to disk during development. The 60/hour limit bites if you re-run a graph 50 times.

---

## 4. Email sandbox: Mailtrap (or Ethereal)

Pretend to send emails to a fake inbox. Useful for end-to-end demos because you can show the actual generated email in the sandbox UI.

- **Mailtrap**: https://mailtrap.io, free tier, easy SMTP creds.
- **Ethereal**: https://ethereal.email, disposable inboxes, no signup.

```python
import smtplib
from email.message import EmailMessage

def send_email(to: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = "noreply@hiregraph.local"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(os.environ["MAILTRAP_HOST"], int(os.environ["MAILTRAP_PORT"])) as s:
        s.starttls()
        s.login(os.environ["MAILTRAP_USER"], os.environ["MAILTRAP_PASS"])
        s.send_message(msg)
```

Mock fallback: write the email to `outbox/{candidate_id}.eml` so you can inspect it after a run.

---

## 5. Resume parsing

You may receive resumes as PDF or as plain text. Two paths.

**Path A (easy):** require resumes as markdown or plain text. We ship them this way in `sample_data/`.

**Path B (real):** parse PDFs with `pymupdf` (a.k.a. `fitz`).

```python
import fitz
def pdf_to_text(path: str) -> str:
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)
```

Add `pymupdf` to `pyproject.toml` if you go this way.

---

## 6. Observability: LangSmith

Highly recommended. Shows you every node call, every tool call, every LLM token. Free tier is generous.

```bash
# in .env
LANGSMITH_API_KEY=ls__...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=hiregraph-assignment-2
```

That's it. Every `app.invoke(...)` then appears as a trace at https://smith.langchain.com. Share a trace link in your README; it earns a bonus point.

---

## 7. Checkpointer

For the assignment, `InMemorySaver()` is enough.

```python
from langgraph.checkpoint.memory import InMemorySaver
app = builder.compile(checkpointer=InMemorySaver())
```

Bonus: swap in `PostgresSaver` (`langgraph-checkpoint-postgres`) so the interrupt survives a process restart. Worth +3 bonus points and looks great on your CV.

---

## 8. UI

You may vibecode the UI. Suggested stacks:

- **HTMX + FastAPI** (single Python repo, no JS toolchain). Recommended.
- **Next.js + shadcn/ui** (modern, but you maintain a Node toolchain).
- **Gradio** (lazy mode; ugly but functional).
- **Streamlit** (lazy mode 2; gets the job done).

Whatever you pick, it must let a reviewer:

1. Trigger a run with a resume + JD.
2. See the streaming trace as the graph progresses.
3. Approve / edit / reject when the graph pauses at human review.
4. See the final scorecard and email.

Sample prompts you can give your AI tool of choice to scaffold the UI:

> "Build me a single-page FastAPI app with HTMX. POST /run accepts a resume markdown and a JD markdown, returns a streaming SSE feed of node updates from my LangGraph app. POST /approve/<thread_id> resumes from an interrupt with a JSON body."

You get full marks if the UI works. Polish is not graded.

---

## 9. Reference implementations you can study

You already have these in the course materials. Do not copy from them, but read them.

* The class 2 email agent project: a multi-file LangGraph project with a real checkpointer, a CLI entry point, a FastAPI addon, and three test scenarios.
* Workbook 05 (full email agent): the pattern walkthrough.
* The project specification document in the course folder: what a production-grade version would look like.

---

## 10. Where to ask for help

- Re-read workbook 01. Always re-read workbook 01.
- Course channel for design questions. Share screenshots, not pages of code.
- Office hours for blockers.
- Stack Overflow tag `langgraph` if you really cannot find an answer.

Good luck.
