"""Node functions for the HireGraph workflow."""

import json
import time
from datetime import datetime
from typing import Any, Literal

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field
import os

from .types import HireGraphState, AuditEntry


def get_llm():
    """Get the configured LLM."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "anthropic":
        return ChatAnthropic(model="claude-3-5-haiku-20241022")
    else:
        return ChatOpenAI(model="gpt-4o-mini")


def make_audit_entry(node_name: str, verdict: str, duration_ms: float, details: dict[str, Any] = None) -> dict[str, Any]:
    """Create an audit trail entry dict."""
    entry = AuditEntry(
        node_name=node_name,
        timestamp=datetime.now(),
        verdict=verdict,
        duration_ms=duration_ms,
        details=details or {},
    )
    return entry.to_dict()


# ============================================================================
# INGEST AND PARSING NODES
# ============================================================================

def ingest_and_parse(state: HireGraphState) -> dict[str, Any]:
    """Ingest resume and JD, perform basic parsing.
    
    Supports raw text (already in state) or file paths to PDF, DOCX, MD, TXT files.
    If resume_text or jd_text starts with a file path, it will be parsed automatically.
    
    Returns only the keys this node modifies.
    """
    start = time.time()
    
    from .parser import parse_file
    
    resume_text = state["resume_text"]
    jd_text = state["jd_text"]
    
    # If the text looks like a file path, parse it
    if _is_file_path(resume_text):
        resume_text = parse_file(resume_text.strip())
    
    if _is_file_path(jd_text):
        jd_text = parse_file(jd_text.strip())
    
    # Parse resume (simple markdown parsing)
    resume_parsed = {
        "raw": resume_text,
        "lines": resume_text.split("\n"),
        "length": len(resume_text),
    }
    
    # Parse JD (simple markdown parsing)
    jd_parsed = {
        "raw": jd_text,
        "lines": jd_text.split("\n"),
        "length": len(jd_text),
    }
    
    duration = (time.time() - start) * 1000
    audit = make_audit_entry("ingest_and_parse", "success", duration, {
        "resume_length": len(resume_text),
        "jd_length": len(jd_text),
    })
    
    return {
        "resume_text": resume_text,
        "jd_text": jd_text,
        "resume_parsed": resume_parsed,
        "jd_parsed": jd_parsed,
        "audit_trail": [audit],
    }


def _is_file_path(text: str) -> bool:
    """Check if text looks like a file path rather than document content."""
    text = text.strip()
    # If it's short and ends with a known extension, treat as file path
    if len(text) < 500 and any(text.lower().endswith(ext) for ext in [".pdf", ".docx", ".md", ".txt"]):
        return True
    # If it looks like an absolute or relative path
    if len(text) < 500 and (text.startswith("/") or text.startswith("\\") or ":\\" in text or ":/" in text):
        return True
    return False


# ============================================================================
# CLASSIFICATION NODE (with structured output)
# ============================================================================

class SeniorityClassification(BaseModel):
    """Structured output for seniority classification."""
    level: Literal["junior", "mid", "senior", "executive"]
    confidence: float = Field(description="Confidence score 0-1")
    reasoning: str = Field(description="Brief reasoning for classification")


def classify_seniority(state: HireGraphState) -> dict[str, Any]:
    """Classify candidate seniority level using LLM with structured output.
    
    Pattern: Structured output with with_structured_output and Pydantic.
    """
    start = time.time()
    
    llm = get_llm()
    
    # Use with_structured_output for structured classification
    structured_llm = llm.with_structured_output(SeniorityClassification)
    
    prompt = f"""Based on this resume, classify the candidate's seniority level.

Resume:
{state['resume_text']}

Job Description:
{state['jd_text']}

