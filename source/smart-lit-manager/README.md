# Smart Literature Manager

**An AI-Assisted Academic Paper Management Tool**

A desktop application for researchers to organize, search, analyze, and export academic papers. Built with Python, PyQt5, and PyMuPDF. Features optional AI-powered paper summarization via OpenAI.

---

## Features

| Category | Feature | Description |
|----------|---------|-------------|
| **📄 Import** | PDF Auto-Extraction | Import PDFs → auto-extract title, authors, abstract, DOI, year, journal |
| | Drag & Drop | Drag PDF files directly onto the paper table to import |
| | Quick Import | Skip the dialog by dropping files or using batch JSON import |
| **🏷️ Organize** | Tags | Color-coded tags with full CRUD management |
| | Tag Filter | Filter papers by any tag from the dropdown |
| | Sortable Table | Click column headers to sort by title, author, year, journal, or date |
| **🔍 Search** | Full-Text Search | Search titles, authors, abstracts, notes, and cached PDF text |
| | Debounced Search | 300ms debounce for smooth real-time searching |
| | Relevance Scoring | Title and author matches are boosted for better results |
| | Context Snippets | Search results show context around matching terms |
| **📝 Notes** | Per-Paper Notes | Add and auto-save personal notes to any paper |
| | Auto-Save | Notes are saved when switching papers or saving changes |
| **📖 Export** | BibTeX | One-click BibTeX citation export to clipboard |
| | RIS | RIS format export for reference managers |
| | JSON | Batch export/import all papers as JSON |
| **🔐 Backup** | Database Backup | Create timestamped backups of your entire library |
| | Database Restore | Restore from any backup file with safety confirmation |
| **🤖 AI** | Paper Summaries | Generate research summaries via OpenAI API (optional) |
| | Keyword Extraction | Extract key research terms from papers |
| | Tag Suggestions | AI-suggested tags based on paper content |
| **🖥️ UX** | Keyboard Shortcuts | Ctrl+O (import), Ctrl+E (export), Ctrl+I (import JSON), Ctrl+K (API key), Ctrl+D (open PDF), Ctrl+, (settings) |
| | PDF Viewer | Double-click or press Ctrl+D to open PDFs in system viewer |
| | Preferences | Settings dialog for API key configuration |
| | Exit Confirmation | Safety dialog when closing with papers loaded |
| | Statistics Dashboard | View paper counts by year, with/without abstracts, tag counts |
| | Error Handling | Structured logging + global exception hooks + user-friendly error messages |

## Quick Start

### Option 1: Pre-built Executable (Recommended)

1. Download **SmartLitManager.exe** (74.7 MB, standalone, no Python needed)
2. Double-click to run
3. Click **File → Import Paper** (or press **Ctrl+O**) to add your first PDF

### Option 2: Run from Source

`ash
# Requirements: Python 3.7+, PyQt5, PyMuPDF, Pillow
pip install PyQt5 PyMuPDF Pillow

# Launch
cd smart-lit-manager
python main.py
`

### Option 3: Run Tests

`ash
pip install pytest
cd smart-lit-manager
python -m pytest tests/ -v   # 36 tests covering models, database, search, citations
`

## Usage Guide

### Basic Workflow

1. **Import Papers** — File → Import Paper (or drag PDF files onto the paper list)
2. **Auto-Extract** — Click "Auto-Extract Metadata from PDF" to fill in paper details
3. **Tag & Categorize** — Add comma-separated tags during import or later
4. **Search & Browse** — Type in the search bar or filter by tag
5. **Take Notes** — Add notes in the detail panel (auto-saved)
6. **Export Citations** — Click "Export BibTeX" or "Export RIS"
7. **AI Summary** — Set your OpenAI API key in Tools → Preferences, then click "AI Summary"

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+O | Import Paper |
| Ctrl+E | Export Papers as JSON |
| Ctrl+I | Import Papers from JSON |
| Ctrl+K | Set OpenAI API Key |
| Ctrl+D | Open PDF (selected paper) |
| Ctrl+, | Preferences |
| Ctrl+Q | Exit |

### Backup & Restore

Your library is automatically stored at ~/.smart-lit-manager/library.db. Use:
- **File → Backup Database** to create a timestamped backup
- **File → Restore Database** to restore from a previous backup

