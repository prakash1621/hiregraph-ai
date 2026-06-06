import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

from hiregraph.graph import graph

state = {
    "resume_text": "Python developer with 10 years experience",
    "jd_text": "Senior Data Engineer",
    "seniority": "",
    "scorecard": {},
    "recommendation": "",
    "email_draft": "",
    "audit_trail": []
}

result = graph.invoke(state)

print(result)