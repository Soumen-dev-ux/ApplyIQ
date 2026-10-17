import re
from collections import OrderedDict

SKILL_TERMS = ["python","java","javascript","typescript","react","node.js","nodejs","fastapi","django","flask","spring boot","html","css","tailwind","sql","postgresql","mysql","mongodb","firebase","git","docker","kubernetes","aws","gcp","azure","machine learning","deep learning","pytorch","tensorflow","rest api","api development","data analysis","communication","leadership","testing","agile","linux","c++","c","figma","excel","power bi"]
STOP = {"the","and","for","with","from","this","that","you","your","are","will","our","have","has","years","year","work","role","team","ability","experience","skills","strong","good","using","use","required","preferred","about","into","across","including","such","must","should","their","they","who","what","when","where","how","all","any","can","not","job","description","responsibilities","requirements","candidate","company"}

def normalize(s: str) -> str: return re.sub(r"\s+", " ", s.lower()).strip()
def extract_skills(text: str) -> list[str]:
    low=normalize(text); found=[]
    for term in SKILL_TERMS:
        pattern=r"(?<![a-z0-9+#.])"+re.escape(term)+r"(?![a-z0-9+#.])"
        if re.search(pattern, low): found.append(term)
    return found
def extract_requirements(job: str) -> list[str]:
    low=normalize(job); requirements=[]
    for term in SKILL_TERMS:
        if re.search(r"(?<![a-z0-9+#.])"+re.escape(term)+r"(?![a-z0-9+#.])", low): requirements.append(term)
    # Add recurring meaningful words for roles whose requirements are not just technical skills.
    words=re.findall(r"[a-z][a-z0-9+#.-]{3,}", low)
    freq=OrderedDict()
    for w in words:
        w=w.strip(".-")
        if w not in STOP and w not in SKILL_TERMS and len(w)>3: freq[w]=freq.get(w,0)+1
    for word,count in sorted(freq.items(),key=lambda x:(-x[1],x[0])):
        if count>=2 and len(requirements)<12: requirements.append(word)
    return requirements[:12]
def analyze(resume: str, job: str) -> dict:
    resume_low=normalize(resume); requirements=extract_requirements(job); skills=extract_skills(resume)
    matched=[]; missing=[]; unclear=[]
    for req in requirements:
        if req in resume_low:
            matched.append(req)
        elif req in SKILL_TERMS:
            missing.append(req)
        else:
            unclear.append(req)
    score=round(100*len(matched)/max(1,len(requirements))) if requirements else 0
    if not requirements: summary="No clear requirements were detected. Add a fuller job description with skills and responsibilities."
    elif score>=75: summary="Your resume explicitly mentions many of the detected requirements. Review the remaining gaps and make sure each match is supported by a concrete example."
    elif score>=40: summary="Your resume mentions some of the detected requirements. Strengthen relevant bullets with truthful examples and review requirements that are not yet evidenced."
    else: summary="The resume text contains limited explicit evidence for the detected requirements. This may reflect missing keywords or missing experience; review each item before making changes."
    return {"coverage_score":score,"summary":summary,"matched_requirements":matched,"missing_requirements":missing,"unclear_requirements":unclear,"candidate_skills":skills}
