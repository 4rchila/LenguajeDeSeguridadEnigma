"""
AstGraphWidget: Visualización gráfica del AST con nodos circulares y flechas.
Soporta animación paso a paso para el modo didáctico.
"""
from typing import List, Optional, Tuple
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, QPainterPath
import parser.ast_nodes as ast


# ── Modelo interno para layout del árbol ──

class TreeLayoutNode:
    """Nodo intermedio para calcular posiciones x,y antes de pintar."""
    def __init__(self, label: str, node_type: str, ast_node: ast.ASTNode = None):
        self.label = label
        self.node_type = node_type  # 'root', 'branch', 'leaf'
        self.ast_node = ast_node
        self.children: List['TreeLayoutNode'] = []
        self.x = 0.0
        self.y = 0.0
        self.visible = False  # Para animación: solo los visibles se pintan

    def add_child(self, child: 'TreeLayoutNode') -> 'TreeLayoutNode':
        self.children.append(child)
        return child


# ── Colores por tipo de nodo ──

NODE_COLORS = {
    'root':     ('#4c6ef5', '#e8ecff'),   # Azul — Programa
    'struct':   ('#10b981', '#d1fae5'),   # Verde — Definir, Bloque
    'rule':     ('#f59e0b', '#fef3c7'),   # Ámbar — Reglas, Acciones
    'control':  ('#8b5cf6', '#ede9fe'),   # Violeta — Si, Mientras, Elegir
    'literal':  ('#06b6d4', '#cffafe'),   # Cyan — Literales
    'id':       ('#ec4899', '#fce7f3'),   # Rosa — Identificadores
    'branch':   ('#64748b', '#f1f5f9'),   # Gris — Nodos intermedios
    'leaf':     ('#34d399', '#d1fae5'),   # Verde claro — Hojas
}


def _color_for(node_type: str) -> Tuple[str, str]:
    return NODE_COLORS.get(node_type, NODE_COLORS['branch'])


# ── Convertir AST real a TreeLayoutNode ──

