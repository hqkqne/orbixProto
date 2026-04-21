from PyQt6.QtWidgets import QMainWindow, QWidget, QMessageBox
from ui.ui_main_window import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, token: str, base_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.setupUi(self)
        self.base_url = base_url
        self.headers = {"Auth": f"Bearer {token}"}

        ...
