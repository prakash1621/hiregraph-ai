"""Generate the HireGraph reference architecture as draw.io XML.

Run:
    python3 build_architecture.py
    drawio -x -f png -s 2 -b 24 -o hiregraph_architecture.png hiregraph_architecture.drawio
"""

from __future__ import annotations
import textwrap
from pathlib import Path

HERE = Path(__file__).parent

STYLES = {
    "start":    "ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#2f5b22;fontSize=14;fontStyle=1",
    "end":      "ellipse;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#6b1d1d;fontSize=14;fontStyle=1",
    "data":     "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#3f2b6c;fontSize=13;fontStyle=1",
    "llm":      "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#9a7d0a;fontSize=13;fontStyle=1",
    "action":   "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#a0522d;fontSize=13;fontStyle=1",
    "human":    "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5d0d0;strokeColor=#8b0000;fontSize=13;fontStyle=1",
    "decision": "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#9a7d0a;fontSize=12;fontStyle=1",
    "agent":    "rounded=1;whiteSpace=wrap;html=1;fillColor=#cce5ff;strokeColor=#1a5fb4;fontSize=13;fontStyle=1",
    "title":    "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#444444;fontSize=20;fontStyle=1;align=center;verticalAlign=middle",
    "subtitle": "rounded=1;whiteSpace=wrap;html=1;fillColor=#fafafa;strokeColor=#bbbbbb;fontSize=12;fontStyle=2;align=center;verticalAlign=middle",
    "note":     "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff8e1;strokeColor=#cba002;fontSize=12;dashed=1;fontStyle=2;align=left;verticalAlign=middle",
    "swimlane": "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#999999;dashed=1;fontSize=12;verticalAlign=top;align=center;fontStyle=2",
}

EDGE_DEFAULT = "endArrow=block;html=1;rounded=0;strokeColor=#444444;fontSize=12"
EDGE_DASHED  = "endArrow=block;html=1;rounded=0;strokeColor=#888888;dashed=1;fontSize=12"
EDGE_THICK   = "endArrow=block;html=1;rounded=0;strokeColor=#27496d;strokeWidth=3;fontSize=12;fontStyle=1"
EDGE_LOOP    = "endArrow=block;html=1;rounded=0;strokeColor=#a0522d;dashed=1;fontSize=12;fontStyle=1"


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("\n", "&#xa;")
    )


cells: list[str] = []
next_id = 2


def cid() -> str:
    global next_id
    n = f"n{next_id}"
    next_id += 1
    return n


