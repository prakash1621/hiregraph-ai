"""FastAPI server for HireGraph - Smart Hiring Assistant."""

import os
import sys
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from src.hiregraph.graph import get_graph
from src.hiregraph.parser import parse_file
from src.hiregraph.types import HireGraphState

app = FastAPI(
    title="HireGraph API",
    description="A LangGraph-based smart hiring assistant API",
    version="0.1.0",
)

# CORS for the UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Models
# ============================================================================

class EvaluateRequest(BaseModel):
    """Request body for evaluation."""
    resume_text: str
    jd_text: str
    thread_id: Optional[str] = None


class EvaluateResponse(BaseModel):
    """Response body for evaluation."""
    recommendation: str
    overall_score: float
    seniority_level: str
    decision_reasoning: str
    scorecard: dict
    email_draft: str
    audit_trail: list
    duration_ms: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    llm_configured: bool
    version: str


# ============================================================================
# API Endpoints (defined BEFORE static mount)
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    has_key = bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
    return HealthResponse(
        status="ok",
        llm_configured=has_key,
        version="0.1.0",
    )


@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(request: EvaluateRequest):
    """Evaluate a resume against a job description."""
    if not request.resume_text.strip():
        raise HTTPException(status_code=400, detail="resume_text is required")
    if not request.jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text is required")

    start = time.time()

    graph = get_graph()

    initial_state: HireGraphState = {
        "resume_text": request.resume_text,
        "jd_text": request.jd_text,
    }

    thread_id = request.thread_id or f"api_{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Run synchronous graph.invoke in a thread to not block the event loop
        import asyncio
        result = await asyncio.to_thread(graph.invoke, initial_state, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

    duration_ms = (time.time() - start) * 1000

    return EvaluateResponse(
        recommendation=result.get("recommendation", "reject"),
        overall_score=result.get("overall_score", 0),
        seniority_level=result.get("seniority_level", "unknown"),
        decision_reasoning=result.get("decision_reasoning", ""),
        scorecard=result.get("scorecard", {}),
        email_draft=result.get("email_draft", ""),
        audit_trail=result.get("audit_trail", []),
        duration_ms=duration_ms,
    )


@app.post("/evaluate/file")
async def evaluate_file(
    resume: UploadFile = File(...),
    jd_text: str = Form(...),
):
    """Evaluate a resume file against a job description text."""
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)

    temp_path = temp_dir / resume.filename
    content = await resume.read()
    temp_path.write_bytes(content)

    try:
        resume_text = parse_file(str(temp_path))
    except Exception as e:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Could not parse resume: {str(e)}")
    finally:
        temp_path.unlink(missing_ok=True)

    request = EvaluateRequest(resume_text=resume_text, jd_text=jd_text)
    return await evaluate(request)


@app.get("/sample-data")
async def get_sample_data():
    """Return available sample resumes and JDs."""
    sample_dir = Path("sample_data")
    resumes = []
    jds = []

    supported_extensions = (".md", ".txt", ".docx", ".pdf")

    resumes_dir = sample_dir / "resumes"
    jds_dir = sample_dir / "jds"

    if resumes_dir.exists():
        for f in sorted(resumes_dir.iterdir()):
            if f.suffix.lower() in supported_extensions:
                try:
                    if f.suffix.lower() in (".md", ".txt"):
                        content = f.read_text(encoding="utf-8")
                    else:
                        # Parse binary files (docx, pdf) using our parser
                        content = parse_file(str(f))
                    resumes.append({
                        "name": f.stem,
                        "filename": f.name,
                        "content": content,
                    })
                except Exception:
                    pass

    if jds_dir.exists():
        for f in sorted(jds_dir.iterdir()):
            if f.suffix.lower() in supported_extensions:
                try:
                    if f.suffix.lower() in (".md", ".txt"):
                        content = f.read_text(encoding="utf-8")
                    else:
                        content = parse_file(str(f))
                    jds.append({
                        "name": f.stem,
                        "filename": f.name,
                        "content": content,
                    })
                except Exception:
                    pass

    return {"resumes": resumes, "jds": jds}


@app.get("/graph-image")
async def get_graph_image():
    """Return the compiled graph PNG."""
    graph_path = Path("graph_out/graph.png")
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail="Graph image not found. Run main.py first.")
    return FileResponse(graph_path, media_type="image/png")


# ============================================================================
# UI - Serve index.html at root (AFTER all API routes)
# ============================================================================

ui_path = Path(__file__).parent.parent / "ui"


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the UI index.html."""
    index_file = ui_path / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>UI not found. Place index.html in ui/ folder.</h1>", status_code=404)
