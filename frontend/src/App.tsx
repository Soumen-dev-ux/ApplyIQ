import React, { useState } from 'react';
import {
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  FileText,
  Gauge,
  LoaderCircle,
  Sparkles,
  UploadCloud,
  Download,
  ShieldCheck,
  CircleHelp,
  Check,
  Copy,
  ExternalLink,
} from 'lucide-react';

type Analysis = {
  application_id: string;
  job_title: string;
  company: string;
  coverage_score: number;
  summary: string;
  matched_requirements: string[];
  missing_requirements: string[];
  unclear_requirements: string[];
  candidate_skills: string[];
  artifacts: Record<string, string>;
  notices: string[];
};

const API = String(import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
const artifactLabels: Record<string, string> = {
  'resume.pdf': 'Resume PDF (1-Page)',
  'resume.tex': 'LaTeX Source (.tex)',
  'cover-letter.pdf': 'Cover letter PDF',
  'cover-note.pdf': 'Cover note PDF',
};

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [description, setDescription] = useState('');
  const [result, setResult] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('overview');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setResult(null);
    if (!file) {
      setError('Please choose your current resume first.');
      return;
    }
    if (!description.trim()) {
      setError('Paste the job description so the analysis has something to compare against.');
      return;
    }
    const body = new FormData();
    body.append('resume', file);
    body.append('job_title', jobTitle);
    body.append('company', company);
    body.append('job_description', description);
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/applications/generate`, { method: 'POST', body });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'The application could not be generated.');
      setResult(data);
      setTab('overview');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not reach the API. Is the backend running on port 8000?');
    } finally {
      setLoading(false);
    }
  }

  async function download(name: string) {
    if (!result) return;
    try {
      const r = await fetch(`${API}/api/applications/${result.application_id}/download/${encodeURIComponent(name)}`);
      if (!r.ok) throw new Error('Download failed.');
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Download failed.');
    }
  }

  return (
    <div className="app-shell">
      <header className="flex flex-wrap items-center justify-between gap-4 mb-10">
        <div className="flex items-center gap-3">
          <div className="grid place-items-center w-11 h-11 rounded-2xl bg-violet-600 text-white">
            <Sparkles size={23} />
          </div>
          <div>
            <div className="font-extrabold text-xl tracking-tight">
              ApplyIQ <span className="text-violet-600">AI</span>
            </div>
            <div className="text-xs muted">Your application, backed by evidence</div>
          </div>
        </div>
        <div className="hidden sm:flex items-center gap-2 text-sm muted">
          <ShieldCheck size={16} /> Private-by-design local MVP
        </div>
      </header>

      <section className="mb-8">
        <div className="eyebrow mb-3">JOB APPLICATION INTELLIGENCE</div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight max-w-3xl leading-tight">
          Apply with clarity.
          <br />
          <span className="text-violet-600">Show your strongest evidence.</span>
        </h1>
        <p className="muted mt-4 max-w-2xl leading-7">
          Compare your resume with a real role, spot gaps honestly, and create strictly 1-page application documents with hyperlinked profiles you can review and edit before sending.
        </p>
      </section>

      <div className="grid lg:grid-cols-[.9fr_1.1fr] gap-6 items-start">
        <form className="panel p-5 sm:p-7" onSubmit={submit}>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-violet-50 text-violet-700 grid place-items-center">
              <BriefcaseBusiness size={20} />
            </div>
            <div>
              <h2 className="font-bold text-lg">Build your application</h2>
              <p className="text-sm muted">Start with your resume and target role.</p>
            </div>
          </div>

          <label className="block text-sm font-semibold mb-2">
            Resume file <span className="muted font-normal">(PDF or DOCX, max 5 MB)</span>
          </label>
          <label className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-slate-200 hover:border-violet-400 rounded-xl p-6 mb-5 text-center cursor-pointer">
            <UploadCloud className="text-violet-600" size={27} />
            <span className="font-semibold text-sm">{file ? file.name : 'Choose your resume'}</span>
            <span className="text-xs muted">Your existing experience stays the source of truth</span>
            <input
              className="hidden"
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </label>

          <div className="grid sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-semibold mb-2">Job title</label>
              <input
                className="field"
                placeholder="e.g. Junior Full Stack Developer"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-2">Company</label>
              <input
                className="field"
                placeholder="e.g. Acme Technologies"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
              />
            </div>
          </div>

          <label className="block text-sm font-semibold mb-2">
            Job description <span className="text-rose-500">*</span>
          </label>
          <textarea
            className="field min-h-44 resize-y"
            placeholder="Paste the full job description here…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
          <p className="text-xs muted mt-2 mb-5">
            Tip: include responsibilities and required skills for a more useful comparison.
          </p>

          {error && <div className="error text-sm mb-4">{error}</div>}

          <button className="primary w-full flex justify-center items-center gap-2" disabled={loading}>
            {loading ? (
              <>
                <LoaderCircle size={18} className="animate-spin" /> Analysing your application…
              </>
            ) : (
              <>
                Analyse & generate documents <ArrowRight size={17} />
              </>
            )}
          </button>
          <p className="text-xs muted leading-5 mt-3">
            <CircleHelp size={13} className="inline mr-1" />
            Never submit generated text without checking every claim.
          </p>
        </form>

        <section className="panel p-5 sm:p-7 min-h-[510px]">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-700 grid place-items-center">
              <Gauge size={20} />
            </div>
            <div>
              <h2 className="font-bold text-lg">Application insights</h2>
              <p className="text-sm muted">Your report and exportable documents appear here.</p>
            </div>
          </div>

          {!result && !loading && (
            <div className="h-80 flex flex-col items-center justify-center text-center px-5">
              <div className="w-16 h-16 rounded-2xl bg-slate-50 grid place-items-center text-slate-400 mb-4">
                <FileText size={28} />
              </div>
              <h3 className="font-bold text-lg mb-2">Your report starts here</h3>
              <p className="muted text-sm leading-6 max-w-sm">
                Upload a resume and add a job description. We’ll map requirements to evidence and prepare strictly 1-page documents with clickable profile links.
              </p>
              <div className="grid grid-cols-3 gap-2 mt-7 w-full max-w-md">
                <div className="bg-slate-50 rounded-xl p-3">
                  <div className="text-violet-600 mb-2">
                    <Gauge size={17} />
                  </div>
                  <div className="text-xs font-semibold">Job-fit</div>
                </div>
                <div className="bg-slate-50 rounded-xl p-3">
                  <div className="text-violet-600 mb-2">
                    <CheckCircle2 size={17} />
                  </div>
                  <div className="text-xs font-semibold">Evidence</div>
                </div>
                <div className="bg-slate-50 rounded-xl p-3">
                  <div className="text-violet-600 mb-2">
                    <Download size={17} />
                  </div>
                  <div className="text-xs font-semibold">Documents</div>
                </div>
              </div>
            </div>
          )}

          {loading && (
            <div className="h-80 flex flex-col items-center justify-center">
              <LoaderCircle size={32} className="animate-spin text-violet-600 mb-4" />
              <p className="font-semibold">Reading resume, condensing to 1 page, and mapping requirements…</p>
              <p className="muted text-sm mt-2">This can take a few seconds.</p>
            </div>
          )}

          {result && (
            <>
              <div className="flex gap-2 flex-wrap mb-5">
                {[
                  ['overview', 'Fit report'],
                  ['resume', 'Resume draft (1-page)'],
                  ['letter', 'Cover letter'],
                  ['note', 'Cover note'],
                  ['tex', 'LaTeX source'],
                ].map(([id, label]) => (
                  <button
                    type="button"
                    key={id}
                    className={`result-tab text-sm ${tab === id ? 'active font-semibold' : ''}`}
                    onClick={() => setTab(id)}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {tab === 'overview' && (
                <>
                  <div className="rounded-2xl bg-violet-50 p-5 mb-5">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-violet-900">Requirement coverage</div>
                        <div className="text-xs text-violet-800 mt-1">Heuristic match, not hiring probability</div>
                      </div>
                      <div className="text-4xl font-extrabold text-violet-700">{result.coverage_score}%</div>
                    </div>
                    <div className="meter mt-4">
                      <span style={{ width: `${result.coverage_score}%` }} />
                    </div>
                    <p className="text-sm text-violet-950 mt-4 leading-6">{result.summary}</p>
                  </div>
                  <div className="grid grid-cols-3 gap-2 mb-5">
                    {[
                      [result.matched_requirements.length, 'Matched', 'text-emerald-700'],
                      [result.unclear_requirements.length, 'Unclear', 'text-amber-700'],
                      [result.missing_requirements.length, 'Not found', 'text-rose-700'],
                    ].map(([n, l, c]) => (
                      <div key={String(l)} className="border border-slate-100 rounded-xl p-3">
                        <div className={`text-2xl font-extrabold ${c}`}>{n}</div>
                        <div className="text-xs muted">{l}</div>
                      </div>
                    ))}
                  </div>
                  <RequirementGroup title="Evidence found" items={result.matched_requirements} color="green" />
                  <RequirementGroup title="Needs confirmation / unclear" items={result.unclear_requirements} color="amber" />
                  <RequirementGroup title="Not found in resume" items={result.missing_requirements} color="red" />
                  <div className="text-xs muted mt-4 leading-5">
                    A missing item may mean it was not mentioned in your resume, not that you lack the skill. Add evidence only if it is accurate.
                  </div>
                </>
              )}

              {tab === 'resume' && (
                <DocumentPreview
                  text={result.artifacts['resume.txt'] || 'Resume draft is unavailable.'}
                  isResume={true}
                />
              )}

              {tab === 'letter' && (
                <DocumentPreview text={result.artifacts['cover-letter.txt'] || 'Cover letter is unavailable.'} />
              )}

              {tab === 'note' && (
                <DocumentPreview text={result.artifacts['cover-note.txt'] || 'Cover note is unavailable.'} />
              )}

              {tab === 'tex' && (
                <DocumentPreview
                  text={result.artifacts['resume.tex'] || 'LaTeX code is unavailable.'}
                  isTex={true}
                />
              )}

              <div className="border-t border-slate-100 pt-5 mt-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-bold">Download your documents</h3>
                  <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
                    ✓ 1-Page Resume Guaranteed
                  </span>
                </div>
                <div className="grid sm:grid-cols-2 gap-2">
                  {Object.entries(artifactLabels).map(([name, label]) => (
                    <button
                      type="button"
                      key={name}
                      onClick={() => download(name)}
                      className="flex items-center justify-between gap-2 border border-slate-200 hover:border-violet-300 rounded-xl px-3 py-3 text-left text-sm"
                    >
                      <span className="flex items-center gap-2">
                        <FileText size={17} className="text-violet-600" />
                        {label}
                      </span>
                      <Download size={16} className="muted" />
                    </button>
                  ))}
                </div>
              </div>

              {result.notices.length > 0 && (
                <div className="mt-4 text-xs muted leading-5">
                  {result.notices.map((n, i) => (
                    <p key={i}>• {n}</p>
                  ))}
                </div>
              )}
            </>
          )}
        </section>
      </div>

      <footer className="text-center text-xs muted mt-8">
        ApplyIQ AI · Evidence before embellishment · Strictly 1-page resume · Clickable hyperlinks
      </footer>
    </div>
  );
}

function RequirementGroup({
  title,
  items,
  color,
}: {
  title: string;
  items: string[];
  color: 'green' | 'amber' | 'red';
}) {
  const styles = { green: 'bg-emerald-500', amber: 'bg-amber-500', red: 'bg-rose-500' };
  return (
    <div className="mb-4">
      <h3 className="text-sm font-bold mb-2">
        {title} <span className="muted font-normal">({items.length})</span>
      </h3>
      {items.length ? (
        <ul className="space-y-2">
          {items.map((x, i) => (
            <li key={`${x}-${i}`} className="flex items-start gap-2 text-sm">
              <span className={`w-2 h-2 rounded-full ${styles[color]} mt-1.5 shrink-0`} />
              <span>{x}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm muted">Nothing to show here.</p>
      )}
    </div>
  );
}

function DocumentPreview({
  text,
  isTex = false,
  isResume = false,
}: {
  text: string;
  isTex?: boolean;
  isResume?: boolean;
}) {
  const [copied, setCopied] = useState(false);

  function copyText() {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="space-y-3">
      {isResume && (
        <div className="flex items-center justify-between gap-2 bg-emerald-50 border border-emerald-200 text-emerald-900 px-3.5 py-2 rounded-xl text-xs font-semibold">
          <span>✓ Strict 1-Page Layout Guaranteed</span>
          <span className="text-[11px] font-normal text-emerald-700">Important links & profiles hyperlinked below</span>
        </div>
      )}

      {isTex && (
        <div className="flex items-center justify-between gap-2 bg-violet-50 border border-violet-200 text-violet-900 px-3.5 py-2 rounded-xl text-xs font-semibold">
          <span>LaTeX Source Code (\href Hyperlinks Enabled)</span>
          <button
            type="button"
            onClick={copyText}
            className="flex items-center gap-1.5 bg-white border border-violet-200 hover:border-violet-400 text-violet-700 px-2.5 py-1 rounded-md text-xs font-medium transition"
          >
            {copied ? <Check size={13} className="text-emerald-600" /> : <Copy size={13} />}
            {copied ? 'Copied code!' : 'Copy LaTeX'}
          </button>
        </div>
      )}

      {!isTex && (
        <div className="flex justify-end">
          <button
            type="button"
            onClick={copyText}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 transition py-1 px-2 rounded hover:bg-slate-100"
          >
            {copied ? <Check size={13} className="text-emerald-600" /> : <Copy size={13} />}
            {copied ? 'Copied text!' : 'Copy text'}
          </button>
        </div>
      )}

      <div className="rounded-xl bg-slate-50 border border-slate-100 p-4 max-h-[430px] overflow-auto">
        {isTex ? (
          <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-5 text-slate-800">
            {text}
          </pre>
        ) : (
          <div className="whitespace-pre-wrap break-words font-sans text-sm leading-6 text-slate-700">
            {renderInteractiveLinks(text)}
          </div>
        )}
      </div>
    </div>
  );
}

function renderInteractiveLinks(text: string) {
  const lines = text.split('\n');
  const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\s\)]+|mailto:[^\s\)]+|[^\s\)]+)\)|(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b)|(https?:\/\/[^\s\)<>"]+)|(\b(?:www\.|github\.com\/|linkedin\.com\/in\/|linkedin\.com\/)[^\s\)<>"]+)/g;

  return lines.map((line, lineIdx) => {
    const parts: (string | React.ReactNode)[] = [];
    let lastIdx = 0;
    let match: RegExpExecArray | null;

    linkRegex.lastIndex = 0;
    while ((match = linkRegex.exec(line)) !== null) {
      if (match.index > lastIdx) {
        parts.push(line.slice(lastIdx, match.index));
      }

      let display = '';
      let url = '';

      if (match[1] && match[2]) {
        display = match[1];
        url = match[2];
        if (!url.startsWith('http://') && !url.startsWith('https://') && !url.startsWith('mailto:')) {
          url = url.includes('@') ? `mailto:${url}` : `https://${url}`;
        }
      } else if (match[3]) {
        display = match[3];
        url = `mailto:${display}`;
      } else if (match[4]) {
        display = match[4];
        url = display;
      } else if (match[5]) {
        display = match[5];
        url = `https://${display}`;
      }

      while (display && '.,;:!?)'.includes(display.slice(-1)) && !match[1]) {
        display = display.slice(0, -1);
      }
      if (url && display && !match[1] && '.,;:!?)'.includes(url.slice(-1))) {
        url = url.slice(0, -1);
      }

      parts.push(
        <a
          key={`link-${lineIdx}-${match.index}`}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-violet-600 hover:text-violet-800 underline font-medium inline-flex items-center gap-0.5 mx-0.5"
        >
          <span>{display}</span>
          <ExternalLink size={11} className="inline opacity-70" />
        </a>
      );
      lastIdx = match.index + match[0].length;
    }

    if (lastIdx < line.length) {
      parts.push(line.slice(lastIdx));
    }

    return (
      <div key={`line-${lineIdx}`} className="min-h-[1.4rem]">
        {parts.length > 0 ? parts : '\u00A0'}
      </div>
    );
  });
}
