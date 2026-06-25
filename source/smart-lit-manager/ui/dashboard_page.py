import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGridLayout, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap

from app.database import get_stats, get_recent_papers


class StatCard(QFrame):
    def __init__(self, label, value, color="#2563EB", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700;")
        layout.addWidget(self.value_label)
        self.desc_label = QLabel(label)
        self.desc_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500;")
        layout.addWidget(self.desc_label)


class DashboardPage(QWidget):
    paper_selected = pyqtSignal(int)
    import_requested = pyqtSignal()

    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(24)

        t = self._theme
        header = QLabel("\U0001F4DA Welcome to Smart Literature Manager")
        hfont = QFont()
        hfont.setPointSize(22)
        hfont.setBold(True)
        header.setFont(hfont)
        header.setStyleSheet(f"color: {t['text']};")
        layout.addWidget(header)

        subtitle = QLabel("Your personal academic paper library. Import PDFs, organize with tags, and search full text.")
        subtitle.setStyleSheet(f"color: {t['text_secondary']}; font-size: 14px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        actions = QHBoxLayout()
        import_btn = QPushButton("\U0001F4C4  Import a Paper")
        import_btn.setMinimumHeight(44)
        import_btn.setStyleSheet(
            f"QPushButton {{ background-color: {t['primary']}; color: white; "
            f"border-radius: 10px; font-size: 14px; font-weight: 600; padding: 10px 24px; }}"
            f"QPushButton:hover {{ background-color: {t['primary_hover']}; }}"
        )
        import_btn.clicked.connect(self.import_requested.emit)
        actions.addWidget(import_btn)
        actions.addStretch()
        layout.addLayout(actions)

        # Stats cards
        self.stats_widget = QWidget()
        self.stats_grid = QGridLayout(self.stats_widget)
        self.stats_grid.setSpacing(16)
        layout.addWidget(self.stats_widget)

        # Recent papers section
        recent_label = QLabel("\U0001F4C3  Recent Papers")
        rfont = QFont()
        rfont.setPointSize(16)
        rfont.setBold(True)
        recent_label.setFont(rfont)
        recent_label.setStyleSheet(f"color: {t['text']};")
        layout.addWidget(recent_label)

        self.recent_container = QVBoxLayout()
        self.recent_container.setSpacing(8)
        layout.addLayout(self.recent_container)

        layout.addStretch()
        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        stats = get_stats()
        recent = get_recent_papers(6)
        t = self._theme

        # Stats cards
        for i in reversed(range(self.stats_grid.count())):
            w = self.stats_grid.itemAt(i).widget()
            if w:
                w.setParent(None)

        cards = [
            ("Total Papers", stats["total"], t["primary"]),
            ("Unread", stats.get("status_unread", 0), t["status_unread"]),
            ("In Progress", stats.get("status_inprog", 0), t["status_progress"]),
            ("Read", stats.get("status_read", 0), t["status_read"]),
        ]
        for i, (label, value, color) in enumerate(cards):
            card = StatCard(label, value, color)
            card.setStyleSheet(
                f"#statCard {{ background-color: {t['surface']}; "
                f"border: 1px solid {t['border']}; border-radius: 12px; }}"
            )
            self.stats_grid.addWidget(card, 0, i)

        # Recent papers
        for i in reversed(range(self.recent_container.count())):
            w = self.recent_container.itemAt(i).widget()
            if w:
                w.setParent(None)

        if not recent:
            empty = QLabel("No papers yet. Click 'Import a Paper' to get started!")
            empty.setStyleSheet(f"color: {t['text_secondary']}; font-size: 14px; padding: 20px;")
            empty.setAlignment(Qt.AlignCenter)
            self.recent_container.addWidget(empty)
            return

        for paper in recent:
            card = QFrame()
            card.setObjectName("recentCard")
            card.setCursor(Qt.PointingHandCursor)
            card.setStyleSheet(
                f"#recentCard {{ background-color: {t['surface']}; "
                f"border: 1px solid {t['border']}; border-radius: 10px; padding: 12px 16px; }}"
                f"#recentCard:hover {{ background-color: {t['hover']}; border-color: {t['primary']}; }}"
            )
            cl = QHBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)

            info = QVBoxLayout()
            title_lbl = QLabel(
                paper.title[:80] + "..." if len(paper.title) > 80 else paper.title
            )
            title_lbl.setStyleSheet(f"color: {t['text']}; font-weight: 600; font-size: 14px;")
            info.addWidget(title_lbl)

            meta = paper.formatted_authors()
            if paper.year:
                meta += f" ({paper.year})"
            meta_lbl = QLabel(meta)
            meta_lbl.setStyleSheet(f"color: {t['text_secondary']}; font-size: 12px;")
            info.addWidget(meta_lbl)
            cl.addLayout(info, stretch=1)

            status_lbl = QLabel(paper.status_emoji())
            status_lbl.setStyleSheet("font-size: 20px;")
            cl.addWidget(status_lbl)

            pid = paper.id
            card.mousePressEvent = lambda e, p=pid: self.paper_selected.emit(p)
            self.recent_container.addWidget(card)
