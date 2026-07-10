import os

from utils.pdf_utils import extract_text_from_pdf
from utils.rag import UserKnowledgeBase


def _mock_github_profile(username):
    return f"""GitHub Profile: @{username}
Top Repositories:
- resume-optimizer (Python, Flask) — AI-powered resume tailoring tool
- fullstack-ecommerce (React, Node.js, MongoDB) — MERN stack shopping app
- algo-practice (Python) — Data structures and algorithms solutions

Stats: 24 public repos · 156 commits this year · Primary languages: Python, JavaScript, TypeScript
Notable: Active open-source contributor, strong backend focus"""


def _mock_leetcode_profile(username):
    return f"""LeetCode Profile: @{username}
Problems Solved: 287 total (Easy: 98, Medium: 152, Hard: 37)
Contest Rating: 1,642
Strong topics: Arrays, Hash Maps, Binary Search, Dynamic Programming (basic)
Weak topics: Graph algorithms, Advanced DP, System design
Recent activity: 12 problems solved in the last 30 days"""


def build_knowledge_base(session, upload_folder):
    kb = UserKnowledgeBase()

    filename = session.get("resume_filename")
    if filename:
        path = os.path.join(upload_folder, filename)
        if os.path.exists(path):
            resume_text = extract_text_from_pdf(path)
            kb.add_document("resume", resume_text, "Uploaded Resume")

    jd = session.get("jd")
    if jd:
        kb.add_document("job_description", jd, "Job Description")

    optimized = session.get("optimized_resume")
    if optimized:
        kb.add_document("optimized_resume", optimized, "Previous Optimization")

    github_user = session.get("github_username")
    if github_user:
        kb.add_document("github", _mock_github_profile(github_user), f"GitHub (@{github_user})")

    leetcode_user = session.get("leetcode_username")
    if leetcode_user:
        kb.add_document("leetcode", _mock_leetcode_profile(leetcode_user), f"LeetCode (@{leetcode_user})")

    return kb
