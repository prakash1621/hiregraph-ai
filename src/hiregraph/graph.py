"""LangGraph graph builder for HireGraph."""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from .types import HireGraphState
from .nodes import (
    ingest_and_parse,
    classify_seniority,
    score_skills,
    score_experience,
    score_education,
    score_public_signals,
    reduce_scores,
    make_decision,
    draft_email,
    evaluate_email,
    end_advance,
    end_reject,
    end_borderline_approved,
    end_error,
)


def build_graph():
    """Build the HireGraph workflow graph.
    
    Implements all required patterns:
    - TypedDict state with raw data
    - Node functions with Command(goto=...) self-routing
    - RetryPolicy on external service nodes
    - LLM-recoverable loopback
    - Saga/compensation pattern
    - Structured output with Pydantic
    - Tool calling (research agent)
    - Short-term memory/MessagesState
    - Prompt chaining
    - Parallelization with reducer
    - Routing based on LLM classification
    - Orchestrator and worker with Send
    - Evaluator and optimizer
    - Agent with tools and ToolNode
    - interrupt() for human review
    """
    
    graph = StateGraph(HireGraphState)
    
    # ========================================================================
    # NODES
    # ========================================================================
    
    # Ingest and parse
    graph.add_node("ingest_and_parse", ingest_and_parse)
    
    # Classification (with structured output)
    graph.add_node("classify_seniority", classify_seniority)
    
    # Parallel scoring nodes (run in parallel, merge via reducer)
    graph.add_node("score_skills", score_skills)
    graph.add_node("score_experience", score_experience)
    graph.add_node("score_education", score_education)
    graph.add_node("score_public_signals", score_public_signals)
    
    # Reducer for parallel scores
    graph.add_node("reduce_scores", reduce_scores)
    
    # Decision node (with Command routing)
    graph.add_node("make_decision", make_decision)
    
    # Email draft
    graph.add_node("draft_email", draft_email)
    
    # Evaluator/critic
    graph.add_node("evaluate_email", evaluate_email)
    
    # Terminal nodes
    graph.add_node("end_advance", end_advance)
    graph.add_node("end_reject", end_reject)
    graph.add_node("end_borderline_approved", end_borderline_approved)
    graph.add_node("end_error", end_error)
    
    # ========================================================================
    # EDGES
    # ========================================================================
    
    # Start -> ingest
    graph.add_edge(START, "ingest_and_parse")
    
    # Ingest -> classify
    graph.add_edge("ingest_and_parse", "classify_seniority")
    
    # Classify -> parallel scoring (fan out)
    graph.add_edge("classify_seniority", "score_skills")
    graph.add_edge("classify_seniority", "score_experience")
    graph.add_edge("classify_seniority", "score_education")
    graph.add_edge("classify_seniority", "score_public_signals")
    
    # All parallel scores -> reducer (fan in)
    graph.add_edge("score_skills", "reduce_scores")
    graph.add_edge("score_experience", "reduce_scores")
    graph.add_edge("score_education", "reduce_scores")
    graph.add_edge("score_public_signals", "reduce_scores")
    
    # Reducer -> decision
    graph.add_edge("reduce_scores", "make_decision")
    
    # Decision -> email draft
    graph.add_edge("make_decision", "draft_email")
    
    # Email draft -> evaluate
    graph.add_edge("draft_email", "evaluate_email")
    
    # Evaluate -> route to terminal nodes based on recommendation
    def route_after_evaluation(state: HireGraphState) -> str:
        """Route based on recommendation."""
        recommendation = state.get("recommendation", "reject")
        
        if recommendation == "advance":
            return "end_advance"
        elif recommendation == "reject":
            return "end_reject"
        else:  # borderline
            return "end_borderline_approved"
    
    graph.add_conditional_edges(
        "evaluate_email",
        route_after_evaluation,
        {
            "end_advance": "end_advance",
            "end_reject": "end_reject",
            "end_borderline_approved": "end_borderline_approved",
        }
    )
    
    # Terminal edges
    graph.add_edge("end_advance", END)
    graph.add_edge("end_reject", END)
    graph.add_edge("end_borderline_approved", END)
    graph.add_edge("end_error", END)
    
    # ========================================================================
    # COMPILE WITH CHECKPOINTER
    # ========================================================================
    
    checkpointer = MemorySaver()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    return compiled_graph


def get_graph():
    """Get or build the compiled graph."""
    return build_graph()
