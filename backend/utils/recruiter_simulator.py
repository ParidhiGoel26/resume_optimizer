import json


def simulate_recruiter_review(client, resume_text, job_description):
    prompt = f"""You are an experienced technical recruiter reviewing a candidate's resume for a specific role.

Read the resume and job description carefully. Respond as if you spent 30 seconds scanning this resume before deciding whether to shortlist.

Return ONLY valid JSON with this exact structure:
{{
  "overall_impression": <number 1.0-10.0, one decimal>,
  "strengths": [<3-5 concise strength strings>],
  "weaknesses": [<3-5 concise weakness strings>],
  "would_shortlist": <true or false>,
  "confidence": <integer 0-100 representing how confident you are in your shortlist decision>
}}

Rules:
- Be specific and realistic — reference actual content from the resume.
- Strengths and weaknesses should be short phrases (under 10 words each).
- Base your shortlist decision on fit for THIS job description.
- Confidence is how sure you are about the shortlist decision, not the impression score.

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

    review = json.loads(response.choices[0].message.content)

    return {
        "overall_impression": float(review.get("overall_impression", 0)),
        "strengths": review.get("strengths", []),
        "weaknesses": review.get("weaknesses", []),
        "would_shortlist": bool(review.get("would_shortlist", False)),
        "confidence": int(review.get("confidence", 0)),
    }
