"""
Paquete del Analizador Semántico (Fase 3) — Mini Compilador "Enigma"
====================================================================
Implementa el análisis estático del Árbol de Sintaxis Abstracta (AST)
producido por el parser. Verifica reglas RBAC + ABAC, integridad de
referencias y tipado fuerte siguiendo el documento de diseño:
"Diseño Analizador Semántico - Enigma".

Componentes principales expuestos:
    - SemanticAnalyzer  → Recorre el AST y dispara errores semánticos.
    - SymbolTable       → Diccionario estructurado de identificadores.
    - Symbol            → Fila individual de la tabla de símbolos.
    - SemanticError     → Excepción/objeto-error con código ERR_SEM_XX.
"""

from .semantic_errors import SemanticError, CODIGOS_SEMANTICOS
from .symbol_table import Symbol, SymbolTable
from .semantic_analyzer import SemanticAnalyzer

__all__ = [
    "SemanticError",
    "CODIGOS_SEMANTICOS",
    "Symbol",
    "SymbolTable",
    "SemanticAnalyzer",
]
