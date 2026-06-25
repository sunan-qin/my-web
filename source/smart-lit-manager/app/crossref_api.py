
import json
import urllib.request
import urllib.error
import logging
import re

log = logging.getLogger(__name__)

CROSSREF_URL = "https://api.crossref.org/works/{doi}"
ARXIV_URL = "https://export.arxiv.org/api/query?id_list={arxiv_id}"
OPENALEX_URL = "https://api.openalex.org/works?search={query}"


def fetch_by_doi(doi):
    """Fetch paper metadata from Crossref API by DOI."""
    doi = doi.strip()
    if not doi:
        return None
    url = CROSSREF_URL.format(doi=doi)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "IntelliPaper/1.0 (mailto:student@example.com)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data.get("message", {})
            title = ""
            if msg.get("title"):
                title = msg["title"][0] if isinstance(msg["title"], list) else msg["title"]
            authors = "; ".join(
                f"{a.get('family', '')}, {''.join(g.get('given', '')[0] if g.get('given') else '')}"
                for a in msg.get("author", [])
            ) if msg.get("author") else ""
            abstract = msg.get("abstract", "")
            # Clean HTML tags from abstract
            if abstract:
                abstract = re.sub(r"<[^>]+>", "", abstract).strip()
            year = None
            if msg.get("published-print"):
                parts = msg["published-print"].get("date-parts", [[]])
                if parts[0]:
                    year = parts[0][0]
            elif msg.get("published-online"):
                parts = msg["published-online"].get("date-parts", [[]])
                if parts[0]:
                    year = parts[0][0]
            elif msg.get("created"):
                parts = msg["created"].get("date-parts", [[]])
                if parts[0]:
                    year = parts[0][0]
            journal = msg.get("container-title", [""])
            journal = journal[0] if isinstance(journal, list) else journal
            publisher = msg.get("publisher", "")
            paper_type = "Journal"
            if msg.get("type"):
                t = msg["type"]
                if "journal" in t: paper_type = "Journal"
                elif "proceedings" in t or "conference" in t: paper_type = "Conference"
                elif "book" in t: paper_type = "Book"
                elif "report" in t or "preprint" in t: paper_type = "Preprint"
                elif "thesis" in t: paper_type = "Thesis"
            return {
                "title": title, "authors": authors, "abstract": abstract,
                "year": year, "journal": journal or "",
                "doi": doi, "publisher": publisher or "", "paper_type": paper_type,
                "source": "Crossref",
            }
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError) as e:
        log.warning("Crossref lookup failed for %s: %s", doi, e)
    return None


def search_by_title(title_query):
    """Search OpenAlex for a paper by title, return best match metadata."""
    import urllib.parse
    q = urllib.parse.quote(title_query)
    url = OPENALEX_URL.format(query=q)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "IntelliPaper/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if results:
                best = results[0]
                doi = (best.get("doi") or "").replace("https://doi.org/", "")
                return {
                    "title": best.get("title", title_query),
                    "authors": "; ".join(
                        a.get("author", {}).get("display_name", "")
                        for a in best.get("authorships", [])
                    ),
                    "year": best.get("publication_year"),
                    "journal": (best.get("primary_location") or {}).get("source", {}).get("display_name", ""),
                    "doi": doi,
                    "abstract": best.get("abstract_inverted_index") and " ".join(best.get("abstract_inverted_index", {}).keys()) or "",
                    "paper_type": "Journal",
                    "publisher": "",
                    "source": "OpenAlex",
                }
    except Exception as e:
        log.warning("OpenAlex search failed: %s", e)
    return None
