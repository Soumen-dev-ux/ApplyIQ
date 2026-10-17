from io import BytesIO
from pathlib import Path
import re
from xml.sax.saxutils import escape
import fitz
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

MD_LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^\s\)]+|mailto:[^\s\)]+|[^\s\)]+)\)')
EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
URL_RE = re.compile(r'https?://[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=%]+')
DOMAIN_RE = re.compile(r'\b(?:www\.|github\.com/|linkedin\.com/in/|linkedin\.com/)[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=%]+')

SECTION_KEYWORDS = {
    "summary", "objective", "experience", "work experience", "professional experience",
    "employment", "skills", "technical skills", "core skills", "projects",
    "personal projects", "education", "certifications", "licenses", "awards",
    "achievements", "volunteer", "publications"
}

def safe_tex(s: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(c, c) for c in s)

def tokenize_links(line: str) -> list[tuple[bool, str, str]]:
    """
    Parses a string into chunks of (is_link, display_text, url_target).
    Recognizes markdown links, email addresses, full URLs, and domain URLs (GitHub, LinkedIn, www).
    """
    matches: list[tuple[int, int, str, str]] = []

    # 1. Markdown links: [display](url)
    for m in MD_LINK_RE.finditer(line):
        start, end = m.span()
        display = m.group(1).strip()
        url = m.group(2).strip()
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("mailto:")):
            url = ("mailto:" + url) if "@" in url else ("https://" + url)
        matches.append((start, end, display, url))

    # 2. Email addresses
    for m in EMAIL_RE.finditer(line):
        start, end = m.span()
        if any(not (end <= s or start >= e) for s, e, _, _ in matches):
            continue
        email = m.group(0)
        matches.append((start, end, email, "mailto:" + email))

    # 3. Protocol URLs: http:// or https://
    for m in URL_RE.finditer(line):
        start, end = m.span()
        raw = m.group(0)
        while raw and raw[-1] in ".,;:!?)":
            raw = raw[:-1]
            end -= 1
        if any(not (end <= s or start >= e) for s, e, _, _ in matches):
            continue
        matches.append((start, end, raw, raw))

    # 4. Domain URLs: github.com/..., linkedin.com/..., www....
    for m in DOMAIN_RE.finditer(line):
        start, end = m.span()
        raw = m.group(0)
        while raw and raw[-1] in ".,;:!?)":
            raw = raw[:-1]
            end -= 1
        if any(not (end <= s or start >= e) for s, e, _, _ in matches):
            continue
        matches.append((start, end, raw, "https://" + raw))

    # Assemble disjoint tokens
    tokens: list[tuple[bool, str, str]] = []
    last_idx = 0
    for start, end, display, url in sorted(matches, key=lambda m: m[0]):
        if start > last_idx:
            tokens.append((False, line[last_idx:start], ""))
        tokens.append((True, display, url))
        last_idx = end
    if last_idx < len(line):
        tokens.append((False, line[last_idx:], ""))
    return tokens

def format_tex_line(line: str) -> str:
    tokens = tokenize_links(line)
    out = []
    for is_link, display, url in tokens:
        if not is_link:
            out.append(safe_tex(display))
        else:
            tex_url = url.replace("%", r"\%")
            out.append(r"\href{" + tex_url + "}{" + safe_tex(display) + "}")
    return "".join(out)

def format_pdf_line(line: str) -> str:
    tokens = tokenize_links(line)
    out = []
    for is_link, display, url in tokens:
        if not is_link:
            out.append(escape(display))
        else:
            safe_url = escape(url)
            safe_disp = escape(display)
            out.append(f'<font color="#2563eb"><u><a href="{safe_url}">{safe_disp}</a></u></font>')
    return "".join(out)

