import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QScrollArea, QGroupBox, QSplitter,
    QFrame, QApplication, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from app.models import READING_STATUS
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtGui import QFont, QPixmap
from app.citation_export import to_bibtex, to_ris, to_apa, to_mla, to_chicago
from app.pdf_extractor import extract_metadata


class PaperDetailWidget(QWidget):
    """Widget showing detailed information about a paper."""

    paper_changed = pyqtSignal()
    summary_ready = pyqtSignal(str)

    def __init__(self, ai_assistant=None, parent=None):
        super().__init__(parent)
        self._paper = None
        self._ai = ai_assistant
        self._paper = None
        self._autosave_timer = QTimer()
        self._autosave_timer.setInterval(30000)  # 30 seconds
        self._autosave_timer.timeout.connect(self._autosave_notes)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        self.title_label = QLabel("Select a paper to view details")
        self.title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)

        # Meta info
        self.meta_label = QLabel("")
        self.meta_label.setWordWrap(True)
        self.meta_label.setStyleSheet("color: #555;")
        layout.addWidget(self.meta_label)

        # Tags display
        self.tags_label = QLabel("")
        self.tags_label.setWordWrap(True)
        layout.addWidget(self.tags_label)

        # Reading status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(READING_STATUS)
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        status_layout.addWidget(self.status_combo)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.export_bib_btn = QPushButton("Export BibTeX")
        self.export_bib_btn.clicked.connect(self._export_bibtex)
        self.export_bib_btn.setEnabled(False)
        btn_layout.addWidget(self.export_bib_btn)

        self.export_ris_btn = QPushButton("Export RIS")
        self.export_ris_btn.clicked.connect(self._export_ris)
        self.export_ris_btn.setEnabled(False)
        btn_layout.addWidget(self.export_ris_btn)

        self.export_apa_btn = QPushButton("APA")
        self.export_apa_btn.clicked.connect(self._export_apa)
        self.export_apa_btn.setEnabled(False)
        btn_layout.addWidget(self.export_apa_btn)

        self.export_mla_btn = QPushButton("MLA")
        self.export_mla_btn.clicked.connect(self._export_mla)
        self.export_mla_btn.setEnabled(False)
        btn_layout.addWidget(self.export_mla_btn)

        self.export_chicago_btn = QPushButton("Chicago")
        self.export_chicago_btn.clicked.connect(self._export_chicago)
        self.export_chicago_btn.setEnabled(False)
        btn_layout.addWidget(self.export_chicago_btn)

        self.ai_summary_btn = QPushButton("AI Summary")
        self.ai_summary_btn.clicked.connect(self._generate_ai_summary)
        self.ai_summary_btn.setEnabled(False)
        btn_layout.addWidget(self.ai_summary_btn)

        self.re_extract_btn = QPushButton("Re-Extract PDF")
        self.re_extract_btn.clicked.connect(self._re_extract)
        self.re_extract_btn.setEnabled(False)
        btn_layout.addWidget(self.re_extract_btn)

        self.export_notes_btn = QPushButton("Export Notes")
        self.export_notes_btn.clicked.connect(self._export_notes_md)
        self.export_notes_btn.setEnabled(False)
        btn_layout.addWidget(self.export_notes_btn)

        self.qa_btn = QPushButton("Ask AI")
        self.qa_btn.clicked.connect(self._ask_ai_question)
        self.qa_btn.setEnabled(False)
        btn_layout.addWidget(self.qa_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Abstract
        abstract_group = QGroupBox("Abstract")
        abstract_layout = QVBoxLayout(abstract_group)
        self.abstract_text = QTextEdit()
        self.abstract_text.setReadOnly(True)
        self.abstract_text.setMaximumHeight(150)
        abstract_layout.addWidget(self.abstract_text)
        layout.addWidget(abstract_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add your notes here...")
        self.notes_edit.textChanged.connect(self._on_notes_changed)
        notes_layout.addWidget(self.notes_edit)
        layout.addWidget(notes_group, stretch=1)

        # AI Summary
        self.ai_group = QGroupBox("AI Summary")
        ai_layout = QVBoxLayout(self.ai_group)
        self.ai_summary_text = QTextEdit()
        self.ai_summary_text.setReadOnly(True)
        self.ai_summary_text.setMaximumHeight(120)
        ai_layout.addWidget(self.ai_summary_text)
        self.ai_group.setVisible(False)
        layout.addWidget(self.ai_group)

    def set_ai_assistant(self, ai):
        self._ai = ai

    def show_paper(self, paper):
        self._paper = paper
        if not paper:
            self.title_label.setText("Select a paper to view details")
            self.meta_label.setText("")
            self.tags_label.setText("")
            self.abstract_text.clear()
            self.notes_edit.blockSignals(True)
            self.notes_edit.clear()
            self.notes_edit.blockSignals(False)
            self.status_combo.blockSignals(True)
            self.status_combo.setCurrentIndex(0)
            self.status_combo.blockSignals(False)
            self.ai_summary_text.clear()
            self.ai_group.setVisible(False)
            for btn in [self.export_bib_btn, self.export_ris_btn, self.export_apa_btn, self.export_mla_btn, self.export_chicago_btn, self.ai_summary_btn, self.re_extract_btn, self.export_notes_btn, self.qa_btn]:
                btn.setEnabled(False)
            return

        self.title_label.setText(paper.title or "(No Title)")
        meta_parts = []
        if paper.authors:
            meta_parts.append(f"Authors: {paper.formatted_authors()}")
        if paper.year:
            meta_parts.append(f"Year: {paper.year}")
        if paper.journal:
            meta_parts.append(f"Journal: {paper.journal}")
        if paper.doi:
            meta_parts.append(f"DOI: {paper.doi}")  # Clickable via context menu
        if paper.file_name:
            meta_parts.append(f"File: {paper.file_name}")
        meta_parts.append(f"Added: {paper.added_date}")
        self.meta_label.setText(" | ".join(meta_parts))

        tags_text = ""
        if paper.tags:
            tags_html = " ".join(
                f'<span style="background-color:#E3F2FD;padding:2px 8px;'
                f'border-radius:10px;margin:2px;">{t}</span>'
                for t in paper.tags
            )
            tags_text = "Tags: " + tags_html
        self.tags_label.setText(tags_text)
        if tags_text:
            self.tags_label.setTextFormat(Qt.RichText)

        self.abstract_text.setPlainText(paper.abstract or "No abstract available.")
        self.status_combo.blockSignals(True)
        idx = self.status_combo.findText(paper.reading_status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        self.status_combo.blockSignals(False)
        self.notes_edit.blockSignals(True)
        self.notes_edit.setPlainText(paper.notes or "")
        self.notes_edit.blockSignals(False)

        # Enable buttons
        self.export_bib_btn.setEnabled(True)
        self.export_ris_btn.setEnabled(True)
        self.export_apa_btn.setEnabled(True)
        self.export_mla_btn.setEnabled(True)
        self.export_chicago_btn.setEnabled(True)
        self.ai_summary_btn.setEnabled(self._ai and self._ai.is_configured())
        self.re_extract_btn.setEnabled(bool(paper.file_path and os.path.exists(paper.file_path)))

        # Clear old AI summary
        self.ai_summary_text.clear()
        self.ai_group.setVisible(False)

    def _on_notes_changed(self):
        if self._paper:
            self._paper.notes = self.notes_edit.toPlainText()
            self._autosave_timer.start()  # Reset autosave timer
    def _autosave_notes(self):
        """Auto-save notes every 30s."""
        self._autosave_timer.stop()
        if self._paper:
            self.paper_changed.emit()

    def _on_status_changed(self, status):
        if self._paper and status:
            self._paper.reading_status = status
            self.paper_changed.emit()

    def _export_bibtex(self):
        if not self._paper:
            return
        text = to_bibtex(self._paper)
        self._copy_to_clipboard(text, "BibTeX citation copied!")

    def _export_ris(self):
        if not self._paper:
            return
        text = to_ris(self._paper)
        self._copy_to_clipboard(text, "RIS citation copied!")

    def _copy_to_clipboard(self, text, msg):
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", msg)

    def _generate_ai_summary(self):
        if not self._paper or not self._ai or not self._ai.is_configured():
            return
        self.ai_summary_text.setPlainText("Generating summary...")
        self.ai_group.setVisible(True)

        result = self._ai.summarize_paper(
            self._paper.title,
            self._paper.abstract
        )
        if result:
            self.ai_summary_text.setPlainText(result)
        else:
            self.ai_summary_text.setPlainText("Failed to generate summary.")

    def mouseDoubleClickEvent(self, event):
        """Double-click the meta line to open PDF if available."""
        if self._paper and self._paper.file_path and os.path.exists(self._paper.file_path):
            try:
                os.startfile(self._paper.file_path)
            except Exception:
                pass
        super().mouseDoubleClickEvent(event)

    def _re_extract(self):
        if not self._paper or not self._paper.file_path:
            return
        if not os.path.exists(self._paper.file_path):
            QMessageBox.warning(self, "Warning", "PDF file not found.")
            return
        result = extract_metadata(self._paper.file_path)
        if result["title"]:
            self._paper.title = result["title"]
        if result["authors"]:
            self._paper.authors = result["authors"]
        if result["year"]:
            self._paper.year = result["year"]
        if result["journal"]:
            self._paper.journal = result["journal"]
        if result["doi"]:
            self._paper.doi = result["doi"]
        if result["abstract"]:
            self._paper.abstract = result["abstract"]
        self.show_paper(self._paper)
        self.paper_changed.emit()
        QMessageBox.information(self, "Done", "Metadata re-extracted from PDF.")


    def _export_apa(self):
        if not self._paper: return
        text = to_apa(self._paper)
        self._copy_to_clipboard(text, "APA citation copied!")

    def _export_mla(self):
        if not self._paper: return
        text = to_mla(self._paper)
        self._copy_to_clipboard(text, "MLA citation copied!")

    def _export_chicago(self):
        if not self._paper: return
        text = to_chicago(self._paper)
        self._copy_to_clipboard(text, "Chicago citation copied!")

    def _export_notes_md(self):
        if not self._paper: return
        from PyQt5.QtWidgets import QFileDialog
        fpath, _ = QFileDialog.getSaveFileName(self, "Export Notes", "", "Markdown (*.md);;All Files (*)")
        if not fpath: return
        lines = [
            f"# {self._paper.title}",
            "",
            f"**Authors:** {self._paper.formatted_authors()}",
            f"**Year:** {self._paper.year or 'N/A'}",
            f"**Journal:** {self._paper.journal or 'N/A'}",
            f"**DOI:** {self._paper.doi or 'N/A'}",
            "",
            "## Abstract",
            self._paper.abstract or "No abstract.",
            "",
            "## Notes",
            self._paper.notes or "No notes.",
            "",
            "## Tags",
            ", ".join(self._paper.tags) if self._paper.tags else "None",
        ]
        text = "\n".join(lines)
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(text)
            QMessageBox.information(self, "Exported", f"Notes saved to:\n{fpath}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export:\n{e}")

    def _ask_ai_question(self):
        if not self._paper or not self._ai or not self._ai.is_configured():
            QMessageBox.information(self, "AI Not Configured", "Please set up your AI API key in Settings first.")
            return
        from PyQt5.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
        from PyQt5.QtWidgets import QApplication as QApp
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ask about: {self._paper.title[:50]}...")
        dialog.setMinimumSize(500, 400)
        layout = QVBoxLayout(dialog)
        question_input = QTextEdit()
        question_input.setPlaceholderText("Ask a question about this paper...\ne.g., What is the main contribution?")
        question_input.setMaximumHeight(80)
        layout.addWidget(question_input)
        answer_display = QTextEdit()
        answer_display.setReadOnly(True)
        answer_display.setPlaceholderText("Answer will appear here...")
        layout.addWidget(answer_display)
        btn_layout = QHBoxLayout()
        ask_btn = QPushButton("Ask")
        btn_layout.addWidget(ask_btn)
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        def do_ask():
            q = question_input.toPlainText().strip()
            if not q: return
            answer_display.setPlainText("Thinking...")
            QApp.processEvents()
            try:
                from app.rag_qa import answer_question
                from app.database import get_fulltext
                fulltext = get_fulltext(self._paper.id) or ""
                answer = answer_question(fulltext, q, self._ai)
                answer_display.setPlainText(answer)
            except Exception as e:
                answer_display.setPlainText(f"Error: {e}")

        ask_btn.clicked.connect(do_ask)
        dialog.exec_()
