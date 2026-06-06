import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

from hiregraph.graph import graph

state = {
    "resume_text": "sample resume",
    "jd_text": "sample jd",
    "seniority": "",
    "scorecard": {},
    "recommendation": "",
    "email_draft": "",
    "audit_trail": []
}

result = graph.invoke(state)

print(result)