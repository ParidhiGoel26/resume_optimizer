import re


def mock_optimize_resume(original_resume, job_description):
    """Lightweight local 'optimization' for demo mode — injects JD keywords."""
    jd_words = set(re.findall(r"\b[A-Za-z]{4,}\b", job_description.lower()))
    resume_lower = original_resume.lower()
    missing = [w for w in jd_words if w not in resume_lower][:8]

    header = "[DEMO MODE] Sample optimized resume — AI features simulated locally.\n\n"
    optimized = original_resume

    if missing and "SKILLS" in original_resume.upper():
        extra = ", ".join(w.title() for w in missing[:5])
        optimized = optimized.replace("SKILLS", f"SKILLS\n• {extra}", 1)
    elif missing:
        optimized += f"\n\nADDITIONAL KEYWORDS: {', '.join(w.title() for w in missing[:5])}"

    optimized = optimized.replace("experience in", "demonstrated experience in", 1)
    optimized = optimized.replace("Experience in", "Demonstrated experience in", 1)

    return header + optimized


def mock_recruiter_review():
    return {
        "overall_impression": 8.3,
        "strengths": [
            "Strong technical project portfolio",
            "Relevant internship experience",
            "Good alignment with required stack",
            "Clear education background",
        ],
        "weaknesses": [
            "Resume could use more quantified achievements",
            "Summary section is somewhat generic",
            "Missing a few keywords from the JD",
        ],
        "would_shortlist": True,
        "confidence": 78,
    }


def mock_skill_gap(resume_text, job_description):
    jd_skills = re.findall(
        r"\b(?:React|Node\.js|Python|Java|JavaScript|TypeScript|AWS|Docker|"
        r"Kubernetes|MongoDB|SQL|Git|API|DevOps|Machine Learning|TensorFlow|"
        r"Flask|Django|Angular|Vue|C\+\+|Rust|Go|Linux|Agile|Scrum)\b",
        job_description,
        re.IGNORECASE,
    )
    resume_lower = resume_text.lower()
    jd_skills = list(dict.fromkeys(s.title() for s in jd_skills))

    matching = [s for s in jd_skills if s.lower() in resume_lower]
    missing = [s for s in jd_skills if s.lower() not in resume_lower]

    if not jd_skills:
        matching = ["Communication", "Problem Solving", "Teamwork"]
        missing = ["Cloud Platforms", "CI/CD", "System Design"]

    transferable = ["Git", "REST APIs", "Debugging"] if not any(
        t.lower() in resume_lower for t in ["Git", "REST APIs"]
    ) else ["Leadership", "Cross-functional Collaboration"]

    readiness = min(95, 45 + len(matching) * 12 - len(missing) * 5)

    return {
        "matching_skills": matching[:6] or ["Python", "Git", "API Development"],
        "missing_skills": missing[:6] or ["Docker", "AWS", "Kubernetes"],
        "transferable_skills": transferable[:4],
        "gap_summary": (
            f"You match {len(matching)} of {len(jd_skills) or 6} key skills from the job description. "
            "Focus on highlighting missing technologies in your projects section."
        ),
        "readiness_score": max(30, readiness),
    }


def mock_career_coach_chat(message, knowledge_base, retrieved):
    """Demo-mode coach using RAG-retrieved context."""
    q = message.lower()
    sources = list({c["label"] for c in retrieved})
    projects = knowledge_base.extract_projects()
    docs = knowledge_base.list_sources()

    if not docs:
        return (
            "I don't have your documents yet. Upload a resume and job description via "
            "**Resume Optimizer** first, then come back — I'll answer using your actual data.",
            [],
            retrieved,
        )

    prefix = "[Demo Mode] Based on your documents"
    if sources:
        prefix += f" ({', '.join(sources[:3])})"

    # Project removal / ordering
    if "traffic" in q or ("remove" in q and "project" in q):
        if any("traffic" in p.lower() for p in projects):
            return (
                f"{prefix}:\n\n"
                "**Smart Traffic Light** — I'd consider shortening or removing it if:\n"
                "• It's older and less relevant than your other projects\n"
                "• You lack metrics (latency, accuracy, scale)\n"
                "• Your target role is software engineering, not IoT/embedded\n\n"
                "Keep it if you can add 1–2 quantified bullets (e.g. 'Reduced wait time by X%'). "
                "Otherwise, replace it with a project closer to your job description stack.",
                sources,
                retrieved,
            )
        return (
            f"{prefix}:\n\nI couldn't find 'Smart Traffic Light' in your resume. "
            "From your projects section, prioritize roles that match your target JD stack and show measurable impact.",
            sources,
            retrieved,
        )

    if "which project" in q or "project" in q and ("first" in q or "order" in q or "keep" in q):
        if projects:
            ranked = "\n".join(f"{i+1}. **{p[:70]}**" for i, p in enumerate(projects[:5]))
            return (
                f"{prefix} — suggested project order:\n\n{ranked}\n\n"
                "Lead with the project that best matches your target role's tech stack and has the strongest metrics.",
                sources,
                retrieved,
            )
        return (
            f"{prefix}: Add a clear PROJECTS section with 2–4 bullet points each. "
            "I can rank them once they're in your resume.",
            sources,
            retrieved,
        )

    # Amazon / company fit
    if "amazon" in q or "good enough" in q or "ready" in q:
        jd_chunk = next((c for c in retrieved if c["source"] == "job_description"), None)
        resume_chunk = next((c for c in retrieved if c["source"] in ("resume", "optimized_resume")), None)
        gap = mock_skill_gap(
            resume_chunk["text"] if resume_chunk else "",
            jd_chunk["text"] if jd_chunk else "Amazon SDE-1 software development algorithms system design",
        )
        verdict = "promising" if gap["readiness_score"] >= 60 else "needs work"
        return (
            f"{prefix}:\n\n"
            f"**Fit for SDE-1: {verdict.title()}** (readiness ~{gap['readiness_score']}%)\n\n"
            f"**Strengths:** {', '.join(gap['matching_skills'][:4]) or 'solid fundamentals'}\n"
            f"**Gaps:** {', '.join(gap['missing_skills'][:4]) or 'system design, scale'}\n\n"
            "Amazon bar: strong DSA, ownership stories, and system design basics. "
            "Quantify impact on 2–3 projects and prep medium/hard LeetCode.",
            sources,
            retrieved,
        )

    # Missing skills
    if "skill" in q and ("missing" in q or "lack" in q or "gap" in q):
        resume_doc = knowledge_base.documents.get("resume", {}).get("content", "")
        jd_doc = knowledge_base.documents.get("job_description", {}).get("content", "")
        gap = mock_skill_gap(resume_doc, jd_doc)
        return (
            f"{prefix}:\n\n"
            f"**Missing / weak skills:** {', '.join(gap['missing_skills'])}\n"
            f"**You already have:** {', '.join(gap['matching_skills'])}\n"
            f"**Transferable:** {', '.join(gap['transferable_skills'])}\n\n"
            f"{gap['gap_summary']}",
            sources,
            retrieved,
        )

    # Default: summarize retrieved context
    if retrieved:
        excerpt = retrieved[0]["text"][:300]
        return (
            f"{prefix}:\n\n"
            f"From **{retrieved[0]['label']}**: \"{excerpt}...\"\n\n"
            "Ask me specifically about projects, skills gaps, or whether your resume fits a target company.",
            sources,
            retrieved,
        )

    return (
        f"{prefix}: I have {len(docs)} document(s) loaded. "
        "Try: 'Which project should I keep first?' or 'What skills am I missing?'",
        sources,
        retrieved,
    )
