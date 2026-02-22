import re
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QAction, QKeySequence, QFont
from PyQt6.QtWidgets import (
    QWidget, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox,
    QFileDialog, QLabel, QFrame,
    QScrollArea, QSizePolicy, QApplication
)

from app.config import DEFAULT_SYSTEM_PROMPT
from app.workers.chat_worker import ChatWorker
from app.ui.themes import get_theme, get_stylesheets

FONT_TITLE = QFont("Segoe UI", 15, QFont.Weight.Bold)
FONT_BODY  = QFont("Segoe UI", 12)
FONT_SMALL = QFont("Segoe UI", 11)

def markdown_to_html(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.+)$",  r"<h2>\1</h2>", text, flags=re.MULTILINE)
    text = re.sub(r"^# (.+)$",   r"<h1>\1</h1>", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`",       r"<code>\1</code>", text)
    text = re.sub(r"^[*-] (.+)$",  r"• \1", text, flags=re.MULTILINE)
    text = text.replace("\n", "<br>")
    return text


class BubbleWidget(QWidget):
    def __init__(self, text: str, is_user: bool, theme: dict, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        label = QLabel(markdown_to_html(text))
        label.setWordWrap(True)
        label.setFont(QFont("Helvetica Neue", 13))
        label.setMaximumWidth(480)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        if is_user:
            bg, fg, radius = theme["bubble_user_bg"], theme["bubble_user_fg"], "18px 18px 4px 18px"
        else:
            bg, fg, radius = theme["bubble_assistant_bg"], theme["bubble_assistant_fg"], "18px 18px 18px 4px"

        label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: {radius};
                padding: 10px 14px;
            }}
        """)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 4, 12, 4)
        if is_user:
            row.addStretch()
            row.addWidget(label)
        else:
            row.addWidget(label)
            row.addStretch()


class ChatArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 8, 0, 8)
        self._layout.setSpacing(6)
        self._layout.addStretch()
        self.setWidget(self._container)

    def add_bubble(self, text: str, is_user: bool, theme: dict):
        self._layout.insertWidget(self._layout.count() - 1, BubbleWidget(text, is_user, theme))
        QApplication.processEvents()
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def clear_bubbles(self):
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def apply_theme(self, theme: dict):
        self._container.setStyleSheet(f"background-color: {theme['chat_bg']};")
        self.setStyleSheet(f"""
            QScrollBar:vertical {{ background: transparent; width: 6px; }}
            QScrollBar::handle:vertical {{ background: {theme['scrollbar']}; border-radius: 3px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ollama Chat")
        self.resize(700, 800)
        self.setMinimumSize(500, 600)

        self._dark_mode = False
        self._busy = False
        self._workers = []
        self._attached_file = None
        self.history = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]

        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        # 頂部工具列
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 4)
        self.title_label = QLabel("Ollama Chat")
        self.title_label.setFont(QFont("Georgia", 15, QFont.Weight.Bold))
        self.theme_btn = QPushButton("暗色")
        self.theme_btn.setFixedSize(88, 32)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)
        top_bar.addWidget(self.title_label)
        top_bar.addStretch()
        top_bar.addWidget(self.theme_btn)

        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.HLine)
        self.divider.setFixedHeight(1)

        self.chat_area = ChatArea()

        self.input_edit = QTextEdit()
        self.input_edit.setFixedHeight(110)
        self.input_edit.setFont(QFont("Helvetica Neue", 13))
        self.input_edit.setPlaceholderText("輸入訊息⋯⋯（Enter 送出，Shift+Enter 換行）")
        self.input_edit.installEventFilter(self)

        self.file_label = QLabel("")
        self.file_label.setFont(QFont("Helvetica Neue", 11))
        self.file_label.setWordWrap(True)

        self.file_btn = QPushButton("附加檔案")
        self.file_btn.setFixedHeight(36)
        self.file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.file_btn.clicked.connect(self._attach_file)

        self.clear_btn = QPushButton("清除")
        self.clear_btn.setFixedSize(80, 36)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_chat)

        self.send_btn = QPushButton("送出")
        self.send_btn.setFixedSize(80, 36)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self.send_message)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(self.file_btn)
        btn_layout.addWidget(self.file_label, stretch=1)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.send_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        layout.addLayout(top_bar)
        layout.addWidget(self.divider)
        layout.addWidget(self.chat_area, stretch=1)
        layout.addWidget(self.input_edit)
        layout.addLayout(btn_layout)

        send_action = QAction(self)
        send_action.setShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Return))
        send_action.triggered.connect(self.send_message)
        self.addAction(send_action)

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self._apply_theme()

    def _apply_theme(self):
        ss = get_stylesheets(self._dark_mode)
        t  = get_theme(self._dark_mode)
        self.theme_btn.setText("亮色" if self._dark_mode else "暗色")
        self.setStyleSheet(ss["window"])
        self.input_edit.setStyleSheet(ss["input_edit"])
        self.send_btn.setStyleSheet(ss["send_btn"])
        self.clear_btn.setStyleSheet(ss["clear_btn"])
        self.file_btn.setStyleSheet(ss["file_btn"])
        self.theme_btn.setStyleSheet(ss["theme_btn"])
        self.title_label.setStyleSheet(ss["title_label"])
        self.divider.setStyleSheet(ss["divider"])
        self.file_label.setStyleSheet(ss["file_label"])
        self.chat_area.apply_theme(t)

    def eventFilter(self, obj, event):
        if obj is self.input_edit and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self.send_message()
                    return True
        return False

    def append_message(self, sender: str, text: str):
        t = get_theme(self._dark_mode)
        self.chat_area.add_bubble(text, is_user=(sender == "user"), theme=t)

    def _attach_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "選擇檔案", "",
            "所有檔案 (*);;文字檔案 (*.txt);;PDF (*.pdf);;圖片 (*.png *.jpg *.jpeg)"
        )
        if path:
            self._attached_file = path
            self.file_label.setText(path.replace("\\", "/").split("/")[-1])

    def send_message(self):
        if self._busy:
            return
        text = self.input_edit.toPlainText().strip()
        if not text:
            return

        display_text = text
        if self._attached_file:
            filename = self._attached_file.replace("\\", "/").split("/")[-1]
            display_text += f"\n[附加檔案：{filename}]"
            text += f"\n（使用者附加了檔案：{self._attached_file}）"

        self.append_message("user", display_text)
        self.history.append({"role": "user", "content": text})
        self.input_edit.clear()
        self._attached_file = None
        self.file_label.setText("")

        self._busy = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("⋯")

        worker = ChatWorker(self.history)
        self._workers.append(worker)
        worker.finished.connect(self.on_reply)
        worker.failed.connect(self.on_error)
        worker.finished.connect(lambda: self.cleanup(worker))
        worker.failed.connect(lambda: self.cleanup(worker))
        worker.start()

    def on_reply(self, reply):
        self.append_message("assistant", reply)
        self.history.append({"role": "assistant", "content": reply})

    def on_error(self, err):
        QMessageBox.warning(self, "錯誤", err)

    def cleanup(self, worker):
        worker.wait()
        if worker in self._workers:
            self._workers.remove(worker)
        self._busy = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText("送出")

    def clear_chat(self):
        self.chat_area.clear_bubbles()
        self._attached_file = None
        self.file_label.setText("")
        self.history = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]