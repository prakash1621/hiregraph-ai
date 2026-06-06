from typing import TypedDict

class HireGraphState(TypedDict):
    resume_text: str
    jd_text: str
    seniority: str
    scorecard: dict
    recommendation: str
    email_draft: str
    audit_trail: list