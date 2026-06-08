#!/usr/bin/env python3
"""CLI entry point for HireGraph."""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

from src.hiregraph.graph import get_graph
from src.hiregraph.types import Decision, HireGraphState


def load_sample_data():
    """Load sample resumes and JD."""
    sample_dir = Path("sample_data")
    
    # Load resumes
    priya_resume = (sample_dir / "resumes" / "resume_priya.md").read_text()
    eitan_resume = (sample_dir / "resumes" / "resume_eitan.md").read_text()
    mira_resume = (sample_dir / "resumes" / "resume_mira.md").read_text()
    
    # Load JD
    jd = (sample_dir / "jds" / "jd_senior_backend.md").read_text()
    
    return {
        "priya": priya_resume,
        "eitan": eitan_resume,
        "mira": mira_resume,
        "jd": jd,
    }


def run_scenario(graph, resume_text: str, jd_text: str, candidate_name: str, thread_id: str = None):
    """Run a single scenario through the graph."""
    print(f"\n{'='*80}")
    print(f"Processing: {candidate_name}")
    print(f"{'='*80}")
    
    # Initial state
    initial_state: HireGraphState = {
        "resume_text": resume_text,
        "jd_text": jd_text,
    }
    
    # Run the graph
    config = {"configurable": {"thread_id": thread_id or f"thread_{candidate_name}"}}
    
    try:
        final_state = graph.invoke(initial_state, config=config)
        
        # Create Decision object
        decision = Decision(
            recommendation=final_state.get("recommendation", "reject"),
            scorecard=final_state.get("scorecard", {}),
            overall_score=final_state.get("overall_score", 0),
            email_draft=final_state.get("email_draft", ""),
            audit_trail=final_state.get("audit_trail", []),
            seniority_level=final_state.get("seniority_level", "unknown"),
            decision_reasoning=final_state.get("decision_reasoning", ""),
        )
        
        # Print results
        print(f"\nRecommendation: {decision.recommendation.upper()}")
        print(f"Seniority Level: {decision.seniority_level}")
        print(f"Overall Score: {decision.overall_score:.1f}/100")
        print(f"\nScorecard:")
        if decision.scorecard.get("dimension_scores"):
            for dim, score in decision.scorecard["dimension_scores"].items():
                print(f"  {dim}: {score:.1f}")
        
        print(f"\nDecision Reasoning: {decision.decision_reasoning}")
        
        print(f"\nEmail Draft:")
        print("-" * 40)
        print(decision.email_draft)
        print("-" * 40)
        
        print(f"\nAudit Trail ({len(decision.audit_trail)} entries):")
        for entry in decision.audit_trail:
            print(f"  {entry['node']}: {entry['verdict']} ({entry['duration_ms']:.1f}ms)")
        
        return decision
        
    except Exception as e:
        print(f"Error processing {candidate_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main entry point."""
    # Load environment
    load_dotenv()
    
    # Check for LLM API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
        sys.exit(1)
    
    print("HireGraph - Smart Hiring Assistant")
    print("=" * 80)
    
    # Build and compile graph
    print("\nBuilding graph...")
    graph = get_graph()
    print("Graph compiled successfully!")
    
    # Write graph visualization
    print("\nGenerating graph visualization...")
    try:
        graph_png = graph.get_graph().draw_mermaid_png()
        output_dir = Path("graph_out")
        output_dir.mkdir(exist_ok=True)
        (output_dir / "graph.png").write_bytes(graph_png)
        print(f"Graph saved to graph_out/graph.png")
    except Exception as e:
        print(f"Warning: Could not generate graph PNG: {e}")
    
    # Load sample data
    print("\nLoading sample data...")
    data = load_sample_data()
    
    # Run three scenarios
    results = []
    
    print("\n" + "=" * 80)
    print("RUNNING SCENARIOS")
    print("=" * 80)
    
    # Scenario 1: Strong candidate (Priya)
    decision1 = run_scenario(graph, data["priya"], data["jd"], "Priya (Strong Senior)")
    if decision1:
        results.append(("Priya (Strong Senior)", decision1))
    
    # Scenario 2: Weak candidate (Mira)
    decision2 = run_scenario(graph, data["mira"], data["jd"], "Mira (Weak/Mismatch)")
    if decision2:
        results.append(("Mira (Weak/Mismatch)", decision2))
    
    # Scenario 3: Borderline candidate (Eitan)
    decision3 = run_scenario(graph, data["eitan"], data["jd"], "Eitan (Borderline Mid-Level)")
    if decision3:
        results.append(("Eitan (Borderline Mid-Level)", decision3))
    
    # Print scoreboard
    print("\n" + "=" * 80)
    print("SCOREBOARD SUMMARY")
    print("=" * 80)
    
    for name, decision in results:
        print(f"\n{name}:")
        print(f"  Recommendation: {decision.recommendation}")
        print(f"  Overall Score: {decision.overall_score:.1f}/100")
        print(f"  Seniority: {decision.seniority_level}")
    
    print("\n" + "=" * 80)
    print("Demo complete!")


if __name__ == "__main__":
    main()