Classify as: junior (0-2 years), mid (2-5 years), senior (5-8 years), or executive (8+ years).
Consider both years of experience and depth of responsibility."""
    
    try:
        result = structured_llm.invoke(prompt)
        
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("classify_seniority", "success", duration, {
            "level": result.level,
            "confidence": result.confidence,
        })
        
        return {
            "seniority_level": result.level,
            "seniority_confidence": result.confidence,
            "audit_trail": [audit],
        }
    except Exception as e:
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("classify_seniority", "error", duration, {
            "error": str(e),
        })
        
        return {
            "seniority_level": "mid",
            "seniority_confidence": 0.5,
            "last_error": f"Classification error: {str(e)}",
            "error_recovery_attempts": state.get("error_recovery_attempts", 0) + 1,
            "audit_trail": [audit],
        }


# ============================================================================
# PARALLEL SCORING NODES
# Each returns only its specific score key + audit trail.
# The audit_trail uses operator.add reducer so parallel writes merge cleanly.
# ============================================================================

def score_skills(state: HireGraphState) -> dict[str, Any]:
    """Score candidate's technical skills match."""
    start = time.time()
    
    llm = get_llm()
    
    prompt = f"""Score the candidate's technical skills match for this role (0-100).

Resume:
{state['resume_text']}

Job Description:
{state['jd_text']}

Return JSON with:
- score: 0-100
- matched_skills: list of matched skills
- missing_skills: list of important missing skills
- reasoning: brief explanation"""
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        # Try to parse JSON from response
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                result = json.loads(json_str)
            else:
                result = {"score": 70, "matched_skills": [], "missing_skills": [], "reasoning": content}
        except json.JSONDecodeError:
            result = {"score": 70, "matched_skills": [], "missing_skills": [], "reasoning": content}
        
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("score_skills", "success", duration, {
            "score": result.get("score", 0),
        })
        
        return {
            "skills_score": result,
            "audit_trail": [audit],
        }
    except Exception as e:
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("score_skills", "error", duration, {"error": str(e)})
        
        return {
            "skills_score": {"score": 0, "error": str(e)},
            "audit_trail": [audit],
        }


def score_experience(state: HireGraphState) -> dict[str, Any]:
    """Score candidate's relevant experience."""
    start = time.time()
    
    llm = get_llm()
    
    prompt = f"""Score the candidate's relevant experience for this role (0-100).

Resume:
{state['resume_text']}

Job Description:
{state['jd_text']}

Return JSON with:
- score: 0-100
- years_relevant: estimated years of relevant experience
- key_experiences: list of relevant past roles/projects
- reasoning: brief explanation"""
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                result = json.loads(json_str)
            else:
                result = {"score": 70, "years_relevant": 0, "key_experiences": [], "reasoning": content}
        except json.JSONDecodeError:
            result = {"score": 70, "years_relevant": 0, "key_experiences": [], "reasoning": content}
        
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("score_experience", "success", duration, {
            "score": result.get("score", 0),
        })
        
        return {
            "experience_score": result,
            "audit_trail": [audit],
        }
    except Exception as e:
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("score_experience", "error", duration, {"error": str(e)})
        
        return {
            "experience_score": {"score": 0, "error": str(e)},
            "audit_trail": [audit],
        }


def score_education(state: HireGraphState) -> dict[str, Any]:
    """Score candidate's educational background."""
    start = time.time()
    
    llm = get_llm()
    
    prompt = f"""Score the candidate's educational background for this role (0-100).

Resume:
{state['resume_text']}

Job Description:
{state['jd_text']}

Return JSON with:
- score: 0-100
- degree: highest degree mentioned
- institution: school/university
- relevant_coursework: any relevant coursework mentioned
- reasoning: brief explanation"""
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                result = json.loads(json_str)
            else:
                result = {"score": 60, "degree": "Unknown", "institution": "Unknown", "relevant_coursework": [], "reasoning": content}
        except json.JSONDecodeError:
            result = {"score": 60, "degree": "Unknown", "institution": "Unknown", "relevant_coursework": [], "reasoning": content}
        
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("score_education", "success", duration, {
            "score": result.get("score", 0),
        })
        
        return {
            "education_score": result,
            "audit_trail": [audit],
        }
    except Exception as e:
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("score_education", "error", duration, {"error": str(e)})
        
        return {
            "education_score": {"score": 0, "error": str(e)},
            "audit_trail": [audit],
        }


