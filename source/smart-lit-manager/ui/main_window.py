import os
import json
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLineEdit, QTableView, QHeaderView, QMessageBox,
    QStatusBar, QLabel, QComboBox, QMenuBar, QAction, QFileDialog,
    QInputDialog, QToolBar, QApplication, QStyle, QFrame, QAbstractItemView,
    QStackedWidget, QGroupBox, QDialog, QDialogButtonBox, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QSortFilterProxyModel, QTimer, QSize
from PyQt5.QtGui import QIcon, QKeySequence, QFont

from app.database import (
    init_db, add_paper, update_paper, delete_paper, get_paper,
    get_all_papers, get_all_tags, delete_tag, update_tag_color,
    search_papers, search_papers_by_tag, get_stats, save_fulltext,
    get_fulltext, get_recent_papers, get_papers_by_status
)
from app.models import Paper, Tag, READING_STATUS
from app.search_engine import search_with_snippets
from app.ai_assistant import AIAssistant
from app.logger import logger
from app.database import backup_database, restore_database, list_backups, find_duplicate, search_papers_advanced, get_papers_by_status
from app.database import export_papers_to_json, import_papers_from_json
from ui.paper_model import PaperTableModel
from ui.import_dialog import ImportDialog
from ui.tag_dialog import TagDialog
from ui.stats_dialog import EnhancedStatsDialog as StatsDialog
from ui.paper_detail import PaperDetailWidget
from ui.dashboard_page import DashboardPage
from app.semantic_search import get_search_engine
from app.hot_folder import HotFolderMonitor
from app.export_manager import export_full_zip, import_full_zip
from app.rag_qa import answer_question
from ui.chat_window import FloatingChatWindow
from ui.stats_dialog import EnhancedStatsDialog
from app.database import search_papers_advanced

def _get_cfg_dir():
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

CONFIG_DIR = _get_cfg_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

THEMES = {
    "light": {
        "bg": "#FFFFFF", "bg2": "#F5F7FA", "surface": "#FFFFFF",
        "primary": "#2563EB", "primary_hover": "#1D4ED8",
        "primary_text": "#FFFFFF", "text": "#1E293B",
        "text_secondary": "#64748B", "border": "#E2E8F0",
        "hover": "#F1F5F9", "selection": "#DBEAFE",
        "selection_text": "#1E3A5F", "header_bg": "#F8FAFC",
        "status_unread": "#94A3B8", "status_toread": "#F59E0B",
        "status_progress": "#3B82F6", "status_read": "#10B981",
    },
    "dark": {
        "bg": "#0F172A", "bg2": "#1E293B", "surface": "#1E293B",
        "primary": "#3B82F6", "primary_hover": "#2563ED",
        "primary_text": "#FFFFFF", "text": "#F1F5F9",
        "text_secondary": "#94A3B8", "border": "#334155",
        "hover": "#334155", "selection": "#1E3A5F",
        "selection_text": "#DBEAFE", "header_bg": "#1E293B",
        "status_unread": "#64748B", "status_toread": "#FBBF24",
        "status_progress": "#60A5FA", "status_read": "#34D399",
    }
}


