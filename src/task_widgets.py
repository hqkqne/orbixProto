from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QWidget, QMessageBox, QVBoxLayout, QDialog,
                             QDialogButtonBox, QFormLayout, QLineEdit, QTextEdit)
from ui.ui_task_page import Ui_Form as TaskPage
from ui.ui_task_create import Ui_Form as TaskCreate
from ui.ui_TaskItem import Ui_Form as Ui_TaskItem
from back_client import ApiWorker

class TaskItemWidget(QWidget, Ui_TaskItem):
    task_deleted = pyqtSignal()
    task_updated = pyqtSignal()

    def __init__(self, task_data: dict, base_url: str, headers: dict):
        super().__init__()
        self.setupUi(self)
        self.base_url = base_url
        self.headers = headers
        self.task_id = task_data.get("id")
        self.task_data = task_data

        self.label.setText(task_data.get("title", "Без названия"))
        self.label_2.setText(f"Автор: {task_data.get('author', 'Unknown')}")
        self.label_4.setText(f'Дата: {task_data.get('created_at', 'N/A')}')
        self.label_3.setText(task_data.get("details", "Нет описания"))

        self.pushButton.clicked.connect(self.handle_edit)
        self.pushButton_2.clicked.connect(self.handle_delete)

    def handle_edit(self):
        dialog = TaskCreateDialog(self.base_url, self.headers, self.task_data)
        if dialog.exec():
            updated_task = dialog.get_task_data()
            if updated_task:
                self.task_updated.emit(updated_task)

    def handle_delete(self):
        #через QMessageBox.question можно подтверждение
        self.pushButton_2.setEnabled(False)
        self.worker = ApiWorker("DELETE", f"{self.base_url}/tasks/{self.task_id}", headers = self.headers)
        self.worker.success.connect(lambda _:self.task_deleted.emit(self.task_id))
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Ошибка", err))
        self.worker.start()

class TaskPageWidget(QWidget, TaskPage):
    def __init__(self, base_url: str, headers: dict):
        super().__init__()
        self.setupUi(self)
        self.base_url = base_url
        self.headers = headers

        self.tasks_layout = QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.tasks_layout.setContentsMargins(5, 5, 5, 5)
        self.tasks_layout.setSpacing(10)
        self.tasks_layout.setSpacing(10)
        self.tasks_layout.addStretch()

        self.create_task_btn.connect(self.show_create_dialog)

    def show_create_dialog(self):
        dialog = TaskCreateDialog(self.base_url, self.headers)
        if dialog.exec():
            task_data = dialog.get_task_data()
            self.create_task(task_data)

    def create_task(self, task_data: dict):
        self.create_task_btn.setEnabled(False)
        self.worker = ApiWorker("POST", f"{self.base_url}/tasks", json_data= task_data, headers= self.headers)
        self.worker.success.connect(lambda _:self.load_tasks())
        self.worker.error.connect(lambda err:QMessageBox.critical(self, "Error", f"Не удалось создать задачу:{err}"))
        self.create_task_btn.setEnabled(True)
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
        for i in reversed(range(self.tasks_layout.count())):
            widget = self.tasks_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def render_tasks(self, task_data: dict):
        """Отображение списка задач"""
        self.create_task_btn.setEnabled(True)
        self.create_task_btn.setText("Создать задачу")
        tasks = task_data if isinstance(task_data, list) else task_data.get("tasks", [])
        if not tasks:
            empty_label = QWidget()
            layout = QVBoxLayout(empty_label)
            from PyQt6.QtWidgets import QLabel
            lbl = QLabel("Нет задач. Создайте первую задачу!")
            lbl.setAlignment(128)  # AlignCenter
            layout.addWidget(lbl)
            self.tasks_layout.addWidget(empty_label)
            return
        for task in tasks:
            item = TaskItemWidget(task, self.base_url, self.headers)
            item.task_deleted.connect(self.on_task_deleted)
            item.task_updated.connect(self.on_task_updated)
            self.tasks_layout.addWidget(item)
    def on_task_deleted(self, task_id: int):
        """Обработчик удаления задачи"""
        self.load_tasks()

    def on_task_updated(self, updated_task: dict):
        task_id = updated_task.get("id")
        self.worker = ApiWorker("PUT", f'{self.base_url}/tasks/{task_id}', json_data=updated_task, headers=self.headers)
        self.worker.success.connect(lambda _:self.load_tasks)

class TaskCreateDialog(QDialog, TaskCreate):
    def __init__(self, base_url:str, headers:dict, task_data: dict = None):
        super.__init__()
        self.base_url = base_url
        self.headers = headers
        self.task_data = task_data
        self.is_edit = task_data or not None

        self.setWindowTitle("Редактировать задачу" if self.is_edit else "Создать задачу")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)
        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()

        if self.is_edit:
            self.title_edit.setText(task_data.get("title", ""))
            self.description_edit.setText(task_data.get("description", ""))
        layout.addRow("Заголовок:", self.title_edit)
        layout.addRow("Описание:", self.description_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.standardButton.Cancel
        )
        buttons.accepted.connect(self.save_task)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def save_task(self):
        title = self.title_edit.text().strip()
        description = self.description_edit.toPlainText().strip()

        if not title:
            QMessageBox.warning(self, "Error","Заголовок обязателен")
            return

        self.task_data = {"title": title, "description": description}
        self.accept()

    def get_task_data(self):
        return self.task_data