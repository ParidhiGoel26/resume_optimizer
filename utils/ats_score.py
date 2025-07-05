import re

def extract_keywords(text):
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    return set(words)

def calculate_ats_score(resume, jd):
    resume_words = extract_keywords(resume)
    jd_words = extract_keywords(jd)

    matched = resume_words & jd_words
    match_percent = int((len(matched) / len(jd_words)) * 100) if jd_words else 0

    return match_percent, list(matched)
