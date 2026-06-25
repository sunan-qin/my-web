import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models import Paper, SearchResult
from app.search_engine import search_with_snippets, _make_snippet


class TestSearchEngine:
    def test_empty_query(self):
        result = search_with_snippets("", [Paper(title="A")])
        assert result == []

    def test_simple_match(self):
        papers = [Paper(title="Machine Learning Basics", abstract="Intro to ML")]
        result = search_with_snippets("Machine", papers)
        assert len(result) >= 1
        assert result[0].score > 0

    def test_no_match(self):
        papers = [Paper(title="Biology")]
        result = search_with_snippets("Physics", papers)
        assert len(result) == 0

    def test_author_boost(self):
        papers = [Paper(title="Paper", authors="Einstein", abstract="Physics")]
        result = search_with_snippets("Einstein", papers)
        assert len(result) >= 1

    def test_multiple_terms(self):
        p = Paper(title="Deep Learning for NLP", abstract="Deep learning methods for NLP")
        result = search_with_snippets("deep learning", [p])
        assert len(result) >= 1

    def test_scoring_order(self):
        p1 = Paper(title="Target Word Here", abstract="short")
        p2 = Paper(title="Random", abstract="Target Word Here appears in abstract")
        result = search_with_snippets("Target Word Here", [p1, p2])
        assert result[0].score >= result[1].score

    def test_snippet_generation(self):
        text = "This is a long text with the TARGET keyword in the middle."
        snippet = _make_snippet(text, ["TARGET"])
        assert "TARGET" in snippet
        assert len(snippet) < len(text) + 30


class TestCitationExport:
    def test_bibtex(self):
        from app.citation_export import to_bibtex
        p = Paper(title="Test", authors="Smith, J.", year=2021, journal="Test J.")
        bib = to_bibtex(p)
        assert "@article" in bib
        assert "Test" in bib
        assert "Smith" in bib
        assert "2021" in bib

    def test_bibtex_many(self):
        from app.citation_export import to_bibtex_many
        bib = to_bibtex_many([Paper(title="A", authors="X"), Paper(title="B", authors="Y")])
        assert bib.count("@article") == 2

    def test_ris(self):
        from app.citation_export import to_ris
        p = Paper(title="Test", authors="Doe, J.", year=2022)
        ris = to_ris(p)
        assert "TY  - JOUR" in ris
        assert "AU  - Doe" in ris
        assert "TI  - Test" in ris
        assert "ER  - " in ris