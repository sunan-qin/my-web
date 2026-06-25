from typing import List
from .models import Paper


def to_bibtex(paper, cite_key=None):
    """Generate BibTeX entry for a paper."""
    if not cite_key:
        first_author = paper.authors.split(";")[0].strip() if paper.authors else "Unknown"
        if "," in first_author:
            last_name = first_author.split(",")[0].strip()
        else:
            tokens = first_author.split()
            last_name = tokens[-1] if tokens else "Unknown"
        year_str = str(paper.year) if paper.year else "0000"
        cite_key = f"{last_name}{year_str}"

    lines = [f"@article{{{cite_key},"]
    lines.append(f"  title = {{{paper.title}}},")
    if paper.authors:
        authors = paper.authors.replace(";", " and ")
        lines.append(f"  author = {{{authors}}},")
    if paper.journal:
        lines.append(f"  journal = {{{paper.journal}}},")
    if paper.year:
        lines.append(f"  year = {{{paper.year}}},")
    if paper.doi:
        lines.append(f"  doi = {{{paper.doi}}},")
    if paper.abstract:
        lines.append(f"  abstract = {{{paper.abstract}}},")
    lines.append("}")
    return "\n".join(lines)


def to_bibtex_many(papers):
    """Generate BibTeX for multiple papers."""
    entries = []
    for i, paper in enumerate(papers):
        cite_key = None
        if paper.authors:
            first_author = paper.authors.split(";")[0].strip()
            if "," in first_author:
                last_name = first_author.split(",")[0].strip()
            else:
                tokens = first_author.split()
                last_name = tokens[-1] if tokens else "Unknown"
            year_str = str(paper.year) if paper.year else "0000"
            cite_key = f"{last_name}{year_str}_{i + 1}"
        entries.append(to_bibtex(paper, cite_key))
    return "\n\n".join(entries)


def to_ris(paper):
    """Generate RIS format citation."""
    lines = ["TY  - JOUR"]
    if paper.authors:
        for author in paper.authors.split(";"):
            lines.append(f"AU  - {author.strip()}")
    if paper.title:
        lines.append(f"TI  - {paper.title}")
    if paper.journal:
        lines.append(f"JO  - {paper.journal}")
    if paper.year:
        lines.append(f"PY  - {paper.year}")
    if paper.doi:
        lines.append(f"DO  - {paper.doi}")
    if paper.abstract:
        lines.append(f"AB  - {paper.abstract}")
    lines.append("ER  - ")
    return "\n".join(lines)

def to_apa(paper):
    """Generate APA 7th edition citation."""
    authors_part = ""
    if paper.authors:
        author_list = [a.strip() for a in paper.authors.replace(" and ", ";").split(";")]
        formatted = []
        for a in author_list:
            if "," in a:
                formatted.append(a.strip())
            else:
                parts = a.strip().split()
                if len(parts) >= 2:
                    last = parts[-1]
                    initials = "".join(p[0] + "." for p in parts[:-1])
                    formatted.append(f"{last}, {initials}")
                else:
                    formatted.append(a.strip())
        if len(formatted) == 1:
            authors_part = formatted[0]
        elif len(formatted) == 2:
            authors_part = f"{formatted[0]} & {formatted[1]}"
        elif len(formatted) > 2:
            authors_part = f"{formatted[0]}, ..., {formatted[-1]}" if len(formatted) > 7 else ", ".join(formatted[:-1]) + f", & {formatted[-1]}"
    else:
        authors_part = "Unknown"

    year_str = f"{paper.year}" if paper.year else "n.d."
    title_str = paper.title if paper.title else "Untitled"
    journal_str = f" *{paper.journal}*," if paper.journal else ""
    doi_str = f" https://doi.org/{paper.doi}" if paper.doi else ""
    return f"{authors_part} ({year_str}). {title_str}.{journal_str}{doi_str}"


def to_mla(paper):
    """Generate MLA 9th edition citation."""
    authors_part = ""
    if paper.authors:
        author_list = [a.strip() for a in paper.authors.replace(" and ", ";").split(";")]
        formatted = []
        for a in author_list:
            if "," in a:
                formatted.append(a.strip())
            else:
                parts = a.strip().split()
                if len(parts) >= 2:
                    formatted.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
                else:
                    formatted.append(a.strip())
        if len(formatted) == 1:
            authors_part = formatted[0]
        elif len(formatted) == 2:
            authors_part = f"{formatted[0]} and {formatted[1]}"
        else:
            authors_part = f"{formatted[0]}, et al."
    else:
        authors_part = "Unknown"

    title_str = f"\"{paper.title}.\"" if paper.title else "\"Untitled.\""
    journal_str = f" *{paper.journal}*," if paper.journal else ""
    year_str = f" {paper.year}," if paper.year else " n.d.,"
    doi_str = f" doi:{paper.doi}." if paper.doi else "."
    return f"{authors_part}. {title_str}{journal_str}{year_str}{doi_str}"


def to_chicago(paper):
    """Generate Chicago Manual of Style citation."""
    authors_part = ""
    if paper.authors:
        author_list = [a.strip() for a in paper.authors.replace(" and ", ";").split(";")]
        formatted = []
        for a in author_list:
            if "," in a:
                formatted.append(a.strip())
            else:
                parts = a.strip().split()
                if len(parts) >= 2:
                    formatted.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
                else:
                    formatted.append(a.strip())
        if len(formatted) <= 3:
            authors_part = ", ".join(formatted)
        else:
            authors_part = f"{formatted[0]} et al."
    else:
        authors_part = "Unknown"

    title_str = f"\"{paper.title}.\"" if paper.title else "\"Untitled.\""
    journal_str = f" *{paper.journal}*" if paper.journal else ""
    year_str = f" ({paper.year})" if paper.year else " (n.d.)"
    doi_str = f" https://doi.org/{paper.doi}." if paper.doi else "."
    return f"{authors_part}. {title_str}{journal_str}{year_str}{doi_str}"
