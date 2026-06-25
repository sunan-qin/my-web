"""Enhanced statistics dialog with charts, word cloud, and journal rankings."""
import os
import io
from collections import Counter
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QGridLayout, QTabWidget, QWidget, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from app.database import get_all_papers


class EnhancedStatsDialog(QDialog):
    """Show library statistics with charts and visualizations."""

    def __init__(self, stats, parent=None):
        super().__init__(parent)
        self.stats = stats
        self._papers = get_all_papers()
        self.setWindowTitle("Library Statistics Dashboard")
        self.setMinimumSize(700, 550)
        self.resize(800, 600)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        
        # Overview tab
        overview = self._build_overview()
        tabs.addTab(overview, "📊 Overview")
        
        # Charts tab
        charts = self._build_charts()
        tabs.addTab(charts, "📈 Charts")
        
        # Word Cloud tab
        wordcloud = self._build_wordcloud()
        tabs.addTab(wordcloud, "☁️ Tags & Keywords")
        
        layout.addWidget(tabs)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _build_overview(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Summary cards
        overview = QGroupBox("Overview")
        grid = QGridLayout(overview)
        items = [
            ("Total Papers", self.stats["total"]),
            ("With Abstracts", self.stats["with_abstract"]),
            ("With Full Text", self.stats["with_fulltext"]),
            ("Unique Tags", self.stats["tag_count"]),
            ("Unread", self.stats.get("status_unread", 0)),
            ("In Progress", self.stats.get("status_inprog", 0)),
            ("Read", self.stats.get("status_read", 0)),
        ]
        for i, (label, value) in enumerate(items):
            grid.addWidget(QLabel(f"<b>{label}:</b>"), i, 0)
            grid.addWidget(QLabel(str(value)), i, 1)
        layout.addWidget(overview)
        
        # Year distribution
        if self.stats["years"]:
            year_group = QGroupBox("Papers by Year")
            year_layout = QGridLayout(year_group)
            year_layout.addWidget(QLabel("<b>Year</b>"), 0, 0)
            year_layout.addWidget(QLabel("<b>Count</b>"), 0, 1)
            for row, (year, count) in enumerate(sorted(self.stats["years"].items(), reverse=True), 1):
                year_layout.addWidget(QLabel(str(year)), row, 0)
                year_layout.addWidget(QLabel(str(count)), row, 1)
            layout.addWidget(year_group)
        
        # Journal rankings
        journal_counts = Counter(p.journal for p in self._papers if p.journal)
        if journal_counts:
            journal_group = QGroupBox("Top Journals/Conferences")
            journal_layout = QGridLayout(journal_group)
            journal_layout.addWidget(QLabel("<b>Rank</b>"), 0, 0)
            journal_layout.addWidget(QLabel("<b>Journal</b>"), 0, 1)
            journal_layout.addWidget(QLabel("<b>Papers</b>"), 0, 2)
            for rank, (journal, count) in enumerate(journal_counts.most_common(10), 1):
                journal_layout.addWidget(QLabel(f"#{rank}"), rank, 0)
                journal_layout.addWidget(QLabel(journal[:50]), rank, 1)
                bar = QLabel("█" * min(count, 20))
                bar.setStyleSheet("color: #2563EB;")
                journal_layout.addWidget(bar, rank, 2)
            layout.addWidget(journal_group)
        
        # Author co-occurrence
        author_counter = Counter()
        for p in self._papers:
            if p.authors:
                authors = [a.strip() for a in p.authors.replace(" and ", ";").split(";")]
                for a in authors:
                    if a:
                        author_counter[a] += 1
        if author_counter:
            author_group = QGroupBox("Top Authors")
            author_layout = QGridLayout(author_group)
            author_layout.addWidget(QLabel("<b>Author</b>"), 0, 0)
            author_layout.addWidget(QLabel("<b>Papers</b>"), 0, 1)
            for rank, (author, count) in enumerate(author_counter.most_common(15), 1):
                author_layout.addWidget(QLabel(f"{author[:40]}"), rank, 0)
                bar = QLabel("█" * min(count, 15))
                bar.setStyleSheet("color: #10B981;")
                author_layout.addWidget(bar, rank, 1)
            layout.addWidget(author_group)
        
        # Reading status distribution
        status_group = QGroupBox("Reading Status Distribution")
        status_layout = QGridLayout(status_group)
        statuses = [
            ("📕 Unread", self.stats.get("status_unread", 0), "#94A3B8"),
            ("📗 To Read", self.stats.get("status_toread", 0), "#F59E0B"),
            ("📝 In Progress", self.stats.get("status_inprog", 0), "#3B82F6"),
            ("✅ Read", self.stats.get("status_read", 0), "#10B981"),
        ]
        for row, (label, count, color) in enumerate(statuses):
            status_layout.addWidget(QLabel(label), row, 0)
            bar = QLabel("█" * min(count, 20))
            bar.setStyleSheet(f"color: {color};")
            status_layout.addWidget(bar, row, 1)
            status_layout.addWidget(QLabel(str(count)), row, 2)
        layout.addWidget(status_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def _build_charts(self):
        """Build charts tab using matplotlib (if available) or text-based fallback."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            
            # Year trend chart
            if self.stats["years"]:
                years = sorted(self.stats["years"].keys())
                counts = [self.stats["years"][y] for y in years]
                fig, ax = plt.subplots(figsize=(6, 3))
                ax.bar(years, counts, color="#3B82F6", alpha=0.8)
                ax.set_xlabel("Year")
                ax.set_ylabel("Papers")
                ax.set_title("Publication Year Trend")
                ax.tick_params(axis="x", rotation=45)
                plt.tight_layout()
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=100)
                plt.close(fig)
                buf.seek(0)
                pixmap = QPixmap()
                pixmap.loadFromData(buf.getvalue())
                img_label = QLabel()
                img_label.setPixmap(pixmap)
                img_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(img_label)
            
            # Journal frequency chart
            journal_counts = Counter(p.journal for p in self._papers if p.journal)
            if journal_counts:
                top_journals = journal_counts.most_common(10)
                j_names = [j[:25] for j, _ in top_journals]
                j_counts = [c for _, c in top_journals]
                fig2, ax2 = plt.subplots(figsize=(6, 3.5))
                ax2.barh(range(len(j_names)), j_counts, color="#10B981", alpha=0.8)
                ax2.set_yticks(range(len(j_names)))
                ax2.set_yticklabels(j_names)
                ax2.set_xlabel("Papers")
                ax2.set_title("Top Journals/Conferences")
                plt.tight_layout()
                buf2 = io.BytesIO()
                fig2.savefig(buf2, format="png", dpi=100)
                plt.close(fig2)
                buf2.seek(0)
                pixmap2 = QPixmap()
                pixmap2.loadFromData(buf2.getvalue())
                img_label2 = QLabel()
                img_label2.setPixmap(pixmap2)
                img_label2.setAlignment(Qt.AlignCenter)
                layout.addWidget(img_label2)
            
            # Reading status pie chart
            status_counts = {
                "Unread": self.stats.get("status_unread", 0),
                "To Read": self.stats.get("status_toread", 0),
                "In Progress": self.stats.get("status_inprog", 0),
                "Read": self.stats.get("status_read", 0),
            }
            if any(status_counts.values()):
                fig3, ax3 = plt.subplots(figsize=(4, 3))
                labels = [k for k, v in status_counts.items() if v > 0]
                sizes = [v for v in status_counts.values() if v > 0]
                colors = ["#94A3B8", "#F59E0B", "#3B82F6", "#10B981"]
                ax3.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors[:len(sizes)])
                ax3.set_title("Reading Status")
                plt.tight_layout()
                buf3 = io.BytesIO()
                fig3.savefig(buf3, format="png", dpi=100)
                plt.close(fig3)
                buf3.seek(0)
                pixmap3 = QPixmap()
                pixmap3.loadFromData(buf3.getvalue())
                img_label3 = QLabel()
                img_label3.setPixmap(pixmap3)
                img_label3.setAlignment(Qt.AlignCenter)
                layout.addWidget(img_label3)
        
        except ImportError:
            no_chart = QLabel("Matplotlib not available.\nInstall with: pip install matplotlib")
            no_chart.setAlignment(Qt.AlignCenter)
            no_chart.setStyleSheet("color: #64748B; font-size: 14px; padding: 40px;")
            layout.addWidget(no_chart)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def _build_wordcloud(self):
        """Build word cloud tab from tags and keywords."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tag cloud
        tag_counts = Counter()
        for p in self._papers:
            for t in (p.tags or []):
                tag_counts[t] += 1
            for kw in (p.keywords or "").split(","):
                kw = kw.strip().lower()
                if kw and len(kw) > 1:
                    tag_counts[kw] += 1
        
        if tag_counts:
            # Sort by frequency
            sorted_tags = tag_counts.most_common(50)
            max_count = max(c for _, c in sorted_tags) if sorted_tags else 1
            
            cloud_group = QGroupBox("Tag & Keyword Cloud")
            cloud_layout = QVBoxLayout(cloud_group)
            
            # Generate HTML word cloud
            html_parts = []
            for tag, count in sorted_tags:
                size = 10 + int((count / max_count) * 30)
                opacity = 0.5 + (count / max_count) * 0.5
                color = f"hsl({(hash(tag) % 360)}, 70%, {50 - (count/max_count)*20}%)"
                html_parts.append(
                    f'<span style="font-size: {size}px; color: {color}; '
                    f'opacity: {opacity:.2f}; display: inline-block; '
                    f'margin: 3px 5px; padding: 2px 6px; '
                    f'background: #F1F5F9; border-radius: 8px;">'
                    f'{tag} ({count})</span>'
                )
            
            html = '<div style="line-height: 2.0; text-align: center;">' + " ".join(html_parts) + "</div>"
            cloud_label = QLabel(html)
            cloud_label.setTextFormat(Qt.RichText)
            cloud_label.setWordWrap(True)
            cloud_layout.addWidget(cloud_label)
            layout.addWidget(cloud_group)
            
            # Tag table
            table_group = QGroupBox("Detailed Tag/Keyword Counts")
            table_layout = QGridLayout(table_group)
            table_layout.addWidget(QLabel("<b>Tag/Keyword</b>"), 0, 0)
            table_layout.addWidget(QLabel("<b>Count</b>"), 0, 1)
            for row, (tag, count) in enumerate(sorted_tags[:20], 1):
                table_layout.addWidget(QLabel(tag), row, 0)
                bar = QLabel("█" * min(count, 15))
                bar.setStyleSheet("color: #8B5CF6;")
                table_layout.addWidget(bar, row, 1)
                table_layout.addWidget(QLabel(str(count)), row, 2)
            layout.addWidget(table_group)
        else:
            no_tags = QLabel("No tags or keywords yet.\nAdd tags when importing papers.")
            no_tags.setAlignment(Qt.AlignCenter)
            no_tags.setStyleSheet("color: #64748B; font-size: 14px; padding: 40px;")
            layout.addWidget(no_tags)
        
        # AI Interpretation button
        ai_btn = QPushButton("🔍 AI Interpretation of Statistics")
        ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6; color: white; border: none;
                border-radius: 8px; padding: 10px 20px; font-size: 13px;
            }
            QPushButton:hover { background-color: #7C3AED; }
        """)
        ai_btn.clicked.connect(self._ai_interpret_stats)
        layout.addWidget(ai_btn)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def _ai_interpret_stats(self):
        """Call AI to interpret library statistics."""
        try:
            from app.ai_assistant import AIAssistant
            from app.database import get_all_papers
            # We don"t have direct access to _ai, so create from config
            import json, os
            cfg_dir = os.path.join(os.path.expanduser("~"), ".smart-lit-manager")
            cfg_file = os.path.join(cfg_dir, "config.json")
            ai = AIAssistant()
            if os.path.exists(cfg_file):
                with open(cfg_file) as f:
                    cfg = json.load(f)
                    ai = AIAssistant(cfg.get("openai_key", ""), cfg.get("ai_model", "OpenAI GPT-3.5"))
            if not ai.is_configured():
                QMessageBox.information(self, "AI Not Configured",
                    "Please set your API key in Settings.")
                return
            
            papers = get_all_papers()
            stats_text = (
                f"Library contains {len(papers)} papers.\n"
                f"Years: {dict(self.stats['years'])}\n"
                f"Reading status: Unread={self.stats.get('status_unread',0)}, "
                f"In Progress={self.stats.get('status_inprog',0)}, "
                f"Read={self.stats.get('status_read',0)}\n"
            )
            if papers:
                journals = Counter(p.journal for p in papers if p.journal)
                if journals:
                    top3 = journals.most_common(3)
                    stats_text += f"Top journals: {', '.join(f'{j}({c})' for j,c in top3)}\n"
                tags_all = [t for p in papers for t in (p.tags or [])]
                if tags_all:
                    top_tags = Counter(tags_all).most_common(5)
                    stats_text += f"Top tags: {', '.join(f'{t}({c})' for t,c in top_tags)}\n"
            
            prompt = (
                "You are a research analytics assistant. Interpret the following "
                "literature library statistics and provide meaningful insights:\n\n"
                f"{stats_text}\n\n"
                "Provide 3-4 concise observations about research focus and gaps."
            )
            result = ai._call_api(prompt)
            if result:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, "AI Library Insights", result)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"AI interpretation failed:\n{e}")
