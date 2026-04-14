from typing import List, Optional, Any
from lexer.tokens import Token

class ASTNode:
    """Clase base para todos los nodos del Árbol de Sintaxis Abstracta (AST)."""
    def __init__(self, start_token: Token = None, end_token: Token = None):
        self.start_token = start_token
        self.end_token = end_token

    def __str__(self):
        return self.__class__.__name__


class ProgramNode(ASTNode):
    """Nodo raíz del programa, contiene una lista de instrucciones."""
    def __init__(self, instrucciones: List[ASTNode], start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.instrucciones = instrucciones


class BloqueNode(ASTNode):
    """Nodo que representa un bloque de instrucciones dentro de llaves o una sola instrucción."""
    def __init__(self, instrucciones: List[ASTNode], start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.instrucciones = instrucciones


# --- Nodos de Definición y Asignación ---

class DefinicionEntidadNode(ASTNode):
    """Ej: Definir Rol Vendedor;"""
    def __init__(self, tipo_entidad: str, identificador: str, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.tipo_entidad = tipo_entidad
        self.identificador = identificador

class AsignacionRolAccionNode(ASTNode):
    """Ej: Rol Vendedor = Acceder Ventas; o Rol Admin = Permitir Consultar Dashboard;"""
    def __init__(self, rol_id: str, regla: 'ReglaSeguridadNode', start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.rol_id = rol_id
        self.regla = regla

class AsignacionUsuarioRolNode(ASTNode):
    """Ej: Usuario Juan = Rol Vendedor;"""
    def __init__(self, usuario_id: str, rol_id: str, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.usuario_id = usuario_id
        self.rol_id = rol_id


# --- Reglas Lógicas de Seguridad ---

class ReglaSeguridadNode(ASTNode):
    """Ej: Permitir Consultar Inventario; o Permitir Ventas;"""
    def __init__(self, accion: str, operacion: Optional[str], identificador: str, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.accion = accion
        self.operacion = operacion # Puede ser None (Ej: Permitir Inventario)
        self.identificador = identificador


# --- Nodos de Valores y Expresiones ---

class LiteralNode(ASTNode):
    """Valores numéricos, cadenas, booleanos o de fecha."""
    def __init__(self, valor: Any, tipo_literal: str, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.valor = valor
        self.tipo = tipo_literal

class IdentificadorNode(ASTNode):
    """Referencia a un id en condiciones o sentencias."""
    def __init__(self, nombre: str, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.nombre = nombre

class CondicionBinariaNode(ASTNode):
    """Operaciones de condición. Ej: Ventas > 100 o Estado == Verdadero"""
    def __init__(self, izq: ASTNode, operador: str, der: ASTNode, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.izq = izq
        self.operador = operador
        self.der = der

class CondicionLogicaNode(ASTNode):
    """Condiciones que engloban a otras con Y / O. Diferenciadito opcional."""
    def __init__(self, izq: ASTNode, operador: str, der: ASTNode, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.izq = izq
        self.operador = operador
        self.der = der

class CondicionUnariaNode(ASTNode):
    """Ej: No Activo"""
    def __init__(self, operador: str, expresion: ASTNode, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.operador = operador
        self.expresion = expresion


# --- Nodos de Control de Flujo ---

class SiEntoncesNode(ASTNode):
    """Estructura Si [condicion] Entonces [bloque] Sino [bloque]"""
    def __init__(self, condicion: ASTNode, bloque_entonces: ASTNode, bloque_sino: Optional[ASTNode] = None, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.condicion = condicion
        self.bloque_entonces = bloque_entonces
        self.bloque_sino = bloque_sino

class MientrasNode(ASTNode):
    """Estructura Mientras [condicion] [bloque]"""
    def __init__(self, condicion: ASTNode, bloque: ASTNode, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.condicion = condicion
        self.bloque = bloque


class CasoNode(ASTNode):
    """Representa Caso [valor_literal]: [bloque] Terminar;"""
    def __init__(self, valor: ASTNode, bloque: ASTNode, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.valor = valor
        self.bloque = bloque

class ElegirNode(ASTNode):
    """Estructura Elegir ( [id] ) { [casos] }"""
    def __init__(self, identificador: str, casos: List[CasoNode], start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.identificador = identificador
        self.casos = casos


# --- Manejo de Errores y Output ---

class IntentarAtraparNode(ASTNode):
    """Estructura Intentar { ... } Atrapar (Error [id]) { ... }"""
    def __init__(self, bloque_intentar: ASTNode, error_id: str, bloque_atrapar: ASTNode, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.bloque_intentar = bloque_intentar
        self.error_id = error_id
        self.bloque_atrapar = bloque_atrapar

class SentenciaSalidaNode(ASTNode):
    """Mostrar [valor]; o Devolver [valor];"""
    def __init__(self, tipo_salida: str, valor: ASTNode, start_token=None, end_token=None):
        super().__init__(start_token, end_token)
        self.tipo_salida = tipo_salida  # 'Mostrar' o 'Devolver'
        self.valor = valor
