# ApplyIQ AI Blueprint

## Goal
An evidence-aware assistant that maps resume evidence to job requirements and prepares editable application drafts. It is not an automated hiring predictor.

## Architecture
- React + TypeScript + Tailwind UI
- FastAPI REST API
- PyMuPDF and python-docx for extraction
- Transparent heuristic requirement coverage
- Optional OpenAI API for drafting only; key remains backend-side
- ReportLab PDF generation and controlled LaTeX template output
- Local artifact storage for development

## Data flow
1. Validate file extension, signature and size.
2. Extract resume text and reject empty/scanned-only documents.
3. Detect job requirements and compare explicit text evidence.
4. Optionally ask an LLM to improve organization and draft cover documents using resume facts only.
5. Generate PDFs and a `.tex` source from controlled code.
6. Return a report and safe download identifiers.

## Limitations
Keyword matches are approximate. A missing keyword does not prove missing ability. PDF output is rendered directly from document text; the `.tex` source is provided for editing/compilation but is not used to render the PDF in this MVP.
