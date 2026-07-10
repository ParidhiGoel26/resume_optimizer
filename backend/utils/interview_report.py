import re


def mock_evaluate_answer(question, answer):
    """Demo-mode evaluation using heuristics."""
    text = (answer or "").strip()
    words = len(text.split())
    qtype = question.get("type", "general")
    topic = question.get("topic", "")

    base = 6.0
    if words >= 80:
        base += 1.5
    elif words >= 40:
        base += 0.8
    elif words < 15:
        base -= 1.5

    star_words = ["situation", "task", "action", "result", "learned", "challenge", "team"]
    if qtype == "behavioral" and any(w in text.lower() for w in star_words):
        base += 1.0

    if topic and topic.lower() in text.lower():
        base += 0.5

    if re.search(r"\d+%|\d+\s*(users|ms|seconds|requests)", text):
        base += 0.4

    base = max(4.0, min(9.5, base))

    structure = base + (0.5 if words > 50 else -0.3)
    communication = base + (0.3 if "." in text else -0.2)
    confidence = base
    technical = base + (0.6 if qtype in ("resume", "jd") and words > 60 else 0)
    completeness = base + (0.4 if words > 70 else -0.4 if words < 25 else 0)

    scores = {
        "technical_accuracy": round(technical, 1),
        "completeness": round(completeness, 1),
        "communication": round(communication, 1),
        "confidence": round(confidence, 1),
        "structure": round(structure, 1),
    }
    scores["overall"] = round(sum(scores.values()) / len(scores), 1)

    feedback_parts = []
    if words < 30:
        feedback_parts.append("Expand your answer with a concrete example and outcome.")
    if qtype == "behavioral" and not any(w in text.lower() for w in star_words):
        feedback_parts.append("Use the STAR method: Situation, Task, Action, Result.")
    if qtype in ("resume", "jd") and topic and topic.lower() not in text.lower():
        feedback_parts.append(f"Mention {topic} explicitly and explain your direct contribution.")
    if not feedback_parts:
        feedback_parts.append("Solid answer. Add metrics or a sharper closing statement.")

    return {
        **scores,
        "feedback": " ".join(feedback_parts),
        "strengths": ["Clear communication"] if words > 40 else ["Concise response"],
        "improvements": ["Add quantified results"] if not re.search(r"\d", text) else ["Deepen technical detail"],
    }


def generate_interview_report(questions, answers_with_evals):
    """Build final report from all answered questions."""
    if not answers_with_evals:
        return {
            "questions_answered": 0,
            "average_overall": 0,
            "dimension_scores": {},
            "strong_areas": [],
            "weak_areas": [],
            "recommendations": ["Complete at least one practice session."],
            "by_type": {},
        }

    topic_scores = {}
    type_scores = {}

    for item in answers_with_evals:
        q = item["question"]
        ev = item["evaluation"]
        topic = q.get("topic", "General")
        qtype = q.get("type", "general")

        topic_scores.setdefault(topic, []).append(ev["overall"])
        type_scores.setdefault(qtype, []).append(ev["overall"])

    def avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else 0

    topic_avgs = {t: avg(s) for t, s in topic_scores.items()}
    strong = sorted(topic_avgs.items(), key=lambda x: x[1], reverse=True)[:5]
    weak = sorted(topic_avgs.items(), key=lambda x: x[1])[:5]

    strong_areas = [t for t, s in strong if s >= 7.0]
    weak_areas = [t for t, s in weak if s < 7.0]

    recommendations = []
    if any(t == "behavioral" for t in type_scores) and avg(type_scores.get("behavioral", [5])) < 7:
        recommendations.append("Practice STAR responses for behavioral questions.")
    if any("Kafka" in t or "AWS" in t or "System" in t for t in weak_areas):
        recommendations.append("Revise distributed systems topics mentioned in the JD (e.g. Kafka, AWS).")
    if avg(type_scores.get("hr", [7])) < 7:
        recommendations.append("Prepare polished answers for 'Tell me about yourself' and 'Why this company?'.")
    if avg(type_scores.get("resume", [7])) < 7:
        recommendations.append("Rehearse deep-dive explanations for each project on your resume.")
    if not recommendations:
        recommendations.append("Strong session overall. Try a harder JD or timed mock next.")

    overall_avg = round(
        sum(item["evaluation"]["overall"] for item in answers_with_evals) / len(answers_with_evals),
        1,
    )

    dimension_keys = ("technical_accuracy", "completeness", "communication", "confidence", "structure")
    dimension_scores = {}
    for key in dimension_keys:
        vals = [item["evaluation"][key] for item in answers_with_evals if key in item["evaluation"]]
        dimension_scores[key] = round(sum(vals) / len(vals), 1) if vals else 0

    return {
        "questions_answered": len(answers_with_evals),
        "average_overall": overall_avg,
        "dimension_scores": dimension_scores,
        "strong_areas": strong_areas[:6] or ["General communication"],
        "weak_areas": weak_areas[:6] or ["Continue practicing"],
        "recommendations": recommendations[:5],
        "by_type": {t: avg(s) for t, s in type_scores.items()},
    }
