from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
)


class QueueWidget(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Generation Queue"))

        self.queue = QListWidget()

        layout.addWidget(self.queue)

        self.setLayout(layout)

    def add_task(self, task):

        self.queue.addItem(
            f"{task.name} ({task.status.value})"
        )

    def update_task(self, task):

        for i in range(self.queue.count()):

            item = self.queue.item(i)

            if item.text().startswith(task.name):

                item.setText(
                    f"{task.name} ({task.status.value})"
                )