from pathlib import Path
from uuid import uuid4
import re
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .config import settings, ROOT_DIR
from .parser import parse_resume, ResumeParseError
from .analyzer import analyze
from .documents import build_documents
from .ai import generate_documents

app=FastAPI(title="ApplyIQ AI API",version="0.1.0",description="Evidence-aware job application analysis and document generation")
origins=list(dict.fromkeys([settings.frontend_origin,"http://localhost:5173","http://127.0.0.1:5173"]))
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=False,allow_methods=["GET","POST","OPTIONS"],allow_headers=["Content-Type"] )
STORAGE=ROOT_DIR.parent / "storage"; STORAGE.mkdir(exist_ok=True)
ALLOWED={"application/pdf","application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
@app.get("/api/health")
def health(): return {"status":"ok","service":"ApplyIQ AI","version":"0.1.0"}
@app.post("/api/applications/generate")
async def generate_application(resume: UploadFile=File(...),job_title: str=Form(""),company: str=Form(""),job_description: str=Form(...)):
    filename=resume.filename or "resume"; suffix=Path(filename).suffix.lower()
    if suffix not in {".pdf",".docx"}: raise HTTPException(400,"Only PDF and DOCX resumes are supported.")
    content=await resume.read(settings.max_upload_mb*1024*1024+1)
    if len(content)>settings.max_upload_mb*1024*1024: raise HTTPException(413,f"Resume exceeds the {settings.max_upload_mb} MB size limit.")
    if not content: raise HTTPException(400,"The uploaded resume is empty.")
    if suffix==".pdf" and not content.startswith(b"%PDF"): raise HTTPException(400,"The uploaded file does not look like a valid PDF.")
    if suffix==".docx" and not content.startswith(b"PK"): raise HTTPException(400,"The uploaded file does not look like a valid DOCX document.")
    if len(job_description.strip())<30: raise HTTPException(400,"Please provide a fuller job description (at least 30 characters).")
    try: resume_text=parse_resume(filename,content)
    except ResumeParseError as exc: raise HTTPException(422,str(exc)) from exc
    report=analyze(resume_text,job_description)
    notices=["Coverage is a keyword-based heuristic, not a hiring or shortlisting probability.","Review every document and verify every claim before sending.","Items marked missing were not found in extracted text; they do not prove you lack that experience."]
    llm_docs=None
    if settings.openai_api_key.strip():
        try: llm_docs=generate_documents(resume_text,job_title,company,job_description)
        except Exception: notices.append("AI document generation was unavailable; conservative template drafts were used instead.")
    else: notices.append("LLM API key is not configured; the analysis and conservative template drafts use local processing.")
    try: artifacts=build_documents(resume_text,job_title,company,report,llm_docs)
    except Exception as exc: raise HTTPException(500,"Document generation failed. Please try again.") from exc
    application_id=uuid4().hex
    folder=STORAGE/application_id; folder.mkdir(parents=True,exist_ok=False)
    for name,data in artifacts.items():
        (folder/name).write_bytes(data.encode("utf-8") if isinstance(data,str) else data)
    # Return text and LaTeX previews and safe artifact names.
    return {"application_id":application_id,"job_title":job_title or "Target role","company":company,"coverage_score":report["coverage_score"],"summary":report["summary"],"matched_requirements":report["matched_requirements"],"missing_requirements":report["missing_requirements"],"unclear_requirements":report["unclear_requirements"],"candidate_skills":report["candidate_skills"],"artifacts":{k:v for k,v in artifacts.items() if k.endswith(".txt") or k.endswith(".tex")},"notices":notices}

@app.get("/api/applications/{application_id}/download/{artifact}")
def download_artifact(application_id: str,artifact: str):
    if not re.fullmatch(r"[a-f0-9]{32}",application_id): raise HTTPException(400,"Invalid application ID.")
    allowed={"resume.pdf","resume.tex","cover-letter.pdf","cover-note.pdf"}
    if artifact not in allowed: raise HTTPException(404,"Artifact not found.")
    path=STORAGE/application_id/artifact
    if not path.is_file(): raise HTTPException(404,"This artifact has expired or does not exist.")
    return FileResponse(path,filename=artifact,media_type="application/pdf" if artifact.endswith(".pdf") else "application/x-tex")
