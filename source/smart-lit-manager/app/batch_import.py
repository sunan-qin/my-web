
import re
import os
from .models import Paper


def parse_bibtex_file(file_path):
    """Parse a .bib file and return a list of Paper objects."""
    papers = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    entries = re.split(r"@\w+\{", content)
    for entry in entries:
        entry = entry.strip()
        if not entry or entry.startswith("%"):
            continue
        fields = _parse_bibtex_fields(entry)
        if not fields:
            continue
        title = fields.get("title", "").strip("{}").strip()
        if not title:
            continue
        authors = fields.get("author", "").strip("{}").strip()
        authors = authors.replace(" and ", ";")
        paper_type = "Journal"
        entry_type = _get_entry_type(content, entry)
        if entry_type in ("inproceedings", "conference"):
            paper_type = "Conference"
        elif entry_type in ("book", "inbook"):
            paper_type = "Book"
        elif entry_type in ("phdthesis", "mastersthesis"):
            paper_type = "Thesis"
        elif entry_type in ("unpublished", "misc"):
            paper_type = "Preprint"
        papers.append(Paper(
            title=title,
            authors=authors,
            year=_int_or_none(fields.get("year", "").strip("{}")),
            journal=fields.get("journal", "").strip("{}").strip(),
            doi=fields.get("doi", "").strip("{}").strip(),
            abstract=fields.get("abstract", "").strip("{}").strip(),
            keywords=fields.get("keywords", "").strip("{}").strip(),
            paper_type=paper_type,
            publisher=fields.get("publisher", "").strip("{}").strip(),
            isbn=fields.get("isbn", "").strip("{}").strip(),
        ))
    return papers


def parse_ris_file(file_path):
    """Parse a .ris file and return a list of Paper objects."""
    papers = []
    current = {}
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("TY  - "):
                current = {"type": line[6:].strip()}
            elif line.startswith("ER  - "):
                if current:
                    p = _ris_to_paper(current)
                    if p:
                        papers.append(p)
                current = {}
            elif "  - " in line:
                key, val = line.split("  - ", 1)
                key = key.strip()
                val = val.strip()
                if key in current:
                    if isinstance(current[key], list):
                        current[key].append(val)
                    else:
                        current[key] = [current[key], val]
                else:
                    current[key] = val
    return papers


def _ris_to_paper(ris):
    title = ris.get("TI", ris.get("T1", ""))
    if not title:
        return None
    authors_raw = ris.get("AU", ris.get("A1", ""))
    if isinstance(authors_raw, list):
        authors = "; ".join(authors_raw)
    else:
        authors = authors_raw
    t = ris.get("type", "")
    paper_type = "Journal"
    if t in ("CONF", "CPAPER"): paper_type = "Conference"
    elif t in ("BOOK", "CHAPTER"): paper_type = "Book"
    elif t in ("THES", "DISS"): paper_type = "Thesis"
    elif t in ("RPRT", "PREP"): paper_type = "Preprint"
    return Paper(
        title=title, authors=authors,
        year=_int_or_none(ris.get("PY", ris.get("Y1", ""))[:4]),
        journal=ris.get("JO", ris.get("JF", ris.get("T2", ""))),
        doi=ris.get("DO", ""),
        abstract=ris.get("AB", ""),
        keywords=ris.get("KW", ""),
        paper_type=paper_type,
        publisher=ris.get("PB", ""),
        isbn=ris.get("SN", ""),
        issn=ris.get("SN", ""),
        start_page=ris.get("SP", ""),
        end_page=ris.get("EP", ""),
    )


def _parse_bibtex_fields(entry):
    fields = {}
    for match in re.finditer(r"(\w+)\s*=\s*\{([^}]*)\}", entry):
        key = match.group(1).lower()
        val = match.group(2).strip()
        fields[key] = val
    return fields


def _get_entry_type(content, entry):
    m = re.match(r"@(\w+)\s*\{", content)
    if m:
        return m.group(1).lower()
    return "article"


def _int_or_none(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
