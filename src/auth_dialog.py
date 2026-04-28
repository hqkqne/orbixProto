import re
from PyQt6.QtWidgets import QDialog, QMessageBox, QLabel
from PyQt6.QtCore import pyqtSignal
from src.back_client import ApiWorker
from ui.ui_login import Ui_Dialog as Ui_login
from ui.ui_reg import Ui_Dialog as Ui_reg

class LoginDialog(QDialog, Ui_login):
    login_successful = pyqtSignal(str)

    def __init__(self, base_url: str):
        super().__init__()
        self.setupUi(self)
        self.base_url = base_url
        self.reg_btn = ClickableLabel()
        self.reg_btn.setStyleSheet("color: #0078D4; text_decoration: underline;")#визуально отличимая
        self.reg_btn.setParent(self)

        self.login_btn.clicked.connect(self.handle_login)
        self.reg_btn.clicked.connect(self.show_register)
        self.email_edit.returnPressed.connect(self.handle_login)
        self.password_edit.returnPressed.connect(self.handle_login)

        # self.password_edit.setEchoMode(QDialog.EchoMode.Password)

    def handle_login(self):
        email = self.email_edit.text().strip()
        pwd = self.password_edit.text().strip()
        if not email or not pwd:
            QMessageBox.warning(self,"error", "login and password are required")
            return
        self.login_btn.setEnabled(False)
        self.login_btn.setText('Вход')
        self.worker = ApiWorker(
            "POST",
            f"{self.base_url}/auth/login",
            json_data= {"email":email, "password": pwd}
        )
        self.worker.success.connect(self.on_login_success)
        self.worker.error.connect(self.on_login_error)
        self.worker.start()

    def on_login_success(self, data: dict):
        token = data.get("access_token")
        if token:
            self.login_successful.emit(token)
            self.show()
        else:
            QMessageBox.warning(self,"Error", "Не получен токен")

    def on_user_logout(self):
        self.main_window = None
        self.show()
        self.email_edit.clear()
        self.password_edit.clear()

    def on_login_error(self, error_msg: str):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Войти")
        QMessageBox.warning(self, "Error", f"Не удалось войти:{error_msg}")

    def show_register(self, event = None):
        reg_dialog = RegDialog(self.base_url)
        reg_dialog.exec()

class RegDialog(QDialog, Ui_reg):
    def __init__(self, base_url: str):
        super().__init__()
        self.setupUi(self)
        self.base_url = base_url
        self.enter_btn.clicked.connect(self.handle_register)

        # self.password_edit.setEchoMode(QDialog.EchoMode.Password)

    def handle_register(self):
        username = self.login_edit.text().strip()
        email = self.email_edit.text().strip()
        password = self.password_edit.text().strip()
        double_password = self.dbl_pwd_edit.text().strip()#я забыл про него. пока повесит

        if not username or not email or not password:
            QMessageBox.warning(self, "Error", "Введите все поля!")
            return
        email_regex = r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            QMessageBox.warning(self, "Error", "Неверный формат email")
            return
        self.enter_btn.setEnabled(False)
        self.enter_btn.setText("Регистрация")

        self.worker = ApiWorker(
            "POST",
            f"{self.base_url}/auth/register",
            json_data={"username": username, "email": email, "password": password}
        )
        self.worker.success.connect(self.on_reg_success)
        self.worker.error.connect(self.on_reg_error)
        self.worker.start()

    def on_reg_success(self, data: dict):
        QMessageBox.information(self, "Success", "Аккаунт успешно создан")
        self.accept()

    def on_reg_error(self, error_msg:str):
        self.enter_btn.setEnabled(True)
        self.enter_btn.setText("Зарегистрироваться")
        QMessageBox.warning(self, "Error registration", f"Не удалось зарегистрироваться{error_msg}")

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
