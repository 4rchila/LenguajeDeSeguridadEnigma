import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase
from gui.main_window import MainWindow
from controller import Controller


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Compilador — Control de Accesos")
    app.setOrganizationName("Universidad")

    window = MainWindow()
    controller = Controller(window)
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()