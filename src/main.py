import sys
from PyQt6.QtWidgets import QApplication
from auth_dialog import LoginDialog
from main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    BASE_URL = "http://127.0.0.1:8000"

    login_dlg = LoginDialog(BASE_URL)
    app.main_window = None

    def on_login(token):
        app.main_window = MainWindow(token, BASE_URL)
        app.main_window.logout_requested.connect(on_logout)
        login_dlg.hide()
        app.main_window.show()

    def on_logout():
        if app.main_window:
            app.main_window.close()
            app.main_window = None

            login_dlg.show()
            login_dlg.email_edit.clear()
            login_dlg.password_edit.clear()

    login_dlg.login_successful.connect(on_login)
    if login_dlg.exec():
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()