def fit_resume_to_one_page(text: str, max_lines: int = 38) -> str:
    """
    Intelligently condenses resume text so that it fits strictly onto a single page.
    Preserves contact information and links, core skills, top experience, and education.
    """
    raw_lines = [l.strip() for l in text.splitlines()]
    cleaned = []
    for line in raw_lines:
        if not line and (not cleaned or not cleaned[-1]):
            continue
        cleaned.append(line)
    while cleaned and not cleaned[-1]:
        cleaned.pop()

    non_empty = [l for l in cleaned if l]
    if len(non_empty) <= max_lines:
        return "\n".join(cleaned)

    # Parse resume into header and sections
    header_lines: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_content: list[str] = []

    for line in cleaned:
        if not line:
            continue
        low = line.lower().strip(":# -_")
        is_heading = (line.isupper() and len(line) < 45) or (low in SECTION_KEYWORDS) or line.startswith("# ") or line.startswith("## ")
        if is_heading:
            if current_title is None and not sections:
                header_lines = list(current_content)
            elif current_title is not None:
                sections.append((current_title, current_content))
            current_title = line.lstrip("# ").strip()
            current_content = []
        else:
            current_content.append(line)

    if current_title is not None:
        sections.append((current_title, current_content))
    elif not sections:
        header_lines = cleaned[:3]
        sections.append(("EXPERIENCE & SKILLS", cleaned[3:]))

    # Keep top 3 header lines (name and contact details with important links)
    final_header = header_lines[:3] if header_lines else []
    
    # Prune sections to fit budget
    budget = max_lines - len(final_header) - len(sections)
    budget = max(budget, 15)

    condensed_sections: list[tuple[str, list[str]]] = []
    for title, lines in sections:
        title_low = title.lower()
        if "skill" in title_low:
            condensed_sections.append((title, lines[:3]))
        elif "education" in title_low:
            condensed_sections.append((title, lines[:2]))
        elif "summary" in title_low or "objective" in title_low:
            condensed_sections.append((title, lines[:2]))
        elif "project" in title_low:
            condensed_sections.append((title, lines[:4]))
        else:
            # Experience or general section: keep top bullets
            condensed_sections.append((title, lines[:6]))

    # Reassemble and enforce strict line limit if still over
    result_lines = list(final_header)
    for title, lines in condensed_sections:
        if result_lines and result_lines[-1] != "":
            result_lines.append("")
        result_lines.append(title)
        result_lines.extend(lines)

    # Flatten and trim trailing items if still exceeding max_lines
    final_non_empty = [l for l in result_lines if l]
    if len(final_non_empty) > max_lines:
        excess = len(final_non_empty) - max_lines
        trimmed: list[str] = []
        for line in reversed(result_lines):
            if excess > 0 and line.startswith(("- ", "• ", "* ")):
                excess -= 1
                continue
            trimmed.append(line)
        result_lines = list(reversed(trimmed))

    return "\n".join(result_lines)

def make_tex(text: str, title: str, single_page: bool = True) -> str:
    if single_page:
        text = fit_resume_to_one_page(text, max_lines=38)

    lines = [x.strip() for x in text.splitlines() if x.strip()]
    out = [
        r"\documentclass[10pt]{article}",
        r"\usepackage[top=0.4in,bottom=0.4in,left=0.45in,right=0.45in]{geometry}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage{enumitem}",
        r"\usepackage{xcolor}",
        r"\definecolor{linkblue}{RGB}{37,99,235}",
        r"\definecolor{headblue}{RGB}{30,58,138}",
        r"\usepackage[colorlinks=true,urlcolor=linkblue,linkcolor=linkblue]{hyperref}",
        r"\pagestyle{empty}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\parskip}{1.5pt}",
        r"\begin{document}",
        r"{\LARGE \textbf{\textcolor{headblue}{" + safe_tex(title) + r"}}}\par\vspace{3pt}",
    ]

    in_itemize = False
    for line in lines:
        is_bullet = line.startswith(("- ", "• ", "* "))
        if is_bullet:
            if not in_itemize:
                out.append(r"\begin{itemize}[leftmargin=*,noitemsep,topsep=1.5pt,parsep=0pt,partopsep=0pt]")
                in_itemize = True
            bullet_body = format_tex_line(line[2:].strip())
            out.append(r"\item " + bullet_body)
            continue

        if in_itemize:
            out.append(r"\end{itemize}")
            in_itemize = False

        is_heading = (line.isupper() and len(line) < 55) or line.startswith("# ") or line.startswith("## ")
        clean_line = line.lstrip("# ").strip()
        if is_heading:
            out.append(r"\vspace{4pt}{\textbf{\normalsize \textcolor{headblue}{" + safe_tex(clean_line) + r"}}}\par\vspace{1pt}\hrule height 0.5pt\vspace{2pt}")
        else:
            out.append(format_tex_line(clean_line) + r"\par")

    if in_itemize:
        out.append(r"\end{itemize}")

    out.append(r"\end{document}")
    return "\n".join(out)

