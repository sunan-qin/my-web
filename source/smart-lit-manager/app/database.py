import sqlite3
import os
from datetime import datetime
from typing import List, Optional
from .models import Paper, Tag

def _get_db_dir():
    primary = os.path.join(os.path.expanduser("~"), ".smart-lit-manager")
    try:
        os.makedirs(primary, exist_ok=True)
        with open(os.path.join(primary, ".wtest"), "w"): pass
        os.remove(os.path.join(primary, ".wtest"))
        return primary
    except (OSError, PermissionError):
        fb = os.path.join(os.environ.get("TEMP", "/tmp"), "smart-lit-manager")
        os.makedirs(fb, exist_ok=True)
        return fb

DB_DIR = _get_db_dir()
DB_PATH = os.path.join(DB_DIR, "library.db")


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    sql = (
        "CREATE TABLE IF NOT EXISTS papers ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  title TEXT NOT NULL DEFAULT '',"
        "  authors TEXT NOT NULL DEFAULT '',"
        "  abstract TEXT NOT NULL DEFAULT '',"
        "  year INTEGER,"
        "  journal TEXT NOT NULL DEFAULT '',"
        "  doi TEXT NOT NULL DEFAULT '',"
        "  file_path TEXT NOT NULL DEFAULT '',"
        "  file_name TEXT NOT NULL DEFAULT '',"
        "  added_date TEXT NOT NULL DEFAULT '',"
        "  notes TEXT NOT NULL DEFAULT '',"
        "  has_fulltext INTEGER NOT NULL DEFAULT 0"
        ");"
        "CREATE TABLE IF NOT EXISTS tags ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  name TEXT NOT NULL UNIQUE,"
        "  color TEXT NOT NULL DEFAULT '#5B9BD5'"
        ");"
        "CREATE TABLE IF NOT EXISTS paper_tags ("
        "  paper_id INTEGER NOT NULL,"
        "  tag_id INTEGER NOT NULL,"
        "  PRIMARY KEY (paper_id, tag_id),"
        "  FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,"
        "  FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE"
        ");"
        "CREATE TABLE IF NOT EXISTS fulltext_cache ("
        "  paper_id INTEGER PRIMARY KEY,"
        "  text_content TEXT NOT NULL,"
        "  FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE"
        ");"
        "CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title);"
        "CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);"
        "CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);"
    )
    conn.executescript(sql)

    # Migrate: add reading_status and rating columns (v2 schema)
    try:
        conn.execute("ALTER TABLE papers ADD COLUMN reading_status TEXT NOT NULL DEFAULT 'Unread'")
    except sqlite3.OperationalError:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE papers ADD COLUMN rating INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    # v3 schema: paper_type, keywords, issn, isbn, start_page, end_page, publisher
    for col in [
        "paper_type TEXT NOT NULL DEFAULT 'Journal'",
        "keywords TEXT NOT NULL DEFAULT ''",
        "issn TEXT NOT NULL DEFAULT ''",
        "isbn TEXT NOT NULL DEFAULT ''",
        "start_page TEXT NOT NULL DEFAULT ''",
        "end_page TEXT NOT NULL DEFAULT ''",
        "publisher TEXT NOT NULL DEFAULT ''",
    ]:
        try:
            conn.execute(f"ALTER TABLE papers ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


def add_paper(paper):
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute(
        "INSERT INTO papers (title, authors, abstract, year, journal, doi, file_path, file_name, added_date, notes, has_fulltext, reading_status, rating, paper_type, keywords, issn, isbn, start_page, end_page, publisher) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (paper.title, paper.authors, paper.abstract, paper.year,
         paper.journal, paper.doi, paper.file_path, paper.file_name,
         now, paper.notes, 1 if paper.has_fulltext else 0,
         paper.reading_status, paper.rating, paper.paper_type,
         paper.keywords, paper.issn, paper.isbn, paper.start_page,
         paper.end_page, paper.publisher)
    )
    paper_id = cursor.lastrowid
    for tag_name in paper.tags:
        _ensure_tag(conn, paper_id, tag_name)
    conn.commit()
    conn.close()
    return paper_id


def _ensure_tag(conn, paper_id, tag_name):
    cursor = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
    row = cursor.fetchone()
    if row:
        tag_id = row["id"]
    else:
        cursor = conn.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
        tag_id = cursor.lastrowid
    conn.execute("INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)", (paper_id, tag_id))


