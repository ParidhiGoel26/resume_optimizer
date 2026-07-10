def _format_context(retrieved):
    if not retrieved:
        return "No relevant document excerpts found."
    parts = []
    for i, chunk in enumerate(retrieved, 1):
        parts.append(f"[{i}] Source: {chunk['label']}\n{chunk['text']}")
    return "\n\n".join(parts)


def career_coach_chat(client, message, chat_history, knowledge_base):
    retrieved = knowledge_base.retrieve(message, top_k=6)
    context = _format_context(retrieved)
    sources = list({c["label"] for c in retrieved})

    history_text = ""
    for turn in chat_history[-6:]:
        history_text += f"User: {turn['user']}\nCoach: {turn['assistant']}\n\n"

    available_docs = ", ".join(s["label"] for s in knowledge_base.list_sources()) or "None"

    prompt = f"""You are an expert AI Career Coach with access to the user's personal career documents.
Answer questions using ONLY the retrieved context and available document list below.
Be specific, actionable, and reference the user's actual resume/projects/skills when possible.
If the user asks about something not in the documents, say what you don't know and suggest what they could upload or connect.

Available documents: {available_docs}

Retrieved context (most relevant excerpts):
{context}

Conversation so far:
{history_text or "(New conversation)"}

User question: {message}

Respond in a helpful, conversational tone. Use bullet points when listing projects or skills.
Keep response under 250 words unless a detailed comparison is needed."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    reply = response.choices[0].message.content.strip()
    return reply, sources, retrieved
