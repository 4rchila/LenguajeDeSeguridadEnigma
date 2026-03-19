import re
from .tokens import TipoToken, Token, PALABRAS_RESERVADAS
from .error_handler import ErrorHandler


def _distancia_edicion(a: str, b: str) -> int:
    """Distancia de Levenshtein entre dos cadenas (inserción, borrado, sustitución)."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    n, m = len(a), len(b)
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i]
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[m]


def _sugerencia_palabra_reservada(identificador: str) -> str | None:
    """
    Si el identificador es una palabra reservada mal escrita (distancia 1),
    devuelve la palabra reservada sugerida; si no, None.
    Solo considera palabras con longitud similar para evitar falsos positivos.
    """
    id_lower = identificador.lower()
    # Evitar falsos positivos: si el "identificador" trae números (ej. Usuario1)
    # o es demasiado corto (ej. variables de una letra como "e"), no sugerimos.
    if any(ch.isdigit() for ch in id_lower):
        return None
    if len(id_lower) < 3:
        return None
    if not id_lower.isalpha():
        return None
    if id_lower in PALABRAS_RESERVADAS:
        return None
    for reservada in PALABRAS_RESERVADAS:
        if abs(len(id_lower) - len(reservada)) > 2:
            continue
        if _distancia_edicion(id_lower, reservada) == 1:
            return reservada
    return None


class Lexer:
    """
    Analizador Léxico principal.
    Convierte el flujo de caracteres (código fuente) en un flujo de Tokens.
    """

    # Definición de las especificaciones léxicas (Regex).
    patrones_lexicos = [
        # 1. Ignorables
        ('COMENTARIO', r'//.*'),     # Comentarios de una sola línea
        ('WHITESPACE', r'[ \t]+'),
        ('NEWLINE',    r'\n'),

        # 2. Literales (cadenas NO pueden contener salto de línea — Caso 8)
        ('NUMERO_DEC', r'[0-9]+\.[0-9]+'),   # Ej: 15.5
        ('ID_MAL_NUMERO', r'[0-9]+[a-zA-Z][a-zA-Z0-9_]*'),  # 123Gerente — Error (antes que NUMERO_ENT)
        ('NUMERO_ENT', r'[0-9]+'),           # Ej: 1, 10
        ('CADENA', r'"[^\n"]*"'),            # "texto" sin newline dentro (evita capturar hasta la siguiente ")
        ('CADENA_SIN_CERRAR', r'"[^\n"]*'),  # Cadena sin cerrar en la misma línea (Error 02)

        # 3. Identificadores (solo letras y números; '_' no permitido — Caso 7)
        ('ID_MAL_GUION', r'_[a-zA-Z0-9_]*'),  # _usuario — Error (uso de _ no permitido)
        ('IDENTIFICADOR', r'[a-zA-Z][a-zA-Z0-9]*'),

        # 4. Operadores Relacionales
        ('OP_REL', r'==|!=|=>|=<|>=|<=|>|<'),
        
        # 5. Operador Asignación
        ('ASIGNACION', r'='),

        # 6. Símbolos (Agrupación / Puntuación)
        # Incluye ':' para soportar el formato 'Caso "X":'
        ('SIMBOLO', r'[(){}\[\];,:]'),
        
        # Otros Símbolos especiales permitidos
        ('BACKSLASH', r'\\'),
        ('NEGACION_SOLA', r'!'), 

        # 7. Reglas para identificar errores comunes
        # Error Léxico 03 - Números mal formados (ej. 15.5.2)
        ('NUMERO_MAL', r'[0-9]+(?:\.[0-9]+){2,}'),
        
        # Error Léxico 01 - Cualquier otro carácter no reconocido (match 1 carácter)
        ('ERROR', r'.'), 
    ]

    def __init__(self):
        # Compilar los patrones en una sola expresión regular usando grupos con nombre `(?P<nombre>regex)`
        patrones_combinados = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.patrones_lexicos)
        self.regex = re.compile(patrones_combinados)
        
        self.errores = ErrorHandler()

    def tokenize(self, codigo_fuente: str) -> list[Token]:
        """
        Función central para tokenizar el código fuente.
        """
        tokens: list[Token] = []
        self.errores.limpiar_errores()

        linea_actual = 1
        # pos_inicio_linea nos ayuda a calcular la columna
        pos_inicio_linea = 0
        
        codigo_procesar = codigo_fuente.lower()

        for match in self.regex.finditer(codigo_procesar):
            tipo_match = match.lastgroup
            lexema = match.group(tipo_match)
            # Para la columna exacta, consideramos el index del match menos el inicio de la línea.
            columna = match.start() - pos_inicio_linea + 1

            if tipo_match == 'WHITESPACE':
                continue
            
            elif tipo_match == 'COMENTARIO':
                continue
            
            elif tipo_match == 'NEWLINE':
                linea_actual += 1
                pos_inicio_linea = match.end()
                continue
                
            elif tipo_match == 'ID_MAL_GUION':
                lexema_original = codigo_fuente[match.start():match.end()]
                self.errores.registrar_error(
                    "ERROR_LEX_06",
                    lexema_original,
                    linea_actual,
                    columna,
                    "Identificador mal formado: uso de _ no permitido"
                )
                tokens.append(Token(lexema_original, TipoToken.ERROR_LEXICO, linea_actual, columna))

            elif tipo_match == 'IDENTIFICADOR':
                # Puede ser PALABRA_RESERVADA, IDENTIFICADOR válido, o palabra reservada mal escrita
                if lexema in PALABRAS_RESERVADAS:
                    tokens.append(Token(lexema, TipoToken.PALABRA_RESERVADA, linea_actual, columna))
                else:
                    sugerencia = _sugerencia_palabra_reservada(lexema)
                    if sugerencia is not None:
                        lexema_original = codigo_fuente[match.start():match.end()]
                        self.errores.registrar_error(
                            "ERROR_LEX_04",
                            lexema_original,
                            linea_actual,
                            columna,
                            f"Palabra reservada mal escrita: '{lexema_original}'. ¿Quiso decir '{sugerencia}'?"
                        )
                        tokens.append(Token(lexema_original, TipoToken.ERROR_LEXICO, linea_actual, columna))
                    else:
                        tokens.append(Token(lexema, TipoToken.IDENTIFICADOR, linea_actual, columna))
                    
            elif tipo_match == 'ID_MAL_NUMERO':
                lexema_original = codigo_fuente[match.start():match.end()]
                self.errores.registrar_error(
                    "ERROR_LEX_05",
                    lexema_original,
                    linea_actual,
                    columna,
                    "Identificador mal formado: empieza con número"
                )
                tokens.append(Token(lexema_original, TipoToken.ERROR_LEXICO, linea_actual, columna))

            elif tipo_match == 'NUMERO_ENT':
                tokens.append(Token(lexema, TipoToken.NUMERO_ENT, linea_actual, columna))
                
            elif tipo_match == 'NUMERO_DEC':
                tokens.append(Token(lexema, TipoToken.NUMERO_DEC, linea_actual, columna))
                
            elif tipo_match == 'CADENA':
                lexema_original = codigo_fuente[match.start():match.end()]
                tokens.append(Token(lexema_original, TipoToken.CADENA, linea_actual, columna))
                
            elif tipo_match == 'OP_REL' or tipo_match == 'ASIGNACION':
                tokens.append(Token(lexema, TipoToken.OPERADOR, linea_actual, columna))
                
            elif tipo_match == 'SIMBOLO' or tipo_match == 'BACKSLASH' or tipo_match == 'NEGACION_SOLA':
                tokens.append(Token(lexema, TipoToken.SIMBOLO, linea_actual, columna))
                
            # MANEJO DE ERRORES LÉXICOS
            elif tipo_match == 'CADENA_SIN_CERRAR':
                lexema_original = codigo_fuente[match.start():match.end()]
                self.errores.registrar_error(
                    "ERROR_LEX_02", lexema_original, linea_actual, columna, "Cadena de texto sin comilla de cierre"
                )
                tokens.append(Token(lexema_original, TipoToken.ERROR_LEXICO, linea_actual, columna))
                
            elif tipo_match == 'NUMERO_MAL':
                self.errores.registrar_error(
                    "ERROR_LEX_03", lexema, linea_actual, columna, "Número mal formado (Múltiples puntos decimales)"
                )
                tokens.append(Token(lexema, TipoToken.ERROR_LEXICO, linea_actual, columna))

            elif tipo_match == 'ERROR':
                lexema_original = codigo_fuente[match.start():match.end()]
                self.errores.registrar_error(
                    "ERROR_LEX_01", lexema_original, linea_actual, columna, "Carácter no reconocido (Foráneo)"
                )
                tokens.append(Token(lexema_original, TipoToken.ERROR_LEXICO, linea_actual, columna))

        return tokens