def update_paper(paper):
    conn = get_connection()
    conn.execute(
        "UPDATE papers SET title=?, authors=?, abstract=?, year=?, journal=?, "
        "doi=?, file_path=?, file_name=?, notes=?, has_fulltext=?, "
        "reading_status=?, rating=?, paper_type=?, keywords=?, "
        "issn=?, isbn=?, start_page=?, end_page=?, publisher=? "
        "WHERE id=?",
        (paper.title, paper.authors, paper.abstract, paper.year,
         paper.journal, paper.doi, paper.file_path, paper.file_name,
         paper.notes, 1 if paper.has_fulltext else 0,
         paper.reading_status, paper.rating, paper.paper_type,
         paper.keywords, paper.issn, paper.isbn, paper.start_page,
         paper.end_page, paper.publisher, paper.id)
    )
    conn.execute("DELETE FROM paper_tags WHERE paper_id=?", (paper.id,))
    for tag_name in paper.tags:
        _ensure_tag(conn, paper.id, tag_name)
    conn.commit()
    conn.close()


def delete_paper(paper_id):
    conn = get_connection()
    conn.execute("DELETE FROM fulltext_cache WHERE paper_id=?", (paper_id,))
    conn.execute("DELETE FROM paper_tags WHERE paper_id=?", (paper_id,))
    conn.execute("DELETE FROM papers WHERE id=?", (paper_id,))
    conn.commit()
    conn.close()


def get_paper(paper_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        conn.close()
        return None
    paper = _row_to_paper(row, conn)
    conn.close()
    return paper


def get_all_papers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM papers ORDER BY added_date DESC").fetchall()
    papers = [_row_to_paper(r, conn) for r in rows]
    conn.close()
    return papers


def get_all_tags():
    conn = get_connection()
    rows = conn.execute(
        "SELECT t.*, COUNT(pt.paper_id) as paper_count "
        "FROM tags t LEFT JOIN paper_tags pt ON t.id = pt.tag_id "
        "GROUP BY t.id ORDER BY t.name"
    ).fetchall()
    tags = []
    for r in rows:
        tags.append(Tag(id=r["id"], name=r["name"], color=r["color"], paper_count=r["paper_count"]))
    conn.close()
    return tags


def delete_tag(tag_id):
    conn = get_connection()
    conn.execute("DELETE FROM paper_tags WHERE tag_id=?", (tag_id,))
    conn.execute("DELETE FROM tags WHERE id=?", (tag_id,))
    conn.commit()
    conn.close()


def update_tag_color(tag_id, color):
    conn = get_connection()
    conn.execute("UPDATE tags SET color=? WHERE id=?", (color, tag_id))
    conn.commit()
    conn.close()


def _row_to_paper(row, conn=None):
    paper = Paper(
        id=row["id"], title=row["title"], authors=row["authors"],
        abstract=row["abstract"], year=row["year"], journal=row["journal"],
        doi=row["doi"], file_path=row["file_path"], file_name=row["file_name"],
        added_date=row["added_date"], notes=row["notes"],
        has_fulltext=bool(row["has_fulltext"]),
        reading_status=row["reading_status"] if "reading_status" in row.keys() else "Unread",
        rating=row["rating"] if "rating" in row.keys() else 0,
        paper_type=row["paper_type"] if "paper_type" in row.keys() else "Journal",
        keywords=row["keywords"] if "keywords" in row.keys() else "",
        issn=row["issn"] if "issn" in row.keys() else "",
        isbn=row["isbn"] if "isbn" in row.keys() else "",
        start_page=row["start_page"] if "start_page" in row.keys() else "",
        end_page=row["end_page"] if "end_page" in row.keys() else "",
        publisher=row["publisher"] if "publisher" in row.keys() else "",
    )
    if conn:
        tag_rows = conn.execute(
            "SELECT t.name FROM tags t "
            "JOIN paper_tags pt ON t.id = pt.tag_id "
            "WHERE pt.paper_id=? ORDER BY t.name",
            (row["id"],)
        ).fetchall()
        paper.tags = [r["name"] for r in tag_rows]
    return paper


def save_fulltext(paper_id, text):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO fulltext_cache (paper_id, text_content) VALUES (?, ?)", (paper_id, text))
    conn.execute("UPDATE papers SET has_fulltext=1 WHERE id=?", (paper_id,))
    conn.commit()
    conn.close()


def get_fulltext(paper_id):
    conn = get_connection()
    row = conn.execute("SELECT text_content FROM fulltext_cache WHERE paper_id=?", (paper_id,)).fetchone()
    conn.close()
    return row["text_content"] if row else None


def search_papers(query):
    conn = get_connection()
    like = f"%{query}%"
    rows = conn.execute(
        "SELECT DISTINCT p.* FROM papers p "
        "LEFT JOIN fulltext_cache fc ON p.id = fc.paper_id "
        "WHERE p.title LIKE ? OR p.authors LIKE ? OR p.abstract LIKE ? "
        "OR p.journal LIKE ? OR p.doi LIKE ? OR p.notes LIKE ? OR p.keywords LIKE ? OR p.publisher LIKE ? "
        "OR fc.text_content LIKE ? "
        "ORDER BY p.added_date DESC",
        (like, like, like, like, like, like, like, like, like)
    ).fetchall()
    papers = [_row_to_paper(r, conn) for r in rows]
    conn.close()
    return papers


def search_papers_by_tag(tag_name):
    conn = get_connection()
    rows = conn.execute(
        "SELECT p.* FROM papers p "
        "JOIN paper_tags pt ON p.id = pt.paper_id "
        "JOIN tags t ON t.id = pt.tag_id "
        "WHERE t.name = ? "
        "ORDER BY p.added_date DESC",
        (tag_name,)
    ).fetchall()
    papers = [_row_to_paper(r, conn) for r in rows]
    conn.close()
    return papers


def get_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) as c FROM papers").fetchone()["c"]
    with_ab = conn.execute("SELECT COUNT(*) as c FROM papers WHERE abstract != ''").fetchone()["c"]
    with_ft = conn.execute("SELECT COUNT(*) as c FROM papers WHERE has_fulltext=1").fetchone()["c"]
    tag_c = conn.execute("SELECT COUNT(*) as c FROM tags").fetchone()["c"]

    # Status breakdown
    unread = conn.execute("SELECT COUNT(*) as c FROM papers WHERE reading_status='Unread'").fetchone()["c"]
    toread = conn.execute("SELECT COUNT(*) as c FROM papers WHERE reading_status='To Read'").fetchone()["c"]
    inprog = conn.execute("SELECT COUNT(*) as c FROM papers WHERE reading_status='In Progress'").fetchone()["c"]
    read = conn.execute("SELECT COUNT(*) as c FROM papers WHERE reading_status='Read'").fetchone()["c"]

    year_rows = conn.execute(
        "SELECT year, COUNT(*) as c FROM papers WHERE year IS NOT NULL GROUP BY year ORDER BY year DESC LIMIT 10"
    ).fetchall()
    years = {r["year"]: r["c"] for r in year_rows}
    conn.close()
    return {
        "total": total, "with_abstract": with_ab,
        "with_fulltext": with_ft, "tag_count": tag_c,
        "years": years,
        "status_unread": unread, "status_toread": toread,
        "status_inprog": inprog, "status_read": read,
    }


