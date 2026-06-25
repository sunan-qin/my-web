import os
import re
import fitz  # PyMuPDF
import logging
log = logging.getLogger(__name__)


def extract_metadata(file_path):
    """Extract metadata and text from a PDF with robust error handling."""
    result = {
        "title": "",
        "authors": "",
        "abstract": "",
        "year": None,
        "journal": "",
        "doi": "",
        "file_name": os.path.basename(file_path) if file_path else "",
        "text_content": ""
    }
    if not file_path or not os.path.exists(file_path):
        log.warning("PDF not found: %s", file_path)
        return result

    doc = None
    try:
        doc = fitz.open(file_path)
        log.info("Opened PDF (%d pages): %s", len(doc), os.path.basename(file_path))
    except Exception as exc:
        log.error("Failed to open PDF %s: %s", file_path, exc)
        return result
    meta = doc.metadata
    if meta:
        title = meta.get("title", "").strip()
        if title:
            result["title"] = title
        author = meta.get("author", "").strip()
        if author:
            result["authors"] = author
    full_text = ""
    for page_num in range(min(len(doc), 50)):
        page = doc[page_num]
        full_text += page.get_text() + "\n"
    doc.close()
    result["text_content"] = full_text
    if not result["title"]:
        result["title"] = _extract_title(full_text)
    doi = _extract_doi(full_text)
    if doi:
        result["doi"] = doi
    year = _extract_year(full_text)
    if year:
        result["year"] = year
    abstract = _extract_abstract(full_text)
    if abstract:
        result["abstract"] = abstract
    journal = _extract_journal(full_text)
    if journal:
        result["journal"] = journal
    return result


def _extract_title(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return ""
    for line in lines[:20]:
        line = line.strip()
        if len(line) > 20 and len(line) < 300:
            if not any(kw in line.lower() for kw in ["abstract", "introduction", "keywords", "doi:", "correspondence"]):
                clean = re.sub(r"\s+", " ", line)
                return clean
    return lines[0] if len(lines[0]) > 10 else ""


def _extract_doi(text):
    patterns = [
        r"10\.\d{4,}/[^\s,;)]+",
        r"doi[:\s]*10\.\d{4,}/[^\s,;)]+",
        r"DOI[:\s]*10\.\d{4,}/[^\s,;)]+",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            doi = match.group(0)
            doi = re.sub(r"^(doi|DOI)[:\s]*", "", doi)
            doi = doi.rstrip(".,;:)")
            return doi
    return ""


def _extract_year(text):
    years = re.findall(r"\b(19[5-9]\d|20[0-2]\d)\b", text)
    if years:
        return int(years[0])
    return None


def _extract_abstract(text):
    patterns = [
        r"Abstract[:\s]*\n*(.*?)(?=\n\s*(?:Introduction|Keywords|1\.\s|I\.\s|$))",
        r"ABSTRACT[:\s]*\n*(.*?)(?=\n\s*(?:INTRODUCTION|KEYWORDS|1\.\s|I\.\s|$))",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            abstract = match.group(1).strip()
            abstract = re.sub(r"\s+", " ", abstract)
            if len(abstract) > 50:
                return abstract
    return ""


def _extract_journal(text):
    patterns = [
        r"(?:Journal|Proceedings|Transactions|International Journal)[^.]*\.",
        r"Published in[:\s]+([^.\n]+)",
        r"arXiv[:\s]+([^\s]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return ""


def is_pdf(file_path):
    """Quick check whether a file looks like a valid PDF."""
    if not file_path or not os.path.isfile(file_path):
        return False
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
        return header == b"%PDF-"
    except Exception:
        return False
