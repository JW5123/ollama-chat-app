from PyQt6.QtCore import QThread, pyqtSignal
from app.services.chat_service import ChatService

class ChatWorker(QThread):
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, history, model: str = None):
        super().__init__()
        self.history = history
        self.model = model
        self.service = ChatService()

    def run(self):
        try:
            full_reply = ""
            for chunk in self.service.chat_stream(self.history, model=self.model):
                full_reply += chunk
                self.chunk_received.emit(chunk)
            self.finished.emit(full_reply)
        except Exception as e:
            self.failed.emit(str(e))