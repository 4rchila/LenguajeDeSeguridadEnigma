from typing import List, Optional
from lexer.tokens import Token, TipoToken
import parser.ast_nodes as ast

class ParserError(Exception):
    """
    Excepción personalizada para manejar errores de sintaxis en el AST.
    Almacena el mensaje detallado y el último token procesado para fácil 
    inspección gráfica y trazabilidad posterior.
    """
    def __init__(self, message: str, token: Optional[Token]):
        super().__init__(message)
        self.message = message
        self.token = token


class Parser:
    """
    Analizador Sintáctico Descendente Recursivo LL(1).
    Procesa un flujo lineal de tokens previamente generados por el 
    Analizador Léxico y construye un Árbol de Sintaxis Abstracta (AST) 
    jerárquico con base en las reglas gramaticales BNF del lenguaje.
    """
    def __init__(self, tokens: List[Token]):
        # Se omiten silenciosamente los tokens que originalmente se 
        # consideraron un error léxico, para no causar ruido innecesario
        # en la matemática del parser. Dependiendo el pipeline de compiladores, 
        # a veces se detiene directamente si hay errores léxicos previos.
        self.tokens = [t for t in tokens if t.tipo != TipoToken.ERROR_LEXICO]
        self.current_pos = 0
        self.errores = []

    # --- UTILIDADES CORE DEL CÓDIGO (LL(1) TOOLS) ---

    def get_current_token(self) -> Optional[Token]:
        if self.current_pos < len(self.tokens):
            return self.tokens[self.current_pos]
        return None

    def get_previous_token(self) -> Optional[Token]:
        """Retorna el token anterior al puntero actual (útil para reportar la línea correcta)."""
        if self.current_pos > 0:
            return self.tokens[self.current_pos - 1]
        return None

    def advance(self):
        """Avanza el puntero de tokens una posición."""
        self.current_pos += 1

    def is_at_end(self) -> bool:
        return self.current_pos >= len(self.tokens)

    # MATCH POR TIPO DE TOKEN (Ej. Identificador, Número, Cadena)
    def match_tipo(self, tipo_esperado: TipoToken) -> Token:
        token = self.get_current_token()
        if token and token.tipo == tipo_esperado:
            self.advance()
            return token
        
        lexema_encontrado = token.lexema if token else "EOF (Fin del Archivo)"
        # Reportar contra el token problemático. Si es un delimitador faltante (ej. ;),
        # el token actual ya pertenece a otra línea; usar el previo es más preciso.
        error_token = token if token else self.get_previous_token()
        raise ParserError(f"Error Sintáctico: Se esperaba un '{tipo_esperado.name}', pero se encontró '{lexema_encontrado}'.", error_token)

    def is_match_tipo(self, tipo: TipoToken) -> bool:
        """Sólo revisa el token actual (lookahead sin consumir)."""
        token = self.get_current_token()
        return token is not None and token.tipo == tipo

    # MATCH POR VALOR LÉXICO (Específico de nuestro lenguaje: "Definir", ";", "{")
    def match_valor(self, valor_esperado: str, ignorar_case=True) -> Token:
        token = self.get_current_token()
        if token:
            valor_actual = token.lexema.lower() if ignorar_case else token.lexema
            esperado = valor_esperado.lower() if ignorar_case else valor_esperado
            if valor_actual == esperado:
                self.advance()
                return token
        
        lexema_encontrado = token.lexema if token else "EOF (Fin del Archivo)"
        # Para delimitadores faltantes (;, }, )), reportar la línea del token previo
        # ya que el token actual pertenece a la siguiente instrucción.
        delimitadores = {";", "}", ")", "Terminar"}
        if valor_esperado in delimitadores:
            error_token = self.get_previous_token() or token
        else:
            error_token = token if token else self.get_previous_token()
        raise ParserError(f"Error Sintáctico: Se esperaba '{valor_esperado}' después de '{error_token.lexema if error_token else '?'}', pero se encontró '{lexema_encontrado}'.", error_token)

    def is_match_valor(self, valor: str, ignorar_case=True) -> bool:
        """Sólo revisa el token actual (lookahead sin consumir)."""
        token = self.get_current_token()
        if token:
            v_actual = token.lexema.lower() if ignorar_case else token.lexema
            v_esperado = valor.lower() if ignorar_case else valor
            return v_actual == v_esperado
        return False
        
    # --- FUNCIONES PURAMENTE MATEMÁTICAS EN MÚLTIPLES NIVELES DESDE EL BNF ---
    
    def parse(self) -> ast.ProgramNode:
        """Punto de Entrada: <programa> ::= <lista_instrucciones>"""
        start_token = self.get_current_token()
        instrucciones = self.parse_lista_instrucciones(dentro_de_bloque=False)
        end_token = self.tokens[-1] if self.tokens else None
        
        # Consumir cualquier token restante y reportar errores específicos
        while not self.is_at_end():
            token_sobrante = self.get_current_token()
            if token_sobrante.tipo == TipoToken.EOF:
                break
            if token_sobrante.lexema == "}":
                self.errores.append(ParserError(
                    f"Error Sintáctico: Se encontró '}}' sin un '{{' de apertura correspondiente.",
                    token_sobrante
                ))
            else:
                self.errores.append(ParserError(
                    f"Error Sintáctico: Código no reconocido '{token_sobrante.lexema}' fuera de una instrucción.",
                    token_sobrante
                ))
            self.advance()
            
        return ast.ProgramNode(instrucciones, start_token, end_token)
        
    def parse_lista_instrucciones(self, dentro_de_bloque=True) -> List[ast.ASTNode]:
        """<lista_instrucciones> ::= <instruccion> <lista_instrucciones> | <instruccion>"""
        instrucciones = []
        # Terminadores contextuales: '}' solo detiene si estamos dentro de un bloque { }
        terminadores = {"atrapar", "sino", "caso"}
        if dentro_de_bloque:
            terminadores.add("}")
        
        while not self.is_at_end():
            t_curr = self.get_current_token()
            if t_curr and t_curr.lexema.lower() in terminadores:
                break
            
            # En el nivel superior, un '}' suelto es un error (llave huérfana)
            if not dentro_de_bloque and t_curr and t_curr.lexema == "}":
                self.errores.append(ParserError(
                    f"Error Sintáctico: Se encontró '}}' sin un '{{' de apertura correspondiente.",
                    t_curr
                ))
                self.advance()
                continue
                
            try:
                inst = self.parse_instruccion()
                if inst:
                    instrucciones.append(inst)
            except ParserError as pe:
                self.errores.append(pe)
                self.synchronize()
                
        return instrucciones

    def synchronize(self):
        """Recuperación modo pánico: avanza buscando el inicio de la siguiente instrucción válida."""
        sync_keywords = {"definir", "rol", "usuario", "permitir", "denegar", "acceder", 
                         "validar", "si", "mientras", "elegir", "intentar", "mostrar", "devolver"}
        
        # Si el token actual ya es un inicio de instrucción, NO avanzamos.
        # Esto evita saltarse la siguiente instrucción válida.
        token = self.get_current_token()
        if token and token.lexema.lower() in sync_keywords:
            return
        
        while not self.is_at_end():
            token = self.get_current_token()
            
            # Si tocamos un delimitador principal (;), lo consumimos y salimos
            if token.lexema == ";":
                self.advance()
                return
            
            # Si hallamos un cierre de bloque, dejamos que el nivel superior lo procese
            if token.lexema == "}":
                return
            
            # Si encontramos una llave de apertura, saltamos el bloque completo { ... }
            # Esto evita que el sync "robe" la } de un bloque anidado.
            if token.lexema == "{":
                self._skip_balanced_block()
                return
                
            self.advance()
            
            # Si el SIGUIENTE token es inicio de otra instrucción general, nos detenemos ahí
            next_token = self.get_current_token()
            if next_token and next_token.lexema.lower() in sync_keywords:
                return

    def _skip_balanced_block(self):
        """Salta un bloque { ... } completo, respetando anidamiento de llaves."""
        self.advance()  # Consumir '{'
        depth = 1
        while not self.is_at_end() and depth > 0:
            t = self.get_current_token()
            if t.lexema == "{":
                depth += 1
            elif t.lexema == "}":
                depth -= 1
            self.advance()

    def parse_bloque(self) -> ast.BloqueNode:
        """<bloque> ::= "{" <lista_instrucciones> "}" | <instruccion>"""
        start_token = self.get_current_token()
        if self.is_match_valor("{"):
            open_brace = self.match_valor("{")  # Consumir '{'
            instrucciones = self.parse_lista_instrucciones(dentro_de_bloque=True)
            
            # Intentar cerrar el bloque con '}'
            if self.is_match_valor("}"):
                end_token = self.match_valor("}")
            else:
                # Falta la llave de cierre: reportar apuntando a donde se abrió
                self.errores.append(ParserError(
                    f"Error Sintáctico: Falta '}}' para cerrar el bloque abierto en la línea {open_brace.linea}.",
                    open_brace
                ))
                end_token = self.get_previous_token() or open_brace
            return ast.BloqueNode(instrucciones, start_token, end_token)
        else:
            # Una sola rama lógica si omiten { }
            inst = self.parse_instruccion()
            return ast.BloqueNode([inst], start_token, inst.end_token if inst else start_token)

    def parse_instruccion(self) -> ast.ASTNode:
        """Router maestro de instrucciones BNF top level."""
        # Se analizan tokens de Anticipación (Lookahead) para desviar al árbol correcto.
        
        if self.is_match_valor("Definir"):
            inst = self.parse_definicion_estructura()
            self.match_valor(";")
            return inst
            
        elif self.is_match_valor("Rol") or self.is_match_valor("Usuario"):
            inst = self.parse_asignacion()
            self.match_valor(";")
            return inst
            
        elif (self.is_match_valor("Permitir") or self.is_match_valor("Denegar") or 
              self.is_match_valor("Acceder") or self.is_match_valor("Validar")):
            inst = self.parse_regla_seguridad()
            self.match_valor(";")
            return inst
            
        elif self.is_match_valor("Si") or self.is_match_valor("Mientras") or self.is_match_valor("Elegir"):
            return self.parse_sentencia_control()
            
        elif self.is_match_valor("Intentar"):
            return self.parse_manejo_error()
            
        elif self.is_match_valor("Mostrar") or self.is_match_valor("Devolver"):
            inst = self.parse_sentencia_salida()
            self.match_valor(";")
            return inst
            
        else:
            token = self.get_current_token()
            raise ParserError(f"Error Sintáctico: Instrucción inválida, no se reconoce como base legítima del lenguaje.", token)

    # ... SUB-ANÁLISIS DE LA GRAMÁTICA ...

    def parse_definicion_estructura(self) -> ast.ASTNode:
        """<definicion_estructura> ::= "Definir" <tipo_entidad> <id>"""
        t_definir = self.match_valor("Definir")
        t_tipo = self.get_current_token()
        
        if self.is_match_valor("Rol") or self.is_match_valor("Usuario") or self.is_match_valor("Modulo"):
            self.advance()  # Consumir el tipo_entidad
            t_id = self.match_tipo(TipoToken.IDENTIFICADOR)
            return ast.DefinicionEntidadNode(t_tipo.lexema, t_id.lexema, t_definir, t_id)
        
        raise ParserError(f"Se esperaba 'Rol', 'Usuario' o 'Modulo' despues de 'Definir', no '{t_tipo.lexema if t_tipo else 'EOF'}'.", t_tipo)

    def parse_asignacion(self) -> ast.ASTNode:
        """
        Puede derivar en dos vértices:
        <asignacion_rol> ::= "Rol" <id> "=" <accion_acceso> <id>
        <asignacion_variable> ::= "Usuario" <id> "=" "Rol" <id>
        """
        t_start = self.get_current_token()
        
        if self.is_match_valor("Rol"):
            self.match_valor("Rol")
            t_id = self.match_tipo(TipoToken.IDENTIFICADOR)
            self.match_valor("=")
            t_accion = self.get_current_token()
            
            # Acciones puras admitibles asignables al Rol (Permiten construir una <regla_seguridad>)
            if t_accion and (self.is_match_valor("Permitir") or self.is_match_valor("Denegar") or 
                             self.is_match_valor("Acceder") or self.is_match_valor("Validar")):
                regla_node = self.parse_regla_seguridad()
                return ast.AsignacionRolAccionNode(t_id.lexema, regla_node, t_start, regla_node.end_token)
            else:
                 raise ParserError("Se esperaba una accion de acceso (Ej. 'Acceder', 'Permitir') tras un signo '=' para vincular a un Rol.", t_accion)
            
        elif self.is_match_valor("Usuario"):
            self.match_valor("Usuario")
            t_id_usr = self.match_tipo(TipoToken.IDENTIFICADOR)
            self.match_valor("=")
            self.match_valor("Rol")
            t_id_rol = self.match_tipo(TipoToken.IDENTIFICADOR)
            return ast.AsignacionUsuarioRolNode(t_id_usr.lexema, t_id_rol.lexema, t_start, t_id_rol)
            
    def parse_regla_seguridad(self) -> ast.ASTNode:
        """<regla_seguridad> ::= <accion_acceso> <operacion_negocio> <id> | <accion_acceso> <id>"""
        t_start = self.get_current_token()
        accion = t_start.lexema
        self.advance() # consumir Permitir, Denegar, etc.
        
        t_siguiente = self.get_current_token()
        operacion = None
        
        # Detectar doble acción de acceso (Ej: "Denegar Permitir Reportes;")
        acciones_acceso = ["permitir", "denegar", "acceder", "validar"]
        if t_siguiente and t_siguiente.lexema.lower() in acciones_acceso:
            raise ParserError(
                f"Error Sintáctico: Doble acción de acceso detectada. '{accion}' no puede ir seguido de '{t_siguiente.lexema}'. "
                f"Use una operación de negocio (Consultar, Registrar, etc.) o un identificador.",
                t_siguiente
            )
        
        ops_negocio = ["consultar", "registrar", "modificar", "eliminar", "insertar"]
        if t_siguiente and t_siguiente.lexema.lower() in ops_negocio:
            operacion = t_siguiente.lexema
            self.advance()
            
        t_id_mod = self.match_tipo(TipoToken.IDENTIFICADOR)
        return ast.ReglaSeguridadNode(accion, operacion, t_id_mod.lexema, t_start, t_id_mod)
        
    def parse_sentencia_control(self) -> ast.ASTNode:
        """Bifurcador if_stmt, while_stmt, switch_stmt"""
        if self.is_match_valor("Si"):
            t_start = self.match_valor("Si")
            condicion = self.parse_condicion()
            self.match_valor("Entonces")
            bloque_entonces = self.parse_bloque()
            
            bloque_sino = None
            t_end = bloque_entonces.end_token
            
            if self.is_match_valor("Sino"):
                self.match_valor("Sino")
                bloque_sino = self.parse_bloque()
                t_end = bloque_sino.end_token
                
            return ast.SiEntoncesNode(condicion, bloque_entonces, bloque_sino, t_start, t_end)
            
        elif self.is_match_valor("Mientras"):
            t_start = self.match_valor("Mientras")
            condicion = self.parse_condicion()
            bloque = self.parse_bloque()
            return ast.MientrasNode(condicion, bloque, t_start, bloque.end_token)
            
        elif self.is_match_valor("Elegir"):
            t_start = self.match_valor("Elegir")
            self.match_valor("(")
            t_id = self.match_tipo(TipoToken.IDENTIFICADOR)
            self.match_valor(")")
            self.match_valor("{")
            
            casos = []
            while self.is_match_valor("Caso"):
                try:
                    casos.append(self.parse_caso())
                except ParserError as pe:
                    self.errores.append(pe)
                    self.synchronize()
                
            t_end = self.match_valor("}")
            return ast.ElegirNode(t_id.lexema, casos, t_start, t_end)
            
    def parse_caso(self) -> ast.CasoNode:
        """<caso> ::= "Caso" <valor_literal> ":" <bloque> "Terminar" ";" """
        t_start = self.match_valor("Caso")
        valor = self.parse_valor()
        self.match_valor(":")
        bloque = self.parse_bloque()
        self.match_valor("Terminar")
        self.match_valor(";")
        return ast.CasoNode(valor, bloque, t_start, self.tokens[self.current_pos-1])
        
    def parse_manejo_error(self) -> ast.ASTNode:
        """<manejo_error> ::= "Intentar" <bloque> "Atrapar" "(" "Error" <id> ")" <bloque>"""
        t_start = self.match_valor("Intentar")
        bloque_int = self.parse_bloque()
        self.match_valor("Atrapar")
        self.match_valor("(")
        self.match_valor("Error")
        t_id = self.match_tipo(TipoToken.IDENTIFICADOR)
        self.match_valor(")")
        bloque_atr = self.parse_bloque()
        return ast.IntentarAtraparNode(bloque_int, t_id.lexema, bloque_atr, t_start, bloque_atr.end_token)
        
    def parse_sentencia_salida(self) -> ast.ASTNode:
        """<sentencia_salida> ::= "Mostrar" <valor> | "Devolver" <valor>"""
        t_start = self.get_current_token()
        tipo_salida = t_start.lexema
        self.advance() # consumir 'mostrar' o 'devolver'
        valor = self.parse_valor()
        return ast.SentenciaSalidaNode(tipo_salida, valor, t_start, valor.end_token)
        
    def parse_condicion(self) -> ast.ASTNode:
        """
        Toma una base binaria o unitaria para condicionantes.  
        Ej. "Ventas > 100", o simplemente un flag local "Verdadero".
        """
        v_izq = self.parse_valor()
        t_op = self.get_current_token()
        
        ops_relacionales = ["==", "!=", "<", ">", "<=", ">=", "=>", "=<", "=", "y", "o"]
        
        if t_op and t_op.lexema.lower() in ops_relacionales:
            self.advance()
            v_der = self.parse_valor()
            return ast.CondicionBinariaNode(v_izq, t_op.lexema, v_der, v_izq.start_token, v_der.end_token)
            
        return v_izq # Si no hay operador, expurga expresión regular o identificador puro
        
    def parse_valor(self) -> ast.ASTNode:
        """<valor> ::= <id> | <valor_literal>"""
        t = self.get_current_token()
        if not t:
            raise ParserError("Se esperaba una expresión o valor pero se encontró End-Of-File", self.tokens[-1] if self.tokens else None)
            
        if self.is_match_tipo(TipoToken.IDENTIFICADOR):
            self.advance()
            return ast.IdentificadorNode(t.lexema, t, t)
        elif self.is_match_tipo(TipoToken.NUMERO_ENT) or self.is_match_tipo(TipoToken.NUMERO_DEC):
            self.advance()
            return ast.LiteralNode(t.lexema, "Numero", t, t)
        elif self.is_match_tipo(TipoToken.CADENA):
            self.advance()
            return ast.LiteralNode(t.lexema, "Cadena", t, t)
        elif self.is_match_valor("Verdadero") or self.is_match_valor("Falso"):
            self.advance()
            return ast.LiteralNode(t.lexema, "Logico", t, t)
        else:
             raise ParserError(f"Valor incomprensible detectado: '{t.lexema}'. Solo se admiten identificadores, o primitivas.", t)