class DragDropTableView(QTableView):
    """QTableView with drag-drop support for PDF files."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        main_win = self.window() if self.window() else None
        if main_win and hasattr(main_win, "_import_pdf_file"):
            for url in event.mimeData().urls():
                fpath = url.toLocalFile()
                if fpath.lower().endswith(".pdf") and os.path.isfile(fpath):
                    main_win._import_pdf_file(fpath)
                    event.acceptProposedAction()



class SmartLitManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self._config = self._load_config()
        self._theme_name = self._config.get("theme", "light")
        self._theme = THEMES.get(self._theme_name, THEMES["light"])
        self.setWindowTitle("Smart Literature Manager")
        self.setMinimumSize(1150, 750)
        self.resize(1300, 800)
        self._apply_theme()
        init_db()
        self._papers = []
        self._search_mode = "all"
        self._ai = AIAssistant(self._config.get("openai_key", ""), model_name=self._config.get("ai_model", "DeepSeek-V3"))
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._load_papers()
        self._semantic = get_search_engine()
        self._chat_window = FloatingChatWindow(self._ai, self)
        self._chat_window.set_ai_assistant(self._ai)
        self._chat_window.closed.connect(lambda: None)
        self._hot_folder = HotFolderMonitor()
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self.search_input.textChanged.connect(self._on_search_changed)

    def _apply_theme(self):
        t = self._theme
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {t['bg']}; }}
            QWidget {{ color: {t['text']}; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; }}
            QMenuBar {{ background-color: {t['bg2']}; border-bottom: 1px solid {t['border']}; padding: 2px 0; font-size: 13px; }}
            QMenuBar::item:selected {{ background-color: {t['hover']}; border-radius: 4px; }}
            QMenu {{ background-color: {t['surface']}; border: 1px solid {t['border']}; border-radius: 8px; padding: 4px; }}
            QMenu::item {{ padding: 6px 28px 6px 16px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {t['selection']}; color: {t['selection_text']}; }}
            QToolBar {{ background-color: {t['bg2']}; border: none; border-bottom: 1px solid {t['border']}; spacing: 4px; padding: 4px 8px; }}
            QToolBar QToolButton {{ background: transparent; border: none; border-radius: 6px; padding: 6px 10px; font-size: 13px; }}
            QToolBar QToolButton:hover {{ background-color: {t['hover']}; }}
            QTableView {{ background-color: {t['surface']}; alternate-background-color: {t['bg2']}; border: 1px solid {t['border']}; border-radius: 8px; gridline-color: {t['border']}; selection-background-color: {t['selection']}; selection-color: {t['selection_text']}; font-size: 13px; outline: none; }}
            QTableView::item {{ padding: 8px 10px; border-bottom: 1px solid {t['border']}; }}
            QTableView::item:selected {{ background-color: {t['selection']}; color: {t['selection_text']}; }}
            QHeaderView::section {{ background-color: {t['header_bg']}; border: none; border-bottom: 2px solid {t['border']}; border-right: 1px solid {t['border']}; padding: 10px 8px; font-weight: 600; font-size: 12px; color: {t['text_secondary']}; }}
            QPushButton {{ background-color: {t['primary']}; color: {t['primary_text']}; border: none; padding: 8px 18px; border-radius: 6px; font-size: 13px; font-weight: 500; }}
            QPushButton:hover {{ background-color: {t['primary_hover']}; }}
            QPushButton:disabled {{ background-color: {t['border']}; color: {t['text_secondary']}; }}
            QLineEdit {{ border: 1.5px solid {t['border']}; border-radius: 8px; padding: 9px 14px; font-size: 13px; background-color: {t['surface']}; color: {t['text']}; }}
            QLineEdit:focus {{ border-color: {t['primary']}; }}
            QComboBox {{ border: 1.5px solid {t['border']}; border-radius: 8px; padding: 8px 14px; font-size: 13px; background-color: {t['surface']}; color: {t['text']}; min-width: 140px; }}
            QComboBox:hover {{ border-color: {t['primary']}; }}
            QComboBox QAbstractItemView {{ background-color: {t['surface']}; border: 1px solid {t['border']}; border-radius: 6px; selection-background-color: {t['selection']}; selection-color: {t['selection_text']}; }}
            QSplitter::handle {{ background-color: {t['border']}; width: 2px; margin: 4px 0; }}
            QStatusBar {{ background-color: {t['bg2']}; border-top: 1px solid {t['border']}; font-size: 12px; color: {t['text_secondary']}; padding: 2px 10px; }}
            QScrollBar:vertical {{ background: {t['bg2']}; width: 8px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 4px; min-height: 30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{ height: 8px; background: {t['bg2']}; border-radius: 4px; }}
            QScrollBar::handle:horizontal {{ background: {t['border']}; border-radius: 4px; min-width: 30px; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
            QGroupBox {{ border: 1px solid {t['border']}; border-radius: 8px; margin-top: 12px; padding: 16px 12px 12px; font-weight: 600; font-size: 13px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; color: {t['text_secondary']}; }}
            QTextEdit {{ border: 1px solid {t['border']}; border-radius: 8px; padding: 8px; background-color: {t['surface']}; color: {t['text']}; font-size: 13px; }}
            QTextEdit:focus {{ border-color: {t['primary']}; }}
        """)

    def toggle_theme(self):
        self._theme_name = "dark" if self._theme_name == "light" else "light"
        self._theme = THEMES[self._theme_name]
        self._config["theme"] = self._theme_name
        self._save_config()
        self._apply_theme()
        if hasattr(self, "dashboard"):
            self.dashboard._theme = self._theme
            self.dashboard.refresh()
        self.theme_btn.setText("\U0001F319" if self._theme_name == "light" else "\u2600\uFE0F")
        btn_bg = "transparent"
        btn_border = self._theme["border"]
        self.theme_btn.setStyleSheet(f"QPushButton {{ background: {btn_bg}; border: 1px solid {btn_border}; border-radius: 18px; font-size: 16px; padding: 0; }} QPushButton:hover {{ background-color: {self._theme['hover']}; }}")
        self.status_label.setText(f"Theme switched to {self._theme_name} mode")

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Search bar
        sc = QWidget()
        sc.setObjectName("searchContainer")
        sc.setStyleSheet(f"#searchContainer {{ background-color: {self._theme['bg2']}; border-bottom: 1px solid {self._theme['border']}; }}")
        sl = QHBoxLayout(sc)
        sl.setContentsMargins(16, 10, 16, 10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search papers by title, author, keyword, or DOI...")
        self.search_input.setClearButtonEnabled(True)
        sl.addWidget(self.search_input, stretch=1)

        self.tag_filter = QComboBox()
        self.tag_filter.addItem("All Papers")
        self.tag_filter.currentTextChanged.connect(self._on_tag_filter)
        sl.addWidget(self.tag_filter)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Journal", "Conference", "Preprint", "Book", "Thesis"])
        self.type_filter.currentTextChanged.connect(self._on_type_filter)
        sl.addWidget(self.type_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Unread", "To Read", "In Progress", "Read"])
        self.status_filter.currentTextChanged.connect(self._on_type_filter)  # reuses same refresh
        sl.addWidget(self.status_filter)

        self.theme_btn = QPushButton("\U0001F319" if self._theme_name == "light" else "\u2600\uFE0F")
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setToolTip("Toggle dark/light theme")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setStyleSheet(f"QPushButton {{ background: transparent; border: 1px solid {self._theme['border']}; border-radius: 18px; font-size: 16px; padding: 0; }} QPushButton:hover {{ background-color: {self._theme['hover']}; }}")
        sl.addWidget(self.theme_btn)
        main_layout.addWidget(sc)

        # Stacked widget
        self.stack = QStackedWidget()
        self.dashboard = DashboardPage(self._theme, self)
        self.dashboard.paper_selected.connect(self._on_dashboard_paper_selected)
        self.dashboard.import_requested.connect(self._import_paper)
        self.stack.addWidget(self.dashboard)

        self.main_view = QWidget()
        mv = QVBoxLayout(self.main_view)
        mv.setContentsMargins(12, 8, 12, 8)

        splitter = QSplitter(Qt.Horizontal)
        self.table = DragDropTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.clicked.connect(self._on_paper_selected)
        self.table.setMinimumWidth(420)
        # Drag-drop handled via the wrapper class below
        self.table.doubleClicked.connect(self._open_pdf)

        self.model = PaperTableModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.table.setModel(self.proxy)
        splitter.addWidget(self.table)

        self.detail = PaperDetailWidget(self._ai)
        self.detail.paper_changed.connect(self._on_paper_changed_from_detail)
        splitter.addWidget(self.detail)
        splitter.setSizes([480, 520])
        mv.addWidget(splitter, stretch=1)
        self.stack.addWidget(self.main_view)
        main_layout.addWidget(self.stack, stretch=1)

        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)
        self.stack.setCurrentIndex(0)

    def show_dashboard(self):
        self.dashboard.refresh()
        self.stack.setCurrentIndex(0)
        self.status_label.setText("Dashboard")

    def _on_dashboard_paper_selected(self, paper_id):
        self._search_mode = "all"
        self.search_input.clear()
        self._load_papers()
        for row, p in enumerate(self._papers):
            if p.id == paper_id:
                idx = self.model.index(row, 0)
                self.table.selectRow(self.proxy.mapFromSource(idx).row())
                self._on_paper_selected(self.proxy.mapFromSource(idx))
                break
        self.stack.setCurrentIndex(1)

    def _setup_menu(self):
        mb = self.menuBar()
        fm = mb.addMenu("File")
        a = QAction("Import Paper...", self)
        a.setShortcut(QKeySequence.Open); a.triggered.connect(self._import_paper)
        fm.addAction(a)
        a = QAction("Import BibTeX (.bib)...", self)
        a.triggered.connect(self._import_bibtex)
        fm.addAction(a)
        a = QAction("Import RIS (.ris)...", self)
        a.triggered.connect(self._import_ris)
        fm.addAction(a)
        fm.addSeparator()
        a = QAction("Export Papers as JSON...", self)
        a.setShortcut(QKeySequence("Ctrl+E")); a.triggered.connect(self._export_json)
        fm.addAction(a)
        a = QAction("Import Papers from JSON...", self)
        a.setShortcut(QKeySequence("Ctrl+I")); a.triggered.connect(self._import_json)
        fm.addAction(a)
        fm.addSeparator()
        a = QAction("Backup Database...", self); a.triggered.connect(self._backup_database)
        a = QAction("Full Backup (.zip)...", self); a.triggered.connect(self._backup_full_zip)
        a = QAction("Restore from .zip...", self); a.triggered.connect(self._restore_full_zip)
        fm.addAction(a)
        a = QAction("Restore Database...", self); a.triggered.connect(self._restore_database)
        fm.addAction(a)
        fm.addSeparator()
        a = QAction("Exit", self); a.setShortcut(QKeySequence.Quit); a.triggered.connect(self.close)
        fm.addAction(a)

        vm = mb.addMenu("View")
        a = QAction("Dashboard", self); a.setShortcut(QKeySequence("Ctrl+1")); a.triggered.connect(self.show_dashboard)
        vm.addAction(a)
        a = QAction("Paper List", self); a.setShortcut(QKeySequence("Ctrl+2")); a.triggered.connect(lambda: self.stack.setCurrentIndex(1))
        vm.addAction(a)
        vm.addSeparator()
        a = QAction("AI Chat", self); a.setShortcut(QKeySequence("Ctrl+Space")); a.triggered.connect(self._toggle_chat)
        vm.addAction(a)
        a = QAction("Toggle Theme", self); a.setShortcut(QKeySequence("Ctrl+T")); a.triggered.connect(self.toggle_theme)
        vm.addAction(a)

        tm = mb.addMenu("Tools")
        a = QAction("Set OpenAI API Key...", self); a.setShortcut(QKeySequence("Ctrl+K")); a.triggered.connect(self._set_api_key)
        tm.addAction(a)
        a = QAction("Manage Tags...", self); a.triggered.connect(self._manage_tags)
        tm.addAction(a)
        tm.addSeparator()
        a = QAction("Library Statistics...", self); a.triggered.connect(self._show_stats)
        tm.addAction(a)
        tm.addSeparator()
        a = QAction("Preferences...", self); a.setShortcut(QKeySequence("Ctrl+,")); a.triggered.connect(self._show_settings)
        tm.addAction(a)

        hm = mb.addMenu("Help")
        a = QAction("About", self); a.triggered.connect(self._show_about)
        hm.addAction(a)

    def _setup_toolbar(self):
        tb = QToolBar(); tb.setMovable(False); tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)
        a = QAction(" Dashboard", self); a.triggered.connect(self.show_dashboard); tb.addAction(a)
        a = QAction(" Import", self); a.triggered.connect(self._import_paper); tb.addAction(a)
        a = QAction(" Delete", self); a.triggered.connect(self._delete_paper); tb.addAction(a)
        tb.addSeparator()
        a = QAction(" Save", self); a.triggered.connect(self._save_current_paper); tb.addAction(a)
        a = QAction(" Open PDF", self); a.setShortcut(QKeySequence("Ctrl+D")); a.triggered.connect(self._open_pdf); tb.addAction(a)

    def _on_search_changed(self):
        self._search_timer.start(300)

    def _perform_search(self):
        q = self.search_input.text().strip()
        if not q:
            self._apply_filters()
            return
        papers = search_papers(q)
        self._papers = papers
        self.model.set_papers(papers)
        self.stack.setCurrentIndex(1)
        # Also index for semantic search
        self._semantic.index_papers(papers)
        self.status_label.setText(f"Found {len(papers)} papers for '{q}'")

    def _on_tag_filter(self, text):
        if text == "All Papers":
            self._search_mode = "all"
            self._load_papers()
        else:
            self._search_mode = text
            papers = search_papers_by_tag(text)
            self._papers = papers
            self.model.set_papers(papers)
            self.stack.setCurrentIndex(1)
            self.status_label.setText(f"{len(papers)} papers tagged '{text}'")

    def _refresh_tag_filter(self):
        cur = self.tag_filter.currentText()
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem("All Papers")
        for tag in get_all_tags():
            self.tag_filter.addItem(tag.name)
        idx = self.tag_filter.findText(cur)
        if idx >= 0: self.tag_filter.setCurrentIndex(idx)
        self.tag_filter.blockSignals(False)

    def _on_type_filter(self):
        self._apply_filters()

    def _apply_filters(self):
        paper_type = self.type_filter.currentText()
        status = self.status_filter.currentText()
        tag = self.tag_filter.currentText()
        if paper_type == "All Types": paper_type = None
        if status == "All Status": status = None
        tag_name = tag if tag != "All Papers" else None

        papers = search_papers_advanced(
            paper_type=paper_type, status=status,
            tags=[tag_name] if tag_name else None
        )
        self._papers = papers
        self.model.set_papers(papers)
        self._semantic.index_papers(papers)
        self.stack.setCurrentIndex(1)
        paper_count = len(papers)
        self.status_label.setText(f"{paper_count} papers")

    def _load_papers(self):
        papers = get_all_papers()
        self.model.set_papers(papers)
        self._refresh_tag_filter()
        self.status_label.setText(f"{len(papers)} papers in library")

    def _import_paper(self):
        dialog = ImportDialog(self)
        if dialog.exec_() == ImportDialog.Accepted and dialog.paper:
            # Dedup check
            dup = find_duplicate(dialog.paper.title, dialog.paper.doi)
            if dup:
                reason, existing_id, existing_title = dup
                reply = QMessageBox.question(self, "Duplicate Found",
                    f"A similar paper already exists:\n{existing_title}\n\n"
                    f"Reason: {reason} match\nAdd anyway?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
            paper_id = add_paper(dialog.paper)
            if paper_id:
                if dialog.paper.file_path and os.path.exists(dialog.paper.file_path):
                    try:
                        from app.pdf_extractor import extract_metadata
                        result = extract_metadata(dialog.paper.file_path)
                        if result["text_content"]:
                            save_fulltext(paper_id, result["text_content"])
                    except Exception:
                        pass
                self.status_label.setText(f"Imported: {dialog.paper.title}")
                self._load_papers()

    def _on_paper_selected(self, index):
        src = self.proxy.mapToSource(index)
        paper = self.model.get_paper(src.row())
        if paper:
            fresh = get_paper(paper.id)
            if fresh:
                self.detail.show_paper(fresh)

    def _on_paper_changed_from_detail(self):
        self._save_current_paper()

    def _save_current_paper(self):
        paper = self.detail._paper
        if paper and paper.id:
            update_paper(paper)
            self._load_papers()
            self.status_label.setText("Paper saved.")

    def _delete_paper(self):
        paper = self.detail._paper
        if not paper or not paper.id:
            return
        reply = QMessageBox.question(self, "Delete Paper", f"Delete '{paper.title}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_paper(paper.id)
            self.detail.show_paper(None)
            self._load_papers()
            self.status_label.setText("Paper deleted.")

    def _open_pdf(self):
        paper = self.detail._paper
        if not paper or not paper.file_path:
            QMessageBox.information(self, "Open PDF", "No PDF file associated with this paper.")
            return
        if not os.path.exists(paper.file_path):
            QMessageBox.warning(self, "File Not Found", f"The PDF file is no longer at:\n{paper.file_path}")
            return
        try:
            os.startfile(paper.file_path)
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Could not open PDF:\n{exc}")

    def _import_pdf_file(self, fpath):
        from app.pdf_extractor import extract_metadata
        result = extract_metadata(fpath)
        paper = Paper(
            title=result["title"] or os.path.splitext(os.path.basename(fpath))[0],
            authors=result["authors"], abstract=result["abstract"],
            year=result["year"], journal=result["journal"], doi=result["doi"],
            file_path=fpath, file_name=os.path.basename(fpath),
        )
        pid = add_paper(paper)
        if result["text_content"]:
            save_fulltext(pid, result["text_content"])
        self.status_label.setText(f"Imported: {paper.title}")
        self._load_papers()

    def _import_bibtex(self):
        from app.batch_import import parse_bibtex_file
        fpaths, _ = QFileDialog.getOpenFileNames(self, "Import BibTeX", "", "BibTeX Files (*.bib);;All Files (*)")
        if not fpaths:
            return
        imported = 0
        skipped = 0
        for fp in fpaths:
            papers = parse_bibtex_file(fp)
            for p in papers:
                dup = find_duplicate(p.title, p.doi)
                if dup:
                    skipped += 1
                    continue
                add_paper(p)
                imported += 1
        QMessageBox.information(self, "Import Complete",
            f"Imported {imported} papers from {len(fpaths)} file(s).\n{skipped} duplicates skipped.")
        self._load_papers()

    def _import_ris(self):
        from app.batch_import import parse_ris_file
        fpaths, _ = QFileDialog.getOpenFileNames(self, "Import RIS", "", "RIS Files (*.ris);;All Files (*)")
        if not fpaths:
            return
        imported = 0
        for fp in fpaths:
            papers = parse_ris_file(fp)
            for p in papers:
                dup = find_duplicate(p.title, p.doi)
                if dup:
                    continue
                add_paper(p)
                imported += 1
        QMessageBox.information(self, "Import Complete", f"Imported {imported} papers.")
        self._load_papers()

    def _manage_tags(self):
        tags = get_all_tags()
        dialog = TagDialog(tags, self)
        if dialog.exec_() == TagDialog.Accepted and dialog.modified:
            for tag in dialog.get_tags():
                if tag.id:
                    update_tag_color(tag.id, tag.color)
                else:
                    conn = __import__("app.database", fromlist=["get_connection"]).get_connection()
                    conn.execute("INSERT OR IGNORE INTO tags (name, color) VALUES (?, ?)", (tag.name, tag.color))
                    conn.commit(); conn.close()
            self._refresh_tag_filter()
            self.status_label.setText("Tags updated.")

    def _set_api_key(self):
        key, ok = QInputDialog.getText(self, "OpenAI API Key", "Enter your OpenAI API key:", text=self._config.get("openai_key", ""))
        if ok:
            self._config["openai_key"] = key
            self._save_config()
            self._ai = AIAssistant(key, model_name=self._config.get("ai_model", "DeepSeek-V3"))
            self.detail.set_ai_assistant(self._ai)
            self._chat_window.set_ai_assistant(self._ai)
            self.status_label.setText("API key set." if key else "API key cleared.")

    def _show_stats(self):
        EnhancedStatsDialog(get_stats(), self).exec_()

    def _show_about(self):
        QMessageBox.about(self, "About Smart Literature Manager",
            "Smart Literature Manager v2.0\n\nAn AI-assisted academic paper management tool.\nBuilt with Python, PyQt5, and PyMuPDF.")

    def _export_json(self):
        fpath, _ = QFileDialog.getSaveFileName(self, "Export Papers", "", "JSON Files (*.json);;All Files (*)")
        if fpath:
            count = export_papers_to_json(fpath)
            QMessageBox.information(self, "Export Complete", f"Exported {count} papers to:\n{fpath}")

    def _import_json(self):
        fpath, _ = QFileDialog.getOpenFileName(self, "Import Papers", "", "JSON Files (*.json);;All Files (*)")
        if fpath:
            try:
                count = import_papers_from_json(fpath)
                QMessageBox.information(self, "Import Complete", f"Imported {count} papers.")
                self._load_papers()
            except Exception as exc:
                QMessageBox.critical(self, "Import Error", str(exc))

    def _backup_database(self):
        fpath, _ = QFileDialog.getSaveFileName(self, "Save Database Backup", "", "Database Files (*.db);;All Files (*)")
        if fpath:
            try:
                result = backup_database(fpath)
                QMessageBox.information(self, "Backup Complete", f"Database backed up to:\n{result}")
            except Exception as exc:
                QMessageBox.critical(self, "Backup Error", str(exc))

    def _restore_database(self):
        backups = list_backups()
        msg = "Select a backup file to restore.\n"
        if backups:
            msg += "\nAvailable backups:\n"
            for name, _, size in backups[:5]:
                msg += f"  {name} ({size / 1024:.0f} KB)\n"
        reply = QMessageBox.warning(self, "Restore Database", msg + "\nThis will replace your current database! Continue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes: return
        fpath, _ = QFileDialog.getOpenFileName(self, "Select Backup File", "", "Database Files (*.db);;All Files (*)")
        if fpath:
            try:
                restore_database(fpath)
                QMessageBox.information(self, "Restore Complete", "Database restored.")
                self._load_papers()
            except Exception as exc:
                QMessageBox.critical(self, "Restore Error", str(exc))

    def _show_settings(self):
        from PyQt5.QtWidgets import QGroupBox, QFormLayout, QComboBox, QCheckBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Preferences"); dialog.setMinimumWidth(520)
        layout = QVBoxLayout(dialog); layout.setSpacing(16)

        g = QGroupBox("Appearance")
        f = QFormLayout(g)
        btn = QPushButton(f"Switch to {'Dark' if self._theme_name == 'light' else 'Light'} Mode")
        btn.clicked.connect(lambda: (self.toggle_theme(), dialog.close()))
        f.addRow("Theme:", btn)
        layout.addWidget(g)

        g2 = QGroupBox("AI Model")
        f2 = QFormLayout(g2)
        model_combo = QComboBox()
        model_combo.addItems(["DeepSeek-V3", "DeepSeek-R1", "OpenAI GPT-3.5", "OpenAI GPT-4o", "Ollama (Local)"])
        idx = model_combo.findText(self._config.get("ai_model", "DeepSeek-V3"))
        if idx >= 0: model_combo.setCurrentIndex(idx)
        f2.addRow("Model:", model_combo)
        api_key_edit = QLineEdit(self._config.get("openai_key", ""))
        api_key_edit.setPlaceholderText("DeepSeek / OpenAI API key (not needed for Ollama)")
        f2.addRow("API Key:", api_key_edit)
        layout.addWidget(g2)

        g3 = QGroupBox("Hot Folder")
        f3 = QFormLayout(g3)
        hot_folder_edit = QLineEdit(self._config.get("hot_folder", ""))
        hot_folder_edit.setPlaceholderText("e.g. C:\\Papers\\Inbox")
        f3.addRow("Watch Folder:", hot_folder_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(lambda: hot_folder_edit.setText(
            QFileDialog.getExistingDirectory(dialog, "Select Folder") or hot_folder_edit.text()))
        f3.addRow("", browse_btn)
        hot_enabled = QCheckBox("Enable hot folder monitoring")
        hot_enabled.setChecked(self._config.get("hot_folder_enabled", False))
        f3.addRow("", hot_enabled)
        layout.addWidget(g3)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self._save_settings(dialog, api_key_edit, model_combo, hot_folder_edit, hot_enabled))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec_()

    def _save_settings(self, dialog, api_key_edit, model_combo=None, hot_folder_edit=None, hot_enabled=None):
        self._config["openai_key"] = api_key_edit.text()
        if model_combo:
            self._config["ai_model"] = model_combo.currentText()
        if hot_folder_edit:
            self._config["hot_folder"] = hot_folder_edit.text()
        if hot_enabled:
            self._config["hot_folder_enabled"] = hot_enabled.isChecked()
        self._save_config()

        model_name = self._config.get("ai_model", "DeepSeek-V3")
        self._ai = AIAssistant(self._config.get("openai_key", ""), model_name=model_name)
        self.detail.set_ai_assistant(self._ai)
        self._chat_window.set_ai_assistant(self._ai)

        # Handle hot folder
        if self._config.get("hot_folder_enabled") and self._config.get("hot_folder"):
            self._hot_folder.stop()
            self._hot_folder = HotFolderMonitor(
                self._config["hot_folder"],
                callback=self._import_pdf_file
            )
            self._hot_folder.start()
            self.status_label.setText(f"Hot folder active: {self._config['hot_folder']}")
        else:
            self._hot_folder.stop()

        self.status_label.setText("Preferences saved.")
        dialog.accept()

    def _toggle_chat(self):
        self._chat_window.toggle_visibility()

    def _backup_full_zip(self):
        from PyQt5.QtWidgets import QFileDialog
        fpath, _ = QFileDialog.getSaveFileName(self, "Save Full Backup", "", "ZIP Archive (*.zip)")
        if not fpath: return
        from app.database import DB_PATH, DB_DIR
        pdf_dir = None
        papers_dir = os.path.join(DB_DIR, "pdfs")
        if os.path.isdir(papers_dir):
            pdf_dir = papers_dir
        count = export_full_zip(fpath, DB_PATH, pdf_dir=pdf_dir)
        if count > 0:
            QMessageBox.information(self, "Backup Complete", f"Full backup saved with {count} files.\n{fpath}")
        else:
            QMessageBox.warning(self, "Backup Failed", "Could not create full backup.")

    def _restore_full_zip(self):
        from PyQt5.QtWidgets import QFileDialog
        reply = QMessageBox.warning(self, "Restore Backup",
            "This will replace your current library! Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes: return
        fpath, _ = QFileDialog.getOpenFileName(self, "Select Backup File", "", "ZIP Archive (*.zip)")
        if not fpath: return
        from app.database import DB_DIR
        extract_to = os.path.join(DB_DIR, "restore")
        result = import_full_zip(fpath, extract_to)
        if result["success"]:
            if result["db_path"]:
                from app.database import restore_database
                restore_database(result["db_path"])
            QMessageBox.information(self, "Restore Complete",
                f"Restored {result['files']} files. Please restart the application.")
        else:
            QMessageBox.critical(self, "Restore Failed", result.get("error", "Unknown error"))

    def closeEvent(self, event):
        if self._papers:
            reply = QMessageBox.question(self, "Exit", "Are you sure you want to exit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes: event.accept()
            else: event.ignore()
        else: event.accept()

    def _load_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception: pass
        return {}

    def _save_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self._config, f, indent=2)
