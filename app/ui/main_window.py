import re
import json
import uuid
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import (
    QAction, QKeySequence, QFont, QTextOption,
    QSyntaxHighlighter, QTextCharFormat, QColor
)
from PyQt6.QtWidgets import (
    QWidget, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox,
    QFileDialog, QLabel, QFrame,
    QScrollArea, QSizePolicy, QApplication, QComboBox,
    QPlainTextEdit
)

from app.config import DEFAULT_SYSTEM_PROMPT, AVAILABLE_MODELS
from app.workers.chat_worker import ChatWorker
from app.ui.themes import get_stylesheets

FONT_TITLE = QFont("Microsoft JhengHei", 15, QFont.Weight.Bold)
FONT_BODY  = QFont("Microsoft JhengHei", 12)
FONT_SMALL = QFont("Microsoft JhengHei", 11)
FONT_TINY  = QFont("Microsoft JhengHei", 10)
FONT_CODE  = QFont("Consolas", 11)

_URL_RE = re.compile(r"(https?://[^\s\"'<>]+)")

HISTORY_DIR = Path.home() / ".ollama_chat" / "histories"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#569CD6"))

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6A9955"))

        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#B5CEA8"))

        self.rules = [
            (re.compile(r"\b\d+(\.\d+)?\b"), self.number_format),
            (re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format),
            (re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), self.string_format),
            (re.compile(r"#[^\n]*"), self.comment_format),
            (re.compile(r"//[^\n]*"), self.comment_format),
        ]

    def highlightBlock(self, text: str):
        default_format = QTextCharFormat()
        default_format.setForeground(QColor("#D4D4D4"))
        self.setFormat(0, len(text), default_format)

        for pattern, fmt in self.rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


def parse_message(text: str):
    pattern = re.compile(r"```(\w*)\n?(.*?)```", re.DOTALL)
    segments, last = [], 0
    for m in pattern.finditer(text):
        if m.start() > last and text[last:m.start()].strip():
            segments.append(("text", text[last:m.start()].strip(), ""))
        segments.append(("code", m.group(2), m.group(1).strip()))
        last = m.end()
    if last < len(text) and text[last:].strip():
        segments.append(("text", text[last:].strip(), ""))
    return segments


