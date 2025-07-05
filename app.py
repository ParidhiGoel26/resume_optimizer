import os
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI

from utils.pdf_utils import extract_text_from_pdf
from utils.diff_utils import get_diff_html
from utils.pdf_exporter import generate_pdf

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")  # ✅ Pulled from .env
client = OpenAI(api_key=api_key)

# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")  # Optional: .env for secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Utility to calculate ATS score dynamically
def calculate_ats_score(resume_text, jd_text):
    resume_words = set(resume_text.lower().split())
    jd_words = set(jd_text.lower().split())
    matched = jd_words & resume_words
    score = round((len(matched) / len(jd_words)) * 100) if jd_words else 0
    return score, sorted(matched)

# Utility to extract new keywords added in optimization
def find_added_keywords(original, optimized):
    original_set = set(original.lower().split())
    optimized_set = set(optimized.lower().split())
    return sorted(list(optimized_set - original_set))

# STEP 1: Upload Resume
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        resume = request.files['resume']
        if resume and resume.filename.endswith('.pdf'):
            filename = secure_filename(resume.filename)
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume.save(resume_path)

            session['resume_filename'] = filename
            return redirect(url_for('jobdesc'))
    return render_template('index.html')

# STEP 2: Paste Job Description
@app.route('/jobdesc', methods=['GET', 'POST'])
def jobdesc():
    if request.method == 'POST':
        jd_text = request.form['jd']
        session['jd'] = jd_text
        return redirect(url_for('result', filename=session.get('resume_filename')))
    return render_template('jd.html')

# STEP 3: Optimization and Result Page
@app.route('/result')
def result():
    filename = request.args.get('filename')
    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    original_resume = extract_text_from_pdf(resume_path)
    job_description = session.get('jd', '')

    prompt = f"""
You are an expert resume optimizer.

🎯 Goal:
Slightly optimize the user’s uploaded resume to match the provided job description **without changing its structure or formatting**.

📝 Instructions:
- DO NOT change section names, layout, or formatting (e.g., spacing, indentation, bullet style, headers).
- DO NOT add or remove any sections. Keep all headings exactly as in the original resume.
- Keep **80% or more** of the original resume text **unchanged**. Your job is to tweak only the wording slightly where it helps improve alignment with the job description.
- Focus only on:
  - Wording improvements in OBJECTIVE,SUMMARY, WORK EXPERIENCE, SKILLS, and PROJECTS if present 
  - Adding **only very relevant keywords** if needed
  - Slight restructuring of bullet points, only if clearly required for ATS or alignment
- DO NOT modify CERTIFICATIONS, EDUCATION, or ACHIEVEMENTS.
- DO NOT include these instructions or any comments in your response.
- Output ONLY the optimized resume content.
- Write name, contact details, and other personal information exactly as in the original resume.
- Keep the starting information (name, contact details) unchanged.

📄 Job Description:
{job_description}

📄 Resume:
{original_resume}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    optimized_resume = response.choices[0].message.content.strip()

    # Save in session
    session['optimized_resume'] = optimized_resume

    # ATS score calculation
    ats_score, matched_keywords = calculate_ats_score(optimized_resume, job_description)
    added_keywords = find_added_keywords(original_resume, optimized_resume)

    # Diff rendering
    diff_html = get_diff_html(original_resume, optimized_resume)

    return render_template(
        'result.html',
        filename=filename,
        original_resume=original_resume,
        optimized_resume=optimized_resume,
        diff_html=diff_html,
        ats_score=ats_score,
        matched_keywords=matched_keywords,
        added_keywords=added_keywords
    )

# PDF Download
@app.route('/download')
def download_pdf():
    optimized_resume = session.get('optimized_resume', '')
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'optimized_resume.pdf')
    generate_pdf(optimized_resume, output_path)
    return send_file(output_path, as_attachment=True)

# Run
if __name__ == '__main__':
    app.run(debug=True)
