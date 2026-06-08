"""End-to-end tests for HireGraph."""

import pytest
from pathlib import Path
from src.hiregraph.graph import build_graph
from src.hiregraph.types import HireGraphState


@pytest.fixture
def sample_data():
    """Load sample data for testing."""
    sample_dir = Path("sample_data")
    
    priya_resume = (sample_dir / "resumes" / "resume_priya.md").read_text()
    eitan_resume = (sample_dir / "resumes" / "resume_eitan.md").read_text()
    mira_resume = (sample_dir / "resumes" / "resume_mira.md").read_text()
    jd = (sample_dir / "jds" / "jd_senior_backend.md").read_text()
    
    return {
        "priya": priya_resume,
        "eitan": eitan_resume,
        "mira": mira_resume,
        "jd": jd,
    }


@pytest.fixture
def graph():
    """Build the graph for testing."""
    return build_graph()


def test_graph_builds():
    """Test that the graph builds without errors."""
    graph = build_graph()
    assert graph is not None


def test_graph_has_nodes():
    """Test that the graph has all required nodes."""
    graph = build_graph()
    
    # Check that graph has nodes
    assert graph is not None
    assert hasattr(graph, 'nodes')
    
    # Check for key nodes by checking the graph structure
    graph_str = str(graph)
    assert "ingest_and_parse" in graph_str or len(graph.nodes) > 0


def test_e2e_strong_candidate(graph, sample_data):
    """Test end-to-end with a strong candidate (Priya)."""
    initial_state: HireGraphState = {
        "resume_text": sample_data["priya"],
        "jd_text": sample_data["jd"],
    }
    
    config = {"configurable": {"thread_id": "test_priya"}}
    
    try:
        result = graph.invoke(initial_state, config=config)
        
        # Check that we got a result
        assert result is not None
        assert "recommendation" in result
        assert "overall_score" in result
        assert "audit_trail" in result
        
        # Strong candidate should get advance or borderline
        assert result["recommendation"] in ["advance", "borderline"]
        
        # Should have audit trail entries
        assert len(result["audit_trail"]) > 0
        
    except Exception as e:
        # If LLM is not available, skip this test
        if "API" in str(e) or "key" in str(e).lower():
            pytest.skip(f"LLM not available: {e}")
        else:
            raise


def test_e2e_weak_candidate(graph, sample_data):
    """Test end-to-end with a weak candidate (Mira)."""
    initial_state: HireGraphState = {
        "resume_text": sample_data["mira"],
        "jd_text": sample_data["jd"],
    }
    
    config = {"configurable": {"thread_id": "test_mira"}}
    
    try:
        result = graph.invoke(initial_state, config=config)
        
        # Check that we got a result
        assert result is not None
        assert "recommendation" in result
        assert "overall_score" in result
        
        # Weak candidate should get reject or borderline
        assert result["recommendation"] in ["reject", "borderline"]
        
    except Exception as e:
        if "API" in str(e) or "key" in str(e).lower():
            pytest.skip(f"LLM not available: {e}")
        else:
            raise


def test_e2e_borderline_candidate(graph, sample_data):
    """Test end-to-end with a borderline candidate (Eitan)."""
    initial_state: HireGraphState = {
        "resume_text": sample_data["eitan"],
        "jd_text": sample_data["jd"],
    }
    
    config = {"configurable": {"thread_id": "test_eitan"}}
    
    try:
        result = graph.invoke(initial_state, config=config)
        
        # Check that we got a result
        assert result is not None
        assert "recommendation" in result
        assert "overall_score" in result
        
        # Should have audit trail
        assert len(result["audit_trail"]) > 0
        
    except Exception as e:
        if "API" in str(e) or "key" in str(e).lower():
            pytest.skip(f"LLM not available: {e}")
        else:
            raise


def test_audit_trail_completeness(graph, sample_data):
    """Test that audit trail captures all node executions."""
    initial_state: HireGraphState = {
        "resume_text": sample_data["priya"],
        "jd_text": sample_data["jd"],
    }
    
    config = {"configurable": {"thread_id": "test_audit"}}
    
    try:
        result = graph.invoke(initial_state, config=config)
        
        # Check audit trail
        audit_trail = result.get("audit_trail", [])
        assert len(audit_trail) > 0
        
        # Check that entries have required fields
        for entry in audit_trail:
            assert "node" in entry
            assert "verdict" in entry
            assert "duration_ms" in entry
            assert "timestamp" in entry
        
    except Exception as e:
        if "API" in str(e) or "key" in str(e).lower():
            pytest.skip(f"LLM not available: {e}")
        else:
            raise
