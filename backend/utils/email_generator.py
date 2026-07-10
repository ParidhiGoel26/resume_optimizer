import re


EMAIL_TYPES = {
    "job_application": {
        "label": "Job Application",
        "subject_hint": "Application for [Role]",
    },
    "internship_application": {
        "label": "Internship Application",
        "subject_hint": "Internship Application — [Role/Season]",
    },
    "recruiter_followup": {
        "label": "Recruiter Follow-up",
        "subject_hint": "Following up on [Role] application",
    },
    "referral_request": {
        "label": "Referral Request",
        "subject_hint": "Referral request for [Role]",
    },
}


def _extract_name(resume_text):
    lines = [ln.strip() for ln in resume_text.split("\n") if ln.strip()]
    if lines and len(lines[0]) < 50 and "@" not in lines[0]:
        return lines[0]
    return "Candidate"


def _role_hint(jd_text):
    match = re.search(
        r"(?:hiring|seeking|looking for|position)[:\s]*([^\n.]{8,60})",
        jd_text or "",
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else "the open position"


def mock_email(resume_text, jd_text, email_type="job_application"):
    name = _extract_name(resume_text)
    role = _role_hint(jd_text)
    email_type = email_type if email_type in EMAIL_TYPES else "job_application"

    templates = {
        "job_application": {
            "subject": f"Application for {role}",
            "body": (
                f"Dear Hiring Manager,\n\n"
                f"I am writing to apply for {role}. Based on my background outlined in the attached resume, "
                f"I believe I am a strong fit for the technical and collaborative requirements described in your posting.\n\n"
                f"I would welcome the opportunity to discuss how my experience can support your team's goals. "
                f"Thank you for your consideration.\n\n"
                f"Best regards,\n{name}"
            ),
        },
        "internship_application": {
            "subject": f"Internship Application — {role}",
            "body": (
                f"Dear Hiring Team,\n\n"
                f"I am a motivated student/professional eager to contribute as an intern in {role}. "
                f"My coursework and projects have prepared me with hands-on skills that align with your requirements.\n\n"
                f"I am available for the upcoming term and excited to learn while adding value to your team. "
                f"Please find my resume attached for your review.\n\n"
                f"Thank you,\n{name}"
            ),
        },
        "recruiter_followup": {
            "subject": f"Following up — {role} application",
            "body": (
                f"Hi,\n\n"
                f"I wanted to follow up on my application for {role}. I remain very interested in the opportunity "
                f"and believe my skills are well aligned with what you're looking for.\n\n"
                f"If helpful, I'd be happy to share additional work samples or schedule a brief call at your convenience.\n\n"
                f"Best,\n{name}"
            ),
        },
        "referral_request": {
            "subject": f"Referral request for {role}",
            "body": (
                f"Hi [Contact Name],\n\n"
                f"I hope you're doing well. I noticed an opening for {role} at your organization and wondered "
                f"if you might be open to referring me or pointing me to the right contact.\n\n"
                f"I've attached my resume for context. I completely understand if you're unable to — either way, "
                f"I appreciate your time.\n\n"
                f"Thanks,\n{name}"
            ),
        },
    }

    t = templates[email_type]
    return {
        "subject": t["subject"],
        "body": "[Demo Mode]\n\n" + t["body"],
        "type": email_type,
        "type_label": EMAIL_TYPES[email_type]["label"],
    }


def generate_email(client, resume_text, jd_text, email_type="job_application"):
    meta = EMAIL_TYPES.get(email_type, EMAIL_TYPES["job_application"])

    prompt = f"""Write a professional email for: {meta['label']}

Use the candidate's resume and job description. Output plain text with:
Subject: <one line subject>
---
<email body>

Requirements:
- Concise (under 200 words for body)
- Professional, ready to send
- Reference real skills from resume only
- Suggested subject similar to: {meta['subject_hint']}
- Sign with candidate name from resume

Job Description:
{jd_text}

Resume:
{resume_text}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content.strip()

    subject = meta["subject_hint"]
    body = raw
    if "Subject:" in raw:
        parts = raw.split("---", 1)
        subject_line = parts[0].replace("Subject:", "").strip()
        if subject_line:
            subject = subject_line
        if len(parts) > 1:
            body = parts[1].strip()

    return {
        "subject": subject,
        "body": body,
        "type": email_type,
        "type_label": meta["label"],
    }
