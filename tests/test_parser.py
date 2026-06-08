"""Test file parser for PDF, DOCX, and text files."""

import pytest
from pathlib import Path
from src.hiregraph.parser import parse_file, detect_file_type


def test_parse_markdown_file():
    """Test parsing a markdown resume."""
    result = parse_file("sample_data/resumes/resume_priya.md")
    
    assert "Priya Ramanathan" in result
    assert "Senior backend engineer" in result.lower() or "Backend" in result
    assert len(result) > 100


def test_parse_text_jd():
    """Test parsing a markdown JD."""
    result = parse_file("sample_data/jds/jd_senior_backend.md")
    
    assert "Senior Backend Engineer" in result
    assert "Acme Cloud Logistics" in result
    assert len(result) > 100


def test_parse_nonexistent_file():
    """Test that parsing a nonexistent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        parse_file("nonexistent_file.pdf")


def test_detect_file_type_pdf():
    """Test file type detection for PDF."""
    assert detect_file_type("resume.pdf") == "pdf"
    assert detect_file_type("Resume_John_Doe.PDF") == "pdf"


def test_detect_file_type_docx():
    """Test file type detection for DOCX."""
    assert detect_file_type("resume.docx") == "docx"


def test_detect_file_type_markdown():
    """Test file type detection for markdown."""
    assert detect_file_type("resume.md") == "markdown"


def test_detect_file_type_text():
    """Test file type detection for text."""
    assert detect_file_type("resume.txt") == "text"
    assert detect_file_type("resume.other") == "text"
