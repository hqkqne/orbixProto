import re
from PyQt6.QtWidgets import QDialog, QMessageBox, QLabel, QWidget, QVBoxLayout, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt, QLine
from src.back_client import ApiWorker, EmailCheckWorker
from ui.ui_login import Ui_Dialog as Ui_login
from ui.ui_reg import Ui_Dialog as Ui_reg

class LoginDialog(QDialog, Ui_login):
    login_successful = pyqtSignal(str)

    def __init__(self, base_url: str):
        super().__init__()
        self.setupUi(self)
        self.base_url = base_url
        self.main_window = None

        self.reg_btn.setText('<a href="register">Зарегистрироваться</a>')
        self.reg_btn.setStyleSheet("""
            QLabel { color: #1A1AFF; background: transparent; border: none; padding: 4px; }
            QLabel:hover { color: #005A9E; text-decoration: underline; }
            QLabel:pressed { color: #003F7F; }
        """)
        self.reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reg_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reg_btn.setOpenExternalLinks(False)

        self.login_btn.clicked.connect(self.handle_login)
        self.reg_btn.linkActivated.connect(lambda _: self.show_register())
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
        self.email = None
        self.enter_btn.clicked.connect(self.handle_register)
        self.comboBox.addItem("Заказчик", userData=1)
        self.comboBox.addItem("Исполнитель", userData=2)

        # self.password_edit.setEchoMode(QDialog.EchoMode.Password)

    def handle_register(self):
        username = self.login_edit.text().strip()
        email = self.mail_edit.text().strip()
        password = self.password_edit.text().strip()
        phone_number = self.phone_edit.text().strip()

        role_id = self.comboBox.currentData()
        role = "customer" if role_id == 1 else "volunteer"
        fields = [username, email, password, role, phone_number]
        if not all(fields):
            QMessageBox.warning(self, "Error", "Введите все поля!")
            return
        email_regex = r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            QMessageBox.warning(self, "Error", "Неверный формат email")
            return
        self.enter_btn.setEnabled(False)
        self.enter_btn.setText("Регистрация")
        self.email = email
        self.worker = ApiWorker(
            "POST",
            f"{self.base_url}/auth/register",
            json_data={
                "username": username,
                "email": email,
                "password": password,
                "phone_number": phone_number,
                "role": role
            }
        )
        self.worker.success.connect(self.on_reg_success)
        self.worker.error.connect(self.on_reg_error)
        self.worker.start()

    def on_reg_success(self):
        self.enter_btn.setEnabled(True)
        QMessageBox.information(self, "Success", "Подтвердите почту")
        self.start_email_polling()

    def start_email_polling(self):
        print("start_email_polling")
        self.email_worker = EmailCheckWorker(
            f"{self.base_url}/auth/verified",
            self.email,
            timeout=120,
            interval=4
        )
        self.email_worker.verification_success.connect(self.verify_phone)
        self.email_worker.verification_failed.connect(self.on_verification_failed)
        self.email_worker.start()

    #перегрузка для того чтобы не было утечек
    def reject(self):
        if hasattr(self, "email_worker") and self.email_worker.isRunning():
            self.email_worker.terminate()
            self.email_worker.wait()
        super().reject()

    def CloseEvent(self, event):
        self.reject()
        super().closeEvent(event)

    def on_verification_failed(self, msg):
        QMessageBox.warning(self, "Error", msg)
        self.reject()

    def verify_phone(self):
        self.phone_window = PhoneVerificationWindow(self.base_url, self.email)
        self.phone_window.verification_complete.connect(self.on_phone_verified)
        self.phone_window.request_code()
        self.phone_window.exec()

    def on_phone_verified(self):
        QMessageBox.information(self, "Success", "Пользователь зарегистрирован")
        self.accept()

    def on_reg_error(self, error_msg:str):
        self.enter_btn.setEnabled(True)
        self.enter_btn.setText("Зарегистрироваться")
        QMessageBox.warning(self, "Error registration", f"Не удалось зарегистрироваться{error_msg}")

class PhoneVerificationWindow(QDialog):
    verification_complete = pyqtSignal()
    def __init__(self, base_url: str, email: str, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Верификация телефона")
        self.resize(300, 150)
        self.base_url = base_url
        self.email = email
        self.expected_code = None

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Почта подтверждена! Подтверждение телефона"))

        self.mock_code = QLabel()
        self.mock_code.setStyleSheet("color: #0d6efd; font-weight: bold; background: #e7f1ff; padding: 8px; border-radius: 4px;")
        self.mock_code.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mock_code.hide()
        layout.addWidget(self.mock_code)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Пример: 111111")
        self.code_input.setMaxLength(6)
        self.code_input.setInputMethodHints(Qt.InputMethodHint.ImhDigitsOnly)
        self.code_input.returnPressed.connect(self.handle_verify)
        layout.addWidget(self.code_input)

        self.confirm_btn = QPushButton("Подтвердить")
        self.confirm_btn.clicked.connect(self.handle_verify)
        layout.addWidget(self.confirm_btn)

        self.setLayout(layout)

    def request_code(self):
        self.worker = ApiWorker("POST", f"{self.base_url}/auth/send-phone-code", json_data={"email":self.email})
        self.worker.success.connect(self.on_code_received)
        # self.worker.error.connect(lambda msg: QMessageBox.warning(self, "error", f"Не удалось получить код: {msg}"))
        self.worker.error.connect(self.on_code_request_error)
        self.worker.start()

    def on_code_request_error(self, msg: str):
        print(f"🔴 [send-phone-code] Ошибка: {msg}")
        QMessageBox.warning(self, "Ошибка", f"Не удалось получить код: {msg}")

    def on_code_received(self, data:dict):
        print(f"🟢 [send-phone-code] Ответ: {data}")
        code = data.get("verification_code")
        # if not code:
        #     QMessageBox.warning(self, "Ошибка", "Код не получен")
        #     return
        if code:
            self.expected_code = str(code)
            self.mock_code.setText(f"Код: {self.expected_code}")
            self.mock_code.show()
            self.mock_code.raise_()
            self.mock_code.activateWindow()
        self.code_input.setFocus()

    def handle_verify(self):
        entered_code = self.code_input.text().strip()
        if not entered_code:
            QMessageBox.warning(self, "Ошибка", "Введите код")
            return
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setText("Проверка...")

        self.worker = ApiWorker("POST", f"{self.base_url}/auth/verify-phone",
                                json_data={"email": self.email, "code": entered_code})
        self.worker.success.connect(self.on_phone_verified_success)
        self.worker.error.connect(self.on_phone_verified_error)
        self.worker.start()

    def on_phone_verified_success(self):
        print("Телефон подтврежден")
        self.verification_complete.emit()
        self.close()
    def on_phone_verified_error(self, msg: str):
        self.confirm_btn.setEnabled(True)
        self.confirm_btn.setText("Подтвердить")
        QMessageBox.warning(self, "Error", f"Код неверный или истек:{msg}")
        self.code_input.clear()
        self.code_input.setFocus()

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)