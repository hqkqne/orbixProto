from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (QWidget, QMessageBox, QVBoxLayout, QDialog,
                             QDialogButtonBox, QFormLayout, QLineEdit, QTextEdit, QLabel, QPushButton, QHBoxLayout)
from PyQt6.QtWidgets.QWidget import layout

from ui.ui_task_page import Ui_Form as TaskPage
from ui.ui_task_create import Ui_Form as TaskCreate
from ui.ui_TaskItem import Ui_Form as Ui_TaskItem
from back_client import ApiWorker

class TaskItemWidget(QWidget, Ui_TaskItem):
    task_deleted = pyqtSignal()
    task_updated = pyqtSignal(dict)

    def __init__(self, task_data: dict, base_url: str, headers: dict):
        super().__init__()
        self.setupUi(self)
        self.base_url = base_url
        self.headers = headers
        self.task_id = task_data.get("id")
        self.task_data = task_data.copy()

        self.label.setText(task_data.get("title", "Без названия"))
        self.label_2.setText(f"Автор: {task_data.get('author', 'Unknown')}")
        self.label_4.setText(f"Дата: {task_data.get('created_at', 'N/A')}")
        self.label_3.setText(task_data.get("details", "Нет описания"))

        self.pushButton.clicked.connect(self.handle_edit)
        self.pushButton_2.clicked.connect(self.handle_delete)

    def handle_edit(self):
        dialog = TaskCreateDialog(self.base_url, self.headers, self.task_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_task = dialog.get_task_data()
            if updated_task:
                self.worker = ApiWorker("PUT", f"{self.base_url}/tasks/{self.task_id}",
                                        json_data = updated_task, headers= self.headers)
                self.worker.success.connect(lambda _:self.task_updated.emit(updated_task))
                self.worker.success.connect(self.accept)
                self.worker.error.connect(lambda err: QMessageBox.critical(self, "Ошибка", f"Не удалось обновить: {err}"))
                # self.worker.finished.connect(lambda: self)
                self.worker.start()

    def handle_delete(self):
        reply =  QMessageBox.question(self, "Подтверждение", "Удалить задачу?",
                                      QMessageBox.standardButton.Yes | QMessageBox.standardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._block_buttons(True)
            self.worker = ApiWorker("DELETE", f"{self.base_url}/tasks/{self.task_id}", headers = self.headers)
            self.worker.success.connect(lambda _:self.task_deleted.emit())
            self.worker.success.connect(lambda _: self.accept)
            self.worker.error.connect(lambda err: QMessageBox.critical(self, "Ошибка", f"Не удалось удалить: {err}"))
            self.worker.finished.connect(lambda: self._block_buttons(False))
            self.worker.start()

    def _block_buttons(self, state: bool):
        self.pushButton.setEnabled(not state)
        self.pushButton_2.setEnabled(not state)

class TaskListItemWidget(QWidget):
    clicked = pyqtSignal()

    def __init__(self, task_data: dict, base_url: str, headers: dict):
        super().__init__()
        self.task_data = task_data.copy()
        self.base_url = base_url
        self.headers = headers

        # клики на карточку
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setStyleSheet("""
            TaskItemWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
            TaskItemWidget:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        self.lbl_title = QLabel(task_data.get("title", "Без названия"))
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.lbl_autor = QLabel(f"{task_data.get('author', 'Unknown')}")
        self.lbl_autor.setStyleSheet("color: #64748b;")

        self.lbl_date = QLabel(f"{task_data.get('created_at', 'N/A')[:10]}")
        self.lbl_date.setStyleSheet('color: #64748b; margin-left: auto;')

        layout.addWidget(self.lbl_title, 2)
        layout.addWidget(self.lbl_autor, 1)
        layout.addWidget(self.lbl_date, 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child_under_cursor = self.childAt(event.pos())
            if child_under_cursor is None or not isinstance(child_under_cursor, QPushButton):
                self.clicked.emit(self.task_data)
                return
            super().mousePressEvent(event)

class TaskPageWidget(QWidget, TaskPage):
    def __init__(self, base_url: str, headers: dict, parent: QWidget = None):
        super().__init__(parent)
        self.setupUi(self)
        self.base_url = base_url
        self.headers = headers

        self.tasks_layout = QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.tasks_layout.setContentsMargins(5, 5, 5, 5)
        self.tasks_layout.setSpacing(10)
        self.tasks_layout.setSpacing(10)
        self.tasks_layout.addStretch()

        self.create_task_btn.clicked.connect(self.show_create_dialog)
        self.load_tasks()

    def show_create_dialog(self):
        dialog = TaskCreateDialog(self.base_url, self.headers)
        if dialog.exec()  == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            if task_data:
                self.create_task(task_data)

    def create_task(self, task_data: dict):
        self.create_task_btn.setEnabled(False)
        self.create_task_btn.setText("Создание...")
        self.worker = ApiWorker("POST", f"{self.base_url}/tasks", json_data= task_data, headers= self.headers)
        self.worker.success.connect(lambda _:self.load_tasks())
        self.worker.error.connect(lambda err:QMessageBox.critical(self, "Error", f"Не удалось создать задачу:{err}"))
        self.worker.finished.connect(lambda: self.create_task_btn.setEnabled(True))
        self.worker.start()

    def load_tasks(self):
        """Загрузка задачи с сервера"""
        self.clear_task()

        self.create_task_btn.setEnabled(False)
        self.create_task_btn.setText("Загрузка...")

        self.worker = ApiWorker("GET", f"{self.base_url}/tasks", headers= self.headers)
        self.worker.success.connect(self.render_tasks)
        self.worker.error.connect(self.on_load_error)
        self.worker.start()

    def on_load_error(self, error_msg: str):
        self.create_task_btn.setEnabled(True)
        self.create_task_btn.setText("Создать задачу")
        QMessageBox.critical(self,"Ошибка загрузки", error_msg)

    def clear_task(self):
        while self.tasks_layout.count() > 0:
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def render_tasks(self, task_data: dict):
        """Отображение списка задач"""
        self.create_task_btn.setEnabled(True)
        # self.create_task_btn.setText("Создать задачу")
        tasks = task_data if isinstance(task_data, list) else task_data.get("tasks", [])
        if not tasks:
            empty_label = QLabel("Нет задач")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_layout.addWidget(empty_label)
            return

        for task in tasks:
            item = TaskItemWidget(task, self.base_url, self.headers)
            item.clicked.connect(self.on_task_details)
            self.tasks_layout.addWidget(item)

    def on_task_details(self, task_data: dict):
        dialog = TaskItemWidget(task_data, self.base_url, self.headers)
        dialog.task_updated.connect(lambda _: self.load_tasks())
        dialog.task_deleted.conncet(lambda _: self.load_tasks())
        dialog.exec()

class TaskCreateDialog(QDialog, TaskCreate):
    def __init__(self, base_url:str, headers:dict, task_data: dict = None):
        super().__init__()
        self.setupUi(self)
        self.base_url = base_url
        self.headers = headers
        self.task_data = task_data
        self.is_edit = task_data is not None

        self.setWindowTitle("Редактировать задачу" if self.is_edit else "Создать задачу")
        self.setMinimumWidth(400)

        if self.is_edit:
            self.lineEdit.setText(task_data.get("title", ''))
            self.lineEdit_2.setText(task_data.get("description", ""))

        self.login_btn.clicked.connect(self.save_task)
        self.login_btn.setText("Сохранить" if self.is_edit else "Создать")

    def save_task(self):
        title = self.lineEdit.text().strip()
        description = self.lineEdit_2.text().strip()

        if not title:
            QMessageBox.warning(self, "Error","Заголовок обязателен")
            return

        self.task_data.update({"title": title, "description": description})
        self.accept()

    def get_task_data(self):
        return self.task_data