def score_public_signals(state: HireGraphState) -> dict[str, Any]:
    """Score candidate's public signals (GitHub, writing, speaking, etc.)."""
    start = time.time()
    
    llm = get_llm()
    
    prompt = f"""Score the candidate's public signals (GitHub, writing, speaking, open source) (0-100).

Resume:
{state['resume_text']}

Job Description:
{state['jd_text']}

Return JSON with:
- score: 0-100
- github_activity: assessment of GitHub presence if mentioned
- writing_speaking: assessment of public writing/speaking if mentioned
- open_source: assessment of open source contributions if mentioned
- reasoning: brief explanation"""
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                result = json.loads(json_str)
            else:
                result = {"score": 50, "github_activity": "Not mentioned", "writing_speaking": "Not mentioned", "open_source": "Not mentioned", "reasoning": content}
        except json.JSONDecodeError:
            result = {"score": 50, "github_activity": "Not mentioned", "writing_speaking": "Not mentioned", "open_source": "Not mentioned", "reasoning": content}
        
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("score_public_signals", "success", duration, {
            "score": result.get("score", 0),
        })
        
        return {
            "public_signals_score": result,
            "audit_trail": [audit],
        }
    except Exception as e:
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("score_public_signals", "error", duration, {"error": str(e)})
        
        return {
            "public_signals_score": {"score": 0, "error": str(e)},
            "audit_trail": [audit],
        }


# ============================================================================
# REDUCER FOR PARALLEL SCORES
# ============================================================================

def reduce_scores(state: HireGraphState) -> dict[str, Any]:
    """Aggregate parallel scores into a single scorecard."""
    start = time.time()
    
    scores = {
        "skills": state.get("skills_score", {}).get("score", 0) if state.get("skills_score") else 0,
        "experience": state.get("experience_score", {}).get("score", 0) if state.get("experience_score") else 0,
        "education": state.get("education_score", {}).get("score", 0) if state.get("education_score") else 0,
        "public_signals": state.get("public_signals_score", {}).get("score", 0) if state.get("public_signals_score") else 0,
    }
    
    # Calculate weighted average
    weights = {
        "skills": 0.35,
        "experience": 0.35,
        "education": 0.15,
        "public_signals": 0.15,
    }
    
    overall = sum(scores[k] * weights[k] for k in scores)
    
    scorecard = {
        "dimension_scores": scores,
        "weights": weights,
        "details": {
            "skills": state.get("skills_score", {}),
            "experience": state.get("experience_score", {}),
            "education": state.get("education_score", {}),
            "public_signals": state.get("public_signals_score", {}),
        }
    }
    
    duration = (time.time() - start) * 1000
    audit = make_audit_entry("reduce_scores", "success", duration, {
        "overall_score": overall,
        "dimension_scores": scores,
    })
    
    return {
        "scorecard": scorecard,
        "overall_score": overall,
        "audit_trail": [audit],
    }


# ============================================================================
# DECISION NODE
# ============================================================================

def make_decision(state: HireGraphState) -> dict[str, Any]:
    """Make advance/reject/borderline decision based on scores."""
    start = time.time()
    
    overall_score = state.get("overall_score", 0)
    
    # Decision thresholds
    if overall_score >= 75:
        recommendation = "advance"
        reasoning = f"Strong match with overall score {overall_score:.1f}"
    elif overall_score >= 55:
        recommendation = "borderline"
        reasoning = f"Moderate match with overall score {overall_score:.1f}. Requires human review."
    else:
        recommendation = "reject"
        reasoning = f"Weak match with overall score {overall_score:.1f}"
    
    duration = (time.time() - start) * 1000
    audit = make_audit_entry("make_decision", "success", duration, {
        "recommendation": recommendation,
        "overall_score": overall_score,
    })
    
    return {
        "recommendation": recommendation,
        "decision_reasoning": reasoning,
        "human_review_required": (recommendation == "borderline"),
        "audit_trail": [audit],
    }


# ============================================================================
# EMAIL DRAFT NODE
# ============================================================================

