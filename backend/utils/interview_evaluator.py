import json


def evaluate_answer(client, question, answer, question_type):
    prompt = f"""You are an expert interview coach evaluating a candidate's answer.

Question ({question_type}): {question['text']}
Topic: {question.get('topic', 'General')}

Candidate's answer:
{answer}

Evaluate on these dimensions (scores 1-10, one decimal allowed):
- technical_accuracy: correctness and depth (weight more for resume/jd questions)
- completeness: did they fully answer the question
- communication: clarity, conciseness, structure
- confidence: assertiveness without arrogance
- structure: logical flow (STAR for behavioral, clear intro/body/conclusion for HR)

Return ONLY valid JSON:
{{
  "technical_accuracy": <number>,
  "completeness": <number>,
  "communication": <number>,
  "confidence": <number>,
  "structure": <number>,
  "overall": <number>,
  "feedback": "<2-4 sentences of specific, actionable feedback>",
  "strengths": ["<short phrase>"],
  "improvements": ["<short phrase>"]
}}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)
    return _normalize_evaluation(data)


def _normalize_evaluation(data):
    scores = {}
    for key in ("technical_accuracy", "completeness", "communication", "confidence", "structure"):
        scores[key] = round(float(data.get(key, 7)), 1)

    if "overall" in data:
        scores["overall"] = round(float(data["overall"]), 1)
    else:
        scores["overall"] = round(sum(scores.values()) / len(scores), 1)

    return {
        **scores,
        "feedback": data.get("feedback", "Good effort. Add more specific examples."),
        "strengths": data.get("strengths", [])[:3],
        "improvements": data.get("improvements", [])[:3],
    }
