from app.analyzer import analyze, extract_skills
def test_extract_skills():
    assert "python" in extract_skills("Built a Python API with FastAPI and PostgreSQL")
def test_analysis_matches_explicit_evidence():
    result=analyze("Python developer using React and PostgreSQL", "Required: Python, React, Docker")
    assert "python" in result["matched_requirements"]
    assert "react" in result["matched_requirements"]
    assert "docker" in result["missing_requirements"]
    assert result["coverage_score"]==67