def ast_to_layout(node: ast.ASTNode) -> Optional[TreeLayoutNode]:
    """Convierte recursivamente un ASTNode en un TreeLayoutNode para dibujar."""
    if node is None:
        return None

    if isinstance(node, ast.ProgramNode):
        ln = TreeLayoutNode("Programa", "root", node)
        for inst in node.instrucciones:
            child = ast_to_layout(inst)
            if child:
                ln.add_child(child)
        return ln

    elif isinstance(node, ast.BloqueNode):
        ln = TreeLayoutNode("Bloque { }", "struct", node)
        for inst in node.instrucciones:
            child = ast_to_layout(inst)
            if child:
                ln.add_child(child)
        return ln

    elif isinstance(node, ast.DefinicionEntidadNode):
        ln = TreeLayoutNode(f"Definir", "struct", node)
        ln.add_child(TreeLayoutNode(node.tipo_entidad, "branch", node))
        ln.add_child(TreeLayoutNode(node.identificador, "id", node))
        return ln

    elif isinstance(node, ast.AsignacionRolAccionNode):
        ln = TreeLayoutNode("Asignación", "struct", node)
        ln.add_child(TreeLayoutNode(f"Rol: {node.rol_id}", "id", node))
        eq = TreeLayoutNode("=", "branch", node)
        ln.add_child(eq)
        regla = ast_to_layout(node.regla)
        if regla:
            eq.add_child(regla)
        return ln

    elif isinstance(node, ast.AsignacionUsuarioRolNode):
        ln = TreeLayoutNode("Asignación", "struct", node)
        ln.add_child(TreeLayoutNode(f"Usuario: {node.usuario_id}", "id", node))
        ln.add_child(TreeLayoutNode("=", "branch", node))
        ln.add_child(TreeLayoutNode(f"Rol: {node.rol_id}", "id", node))
        return ln

    elif isinstance(node, ast.ReglaSeguridadNode):
        ln = TreeLayoutNode(node.accion, "rule", node)
        if node.operacion:
            ln.add_child(TreeLayoutNode(node.operacion, "rule", node))
        ln.add_child(TreeLayoutNode(node.identificador, "id", node))
        return ln

    elif isinstance(node, ast.SiEntoncesNode):
        ln = TreeLayoutNode("Si Entonces", "control", node)
        cond = TreeLayoutNode("Condición", "branch", node)
        cond_child = ast_to_layout(node.condicion)
        if cond_child:
            cond.add_child(cond_child)
        ln.add_child(cond)
        then = TreeLayoutNode("Entonces", "control", node)
        bloque = ast_to_layout(node.bloque_entonces)
        if bloque:
            then.add_child(bloque)
        ln.add_child(then)
        if node.bloque_sino:
            sino = TreeLayoutNode("Sino", "control", node)
            bloque_s = ast_to_layout(node.bloque_sino)
            if bloque_s:
                sino.add_child(bloque_s)
            ln.add_child(sino)
        return ln

    elif isinstance(node, ast.MientrasNode):
        ln = TreeLayoutNode("Mientras", "control", node)
        cond = TreeLayoutNode("Condición", "branch", node)
        cond_child = ast_to_layout(node.condicion)
        if cond_child:
            cond.add_child(cond_child)
        ln.add_child(cond)
        body = TreeLayoutNode("Cuerpo", "control", node)
        bloque = ast_to_layout(node.bloque)
        if bloque:
            body.add_child(bloque)
        ln.add_child(body)
        return ln

    elif isinstance(node, ast.ElegirNode):
        ln = TreeLayoutNode(f"Elegir", "control", node)
        ln.add_child(TreeLayoutNode(node.identificador, "id", node))
        for caso in node.casos:
            child = ast_to_layout(caso)
            if child:
                ln.add_child(child)
        return ln

    elif isinstance(node, ast.CasoNode):
        ln = TreeLayoutNode("Caso", "control", node)
        val = ast_to_layout(node.valor)
        if val:
            ln.add_child(val)
        body = TreeLayoutNode("Cuerpo", "branch", node)
        bloque = ast_to_layout(node.bloque)
        if bloque:
            body.add_child(bloque)
        ln.add_child(body)
        return ln

    elif isinstance(node, ast.IntentarAtraparNode):
        ln = TreeLayoutNode("Intentar/Atrapar", "control", node)
        int_block = TreeLayoutNode("Intentar", "control", node)
        bloque_i = ast_to_layout(node.bloque_intentar)
        if bloque_i:
            int_block.add_child(bloque_i)
        ln.add_child(int_block)
        atr_block = TreeLayoutNode(f"Atrapar ({node.error_id})", "control", node)
        bloque_a = ast_to_layout(node.bloque_atrapar)
        if bloque_a:
            atr_block.add_child(bloque_a)
        ln.add_child(atr_block)
        return ln

    elif isinstance(node, ast.SentenciaSalidaNode):
        ln = TreeLayoutNode(node.tipo_salida, "rule", node)
        val = ast_to_layout(node.valor)
        if val:
            ln.add_child(val)
        return ln

    elif isinstance(node, ast.CondicionBinariaNode):
        ln = TreeLayoutNode(node.operador, "branch", node)
        izq = ast_to_layout(node.izq)
        if izq:
            ln.add_child(izq)
        der = ast_to_layout(node.der)
        if der:
            ln.add_child(der)
        return ln

    elif isinstance(node, ast.CondicionLogicaNode):
        ln = TreeLayoutNode(node.operador, "branch", node)
        izq = ast_to_layout(node.izq)
        if izq:
            ln.add_child(izq)
        der = ast_to_layout(node.der)
        if der:
            ln.add_child(der)
        return ln

    elif isinstance(node, ast.CondicionUnariaNode):
        ln = TreeLayoutNode(node.operador, "branch", node)
        child = ast_to_layout(node.expresion)
        if child:
            ln.add_child(child)
        return ln

    elif isinstance(node, ast.LiteralNode):
        return TreeLayoutNode(str(node.valor), "literal", node)

    elif isinstance(node, ast.IdentificadorNode):
        return TreeLayoutNode(node.nombre, "id", node)

    else:
        return TreeLayoutNode(node.__class__.__name__, "branch", node)


# ── Layout engine: calcula posiciones x, y ──

NODE_RADIUS = 30
H_SPACING = 100   # Espacio horizontal adicional entre nodos hermanos
V_SPACING = 100  # Espacio vertical entre niveles

