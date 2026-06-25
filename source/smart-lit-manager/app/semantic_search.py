"""
Hybrid semantic search engine.
Priority: sentence-transformers (if available) → TF-IDF (built-in fallback).
"""
import math
import re
import logging
from collections import Counter
from typing import List, Optional

from .models import Paper, SearchResult

log = logging.getLogger(__name__)

# Try to load sentence-transformers; gracefully degrade if unavailable
_HAS_SENTENCE_TRANSFORMERS = False
_SENTENCE_MODEL = None

try:
    import sentence_transformers
    _HAS_SENTENCE_TRANSFORMERS = True
    log.info("sentence-transformers available for semantic search")
except ImportError:
    log.info("sentence-transformers not installed; using TF-IDF fallback")


def _get_sentence_model():
    global _SENTENCE_MODEL
    if _HAS_SENTENCE_TRANSFORMERS and _SENTENCE_MODEL is None:
        try:
            _SENTENCE_MODEL = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
            log.info("Loaded all-MiniLM-L6-v2 model")
        except Exception as e:
            log.warning("Failed to load sentence model: %s", e)
    return _SENTENCE_MODEL


class TfidfVectorizer:
    """Lightweight TF-IDF using pure Python + math."""

    def __init__(self):
        self.idf = {}
        self._vocab = {}
        self._doc_count = 0

    def _tokenize(self, text):
        return re.findall(r"[a-z0-9]{2,}", text.lower())

    def fit(self, documents):
        self._doc_count = len(documents)
        df = Counter()
        for doc in documents:
            tokens = set(self._tokenize(doc))
            for t in tokens:
                df[t] += 1
        self._vocab = {t: i for i, t in enumerate(df.keys())}
        self.idf = {t: math.log((self._doc_count + 1) / (freq + 1)) + 1
                    for t, freq in df.items()}
        return self

    def transform(self, document):
        tokens = self._tokenize(document)
        if not tokens:
            return {}
        tf = Counter(tokens)
        max_tf = max(tf.values()) or 1
        return {self._vocab[t]: (count / max_tf) * self.idf.get(t, 0)
                for t, count in tf.items() if t in self._vocab}


