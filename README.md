# Career Copilot - AI-Powered Career Assistant

An AI-powered career toolkit built with Flask. Upload a resume and job description once, then use multiple tools — resume tailoring, ATS analysis, career coaching, interview prep, and document generation — all from a single session.

## Features

| Tool | Route | Description |
|------|-------|-------------|
| **Dashboard** | `/dashboard` | Overview and quick links to all tools |
| **Resume Optimizer** | `/` | Upload a PDF resume, paste a JD, get an AI-tailored version with diff view and PDF download |
| **Analysis** | `/analysis` | ATS score, skill gap analysis, and simulated recruiter review |
| **AI Career Coach** | `/career-coach` | RAG-powered chat grounded in your resume, JD, and career knowledge base |
| **Interview Prep** | `/interview-prep` | 10–15 mixed questions (resume, JD, behavioral, HR) with a final evaluation report |
| **Documents** | `/documents` | ATS-friendly cover letters and professional emails (TXT/PDF export) |

Most tools share resume and JD data from the Resume Optimizer flow. Complete that first for the best experience.

### Resume Optimizer
- PDF resume upload and text extraction
- AI content optimization (OpenAI GPT)
- Side-by-side diff of original vs optimized resume
- ATS keyword scoring
- Download optimized resume as PDF

### Analysis
- ATS compatibility score with matched/missing keywords
- Skill gap breakdown vs the job description
- AI recruiter review with strengths and improvement areas

### AI Career Coach
- Chat interface with context from your resume and JD
- RAG retrieval over a built-in career knowledge base
- Optional GitHub / LeetCode profile connect (mock data in demo mode)

### Interview Prep
- Randomized question sets from resume, JD, behavioral (STAR), and HR categories
- Answer one question at a time; evaluation runs in the background
- Scores and feedback appear in the **final report only** (not per question)

### Documents
- **Cover letter** — Professional, Friendly, or Startup tone; ATS keyword alignment
- **Professional emails** — Job application, internship, recruiter follow-up, referral request
- Export as TXT or PDF

## Tech Stack

- **Backend:** Python 3, Flask, OpenAI API
- **Frontend:** Jinja2 templates, HTML/CSS
- **PDF:** pdfplumber (parsing), ReportLab (export)

## Project Structure

```
resume_optimizer/
├── backend/
│   ├── app.py                 # Flask routes and session logic
│   ├── requirements.txt
│   ├── uploads/               # Uploaded resumes and generated PDFs
│   └── utils/
│       ├── resume_optimizer.py
│       ├── ats_score.py
│       ├── skill_gap.py
│       ├── recruiter_simulator.py
│       ├── career_coach.py / rag.py / knowledge_base.py
│       ├── interview_questions.py / interview_evaluator.py / interview_report.py
│       ├── cover_letter.py / email_generator.py
│       ├── mock_data.py       # Demo mode responses
│       └── pdf_utils.py / pdf_exporter.py / diff_utils.py
├── frontend/
│   ├── templates/             # HTML pages (base layout + tool pages)
│   └── static/css/            # Shared styles (layout.css, tools.css)
├── .env                       # API keys and config (create from .env.example)
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys) (or use demo mode)

## Setup

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd resume_optimizer
   ```

2. **Create environment file**

   Copy `.env.example` to `.env` in the project root:

   ```bash
   cp .env.example .env
   ```

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   FLASK_SECRET_KEY=your_random_secret_key_here

   # Set to true to run the full UI without OpenAI API credits
   DEMO_MODE=true
   ```

   With `DEMO_MODE=true`, AI features return realistic mock responses so you can test every page without spending API credits.

3. **Create a virtual environment and install dependencies**

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate

   pip install -r backend/requirements.txt
   ```

4. **Run the app** (from the project root)

   ```bash
   # Windows (recommended — uses project venv)
   .\venv\Scripts\python.exe backend\app.py

   # macOS / Linux
   python backend/app.py
   ```

5. Open **http://127.0.0.1:5000** in your browser.

## Typical Workflow

1. Go to **Resume Optimizer** — upload your PDF resume and paste the job description.
2. Review the optimized resume, diff, and ATS score.
3. Use other tools (Analysis, Career Coach, Interview Prep, Documents) — they reuse the same session data.
4. Download tailored outputs (resume PDF, cover letter, emails) as needed.

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key for live AI features |
| `FLASK_SECRET_KEY` | No | Flask session secret (defaults to a dev value) |
| `DEMO_MODE` | No | `true` to enable mock AI responses |

\*Not required when `DEMO_MODE=true`.

## Troubleshooting

**`ModuleNotFoundError` (e.g. pdfplumber)**  
Run the app with the virtual environment Python, not the system Python:

```bash
.\venv\Scripts\python.exe backend\app.py
```

**`BuildError: Could not build url for endpoint 'documents'`**  
Usually caused by an old Flask process still running with outdated code. Stop all servers (`Ctrl+C`), then kill stray processes if needed:

```powershell
# Windows PowerShell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*backend*app.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

Restart with a single instance:

```bash
.\venv\Scripts\python.exe backend\app.py
```

**OpenAI quota / rate limit errors**  
Set `DEMO_MODE=true` in `.env` and restart the server.

## Roadmap

- Integrations (LinkedIn, Indeed, etc.)
- Settings page
- Live GitHub / LeetCode API integration
- Voice recording for interview answers

## Contributors

- **Paridhi Goel**