You can also export/import all paper metadata as JSON for portability.

## Project Architecture

`
smart-lit-manager/
├── main.py                          # Entry point with splash + exception hook
├── app/                             # Backend / Business logic
│   ├── models.py                    # Data models: Paper, Tag, SearchResult
│   ├── database.py                  # SQLite ORM with full CRUD, search, stats, backup/restore
│   ├── pdf_extractor.py             # PDF metadata extraction via PyMuPDF
│   ├── citation_export.py           # BibTeX + RIS format generators
│   ├── search_engine.py             # Ranked search with context snippets
│   ├── ai_assistant.py              # OpenAI API client for summaries
│   └── logger.py                    # Structured logging + global exception hook
├── ui/                              # Frontend / GUI (PyQt5)
│   ├── main_window.py               # Main window: menus, toolbar, drag-drop, search, settings
│   ├── paper_model.py               # QAbstractTableModel for sortable paper table
│   ├── paper_detail.py              # Detail panel: abstract, notes, AI summary, PDF open
│   ├── import_dialog.py             # PDF import dialog with auto-extraction
│   ├── tag_dialog.py                # Tag CRUD with color picker
│   └── stats_dialog.py              # Library statistics dashboard
├── tests/                           # Test suite
│   ├── test_models.py               # Paper, Tag, SearchResult tests (7 tests)
│   ├── test_database.py             # Full CRUD, search, fulltext, stats, tags tests (18 tests)
│   └── test_search_engine.py        # Search + citation export tests (11 tests)
├── requirements.txt                 # Python dependencies
├── build_exe.py                     # PyInstaller build script
└── README.md                        # This file
`

## Test Coverage

36 unit tests in 3 test files — all passing:

- **	ests/test_models.py** — Paper formatting, citation generation, default values
- **	ests/test_database.py** — CRUD operations, search, fulltext, statistics, tags (with isolated temp DB per test)
- **	ests/test_search_engine.py** — Relevance scoring, snippet generation, BibTeX/RIS export

Run with: python -m pytest tests/ -v

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.9 |
| GUI Framework | PyQt5 |
| PDF Processing | PyMuPDF (fitz) v1.26.5 |
| Database | SQLite3 (WAL mode) |
| Image Processing | Pillow |
| AI Integration | OpenAI API (optional, gpt-3.5-turbo) |
| Packaging | PyInstaller v6.20 |
| Testing | pytest |

## How AI (Codex CLI) Helped Build This

This project was developed with **Codex CLI** as the primary development partner. Key contributions:

### Architecture & Planning
- Proposed the modular 3-layer architecture (data models → business logic → GUI)
- Recommended SQLite with WAL mode, PyQt5 for cross-platform GUI, and PyMuPDF for PDF processing
- Designed the normalized database schema with proper foreign keys and indexes

### Database Layer
- Implemented full SQLite ORM with CRUD, full-text search, tag management, and statistics
- Added backup/restore, JSON export/import functions
- Fixed SQL syntax issues and path-variable scoping during test setup

### PDF Extraction
- Built regex patterns for DOI, year, abstract, and journal extraction
- Added is_pdf() validator and graceful error handling for corrupt files
- Chose page-limited extraction (first 50 pages) for performance

### Search Engine
- Implemented relevance scoring with title/author boosting
- Built context-aware snippet extraction around the first matching term
- Achieved 7/7 search tests passing

### GUI Development
- Built complete PyQt5 interface: sortable table, split-pane layout, debounced search (300ms)
- Added drag-drop PDF import, double-click PDF open, and keyboard shortcuts (Ctrl+O/E/I/K/D/,)
- Implemented settings dialog with API key configuration
- Added database backup/restore dialogs with safety confirmations
- Added splash screen and global exception hook for startup robustness

### Bug Fixes & Packaging
- Fixed relative import issue (rom ..app → rom app) for PyInstaller compatibility
- Fixed PyQt5 enum error (QTableView.SingleRow → QAbstractItemView.SingleSelection)
- Fixed f-string quote escaping in PowerShell-generated source files
- Configured PyInstaller with correct hidden imports for 74.7 MB standalone .exe

### Testing
- Wrote 36 unit tests covering all backend modules
- Used temp-directory DB isolation for database tests
- All tests pass with pytest

## License

Academic project — developed as an exercise in AI-assisted software engineering.