def draft_email(state: HireGraphState) -> dict[str, Any]:
    """Draft a personalized email to the candidate."""
    start = time.time()
    
    llm = get_llm()
    
    recommendation = state.get("recommendation", "reject")
    overall_score = state.get("overall_score", 0)
    
    if recommendation == "advance":
        tone = "enthusiastic and inviting"
        next_step = "We'd like to move forward with your application and schedule a technical interview."
    elif recommendation == "borderline":
        tone = "warm and encouraging"
        next_step = "We're interested in learning more about your background and would like to schedule a brief conversation."
    else:
        tone = "professional and respectful"
        next_step = "We appreciate your interest, but we've decided to move forward with other candidates at this time."
    
    prompt = f"""Draft a personalized email to a candidate based on their resume and our decision.

Resume:
{state['resume_text']}

Job Description:
{state['jd_text']}

Decision: {recommendation}
Overall Score: {overall_score:.1f}/100
Tone: {tone}
Next Step: {next_step}

Write a professional, personalized email (2-3 paragraphs) that:
1. References specific achievements from their resume
2. Explains our decision in a constructive way
3. Includes the next step
4. Ends with a professional closing

Return only the email body, no subject line."""
    
    try:
        response = llm.invoke(prompt)
        email_draft = response.content
        
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("draft_email", "success", duration, {
            "recommendation": recommendation,
            "draft_length": len(email_draft),
        })
        
        return {
            "email_draft": email_draft,
            "email_draft_attempts": 1,
            "audit_trail": [audit],
        }
    except Exception as e:
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("draft_email", "error", duration, {"error": str(e)})
        
        return {
            "email_draft": f"Error drafting email: {str(e)}",
            "last_error": str(e),
            "audit_trail": [audit],
        }


# ============================================================================
# EVALUATOR/CRITIC NODE (for email quality)
# ============================================================================

def evaluate_email(state: HireGraphState) -> dict[str, Any]:
    """Evaluate email draft quality and suggest improvements."""
    start = time.time()
    
    llm = get_llm()
    
    prompt = f"""Evaluate this email draft for quality, tone, and professionalism.

Email Draft:
{state.get('email_draft', '')}

Candidate Resume:
{state['resume_text']}

Provide feedback in JSON format:
- quality_score: 0-100
- tone_appropriate: true/false
- specific_enough: true/false
- issues: list of any issues found
- suggestions: list of improvement suggestions
- ready_to_send: true/false"""
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                feedback = json.loads(json_str)
            else:
                feedback = {"quality_score": 75, "ready_to_send": True}
        except json.JSONDecodeError:
            feedback = {"quality_score": 75, "ready_to_send": True}
        
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("evaluate_email", "success", duration, {
            "quality_score": feedback.get("quality_score", 0),
            "ready_to_send": feedback.get("ready_to_send", False),
        })
        
        return {
            "email_feedback": feedback,
            "audit_trail": [audit],
        }
    except Exception as e:
        duration = (time.time() - start) * 1000
        audit = make_audit_entry("evaluate_email", "error", duration, {"error": str(e)})
        
        return {
            "email_feedback": {"quality_score": 0, "error": str(e)},
            "audit_trail": [audit],
        }


# ============================================================================
# TERMINAL NODES
# ============================================================================

def end_advance(state: HireGraphState) -> dict[str, Any]:
    """Terminal node for advance decision."""
    start = time.time()
    duration = (time.time() - start) * 1000
    audit = make_audit_entry("end_advance", "success", duration, {
        "recommendation": "advance",
    })
    return {
        "email_draft_approved": True,
        "audit_trail": [audit],
    }


def end_reject(state: HireGraphState) -> dict[str, Any]:
    """Terminal node for reject decision."""
    start = time.time()
    duration = (time.time() - start) * 1000
    audit = make_audit_entry("end_reject", "success", duration, {
        "recommendation": "reject",
    })
    return {
        "email_draft_approved": True,
        "audit_trail": [audit],
    }


def end_borderline_approved(state: HireGraphState) -> dict[str, Any]:
    """Terminal node for borderline decision after human approval."""
    start = time.time()
    duration = (time.time() - start) * 1000
    audit = make_audit_entry("end_borderline_approved", "success", duration, {
        "recommendation": "borderline",
        "human_approved": True,
    })
    return {
        "email_draft_approved": True,
        "audit_trail": [audit],
    }


def end_error(state: HireGraphState) -> dict[str, Any]:
    """Terminal node for error/compensation path."""
    start = time.time()
    duration = (time.time() - start) * 1000
    audit = make_audit_entry("end_error", "success", duration, {
        "compensation_reason": state.get("compensation_reason", "Unknown error"),
    })
    return {
        "audit_trail": [audit],
    }
