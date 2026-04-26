"""
Analizador Semántico (Fase 3) — Lenguaje Enigma
================================================
Recorre el Árbol de Sintaxis Abstracta producido por el parser y aplica
las 7 reglas semánticas del documento "Diseño Analizador Semántico —
Enigma":

    1. Unicidad de Entidades            → ERR_SEM_01
    2. Integridad Referencial            → ERR_SEM_02
    3. Compatibilidad de Asignación      → ERR_SEM_03
    4. Coherencia de Operaciones (RBAC)  → ERR_SEM_04
    5. Validación lógica de Expresiones  → ERR_SEM_05
    6. Operaciones entre Tipos           → ERR_SEM_06
    7. Conflicto de Políticas            → ERR_SEM_07

Estrategia de implementación:
    * Patrón **Visitor** (despacho por tipo de nodo).
    * Política **Fail-Fast**: el primer SemanticError se lanza como
      excepción y el análisis aborta. La excepción se captura en el
      método público `analizar()` para que la GUI pueda mostrarlo.
    * **Zero Trust**: ningún identificador se confía hasta consultar la
      Tabla de Símbolos, ni siquiera dentro de bloques anidados.
"""

from typing import List, Optional

import parser.ast_nodes as ast

from .semantic_errors import SemanticError
from .symbol_table import (
    Symbol,
    SymbolTable,
    TIPO_ROL,
    TIPO_USUARIO,
    TIPO_MODULO,
    TIPO_VARIABLE_ENTORNO,
    SUBTIPO_BOOLEANO,
    SUBTIPO_CADENA,
    SUBTIPO_ENTERO,
    SUBTIPO_DECIMAL,
    SUBTIPO_TIEMPO,
)


# Conjuntos canónicos del lenguaje (case-insensitive en comparación).
ACCIONES_ACCESO = {"permitir", "denegar", "acceder", "validar"}
OPERACIONES_NEGOCIO = {"consultar", "registrar", "modificar", "eliminar", "insertar"}

# Tipos numéricos compatibles para comparaciones (<, >, <=, >=, etc.)
TIPOS_NUMERICOS = {SUBTIPO_ENTERO, SUBTIPO_DECIMAL, SUBTIPO_TIEMPO, "Numero"}

# Operadores que producen un valor booleano.
OPERADORES_RELACIONALES = {"==", "!=", "<", ">", "<=", ">=", "=>", "=<", "="}
OPERADORES_LOGICOS      = {"y", "o"}


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def _linea_de(node) -> int:
    tok = getattr(node, "start_token", None)
    return getattr(tok, "linea", 0) if tok else 0


def _columna_de(node) -> int:
    tok = getattr(node, "start_token", None)
    return getattr(tok, "columna", 0) if tok else 0


def _es_par_opuesto(a1: str, a2: str) -> bool:
    """¿(Permitir, Denegar) o viceversa?"""
    s = {a1.lower(), a2.lower()}
    return s == {"permitir", "denegar"}


# ─────────────────────────────────────────────────────────────────────
# Analizador
# ─────────────────────────────────────────────────────────────────────

