#!/usr/bin/env python3
"""Run HireGraph on a single resume + JD pair.

Usage:
    python run_single.py <resume_path> <jd_path>

Examples:
    python run_single.py sample_data/resumes/resume_priya.md sample_data/jds/jd_senior_backend.md
    python run_single.py C:/path/to/resume.pdf sample_data/jds/jd_senior_backend.md
    python run_single.py my_resume.docx my_job.txt
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

from src.hiregraph.graph import get_graph
from src.hiregraph.parser import parse_file
from src.hiregraph.types import Decision


def main():
    load_dotenv()
    
    if len(sys.argv) < 3:
        print("Usage: python run_single.py <resume_path> <jd_path>")
        print()
        print("Examples:")
        print("  python run_single.py sample_data/resumes/resume_priya.md sample_data/jds/jd_senior_backend.md")
        print("  python run_single.py my_resume.pdf sample_data/jds/jd_senior_backend.md")
        print("  python run_single.py resume.docx job_description.docx")
        sys.exit(1)
    
    resume_path = sys.argv[1]
    jd_path = sys.argv[2]
    
    # Validate files exist
    if not Path(resume_path).exists():
        print(f"Error: Resume file not found: {resume_path}")
        sys.exit(1)
    if not Path(jd_path).exists():
        print(f"Error: JD file not found: {jd_path}")
        sys.exit(1)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")
        sys.exit(1)
    
    # Parse files
    print(f"Resume: {resume_path}")
    print(f"JD:     {jd_path}")
    print()
    
    resume_text = parse_file(resume_path)
    jd_text = parse_file(jd_path)
    
    print(f"Resume parsed: {len(resume_text)} characters")
    print(f"JD parsed:     {len(jd_text)} characters")
    print()
    
    # Build graph and run
    print("Running HireGraph...")
    print("=" * 60)
    
    graph = get_graph()
    
    initial_state = {
        "resume_text": resume_text,
        "jd_text": jd_text,
    }
    
    config = {"configurable": {"thread_id": "single_run"}}
    final_state = graph.invoke(initial_state, config=config)
    
    # Display results
    decision = Decision(
        recommendation=final_state.get("recommendation", "reject"),
        scorecard=final_state.get("scorecard", {}),
        overall_score=final_state.get("overall_score", 0),
        email_draft=final_state.get("email_draft", ""),
        audit_trail=final_state.get("audit_trail", []),
        seniority_level=final_state.get("seniority_level", "unknown"),
        decision_reasoning=final_state.get("decision_reasoning", ""),
    )
    
    print()
    print(f"RECOMMENDATION:  {decision.recommendation.upper()}")
    print(f"SENIORITY LEVEL: {decision.seniority_level}")
    print(f"OVERALL SCORE:   {decision.overall_score:.1f}/100")
    print()
    
    print("SCORECARD:")
    if decision.scorecard.get("dimension_scores"):
        for dim, score in decision.scorecard["dimension_scores"].items():
            bar = "#" * int(score / 5) + "." * (20 - int(score / 5))
            print(f"  {dim:20s} [{bar}] {score:.0f}")
    print()
    
    print(f"REASONING: {decision.decision_reasoning}")
    print()
    
    print("EMAIL DRAFT:")
    print("-" * 60)
    print(decision.email_draft)
    print("-" * 60)
    print()
    
    print(f"AUDIT TRAIL ({len(decision.audit_trail)} steps):")
    for entry in decision.audit_trail:
        print(f"  {entry['node']:30s} {entry['verdict']:8s} ({entry['duration_ms']:.0f}ms)")


if __name__ == "__main__":
    main()
