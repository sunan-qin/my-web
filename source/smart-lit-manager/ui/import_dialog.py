from PyQt5.QtWidgets import QApplication
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QFormLayout, QFileDialog, QMessageBox,
    QProgressDialog, QSpinBox, QGroupBox, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt
from app.models import Paper
from app.pdf_extractor import extract_metadata


class ImportDialog(QDialog):
    """Dialog for importing a PDF paper."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.paper = None
        self.setWindowTitle("Import Paper")
        self.setMinimumSize(600, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # File selection
        file_group = QGroupBox("PDF File")
        file_layout = QHBoxLayout(file_group)
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Select a PDF file...")
        self.file_path.setReadOnly(True)
        file_layout.addWidget(self.file_path)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        layout.addWidget(file_group)

        # Auto-extract button
        self.extract_btn = QPushButton("Auto-Extract Metadata from PDF")
        self.extract_btn.clicked.connect(self._auto_extract)
        self.extract_btn.setEnabled(False)
        layout.addWidget(self.extract_btn)

        # Metadata form
        form = QFormLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Paper title")
        form.addRow("Title:", self.title_edit)

        self.authors_edit = QLineEdit()
        self.authors_edit.setPlaceholderText("e.g. Smith, J.; Doe, J.")
        form.addRow("Authors:", self.authors_edit)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(1800, 2030)
        self.year_spin.setSpecialValueText("Unknown")
        self.year_spin.setValue(0)
        form.addRow("Year:", self.year_spin)

        self.journal_edit = QLineEdit()
        self.journal_edit.setPlaceholderText("Journal name")
        form.addRow("Journal:", self.journal_edit)

        self.doi_edit = QLineEdit()
        self.doi_edit.setPlaceholderText("10.xxxx/xxxxx")
        form.addRow("DOI:", self.doi_edit)

        doi_lookup_btn = QPushButton("Lookup DOI")
        doi_lookup_btn.clicked.connect(self._doi_lookup)
        form.addRow("", doi_lookup_btn)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Journal", "Conference", "Preprint", "Book", "Thesis", "Other"])
        form.addRow("Type:", self.type_combo)

        self.keywords_edit = QLineEdit()
        self.keywords_edit.setPlaceholderText("e.g. transformer, attention, nlp")
        form.addRow("Keywords:", self.keywords_edit)

        pages_layout = QHBoxLayout()
        self.start_page_edit = QLineEdit()
        self.start_page_edit.setPlaceholderText("Start")
        self.start_page_edit.setMaximumWidth(80)
        pages_layout.addWidget(self.start_page_edit)
        pages_layout.addWidget(QLabel("-"))
        self.end_page_edit = QLineEdit()
        self.end_page_edit.setPlaceholderText("End")
        self.end_page_edit.setMaximumWidth(80)
        pages_layout.addWidget(self.end_page_edit)
        pages_layout.addStretch()
        form.addRow("Pages:", pages_layout)

        self.publisher_edit = QLineEdit()
        self.publisher_edit.setPlaceholderText("Publisher name")
        form.addRow("Publisher:", self.publisher_edit)

        self.issn_edit = QLineEdit()
        self.issn_edit.setPlaceholderText("ISSN/ISBN")
        form.addRow("ISSN/ISBN:", self.issn_edit)

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("e.g. machine-learning, nlp, transformers")
        form.addRow("Tags:", self.tags_edit)

        self.abstract_edit = QTextEdit()
        self.abstract_edit.setPlaceholderText("Paper abstract...")
        self.abstract_edit.setMaximumHeight(150)
        form.addRow("Abstract:", self.abstract_edit)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self._import)
        import_btn.setDefault(True)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if path:
            self.file_path.setText(path)
            self.extract_btn.setEnabled(True)

    def _auto_extract(self):
        path = self.file_path.text()
        if not path or not os.path.exists(path):
            return

        progress = QProgressDialog("Extracting metadata from PDF...", None, 0, 0, self)
        progress.setWindowTitle("Extracting")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        QApplication.processEvents()

        try:
            result = extract_metadata(path)
            if result["title"]:
                self.title_edit.setText(result["title"])
            if result["authors"]:
                self.authors_edit.setText(result["authors"])
            if result["year"]:
                self.year_spin.setValue(result["year"])
            if result["journal"]:
                self.journal_edit.setText(result["journal"])
            if result["doi"]:
                self.doi_edit.setText(result["doi"])
            if result["abstract"]:
                self.abstract_edit.setPlainText(result["abstract"])
        finally:
            progress.close()

    def _doi_lookup(self):
        doi = self.doi_edit.text().strip()
        if not doi:
            QMessageBox.information(self, "DOI Lookup", "Enter a DOI first.")
            return
        try:
            from app.crossref_api import fetch_by_doi
            result = fetch_by_doi(doi)
            if result:
                self.title_edit.setText(result.get("title", ""))
                self.authors_edit.setText(result.get("authors", ""))
                if result.get("abstract"):
                    self.abstract_edit.setPlainText(result["abstract"])
                if result.get("year"):
                    self.year_spin.setValue(result["year"])
                self.journal_edit.setText(result.get("journal", ""))
                self.publisher_edit.setText(result.get("publisher", ""))
                type_name = result.get("paper_type", "Journal")
                idx = self.type_combo.findText(type_name)
                if idx >= 0:
                    self.type_combo.setCurrentIndex(idx)
                QMessageBox.information(self, "Done", "Metadata fetched from CrossRef!")
            else:
                QMessageBox.information(self, "Not Found", "Could not fetch metadata for this DOI.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"DOI lookup failed:\n{e}")

    def _import(self):
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Warning", "Please enter a paper title.")
            return

        tags = [t.strip() for t in self.tags_edit.text().split(",") if t.strip()]

        self.paper = Paper(
            title=title,
            authors=self.authors_edit.text().strip(),
            abstract=self.abstract_edit.toPlainText().strip(),
            year=self.year_spin.value() if self.year_spin.value() > 0 else None,
            journal=self.journal_edit.text().strip(),
            doi=self.doi_edit.text().strip(),
            file_path=self.file_path.text(),
            file_name=os.path.basename(self.file_path.text()) if self.file_path.text() else "",
            tags=tags,
            paper_type=self.type_combo.currentText(),
            keywords=self.keywords_edit.text().strip(),
            publisher=self.publisher_edit.text().strip(),
            issn=self.issn_edit.text().strip(),
            start_page=self.start_page_edit.text().strip(),
            end_page=self.end_page_edit.text().strip(),
        )
        self.accept()

