import sys
from PyQt6.QtCore import QSize,Qt
from PyQt6.QtWidgets import (
QWidget,QApplication,QPushButton, QTextEdit, QMainWindow, QCheckBox, QTreeWidget
)

# class TaskWidget(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.ui = Ui_TaskWidget()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("application")
        self.setMinimumSize(QSize(400, 300))
        self.setMaximumSize(QSize(800,600))

        button = QPushButton('text')
        button.setCheckable(True)
        button.clicked.connect(self.the_button_was_clicked)
        button.clicked.connect(self.is_toggled)
        self.setCentralWidget(button)

    def the_button_was_clicked(button):
        print('Click!')
    def is_toggled(self, checked):
        print("click?", checked)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())