def _layout_tree(node: TreeLayoutNode, depth: int = 0) -> float:
    """
    Algoritmo de layout: asigna posiciones bottom-up teniendo en cuenta el ancho del texto.
    Retorna el ancho total asignado al subárbol.
    """
    node.y = depth * V_SPACING

    # Estimar el ancho del texto (aprox. 8.5 px por caracter + padding)
    text_width = len(node.label) * 8.5
    node_w = max(120, text_width + 40)
    min_space = node_w + H_SPACING

    if not node.children:
        node.x = min_space / 2.0
        return min_space

    # Layout recursivo de hijos
    child_widths = []
    for child in node.children:
        w = _layout_tree(child, depth + 1)
        child_widths.append(w)

    total_width = sum(child_widths)

    # Posicionar hijos
    cursor_x = 0.0
    for i, child in enumerate(node.children):
        _offset_subtree(child, cursor_x)
        cursor_x += child_widths[i]

    # Centrar padre sobre hijos
    first_child_center = node.children[0].x
    last_child_center = node.children[-1].x
    node.x = (first_child_center + last_child_center) / 2.0

    # Si el nodo padre es más ancho que todos sus hijos combinados,
    # ajustar el ancho total y centrar los hijos debajo.
    if min_space > total_width:
        offset = (min_space - total_width) / 2.0
        for child in node.children:
            _offset_subtree(child, offset)
        node.x = min_space / 2.0
        return min_space

    return total_width


def _offset_subtree(node: TreeLayoutNode, dx: float):
    """Desplaza todo un subárbol horizontalmente."""
    node.x += dx
    for child in node.children:
        _offset_subtree(child, dx)


def _normalize_positions(root: TreeLayoutNode, padding: float = 40.0):
    """Encuentra el min x/y y ajusta para que todo quede en coordenadas positivas con padding."""
    all_nodes = _flatten(root)
    if not all_nodes:
        return
    min_x = min(n.x for n in all_nodes)
    min_y = min(n.y for n in all_nodes)
    for n in all_nodes:
        n.x -= min_x - padding - NODE_RADIUS
        n.y -= min_y - padding - NODE_RADIUS


def _flatten(node: TreeLayoutNode) -> List[TreeLayoutNode]:
    """Recorrido DFS pre-orden, devuelve lista plana de nodos."""
    result = [node]
    for child in node.children:
        result.extend(_flatten(child))
    return result


# ── Canvas: dibuja el árbol con QPainter ──