def simple_markdown(text: str, inline_code_style: str, link_color: str) -> str:
    text = re.sub(r"<(https?://[^\s>]+)>", r"\1", text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.+)$",  r"<h2>\1</h2>", text, flags=re.MULTILINE)
    text = re.sub(r"^# (.+)$",   r"<h1>\1</h1>", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", rf"<code style='{inline_code_style}'>\1</code>", text)
    text = re.sub(r"^[*-] (.+)$", r"• \1", text, flags=re.MULTILINE)
    text = _URL_RE.sub(
        rf'<a href="\1" style="color:{link_color};text-decoration:underline;">\1</a>',
        text
    )
    text = text.replace("\n", "<br>")
    return text

class ConversationStore:
    @staticmethod
    def save(conv_id: str, title: str, history: list):
        data = {
            "id": conv_id,
            "title": title,
            "updated_at": datetime.now().isoformat(),
            "history": history,
        }
        path = HISTORY_DIR / f"{conv_id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def load(conv_id: str) -> dict | None:
        path = HISTORY_DIR / f"{conv_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def delete(conv_id: str):
        path = HISTORY_DIR / f"{conv_id}.json"
        if path.exists():
            path.unlink()

    @staticmethod
    def list_all() -> list[dict]:
        # 回傳所有對話的 meta，依 updated_at 降冪排序
        result = []
        for p in HISTORY_DIR.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                result.append({
                    "id": data["id"],
                    "title": data.get("title", "未命名對話"),
                    "updated_at": data.get("updated_at", ""),
                })
            except Exception:
                pass
        result.sort(key=lambda x: x["updated_at"], reverse=True)
        return result

    @staticmethod
    def make_title(history: list) -> str:
        # 取第一則 user 訊息的前 20 字作為標題
        for msg in history:
            if msg["role"] == "user":
                content = msg["content"].strip().replace("\n", " ")
                return content[:20] + ("…" if len(content) > 20 else "")
        return "新對話"

class ConvItem(QWidget):
    def __init__(self, conv_id: str, title: str, updated_at: str,
                on_click, on_delete, ss: dict, parent=None):
        super().__init__(parent)
        self.conv_id = conv_id
        self._on_click = on_click
        self._on_delete = on_delete
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ss = ss
        self._selected = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 6, 4)
        layout.setSpacing(4)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)

        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(FONT_SMALL)
        self.title_lbl.setWordWrap(False)

        dt = updated_at[:16].replace("T", " ") if updated_at else ""
        self.date_lbl = QLabel(dt)
        self.date_lbl.setFont(FONT_TINY)

        text_col.addWidget(self.title_lbl)
        text_col.addWidget(self.date_lbl)

        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(22, 22)
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setVisible(False)
        self.del_btn.clicked.connect(lambda: self._on_delete(self.conv_id))

        layout.addLayout(text_col, stretch=1)
        layout.addWidget(self.del_btn)

        self._apply_style()

    def _apply_style(self):
        ss = self._ss
        bg = ss["sidebar_item_active"] if self._selected else ss["sidebar_item"]
        self.setStyleSheet(bg)
        self.title_lbl.setStyleSheet(ss["sidebar_item_title"])
        self.date_lbl.setStyleSheet(ss["sidebar_item_date"])
        self.del_btn.setStyleSheet(ss["sidebar_del_btn"])

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style()

    def enterEvent(self, e):
        self.del_btn.setVisible(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.del_btn.setVisible(False)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            # 若點擊位置在刪除按鈕上，讓事件繼續傳遞給按鈕，不觸發切換
            if self.del_btn.isVisible() and self.del_btn.geometry().contains(e.pos()):
                super().mousePressEvent(e)
                return
            self._on_click(self.conv_id)
        super().mousePressEvent(e)


# 側邊欄
class Sidebar(QWidget):
    def __init__(self, on_select, on_delete, on_new, ss: dict, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self._on_select = on_select
        self._on_delete = on_delete
        self._ss = ss
        self._items: dict[str, ConvItem] = {}
        self._active_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 新對話按鈕
        self.new_btn = QPushButton("＋ 新對話")
        self.new_btn.setFont(FONT_SMALL)
        self.new_btn.setFixedHeight(40)
        self.new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_btn.clicked.connect(on_new)
        layout.addWidget(self.new_btn)

        # 捲動區
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._list_layout.setSpacing(2)
        self._list_layout.addStretch()
        self._scroll.setWidget(self._list_widget)
        layout.addWidget(self._scroll, stretch=1)

        self.apply_theme(ss)

    def apply_theme(self, ss: dict):
        self._ss = ss
        self.setStyleSheet(ss["sidebar"])
        self.new_btn.setStyleSheet(ss["sidebar_new_btn"])
        self._scroll.setStyleSheet(ss["sidebar_scroll"])
        for item in self._items.values():
            item._ss = ss
            item._apply_style()

    def refresh(self, convs: list[dict]):
        for item in self._items.values():
            item.deleteLater()
        self._items.clear()
        while self._list_layout.count() > 1:
            self._list_layout.takeAt(0)

        for conv in convs:
            item = ConvItem(
                conv["id"], conv["title"], conv["updated_at"],
                self._on_select, self._on_delete, self._ss
            )
            if conv["id"] == self._active_id:
                item.set_selected(True)
            self._items[conv["id"]] = item
            self._list_layout.insertWidget(self._list_layout.count() - 1, item)

    def set_active(self, conv_id: str | None):
        for cid, item in self._items.items():
            item.set_selected(cid == conv_id)
        self._active_id = conv_id


# 訊息泡泡
class TextBubble(QWidget):
    def __init__(self, text: str, is_user: bool, ss: dict, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setMaximumWidth(700)
        self._ss = ss

        self._label = QLabel(simple_markdown(text, ss["inline_code_style"], ss["link_color"]))
        self._label.setWordWrap(True)
        self._label.setFont(FONT_BODY)
        self._label.setMaximumWidth(500)
        self._label.setTextFormat(Qt.TextFormat.RichText)
        self._label.setOpenExternalLinks(True)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard |
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self._label.setStyleSheet(ss["bubble_user"] if is_user else ss["bubble_assistant"])

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 2, 12, 2)
        if is_user:
            row.addStretch()
            row.addWidget(self._label)
        else:
            row.addWidget(self._label)
            row.addStretch()

    def update_text(self, text: str):
        self._label.setText(simple_markdown(text, self._ss["inline_code_style"], self._ss["link_color"]))
        self._label.setOpenExternalLinks(True)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard |
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )


class CodeBlock(QWidget):
    def __init__(self, code: str, lang: str, ss: dict, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._code = code
        self._ss = ss

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 4, 12, 4)

        container = QWidget()
        container.setStyleSheet(ss["code_container"])

        inner = QVBoxLayout(container)
        inner.setContentsMargins(0, 0, 0, 0)

        header = QWidget()
        header.setStyleSheet(ss["code_header_bar"])
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 6, 10, 6)

        lang_label = QLabel(lang if lang else "plaintext")
        lang_label.setFont(FONT_SMALL)
        lang_label.setStyleSheet(ss["code_lang_label"])

        self._copy_btn = QPushButton("複製")
        self._copy_btn.setFont(FONT_SMALL)
        self._copy_btn.setFixedHeight(26)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setStyleSheet(ss["code_copy_btn"])
        self._copy_btn.clicked.connect(self._copy_code)

        header_layout.addWidget(lang_label)
        header_layout.addStretch()
        header_layout.addWidget(self._copy_btn)
        inner.addWidget(header)

        self._code_edit = QPlainTextEdit()
        self._code_edit.setFont(FONT_CODE)
        self._code_edit.setReadOnly(True)
        self._code_edit.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self._code_edit.setFrameStyle(QFrame.Shape.NoFrame)
        self._code_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._code_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._code_edit.setStyleSheet(ss["code_edit"])

        self._highlighter = CodeHighlighter(self._code_edit.document())
        self._code_edit.setPlainText(code)

        block_count = self._code_edit.blockCount()
        line_height = self._code_edit.fontMetrics().lineSpacing()
        self._code_edit.setFixedHeight(block_count * line_height + 24)

        inner.addWidget(self._code_edit)
        outer.addWidget(container)

    def _copy_code(self):
        QApplication.clipboard().setText(self._code)
        self._copy_btn.setText("已複製")
        QTimer.singleShot(1500, lambda: self._copy_btn.setText("複製"))


