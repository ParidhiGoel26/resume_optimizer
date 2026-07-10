import math
import re
from collections import Counter


def _tokenize(text):
    return re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())


def _chunk_text(text, source, chunk_size=400, overlap=80):
    if not text or not text.strip():
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    chunk_id = 0

    for para in paragraphs:
        if len(para) <= chunk_size:
            chunks.append({"id": chunk_id, "source": source, "text": para})
            chunk_id += 1
            continue

        start = 0
        while start < len(para):
            end = start + chunk_size
            piece = para[start:end]
            if end < len(para):
                last_space = piece.rfind(" ")
                if last_space > chunk_size // 2:
                    piece = piece[:last_space]
                    end = start + last_space

            chunks.append({"id": chunk_id, "source": source, "text": piece.strip()})
            chunk_id += 1
            start = max(end - overlap, start + 1)

    return chunks


class UserKnowledgeBase:
    def __init__(self):
        self.chunks = []
        self.documents = {}
        self._idf = {}

    def add_document(self, source, content, label=None):
        if not content or not str(content).strip():
            return
        self.documents[source] = {
            "label": label or source,
            "content": content,
        }
        self.chunks.extend(_chunk_text(str(content), source))
        self._idf = {}

    def _compute_idf(self):
        if self._idf:
            return
        doc_freq = Counter()
        for chunk in self.chunks:
            terms = set(_tokenize(chunk["text"]))
            for term in terms:
                doc_freq[term] += 1
        n = len(self.chunks) or 1
        self._idf = {term: math.log((n + 1) / (freq + 1)) + 1 for term, freq in doc_freq.items()}

    def retrieve(self, query, top_k=5):
        if not self.chunks:
            return []

        self._compute_idf()
        query_terms = _tokenize(query)
        if not query_terms:
            return self.chunks[:top_k]

        scored = []
        for chunk in self.chunks:
            chunk_terms = _tokenize(chunk["text"])
            if not chunk_terms:
                continue
            term_freq = Counter(chunk_terms)
            score = 0.0
            for term in query_terms:
                if term in term_freq:
                    score += term_freq[term] * self._idf.get(term, 1.0)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scored[:top_k]:
            results.append({
                "source": chunk["source"],
                "label": self.documents.get(chunk["source"], {}).get("label", chunk["source"]),
                "text": chunk["text"],
                "score": round(score, 2),
            })
        return results

    def list_sources(self):
        return [
            {"id": src, "label": meta["label"], "chars": len(meta["content"])}
            for src, meta in self.documents.items()
        ]

    def extract_projects(self):
        resume_text = ""
        for src in ("resume", "optimized_resume"):
            if src in self.documents:
                resume_text += "\n" + self.documents[src]["content"]

        projects = re.findall(
            r"(?:^|\n)\s*[-•*]?\s*([A-Z][^\n]{10,80}(?:project|app|system|platform|tool)[^\n]{0,60})",
            resume_text,
            re.IGNORECASE | re.MULTILINE,
        )
        if not projects:
            projects = re.findall(
                r"(?:PROJECTS?|Personal Projects)[:\s]*\n([\s\S]{0,800})",
                resume_text,
                re.IGNORECASE,
            )
            if projects:
                bullets = re.findall(r"[-•*]\s*([^\n]+)", projects[0])
                projects = bullets[:6]

        return [p.strip() for p in projects if len(p.strip()) > 5][:8]
