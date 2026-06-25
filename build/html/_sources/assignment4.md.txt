# Assignment 4

## IntelliPaper — Intelligent Literature Management Tool

> **📥 Download Now**: IntelliPaper.exe 
<https://github.com/sunan-qin/my-web/blob/main/_static/downloads/IntelliPaper.exe>`_

---

## I. Background and Design

### 1.1 Software Overview

**IntelliPaper** (full name: Smart Literature Manager) is a cross-platform desktop literature management application designed for researchers. It helps users organize, search, analyze, annotate, and export academic papers, and provides optional AI-assisted features (abstract generation, keyword extraction, RAG Q&A, and conversational research assistant).

### 1.2 Design Motivation

In the academic research process, researchers often face the following pain points:

- **Papers scattered everywhere**: PDF files stored in different folders, lacking unified management.
- **Cumbersome metadata entry**: Manually entering titles, authors, abstracts, etc. is extremely time-consuming.
- **Difficult retrieval**: Unable to perform fuzzy searches on paper titles, abstracts, or full text within the file system.
- **Complex citation management**: Switching between different submission formats (BibTeX, RIS, APA, MLA, Chicago) is troublesome.
- **Lack of AI empowerment**: Existing tools (such as Zotero, Mendeley) lack deep integration with LLMs.

**Core Design Philosophy**: **"A desktop application that solves the entire literature management workflow"** — from PDF import → automatic metadata extraction → storage and indexing → search and discovery → notes and annotation → citation export → AI analysis, forming a complete closed loop.

### 1.3 Architecture Decisions

Adopting the classic **three-layer architecture**, modular separation of concerns:

`
┌──────────────────────────────────────────────────┐
│                   UI Layer (PyQt5)                │
│  MainWindow │ Dashboard │ PaperDetail │ Chat     │
│  ImportDialog │ TagDialog │ StatsDialog          │
├──────────────────────────────────────────────────┤
│               Business Logic Layer               │
│  SearchEngine │ SemanticSearch │ CitationExport  │
│  PDFExtractor │ CrossrefAPI │ RAG_QA │ HotFolder│
│  BatchImport │ ExportManager │ AIAssistant       │
├──────────────────────────────────────────────────┤
│               Data Layer (SQLite)                │
│  Models (Paper/Tag) │ Database (CRUD/FullText)  │
└──────────────────────────────────────────────────┘
`

**Key Architecture Decisions**:

| Decision | Choice | Reason |
|----------|--------|--------|
| GUI Framework | PyQt5 | Cross-platform, native look and feel, signal/slot asynchronous mechanism |
| Database | SQLite + WAL mode | Zero configuration, single file deployment, WAL enables concurrent reads, suitable for desktop applications |
| PDF Engine | PyMuPDF (fitz) | Pure Python high-speed bindings, metadata + full text extraction |
| AI Interface | Native HTTP (urllib) | No external SDK dependencies, supports DeepSeek/OpenAI/Ollama multiple models |
| Search Solution | Two-layer hybrid search | TF-IDF built-in search + optional sentence-transformers semantic search |
| Packaging | PyInstaller | Single-file .exe release, users do not need to install Python |

---

## II. Tech Stack

| Category | Technology |
|----------|------------|
| **Programming Language** | Python 3.9 |
| **GUI Framework** | PyQt5 5.15 |
| **PDF Processing** | PyMuPDF (fitz) |
| **Database** | SQLite3 (WAL mode, migration-style schema evolution) |
| **Image Processing** | Pillow 8.0 |
| **Semantic Search** | sentence-transformers (optional) |
| **AI Model Support** | DeepSeek-V3 / DeepSeek-R1 / OpenAI GPT-4o / GPT-3.5-turbo / Ollama |
| **Build Tool** | PyInstaller 6.20 |
| **Testing Framework** | pytest 8.4 |
| **Operating System** | Windows 11 (development) / Cross-platform (runtime) |
| **CPU** | AMD Ryzen 5 5600H |
| **AI Development Partner** | Codex CLI (based on OpenAI gpt-4o) |

---

## III. Feature List

### Core Features

