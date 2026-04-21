from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
from ui.ui_login import Ui_Dialog as Ui_login
from ui.ui_reg import Ui_Dialog as Ui_reg

class LoginDialog(QDialog, Ui_login):
    login_successful = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.login_btn.clicked.connect(self.handle_login)
        self.reg_btn.mousePressEvent = lambda e: self.show_register()
        #визуально отличимая
        self.reg_btn.setStyleSheet("color: #0078D4; text_decoration: underline; cursor: pointer;")

    def handle_login(self):
        email = self.email_edit.text().strip()
        pwd = self.password_edit.text().strip()
        if not email or not pwd:
            QMessageBox.warning(self,"error", "login and password are required")
            return
        self.login_successful.emit(email)
        self.accept()

    def show_register(self, event = None):
        reg = RegDialog()
        reg.exec()

class RegDialog(QDialog, Ui_reg):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.login_btn.clicked.connect(self.handle_register)

    def handle_register(self):
        if not self.email_edit.text().strip() or not self.password_edit.text():
            QMessageBox.warning(self, "Error", "Заполните все поля")
            return
        QMessageBox.information(self, "Align", "Аккаунт создан!")
        self.accept()