class SemanticAnalyzer:
    """
    Visitor que valida el AST contra las reglas semánticas del lenguaje
    Enigma. Consume un ProgramNode y produce:
        * `tabla`     → SymbolTable con todas las entidades registradas.
        * `errores`   → Lista (longitud 0 ó 1 por fail-fast) con
                        SemanticError detectados.
        * `exitoso`   → bool: True si y sólo si la lista está vacía.
    """

    def __init__(self):
        self.tabla = SymbolTable(inicializar_globales=True)
        self.errores: List[SemanticError] = []
        self.exitoso: bool = False

    # ---------- API pública ----------

    def analizar(self, arbol: ast.ProgramNode) -> bool:
        """
        Punto de entrada. Recorre el árbol y captura el SemanticError si
        ocurre. Retorna True si el análisis fue exitoso.
        """
        self.errores.clear()
        try:
            if arbol is None:
                return True
            self._visitar(arbol)
            self.exitoso = True
            return True
        except SemanticError as err:
            self.errores.append(err)
            self.exitoso = False
            return False

    # ---------- Despacho del Visitor ----------

    def _visitar(self, node: ast.ASTNode):
        if node is None:
            return None
        method = getattr(self, f"_visit_{type(node).__name__}", self._visit_generico)
        return method(node)

    def _visit_generico(self, node: ast.ASTNode):
        # Caso por defecto: si llegamos a un nodo no manejado, no lo
        # consideramos un error semántico (lo deja pasar el parser).
        return None

    # ─────────────────────────────────────────────────────────────────
    # Nodos estructurales
    # ─────────────────────────────────────────────────────────────────

    def _visit_ProgramNode(self, node: ast.ProgramNode):
        for inst in node.instrucciones:
            self._visitar(inst)

    def _visit_BloqueNode(self, node: ast.BloqueNode):
        # En Enigma todos los bloques comparten el mismo scope global
        # (no hay scopes anidados según el documento). Sólo recorremos
        # las instrucciones contenidas.
        for inst in node.instrucciones:
            self._visitar(inst)

    # ─────────────────────────────────────────────────────────────────
    # Definición y asignación de entidades
    # ─────────────────────────────────────────────────────────────────

    def _visit_DefinicionEntidadNode(self, node: ast.DefinicionEntidadNode):
        """
        Regla 1 — Unicidad: si ya existe el identificador,
        ERR_SEM_01 (Redeclaración).
        """
        tipo_canon = self._normalizar_tipo_entidad(node.tipo_entidad)
        nuevo = Symbol(
            identificador=node.identificador,
            tipo_dato=tipo_canon,
            linea=_linea_de(node),
            columna=_columna_de(node),
        )
        previo = self.tabla.declarar(nuevo)
        if previo is not None:
            self._raise(
                "ERR_SEM_01",
                f"Redeclaración. El identificador '{node.identificador}' ya existe "
                f"en el entorno como tipo '{previo.tipo_dato}'.",
                node,
                lexema=node.identificador,
            )

    def _visit_AsignacionUsuarioRolNode(self, node: ast.AsignacionUsuarioRolNode):
        """
        Usuario X = Rol Y;

        Reglas aplicables:
            * Existencia de X (ERR_SEM_02)
            * Existencia de Y (ERR_SEM_02)
            * X.tipo == Usuario (ERR_SEM_03)
            * Y.tipo == Rol     (ERR_SEM_03)
        """
        sym_usr = self.tabla.buscar(node.usuario_id)
        if sym_usr is None:
            self._raise(
                "ERR_SEM_02",
                f"Entidad No Encontrada. El Usuario '{node.usuario_id}' no ha sido "
                f"definido previamente con 'Definir Usuario {node.usuario_id};'.",
                node, lexema=node.usuario_id,
            )

        if sym_usr.tipo_dato != TIPO_USUARIO:
            self._raise(
                "ERR_SEM_03",
                f"Incompatibilidad. Se intenta asignar un Rol a '{node.usuario_id}', "
                f"pero está declarado como tipo '{sym_usr.tipo_dato}'. La herencia "
                f"de roles sólo aplica a entidades tipo Usuario.",
                node, lexema=node.usuario_id,
            )

        sym_rol = self.tabla.buscar(node.rol_id)
        if sym_rol is None:
            self._raise(
                "ERR_SEM_02",
                f"Entidad No Encontrada. El Rol '{node.rol_id}' no ha sido definido "
                f"previamente con 'Definir Rol {node.rol_id};'.",
                node, lexema=node.rol_id,
            )

        if sym_rol.tipo_dato != TIPO_ROL:
            self._raise(
                "ERR_SEM_03",
                f"Incompatibilidad. '{node.rol_id}' está declarado como "
                f"'{sym_rol.tipo_dato}', no como Rol. Un Usuario sólo puede heredar "
                f"de un Rol (RBAC).",
                node, lexema=node.rol_id,
            )

        # Asignación válida → actualizar herencia.
        self.tabla.actualizar_rol_vinculado(node.usuario_id, sym_rol.identificador)

    def _visit_AsignacionRolAccionNode(self, node: ast.AsignacionRolAccionNode):
        """
        Rol X = <regla_seguridad>;

        Reglas:
            * Existencia de X (ERR_SEM_02)
            * X.tipo == Rol   (ERR_SEM_03)
            * Validar la regla (módulo existe, dominio válido, conflicto)
        """
        sym_rol = self.tabla.buscar(node.rol_id)
        if sym_rol is None:
            self._raise(
                "ERR_SEM_02",
                f"Entidad No Encontrada. El Rol '{node.rol_id}' no ha sido definido "
                f"previamente. Use 'Definir Rol {node.rol_id};' antes de asignar políticas.",
                node, lexema=node.rol_id,
            )

        if sym_rol.tipo_dato != TIPO_ROL:
            self._raise(
                "ERR_SEM_03",
                f"Incompatibilidad. No se pueden asignar políticas directamente a "
                f"una entidad tipo '{sym_rol.tipo_dato}'. Asigne la política a un Rol, "
                f"y vincule el Rol al {sym_rol.tipo_dato}.",
                node, lexema=node.rol_id,
            )

        regla: ast.ReglaSeguridadNode = node.regla
        accion = regla.accion
        operacion = regla.operacion
        target = regla.identificador

        # 1) Validar dominio (módulo existe + es Modulo cuando hay operación)
        sym_target = self._validar_objetivo_regla(regla)

        # 2) Detectar conflicto de políticas (ERR_SEM_07)
        nueva_pol = (accion, operacion, sym_target.identificador)
        if self._hay_conflicto_politica(sym_rol, nueva_pol):
            self._raise(
                "ERR_SEM_07",
                f"Conflicto de Políticas. El Rol '{sym_rol.identificador}' ya tiene "
                f"una regla contradictoria sobre "
                f"'{operacion or '·'} {sym_target.identificador}'. No puede coexistir "
                f"Permitir y Denegar para el mismo recurso.",
                regla, lexema=sym_target.identificador,
            )

        # 3) Registrar política en la fila del rol.
        self.tabla.agregar_politica(sym_rol.identificador, nueva_pol)

    def _visit_ReglaSeguridadNode(self, node: ast.ReglaSeguridadNode):
        """
        Permitir|Denegar|Acceder|Validar [operación] <id>;

        Sin contexto de Rol, sólo podemos validar el dominio del objetivo.
        """
        self._validar_objetivo_regla(node)

    # ─────────────────────────────────────────────────────────────────
    # Sentencias de control
    # ─────────────────────────────────────────────────────────────────

    def _visit_SiEntoncesNode(self, node: ast.SiEntoncesNode):
        self._exigir_condicion_booleana(node.condicion, contexto="Si")
        self._visitar(node.bloque_entonces)
        if node.bloque_sino:
            self._visitar(node.bloque_sino)

    def _visit_MientrasNode(self, node: ast.MientrasNode):
        self._exigir_condicion_booleana(node.condicion, contexto="Mientras")
        self._visitar(node.bloque)

    def _visit_ElegirNode(self, node: ast.ElegirNode):
        # Validamos que el identificador exista — Elegir trabaja sobre
        # un valor concreto, no podemos elegir sobre algo no declarado.
        sym = self.tabla.buscar(node.identificador)
        if sym is None:
            self._raise(
                "ERR_SEM_02",
                f"Entidad No Encontrada. 'Elegir' sobre '{node.identificador}', pero "
                f"este identificador no fue declarado.",
                node, lexema=node.identificador,
            )
        for caso in node.casos:
            self._visitar(caso)

    def _visit_CasoNode(self, node: ast.CasoNode):
        self._visitar(node.bloque)

    # ─────────────────────────────────────────────────────────────────
    # Manejo de errores y salida
    # ─────────────────────────────────────────────────────────────────

    def _visit_IntentarAtraparNode(self, node: ast.IntentarAtraparNode):
        self._visitar(node.bloque_intentar)
        # Inyectamos temporalmente el id del error como variable booleana
        # para que sea visible dentro del bloque de Atrapar.
        sym_err = Symbol(
            identificador=node.error_id,
            tipo_dato=TIPO_VARIABLE_ENTORNO,
            sub_tipo=SUBTIPO_BOOLEANO,
            linea=_linea_de(node),
            es_global=False,
        )
        previo = self.tabla.declarar(sym_err)
        try:
            self._visitar(node.bloque_atrapar)
        finally:
            # Si lo creamos nosotros, lo retiramos al salir.
            if previo is None:
                clave = node.error_id.lower()
                self.tabla._tabla.pop(clave, None)  # acceso interno

    def _visit_SentenciaSalidaNode(self, node: ast.SentenciaSalidaNode):
        # Mostrar/Devolver: validar que el valor sea resoluble.
        self._tipo_de(node.valor)

    # ─────────────────────────────────────────────────────────────────
    # Validaciones puntuales
    # ─────────────────────────────────────────────────────────────────

    def _validar_objetivo_regla(self, regla: ast.ReglaSeguridadNode) -> Symbol:
        """Comprueba existencia y dominio del identificador objetivo."""
        sym = self.tabla.buscar(regla.identificador)
        if sym is None:
            self._raise(
                "ERR_SEM_02",
                f"Entidad No Encontrada. Se intentó aplicar la regla "
                f"'{regla.accion}{(' ' + regla.operacion) if regla.operacion else ''} "
                f"{regla.identificador}', pero '{regla.identificador}' no ha sido "
                f"definido previamente.",
                regla, lexema=regla.identificador,
            )

        # Si hay operación de negocio (Consultar/Registrar/...), el
        # objetivo DEBE ser de tipo Módulo (regla 4 — Dominio).
        if regla.operacion is not None:
            if regla.operacion.lower() in OPERACIONES_NEGOCIO and sym.tipo_dato != TIPO_MODULO:
                self._raise(
                    "ERR_SEM_04",
                    f"Dominio Inválido. La operación '{regla.operacion}' sólo puede "
                    f"ejecutarse sobre un Módulo. '{regla.identificador}' está "
                    f"declarado como '{sym.tipo_dato}'.",
                    regla, lexema=regla.identificador,
                )
        else:
            # Acción sin operación: Acceder/Validar X — exigir Módulo.
            if regla.accion.lower() in {"acceder", "validar"} and sym.tipo_dato != TIPO_MODULO:
                self._raise(
                    "ERR_SEM_04",
                    f"Dominio Inválido. '{regla.accion}' debe aplicarse a un Módulo. "
                    f"'{regla.identificador}' es de tipo '{sym.tipo_dato}'.",
                    regla, lexema=regla.identificador,
                )

        return sym

    def _hay_conflicto_politica(self, rol: Symbol, nueva: tuple) -> bool:
        """ERR_SEM_07 — busca pares Permitir/Denegar exactos."""
        a_new, op_new, mod_new = nueva
        for a, op, mod in rol.politicas:
            if op == op_new and mod.lower() == mod_new.lower():
                if _es_par_opuesto(a, a_new):
                    return True
        return False

    def _exigir_condicion_booleana(self, cond: ast.ASTNode, contexto: str) -> None:
        """ERR_SEM_05 — la condición debe resolverse a Booleano."""
        tipo = self._tipo_de(cond)
        if tipo != SUBTIPO_BOOLEANO:
            self._raise(
                "ERR_SEM_05",
                f"Expresión No Booleana. La condición de '{contexto}' debe evaluarse "
                f"a Verdadero/Falso, pero se obtuvo tipo '{tipo}'. Falta operador "
                f"relacional o lógico.",
                cond,
            )

    # ─────────────────────────────────────────────────────────────────
    # Sistema de tipos
    # ─────────────────────────────────────────────────────────────────

    def _tipo_de(self, expr: ast.ASTNode) -> str:
        """
        Calcula el tipo semántico de una expresión. Retorna uno de:
        Booleano | Cadena | Entero | Decimal | Tiempo | Numero |
        Rol | Usuario | Modulo | Variable_Entorno | Desconocido
        """
        if expr is None:
            return "Desconocido"

        if isinstance(expr, ast.LiteralNode):
            t = expr.tipo
            if t == "Logico":
                return SUBTIPO_BOOLEANO
            if t == "Cadena":
                return SUBTIPO_CADENA
            if t == "Numero":
                return self._inferir_subtipo_numerico(expr.valor)
            return t

        if isinstance(expr, ast.IdentificadorNode):
            sym = self.tabla.buscar(expr.nombre)
            if sym is None:
                self._raise(
                    "ERR_SEM_02",
                    f"Entidad No Encontrada. El identificador '{expr.nombre}' "
                    f"no ha sido definido en el entorno.",
                    expr, lexema=expr.nombre,
                )
            # Variables de entorno → su sub_tipo es el tipo de dato real.
            if sym.tipo_dato == TIPO_VARIABLE_ENTORNO and sym.sub_tipo:
                return sym.sub_tipo
            return sym.tipo_dato

        if isinstance(expr, ast.CondicionBinariaNode):
            return self._tipo_condicion_binaria(expr)

        if isinstance(expr, ast.CondicionLogicaNode):
            return self._tipo_condicion_logica(expr)

        if isinstance(expr, ast.CondicionUnariaNode):
            t = self._tipo_de(expr.expresion)
            if t != SUBTIPO_BOOLEANO:
                self._raise(
                    "ERR_SEM_06",
                    f"Operación Inválida. El operador '{expr.operador}' requiere un "
                    f"valor Booleano, no '{t}'.",
                    expr,
                )
            return SUBTIPO_BOOLEANO

        return "Desconocido"

    def _tipo_condicion_binaria(self, expr: ast.CondicionBinariaNode) -> str:
        """
        Tipa relación binaria. Maneja relacionales y lógicos para
        compatibilidad con el parser actual (que mete y/o como binarios).
        """
        op = expr.operador.lower()
        t_izq = self._tipo_de(expr.izq)
        t_der = self._tipo_de(expr.der)

        if op in OPERADORES_LOGICOS:
            if t_izq != SUBTIPO_BOOLEANO or t_der != SUBTIPO_BOOLEANO:
                self._raise(
                    "ERR_SEM_06",
                    f"Operación Inválida. El operador lógico '{op}' requiere ambos "
                    f"operandos Booleanos, se obtuvieron '{t_izq}' y '{t_der}'.",
                    expr,
                )
            return SUBTIPO_BOOLEANO

        if op in OPERADORES_RELACIONALES:
            self._validar_compatibilidad_relacional(op, t_izq, t_der, expr)
            return SUBTIPO_BOOLEANO

        # Operador no reconocido → tratamos como inválido.
        self._raise(
            "ERR_SEM_06",
            f"Operación Inválida. Operador '{expr.operador}' no es compatible en "
            f"una expresión binaria.",
            expr,
        )
        return "Desconocido"

    def _tipo_condicion_logica(self, expr: ast.CondicionLogicaNode) -> str:
        t_izq = self._tipo_de(expr.izq)
        t_der = self._tipo_de(expr.der)
        if t_izq != SUBTIPO_BOOLEANO or t_der != SUBTIPO_BOOLEANO:
            self._raise(
                "ERR_SEM_06",
                f"Operación Inválida. El conector '{expr.operador}' debe unir dos "
                f"expresiones Booleanas (recibió '{t_izq}' y '{t_der}').",
                expr,
            )
        return SUBTIPO_BOOLEANO

    def _validar_compatibilidad_relacional(
        self, op: str, t_izq: str, t_der: str, expr: ast.ASTNode
    ) -> None:
        """ERR_SEM_06 — los relacionales sólo entre tipos compatibles."""

        # Normalizamos las variantes alternas que el lenguaje admite:
        #   '=>' ⇒ '>='   y   '=<' ⇒ '<='   (orden de escritura invertido).
        #   '='  ⇒ '=='   (igualdad estructural).
        equivalencias = {"=>": ">=", "=<": "<=", "=": "=="}
        op_norm = equivalencias.get(op, op)

        # Bloqueo explícito: comparar entidades RBAC contra cualquier valor
        # primitivo carece de sentido lógico.
        entidades = {TIPO_ROL, TIPO_USUARIO, TIPO_MODULO}
        if t_izq in entidades or t_der in entidades:
            self._raise(
                "ERR_SEM_06",
                f"Operación Inválida. No se puede comparar entidades RBAC con el "
                f"operador '{op}' (tipos: '{t_izq}' vs '{t_der}').",
                expr,
            )

        # ==, != aceptan cualquier par del MISMO tipo (o numéricos entre sí).
        if op_norm in {"==", "!="}:
            if self._tipos_compatibles_igualdad(t_izq, t_der):
                return
            self._raise(
                "ERR_SEM_06",
                f"Operación Inválida. No se pueden comparar tipos incompatibles "
                f"con '{op}': '{t_izq}' vs '{t_der}'.",
                expr,
            )

        # <, >, <=, >= → solo numéricos / tiempo.
        if op_norm in {"<", ">", "<=", ">="}:
            if t_izq in TIPOS_NUMERICOS and t_der in TIPOS_NUMERICOS:
                return
            self._raise(
                "ERR_SEM_06",
                f"Operación Inválida. El operador '{op}' requiere operandos "
                f"numéricos o de tipo Tiempo. Se obtuvo '{t_izq}' vs '{t_der}'.",
                expr,
            )

    def _tipos_compatibles_igualdad(self, a: str, b: str) -> bool:
        if a == b:
            return True
        # Numéricos entre sí son intercambiables.
        if a in TIPOS_NUMERICOS and b in TIPOS_NUMERICOS:
            return True
        return False

    # ─────────────────────────────────────────────────────────────────
    # Utilidades
    # ─────────────────────────────────────────────────────────────────

    def _inferir_subtipo_numerico(self, valor) -> str:
        """Diferencia un literal entero, decimal o de tiempo (HH:MM)."""
        s = str(valor)
        if ":" in s:
            return SUBTIPO_TIEMPO
        if "." in s:
            return SUBTIPO_DECIMAL
        return SUBTIPO_ENTERO

    def _normalizar_tipo_entidad(self, lexema: str) -> str:
        """Convierte 'rol'/'Rol' → 'Rol' canónico."""
        l = (lexema or "").lower()
        if l == "rol":     return TIPO_ROL
        if l == "usuario": return TIPO_USUARIO
        if l == "modulo":  return TIPO_MODULO
        return lexema

    def _raise(self, codigo: str, mensaje: str, node: ast.ASTNode = None,
               lexema: Optional[str] = None) -> None:
        """Empaqueta y lanza un SemanticError siempre con ubicación."""
        raise SemanticError(
            codigo=codigo,
            mensaje=mensaje,
            linea=_linea_de(node) if node else 0,
            columna=_columna_de(node) if node else 0,
            lexema=lexema,
        )
