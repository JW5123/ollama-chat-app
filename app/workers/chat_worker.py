from PyQt6.QtCore import QThread, pyqtSignal
from app.services.chat_service import ChatService

class ChatWorker(QThread):
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, history):
        super().__init__()
        self.history = history
        self.service = ChatService()

    def run(self):
        try:
            reply = self.service.chat(self.history)
            self.finished.emit(reply)
        except Exception as e:
            self.failed.emit(str(e))