| Category | Feature | Description |
|----------|---------|-------------|
| 📄 **Import** | Automatic PDF Extraction | Automatically identify title, author, abstract, DOI, year, journal after importing PDF |
| | Drag-and-Drop Import | Directly drag PDF files into the paper list |
| | BibTeX/RIS Import | Batch import .bib or .ris files |
| | Hot Folder Monitoring | Background thread monitors specified directory in real time, automatically imports new PDFs |
| | Title Search Import | Search paper metadata by title via OpenAlex API |
| 🔍 **Search** | Full-Text Search | Multi-field combined search across title/author/abstract/notes/DOI |
| | Keyword Boost | Title match +5 points, author match +3 points, improving relevance ranking |
| | Context Snippets | Search results show context text around matched words |
| | Semantic Search | Optional sentence-transformers embedding, supports "similar paper recommendations" |
| | Advanced Filtering | Filter by title/author/year range/paper type/tags/reading status |
| 🏷️ **Organization** | Tag Management | Color tags, complete CRUD management | | | Bulk tag assignment | |
| | Reading List | Unread/in-progress/read status tracking |
| | Favorites | Starred paper management |
| 📝 **Annotation** | Notes Editor | Rich text notes per paper, supports Markdown |
| | PDF Viewer | Built-in PDF viewer with page navigation |
| 📤 **Export** | Citation Export | Support for BibTeX, RIS, APA, MLA, Chicago formats |
| | JSON Export/Import | Full data (including notes and tags) serialized as JSON, supports re-import |
| | Full Archive | .zip complete archive containing PDFs + database + cache |
| 🤖 **AI Features** | Abstract Generation | One-click AI-generated paper abstract summary |
| | Keyword Extraction | Automatically extract 3-8 key terms from full text |
| | RAG Q&A | Conversational Q&A based on paper full text (Retrieval-Augmented Generation) |
| | AI Floating Chat | Always-on-top floating chat window, supports multi-turn conversation |
| | Multi-Model Support | Switch between DeepSeek, OpenAI GPT, Ollama local models |

### Dashboard Features

| Feature | Description |
|---------|-------------|
| **Statistics Cards** | Total papers, authors, tags, sources aggregated display |
| **Recent Papers** | Recently added/modified paper list |
| **Tag Cloud** | Tag usage frequency visualization |
| **Timeline** | Paper publication year distribution chart |
| **Category Distribution** | Paper type distribution pie chart |
| **AI Insights** | AI-generated reading suggestions and research trend analysis |

---

## IV. AI Development Process

### 4.1 Development Method

This project was developed entirely using **Codex CLI** (an AI coding agent based on OpenAI gpt-4o). The development process adopted a **conversational interaction** approach: describe requirements through natural language, and Codex CLI outputs complete, production-ready code.

**Development Model Comparison**:

| Approach | Applicable Scenarios | Efficiency |
|----------|----------------------|------------|
| **Full human development** | Small experiments, familiar projects | Low |
| **ChatGPT copy-paste** | Snippet generation, code explanation | Medium |
| **Cursor/Trae automatic completion** | Rapid iteration within existing code | Medium-High |
| **Codex CLI full-process development** | Complete project from scratch to completion | High |

### 4.2 Prompt Design Principles

Throughout the development process, the following prompt design patterns were followed:

1. **Hierarchical Breakdown**: Break requirements into independent, gradually deepening tasks. Example: "First, help me design an SQLite model for the paper management system" → "Then implement the CRUD operations of the model"
2. **Specify Tech Stack Explicitly**: "Use PyQt5 to implement the main window layout, the left side contains the paper list (QTreeView), and the right side is the detail panel (QStackedWidget)"
3. **Provide Context**: In each interaction, reference existing code or files to maintain coherence. Example: "In the existing paper_model.py, add a method to sort by publication year"
4. **Iterative Refinement**: First generate the basic version, then gradually add features through follow-up prompts. Example: "The current search function is too slow, please add full-text search index"
5. **Exception Handling**: Explicitly specify expected boundary conditions. Example: "Handle the case where PDF file parsing fails, return a friendly error message"

### 4.3 Task Decomposition Record (Partial)

| Round | Task Description | Lines of Code | Key Implementation |
|-------|------------------|---------------|-------------------|
| 1 | Identify requirements + architecture design | 0 | Requirements analysis document + architecture diagram |
| 2 | Data model + database layer | 156 | Paper/Tag/SearchResult models, CRUD operations |
| 3 | PDF extraction + metadata parsing | 89 | PyMuPDF-based meta + full text extraction, Crossref API query |
| 4 | Full-text search engine | 134 | TF-IDF ranking + keyword boost + context snippets |
| 5 | GUI main window + paper list | 203 | MainWindow layout, QTableView + custom model |
| 6 | Detail panel + notes | 112 | PaperDetail widget, rich text notes editing |
| 7 | Import dialog + BibTeX/RIS import | 97 | ImportDialog, bibtexparser parsing |
| 8 | Tag management + filtering | 68 | TagDialog, tag CRUD, filtered search |
| 9 | Citation export (4 formats) | 105 | CitationExport supporting BibTeX/RIS/APA/MLA/Chicago |
| 10 | Statistics dashboard | 136 | StatsDialog, charts + tag cloud + timeline |
| 11 | AI assistant integration | 178 | AIAssistant, multi-model switching, QThread async |
| 12 | RAG Q&A engine | 152 | Text chunking, retrieval, LLM generation pipeline |
| 13 | Hot folder + batch import | 64 | HotFolder watchdog, BatchImport parallel parsing |
| 14 | Export manager + JSON serialization | 88 | ExportManager .zip archive, JSON dump/load |
| 15 | Semantic search | 96 | sentence-transformers embedding + FAISS cosine similarity |
| 16 | Floating AI chat window | 121 | ChatWindow, always-on-top, streaming output |
| 17 | Dashboard page + startup splash | 89 | DashboardPage, welcome animation, cache warm-up |
| 18 | Bug fixes + edge case handling | 76 | Empty list, None value, encoding fallback protection |
| 19 | Testing: 36 unit tests + mocks | 342 | pytest coverage, fixture isolation, Mock database |
| 20 | EXE packaging + release | 28 | PyInstaller spec optimization, single-file 78.7 MB |