class SemanticSearch:
    """Hybrid semantic search engine supporting both sentence-transformers and TF-IDF."""

    def __init__(self):
        self._vectorizer = TfidfVectorizer()
        self._vectors = []
        self._papers = []
        self._is_fitted = False
        self._sentence_model = None
        self._sentence_embeddings = None

    def _use_sentence_model(self):
        if self._sentence_model is None:
            self._sentence_model = _get_sentence_model()
        return self._sentence_model is not None

    def index_papers(self, papers: List[Paper]):
        """Build index from papers. Uses sentence-transformers if available."""
        if not papers:
            self._papers = []
            self._vectors = []
            self._sentence_embeddings = None
            self._is_fitted = False
            return

        self._papers = papers
        documents = [
            f"{p.title or ''} {p.abstract or ''} {p.keywords or ''} {p.authors or ''}"
            for p in papers
        ]

        # Try sentence-transformers first
        if self._use_sentence_model():
            try:
                self._sentence_embeddings = self._sentence_model.encode(
                    documents, show_progress_bar=False
                )
                self._is_fitted = True
                log.info("Indexed %d papers with sentence-transformers", len(papers))
                return
            except Exception as e:
                log.warning("sentence-transformers encoding failed: %s", e)
                self._sentence_embeddings = None

        # Fallback to TF-IDF
        self._vectorizer.fit(documents)
        self._vectors = [self._vectorizer.transform(d) for d in documents]
        self._is_fitted = True
        log.info("Indexed %d papers with TF-IDF", len(papers))

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search papers by semantic similarity."""
        if not self._is_fitted or not query.strip():
            return []

        if self._use_sentence_model() and self._sentence_embeddings is not None:
            return self._sentence_search(query, top_k)
        return self._tfidf_search(query, top_k)

    def _sentence_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Search using sentence-transformers embeddings."""
        try:
            query_vec = self._sentence_model.encode([query])[0]
            scores = []
            for i, emb in enumerate(self._sentence_embeddings):
                sim = self._cosine_similarity_dict(query_vec, emb)
                if sim > 0:
                    scores.append((i, sim))
            scores.sort(key=lambda x: x[1], reverse=True)
            return self._build_results(scores[:top_k])
        except Exception as e:
            log.warning("sentence search failed, falling back: %s", e)
            return self._tfidf_search(query, top_k)

    def _tfidf_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Search using TF-IDF vectors."""
        query_vec = self._vectorizer.transform(query)
        if not query_vec:
            return []
        scores = []
        for i, vec in enumerate(self._vectors):
            sim = self._cosine_similarity(query_vec, vec)
            if sim > 0:
                scores.append((i, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return self._build_results(scores[:top_k])

    def _build_results(self, scored_indices) -> List[SearchResult]:
        results = []
        for idx, score in scored_indices:
            paper = self._papers[idx]
            snippet = (paper.abstract or paper.title)[:200]
            results.append(SearchResult(paper=paper, snippet=snippet, score=round(score, 4)))
        return results

    def similar_papers(self, paper_id: int, top_k: int = 5) -> List[SearchResult]:
        """Find top-k most similar papers to a given paper."""
        target_idx = None
        for i, p in enumerate(self._papers):
            if p.id == paper_id:
                target_idx = i
                break
        if target_idx is None or not self._is_fitted:
            return []

        if self._use_sentence_model() and self._sentence_embeddings is not None:
            target_vec = self._sentence_embeddings[target_idx]
            scored = []
            for i, emb in enumerate(self._sentence_embeddings):
                if i == target_idx:
                    continue
                sim = self._cosine_similarity_dict(target_vec, emb)
                if sim > 0:
                    scored.append((i, sim))
        else:
            target_vec = self._vectors[target_idx] if target_idx < len(self._vectors) else {}
            if not target_vec:
                return []
            scored = []
            for i, vec in enumerate(self._vectors):
                if i == target_idx:
                    continue
                sim = self._cosine_similarity(target_vec, vec)
                if sim > 0:
                    scored.append((i, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        scored = scored[:top_k]
        results = []
        for idx, score in scored:
            paper = self._papers[idx]
            # Include common keywords
            common_keywords = self._common_keywords(self._papers[target_idx], paper)
            snippet = f"Keywords: {paper.keywords or 'N/A'} | Similarity: {score:.2%}"
            if common_keywords:
                snippet += f" | Common: {', '.join(common_keywords[:5])}"
            results.append(SearchResult(paper=paper, snippet=snippet, score=round(score, 4)))
        return results

    @staticmethod
    def _common_keywords(p1: Paper, p2: Paper) -> List[str]:
        """Extract common keywords between two papers."""
        kw1 = set(k.strip().lower() for k in (p1.keywords or "").split(",") if k.strip())
        kw2 = set(k.strip().lower() for k in (p2.keywords or "").split(",") if k.strip())
        common = kw1 & kw2
        # Also check tags
        tag1 = set(t.lower() for t in (p1.tags or []))
        tag2 = set(t.lower() for t in (p2.tags or []))
        common_tags = tag1 & tag2
        return list(common | common_tags)

    @staticmethod
    def _cosine_similarity(vec_a, vec_b):
        """Cosine similarity between two sparse dict vectors."""
        if not vec_a or not vec_b:
            return 0.0
        dot = sum(v * vec_b.get(k, 0) for k, v in vec_a.items())
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _cosine_similarity_dict(vec_a, vec_b):
        """Cosine similarity between two numpy/dense vectors."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# Global singleton
_search_engine = None


def get_search_engine():
    global _search_engine
    if _search_engine is None:
        _search_engine = SemanticSearch()
    return _search_engine
