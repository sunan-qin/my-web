"""Floating AI Chat window for IntelliPaper — async DeepSeek/OpenAI chat."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFrame, QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont


class FloatingChatWindow(QFrame):
    """Floating always-on-top AI chat window. Async via signals; never freezes UI."""

    closed = pyqtSignal()

    def __init__(self, ai_assistant=None, parent=None):
        super().__init__(parent)
        self._ai = ai_assistant
        self._setup_ui()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setMinimumSize(380, 450)
        self.resize(420, 520)
        self._dragging = False
        self._drag_pos = None

        # Connect AI signals if assistant is available
        self._connect_ai_signals()

    def _connect_ai_signals(self):
        if self._ai:
            self._ai.response_ready.connect(self._on_ai_response)
            self._ai.error_occurred.connect(self._on_ai_error)
            self._ai.status_changed.connect(self._on_ai_status)

    def set_ai_assistant(self, ai):
        # Disconnect old signals
        if self._ai:
            try:
                self._ai.response_ready.disconnect()
                self._ai.error_occurred.disconnect()
                self._ai.status_changed.disconnect()
            except TypeError:
                pass
        self._ai = ai
        self._connect_ai_signals()
        self._update_status_ui()

    def _update_status_ui(self):
        if self._ai and self._ai.is_configured():
            self.status_label.setText("AI ready — DeepSeek/OpenAI")
            self.status_label.setStyleSheet("color: #34D399; font-size: 11px;")
            self.send_btn.setEnabled(True)
        else:
            self.status_label.setText("Set API key in Settings (Ctrl+,)")
            self.status_label.setStyleSheet("color: #F59E0B; font-size: 11px;")
            self.send_btn.setEnabled(False)

    def _setup_ui(self):
        self.setObjectName("chatWindow")
        self.setStyleSheet("""
            #chatWindow {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── Title bar ──
        title_bar = QHBoxLayout()
        title_label = QLabel("\U0001F916  AI Assistant")
        title_label.setStyleSheet("color: #F1F5F9; font-weight: bold; font-size: 13px;")
        title_bar.addWidget(title_label)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedHeight(22)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #94A3B8; border: 1px solid #475569;
                border-radius: 4px; font-size: 11px; padding: 0 8px;
            }
            QPushButton:hover { color: #E2E8F0; border-color: #64748B; }
        """)
        self.clear_btn.clicked.connect(self._clear_chat)
        title_bar.addWidget(self.clear_btn)

        title_bar.addStretch()

        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #94A3B8; border: none; font-size: 14px; }
            QPushButton:hover { color: #EF4444; }
        """)
        close_btn.clicked.connect(self.hide_chat)
        title_bar.addWidget(close_btn)
        layout.addLayout(title_bar)

        # ── Chat display ──
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #0F172A;
                color: #E2E8F0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        # Welcome message
        self.chat_display.setHtml(
            '<div style="color: #94A3B8; text-align: center; padding: 20px;">'
            '<div style="font-size: 32px; margin-bottom: 8px;">\U0001F916</div>'
            '<b>AI Assistant</b><br>'
            'Ask anything about your papers:<br><br>'
            '\U0001F50D "Find papers about machine learning"<br>'
            '\U0001F4D6 "Summarize the latest papers"<br>'
            '\U0001F4CA "What are my research trends?"<br><br>'
            '<span style="color: #F59E0B;">Set API key in Settings (Ctrl+,) first</span>'
            '</div>'
        )
        layout.addWidget(self.chat_display, stretch=1)

        # ── Input area ──
        input_layout = QHBoxLayout()
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Ask AI about your library...")
        self.input_field.setMaximumHeight(60)
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: #0F172A;
                color: #E2E8F0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px;
                font-size: 13px;
            }
        """)
        # Ctrl+Enter to send
        self.input_field.installEventFilter(self)  # Simplified: we'll handle via signal
        input_layout.addWidget(self.input_field, stretch=1)

        self.send_btn = QPushButton("\u27A4")
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #2563EB; }
            QPushButton:disabled { background-color: #475569; }
        """)
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

        # ── Status label ──
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: #64748B; font-size: 11px;")
        layout.addWidget(self.status_label)

    # ── Message handling ──

    def _send_message(self):
        text = self.input_field.toPlainText().strip()
        if not text or not self._ai:
            return
        self.input_field.clear()
        self.send_btn.setEnabled(False)

        # Show user message
        self._append_message("You", text, "#60A5FA")

        if not self._ai.is_configured():
            self._append_message("System", "Set API key in Settings (Ctrl+,)", "#F59E0B")
            self.send_btn.setEnabled(True)
            return

        # Gather library context
        try:
            from app.database import get_all_papers
            papers = get_all_papers()
            lib_context = f"User's library has {len(papers)} papers."
            if papers:
                lib_context += "\nRecent:\n" + "\n".join(
                    f"- \"{p.title}\" ({p.year or 'N/A'})"
                    for p in papers[:5]
                )
        except Exception:
            lib_context = "Library: unknown"

        # Send async
        self._ai.chat_async(text, library_context=lib_context)

    def _on_ai_response(self, response_text):
        self._append_message("AI", response_text, "#E2E8F0")
        self.send_btn.setEnabled(True)

    def _on_ai_error(self, error_msg):
        self._append_message("Error", error_msg, "#EF4444")
        self.send_btn.setEnabled(True)

    def _on_ai_status(self, status_text):
        self.status_label.setText(status_text)
        if status_text == "Ready":
            self.status_label.setStyleSheet("color: #34D399; font-size: 11px;")
        elif status_text == "Thinking...":
            self.status_label.setStyleSheet("color: #FBBF24; font-size: 11px;")
        elif status_text == "Error":
            self.status_label.setStyleSheet("color: #EF4444; font-size: 11px;")

    def _append_message(self, sender, text, color):
        self.chat_display.append(
            f'<div style="color: {color}; margin: 6px 0; line-height: 1.5;">'
            f'<b>{sender}:</b> {text}</div>'
        )
        # Auto-scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _clear_chat(self):
        self.chat_display.clear()
        self.chat_display.setHtml(
            '<div style="color: #94A3B8; text-align: center; padding: 20px;">'
            'Chat cleared. Start a new conversation!</div>'
        )
        if self._ai:
            self._ai.clear_conversation()

    # ── Visibility ──

    def show_chat(self):
        self.show()
        self.raise_()
        self.input_field.setFocus()
        self._update_status_ui()

    def hide_chat(self):
        self.hide()
        self.closed.emit()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide_chat()
        else:
            self.show_chat()

    # ── Window dragging ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._dragging:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        event.accept()
