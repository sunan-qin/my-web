from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor


class PaperTableModel(QAbstractTableModel):
    """Qt Model for displaying papers in a table view."""

    COLUMNS = ["Status", "Title", "Authors", "Year", "Journal", "Tags", "Added"]

    def __init__(self, papers=None, parent=None):
        super().__init__(parent)
        self._papers = papers or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._papers)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._papers):
            return None
        paper = self._papers[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return paper.status_emoji() + " " + paper.reading_status
            elif col == 1:
                return paper.title or "(No Title)"
            elif col == 2:
                return paper.formatted_authors()
            elif col == 3:
                return str(paper.year) if paper.year else ""
            elif col == 4:
                return paper.journal or ""
            elif col == 5:
                return ", ".join(paper.tags) if paper.tags else ""
            elif col == 6:
                return paper.added_date

        if role == Qt.ForegroundRole and col == 1:
            if paper.title:
                return QColor("#1A73E8")
            return QColor("#888")

        if role == Qt.ToolTipRole:
            return paper.short_citation()

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section]
        return None

    def get_paper(self, row):
        if 0 <= row < len(self._papers):
            return self._papers[row]
        return None

    def set_papers(self, papers):
        self.beginResetModel()
        self._papers = papers
        self.endResetModel()

    def sort(self, column, order=Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        reverse = order == Qt.DescendingOrder
        if column == 0:
            self._papers.sort(key=lambda p: p.reading_status, reverse=reverse)
        elif column == 1:
            self._papers.sort(key=lambda p: (p.title or "").lower(), reverse=reverse)
        elif column == 2:
            self._papers.sort(key=lambda p: (p.authors or "").lower(), reverse=reverse)
        elif column == 3:
            self._papers.sort(key=lambda p: p.year if p.year else 0, reverse=reverse)
        elif column == 4:
            self._papers.sort(key=lambda p: (p.journal or "").lower(), reverse=reverse)
        elif column == 6:
            self._papers.sort(key=lambda p: p.added_date or "", reverse=reverse)
        self.layoutChanged.emit()
