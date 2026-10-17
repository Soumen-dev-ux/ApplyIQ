from app.documents import make_tex, make_pdf, fit_resume_to_one_page, tokenize_links
import fitz

def test_tex_escapes_special_characters():
    tex = make_tex("C++ & Python_3", "Engineer")
    assert r"\&" in tex and r"\_" in tex

def test_pdf_starts_with_pdf_header():
    assert make_pdf("Sample resume text", "Resume").startswith(b"%PDF")

def test_tokenize_and_hyperlink_links():
    text = "Contact: test@example.com | [LinkedIn](https://linkedin.com/in/octocat) | github.com/octocat | https://portfolio.dev"
    tokens = tokenize_links(text)
    links = [t for t in tokens if t[0]]
    assert len(links) == 4
    assert links[0][2] == "mailto:test@example.com"
    assert links[1][2] == "https://linkedin.com/in/octocat"
    assert links[2][2] == "https://github.com/octocat"
    assert links[3][2] == "https://portfolio.dev"

def test_tex_generates_href_hyperlinks():
    text = "OCTOCAT DEVELOPER\nEmail: octo@github.com | [GitHub](https://github.com/octocat) | linkedin.com/in/octocat"
    tex = make_tex(text, "Engineer")
    assert r"\href{mailto:octo@github.com}{octo@github.com}" in tex
    assert r"\href{https://github.com/octocat}{GitHub}" in tex
    assert r"\href{https://linkedin.com/in/octocat}{linkedin.com/in/octocat}" in tex
    assert r"\usepackage[colorlinks=true,urlcolor=linkblue,linkcolor=linkblue]{hyperref}" in tex

def test_tex_groups_consecutive_bullets():
    text = "EXPERIENCE\n- Built scalable REST APIs in FastAPI\n- Optimized database queries by 40%\n- Mentored junior engineers"
    tex = make_tex(text, "Engineer")
    assert tex.count(r"\begin{itemize}") == 1
    assert tex.count(r"\end{itemize}") == 1
    assert r"\item Built scalable REST APIs in FastAPI" in tex

def test_fit_resume_to_one_page():
    long_resume = "JOHN DOE\nemail: john@doe.com | github.com/johndoe\n\nSUMMARY\nExperienced engineer.\n\nEXPERIENCE\n" + "\n".join([f"- Led feature {i} resulting in high user satisfaction and metric gains." for i in range(50)]) + "\n\nEDUCATION\nBS Computer Science\n\nSKILLS\nPython, React, SQL, Docker"
    condensed = fit_resume_to_one_page(long_resume, max_lines=38)
    non_empty = [l for l in condensed.splitlines() if l.strip()]
    assert len(non_empty) <= 38
    assert "john@doe.com" in condensed
    assert "EXPERIENCE" in condensed
    assert "EDUCATION" in condensed
    assert "SKILLS" in condensed

def test_pdf_strictly_one_page():
    long_resume = "ALEX RIVERA\nEmail: alex@example.com | github.com/alex | linkedin.com/in/alex\n\nPROFESSIONAL SUMMARY\nSenior software engineer with 8 years building cloud services.\n\nEXPERIENCE\n" + "\n".join([f"- Engineered microservice component {i} handling high throughput requests and improved uptime." for i in range(60)]) + "\n\nEDUCATION\nBS in Software Engineering, University\n\nSKILLS\nPython, FastAPI, TypeScript, React, Docker, Kubernetes, AWS"
    pdf_bytes = make_pdf(long_resume, "Software Engineer", single_page=True)
    assert pdf_bytes.startswith(b"%PDF")
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        assert len(doc) == 1
