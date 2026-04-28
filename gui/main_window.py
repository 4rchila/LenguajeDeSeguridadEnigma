from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout,
    QHBoxLayout, QToolBar, QStatusBar, QLabel,
    QFileDialog, QFrame, QSizePolicy, QTabWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QAction, QPixmap

from gui.code_editor import CodeEditor
from gui.token_table import TokenTable, ErrorPanel
from gui.ast_graph_widget import AstGraphWidget
from gui.symbol_table_widget import SymbolTableWidget
from gui.icons import Icons


class MainWindow(QMainWindow):
    """Ventana principal del Compilador de Control de Accesos."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ENIGMA")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

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

        left_header = self._make_panel_header("Editor de Código  ·  .acl",
                                               icon=Icons.code("#0ea5e9", 14))
        self.code_editor = CodeEditor()

        left_layout.addWidget(left_header)
        left_layout.addWidget(self.code_editor)

        right_frame = QFrame()
        right_frame.setObjectName("panelFrame")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.resultado_tabs = QTabWidget()
        self.resultado_tabs.setObjectName("resultadoTabs")
        self.token_table = TokenTable()
        self.ast_graph = AstGraphWidget()
        self.symbol_table_widget = SymbolTableWidget()

        TAB_ICON_COLOR = "#94a3b8"
        self.resultado_tabs.setIconSize(QSize(16, 16))
        self.resultado_tabs.addTab(self.token_table,         "Tokens")
        self.resultado_tabs.addTab(self.ast_graph,           "Árbol Sintáctico")
        self.resultado_tabs.addTab(self.symbol_table_widget, "Tabla de Símbolos")

        # Contenedor del panel de errores (header + tabla) para ocultar/mostrar como unidad
        self.error_container = QFrame()
        self.error_container.setObjectName("panelFrame")
        error_container_layout = QVBoxLayout(self.error_container)
        error_container_layout.setContentsMargins(0, 0, 0, 0)
        error_container_layout.setSpacing(0)
        self.error_header = self._make_panel_header("Errores",
                                                     accent=True,
                                                     icon=Icons.alert("#fb7185", 14))
        self.error_panel = ErrorPanel()
        error_container_layout.addWidget(self.error_header)
        error_container_layout.addWidget(self.error_panel)

        # Ocultar panel de errores por defecto
        self.error_container.setVisible(False)

        # Splitter vertical derecho: tabs arriba, errores abajo (redimensionable)
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.right_splitter.setHandleWidth(6)
        self.right_splitter.setObjectName("rightSplitter")
        self.right_splitter.addWidget(self.resultado_tabs)
        self.right_splitter.addWidget(self.error_container)
        self.right_splitter.setStretchFactor(0, 3)
        self.right_splitter.setStretchFactor(1, 1)

        right_frame = QFrame()
        right_frame.setObjectName("panelFrame")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self.right_splitter)

        self.splitter.addWidget(left_frame)
        self.splitter.addWidget(right_frame)

        # 50/50 por defecto, ambos con el mismo factor de estiramiento
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        root_layout.addWidget(self.splitter)

    def _make_panel_header(self, title: str, accent: bool = False,
                            icon: QIcon = None) -> QWidget:
        """Encabezado con ícono opcional + título — sin emojis."""
        wrap = QWidget()
        wrap.setObjectName("errorHeader" if accent else "panelHeader")
        wrap.setFixedHeight(32)
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        if icon is not None:
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(QSize(14, 14)))
            icon_label.setFixedSize(14, 14)
            layout.addWidget(icon_label)

        text_label = QLabel(title)
        text_label.setObjectName("panelHeaderText")
        layout.addWidget(text_label)
        layout.addStretch()
        return wrap

    def _build_toolbar(self):
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setObjectName("mainToolbar")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        # Logo en la esquina superior izquierda
        self.lbl_logo = QLabel()
        logo_pixmap = QPixmap("Logo ENIGMA.png").scaled(
            150, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.lbl_logo.setPixmap(logo_pixmap)
        self.lbl_logo.setContentsMargins(8, 0, 16, 0)
        toolbar.addWidget(self.lbl_logo)

        # Análisis rápido
        self.action_analyze = QAction("Analizar Rápido", self)
        self.action_analyze.setToolTip("Ejecutar análisis instantáneo (Ctrl+Enter)")
        self.action_analyze.setShortcut("Ctrl+Return")
        self.action_analyze.setObjectName("btnAnalyze")
        toolbar.addAction(self.action_analyze)

        toolbar.addSeparator()

        # Modo didáctico
        self.action_analyze_step = QAction("Modo Didáctico", self)
        self.action_analyze_step.setToolTip("Analizar paso a paso (F10)")
        self.action_analyze_step.setShortcut("F10")
        self.action_analyze_step.setObjectName("btnDidactic")
        toolbar.addAction(self.action_analyze_step)

        self.action_pause = QAction("Pausa", self)
        self.action_pause.setToolTip("Pausar / Continuar animación (Espacio)")
        self.action_pause.setShortcut("Space")
        self.action_pause.setVisible(False)
        self.action_pause.setObjectName("btnPause")
        toolbar.addAction(self.action_pause)

        self.action_stop = QAction("Finalizar", self)
        self.action_stop.setToolTip("Finalizar animación anticipadamente (Esc)")
        self.action_stop.setShortcut("Esc")
        self.action_stop.setVisible(False)
        self.action_stop.setObjectName("btnStop")
        toolbar.addAction(self.action_stop)

        toolbar.addSeparator()

        self.action_clear = QAction("Limpiar", self)
        self.action_clear.setToolTip("Borrar editor y resultados (Ctrl+L)")
        self.action_clear.setShortcut("Ctrl+L")
        toolbar.addAction(self.action_clear)

        toolbar.addSeparator()

        self.action_open = QAction("Cargar archivo", self)
        self.action_open.setToolTip("Abrir archivo .acl (Ctrl+O)")
        self.action_open.setShortcut("Ctrl+O")
        toolbar.addAction(self.action_open)

        toolbar.addSeparator()

        self.action_export = QAction("Exportar JSON", self)
        self.action_export.setToolTip("Exportar políticas compiladas a JSON (Ctrl+E)")
        self.action_export.setShortcut("Ctrl+E")
        self.action_export.setEnabled(False)
        self.action_export.setObjectName("btnExport")
        toolbar.addAction(self.action_export)

        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        toolbar.addWidget(spacer)

        # Controles de ventana (sin texto)
        from PyQt6.QtWidgets import QToolButton
        
        self.btn_min = QToolButton(self)
        self.btn_min.setIcon(Icons.minimize("#94a3b8"))
        self.btn_min.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.btn_min.clicked.connect(self.showMinimized)
        
        self.btn_max = QToolButton(self)
        self.btn_max.setIcon(Icons.maximize("#94a3b8"))
        self.btn_max.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.btn_max.clicked.connect(self._toggle_maximize)
        
        self.btn_close = QToolButton(self)
        self.btn_close.setIcon(Icons.x("#94a3b8"))
        self.btn_close.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.btn_close.clicked.connect(self.close)

        # Removemos algo de padding para estos botones en específico
        btn_style = "QToolButton { padding: 6px; }"
        self.btn_min.setStyleSheet(btn_style)
        self.btn_max.setStyleSheet(btn_style)
        self.btn_close.setStyleSheet(btn_style)

        toolbar.addWidget(self.btn_min)
        toolbar.addWidget(self.btn_max)
        toolbar.addWidget(self.btn_close)

        self.action_open.triggered.connect(self._on_open_file)

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _build_statusbar(self):
        self.statusBar().setObjectName("statusBar")

        self.lbl_analyzer = QLabel("Estado: Esperando...")
        self.lbl_analyzer.setStyleSheet("color: #0ea5e9; font-weight: 600;")
        
        self.lbl_tokens = QLabel("Tokens: 0")
        self.lbl_errors = QLabel("Errores: 0")
        self.lbl_cursor = QLabel("Ln 1, Col 1")

        for lbl in (self.lbl_analyzer, self.lbl_tokens, self.lbl_errors, self.lbl_cursor):
            lbl.setContentsMargins(8, 0, 8, 0)

        self.statusBar().addWidget(self.lbl_analyzer)
        self.statusBar().addWidget(self._separator())
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
            self.show_error_panel()
            self.statusBar().showMessage(
                f"Análisis completado — {len(errors)} error(es) léxico(s) encontrado(s).",
                6000
            )
        else:
            self.hide_error_panel()
            self.statusBar().showMessage(
                f"Análisis completado — {len(tokens)} token(s) reconocido(s) sin errores.",
                4000
            )

    def navigate_to_line(self, line: int):
        self.code_editor.go_to_line(line)

    def _on_clear(self):
        self.code_editor.clear()
        self.code_editor.set_lexical_errors([])
        self.token_table.clear_table()
        self.symbol_table_widget.clear_table()
        self.error_panel.clear_panel()
        self.hide_error_panel()
        self.lbl_tokens.setText("Tokens: 0")
        self.lbl_errors.setText("Errores: 0")
        self.statusBar().showMessage("Editor y resultados limpiados.", 3000)

    def show_error_panel(self):
        """Muestra el panel de errores y su encabezado."""
        self.error_container.setVisible(True)

    def hide_error_panel(self):
        """Oculta el panel de errores y su encabezado."""
        self.error_container.setVisible(False)

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
        sep.setFixedWidth(1)
        sep.setStyleSheet("background-color: #2d3148; margin: 4px 0px;")
        return sep

    def _apply_styles(self):
        self.setStyleSheet("""
            /* ── Variables globales ── */
            QMainWindow, QWidget {
                background-color: #0A0E17;
                color: #e2e8f0;
                font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
                font-size: 13px;
            }

            /* ── Toolbar ── */
            QToolBar#mainToolbar {
                background-color: #0A0E17;
                border-bottom: 1px solid #161c2d;
                padding: 10px 14px;
                spacing: 8px;
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
            QToolBar#mainToolbar QToolButton[objectName="btnAnalyze"], 
            QToolBar#mainToolbar QToolButton[objectName="btnDidactic"] {
                background-color: #3b5bdb;
                color: #ffffff;
                border-color: #4c6ef5;
                font-weight: 600;
            }
            QToolBar#mainToolbar QToolButton[objectName="btnAnalyze"]:hover,
            QToolBar#mainToolbar QToolButton[objectName="btnDidactic"]:hover {
                background-color: #4c6ef5;
            }
            QToolBar#mainToolbar QToolButton[objectName="btnAnalyze"]:pressed,
            QToolBar#mainToolbar QToolButton[objectName="btnDidactic"]:pressed {
                background-color: #2f4dc4;
            }
            QToolBar#mainToolbar QToolButton[objectName="btnPause"] {
                color: #fb923c;
            }
            QToolBar#mainToolbar QToolButton[objectName="btnStop"] {
                color: #ef4444;
            }
            QToolBar#mainToolbar QToolButton[objectName="btnExport"] {
                background-color: #166534;
                color: #22c55e;
                border-color: #16a34a;
                font-weight: 600;
            }
            QToolBar#mainToolbar QToolButton[objectName="btnExport"]:hover {
                background-color: #15803d;
                color: #ffffff;
            }
            QToolBar#mainToolbar QToolButton[objectName="btnExport"]:disabled {
                background-color: transparent;
                color: #3a4256;
                border-color: transparent;
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

            /* ── Paneles y Tabs ── */
            QFrame#panelFrame {
                background-color: #0A0E17;
                border: 1px solid #161c2d;
                border-radius: 12px;
            }
            QTabWidget::pane {
                border: none;
                border-top: 1px solid #1e2235;
            }
            QTabBar::tab {
                background-color: #1a1d27;
                color: #7c8db5;
                padding: 8px 16px;
                border: none;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                color: #0ea5e9;
                border-top: 2px solid #0ea5e9;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:hover:!selected {
                background-color: #252838;
                color: #e2e8f0;
            }
            QWidget#panelHeader {
                background-color: #1a1d27;
                border-bottom: 1px solid #1e2235;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QWidget#panelHeader QLabel#panelHeaderText {
                color: #7c8db5;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                background: transparent;
            }
            QWidget#errorHeader {
                background-color: #1a1520;
                border-bottom: 1px solid #2d1f3d;
            }
            QWidget#errorHeader QLabel#panelHeaderText {
                color: #fb7185;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
                background: transparent;
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
                background-color: #0A0E17;
                border-top: 2px solid;
                border-top-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ea5e9, stop:1 #b700ff);
                color: #4a5568;
                font-size: 11px;
                padding: 2px 0;
            }
            QStatusBar::item {
                border: none;
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