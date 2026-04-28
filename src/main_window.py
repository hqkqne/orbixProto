from PyQt6.QtWidgets import QMainWindow, QMessageBox

from src.task_widgets import TaskPageWidget
from ui.ui_main_window import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, token: str, base_url: str = "http://127.0.0.1:8000"):
        super().__init__()
        self.setupUi(self)
        self.base_url = base_url
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}

        self.task_page = TaskPageWidget(base_url, self.headers)
        self.stackedWidget.addWidget(self.task_page)

        self.task_btn.clicked.connect(
            lambda: self.stackedWidget.setCurrentWidget(self.task_page))
        #self.user_btn.clicked.connect() и др
        self.btn_logout.clicked.connect(self.logout)
        # self.btn_profile

    def logout(self):
        self.close()