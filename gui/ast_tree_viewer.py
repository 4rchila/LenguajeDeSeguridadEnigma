from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt
import parser.ast_nodes as ast

class AstTreeViewer(QTreeWidget):
    """
    Componente visual para representar el Árbol de Sintaxis Abstracta (AST)
    utilizando QTreeWidget. Permite expandir gráficamente los nodos generados en la Fase 2.
    """
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setObjectName("astViewer")
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #1a1d27;
                color: #e2e8f0;
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                padding: 5px;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #2d3148;
                color: #5edfe2;
            }
            QTreeWidget::item:hover {
                background-color: #252838;
            }
        """)

    def clear_tree(self):
        self.clear()

    def populate_from_ast(self, root_node: ast.ASTNode):
        """Reconstruye todo el QTreeWidget a partir del AST real."""
        self.clear_tree()
        if not root_node:
            return
            
        root_item = self._create_tree_item(root_node)
        self.addTopLevelItem(root_item)
        self.expandAll()

    def _create_tree_item(self, node: ast.ASTNode) -> QTreeWidgetItem:
        """Función recursiva para transcribir ASTNode a QTreeWidgetItem."""
        item = QTreeWidgetItem()
        
        # Guardaremos internamente la referencia del nodo en el item, útil si luego
        # se quiere animar paso a paso y buscar por nodo.
        item.setData(0, Qt.ItemDataRole.UserRole, node)
        
        if isinstance(node, ast.ProgramNode):
            item.setText(0, "Programa")
            # item.setIcon(0, ...) # Aquí se podrían añadir iconos nativos de pyqt pero lo dejaremos clean
            for inst in node.instrucciones:
                item.addChild(self._create_tree_item(inst))
                
        elif isinstance(node, ast.BloqueNode):
            item.setText(0, "Bloque { ... }")
            for inst in node.instrucciones:
                item.addChild(self._create_tree_item(inst))
                
        elif isinstance(node, ast.DefinicionEntidadNode):
            item.setText(0, f"Definicion: {node.tipo_entidad} '{node.identificador}'")
            
        elif isinstance(node, ast.AsignacionRolAccionNode):
            item.setText(0, f"Asignacion: Rol '{node.rol_id}' = ")
            item.addChild(self._create_tree_item(node.regla))
            
        elif isinstance(node, ast.AsignacionUsuarioRolNode):
            item.setText(0, f"Asignacion: Usuario '{node.usuario_id}' = Rol '{node.rol_id}'")
            
        elif isinstance(node, ast.ReglaSeguridadNode):
            op = f" {node.operacion}" if node.operacion else ""
            item.setText(0, f"ReglaSeguridad: {node.accion}{op} '{node.identificador}'")
            
        elif isinstance(node, ast.SiEntoncesNode):
            item.setText(0, "Si Entonces")
            
            cond_item = QTreeWidgetItem(["Condición"])
            cond_item.addChild(self._create_tree_item(node.condicion))
            item.addChild(cond_item)
            
            ent_item = QTreeWidgetItem(["Si se cumple"])
            ent_item.addChild(self._create_tree_item(node.bloque_entonces))
            item.addChild(ent_item)
            
            if node.bloque_sino:
                sino_item = QTreeWidgetItem(["Sino"])
                sino_item.addChild(self._create_tree_item(node.bloque_sino))
                item.addChild(sino_item)
                
        elif isinstance(node, ast.MientrasNode):
            item.setText(0, "Mientras")
            
            cond_item = QTreeWidgetItem(["Condición"])
            cond_item.addChild(self._create_tree_item(node.condicion))
            item.addChild(cond_item)
            
            bloque_item = QTreeWidgetItem(["Cuerpo del Ciclo"])
            bloque_item.addChild(self._create_tree_item(node.bloque))
            item.addChild(bloque_item)
            
        elif isinstance(node, ast.ElegirNode):
            item.setText(0, f"Elegir ({node.identificador})")
            for caso in node.casos:
                item.addChild(self._create_tree_item(caso))

        elif isinstance(node, ast.CasoNode):
            item.setText(0, "Caso")
            item.addChild(self._create_tree_item(node.valor))
            bloque_item = QTreeWidgetItem(["Cuerpo"])
            bloque_item.addChild(self._create_tree_item(node.bloque))
            item.addChild(bloque_item)

        elif isinstance(node, ast.IntentarAtraparNode):
            item.setText(0, "Intentar / Atrapar")
            
            int_item = QTreeWidgetItem(["Intentar"])
            int_item.addChild(self._create_tree_item(node.bloque_intentar))
            item.addChild(int_item)
            
            atr_item = QTreeWidgetItem([f"Atrapar (Error '{node.error_id}')"])
            atr_item.addChild(self._create_tree_item(node.bloque_atrapar))
            item.addChild(atr_item)
            
        elif isinstance(node, ast.SentenciaSalidaNode):
            item.setText(0, f"Salida: {node.tipo_salida}")
            item.addChild(self._create_tree_item(node.valor))
            
        elif isinstance(node, ast.CondicionBinariaNode):
            item.setText(0, f"Operador Binario: '{node.operador}'")
            item.addChild(self._create_tree_item(node.izq))
            item.addChild(self._create_tree_item(node.der))
            
        elif isinstance(node, ast.LiteralNode):
            item.setText(0, f"[{node.tipo}] {node.valor}")
            
        elif isinstance(node, ast.IdentificadorNode):
            item.setText(0, f"ID: {node.nombre}")
            
        else:
            item.setText(0, f"NodoDesconocido: {node.__class__.__name__}")
            
        return item
