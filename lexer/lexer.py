import re
from .tokens import TipoToken, Token, PALABRAS_RESERVADAS
from .error_handler import ErrorHandler

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

        # 2. Literales
        ('NUMERO_DEC', r'[0-9]+\.[0-9]+'),  # Ej: 15.5
        ('NUMERO_ENT', r'[0-9]+'),          # Ej: 1, 10
        ('CADENA',     r'"[^"]*"'),         # Ej: "cualquier texto"
        
        # Captura de cadenas sin cerrar (Error Léxico 02) 
        ('CADENA_SIN_CERRAR', r'"[^"]*'), 

        # 3. Identificadores (Nombres de usuario, roles variables...)
        # Los identificadores pueden empezar por letra seguida de letras, números o _ -> [a-z][a-z0-9_]*
        ('IDENTIFICADOR', r'[a-zA-Z][a-zA-Z0-9_]*'),

        # 4. Operadores Relacionales
        ('OP_REL', r'==|!=|=>|=<|>=|<=|>|<'),
        
        # 5. Operador Asignación
        ('ASIGNACION', r'='),

        # 6. Símbolos (Agrupación / Puntuación)
        ('SIMBOLO', r'[(){}\[\];,]'),
        
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
                
            elif tipo_match == 'IDENTIFICADOR':
                # Puede ser un IDENTIFICADOR real o una PALABRA_RESERVADA encubierta
                if lexema in PALABRAS_RESERVADAS:
                    tokens.append(Token(lexema, TipoToken.PALABRA_RESERVADA, linea_actual, columna))
                else:
                    tokens.append(Token(lexema, TipoToken.IDENTIFICADOR, linea_actual, columna))
                    
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