def node(label: str, x: int, y: int, w: int, h: int, style_key: str) -> str:
    nid = cid()
    cells.append(
        f'<mxCell id="{nid}" value="{_escape(label)}" style="{STYLES[style_key]}" vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )
    return nid


def edge(src: str, dst: str, label: str = "", style: str = EDGE_DEFAULT) -> str:
    eid = cid()
    cells.append(
        f'<mxCell id="{eid}" value="{_escape(label)}" style="{style}" '
        f'edge="1" parent="1" source="{src}" target="{dst}">'
        f'<mxGeometry relative="1" as="geometry"/></mxCell>'
    )
    return eid


# Title
node("HireGraph reference architecture", 60, 30, 2080, 60, "title")
node(
    "One reference design. You may use this, evolve it, or design your own. "
    "Whatever you build must still cover every required pattern from the rubric.",
    60, 100, 2080, 40, "subtitle",
)

# --- Ingest band ---
START = node("START", 1040, 180, 120, 60, "start")
ingest = node("ingest_resume_and_jd\n(data)", 980, 280, 240, 70, "data")
classify = node("classify_seniority\n(LLM, with_structured_output)", 940, 380, 320, 80, "llm")
plan = node("plan_required_skills\n(LLM, with_structured_output)", 940, 490, 320, 80, "llm")

edge(START, ingest, style=EDGE_THICK)
edge(ingest, classify, style=EDGE_THICK)
edge(classify, plan, style=EDGE_THICK)

# --- Orchestrator and Workers band ---
node("Orchestrator and worker  (workbook 10)", 100, 600, 800, 30, "swimlane")
assign = node("assign_skill_workers\n(Send fan out)", 320, 640, 280, 70, "llm")
edge(plan, assign, "one Send per skill", style=EDGE_THICK)

w1 = node("skill_worker\nskill #1", 80, 770, 180, 70, "llm")
w2 = node("skill_worker\nskill #2", 290, 770, 180, 70, "llm")
w3 = node("skill_worker\nskill #3", 500, 770, 180, 70, "llm")
wN = node("skill_worker\n...", 710, 770, 160, 70, "llm")

for w in (w1, w2, w3, wN):
    edge(assign, w)

# --- Parallel scorers band ---
node("Parallelization with reducer  (workbook 08)", 1000, 600, 1140, 30, "swimlane")
exp_score = node("experience_scorer\n(LLM)", 1040, 640, 220, 70, "llm")
edu_score = node("education_scorer\n(LLM)", 1300, 640, 220, 70, "llm")
sig_score = node("signal_scorer\n(LLM)", 1560, 640, 220, 70, "llm")
research = node("research_agent\n(agent + tools)", 1820, 640, 240, 70, "agent")

for s in (exp_score, edu_score, sig_score, research):
    edge(plan, s, style=EDGE_DASHED)

# Tools box for research agent
tools = node(
    "Tools\n- tavily_search\n- github_profile\n- (others you add)",
    1860, 740, 220, 100, "action",
)
edge(research, tools, "calls", style=EDGE_DASHED)
edge(tools, research, "results", style=EDGE_DASHED)

# --- Aggregate ---
aggregate = node(
    "aggregate_scores\n(combine skill scores, experience, education, signals)",
    700, 890, 780, 90, "data",
)
for w in (w1, w2, w3, wN):
    edge(w, aggregate)
for s in (exp_score, edu_score, sig_score, research):
    edge(s, aggregate)

note_reducer = node(
    "Reducer on completed_scores\nAnnotated[list, operator.add]",
    140, 905, 520, 60, "note",
)

# --- Decision ---
decide = node("recommendation?", 1000, 1010, 200, 90, "decision")
edge(aggregate, decide, style=EDGE_THICK)

# --- Three branches ---
advance = node("draft_email\n(LLM)", 660, 1140, 240, 80, "llm")
review = node("human_review\n(interrupt)", 1000, 1140, 240, 80, "human")
reject = node("draft_rejection\n(LLM)", 1340, 1140, 240, 80, "llm")

edge(decide, advance, "advance")
edge(decide, review, "borderline", style=EDGE_THICK)
edge(decide, reject, "reject")

# Human review goes back to draft on approval
edge(review, advance, "approved", style=EDGE_THICK)
edge(review, reject, "rejected by reviewer")

# --- Critic loop (evaluator-optimizer) ---
critic = node(
    "critic_loop\n(evaluator + optimizer, max 3 attempts)",
    660, 1260, 240, 80, "llm",
)
edge(advance, critic, style=EDGE_THICK)
edge(critic, advance, "not yet good enough", style=EDGE_LOOP)

# --- Send + saga ---
node("Saga / compensation  (workbook 04)", 60, 1370, 2080, 30, "swimlane")
send_email = node(
    "send_email + update_ats\n(RetryPolicy, retry_on=ConnectionError)",
    560, 1410, 400, 90, "action",
)
edge(critic, send_email, "accepted", style=EDGE_THICK)

# Reject and review-reject still go through finalize via a quick log node
log_reject = node("log_rejection\n(action)", 1340, 1260, 240, 70, "action")
edge(reject, log_reject)

compensate = node(
    "compensate\n(rollback, alert engineer)",
    1040, 1410, 280, 90, "action",
)
edge(send_email, compensate, "retries exhausted", style=EDGE_LOOP)

finalize = node("finalize\n(write audit trail)", 760, 1540, 300, 80, "data")
edge(send_email, finalize, "sent")
edge(compensate, finalize, "compensated")
edge(log_reject, finalize, "logged")

END = node("END", 880, 1670, 120, 60, "end")
edge(finalize, END, style=EDGE_THICK)

# --- Legend ---
legend_x, legend_y = 60, 1660
node("Legend", legend_x, legend_y - 30, 200, 30, "subtitle")
node("data step", legend_x, legend_y, 200, 30, "data")
node("LLM step", legend_x, legend_y + 40, 200, 30, "llm")
node("action / saga step", legend_x, legend_y + 80, 200, 30, "action")
node("human input (interrupt)", legend_x, legend_y + 120, 200, 30, "human")
node("agent with tools", legend_x, legend_y + 160, 200, 30, "agent")

# --- Render the file ---
body = "\n".join(cells)
xml = textwrap.dedent(f"""\
    <mxfile host="app.diagrams.net" agent="hiregraph-architecture">
      <diagram name="hiregraph-architecture" id="d1">
        <mxGraphModel dx="2200" dy="1800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2200" pageHeight="1800" math="0" shadow="0">
          <root>
            <mxCell id="0"/>
            <mxCell id="1" parent="0"/>
{body}
          </root>
        </mxGraphModel>
      </diagram>
    </mxfile>
""")

out = HERE / "hiregraph_architecture.drawio"
out.write_text(xml)
print(f"wrote {out}")
