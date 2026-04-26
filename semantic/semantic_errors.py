"""
Catálogo y entidad de errores semánticos.
=========================================
Implementa los 7 códigos ERR_SEM_XX descritos en el documento
"Diseño Analizador Semántico - Enigma" (sección 2 — Catálogo).

Filosofía:
    - "Fail-Fast": al detectar la primera inconsistencia, el análisis
      lanza la excepción y aborta. Aún así guardamos la lista para que
      la GUI pueda mostrarla amigablemente.
    - "Zero Trust": ningún identificador se da por bueno hasta que se
      certifica contra la Tabla de Símbolos.
"""

from dataclasses import dataclass
from typing import Optional


CODIGOS_SEMANTICOS = {
    "ERR_SEM_01": "Redeclaración",
    "ERR_SEM_02": "Entidad No Declarada",
    "ERR_SEM_03": "Incompatibilidad de Tipos",
    "ERR_SEM_04": "Dominio Inválido",
    "ERR_SEM_05": "Expresión No Booleana",
    "ERR_SEM_06": "Operación Inválida entre Tipos",
    "ERR_SEM_07": "Conflicto de Políticas de Seguridad",
}


@dataclass
class SemanticError(Exception):
    """
    Representa una violación a las reglas semánticas del lenguaje.

    Atributos:
        codigo:   ERR_SEM_01 … ERR_SEM_07
        mensaje:  Texto humano y explicativo
        linea:    Línea del archivo fuente donde se origina
        columna:  Columna correspondiente
        lexema:   Token/lexema que provocó el error (opcional)
    """
    codigo: str
    mensaje: str
    linea: int = 0
    columna: int = 0
    lexema: Optional[str] = None

    def __post_init__(self):
        super().__init__(self.mensaje)

    @property
    def clasificacion(self) -> str:
        return CODIGOS_SEMANTICOS.get(self.codigo, "Error Semántico Desconocido")

    def __str__(self) -> str:
        prefijo = f"[Abortado] {self.codigo}"
        donde = f"línea {self.linea}" if self.linea else "ubicación desconocida"
        return f"{prefijo} en {donde}: {self.mensaje}"
