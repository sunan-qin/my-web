import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models import Paper, Tag, SearchResult


class TestPaper:
    def test_empty_paper(self):
        p = Paper()
        assert p.title == ""
        assert p.formatted_authors() == "Unknown Authors"
        assert p.short_citation().startswith("Unknown")

    def test_paper_basic(self):
        p = Paper(title="Test Title", authors="Smith, J.", year=2023)
        assert p.title == "Test Title"

    def test_authors_with_semicolon(self):
        p = Paper(authors="Smith, J.; Doe, J.")
        result = p.formatted_authors()
        assert "Smith" in result
        assert "Doe" in result

    def test_short_citation_truncates(self):
        p = Paper(title="A" * 100, authors="Doe, J.", year=2020)
        assert len(p.short_citation()) < 130

    def test_no_year_in_citation(self):
        p = Paper(title="No Year", authors="Author")
        assert "(" not in p.short_citation()

    def test_no_authors_citation(self):
        p = Paper(title="Alone")
        assert "Unknown" in p.short_citation()


class TestSearchResult:
    def test_defaults(self):
        sr = SearchResult(paper=Paper())
        assert sr.snippet == ""
        assert sr.score == 0.0

    def test_with_values(self):
        p = Paper(title="Deep Learning")
        sr = SearchResult(paper=p, snippet="...deep...", score=5.0)
        assert sr.paper.title == "Deep Learning"
        assert sr.score == 5.0