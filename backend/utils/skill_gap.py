import json


def analyze_skill_gap(client, resume_text, job_description):
    prompt = f"""You are a career analyst comparing a candidate's resume against a job description.

Identify skill alignment and gaps. Return ONLY valid JSON with this exact structure:
{{
  "matching_skills": [<skills/technologies the candidate clearly has that match the JD>],
  "missing_skills": [<important skills from the JD that are absent or weak on the resume>],
  "transferable_skills": [<candidate skills that partially apply to the role>],
  "gap_summary": "<1-2 sentence summary of the overall skill fit>",
  "readiness_score": <integer 0-100 for how ready the candidate is skill-wise for this role>
}}

Rules:
- List 4-8 items per skills array when possible.
- Use concise skill names (e.g. "React", "System Design", "AWS").
- missing_skills should come directly from JD requirements.
- Be realistic and specific to the provided resume and JD.

Job Description:
{job_description}

Resume:
{resume_text}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)

    return {
        "matching_skills": data.get("matching_skills", []),
        "missing_skills": data.get("missing_skills", []),
        "transferable_skills": data.get("transferable_skills", []),
        "gap_summary": data.get("gap_summary", ""),
        "readiness_score": int(data.get("readiness_score", 0)),
    }
