"""Test HireGraphState and types."""

import pytest
from src.hiregraph.types import HireGraphState, AuditEntry, Decision
from datetime import datetime


def test_hiregraph_state_creation():
    """Test that HireGraphState can be created with required fields."""
    state: HireGraphState = {
        "resume_text": "Sample resume",
        "jd_text": "Sample JD",
        "audit_trail": [],
        "error_recovery_attempts": 0,
    }
    
    assert state["resume_text"] == "Sample resume"
    assert state["jd_text"] == "Sample JD"
    assert state["audit_trail"] == []
    assert state["error_recovery_attempts"] == 0


def test_audit_entry_creation():
    """Test AuditEntry creation and serialization."""
    entry = AuditEntry(
        node_name="test_node",
        timestamp=datetime.now(),
        verdict="success",
        duration_ms=100.5,
        details={"key": "value"},
    )
    
    assert entry.node_name == "test_node"
    assert entry.verdict == "success"
    assert entry.duration_ms == 100.5
    
    # Test serialization
    entry_dict = entry.to_dict()
    assert entry_dict["node"] == "test_node"
    assert entry_dict["verdict"] == "success"
    assert entry_dict["duration_ms"] == 100.5
    assert entry_dict["details"]["key"] == "value"


def test_decision_creation():
    """Test Decision object creation and serialization."""
    decision = Decision(
        recommendation="advance",
        scorecard={"skills": 85, "experience": 90},
        overall_score=87.5,
        email_draft="Test email",
        audit_trail=[],
        seniority_level="senior",
        decision_reasoning="Strong match",
    )
    
    assert decision.recommendation == "advance"
    assert decision.overall_score == 87.5
    assert decision.seniority_level == "senior"
    
    # Test serialization
    decision_dict = decision.to_dict()
    assert decision_dict["recommendation"] == "advance"
    assert decision_dict["overall_score"] == 87.5


def test_state_with_all_fields():
    """Test state with all optional fields."""
    state: HireGraphState = {
        "resume_text": "Resume",
        "jd_text": "JD",
        "seniority_level": "senior",
        "seniority_confidence": 0.95,
        "skills_score": {"score": 85},
        "experience_score": {"score": 90},
        "education_score": {"score": 75},
        "public_signals_score": {"score": 80},
        "overall_score": 85.0,
        "recommendation": "advance",
        "email_draft": "Email",
        "audit_trail": [],
        "error_recovery_attempts": 0,
    }
    
    assert state["seniority_level"] == "senior"
    assert state["overall_score"] == 85.0
    assert state["recommendation"] == "advance"
