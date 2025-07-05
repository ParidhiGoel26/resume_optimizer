# Resume Optimizer 🧠📄

## Abstract

The Resume Optimizer is a smart web app that takes your resume and job description, and rewrites your resume to align better with the job requirements.  
It uses OpenAI's GPT model to optimize resume content while maintaining structure and ATS (Applicant Tracking System) friendliness.

---

## Tech Stack

- **Frontend**: HTML + CSS (Jinja2 templating via Flask)  
- **Backend**: Python (Flask) 

---

## Features

- 📤 Upload resume (PDF)
- 🧾 Paste job description
- ⚙️ AI optimizes your resume content
- 📊 ATS Score calculation
- 📄 Diff view of optimized vs original resume
- 📥 Download optimized resume as PDF

---

## How to Run Locally

1. **Clone the repo**:
   ```bash
   git clone https://github.com/ParidhiGoel26/resume_optimizer.git
   cd resume_optimizer

2.**Create virtual environment & install dependencies**:
```bash
python -m venv venv
venv\Scripts\activate   # On Windows
pip install -r requirements.txt

3.**Set your OpenAI API key**:
```bash
Create a .env file in the root folder:
OPENAI_API_KEY=your-key-here

4.**Run the app**:
```bash
python app.py





