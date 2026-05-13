from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (QWidget, QMessageBox, QVBoxLayout, QDialog,
                             QDialogButtonBox, QFormLayout, QLineEdit, QTextEdit, QLabel, QPushButton, QHBoxLayout)
from ui.ui_profile import Ui_Form as ProfilePageUI
from back_client import ApiWorker

class ProfileWidget(QDialog, ProfilePageUI):
    def __init__(self, base_url: str, headers: dict, parent: QWidget = None):
        super().__init__(parent)
        self.setupUi(self)
        self.base_url = base_url
        self.headers = headers
        # self.current_user_id = None

        self.history_layout = QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.history_layout.setContentsMargins(5, 5, 5, 5)
        self.history_layout.setSpacing(10)
        self._stretch_item = self.history_layout.addStretch()

        self.load_profile()

    def load_profile(self):
        self.setEnabled(False)
        self.worker = ApiWorker("GET", f"{self.base_url}/users/me", headers=self.headers)
        self.worker.success.connect(self.render_profile)
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить профиль: {err}"))
        self.worker.finished.conncet(lambda: self.worker.deleteLater())
        self.worker.start()

    def render_profile(self, data: dict):
        self.setEnabled(True)
        self.current_user_id = data.get("current_user_id")
        if not self.current_user_id:
            QMessageBox.critical(self, "Ошибка", "Не удалось найти пользователя")
            return
        self.name_lbl.setText(data.get("name", data.get("username", "Пользователь")))
        # self.location_lbl
        # self.description_lbl.setText(data.get("", ))
        self.load_avatar()

        if self.current_user_id:
            self.load_history(self.current_user_id)

    def load_history(self, user_id: str):
        self.clear_history()
        self.worker = ApiWorker("GET", f"{self.base_url}/users/{user_id}", headers=self.headers)
        self.worker.success(self.render_history)
        self.worker.error.connect(
            lambda err: QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить историю: {err}"))
        self.worker.finished.conncet(lambda: self.worker.deleteLater())
        self.worker.start()

    def render_history(self, data: dict):
        items = data if isinstance(data, list) else data.get()
        if not items:
            empty = QLabel("История заказов пуста")
            self.history_layout.addWidget(empty)
        for item in items:
            title = item.get("title", "...")
            date = item.get("date", item.get("created_at", "N/A"))[:10]
            status = item.get("status", "in progress")
            card = QLabel(f"<b>{date}<b> - {title}")
            card.setStyleSheet("""
                padding: 10px;    
            """)
            self.history_layout.addWidget(card)

    def clear_history(self):
        while self.history_layout.count() >0:
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.history_layout.addStretch()

    def load_avatar(self,url: str|None):
        if not url:
            self.image.setText("image")
            self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return
        ...