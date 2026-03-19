from PyQt6.QtCore import QTimer

from gui.main_window import MainWindow
from lexer.lexer import Lexer


class Controller:
    """
    Mediador entre la GUI y el lexer.
    Al presionar Analizar: obtiene el texto del editor, llama a lexer.tokenize()
    y actualiza la tabla de tokens y el panel de errores con los resultados.
    Subrayado en vivo (Error Lens): al escribir, se analiza con debounce y se
    marcan los errores léxicos en rojo en el editor.
    """

    DEBOUNCE_MS = 450  # ms de espera tras dejar de escribir para actualizar subrayados

    def __init__(self, window: MainWindow):
        self.window = window
        self.lexer = Lexer()
        self._live_timer = QTimer(self.window)
        self._live_timer.setSingleShot(True)
        self._live_timer.timeout.connect(self._update_live_errors)
        self._connect_signals()

    def _connect_signals(self):
        self.window.action_analyze.triggered.connect(self.on_analyze)
        self.window.error_panel.navigate_to_line.connect(self.window.navigate_to_line)
        self.window.code_editor.textChanged.connect(self._on_text_changed)

    def on_analyze(self):
        code = self.window.get_code().strip()
        if not code:
            self.window.statusBar().showMessage(
                "El editor está vacío. Escribe código para analizar.", 3000
            )
            return

        try:
            tokens = self.lexer.tokenize(code)
            errors = self.lexer.errores.obtener_errores()
            self.window.show_results(tokens, errors)
        except Exception as exc:
            self.window.statusBar().showMessage(
                f"Error inesperado durante el análisis: {exc}", 6000
            )

    def _on_text_changed(self):
        """Reinicia el timer para actualizar subrayados de errores al dejar de escribir."""
        self._live_timer.stop()
        self._live_timer.start(self.DEBOUNCE_MS)

    def _update_live_errors(self):
        """Ejecuta el lexer sobre el código actual y subraya errores en el editor (Error Lens)."""
        code = self.window.get_code()
        if not code.strip():
            self.window.code_editor.set_lexical_errors([])
            return
        try:
            self.lexer.tokenize(code)
            errors = self.lexer.errores.obtener_errores()
            self.window.code_editor.set_lexical_errors(errors)
        except Exception:
            self.window.code_editor.set_lexical_errors([])