class _TreeCanvas(QWidget):
    """Widget interno que pinta los nodos y aristas del árbol."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root: Optional[TreeLayoutNode] = None
        self.all_nodes: List[TreeLayoutNode] = []
        self.visible_count = 0
        self.highlighted_node: Optional[TreeLayoutNode] = None
        self.setMinimumSize(200, 200)

    def set_tree(self, root: TreeLayoutNode):
        self.root = root
        if root:
            _layout_tree(root)
            _normalize_positions(root)
            self.all_nodes = _flatten(root)
            # Calcular tamaño del canvas
            if self.all_nodes:
                max_x = max(n.x for n in self.all_nodes) + NODE_RADIUS + 50
                max_y = max(n.y for n in self.all_nodes) + NODE_RADIUS + 50
                self.setMinimumSize(int(max_x), int(max_y))
                self.setFixedSize(int(max_x), int(max_y))
        else:
            self.all_nodes = []
        self.visible_count = 0
        self.update()

    def show_all(self):
        """Muestra todos los nodos de una vez."""
        for n in self.all_nodes:
            n.visible = True
        self.visible_count = len(self.all_nodes)
        self.update()

    def show_next_node(self) -> Optional[TreeLayoutNode]:
        """Hace visible el siguiente nodo en la secuencia DFS. Retorna el nodo recién revelado."""
        if self.visible_count < len(self.all_nodes):
            node = self.all_nodes[self.visible_count]
            node.visible = True
            self.visible_count += 1
            self.highlighted_node = node
            self.update()
            return node
        self.highlighted_node = None
        self.update()
        return None

    def paintEvent(self, event):
        if not self.root:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw Dotted Grid Background
        painter.fillRect(self.rect(), QColor("#0A0E17"))
        pen = QPen(QColor("#1E2235"), 1.5)
        painter.setPen(pen)
        for x in range(0, self.width(), 30):
            for y in range(0, self.height(), 30):
                painter.drawPoint(x, y)

        # Dibujar aristas primero (bajo los nodos)
        for node in self.all_nodes:
            if not node.visible:
                continue
            for child in node.children:
                if not child.visible:
                    continue
                self._draw_edge(painter, node, child)

        # Dibujar nodos
        for node in self.all_nodes:
            if not node.visible:
                continue
            is_highlighted = (node is self.highlighted_node)
            self._draw_node(painter, node, is_highlighted)

        painter.end()

    def _get_dynamic_color(self, text: str) -> str:
        # Paleta Neon Cyberpunk generada deterministicamente
        neon_colors = ["#00f0ff", "#ff0055", "#b700ff", "#ffcc00", "#00ff66", "#ff00ff", "#0088ff", "#ff8800"]
        idx = sum(ord(c) for c in text) % len(neon_colors)
        return neon_colors[idx]

    def _draw_edge(self, painter: QPainter, parent: TreeLayoutNode, child: TreeLayoutNode):
        border_hex = self._get_dynamic_color(child.label)
        color = QColor(border_hex)
        color.setAlpha(150)
        pen = QPen(color, 2)
        painter.setPen(pen)

        h = 36 # Altura de la píldora
        px, py = parent.x, parent.y + h/2
        cx, cy = child.x, child.y - h/2

        path = QPainterPath()
        path.moveTo(px, py)
        
        # Curva de bezier suave
        ctrl1_y = py + (cy - py) / 2
        path.cubicTo(px, ctrl1_y, cx, ctrl1_y, cx, cy)
        
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # Pequeño círculo neón al final de la flecha
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(cx, cy - 2), 4, 4)

    def _draw_node(self, painter: QPainter, node: TreeLayoutNode, highlighted: bool):
        border_hex = self._get_dynamic_color(node.label)
        bg_hex = "#0A0E17"
        
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        fm = QFontMetrics(font)
        text = node.label
        text_width = fm.horizontalAdvance(text)
        
        # Ancho y alto del nodo (Píldora)
        h = 36
        w = max(120, text_width + 40)
        
        cx, cy = node.x, node.y
        rect = QRectF(cx - w/2, cy - h/2, w, h)
        
        # Dibujar Resplandor (Glow effect)
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(1, 5):
            glow_color = QColor(border_hex)
            glow_color.setAlpha(40 - i*8)
            painter.setBrush(QBrush(glow_color))
            painter.drawRoundedRect(rect.adjusted(-i*2, -i*2, i*2, i*2), h/2 + i*2, h/2 + i*2)
            
        if highlighted:
            glow_color = QColor("#ffffff")
            glow_color.setAlpha(60)
            painter.setBrush(QBrush(glow_color))
            painter.drawRoundedRect(rect.adjusted(-5, -5, 5, 5), h/2 + 5, h/2 + 5)
            
        # Fondo y borde
        painter.setBrush(QBrush(QColor(bg_hex)))
        painter.setPen(QPen(QColor(border_hex), 2))
        painter.drawRoundedRect(rect, h/2, h/2)
        
        # Texto
        painter.setFont(font)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)


# ── Widget público con scroll ──

class AstGraphWidget(QScrollArea):
    """
    Widget con scroll que contiene el canvas del árbol gráfico.
    Interfaz pública para la ventana principal.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = _TreeCanvas()
        self.setWidget(self.canvas)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("astGraphScroll")
        self.setStyleSheet("""
            QScrollArea#astGraphScroll {
                background-color: #0A0E17;
                border: none;
            }
            QScrollArea#astGraphScroll > QWidget > QWidget {
                background-color: #0A0E17;
            }
        """)
        self.canvas.setStyleSheet("background-color: #0A0E17;")

    def clear_graph(self):
        self.canvas.root = None
        self.canvas.all_nodes = []
        self.canvas.visible_count = 0
        self.canvas.setMinimumSize(200, 200)
        self.canvas.update()

    def set_ast(self, root_node: ast.ASTNode):
        """Carga un AST completo y lo muestra de inmediato (modo rápido)."""
        layout_root = ast_to_layout(root_node)
        if layout_root:
            self.canvas.set_tree(layout_root)
            self.canvas.show_all()

    def prepare_animation(self, root_node: ast.ASTNode):
        """Carga un AST pero no muestra nada aún (para modo didáctico)."""
        layout_root = ast_to_layout(root_node)
        if layout_root:
            self.canvas.set_tree(layout_root)

    def animate_next_node(self) -> Optional[ast.ASTNode]:
        """Revela el siguiente nodo. Retorna el ASTNode asociado o None si terminó."""
        ln = self.canvas.show_next_node()
        if ln:
            # Hacer scroll para que el nodo sea visible
            target_x = max(0, int(ln.x) - self.viewport().width() // 2)
            target_y = max(0, int(ln.y) - self.viewport().height() // 2)
            self.horizontalScrollBar().setValue(target_x)
            self.verticalScrollBar().setValue(target_y)
            return ln.ast_node
        return None

    def animation_finished(self) -> bool:
        return self.canvas.visible_count >= len(self.canvas.all_nodes)

    def get_total_nodes(self) -> int:
        return len(self.canvas.all_nodes)

    def get_visible_count(self) -> int:
        return self.canvas.visible_count
