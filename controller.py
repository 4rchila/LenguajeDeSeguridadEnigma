from gui.main_window import MainWindow


class Controller:
    
    def __init__(self, window: MainWindow):
        self.window = window
        self._connect_signals()

    def _connect_signals(self):
        self.window.action_analyze.triggered.connect(self.on_analyze)
        self.window.error_panel.navigate_to_line.connect(self.window.navigate_to_line)

    def on_analyze(self):
        code = self.window.get_code().strip()
        if not code:
            self.window.statusBar().showMessage(
                "El editor está vacío. Escribe código para analizar.", 3000
            )
            return

        try:
            tokens, errors = _demo_tokenize(code)

            self.window.show_results(tokens, errors)

        except Exception as exc:
            self.window.statusBar().showMessage(
                f"Error inesperado durante el análisis: {exc}", 6000
            )

from dataclasses import dataclass
from enum import Enum, auto


class TipoToken(Enum):
    PALABRA_RESERVADA = auto()
    IDENTIFICADOR     = auto()
    NUMERO            = auto()
    OPERADOR          = auto()
    SIMBOLO           = auto()
    CADENA            = auto()
    ERROR_LEXICO      = auto()


@dataclass
class Token:
    lexema: str
    tipo:   TipoToken
    linea:  int
    col:    int


PALABRAS_RESERVADAS = {
    "Definir", "Rol", "Usuario", "Modulo", "Permitir", "Denegar",
    "Acceder", "Validar", "Consultar", "Registrar", "Modificar",
    "Eliminar", "Insertar", "Si", "Entonces", "Sino", "Mientras",
    "Elegir", "Caso", "Terminar", "Intentar", "Atrapar", "Error",
    "Verdadero", "Falso", "Cadena", "Horario", "Y", "O", "No",
    "Mostrar", "Devolver",
}

OPERADORES = {"==", "!=", "=>", "=<", "=", "<", ">"}
SIMBOLOS   = set("(){}[];,\\")

import re

_TOKEN_SPEC = [
    ("CADENA",   r'"[^"]*"'),
    ("NUMERO",   r'\b\d+\b'),
    ("OP2",      r'==|!=|=>|=<'),
    ("OP1",      r'[=<>]'),
    ("SIMBOLO",  r'[(){}\[\];,\\]'),
    ("WORD",     r'\b[A-Za-záéíóúÁÉÍÓÚñÑ_][A-Za-záéíóúÁÉÍÓÚñÑ0-9_]*\b'),
    ("SKIP",     r'[ \t]+'),
    ("NEWLINE",  r'\n'),
    ("ERROR",    r'.'),
]

_MASTER = re.compile(
    "|".join(f"(?P<{name}>{pat})" for name, pat in _TOKEN_SPEC)
)


def _demo_tokenize(code: str):
    tokens = []
    line = 1
    line_start = 0

    for m in _MASTER.finditer(code):
        kind  = m.lastgroup
        value = m.group()
        col   = m.start() - line_start + 1

        if kind == "NEWLINE":
            line += 1
            line_start = m.end()
        elif kind == "SKIP":
            pass
        elif kind == "CADENA":
            tokens.append(Token(value, TipoToken.CADENA, line, col))
        elif kind == "NUMERO":
            tokens.append(Token(value, TipoToken.NUMERO, line, col))
        elif kind in ("OP2", "OP1"):
            tokens.append(Token(value, TipoToken.OPERADOR, line, col))
        elif kind == "SIMBOLO":
            tokens.append(Token(value, TipoToken.SIMBOLO, line, col))
        elif kind == "WORD":
            tipo = (TipoToken.PALABRA_RESERVADA
                    if value in PALABRAS_RESERVADAS
                    else TipoToken.IDENTIFICADOR)
            tokens.append(Token(value, tipo, line, col))
        else:  # ERROR
            tokens.append(Token(value, TipoToken.ERROR_LEXICO, line, col))

    errors = [t for t in tokens if t.tipo == TipoToken.ERROR_LEXICO]
    return tokens, errors