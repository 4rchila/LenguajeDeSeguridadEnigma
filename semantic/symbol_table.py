"""
Tabla de Símbolos del Analizador Semántico.
===========================================
Implementación basada en el documento "Diseño Analizador Semántico —
Enigma", sección 4 (Diseño de la Tabla de Símbolos) y 5 (Ciclo de Vida).

Estructura de cada fila:
    +------+----------+----------+----------+--------------+
    |  ID  | Tipo_Dato| Sub_Tipo | Rol_Vinc.|  Políticas   |
    +------+----------+----------+----------+--------------+

Los identificadores son CASE-INSENSITIVE (igual que el resto del
lenguaje), pero internamente almacenamos el lexema original para
facilitar mensajes de error legibles. La búsqueda usa la versión en
minúsculas como llave primaria.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# Tipos canónicos del lenguaje.
TIPO_ROL              = "Rol"
TIPO_USUARIO          = "Usuario"
TIPO_MODULO           = "Modulo"
TIPO_VARIABLE_ENTORNO = "Variable_Entorno"

# Sub-tipos de las variables ABAC.
SUBTIPO_TIEMPO   = "Tiempo"
SUBTIPO_ENTERO   = "Entero"
SUBTIPO_DECIMAL  = "Decimal"
SUBTIPO_BOOLEANO = "Booleano"
SUBTIPO_CADENA   = "Cadena"


# Una política se compone de (Acción, Operación, Modulo).
# Acción     ∈ {"Permitir", "Denegar", "Acceder", "Validar"}
# Operación  ∈ {"Consultar", "Registrar", "Modificar", "Eliminar", "Insertar", None}
# Modulo     ∈ identificador definido tipo Modulo
Politica = Tuple[str, Optional[str], str]


@dataclass
class Symbol:
    """Una fila de la Tabla de Símbolos."""
    identificador: str
    tipo_dato: str
    sub_tipo: Optional[str] = None
    rol_vinculado: Optional[str] = None
    politicas: List[Politica] = field(default_factory=list)
    linea: int = 0
    columna: int = 0
    es_global: bool = False  # True para variables ABAC inyectadas

    def resumen(self) -> str:
        """Texto amigable usado por la GUI."""
        pol = "—"
        if self.politicas:
            pol = ", ".join(
                f"({a},{op or '·'},{m})" for a, op, m in self.politicas
            )
        return (
            f"{self.identificador} | {self.tipo_dato} | "
            f"{self.sub_tipo or '—'} | {self.rol_vinculado or '—'} | {pol}"
        )


class SymbolTable:
    """
    Diccionario estructurado de símbolos.
    Llave: identificador en minúsculas (case-insensitive).
    Valor: Symbol con el lexema original conservado.

    Al instanciarse inyecta el "Contexto Global" (variables ABAC) tal
    como exige el documento (Paso 0 — Inicialización Automática).
    """

    def __init__(self, inicializar_globales: bool = True):
        self._tabla: Dict[str, Symbol] = {}
        if inicializar_globales:
            self._inyectar_contexto_global()

    # ---------- Contexto global ABAC ----------

    def _inyectar_contexto_global(self) -> None:
        """
        Variables de entorno disponibles desde la línea 1 sin haber
        sido declaradas con `Definir`. Previenen errores ERR_SEM_02 al
        evaluar reglas ABAC como `Si Horario < 18 Entonces`.

        Nota de implementación:
            El documento de Diseño Semántico nombra las variables como
            `Monto_Venta` y `Ubicacion_IP`, pero la fase Léxica del
            lenguaje Enigma prohíbe el carácter `_` en identificadores
            (Caso 7 de la Propuesta Léxica). Por compatibilidad con el
            lexer real las exponemos en camelCase (`MontoVenta`,
            `UbicacionIP`); el resultado funcional es el mismo.
        """
        globales: List[Tuple[str, str]] = [
            ("Horario",      SUBTIPO_TIEMPO),
            ("MontoVenta",   SUBTIPO_ENTERO),
            ("UbicacionIP",  SUBTIPO_CADENA),
        ]
        for nombre, subtipo in globales:
            self._tabla[nombre.lower()] = Symbol(
                identificador=nombre,
                tipo_dato=TIPO_VARIABLE_ENTORNO,
                sub_tipo=subtipo,
                es_global=True,
            )

    # ---------- API pública ----------

    def declarar(self, simbolo: Symbol) -> Optional[Symbol]:
        """
        Registra un símbolo. Si ya existía, retorna el símbolo previo
        para que el llamador genere el ERR_SEM_01. NO sobreescribe.
        """
        clave = simbolo.identificador.lower()
        if clave in self._tabla:
            return self._tabla[clave]
        self._tabla[clave] = simbolo
        return None

    def buscar(self, nombre: str) -> Optional[Symbol]:
        if not nombre:
            return None
        return self._tabla.get(nombre.lower())

    def existe(self, nombre: str) -> bool:
        return nombre is not None and nombre.lower() in self._tabla

    def eliminar(self, nombre: str) -> None:
        """Elimina un símbolo de la tabla si existe. Útil para variables temporales
        como el error_id de los bloques Intentar/Atrapar."""
        if nombre:
            self._tabla.pop(nombre.lower(), None)

    def actualizar_rol_vinculado(self, usuario: str, rol: str) -> None:
        sym = self.buscar(usuario)
        if sym:
            sym.rol_vinculado = rol

    def agregar_politica(self, rol: str, politica: Politica) -> None:
        sym = self.buscar(rol)
        if sym:
            sym.politicas.append(politica)

    def filas(self) -> List[Symbol]:
        """Lista ordenada para presentación en la GUI."""
        # Globales primero (Horario…), luego declaraciones del usuario.
        return sorted(
            self._tabla.values(),
            key=lambda s: (not s.es_global, s.linea, s.identificador.lower()),
        )

    def __len__(self) -> int:
        return len(self._tabla)

    def __iter__(self):
        return iter(self._tabla.values())

    def __contains__(self, item) -> bool:
        return self.existe(item)
