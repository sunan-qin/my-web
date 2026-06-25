from dataclasses import dataclass, field
from typing import List, Optional

READING_STATUS = ["Unread", "To Read", "In Progress", "Read"]


PAPER_TYPES = ["Journal", "Conference", "Preprint", "Book", "Thesis", "Other"]


@dataclass
class Paper:
    id: Optional[int] = None
    title: str = ""
    authors: str = ""
    abstract: str = ""
    year: Optional[int] = None
    journal: str = ""
    doi: str = ""
    file_path: str = ""
    file_name: str = ""
    added_date: str = ""
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    has_fulltext: bool = False
    reading_status: str = "Unread"
    rating: int = 0
    paper_type: str = "Journal"
    keywords: str = ""
    issn: str = ""
    isbn: str = ""
    start_page: str = ""
    end_page: str = ""
    publisher: str = "" 

    def formatted_authors(self) -> str:
        if not self.authors:
            return "Unknown Authors"
        parts = [a.strip() for a in self.authors.replace(" and ", ";").split(";")]
        formatted = []
        for p in parts:
            if "," in p:
                formatted.append(p.strip())
            else:
                tokens = p.strip().split()
                if len(tokens) >= 2:
                    formatted.append(f"{tokens[-1]}, {' '.join(tokens[:-1])}")
                else:
                    formatted.append(p.strip())
        return "; ".join(formatted)

    def short_citation(self) -> str:
        first_author = self.authors.split(";")[0].strip() if self.authors else "Unknown"
        if "," in first_author:
            last_name = first_author.split(",")[0].strip()
        else:
            tokens = first_author.split()
            last_name = tokens[-1] if tokens else "Unknown"
        year_str = f" ({self.year})" if self.year else ""
        title_short = (self.title[:60] + "...") if len(self.title) > 60 else self.title
        return f"{last_name}{year_str} -- {title_short}"

    def status_emoji(self) -> str:
        mapping = {
            "Unread": "\U0001F4D5",       # closed book
            "To Read": "\U0001F4D6",      # open book
            "In Progress": "\U0001F4DD",  # memo
            "Read": "\u2705",             # check mark
        }
        return mapping.get(self.reading_status, "\U0001F4D5")


@dataclass
class Tag:
    id: Optional[int] = None
    name: str = ""
    color: str = "#5B9BD5"
    paper_count: int = 0


@dataclass
class SearchResult:
    paper: Paper
    snippet: str = ""
    score: float = 0.0