"""RAG-based Q&A engine for paper full-text analysis with chunking + retrieval."""
import re
import math
import logging
from collections import Counter
from typing import List, Tuple

log = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[dict]:
    """Split text into overlapping chunks.
    
    Args:
        text: Full text content.
        chunk_size: Characters per chunk.
        overlap: Overlap between consecutive chunks.
    
    Returns:
        List of dicts with keys: index, text, start_pos.
    """
    if not text:
        return []
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text_segment = text[start:end]
        chunks.append({
            "index": idx,
            "text": chunk_text_segment,
            "start_pos": start,
        })
        idx += 1
        next_start = start + chunk_size - overlap
        if next_start <= start:
            next_start = start + chunk_size
        start = next_start
    log.debug("Split %d chars into %d chunks", len(text), len(chunks))
    return chunks


def _tokenize(text: str) -> List[str]:
    """Simple tokenizer for TF-IDF scoring."""
    return re.findall(r"[a-z0-9]{2,}", text.lower())


def _tfidf_score(query_tokens: List[str], chunk_text_segment: str) -> float:
    """Compute TF-IDF-like relevance score between query and a chunk."""
    chunk_tokens = _tokenize(chunk_text_segment)
    if not chunk_tokens:
        return 0.0
    chunk_counter = Counter(chunk_tokens)
    max_tf = max(chunk_counter.values()) if chunk_counter else 1
    score = 0.0
    for qt in set(query_tokens):
        tf = chunk_counter.get(qt, 0) / max_tf
        score += tf
    return score / max(len(set(query_tokens)), 1)


def retrieve_relevant_chunks(query: str, chunks: List[dict], top_k: int = 3) -> List[dict]:
    """Retrieve top-k most relevant chunks for a query.
    
    Uses TF-IDF cosine-similarity scoring.
    
    Args:
        query: Natural language question.
        chunks: List of chunk dicts from chunk_text().
        top_k: Number of chunks to return.
    
    Returns:
        Top-k chunks sorted by relevance, each with added 'relevance' key.
    """
    if not query.strip() or not chunks:
        return []
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []
    scored = []
    for chunk in chunks:
        rel = _tfidf_score(query_tokens, chunk["text"])
        if rel > 0:
            scored.append((chunk, rel))
    scored.sort(key=lambda x: x[1], reverse=True)
    result = []
    for chunk, rel in scored[:top_k]:
        chunk_copy = dict(chunk)
        chunk_copy["relevance"] = round(rel, 4)
        result.append(chunk_copy)
    return result


def answer_question(paper_fulltext: str, question: str, ai_assistant=None) -> str:
    """Answer a question about a paper using RAG.
    
    If ai_assistant is provided and configured, uses LLM with retrieved context.
    Otherwise, returns the most relevant text chunks directly.
    
    Args:
        paper_fulltext: Full text content of the paper.
        question: User's question about the paper.
        ai_assistant: Optional AIAssistant instance for LLM-powered answer.
    
    Returns:
        Answer string.
    """
    chunks = chunk_text(paper_fulltext)
    relevant = retrieve_relevant_chunks(question, chunks, top_k=3)
    if not relevant:
        return "No relevant content found in the paper to answer your question."
    context = "\n\n".join(c["text"] for c in relevant)
    
    if ai_assistant and ai_assistant.is_configured():
        prompt = (
            "You are a research assistant. Based on the following paper excerpt, "
            "answer the user's question concisely and accurately.\n\n"
            f"Paper excerpt:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        answer = ai_assistant._call_api(prompt, max_tokens=500)
        if answer:
            return answer
    
    # Fallback: return the most relevant chunk as a summary
    best = relevant[0]
    return f"[Top relevant passage - relevance: {best['relevance']:.2%}]\n\n{best['text'][:500]}..."
