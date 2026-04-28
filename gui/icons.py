"""
gui/icons.py — Biblioteca de íconos vectoriales.
================================================
Genera `QIcon` minimalistas (estilo Lucide / Feather) a partir de
operaciones `QPainter`, sin depender de archivos externos ni de
emojis Unicode (que dependen de la fuente del sistema y se ven
inconsistentes entre máquinas).

Cada función devuelve un QIcon con todos los estados (Normal, Active,
Disabled) ya pre-renderizados para que la barra de herramientas y los
tabs se vean nítidos en cualquier resolución.

Uso típico:
    from gui.icons import Icons
    action.setIcon(Icons.play("#60a5fa"))
    tab_widget.addTab(w, Icons.tree("#5edfe2"), "AST")
"""

from typing import Callable

from PyQt6.QtCore import Qt, QRectF, QPointF, QSize
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QPen, QColor, QBrush, QPainterPath,
)


_DEFAULT_SIZE = 18
_STROKE_WIDTH = 1.7


def _new_pixmap(size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    return pm


def _stroke_pen(color: str, width: float = _STROKE_WIDTH) -> QPen:
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _begin(pm: QPixmap, color: str, fill: bool = False) -> QPainter:
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(_stroke_pen(color))
    if fill:
        p.setBrush(QBrush(QColor(color)))
    else:
        p.setBrush(Qt.BrushStyle.NoBrush)
    return p


def _build_icon(draw_fn: Callable[[QPainter, int], None],
                color: str,
                size: int = _DEFAULT_SIZE,
                fill: bool = False) -> QIcon:
    """Crea un QIcon a partir de una función de dibujo (color enchufable)."""
    pm = _new_pixmap(size)
    p = _begin(pm, color, fill=fill)
    draw_fn(p, size)
    p.end()

    # También una versión "muted" para el estado deshabilitado.
    icon = QIcon(pm)
    pm_disabled = _new_pixmap(size)
    p = _begin(pm_disabled, "#3a4256", fill=fill)
    draw_fn(p, size)
    p.end()
    icon.addPixmap(pm_disabled, QIcon.Mode.Disabled)
    return icon


# ─────────────────────────────────────────────────────────────────────
# Definiciones individuales — cada función dibuja un ícono en un canvas
# (size × size) usando coordenadas relativas para escalar limpiamente.
# ─────────────────────────────────────────────────────────────────────

def _draw_play(p: QPainter, s: int):
    path = QPainterPath()
    path.moveTo(s * 0.30, s * 0.18)
    path.lineTo(s * 0.82, s * 0.50)
    path.lineTo(s * 0.30, s * 0.82)
    path.closeSubpath()
    p.fillPath(path, p.brush() if p.brush().style() != Qt.BrushStyle.NoBrush
               else QBrush(p.pen().color()))
    p.drawPath(path)


def _draw_step(p: QPainter, s: int):
    """Tres rectángulos crecientes: visualiza la noción de pasos."""
    p.setBrush(QBrush(p.pen().color()))
    rects = [
        QRectF(s * 0.16, s * 0.62, s * 0.14, s * 0.22),
        QRectF(s * 0.36, s * 0.46, s * 0.14, s * 0.38),
        QRectF(s * 0.56, s * 0.22, s * 0.14, s * 0.62),
    ]
    for r in rects:
        p.drawRoundedRect(r, 1.4, 1.4)


def _draw_minimize(p: QPainter, s: int):
    p.drawLine(QPointF(s * 0.2, s * 0.8), QPointF(s * 0.8, s * 0.8))

def _draw_maximize(p: QPainter, s: int):
    p.drawRect(QRectF(s * 0.2, s * 0.2, s * 0.6, s * 0.6))

def _draw_pause(p: QPainter, s: int):
    p.setBrush(QBrush(p.pen().color()))
    p.drawRoundedRect(QRectF(s * 0.30, s * 0.20, s * 0.13, s * 0.60), 1.5, 1.5)
    p.drawRoundedRect(QRectF(s * 0.57, s * 0.20, s * 0.13, s * 0.60), 1.5, 1.5)


def _draw_stop(p: QPainter, s: int):
    p.setBrush(QBrush(p.pen().color()))
    p.drawRoundedRect(QRectF(s * 0.24, s * 0.24, s * 0.52, s * 0.52), 2.5, 2.5)


def _draw_x(p: QPainter, s: int):
    p.drawLine(QPointF(s * 0.28, s * 0.28), QPointF(s * 0.72, s * 0.72))
    p.drawLine(QPointF(s * 0.72, s * 0.28), QPointF(s * 0.28, s * 0.72))


def _draw_folder(p: QPainter, s: int):
    path = QPainterPath()
    path.moveTo(s * 0.14, s * 0.34)
    path.lineTo(s * 0.40, s * 0.34)
    path.lineTo(s * 0.48, s * 0.26)
    path.lineTo(s * 0.86, s * 0.26)
    path.lineTo(s * 0.86, s * 0.78)
    path.lineTo(s * 0.14, s * 0.78)
    path.closeSubpath()
    p.drawPath(path)


def _draw_code(p: QPainter, s: int):
    """Brackets < / > — editor de código."""
    p.drawLine(QPointF(s * 0.34, s * 0.30), QPointF(s * 0.18, s * 0.50))
    p.drawLine(QPointF(s * 0.18, s * 0.50), QPointF(s * 0.34, s * 0.70))
    p.drawLine(QPointF(s * 0.66, s * 0.30), QPointF(s * 0.82, s * 0.50))
    p.drawLine(QPointF(s * 0.82, s * 0.50), QPointF(s * 0.66, s * 0.70))
    # Slash en medio
    p.drawLine(QPointF(s * 0.58, s * 0.22), QPointF(s * 0.42, s * 0.78))


def _draw_list(p: QPainter, s: int):
    """Líneas horizontales con bullets — Token list / lista."""
    for i, y_rel in enumerate((0.30, 0.50, 0.70)):
        y = s * y_rel
        # bullet
        bullet = QRectF(s * 0.20 - 1.2, y - 1.2, 2.4, 2.4)
        p.setBrush(QBrush(p.pen().color()))
        p.drawEllipse(bullet)
        p.setBrush(Qt.BrushStyle.NoBrush)
        # línea
        p.drawLine(QPointF(s * 0.32, y), QPointF(s * 0.84, y))


def _draw_tree(p: QPainter, s: int):
    """Tres nodos enlazados: padre + 2 hijos (estructura de árbol)."""
    r = s * 0.10
    # Nodos
    nodes = [
        (s * 0.50, s * 0.22),  # raíz
        (s * 0.24, s * 0.74),  # hijo izq
        (s * 0.76, s * 0.74),  # hijo der
    ]
    # Líneas primero para que queden por debajo
    p.drawLine(QPointF(*nodes[0]), QPointF(*nodes[1]))
    p.drawLine(QPointF(*nodes[0]), QPointF(*nodes[2]))
    # Círculos
    p.setBrush(QBrush(p.pen().color()))
    for x, y in nodes:
        p.drawEllipse(QPointF(x, y), r, r)


def _draw_graph(p: QPainter, s: int):
    """Grafo: 4 nodos con conexiones cruzadas — AST gráfico."""
    nodes = [
        (s * 0.22, s * 0.30),
        (s * 0.78, s * 0.30),
        (s * 0.22, s * 0.74),
        (s * 0.78, s * 0.74),
    ]
    p.drawLine(QPointF(*nodes[0]), QPointF(*nodes[1]))
    p.drawLine(QPointF(*nodes[0]), QPointF(*nodes[3]))
    p.drawLine(QPointF(*nodes[1]), QPointF(*nodes[2]))
    p.drawLine(QPointF(*nodes[2]), QPointF(*nodes[3]))
    p.setBrush(QBrush(p.pen().color()))
    r = s * 0.09
    for x, y in nodes:
        p.drawEllipse(QPointF(x, y), r, r)


def _draw_table(p: QPainter, s: int):
    """Cuadrícula de tabla — Tabla de Símbolos."""
    rect = QRectF(s * 0.16, s * 0.20, s * 0.68, s * 0.60)
    p.drawRoundedRect(rect, 2, 2)
    # Línea horizontal de cabecera
    p.drawLine(
        QPointF(s * 0.16, s * 0.36),
        QPointF(s * 0.84, s * 0.36),
    )
    # Líneas verticales
    p.drawLine(QPointF(s * 0.39, s * 0.20), QPointF(s * 0.39, s * 0.80))
    p.drawLine(QPointF(s * 0.61, s * 0.20), QPointF(s * 0.61, s * 0.80))
    # Línea horizontal media
    p.drawLine(QPointF(s * 0.16, s * 0.58), QPointF(s * 0.84, s * 0.58))


def _draw_alert_triangle(p: QPainter, s: int):
    """Triángulo de advertencia — error sintáctico."""
    path = QPainterPath()
    path.moveTo(s * 0.50, s * 0.16)
    path.lineTo(s * 0.86, s * 0.80)
    path.lineTo(s * 0.14, s * 0.80)
    path.closeSubpath()
    p.drawPath(path)
    # Exclamación
    p.drawLine(QPointF(s * 0.50, s * 0.40), QPointF(s * 0.50, s * 0.60))
    p.setBrush(QBrush(p.pen().color()))
    p.drawEllipse(QPointF(s * 0.50, s * 0.70), 1.2, 1.2)


def _draw_shield_x(p: QPainter, s: int):
    """Escudo con X — error semántico (RBAC/ABAC violado)."""
    path = QPainterPath()
    path.moveTo(s * 0.50, s * 0.14)
    path.lineTo(s * 0.84, s * 0.28)
    path.lineTo(s * 0.84, s * 0.54)
    # Curva inferior del escudo
    path.cubicTo(
        QPointF(s * 0.84, s * 0.74),
        QPointF(s * 0.50, s * 0.86),
        QPointF(s * 0.50, s * 0.86),
    )
    path.cubicTo(
        QPointF(s * 0.50, s * 0.86),
        QPointF(s * 0.16, s * 0.74),
        QPointF(s * 0.16, s * 0.54),
    )
    path.lineTo(s * 0.16, s * 0.28)
    path.closeSubpath()
    p.drawPath(path)
    # X interior
    p.drawLine(QPointF(s * 0.38, s * 0.40), QPointF(s * 0.62, s * 0.60))
    p.drawLine(QPointF(s * 0.62, s * 0.40), QPointF(s * 0.38, s * 0.60))


def _draw_x_circle(p: QPainter, s: int):
    """Círculo con X — error léxico."""
    p.drawEllipse(
        QPointF(s * 0.50, s * 0.50),
        s * 0.34, s * 0.34
    )
    p.drawLine(QPointF(s * 0.36, s * 0.36), QPointF(s * 0.64, s * 0.64))
    p.drawLine(QPointF(s * 0.64, s * 0.36), QPointF(s * 0.36, s * 0.64))


def _draw_check_circle(p: QPainter, s: int):
    """Círculo con check — éxito."""
    p.drawEllipse(
        QPointF(s * 0.50, s * 0.50),
        s * 0.34, s * 0.34
    )
    p.drawLine(QPointF(s * 0.34, s * 0.52), QPointF(s * 0.46, s * 0.64))
    p.drawLine(QPointF(s * 0.46, s * 0.64), QPointF(s * 0.68, s * 0.40))


def _draw_eye(p: QPainter, s: int):
    """Ojo — Modo didáctico."""
    path = QPainterPath()
    path.moveTo(s * 0.10, s * 0.50)
    path.cubicTo(
        QPointF(s * 0.30, s * 0.18),
        QPointF(s * 0.70, s * 0.18),
        QPointF(s * 0.90, s * 0.50),
    )
    path.cubicTo(
        QPointF(s * 0.70, s * 0.82),
        QPointF(s * 0.30, s * 0.82),
        QPointF(s * 0.10, s * 0.50),
    )
    p.drawPath(path)
    p.drawEllipse(QPointF(s * 0.50, s * 0.50), s * 0.13, s * 0.13)


def _draw_zap(p: QPainter, s: int):
    """Rayo — análisis rápido."""
    path = QPainterPath()
    path.moveTo(s * 0.56, s * 0.12)
    path.lineTo(s * 0.22, s * 0.54)
    path.lineTo(s * 0.46, s * 0.54)
    path.lineTo(s * 0.40, s * 0.88)
    path.lineTo(s * 0.78, s * 0.46)
    path.lineTo(s * 0.54, s * 0.46)
    path.closeSubpath()
    p.fillPath(path, QBrush(p.pen().color()))
    p.drawPath(path)


def _draw_download(p: QPainter, s: int):
    """Flecha abajo con bandeja — exportar / descargar."""
    # Flecha abajo
    p.drawLine(QPointF(s * 0.50, s * 0.16), QPointF(s * 0.50, s * 0.58))
    p.drawLine(QPointF(s * 0.34, s * 0.44), QPointF(s * 0.50, s * 0.58))
    p.drawLine(QPointF(s * 0.66, s * 0.44), QPointF(s * 0.50, s * 0.58))
    # Bandeja
    path = QPainterPath()
    path.moveTo(s * 0.18, s * 0.62)
    path.lineTo(s * 0.18, s * 0.82)
    path.lineTo(s * 0.82, s * 0.82)
    path.lineTo(s * 0.82, s * 0.62)
    p.drawPath(path)


# ─────────────────────────────────────────────────────────────────────
# Fachada pública
# ─────────────────────────────────────────────────────────────────────

class Icons:
    """Fachada estática para crear QIcons en cualquier color y tamaño."""

    @staticmethod
    def play(color: str = "#e2e8f0", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_play, color, size, fill=True)

    @staticmethod
    def zap(color: str = "#fbbf24", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_zap, color, size, fill=True)

    @staticmethod
    def step(color: str = "#a78bfa", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_step, color, size, fill=True)

    @staticmethod
    def pause(color: str = "#fb923c", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_pause, color, size, fill=True)

    @staticmethod
    def stop(color: str = "#ef4444", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_stop, color, size, fill=True)

    @staticmethod
    def x(color: str = "#94a3b8", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_x, color, size)

    @staticmethod
    def folder(color: str = "#94a3b8", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_folder, color, size)

    @staticmethod
    def code(color: str = "#5edfe2", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_code, color, size)

    @staticmethod
    def list(color: str = "#5edfe2", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_list, color, size)

    @staticmethod
    def tree(color: str = "#5edfe2", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_tree, color, size)

    @staticmethod
    def graph(color: str = "#5edfe2", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_graph, color, size)

    @staticmethod
    def table(color: str = "#5edfe2", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_table, color, size)

    @staticmethod
    def alert(color: str = "#facc15", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_alert_triangle, color, size)

    @staticmethod
    def shield_x(color: str = "#fb7185", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_shield_x, color, size)

    @staticmethod
    def x_circle(color: str = "#f87171", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_x_circle, color, size)

    @staticmethod
    def check(color: str = "#22c55e", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_check_circle, color, size)

    @staticmethod
    def eye(color: str = "#a78bfa", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_eye, color, size)

    @staticmethod
    def download(color: str = "#22c55e", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_download, color, size)

    @staticmethod
    def minimize(color: str = "#94a3b8", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_minimize, color, size)

    @staticmethod
    def maximize(color: str = "#94a3b8", size: int = _DEFAULT_SIZE) -> QIcon:
        return _build_icon(_draw_maximize, color, size)

    # ─────── Pixmap helpers (para QLabels e items dentro de QListWidget) ───────

    @staticmethod
    def pixmap(name: str, color: str, size: int = _DEFAULT_SIZE) -> QPixmap:
        """Devuelve un QPixmap directo (usado para QLabels)."""
        icon = getattr(Icons, name)(color, size)
        return icon.pixmap(QSize(size, size))
