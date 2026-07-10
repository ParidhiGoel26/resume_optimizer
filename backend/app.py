import os
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI

from utils.pdf_utils import extract_text_from_pdf
from utils.diff_utils import get_diff_html
from utils.pdf_exporter import generate_pdf
from utils.recruiter_simulator import simulate_recruiter_review
from utils.resume_optimizer import optimize_resume
from utils.openai_errors import format_openai_error
from utils.ats_score import calculate_ats_score as compute_ats_score
from utils.skill_gap import analyze_skill_gap
from utils.mock_data import (
    mock_optimize_resume,
    mock_recruiter_review,
    mock_skill_gap,
    mock_career_coach_chat,
)
from utils.knowledge_base import build_knowledge_base
from utils.career_coach import career_coach_chat
from utils.interview_questions import build_interview_session
from utils.interview_evaluator import evaluate_answer
from utils.interview_report import mock_evaluate_answer, generate_interview_report
from utils.cover_letter import generate_cover_letter, mock_cover_letter
from utils.email_generator import generate_email, mock_email

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

load_dotenv(PROJECT_ROOT / ".env")
DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")
api_key = os.getenv("OPENAI_API_KEY")

if not DEMO_MODE and not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Create a .env file in the project root "
        f"({PROJECT_ROOT / '.env'}) with your OpenAI API key, "
        "or set DEMO_MODE=true to test without API credits. "
        "See .env.example for the format."
    )

client = OpenAI(api_key=api_key) if api_key else None

