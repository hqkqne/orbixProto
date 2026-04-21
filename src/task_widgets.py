from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QMessageBox, QVBoxLayout
from ui.ui_task_page import Ui_Form as TaskPage
from ui.ui_task_create import Ui_Form as Ui_TaskCreate
from ui.ui_TaskItem import Ui_Form as Ui_TaskItem
from back_client import ApiWorker

class TaskItemWidget(QWidget, Ui_TaskItem):
    edit_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()

    def __init__(self, task_data: dict, base_url: str, headers: dict):
        super().__init__()
        self.setupUi(self)
        self.base_url = base_url
        self.headers = headers
        self.task_id = task_data.get("id")

        self.label.setText(task_data.get("title", "Без названия"))
        self.label_2.setText(f"Автор: {task_data.get('author', 'Unknown')}")
        self.label_4.setText(f'Дата: {task_data.get('created_at', 'N/A')}')
        self.label_3.setText(task_data.get("details", "Нет описания"))

        self.pushButton.clicked.connect(self.edit_clicked.emit)
        self.pushButton_2.clicked.connect(self.handle_delete)

    def handle_delete(self):
        self.pushButton_2.setEnabled(False)
        self.worker = ApiWorker("DELETE", f"{self.base_url}/tasks/{self.task_id}", headers = self.headers)
        self.worker.success.connect(lambda _:self.delete_clicked.emit())
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Ошибка", err))
        self.worker.start()

class TaskPage(QWidget, TaskPage):
    open_create_dialog = pyqtSignal()
    def __init__(self, base_url: str, headers: dict):
        super().__init__()
        self.setupUi(self)
        self.base_url = base_url
        self.headers = headers

        self.content_layout = QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(10)
        self.content_layout.addStretch()

        self.create_task_btn.connect(self.open_create_dialog.emit)
        self.load_tasks()

    def load_tasks(self):
        self.create_task_btn.setEnabled(False)
        self.worker = ApiWorker("GET", f"{self.base_url}/tasks", headers= self.headers)
        self.worker.success.connect(self.render_tasks)
        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Ошибка загрузки", err))
        self.worker.start()

    def render_tasks(self, tasks_list: list):
        self.create_task_btn.setEnabled(True)
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for task in tasks_list:
            item = TaskItemWidget(task, self.base_url, self.headers)
            item.delete_clicked.connect(self.load_tasks())
            self.content_layout.insertWidget(self.content_layout.count() -1, item)

