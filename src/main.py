import sys
from PyQt6.QtWidgets import QApplication
from auth_dialog import LoginDialog
from main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    BASE_URL = "http://127.0.0.1:8000"

    login_dlg = LoginDialog(BASE_URL)

    def on_login(token):
        main_window = MainWindow(token, BASE_URL)
        main_window.show()

    login_dlg.login_successful.connect(on_login)
    if login_dlg.exec():
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()