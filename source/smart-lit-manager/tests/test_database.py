import sys, os, tempfile, shutil
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app.database as db_mod
from app.models import Paper


def _fresh_connection():
    db_mod.DB_DIR = tempfile.mkdtemp()
    db_mod.DB_PATH = os.path.join(db_mod.DB_DIR, "library.db")
    db_mod.init_db()


@pytest.fixture(autouse=True)
def fresh_db():
    _orig_dir = db_mod.DB_DIR
    _orig_path = db_mod.DB_PATH
    _fresh_connection()
    yield
    shutil.rmtree(db_mod.DB_DIR, ignore_errors=True)
    db_mod.DB_DIR = _orig_dir
    db_mod.DB_PATH = _orig_path


def _mk(title="Test", authors="Auth", year=2023, tags=None):
    return Paper(title=title, authors=authors, year=year, tags=tags or ["test"])


class TestAddGet:
    def test_add_and_get(self):
        pid = db_mod.add_paper(_mk())
        p = db_mod.get_paper(pid)
        assert p is not None
        assert p.title == "Test"

    def test_get_nonexistent(self):
        assert db_mod.get_paper(99999) is None

    def test_add_multiple(self):
        db_mod.add_paper(_mk("A"))
        db_mod.add_paper(_mk("B"))
        assert len(db_mod.get_all_papers()) == 2


class TestUpdate:
    def test_update_title(self):
        p = _mk("Old Title")
        pid = db_mod.add_paper(p)
        p.id = pid
        p.title = "New Title"
        db_mod.update_paper(p)
        assert db_mod.get_paper(pid).title == "New Title"

    def test_update_tags(self):
        p = _mk(tags=["old-tag"])
        pid = db_mod.add_paper(p)
        p.id = pid
        p.tags = ["new-tag"]
        db_mod.update_paper(p)
        assert db_mod.get_paper(pid).tags == ["new-tag"]


class TestDelete:
    def test_delete_paper(self):
        pid = db_mod.add_paper(_mk())
        db_mod.delete_paper(pid)
        assert db_mod.get_paper(pid) is None

    def test_delete_reduces_count(self):
        db_mod.add_paper(_mk("A"))
        db_mod.add_paper(_mk("B"))
        n = len(db_mod.get_all_papers())
        db_mod.delete_paper(1)
        assert len(db_mod.get_all_papers()) == n - 1


class TestSearch:
    def test_search_by_title(self):
        db_mod.add_paper(_mk("Quantum Computing"))
        assert len(db_mod.search_papers("Quantum")) >= 1

    def test_search_by_author(self):
        db_mod.add_paper(_mk(authors="Einstein"))
        assert len(db_mod.search_papers("Einstein")) >= 1

    def test_search_no_results(self):
        db_mod.add_paper(_mk("Alpha"))
        assert len(db_mod.search_papers("NonexistentXYZ")) == 0

    def test_search_empty(self):
        db_mod.add_paper(_mk("Whatever"))
        assert len(db_mod.search_papers("")) >= 1


class TestFulltext:
    def test_save_and_get(self):
        pid = db_mod.add_paper(_mk())
        db_mod.save_fulltext(pid, "full text content")
        assert db_mod.get_fulltext(pid) == "full text content"

    def test_fulltext_searchable(self):
        pid = db_mod.add_paper(_mk("Fancy"))
        db_mod.save_fulltext(pid, "rare_term_xyz_42")
        assert len(db_mod.search_papers("rare_term_xyz_42")) >= 1

    def test_get_nonexistent(self):
        pid = db_mod.add_paper(_mk("NoFulltext"))
        assert db_mod.get_fulltext(pid) is None


class TestStats:
    def test_empty_stats(self):
        s = db_mod.get_stats()
        assert s["total"] == 0
        assert s["tag_count"] == 0

    def test_stats_after_add(self):
        db_mod.add_paper(_mk("A", year=2024))
        db_mod.add_paper(_mk("B", year=2024))
        s = db_mod.get_stats()
        assert s["total"] == 2
        assert s["years"].get(2024) == 2


class TestTags:
    def test_auto_creates_tag(self):
        pid = db_mod.add_paper(_mk(tags=["autotag"]))
        assert "autotag" in db_mod.get_paper(pid).tags

    def test_get_all_tags(self):
        db_mod.add_paper(_mk(tags=["ml"]))
        db_mod.add_paper(_mk(tags=["ml", "nlp"]))
        names = [t.name for t in db_mod.get_all_tags()]
        assert "ml" in names
        assert "nlp" in names