import re
from typing import List
from .models import Paper, SearchResult


def search_with_snippets(query, papers):
    """Search papers and return results with snippets."""
    if not query.strip():
        return []
    terms = [t.lower() for t in query.split() if len(t) > 1]
    results = []
    for paper in papers:
        score = 0.0
        snippet = ""
        searchable_text = " ".join([
            paper.title or "",
            paper.authors or "",
            paper.abstract or "",
            paper.journal or "",
            paper.notes or "",
        ]).lower()
        for term in terms:
            count = searchable_text.count(term)
            if count > 0:
                score += count * 2
                if term in paper.title.lower():
                    score += 5
                if term in paper.authors.lower():
                    score += 3
        if score > 0:
            if paper.abstract:
                snippet = _make_snippet(paper.abstract, terms)
            elif paper.title:
                snippet = paper.title[:100]
            results.append(SearchResult(paper=paper, snippet=snippet, score=score))
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def _make_snippet(text, terms, context_chars=80):
    """Create a snippet highlighting matching terms."""
    text_lower = text.lower()
    best_pos = -1
    for term in terms:
        pos = text_lower.find(term)
        if pos >= 0:
            best_pos = pos
            break
    if best_pos < 0:
        return text[:200] + ("..." if len(text) > 200 else "")
    start = max(0, best_pos - context_chars)
    end = min(len(text), best_pos + context_chars)
    snippet = ""
    if start > 0:
        snippet += "..."
    snippet += text[start:end]
    if end < len(text):
        snippet += "..."
    return snippet
