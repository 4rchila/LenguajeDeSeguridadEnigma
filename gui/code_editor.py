from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt6.QtCore import Qt, QRect, QSize, QRegularExpression
from PyQt6.QtGui import (
    QColor, QPainter, QTextFormat, QFont,
    QSyntaxHighlighter, QTextCharFormat, QFontMetrics,
    QPalette, QTextCursor
)

class SyntaxHighlighter(QSyntaxHighlighter):
    PALABRAS_RESERVADAS = [
        # Estructura
        "Definir", "definir", "Rol", "rol", "Usuario", "usuario", "Modulo", "modulo",
        # Seguridad
        "Permitir", "permitir", "Denegar", "denegar", "Acceder", "acceder", "Validar", "validar",
        # Acciones
        "Consultar", "consultar", "Registrar", "registrar", "Modificar", "modificar", "Eliminar", "eliminar", "Insertar", "insertar",
        # Control de flujo
        "Si", "si", "Entonces", "entonces", "Sino", "sino", "Mientras", "mientras", "Elegir", "elegir", "Caso", "caso", "Terminar", "terminar",
        # Manejo de errores
        "Intentar", "intentar", "Atrapar", "atrapar", "Error", "error",
        # Valores y tipos
        "Verdadero", "verdadero", "Falso", "falso", "Cadena", "cadena", "Carácter", "carácter", "Horario", "horario",
        # Lógicos
        "Y", "y", "O", "o", "No", "no",
        # Salida
        "Mostrar", "mostrar", "Devolver", "devolver",
    ]

    def __init__(self, document):
        super().__init__(document)
        self._rules = []
        self._build_rules()

    def _fmt(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _build_rules(self):
        # Palabras reservadas — azul medio
        kw_fmt = self._fmt("#60a5fa", bold=True)
        for word in self.PALABRAS_RESERVADAS:
            pattern = QRegularExpression(rf"\b{word}\b")
            self._rules.append((pattern, kw_fmt))

        # Números — naranja suave
        self._rules.append((
            QRegularExpression(r"\b\d+\b"),
            self._fmt("#fb923c")
        ))

        # Operadores — amarillo
        self._rules.append((
            QRegularExpression(r"(==|!=|=>|=<|=|<|>)"),
            self._fmt("#facc15")
        ))

        # Símbolos de agrupación — verde agua
        self._rules.append((
            QRegularExpression(r"[(){}\[\];,\\:]"),
            self._fmt("#34d399")
        ))

        # Cadenas de texto — verde claro
        self._rules.append((
            QRegularExpression(r'"[^"]*"'),
            self._fmt("#86efac")
        ))

        # Comentarios (si el lenguaje los tuviese, con //) — gris
        self._rules.append((
            QRegularExpression(r"//[^\n]*"),
            self._fmt("#4a5568", italic=True)
        ))

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

class LineNumberArea(QWidget):

    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self.editor = editor
        self.setObjectName("lineNumberArea")

    def sizeHint(self) -> QSize:
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):

    # Colores del editor
    BG_COLOR        = QColor("#0d1117")
    LINE_HL_COLOR   = QColor("#1a2035")
    GUTTER_BG       = QColor("#111827")
    GUTTER_FG       = QColor("#374151")
    GUTTER_FG_CURR  = QColor("#6366f1")
    GUTTER_BORDER   = QColor("#1e2235")
    ERROR_UNDERLINE = QColor("#f87171")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lexical_errors = []  # Lista de errores para subrayado tipo Error Lens
        self._setup_font()
        self._setup_palette()
        self._setup_editor()

        self.line_number_area = LineNumberArea(self)
        self.highlighter = SyntaxHighlighter(self.document())

        # Conectar señales
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_number_area_width(0)
        self._highlight_current_line()

        # Texto de bienvenida
        self.setPlaceholderText(
            "// Escribe aquí tu código en el lenguaje de Control de Accesos\n"
            "// Presiona Ctrl+Enter o el botón ▶ Analizar para ejecutar el análisis\n\n"
            "Definir Rol Gerente;\n"
        )

    def _setup_font(self):
        font = QFont()
        # Cascada de fuentes monoespaciadas de alta calidad
        for candidate in ("JetBrains Mono", "Fira Code", "Cascadia Code",
                          "Source Code Pro", "Consolas", "Courier New"):
            font.setFamily(candidate)
            if QFontMetrics(font).horizontalAdvance("M") > 0:
                break
        font.setPointSize(13)
        font.setFixedPitch(True)
        self.setFont(font)

    def _setup_palette(self):
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Base, self.BG_COLOR)
        pal.setColor(QPalette.ColorRole.Text, QColor("#e2e8f0"))
        pal.setColor(QPalette.ColorRole.Highlight, QColor("#3b5bdb"))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        self.setPalette(pal)

    def _setup_editor(self):
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(
            QFontMetrics(self.font()).horizontalAdvance(" ") * 4
        )
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0d1117;
                color: #e2e8f0;
                border: none;
                border-radius: 0;
                selection-background-color: #3b5bdb;
                selection-color: #ffffff;
                padding: 4px 6px;
            }
        """)

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 16 + self.fontMetrics().horizontalAdvance("9") * max(digits, 3)

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), self.GUTTER_BG)

        # Borde derecho del gutter
        painter.setPen(self.GUTTER_BORDER)
        painter.drawLine(
            self.line_number_area.width() - 1, event.rect().top(),
            self.line_number_area.width() - 1, event.rect().bottom()
        )

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)

                if block_number == current_line:
                    painter.setPen(self.GUTTER_FG_CURR)
                    font = self.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    painter.setPen(self.GUTTER_FG)
                    painter.setFont(self.font())

                painter.drawText(
                    0, top,
                    self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1


    def _highlight_current_line(self):
        extra = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(self.LINE_HL_COLOR)
            selection.format.setProperty(
                QTextFormat.Property.FullWidthSelection, True
            )
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra.append(selection)
        extra.extend(self._build_error_selections())
        self.setExtraSelections(extra)

    def set_lexical_errors(self, errors: list):
        """
        Actualiza los errores léxicos para subrayar en rojo en el editor (estilo Error Lens).
        Cada error debe tener: linea, columna, caracter (texto del error, para longitud).
        """
        self._lexical_errors = list(errors) if errors else []
        self._highlight_current_line()

    def _build_error_selections(self):
        """Construye las selecciones extra para subrayar errores en rojo (ondulado)."""
        selections = []
        doc = self.document()
        if not doc or not self._lexical_errors:
            return selections

        err_fmt = QTextCharFormat()
        err_fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        err_fmt.setUnderlineColor(self.ERROR_UNDERLINE)
        err_fmt.setForeground(self.ERROR_UNDERLINE)

        for err in self._lexical_errors:
            linea = getattr(err, "linea", 1)
            columna = getattr(err, "columna", 1)
            caracter = getattr(err, "caracter", "") or getattr(err, "lexema", "?")
            length = max(1, len(caracter))

            block = doc.findBlockByLineNumber(linea - 1)
            if not block.isValid():
                continue
            pos = block.position() + columna - 1
            if pos < 0:
                pos = block.position()
            # Límite por línea (sin incluir el \n del block) para subrayar exactamente el lexema
            fin_linea = block.position() + len(block.text())
            end_pos = min(pos + length, fin_linea)

            cursor = QTextCursor(doc)
            cursor.setPosition(pos)
            cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)

            sel = QTextEdit.ExtraSelection()
            sel.format = err_fmt
            sel.cursor = cursor
            selections.append(sel)
        return selections

    def go_to_line(self, line: int):
        cursor = QTextCursor(self.document().findBlockByLineNumber(line - 1))
        self.setTextCursor(cursor)
        self.centerCursor()
        self.setFocus()