app = Flask(
    __name__,
    template_folder=str(FRONTEND_DIR / "templates"),
    static_folder=str(FRONTEND_DIR / "static"),
    static_url_path="/static",
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
app.config["UPLOAD_FOLDER"] = str(BACKEND_DIR / "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

NAV_MAP = {
    "dashboard": "dashboard",
    "index": "resume_optimizer",
    "jobdesc": "resume_optimizer",
    "result": "resume_optimizer",
    "download_pdf": "resume_optimizer",
    "analysis": "analysis",
    "career_coach": "career_coach",
    "career_coach_chat": "career_coach",
    "career_coach_connect": "career_coach",
    "interview_prep": "interview_prep",
    "documents": "documents",
    "documents_cover_letter": "documents",
    "documents_email": "documents",
    "documents_download": "documents",
}


@app.context_processor
def inject_nav():
    return {
        "active_nav": NAV_MAP.get(request.endpoint, ""),
        "demo_mode": DEMO_MODE,
    }


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


def calculate_ats_score(resume_text, jd_text):
    resume_words = set(resume_text.lower().split())
    jd_words = set(jd_text.lower().split())
    matched = jd_words & resume_words
    score = round((len(matched) / len(jd_words)) * 100) if jd_words else 0
    return score, sorted(matched)


def find_added_keywords(original, optimized):
    original_set = set(original.lower().split())
    optimized_set = set(optimized.lower().split())
    return sorted(list(optimized_set - original_set))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        resume = request.files["resume"]
        if resume and resume.filename.endswith(".pdf"):
            filename = secure_filename(resume.filename)
            resume_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            resume.save(resume_path)

            session["resume_filename"] = filename
            return redirect(url_for("jobdesc"))
    return render_template("index.html")


@app.route("/jobdesc", methods=["GET", "POST"])
def jobdesc():
    if request.method == "POST":
        jd_text = request.form["jd"]
        session["jd"] = jd_text
        return redirect(url_for("result", filename=session.get("resume_filename")))
    return render_template("jd.html")


@app.route("/result")
def result():
    filename = request.args.get("filename")
    resume_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    original_resume = extract_text_from_pdf(resume_path)
    job_description = session.get("jd", "")

    api_errors = []
    optimization_failed = False
    optimized_resume = original_resume

    try:
        if DEMO_MODE:
            optimized_resume = mock_optimize_resume(original_resume, job_description)
        else:
            optimized_resume = optimize_resume(client, original_resume, job_description)
    except Exception as exc:
        optimization_failed = True
        message = format_openai_error(exc)
        if message not in api_errors:
            api_errors.append(message)

    session["optimized_resume"] = optimized_resume

    recruiter_review = None
    try:
        if DEMO_MODE:
            recruiter_review = mock_recruiter_review()
        else:
            recruiter_review = simulate_recruiter_review(client, optimized_resume, job_description)
    except Exception as exc:
        message = format_openai_error(exc)
        if message not in api_errors:
            api_errors.append(message)

    ats_score, matched_keywords = calculate_ats_score(optimized_resume, job_description)
    added_keywords = find_added_keywords(original_resume, optimized_resume)
    diff_html = get_diff_html(original_resume, optimized_resume)

    return render_template(
        "result.html",
        filename=filename,
        original_resume=original_resume,
        optimized_resume=optimized_resume,
        diff_html=diff_html,
        ats_score=ats_score,
        matched_keywords=matched_keywords,
        added_keywords=added_keywords,
        recruiter_review=recruiter_review,
        api_errors=api_errors,
        optimization_failed=optimization_failed,
    )


@app.route("/download")
def download_pdf():
    optimized_resume = session.get("optimized_resume", "")
    output_path = os.path.join(app.config["UPLOAD_FOLDER"], "optimized_resume.pdf")
    generate_pdf(optimized_resume, output_path)
    return send_file(output_path, as_attachment=True)


def _load_resume_and_jd(use_session=False, uploaded_file=None, jd_text=""):
    if use_session:
        filename = session.get("resume_filename")
        jd = session.get("jd", "")
        if not filename or not jd:
            return None, None, "No resume or job description found from Resume Optimizer."
        resume_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if not os.path.exists(resume_path):
            return None, None, "Uploaded resume file not found. Please upload again."
        return extract_text_from_pdf(resume_path), jd, None

    jd = jd_text.strip()
    if len(jd) < 50:
        return None, None, "Job description must be at least 50 characters."

    has_new_file = uploaded_file and uploaded_file.filename.endswith(".pdf")
    if has_new_file:
        filename = secure_filename(uploaded_file.filename)
        resume_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        uploaded_file.save(resume_path)
        session["resume_filename"] = filename
        session["jd"] = jd
        return extract_text_from_pdf(resume_path), jd, None

    filename = session.get("resume_filename")
    if filename:
        resume_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(resume_path):
            session["jd"] = jd
            return extract_text_from_pdf(resume_path), jd, None

    return None, None, "Please upload a valid PDF resume."


@app.route("/analysis", methods=["GET", "POST"])
def analysis():
    has_session = bool(session.get("resume_filename") and session.get("jd"))
    session_jd = session.get("jd", "")
    api_errors = []
    results = None
    form_error = None

    if request.method == "POST":
        use_session = request.form.get("use_session") == "1"
        resume_text, jd_text, form_error = _load_resume_and_jd(
            use_session=use_session,
            uploaded_file=request.files.get("resume"),
            jd_text=request.form.get("jd", ""),
        )

        if form_error:
            return render_template(
                "analysis.html",
                has_session=has_session,
                session_jd=session_jd,
                form_error=form_error,
            )

        ats_score, matched_keywords = compute_ats_score(resume_text, jd_text)

        skill_gap = None
        try:
            if DEMO_MODE:
                skill_gap = mock_skill_gap(resume_text, jd_text)
            else:
                skill_gap = analyze_skill_gap(client, resume_text, jd_text)
        except Exception as exc:
            message = format_openai_error(exc)
            if message not in api_errors:
                api_errors.append(message)

        recruiter_review = None
        try:
            if DEMO_MODE:
                recruiter_review = mock_recruiter_review()
            else:
                recruiter_review = simulate_recruiter_review(client, resume_text, jd_text)
        except Exception as exc:
            message = format_openai_error(exc)
            if message not in api_errors:
                api_errors.append(message)

        results = {
            "ats_score": ats_score,
            "matched_keywords": sorted(matched_keywords),
            "skill_gap": skill_gap,
            "recruiter_review": recruiter_review,
        }

    return render_template(
        "analysis.html",
        results=results,
        api_errors=api_errors,
        has_session=has_session,
        session_jd=session_jd,
        form_error=form_error,
    )


def _get_coach_context():
    kb = build_knowledge_base(session, app.config["UPLOAD_FOLDER"])
    sources = kb.list_sources()
    chat_history = session.get("coach_chat", [])
    return kb, sources, chat_history


@app.route("/career-coach")
def career_coach():
    kb, sources, chat_history = _get_coach_context()
    return render_template(
        "career_coach.html",
        sources=sources,
        chat_history=chat_history,
        github_connected=bool(session.get("github_username")),
        leetcode_connected=bool(session.get("leetcode_username")),
        github_username=session.get("github_username", ""),
        leetcode_username=session.get("leetcode_username", ""),
    )


@app.route("/career-coach/chat", methods=["POST"])
def career_coach_chat_api():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message is required."}), 400

    kb, _, chat_history = _get_coach_context()
    retrieved = kb.retrieve(message, top_k=6)
    api_error = None

    try:
        if DEMO_MODE:
            reply, sources, retrieved = mock_career_coach_chat(message, kb, retrieved)
        else:
            reply, sources, retrieved = career_coach_chat(client, message, chat_history, kb)
    except Exception as exc:
        api_error = format_openai_error(exc)
        reply = f"I couldn't generate a response. {api_error}"
        sources = []

    turn = {
        "user": message,
        "assistant": reply,
        "sources": sources,
    }
    chat_history = chat_history + [turn]
    session["coach_chat"] = chat_history[-20:]

    return jsonify({
        "reply": reply,
        "sources": sources,
        "retrieved": [{"label": r["label"], "text": r["text"][:200]} for r in retrieved[:3]],
        "error": api_error,
    })


@app.route("/career-coach/connect", methods=["POST"])
def career_coach_connect():
    data = request.get_json(silent=True) or {}
    platform = data.get("platform")
    username = (data.get("username") or "").strip().lstrip("@")
    disconnect = data.get("disconnect", False)

    if platform == "github":
        session["github_username"] = None if disconnect else username
    elif platform == "leetcode":
        session["leetcode_username"] = None if disconnect else username
    else:
        return jsonify({"error": "Invalid platform."}), 400

    if not disconnect and not username:
        return jsonify({"error": "Username is required."}), 400

    kb, sources, _ = _get_coach_context()
    return jsonify({
        "ok": True,
        "sources": sources,
        "github_connected": bool(session.get("github_username")),
        "leetcode_connected": bool(session.get("leetcode_username")),
    })


@app.route("/career-coach/clear", methods=["POST"])
def career_coach_clear():
    session["coach_chat"] = []
    return jsonify({"ok": True})


def _get_resume_text():
    filename = session.get("resume_filename")
    if not filename:
        return ""
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(path):
        return ""
    return extract_text_from_pdf(path)


@app.route("/interview-prep")
def interview_prep():
    interview = session.get("interview")
    has_data = bool(session.get("resume_filename") or session.get("jd"))
    return render_template(
        "interview_prep.html",
        interview=interview,
        has_data=has_data,
        has_resume=bool(session.get("resume_filename")),
        has_jd=bool(session.get("jd")),
    )


@app.route("/interview-prep/start", methods=["POST"])
def interview_prep_start():
    resume_text = _get_resume_text()
    jd_text = session.get("jd", "")

    if not resume_text and not jd_text:
        return jsonify({
            "error": "Upload a resume and/or job description via Resume Optimizer first.",
        }), 400

    questions = build_interview_session(resume_text, jd_text)
    session["interview"] = {
        "questions": questions,
        "current_index": 0,
        "answers": [],
        "report": None,
    }
    session.modified = True

    return jsonify({
        "total": len(questions),
        "question": questions[0],
    })


@app.route("/interview-prep/answer", methods=["POST"])
def interview_prep_answer():
    data = request.get_json(silent=True) or {}
    answer = (data.get("answer") or "").strip()
    if not answer:
        return jsonify({"error": "Please provide an answer."}), 400

    interview = session.get("interview")
    if not interview or interview.get("report"):
        return jsonify({"error": "No active interview session."}), 400

    idx = interview["current_index"]
    questions = interview["questions"]
    if idx >= len(questions):
        return jsonify({"error": "Interview already completed."}), 400

    question = questions[idx]
    api_error = None

    try:
        if DEMO_MODE:
            evaluation = mock_evaluate_answer(question, answer)
        else:
            evaluation = evaluate_answer(client, question, answer, question["type"])
    except Exception as exc:
        api_error = format_openai_error(exc)
        evaluation = mock_evaluate_answer(question, answer)

    interview["answers"].append({
        "question": question,
        "answer": answer,
        "evaluation": evaluation,
    })
    interview["current_index"] = idx + 1

    done = interview["current_index"] >= len(questions)
    response = {
        "done": done,
        "progress": interview["current_index"],
        "total": len(questions),
        "error": api_error,
    }

    if done:
        interview["report"] = generate_interview_report(questions, interview["answers"])
        response["report"] = interview["report"]
    else:
        response["next_question"] = questions[interview["current_index"]]

    session["interview"] = interview
    session.modified = True
    return jsonify(response)


@app.route("/interview-prep/reset", methods=["POST"])
def interview_prep_reset():
    session.pop("interview", None)
    return jsonify({"ok": True})


def _require_resume_jd():
    resume_text = _get_resume_text()
    jd_text = session.get("jd", "")
    if not resume_text or not jd_text:
        return None, None, "Upload a resume and job description via Resume Optimizer first."
    return resume_text, jd_text, None


@app.route("/documents")
def documents():
    has_resume = bool(session.get("resume_filename"))
    has_jd = bool(session.get("jd"))
    return render_template(
        "documents.html",
        has_data=has_resume and has_jd,
        has_resume=has_resume,
        has_jd=has_jd,
    )


@app.route("/documents/cover-letter", methods=["POST"])
def documents_cover_letter():
    resume_text, jd_text, err = _require_resume_jd()
    if err:
        return jsonify({"error": err}), 400

    data = request.get_json(silent=True) or {}
    tone = data.get("tone", "professional")

    try:
        if DEMO_MODE:
            content = mock_cover_letter(resume_text, jd_text, tone)
        else:
            content = generate_cover_letter(client, resume_text, jd_text, tone)
    except Exception as exc:
        return jsonify({"error": format_openai_error(exc)}), 500

    session["documents_cover_letter"] = content
    session.modified = True
    return jsonify({"content": content, "tone": tone})


@app.route("/documents/email", methods=["POST"])
def documents_email():
    resume_text, jd_text, err = _require_resume_jd()
    if err:
        return jsonify({"error": err}), 400

    data = request.get_json(silent=True) or {}
    email_type = data.get("email_type", "job_application")

    try:
        if DEMO_MODE:
            result = mock_email(resume_text, jd_text, email_type)
        else:
            result = generate_email(client, resume_text, jd_text, email_type)
    except Exception as exc:
        return jsonify({"error": format_openai_error(exc)}), 500

    session["documents_email"] = result
    session.modified = True
    return jsonify(result)


@app.route("/documents/download/<kind>/<fmt>")
def documents_download(kind, fmt):
    if kind == "cover_letter":
        content = session.get("documents_cover_letter", "")
        filename = "cover_letter"
    elif kind == "email":
        email = session.get("documents_email", {})
        content = f"Subject: {email.get('subject', '')}\n\n{email.get('body', '')}"
        filename = "professional_email"
    else:
        return "Not found", 404

    if not content:
        return "Nothing to download. Generate a document first.", 400

    if fmt == "pdf":
        path = os.path.join(app.config["UPLOAD_FOLDER"], f"{filename}.pdf")
        generate_pdf(content, path)
        return send_file(path, as_attachment=True, download_name=f"{filename}.pdf")

    if fmt == "txt":
        from io import BytesIO
        buffer = BytesIO(content.encode("utf-8"))
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{filename}.txt",
            mimetype="text/plain",
        )

    return "Invalid format", 400


if __name__ == "__main__":
    app.run(debug=True)