---

## V. Project Testing

### 5.1 Test Results

| Test Suite | Number of Tests | All Passing |
|------------|-----------------|-------------|
| `test_models.py` | 7 | ✅ |
| `test_database.py` | 18 | ✅ |
| `test_search_engine.py` | 11 | ✅ |
| **Total** | **36** | **✅ 100% Pass** |

### 5.2 Test Coverage Highlights

- **Model Tests**: Creating papers, tag association, metadata serialization
- **Database Tests**: CRUD operations, full-text search, tag operations, statistics queries, backup/restore
- **Search Engine Tests**: TF-IDF ranking, keyword boost, context snippets, edge case handling (empty query, special characters, stop words)

---


### Keyboard Shortcuts

| Shortcut | Function |
|----------|----------|
| Ctrl+O | Import paper |
| Ctrl+E | Export JSON |
| Ctrl+I | Import JSON |
| Ctrl+K | Set API key |
| Ctrl+D | Open PDF |
| Ctrl+, | Preferences |
| Ctrl+Q | Exit |

---

## VII. Project Structure

```
smart-lit-manager/
├── main.py                          # Entry point: splash screen + global exception hook + high DPI support
├── app/                             # Backend / Business Logic Layer
│   ├── models.py                    # Data models: Paper, Tag, SearchResult
│   ├── database.py                  # SQLite ORM (CRUD/search/tags/stats/backup/restore)
│   ├── pdf_extractor.py             # PDF metadata + full text extraction (PyMuPDF)
│   ├── search_engine.py             # Ranked search + context snippets
│   ├── semantic_search.py           # Hybrid semantic search (sentence-transformers/TF-IDF)
│   ├── citation_export.py           # Citation export: BibTeX, RIS, APA, MLA, Chicago
│   ├── ai_assistant.py              # AI assistant: multi-model + QThread async
│   ├── rag_qa.py                    # RAG Q&A: chunk segmentation + retrieval + LLM generation
│   ├── batch_import.py              # BibTeX/RIS file parsing
│   ├── crossref_api.py              # Crossref DOI + OpenAlex query
│   ├── hot_folder.py                # Hot folder monitoring (background thread)
│   ├── export_manager.py            # .zip full archive (includes PDFs + DB + cache)
│   └── logger.py                    # Structured logging + global exception hook
├── ui/                              # Frontend / GUI Layer (PyQt5)
│   ├── main_window.py               # Main window (menu/search/table/drag-drop/settings)
│   ├── paper_model.py               # QAbstractTableModel (sortable)
│   ├── paper_detail.py              # Detail panel (abstract/notes/AI/citation/PDF)
│   ├── import_dialog.py             # Import dialog (includes automatic extraction)
│   ├── tag_dialog.py                # Tag management (color picker)
│   ├── stats_dialog.py              # Statistics dashboard (charts/tag cloud/insights)
│   ├── dashboard_page.py            # Home dashboard (stats cards + recent papers)
│   └── chat_window.py               # Floating AI chat window (always on top)
├── tests/                           # Test suite (all 36 passing)
│   ├── test_models.py               # 7 tests
│   ├── test_database.py             # 18 tests
│   └── test_search_engine.py        # 11 tests
├── build_exe.py                     # PyInstaller build script
├── requirements.txt                 # Dependency declaration
└── README.md                        # Project documentation
```

---

## VIII. Conclusion and Outlook

### Project Summary

IntelliPaper successfully advanced AI-assisted development from "entertainment-style prompting" to "engineering-grade results." The project demonstrates a complete software engineering delivery — from architecture design to code implementation, from test coverage to executable packaging, all completed with an LLM (Codex CLI) as the primary development partner.

**Project Highlights**:
- ✅ [IntelliPaper.exe (78.7 MB)](./IntelliPaper.exe) standalone executable, zero external dependencies
- ✅ 36 comprehensive unit tests, all passing
- ✅ 5 AI model switching support (DeepSeek, OpenAI, Ollama)
- ✅ RAG Q&A engine + floating AI chat window
- ✅ Cross-platform runtime (Windows/macOS/Linux)
- ✅ Complete literature management full-process closed loop

### Possible Future Extensions

- **Web Service Version**: Flask/FastAPI backend + React frontend
- **Sync Service**: WebDAV/Nextcloud multi-device synchronization
- **Browser Extension**: Automatically capture paper metadata
- **Citation Network Graph**: Paper citation relationship visualization
- **More AI Capabilities**: Paper translation, research method suggestions, review comment generation

---

*Report generation date: June 15, 2026*
