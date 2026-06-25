from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
    QColorDialog, QWidget, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QIcon, QPixmap


class TagDialog(QDialog):
    """Dialog for managing tags."""

    def __init__(self, tags, parent=None):
        super().__init__(parent)
        self.tags = tags
        self.modified = False
        self.setWindowTitle("Manage Tags")
        self.setMinimumSize(400, 350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Add tag area
        add_layout = QHBoxLayout()
        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("New tag name...")
        add_layout.addWidget(self.new_tag_input)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_tag)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)

        # Tag list
        self.tag_list = QListWidget()
        self._refresh_list()
        layout.addWidget(self.tag_list)

        # Action buttons
        btn_layout = QHBoxLayout()
        self.color_btn = QPushButton("Change Color...")
        self.color_btn.clicked.connect(self._change_color)
        btn_layout.addWidget(self.color_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self._delete_tag)
        self.delete_btn.setStyleSheet("color: #D32F2F;")
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _refresh_list(self):
        self.tag_list.clear()
        for tag in sorted(self.tags, key=lambda t: t.name.lower()):
            item = QListWidgetItem(tag.name)
            color = QColor(tag.color)
            pix = QPixmap(12, 12)
            pix.fill(color)
            item.setIcon(QIcon(pix))
            if tag.paper_count > 0:
                item.setText(f"{tag.name} ({tag.paper_count})")
            self.tag_list.addItem(item)

    def get_tags(self):
        return self.tags

    def _add_tag(self):
        name = self.new_tag_input.text().strip()
        if not name:
            return
        if any(t.name.lower() == name.lower() for t in self.tags):
            QMessageBox.information(self, "Info", "Tag already exists.")
            return
        from app.models import Tag
        self.tags.append(Tag(name=name))
        self.modified = True
        self.new_tag_input.clear()
        self._refresh_list()

    def _delete_tag(self):
        item = self.tag_list.currentItem()
        if not item:
            return
        name = item.text().split(" (")[0]
        reply = QMessageBox.question(
            self, "Confirm", f"Delete tag '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.tags = [t for t in self.tags if t.name != name]
            self.modified = True
            self._refresh_list()

    def _change_color(self):
        item = self.tag_list.currentItem()
        if not item:
            return
        name = item.text().split(" (")[0]
        tag = next((t for t in self.tags if t.name == name), None)
        if not tag:
            return
        color = QColorDialog.getColor(QColor(tag.color), self, f"Color for '{name}'")
        if color.isValid():
            tag.color = color.name()
            self.modified = True
            self._refresh_list()

