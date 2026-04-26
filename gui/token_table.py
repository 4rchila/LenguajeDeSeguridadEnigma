from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QAbstractItemView, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont, QBrush

from gui.icons import Icons

TOKEN_COLORS = {
    "PALABRA_RESERVADA": ("#1e3a5f", "#60a5fa"),
    "IDENTIFICADOR":     ("#1e3d2f", "#4ade80"),
    "NUMERO":            ("#3d2b1a", "#fb923c"),
    "NUMERO_ENT":        ("#3d2b1a", "#fb923c"),
    "NUMERO_DEC":        ("#3d2b1a", "#fb923c"),
    "OPERADOR":          ("#3d3415", "#facc15"),
    "SIMBOLO":           ("#1a3340", "#38bdf8"),
    "CADENA":            ("#1e3325", "#86efac"),
    "ERROR_LEXICO":      ("#3d1515", "#f87171"),
}

DEFAULT_COLORS = ("#1e2235", "#94a3b8")


class TokenTable(QTableWidget):
    HEADERS = ["Lexema", "Tipo de Token", "Línea", "Columna"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_table()
        self._apply_styles()

    def _setup_table(self):
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setRowCount(0)

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.setWordWrap(False)

        hh = self.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(2, 64)
        self.setColumnWidth(3, 90)

        self.verticalHeader().setDefaultSectionSize(28)

    def _apply_styles(self):
        self.setStyleSheet("""
            QTableWidget {
                background-color: #0d1117;
                color: #e2e8f0;
                border: none;
                outline: none;
                gridline-color: transparent;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 0 10px;
                border-bottom: 1px solid #111827;
            }
            QTableWidget::item:selected {
                background-color: #1e2d4f;
                color: #93c5fd;
            }
            QHeaderView::section {
                background-color: #111827;
                color: #64748b;
                border: none;
                border-bottom: 2px solid #1e2235;
                border-right: 1px solid #1e2235;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
            QHeaderView::section:last-child {
                border-right: none;
            }
            QScrollBar:vertical {
                background: #0d1117;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #1e2235;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover { background: #2d3a5e; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)

    def populate(self, tokens: list):
        self.setRowCount(0)
        self.setRowCount(len(tokens))

        mono_font = QFont("JetBrains Mono, Fira Code, Consolas", 12)

        for row, tok in enumerate(tokens):
            tipo_str = tok.tipo.name if hasattr(tok.tipo, "name") else str(tok.tipo)
            is_error = tipo_str == "ERROR_LEXICO"

            item_lex = QTableWidgetItem(tok.lexema)
            item_lex.setFont(mono_font)

            item_tipo = QTableWidgetItem(f"  {tipo_str}  ")
            item_tipo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            bg, fg = TOKEN_COLORS.get(tipo_str, DEFAULT_COLORS)
            item_tipo.setBackground(QBrush(QColor(bg)))
            item_tipo.setForeground(QBrush(QColor(fg)))
            tipo_font = QFont()
            tipo_font.setPointSize(10)
            tipo_font.setBold(True)
            item_tipo.setFont(tipo_font)

            item_line = QTableWidgetItem(str(tok.linea))
            item_line.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_line.setForeground(QBrush(QColor("#64748b")))

            col_val = getattr(tok, "columna", None) or getattr(tok, "col", 0)
            item_col = QTableWidgetItem(str(col_val))
            item_col.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_col.setForeground(QBrush(QColor("#64748b")))

            if is_error:
                error_bg = QBrush(QColor("#200a0a"))
                for item in (item_lex, item_line, item_col):
                    item.setBackground(error_bg)
                    item.setForeground(QBrush(QColor("#fca5a5")))

            self.setItem(row, 0, item_lex)
            self.setItem(row, 1, item_tipo)
            self.setItem(row, 2, item_line)
            self.setItem(row, 3, item_col)
            
        self.scrollToBottom()

    def clear_table(self):
        self.setRowCount(0)


class ErrorPanel(QWidget):
    navigate_to_line = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("errorList")
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)

        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QListWidget#errorList {
                background-color: #0d0a10;
                color: #fca5a5;
                border: none;
                outline: none;
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                font-size: 12px;
                padding: 4px 0;
            }
            QListWidget#errorList::item {
                padding: 5px 14px;
                border-bottom: 1px solid #1a0f1a;
            }
            QListWidget#errorList::item:hover {
                background-color: #1a0f1f;
                color: #fecaca;
            }
            QListWidget#errorList::item:selected {
                background-color: #2d1515;
                color: #fee2e2;
            }
            QScrollBar:vertical {
                background: #0d0a10;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #2d1515;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)

    def populate(self, errors: list):
        self.list_widget.clear()
        self.list_widget.setIconSize(QSize(14, 14))

        if not errors:
            placeholder = QListWidgetItem(Icons.check("#22c55e", 14),
                                            "  Sin errores detectados")
            placeholder.setForeground(QBrush(QColor("#22c55e")))
            placeholder.setFlags(placeholder.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.list_widget.addItem(placeholder)
            return

        for err in errors:
            # Determinación Dinámica (Léxico vs Sintáctico vs Semántico)
            if hasattr(err, "codigo") and str(getattr(err, "codigo", "")).startswith("ERR_SEM_"):
                linea = getattr(err, "linea", 0) or 0
                col   = getattr(err, "columna", 0) or 0
                codigo = err.codigo
                mensaje = getattr(err, "mensaje", str(err))
                msg = f"  [SEMÁNTICO · {codigo}]   Ln {linea}, Col {col}   —   {mensaje}"
                color = QColor("#fb7185")
                icon = Icons.shield_x(color.name(), 14)

            elif hasattr(err, "token") and hasattr(err, "message"):
                if err.token:
                    linea = err.token.linea
                    col = err.token.columna
                else:
                    linea = 0
                    col = 0
                detalle = err.message
                msg = f"  [SINTÁCTICO]   Ln {linea}, Col {col}   —   {detalle}"
                color = QColor("#facc15")
                icon = Icons.alert(color.name(), 14)
            else:
                linea = getattr(err, "linea", 0)
                col = getattr(err, "columna", None) or getattr(err, "col", 0)
                texto = getattr(err, "caracter", None) or getattr(err, "lexema", "?")
                mensaje = getattr(err, "mensaje", None) or "Carácter inválido no pertenece al alfabeto"
                msg = f"  [LÉXICO]   Ln {linea}, Col {col}   —   {mensaje}: '{texto}'"
                color = QColor("#f87171")
                icon = Icons.x_circle(color.name(), 14)

            item = QListWidgetItem(icon, msg)
            item.setForeground(QBrush(color))
            item.setData(Qt.ItemDataRole.UserRole, linea)
            item.setToolTip(f"Doble clic para navegar a la línea {linea}")
            self.list_widget.addItem(item)

    def clear_panel(self):
        self.list_widget.clear()

    def _on_item_double_clicked(self, item: QListWidgetItem):
        line = item.data(Qt.ItemDataRole.UserRole)
        if line is not None:
            self.navigate_to_line.emit(int(line))