def get_recent_papers(limit=5):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM papers ORDER BY added_date DESC LIMIT ?", (limit,)
    ).fetchall()
    papers = [_row_to_paper(r, conn) for r in rows]
    conn.close()
    return papers


def get_papers_by_status(status, limit=None):
    conn = get_connection()
    query = "SELECT * FROM papers WHERE reading_status=? ORDER BY added_date DESC"
    params = [status]
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    rows = conn.execute(query, params).fetchall()
    papers = [_row_to_paper(r, conn) for r in rows]
    conn.close()
    return papers


# ── Backup / Restore ──────────────────────────────────────────

def backup_database(target_path=None):
    import shutil
    from datetime import datetime as dt
    if target_path is None:
        ts = dt.now().strftime("%Y%m%d_%H%M%S")
        target_path = os.path.join(DB_DIR, f"library_backup_{ts}.db")
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    conn = get_connection()
    conn.execute("PRAGMA wal_checkpoint(FULL)")
    conn.close()
    shutil.copy2(DB_PATH, target_path)
    return target_path


def restore_database(source_path):
    import shutil
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Backup not found at {source_path}")
    if os.path.exists(DB_PATH):
        os.replace(DB_PATH, DB_PATH + ".old")
    shutil.copy2(source_path, DB_PATH)
    return True


def list_backups():
    import glob
    pattern = os.path.join(DB_DIR, "library_backup_*.db")
    results = []
    for path in sorted(glob.glob(pattern), reverse=True):
        size = os.path.getsize(path)
        name = os.path.basename(path)
        results.append((name, path, size))
    return results


