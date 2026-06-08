"""Type definitions for HireGraph."""

from typing import TypedDict, Literal, Optional, Any, Annotated
from dataclasses import dataclass, field
from datetime import datetime
import operator


def merge_dict(original: Optional[dict], new: Optional[dict]) -> Optional[dict]:
    """Reducer that merges dicts, taking the latest non-None value."""
    if new is not None:
        return new
    return original


def last_value(original, new):
    """Reducer that keeps the last non-None value."""
    if new is not None:
        return new
    return original


class HireGraphState(TypedDict, total=False):
    """Main state for the HireGraph workflow.
    
    Holds raw data (resume, JD) and structured outputs (classification, scorecard, email, audit trail).
    No prompts in state - prompts are built inside nodes.
    
    Keys written by parallel nodes use Annotated with reducers to handle concurrent updates.
    """
    # Raw inputs
    resume_text: str
    jd_text: str
    
    # Classification
    seniority_level: str
    seniority_confidence: float
    
    # Parsed data
    resume_parsed: dict[str, Any]
    jd_parsed: dict[str, Any]
    
    # Scoring dimensions (run in parallel, use reducers)
    skills_score: Annotated[Optional[dict[str, Any]], merge_dict]
    experience_score: Annotated[Optional[dict[str, Any]], merge_dict]
    education_score: Annotated[Optional[dict[str, Any]], merge_dict]
    public_signals_score: Annotated[Optional[dict[str, Any]], merge_dict]
    
    # Aggregated scorecard
    scorecard: Optional[dict[str, Any]]
    overall_score: Optional[float]
    
    # Decision
    recommendation: str
    decision_reasoning: str
    
    # Email draft
    email_draft: str
    email_draft_attempts: int
    email_draft_approved: bool
    email_feedback: Optional[dict[str, Any]]
    
    # Research enrichment
    research_data: Optional[dict[str, Any]]
    
    # Audit trail (uses list append reducer for parallel writes)
    audit_trail: Annotated[list[dict[str, Any]], operator.add]
    
    # Error handling
    last_error: Optional[str]
    error_recovery_attempts: int
    
    # Human review
    human_review_required: bool
    human_review_feedback: Optional[str]
    
    # Saga/compensation
    compensation_reason: Optional[str]
    ats_update_status: Optional[str]
    email_send_status: Optional[str]


@dataclass
class AuditEntry:
    """Single entry in the audit trail."""
    node_name: str
    timestamp: datetime
    verdict: str
    duration_ms: float
    details: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "node": self.node_name,
            "timestamp": self.timestamp.isoformat(),
            "verdict": self.verdict,
            "duration_ms": self.duration_ms,
            "details": self.details,
        }


@dataclass
class Decision:
    """Final decision object returned to the user."""
    recommendation: str
    scorecard: dict[str, Any]
    overall_score: float
    email_draft: str
    audit_trail: list[dict[str, Any]]
    seniority_level: str
    decision_reasoning: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation": self.recommendation,
            "scorecard": self.scorecard,
            "overall_score": self.overall_score,
            "email_draft": self.email_draft,
            "audit_trail": self.audit_trail,
            "seniority_level": self.seniority_level,
            "decision_reasoning": self.decision_reasoning,
        }