def _render_pdf(text: str, title: str, margin_in: float, font_size: float, leading: float, spacer_ht: float) -> bytes:
    buff = BytesIO()
    doc = SimpleDocTemplate(
        buff,
        pagesize=LETTER,
        rightMargin=margin_in * inch,
        leftMargin=margin_in * inch,
        topMargin=margin_in * inch,
        bottomMargin=margin_in * inch,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="DocHeader",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=font_size + 5.0,
        leading=leading + 5.0,
        spaceAfter=spacer_ht + 1,
        textColor="#1e3a8a",
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading3"],
        fontSize=font_size + 1.5,
        leading=leading + 1.5,
        spaceBefore=spacer_ht + 2,
        spaceAfter=spacer_ht,
        textColor="#1e3a8a",
    ))
    styles.add(ParagraphStyle(
        name="BodyCustom",
        parent=styles["BodyText"],
        fontSize=font_size,
        leading=leading,
        spaceAfter=spacer_ht,
        textColor="#1e293b",
    ))
    styles.add(ParagraphStyle(
        name="BulletCustom",
        parent=styles["BodyText"],
        fontSize=font_size,
        leading=leading,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=spacer_ht,
        textColor="#1e293b",
    ))

    story = [Paragraph(escape(title), styles["DocHeader"])]
    lines = [x.strip() for x in text.splitlines()]
    for line in lines:
        if not line:
            story.append(Spacer(1, spacer_ht))
            continue
        is_heading = (line.isupper() and len(line) < 55) or line.startswith("# ") or line.startswith("## ")
        clean_text = line.lstrip("# ").strip()
        formatted_line = format_pdf_line(clean_text)
        if is_heading:
            story.append(Paragraph(f"<b>{formatted_line}</b>", styles["SectionHeading"]))
        elif line.startswith(("- ", "• ", "* ")):
            bullet_body = format_pdf_line(line[2:].strip())
            story.append(Paragraph(f"• {bullet_body}", styles["BulletCustom"]))
        else:
            story.append(Paragraph(formatted_line, styles["BodyCustom"]))

    doc.build(story)
    return buff.getvalue()

def make_pdf(text: str, title: str, single_page: bool = True) -> bytes:
    if not single_page:
        return _render_pdf(text, title, margin_in=0.6, font_size=9.5, leading=13.0, spacer_ht=4.0)

    condensed_text = fit_resume_to_one_page(text, max_lines=38)
    passes = [
        (0.42, 8.5, 10.8, 2.0),
        (0.38, 8.0, 10.0, 1.5),
        (0.32, 7.5, 9.2, 1.0),
    ]

    last_pdf = None
    for margin_in, font_size, leading, spacer_ht in passes:
        pdf_bytes = _render_pdf(condensed_text, title, margin_in, font_size, leading, spacer_ht)
        last_pdf = pdf_bytes
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                if len(doc) <= 1:
                    return pdf_bytes
        except Exception:
            return pdf_bytes

    # If still > 1 page, prune lines until it fits exactly 1 page
    lines = [l for l in condensed_text.splitlines() if l.strip()]
    while len(lines) > 20:
        lines.pop()
        condensed_text = "\n".join(lines)
        pdf_bytes = _render_pdf(condensed_text, title, margin_in=0.32, font_size=7.5, leading=9.2, spacer_ht=1.0)
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                if len(doc) <= 1:
                    return pdf_bytes
        except Exception:
            return pdf_bytes

    return last_pdf or b""

def build_documents(resume: str, job_title: str, company: str, analysis: dict, llm_docs: dict|None=None) -> dict[str,bytes|str]:
    if llm_docs:
        resume_text = llm_docs.get("resume", resume)
        letter = llm_docs.get("cover_letter", "")
        note = llm_docs.get("cover_note", "")
    else:
        resume_text = fit_resume_to_one_page(resume, max_lines=38)
        company_part = f" at {company}" if company.strip() else ""
        letter = (
            f"Dear Hiring Team,\n\n"
            f"I am writing to express my interest in the {job_title or 'open'} position{company_part}. "
            f"My background, as described in the attached resume, includes the experience and skills explicitly listed there. "
            f"I would welcome the opportunity to discuss how my demonstrated work may relate to your team's needs.\n\n"
            f"I have reviewed the role requirements and am continuing to evaluate how my experience aligns with them. "
            f"I would be glad to provide further detail on relevant projects and contributions.\n\n"
            f"Thank you for your time and consideration.\n\n"
            f"Sincerely,\n[Your name]"
        )
        note = f"Hello, I’m interested in the {job_title or 'open'} role{company_part}. I’ve attached my resume for your consideration and would appreciate the opportunity to discuss the fit. Thank you!"

    title = job_title.strip() or "Professional Resume"
    resume_1page = fit_resume_to_one_page(resume_text, max_lines=38)

    return {
        "resume.txt": resume_1page,
        "cover-letter.txt": letter,
        "cover-note.txt": note,
        "resume.tex": make_tex(resume_1page, title, single_page=True),
        "resume.pdf": make_pdf(resume_1page, title, single_page=True),
        "cover-letter.pdf": make_pdf(letter, "Cover Letter", single_page=False),
        "cover-note.pdf": make_pdf(note, "Cover Note", single_page=False),
    }

