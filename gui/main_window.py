from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout,
    QHBoxLayout, QToolBar, QStatusBar, QLabel,
    QFileDialog, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QAction

from gui.code_editor import CodeEditor
from gui.token_table import TokenTable, ErrorPanel


class MainWindow(QMainWindow):
    """Ventana principal del Analizador Léxico de Control de Accesos."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analizador Léxico — Control de Accesos Empresarial")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        self._build_ui()
        self._build_toolbar()
        self._build_statusbar()
        self._apply_styles()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(8, 4, 8, 8)
        root_layout.setSpacing(4)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(6)

        left_frame = QFrame()
        left_frame.setObjectName("panelFrame")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        left_header = self._make_panel_header("📝  Editor de Código  (.acl)")
        self.code_editor = CodeEditor()

        left_layout.addWidget(left_header)
        left_layout.addWidget(self.code_editor)

        right_frame = QFrame()
        right_frame.setObjectName("panelFrame")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        right_header = self._make_panel_header("🔍  Tokens Identificados")
        self.token_table = TokenTable()

        error_header = self._make_panel_header("⚠️  Errores Léxicos", accent=True)
        self.error_panel = ErrorPanel()
        self.error_panel.setMaximumHeight(160)

        right_layout.addWidget(right_header)
        right_layout.addWidget(self.token_table, stretch=1)
        right_layout.addWidget(error_header)
        right_layout.addWidget(self.error_panel)

        self.splitter.addWidget(left_frame)
        self.splitter.addWidget(right_frame)

        self.splitter.setSizes([780, 520])
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)

        root_layout.addWidget(self.splitter)

    def _make_panel_header(self, title: str, accent: bool = False) -> QLabel:
        label = QLabel(title)
        label.setObjectName("errorHeader" if accent else "panelHeader")
        label.setFixedHeight(32)
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        label.setContentsMargins(12, 0, 0, 0)
        return label

    def _build_toolbar(self):
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setObjectName("mainToolbar")
        self.addToolBar(toolbar)

        self.action_analyze = QAction("▶  Analizar", self)
        self.action_analyze.setToolTip("Ejecutar análisis léxico  (Ctrl+Return)")
        self.action_analyze.setShortcut("Ctrl+Return")
        self.action_analyze.setObjectName("btnAnalyze")
        toolbar.addAction(self.action_analyze)

        toolbar.addSeparator()

        self.action_clear = QAction("✕  Limpiar", self)
        self.action_clear.setToolTip("Borrar editor y resultados  (Ctrl+L)")
        self.action_clear.setShortcut("Ctrl+L")
        toolbar.addAction(self.action_clear)

        toolbar.addSeparator()

        self.action_open = QAction("📂  Cargar archivo", self)
        self.action_open.setToolTip("Abrir archivo .acl  (Ctrl+O)")
        self.action_open.setShortcut("Ctrl+O")
        toolbar.addAction(self.action_open)

        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        toolbar.addWidget(spacer)

        self.lbl_lang = QLabel("Control de Accesos Empresarial  v1.0")
        self.lbl_lang.setObjectName("lblLang")
        toolbar.addWidget(self.lbl_lang)

        self.action_clear.triggered.connect(self._on_clear)
        self.action_open.triggered.connect(self._on_open_file)

    def _build_statusbar(self):
        self.statusBar().setObjectName("statusBar")

        self.lbl_tokens = QLabel("Tokens: 0")
        self.lbl_errors = QLabel("Errores: 0")
        self.lbl_cursor = QLabel("Ln 1, Col 1")

        for lbl in (self.lbl_tokens, self.lbl_errors, self.lbl_cursor):
            lbl.setContentsMargins(8, 0, 8, 0)

        self.statusBar().addWidget(self.lbl_tokens)
        self.statusBar().addWidget(self._separator())
        self.statusBar().addWidget(self.lbl_errors)
        self.statusBar().addPermanentWidget(self.lbl_cursor)

        self.code_editor.cursorPositionChanged.connect(self._update_cursor_label)

    def get_code(self) -> str:
        return self.code_editor.toPlainText()

    def show_results(self, tokens: list, errors: list):
        self.token_table.populate(tokens)
        self.error_panel.populate(errors)
        self.lbl_tokens.setText(f"Tokens: {len(tokens)}")
        self.lbl_errors.setText(f"Errores: {len(errors)}")

        if errors:
            self.statusBar().showMessage(
                f"Análisis completado — {len(errors)} error(es) léxico(s) encontrado(s).",
                6000
            )
        else:
            self.statusBar().showMessage(
                f"Análisis completado — {len(tokens)} token(s) reconocido(s) sin errores.",
                4000
            )

    def navigate_to_line(self, line: int):
        self.code_editor.go_to_line(line)

    def _on_clear(self):
        self.code_editor.clear()
        self.token_table.clear_table()
        self.error_panel.clear_panel()
        self.lbl_tokens.setText("Tokens: 0")
        self.lbl_errors.setText("Errores: 0")
        self.statusBar().showMessage("Editor y resultados limpiados.", 3000)

    def _on_open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir archivo de Control de Accesos",
            "",
            "Archivos ACL (*.acl);;Archivos de texto (*.txt);;Todos (*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.code_editor.setPlainText(f.read())
                self.statusBar().showMessage(f"Archivo cargado: {path}", 4000)
            except Exception as e:
                self.statusBar().showMessage(f"Error al abrir el archivo: {e}", 5000)

    def _update_cursor_label(self):
        cursor = self.code_editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.lbl_cursor.setText(f"Ln {line}, Col {col}")

    def _separator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        return sep

    def _apply_styles(self):
        self.setStyleSheet("""
            /* ── Variables globales ── */
            QMainWindow, QWidget {
                background-color: #0f1117;
                color: #e2e8f0;
                font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
                font-size: 13px;
            }

            /* ── Toolbar ── */
            QToolBar#mainToolbar {
                background-color: #1a1d27;
                border-bottom: 1px solid #2d3148;
                padding: 4px 8px;
                spacing: 4px;
            }
            QToolBar#mainToolbar QToolButton {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid transparent;
                border-radius: 6px;
                padding: 5px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QToolBar#mainToolbar QToolButton:hover {
                background-color: #252a3d;
                color: #e2e8f0;
                border-color: #3d4466;
            }
            QToolBar#mainToolbar QToolButton[objectName="btnAnalyze"] {
                background-color: #3b5bdb;
                color: #ffffff;
                border-color: #4c6ef5;
                font-weight: 600;
            }
            QToolBar#mainToolbar QToolButton[objectName="btnAnalyze"]:hover {
                background-color: #4c6ef5;
            }
            QToolBar#mainToolbar QToolButton[objectName="btnAnalyze"]:pressed {
                background-color: #2f4dc4;
            }
            QLabel#lblLang {
                color: #4a5568;
                font-size: 11px;
                padding-right: 8px;
            }
            QToolBar::separator {
                background-color: #2d3148;
                width: 1px;
                margin: 6px 4px;
            }

            /* ── Paneles ── */
            QFrame#panelFrame {
                background-color: #0f1117;
                border: 1px solid #1e2235;
                border-radius: 8px;
            }
            QLabel#panelHeader {
                background-color: #1a1d27;
                color: #7c8db5;
                border-bottom: 1px solid #1e2235;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
            QLabel#errorHeader {
                background-color: #1a1520;
                color: #c084fc;
                border-bottom: 1px solid #2d1f3d;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }

            /* ── Splitter ── */
            QSplitter::handle {
                background-color: #1e2235;
                width: 4px;
                margin: 0 2px;
            }
            QSplitter::handle:hover {
                background-color: #3b5bdb;
            }

            /* ── Statusbar ── */
            QStatusBar {
                background-color: #1a1d27;
                border-top: 1px solid #2d3148;
                color: #4a5568;
                font-size: 11px;
                padding: 2px 0;
            }
            QStatusBar QLabel {
                color: #64748b;
                font-size: 11px;
            }
            QFrame[frameShape="5"] {   /* VLine */
                color: #2d3148;
                margin: 4px 0;
            }

            /* ── Scrollbars globales ── */
            QScrollBar:vertical {
                background: #0f1117;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #2d3148;
                border-radius: 5px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover { background: #3d4466; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal {
                background: #0f1117;
                height: 10px;
            }
            QScrollBar::handle:horizontal {
                background: #2d3148;
                border-radius: 5px;
                min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover { background: #3d4466; }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal { width: 0; }

            /* ── Menú de archivo ── */
            QFileDialog {
                background-color: #1a1d27;
                color: #e2e8f0;
            }
        """)