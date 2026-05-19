"""Captura un solo escenario por invocación (evita corromper Qt entre runs)."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow
from controller import Controller


def main() -> int:
    if len(sys.argv) < 4:
        print("Uso: python capturar_uno.py <archivo.acl> <pestana 0|1|2> <salida.png>")
        return 1

    archivo = Path(sys.argv[1])
    pestana = int(sys.argv[2])
    salida = Path(sys.argv[3])
    salida.parent.mkdir(parents=True, exist_ok=True)

    if not archivo.exists():
        print(f"[ERROR] No existe el archivo: {archivo}")
        return 2

    with open(archivo, "r", encoding="utf-8") as f:
        codigo = f.read()

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    controller = Controller(window)
    window.resize(1500, 920)
    window.show()
    app.processEvents()

    window.code_editor.setPlainText(codigo)
    app.processEvents()

    def _run():
        try:
            controller.on_analyze()
            app.processEvents()
            window.resultado_tabs.setCurrentIndex(pestana)
            app.processEvents()
        except Exception:
            traceback.print_exc()

        def _capture():
            try:
                pixmap = window.grab()
                pixmap.save(str(salida), "PNG")
                print(f"[OK] {salida}")
            except Exception:
                traceback.print_exc()
            QTimer.singleShot(150, app.quit)

        QTimer.singleShot(400, _capture)

    QTimer.singleShot(500, _run)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
