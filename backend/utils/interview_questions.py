import random
import re


BEHAVIORAL_QUESTIONS = [
    {"text": "Tell me about a challenge you faced and how you overcame it.", "topic": "STAR / Challenges"},
    {"text": "Describe a conflict in your team and how you resolved it.", "topic": "STAR / Teamwork"},
    {"text": "Tell me about a time you failed. What did you learn?", "topic": "STAR / Failure"},
    {"text": "Why should we hire you over other candidates?", "topic": "STAR / Fit"},
    {"text": "Describe a situation where you had to learn something quickly.", "topic": "STAR / Learning"},
    {"text": "Tell me about a time you took initiative without being asked.", "topic": "STAR / Leadership"},
]

HR_QUESTIONS = [
    {"text": "Tell me about yourself.", "topic": "HR / Introduction"},
    {"text": "Why do you want to work at this company?", "topic": "HR / Motivation"},
    {"text": "Why should we hire you?", "topic": "HR / Value"},
    {"text": "What are your greatest strengths and weaknesses?", "topic": "HR / Self-awareness"},
    {"text": "Where do you see yourself in 5 years?", "topic": "HR / Career goals"},
    {"text": "What are your salary expectations?", "topic": "HR / Compensation"},
    {"text": "Why are you leaving your current role?", "topic": "HR / Transition"},
]

TECH_PATTERNS = re.compile(
    r"\b(?:Python|Java|JavaScript|TypeScript|React|Node\.js|AWS|Kafka|Docker|"
    r"Kubernetes|MongoDB|SQL|PostgreSQL|Redis|Spring|Django|Flask|TensorFlow|"
    r"PyTorch|YOLO|OpenCV|Git|CI/CD|Microservices|REST|GraphQL|Linux|Agile)\b",
    re.IGNORECASE,
)


def _extract_projects(resume_text):
    projects = re.findall(
        r"[-•*]\s*([A-Z][^\n]{8,70}(?:project|app|system|platform|tool|recognition|traffic)[^\n]{0,50})",
        resume_text,
        re.IGNORECASE,
    )
    if not projects:
        blocks = re.findall(
            r"(?:PROJECTS?|Personal Projects)[:\s]*\n([\s\S]{0,900})",
            resume_text,
            re.IGNORECASE,
        )
        if blocks:
            projects = re.findall(r"[-•*]\s*([^\n]+)", blocks[0])
    cleaned = []
    for p in projects:
        name = re.sub(r"^[-•*\s]+", "", p.strip())
        if 5 < len(name) < 90:
            cleaned.append(name)
    return list(dict.fromkeys(cleaned))[:6]


def _extract_technologies(text):
    found = TECH_PATTERNS.findall(text or "")
    return list(dict.fromkeys(t.title() if t.lower() != "yolo" else "YOLO" for t in found))


def generate_resume_questions(resume_text):
    questions = []
    projects = _extract_projects(resume_text)
    techs = _extract_technologies(resume_text)

    for project in projects[:4]:
        short = project.split("—")[0].split("-")[0].strip()[:60]
        questions.append({
            "type": "resume",
            "text": f"Explain your {short} project.",
            "topic": short[:40],
        })
        questions.append({
            "type": "resume",
            "text": f"What was the biggest challenge you faced during {short}?",
            "topic": short[:40],
        })

    for tech in techs[:4]:
        questions.append({
            "type": "resume",
            "text": f"Why did you choose {tech} for your project? What alternatives did you consider?",
            "topic": tech,
        })
        questions.append({
            "type": "resume",
            "text": f"How does your experience with {tech} apply to this role?",
            "topic": tech,
        })

    if not questions:
        questions = [
            {"type": "resume", "text": "Walk me through the most relevant project on your resume.", "topic": "Projects"},
            {"type": "resume", "text": "What technical skills from your resume are you strongest in?", "topic": "Skills"},
        ]
    return questions


def generate_jd_questions(jd_text):
    questions = []
    techs = _extract_technologies(jd_text)
    jd_lower = (jd_text or "").lower()

    for tech in techs[:5]:
        questions.append({
            "type": "jd",
            "text": f"The role requires {tech}. Describe your hands-on experience with it.",
            "topic": tech,
        })

    if "responsibilit" in jd_lower or "requirement" in jd_lower:
        questions.append({
            "type": "jd",
            "text": "This role lists specific responsibilities in the JD. Which are you most prepared for and why?",
            "topic": "Responsibilities",
        })
        questions.append({
            "type": "jd",
            "text": "Which requirement from the job description would be your biggest growth area?",
            "topic": "Responsibilities",
        })

    if "team" in jd_lower or "collaborat" in jd_lower:
        questions.append({
            "type": "jd",
            "text": "The JD emphasizes teamwork. Give an example that shows you fit this expectation.",
            "topic": "Teamwork",
        })

    skills_block = re.findall(
        r"(?:skills|requirements|qualifications)[:\s]*([^\n]{20,200})",
        jd_text or "",
        re.IGNORECASE,
    )
    if skills_block:
        questions.append({
            "type": "jd",
            "text": f"The job mentions: \"{skills_block[0][:100]}...\" How do you meet these requirements?",
            "topic": "Required Skills",
        })

    if not questions:
        questions = [
            {"type": "jd", "text": "How does your background align with the key requirements in this job description?", "topic": "Role Fit"},
            {"type": "jd", "text": "What technologies from the JD have you used in production?", "topic": "Technologies"},
        ]
    return questions


def build_interview_session(resume_text, jd_text, count=None):
    pool = []
    pool.extend(generate_resume_questions(resume_text or ""))
    pool.extend(generate_jd_questions(jd_text or ""))

    for q in BEHAVIORAL_QUESTIONS:
        pool.append({"type": "behavioral", **q})
    for q in HR_QUESTIONS:
        pool.append({"type": "hr", **q})

    random.shuffle(pool)
    target = count or random.randint(10, 15)
    target = min(target, len(pool))

    by_type = {"resume": [], "jd": [], "behavioral": [], "hr": []}
    for q in pool:
        by_type[q["type"]].append(q)

    selected = []
    for qtype in ("resume", "jd", "behavioral", "hr"):
        take = max(2, target // 4) if qtype in ("resume", "jd") else max(2, target // 5)
        selected.extend(by_type[qtype][:take])

    random.shuffle(selected)
    selected = selected[:target]

    if len(selected) < 10:
        remaining = [q for q in pool if q not in selected]
        random.shuffle(remaining)
        selected.extend(remaining[: 10 - len(selected)])

    for i, q in enumerate(selected):
        q["id"] = i + 1

    return selected[:target]
