"""
SymbolTableWidget — Visualización de la Tabla de Símbolos.
==========================================================
Muestra el resultado del Analizador Semántico (Fase 3) tal como lo
describe el documento de diseño: una tabla con las columnas
Identificador, Tipo_Dato, Sub_Tipo, Rol_Vinculado y Políticas.

Las variables de entorno globales (Horario, MontoVenta, …) se pintan
con un acento violeta para distinguirlas de las entidades declaradas
explícitamente por el usuario.
"""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont

from semantic.symbol_table import (
    SymbolTable,
    Symbol,
    TIPO_ROL,
    TIPO_USUARIO,
    TIPO_MODULO,
    TIPO_VARIABLE_ENTORNO,
)


# Paleta acordada con los demás widgets del proyecto.
_TIPO_COLORS = {
    TIPO_ROL:              ("#3d2b1a", "#fb923c"),  # Naranja
    TIPO_USUARIO:          ("#1e3d2f", "#4ade80"),  # Verde
    TIPO_MODULO:           ("#1a3340", "#38bdf8"),  # Azul cielo
    TIPO_VARIABLE_ENTORNO: ("#2c1a3d", "#c084fc"),  # Violeta
}
_DEFAULT = ("#1e2235", "#94a3b8")


class SymbolTableWidget(QTableWidget):
    """Tabla de Símbolos del Analizador Semántico — Fase 3."""

    HEADERS = ["Identificador", "Tipo de Dato", "Sub-Tipo",
               "Rol Vinculado", "Políticas / Reglas"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_table()
        self._apply_styles()

    # ── Setup ───────────────────────────────────────────────

    def _setup_table(self):
        self.setColumnCount(len(self.HEADERS))
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
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

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
                padding: 0 12px;
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
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
            QHeaderView::section:last-child { border-right: none; }
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

    # ── API ─────────────────────────────────────────────────

    def populate(self, tabla: SymbolTable):
        """Vuelca todas las filas de la tabla de símbolos en el widget."""
        self.clear_table()
        if tabla is None:
            return

        filas = tabla.filas()
        self.setRowCount(len(filas))

        mono_font = QFont("JetBrains Mono, Fira Code, Consolas", 12)

        for row, sym in enumerate(filas):
            # Columna 0 — Identificador
            item_id = QTableWidgetItem(f"  {sym.identificador}")
            item_id.setFont(mono_font)
            if sym.es_global:
                item_id.setForeground(QBrush(QColor("#c084fc")))
            self.setItem(row, 0, item_id)

            # Columna 1 — Tipo_Dato (con badge de color)
            bg, fg = _TIPO_COLORS.get(sym.tipo_dato, _DEFAULT)
            item_tipo = QTableWidgetItem(f"  {sym.tipo_dato}  ")
            item_tipo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_tipo.setBackground(QBrush(QColor(bg)))
            item_tipo.setForeground(QBrush(QColor(fg)))
            tf = QFont(); tf.setPointSize(10); tf.setBold(True)
            item_tipo.setFont(tf)
            self.setItem(row, 1, item_tipo)

            # Columna 2 — Sub_Tipo
            sub = sym.sub_tipo or "—"
            item_sub = QTableWidgetItem(f"  {sub}")
            item_sub.setForeground(QBrush(QColor("#94a3b8")))
            self.setItem(row, 2, item_sub)

            # Columna 3 — Rol_Vinculado
            rol = sym.rol_vinculado or "—"
            item_rol = QTableWidgetItem(f"  {rol}")
            item_rol.setForeground(QBrush(QColor("#fb923c") if sym.rol_vinculado else QColor("#475569")))
            self.setItem(row, 3, item_rol)

            # Columna 4 — Políticas
            pol_text = self._formatear_politicas(sym)
            item_pol = QTableWidgetItem(f"  {pol_text}")
            item_pol.setForeground(QBrush(QColor("#86efac") if sym.politicas else QColor("#475569")))
            item_pol.setFont(mono_font)
            self.setItem(row, 4, item_pol)

        self.scrollToTop()

    def clear_table(self):
        self.setRowCount(0)

    # ── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _formatear_politicas(sym: Symbol) -> str:
        if not sym.politicas:
            return "—"
        partes = []
        for accion, operacion, modulo in sym.politicas:
            if operacion:
                partes.append(f"{accion} {operacion} {modulo}")
            else:
                partes.append(f"{accion} {modulo}")
        return " | ".join(partes)
