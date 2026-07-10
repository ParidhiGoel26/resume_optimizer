import re


TONE_GUIDES = {
    "professional": "Formal, polished, and confident. Traditional business letter structure.",
    "friendly": "Warm and personable while remaining professional. Conversational but respectful.",
    "startup": "Energetic, concise, and culture-forward. Show passion and scrappy ownership mindset.",
}


def _extract_name(resume_text):
    lines = [ln.strip() for ln in resume_text.split("\n") if ln.strip()]
    if lines:
        first = lines[0]
        if len(first) < 50 and not "@" in first:
            return first
    return "Candidate"


def _jd_keywords(jd_text, limit=8):
    words = re.findall(r"\b[A-Za-z]{4,}\b", jd_text or "")
    stop = {"with", "that", "this", "will", "have", "your", "from", "their", "about", "role", "team"}
    seen = []
    for w in words:
        low = w.lower()
        if low not in stop and low not in [s.lower() for s in seen]:
            seen.append(w.title())
        if len(seen) >= limit:
            break
    return seen


def mock_cover_letter(resume_text, jd_text, tone="professional"):
    name = _extract_name(resume_text)
    keywords = _jd_keywords(jd_text)
    kw_line = ", ".join(keywords[:5]) if keywords else "the required technical skills"

    openings = {
        "professional": f"Dear Hiring Manager,\n\nI am writing to express my strong interest in the position aligned with your requirements. With a background reflected in my resume, I am confident in my ability to contribute effectively to your team.",
        "friendly": f"Hi there,\n\nI hope you're doing well! I came across this opportunity and immediately felt it was a great match for my skills and experience. I'd love to bring my energy and expertise to your team.",
        "startup": f"Hey Team,\n\nI'm excited about this role. I move fast, ship often, and love solving real problems — your JD resonated with me on every line.",
    }

    bodies = {
        "professional": (
            f"My experience includes work with {kw_line}, directly matching the qualifications outlined in your job description. "
            "In my recent roles and projects, I have delivered measurable results through structured execution, collaboration, and continuous improvement."
        ),
        "friendly": (
            f"I've been working with tools like {kw_line}, and I genuinely enjoy building things that make an impact. "
            "What draws me to this role is the chance to grow while contributing to meaningful work alongside a supportive team."
        ),
        "startup": (
            f"I've shipped projects using {kw_line} — not just in theory, but in production. "
            "I thrive in ambiguous environments, wear multiple hats, and care deeply about user impact and team velocity."
        ),
    }

    closings = {
        "professional": "Thank you for your time and consideration. I welcome the opportunity to discuss how my background aligns with your needs.\n\nSincerely,\n" + name,
        "friendly": "Thanks so much for reading — I'd be thrilled to chat more about how I can help.\n\nBest regards,\n" + name,
        "startup": "Let's build something great together. Happy to jump on a quick call anytime.\n\nCheers,\n" + name,
    }

    tone = tone if tone in openings else "professional"
    header = "[Demo Mode] ATS-friendly cover letter\n\n"
    return (
        header
        + openings[tone]
        + "\n\n"
        + bodies[tone]
        + "\n\n"
        + closings[tone]
    )


def generate_cover_letter(client, resume_text, jd_text, tone="professional"):
    tone_guide = TONE_GUIDES.get(tone, TONE_GUIDES["professional"])
    keywords = ", ".join(_jd_keywords(jd_text))

    prompt = f"""Write an ATS-friendly cover letter based on the candidate's resume and job description.

Tone: {tone} — {tone_guide}

Requirements:
- 3-4 short paragraphs, under 400 words
- Include keywords from the JD naturally: {keywords}
- Reference specific skills/experience from the resume (do not invent credentials)
- No placeholder brackets like [Company Name] — use "your organization" if company unknown
- Plain text only, no markdown
- End with the candidate's name from the resume

Job Description:
{jd_text}

Resume:
{resume_text}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
