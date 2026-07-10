def optimize_resume(client, original_resume, job_description):
    prompt = f"""
You are an expert resume optimizer.

🎯 Goal:
Slightly optimize the user's uploaded resume to match the provided job description **without changing its structure or formatting**.

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
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
