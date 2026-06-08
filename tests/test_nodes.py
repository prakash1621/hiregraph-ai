"""Test individual nodes with mocked LLM."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.hiregraph.types import HireGraphState
from src.hiregraph.nodes import (
    ingest_and_parse,
    classify_seniority,
    score_skills,
    reduce_scores,
    make_decision,
    draft_email,
)


@pytest.fixture
def sample_state():
    """Create a sample state for testing."""
    return {
        "resume_text": "Senior Backend Engineer with 8 years experience",
        "jd_text": "Senior Backend Engineer role, 5+ years required",
    }


def test_ingest_and_parse(sample_state):
    """Test ingest_and_parse node."""
    result = ingest_and_parse(sample_state)
    
    assert "resume_parsed" in result
    assert "jd_parsed" in result
    assert result["resume_parsed"]["raw"] == sample_state["resume_text"]
    assert result["jd_parsed"]["raw"] == sample_state["jd_text"]
    assert "audit_trail" in result
    assert len(result["audit_trail"]) == 1
    assert result["audit_trail"][0]["node"] == "ingest_and_parse"


def test_ingest_and_parse_audit_trail(sample_state):
    """Test that ingest_and_parse creates audit entries."""
    result = ingest_and_parse(sample_state)
    
    assert len(result["audit_trail"]) == 1
    entry = result["audit_trail"][0]
    assert entry["verdict"] == "success"
    assert "duration_ms" in entry
    assert entry["details"]["resume_length"] > 0


@patch("src.hiregraph.nodes.get_llm")
def test_classify_seniority_with_mock(mock_get_llm, sample_state):
    """Test classify_seniority with mocked LLM."""
    mock_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_get_llm.return_value = mock_llm
    
    # Mock the structured output
    mock_response = MagicMock()
    mock_response.level = "senior"
    mock_response.confidence = 0.95
    mock_structured_llm.invoke.return_value = mock_response
    
    result = classify_seniority(sample_state)
    
    assert result["seniority_level"] == "senior"
    assert result["seniority_confidence"] == 0.95
    assert "audit_trail" in result
    assert len(result["audit_trail"]) == 1


@patch("src.hiregraph.nodes.get_llm")
def test_score_skills_with_mock(mock_get_llm, sample_state):
    """Test score_skills with mocked LLM."""
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    
    mock_response = MagicMock()
    mock_response.content = '{"score": 85, "matched_skills": ["Python", "PostgreSQL"], "missing_skills": [], "reasoning": "Good match"}'
    mock_llm.invoke.return_value = mock_response
    
    result = score_skills(sample_state)
    
    assert "skills_score" in result
    assert result["skills_score"]["score"] == 85
    assert "audit_trail" in result
    assert len(result["audit_trail"]) == 1


def test_reduce_scores():
    """Test reduce_scores node."""
    state = {
        "resume_text": "Test",
        "jd_text": "Test",
        "skills_score": {"score": 85},
        "experience_score": {"score": 90},
        "education_score": {"score": 75},
        "public_signals_score": {"score": 80},
    }
    
    result = reduce_scores(state)
    
    assert "scorecard" in result
    assert "overall_score" in result
    assert result["overall_score"] > 0
    assert result["scorecard"]["dimension_scores"]["skills"] == 85
    assert "audit_trail" in result


def test_make_decision_advance():
    """Test make_decision node for advance recommendation."""
    state = {"overall_score": 80.0}
    
    result = make_decision(state)
    
    assert result["recommendation"] == "advance"
    assert "decision_reasoning" in result
    assert "audit_trail" in result


def test_make_decision_reject():
    """Test make_decision node for reject recommendation."""
    state = {"overall_score": 40.0}
    
    result = make_decision(state)
    
    assert result["recommendation"] == "reject"
    assert "decision_reasoning" in result


def test_make_decision_borderline():
    """Test make_decision node for borderline recommendation."""
    state = {"overall_score": 65.0}
    
    result = make_decision(state)
    
    assert result["recommendation"] == "borderline"
    assert result["human_review_required"] is True


@patch("src.hiregraph.nodes.get_llm")
def test_draft_email_with_mock(mock_get_llm):
    """Test draft_email with mocked LLM."""
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    
    mock_response = MagicMock()
    mock_response.content = "Dear Candidate,\n\nThank you for your application..."
    mock_llm.invoke.return_value = mock_response
    
    state = {
        "resume_text": "Test resume",
        "jd_text": "Test JD",
        "recommendation": "advance",
        "overall_score": 85.0,
    }
    
    result = draft_email(state)
    
    assert "email_draft" in result
    assert len(result["email_draft"]) > 0
    assert result["email_draft_attempts"] == 1
    assert "audit_trail" in result
