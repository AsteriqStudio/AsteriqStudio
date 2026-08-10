import sys

from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from src.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Apply a professional dark theme
    apply_stylesheet(app, theme="dark_teal.xml")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()