def export_papers_to_json(file_path):
    import json
    papers = get_all_papers()
    data = []
    for p in papers:
        data.append({
            "id": p.id, "title": p.title, "authors": p.authors,
            "abstract": p.abstract, "year": p.year, "journal": p.journal,
            "doi": p.doi, "file_path": p.file_path, "file_name": p.file_name,
            "notes": p.notes, "tags": p.tags,
            "reading_status": p.reading_status, "rating": p.rating,
            "paper_type": p.paper_type, "keywords": p.keywords,
            "issn": p.issn, "isbn": p.isbn,
            "start_page": p.start_page, "end_page": p.end_page,
            "publisher": p.publisher,
        })
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return len(data)


def import_papers_from_json(file_path):
    import json
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    count = 0
    for item in data:
        paper = Paper(
            title=item.get("title", ""),
            authors=item.get("authors", ""),
            abstract=item.get("abstract", ""),
            year=item.get("year"),
            journal=item.get("journal", ""),
            doi=item.get("doi", ""),
            file_path=item.get("file_path", ""),
            file_name=item.get("file_name", ""),
            notes=item.get("notes", ""),
            tags=item.get("tags", []),
            reading_status=item.get("reading_status", "Unread"),
            rating=item.get("rating", 0),
            paper_type=item.get("paper_type", "Journal"),
            keywords=item.get("keywords", ""),
            issn=item.get("issn", ""),
            isbn=item.get("isbn", ""),
            start_page=item.get("start_page", ""),
            end_page=item.get("end_page", ""),
            publisher=item.get("publisher", ""),
        )
        add_paper(paper)
        count += 1
    return count

# ── Dedup & fuzzy matching ──────────────────────────────────

def find_duplicate(title, doi):
    """Check if a paper with the same DOI or similar title exists."""
    conn = get_connection()
    # Exact DOI match
    if doi:
        row = conn.execute("SELECT id, title FROM papers WHERE doi=? AND doi!=''", (doi,)).fetchone()
        if row:
            conn.close()
            return ("doi", row["id"], row["title"])
    # Fuzzy title match (Levenshtein > 92%)
    if title:
        title_clean = title.lower().strip()
        rows = conn.execute("SELECT id, title FROM papers").fetchall()
        for r in rows:
            existing = r["title"].lower().strip()
            if _levenshtein_ratio(title_clean, existing) > 0.92:
                conn.close()
                return ("title", r["id"], r["title"])
    conn.close()
    return None


def _levenshtein_ratio(s1, s2):
    """Compute Levenshtein similarity ratio between two strings."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = temp
    max_len = max(m, n)
    return (max_len - dp[n]) / max_len if max_len else 1.0


def search_papers_advanced(title=None, authors=None, year_from=None, year_to=None,
                            paper_type=None, tags=None, tag_mode="any",
                            status=None, query=None):
    """Advanced multi-dimensional filter search."""
    conn = get_connection()
    conditions = []
    params = []

    if query:
        like = f"%{query}%"
        conditions.append("(p.title LIKE ? OR p.authors LIKE ? OR p.abstract LIKE ? "
                         "OR p.keywords LIKE ? OR p.doi LIKE ?)")
        params.extend([like, like, like, like, like])

    if title:
        conditions.append("p.title LIKE ?")
        params.append(f"%{title}%")
    if authors:
        conditions.append("p.authors LIKE ?")
        params.append(f"%{authors}%")
    if year_from:
        conditions.append("p.year >= ?")
        params.append(year_from)
    if year_to:
        conditions.append("p.year <= ?")
        params.append(year_to)
    if paper_type:
        conditions.append("p.paper_type = ?")
        params.append(paper_type)
    if status:
        conditions.append("p.reading_status = ?")
        params.append(status)
    if tags:
        if tag_mode == "all":
            for tag in tags:
                conditions.append("p.id IN (SELECT pt.paper_id FROM paper_tags pt "
                                 "JOIN tags t ON t.id=pt.tag_id WHERE t.name=?)")
                params.append(tag)
        else:
            placeholders = ",".join("?" for _ in tags)
            conditions.append(f"p.id IN (SELECT pt.paper_id FROM paper_tags pt "
                             f"JOIN tags t ON t.id=pt.tag_id WHERE t.name IN ({placeholders}))")
            params.extend(tags)

    where = " AND ".join(conditions) if conditions else "1=1"
    rows = conn.execute(
        f"SELECT DISTINCT p.* FROM papers p WHERE {where} ORDER BY p.added_date DESC",
        params
    ).fetchall()
    papers = [_row_to_paper(r, conn) for r in rows]
    conn.close()
    return papers