# 聊天區
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
        self._layout.setSpacing(4)
        self._layout.addStretch()
        self.setWidget(self._container)

    def add_message(self, text: str, is_user: bool, ss: dict):
        for seg_type, content, lang in parse_message(text):
            if not content:
                continue
            widget = TextBubble(content, is_user, ss) if seg_type == "text" else CodeBlock(content, lang, ss)
            self._layout.insertWidget(self._layout.count() - 1, widget)
        QApplication.processEvents()
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def add_stream_bubble(self, ss: dict) -> TextBubble:
        bubble = TextBubble("", False, ss)
        self._layout.insertWidget(self._layout.count() - 1, bubble)
        return bubble

    def remove_widget(self, widget: QWidget):
        idx = self._layout.indexOf(widget)
        if idx >= 0:
            item = self._layout.takeAt(idx)
            if item.widget():
                item.widget().deleteLater()

    def clear_messages(self):
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def apply_theme(self, ss: dict):
        self._container.setStyleSheet(ss["chat_container"])
        self.setStyleSheet(ss["scrollbar"])

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ollama Chat")
        self.resize(920, 800)
        self.setMinimumSize(600, 600)

        self._dark_mode = False
        self._busy = False
        self._workers = []
        self._attached_file = None
        self._stream_bubble = None
        self._current_stream = ""

        # 當前對話
        self._conv_id: str | None = None
        self.history: list = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]

        self._build_ui()
        self._apply_theme()
        self._refresh_sidebar()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 側邊欄
        ss = get_stylesheets(self._dark_mode)
        self.sidebar = Sidebar(
            on_select=self._load_conversation,
            on_delete=self._delete_conversation,
            on_new=self.new_chat,
            ss=ss,
        )
        root.addWidget(self.sidebar)

        # 分隔線
        self._side_divider = QFrame()
        self._side_divider.setFrameShape(QFrame.Shape.VLine)
        self._side_divider.setFixedWidth(1)
        root.addWidget(self._side_divider)

        # 主區域
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(10)

        # 頂部
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.title_label = QLabel("Ollama Chat")
        self.title_label.setFont(FONT_TITLE)

        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        self.model_combo.setFixedHeight(32)
        self.model_combo.setMinimumWidth(150)
        self.model_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.model_combo.setFont(FONT_SMALL)
        self.model_combo.view().setFont(FONT_SMALL)

        self.theme_btn = QPushButton("暗色")
        self.theme_btn.setFixedSize(64, 32)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)

        top_bar.addWidget(self.title_label)
        top_bar.addStretch()
        top_bar.addWidget(self.model_combo)
        top_bar.addWidget(self.theme_btn)

        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.HLine)
        self.divider.setFixedHeight(1)

        self.chat_area = ChatArea()

        self.input_edit = QTextEdit()
        self.input_edit.setFixedHeight(110)
        self.input_edit.setFont(FONT_BODY)
        self.input_edit.setPlaceholderText("輸入訊息⋯⋯（Enter 送出，Shift+Enter 換行）")
        self.input_edit.installEventFilter(self)

        self.file_label = QLabel("")
        self.file_label.setFont(FONT_SMALL)
        self.file_label.setWordWrap(True)

        self.file_btn = QPushButton("附加檔案")
        self.file_btn.setFixedHeight(36)
        self.file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.file_btn.clicked.connect(self._attach_file)

        self.send_btn = QPushButton("送出")
        self.send_btn.setFixedSize(80, 36)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self.send_message)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(self.file_btn)
        btn_layout.addWidget(self.file_label, stretch=1)
        btn_layout.addWidget(self.send_btn)

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.divider)
        main_layout.addWidget(self.chat_area, stretch=1)
        main_layout.addWidget(self.input_edit)
        main_layout.addLayout(btn_layout)

        root.addWidget(main_widget, stretch=1)

        send_action = QAction(self)
        send_action.setShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Return))
        send_action.triggered.connect(self.send_message)
        self.addAction(send_action)

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self._apply_theme()

    def _apply_theme(self):
        ss = get_stylesheets(self._dark_mode)
        self.theme_btn.setText("亮色" if self._dark_mode else "暗色")
        self.setStyleSheet(ss["window"])
        self.input_edit.setStyleSheet(ss["input_edit"])
        self.send_btn.setStyleSheet(ss["send_btn"])
        self.file_btn.setStyleSheet(ss["file_btn"])
        self.theme_btn.setStyleSheet(ss["theme_btn"])
        self.title_label.setStyleSheet(ss["title_label"])
        self.divider.setStyleSheet(ss["divider"])
        self._side_divider.setStyleSheet(ss["divider"])
        self.file_label.setStyleSheet(ss["file_label"])
        self.model_combo.setStyleSheet(ss["model_combo"])
        self.chat_area.apply_theme(ss)
        self.sidebar.apply_theme(ss)

    def eventFilter(self, obj, event):
        if obj is self.input_edit and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self.send_message()
                    return True
        return False

    def append_message(self, sender: str, text: str):
        ss = get_stylesheets(self._dark_mode)
        self.chat_area.add_message(text, is_user=(sender == "user"), ss=ss)

    def _attach_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "選擇檔案", "",
            "所有檔案 (*);;文字檔案 (*.txt);;PDF (*.pdf);;圖片 (*.png *.jpg *.jpeg)"
        )
        if path:
            self._attached_file = path
            self.file_label.setText(path.replace("\\", "/").split("/")[-1])

    def _refresh_sidebar(self):
        convs = ConversationStore.list_all()
        self.sidebar.refresh(convs)
        self.sidebar.set_active(self._conv_id)

    def _save_current(self):
        msgs = [m for m in self.history if m["role"] != "system"]
        if not msgs:
            return
        if self._conv_id is None:
            self._conv_id = str(uuid.uuid4())
        title = ConversationStore.make_title(self.history)
        ConversationStore.save(self._conv_id, title, self.history)
        self._refresh_sidebar()

    def _load_conversation(self, conv_id: str):
        if self._busy:
            return

        data = ConversationStore.load(conv_id)
        if not data:
            return

        self._conv_id = conv_id
        self.history = data["history"]
        self.chat_area.clear_messages()

        ss = get_stylesheets(self._dark_mode)
        for msg in self.history:
            if msg["role"] == "system":
                continue
            self.chat_area.add_message(msg["content"], is_user=(msg["role"] == "user"), ss=ss)

        self.sidebar.set_active(conv_id)

    def _delete_conversation(self, conv_id: str):
        reply = QMessageBox.question(
            self, "刪除對話", "確定要刪除這則對話嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        ConversationStore.delete(conv_id)
        if self._conv_id == conv_id:
            self._conv_id = None
            self.history = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
            self.new_chat()
        else:
            self._refresh_sidebar()

    def new_chat(self):
        if self._busy:
            return

        self._conv_id = None
        self.history = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
        self.chat_area.clear_messages()
        self._stream_bubble = None
        self._current_stream = ""
        self._attached_file = None
        self.file_label.setText("")
        self.sidebar.set_active(None)
        self._refresh_sidebar()

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

        MAX_HISTORY = 12
        if len(self.history) > MAX_HISTORY + 1:
            self.history = [self.history[0]] + self.history[-MAX_HISTORY:]

        self.input_edit.clear()
        self._attached_file = None
        self.file_label.setText("")

        self._busy = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("⋯")

        selected_model = self.model_combo.currentText()
        worker = ChatWorker(self.history, selected_model)
        self._workers.append(worker)
        worker.finished.connect(self.on_reply)
        worker.failed.connect(self.on_error)
        worker.finished.connect(lambda: self.cleanup(worker))
        worker.failed.connect(lambda: self.cleanup(worker))
        worker.chunk_received.connect(self.on_stream_chunk)
        worker.start()

    def on_stream_chunk(self, chunk):
        if self._stream_bubble is None:
            self._current_stream = ""
            self._stream_bubble = self.chat_area.add_stream_bubble(get_stylesheets(self._dark_mode))

        self._current_stream += chunk
        self._stream_bubble.update_text(self._current_stream)
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

    def on_reply(self, reply):
        ss = get_stylesheets(self._dark_mode)
        if self._stream_bubble is not None:
            self.chat_area.remove_widget(self._stream_bubble)
            self._stream_bubble = None

        self.chat_area.add_message(reply, is_user=False, ss=ss)
        self.history.append({"role": "assistant", "content": reply})
        self._current_stream = ""

        self._save_current()

    def on_error(self, err):
        QMessageBox.warning(self, "錯誤", err)

    def cleanup(self, worker):
        worker.wait()
        if worker in self._workers:
            self._workers.remove(worker)
        self._busy = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText("送出")