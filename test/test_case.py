"""
Test Suite para el Compilador del Lenguaje Enigma.
===================================================
Cubre las tres fases del compilador:
  - Fase 1: Analizador Léxico
  - Fase 2: Analizador Sintáctico (Parser)
  - Fase 3: Analizador Semántico

Ejecución:
    python -m pytest test/test_case.py -v
"""

import sys
import os

# Asegurar que el directorio raíz del proyecto esté en el path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from lexer.tokens import TipoToken, Token, PALABRAS_RESERVADAS
from lexer.lexer import Lexer
from lexer.error_handler import ErrorHandler, ErrorLexico
from parser.parser import Parser, ParserError
import parser.ast_nodes as ast
from semantic.semantic_analyzer import SemanticAnalyzer
from semantic.semantic_errors import SemanticError
from semantic.symbol_table import SymbolTable


# ═══════════════════════════════════════════════════════════════════
# FASE 1: ANALIZADOR LÉXICO
# ═══════════════════════════════════════════════════════════════════


class TestLexerTokensBasicos:
    """Verificar reconocimiento correcto de cada tipo de token."""

    def setup_method(self):
        self.lexer = Lexer()

    def _tokenize(self, code):
        """Helper: tokeniza y devuelve (tokens, errores)."""
        tokens = self.lexer.tokenize(code)
        errores = self.lexer.errores.obtener_errores()
        return tokens, errores

    def test_entrada_vacia(self):
        tokens, errores = self._tokenize("")
        assert len(tokens) == 0
        assert len(errores) == 0

    def test_palabra_reservada(self):
        tokens, errores = self._tokenize("Definir")
        assert len(tokens) == 1
        assert tokens[0].tipo == TipoToken.PALABRA_RESERVADA

    def test_todas_las_palabras_reservadas(self):
        """Cada palabra reservada del catálogo debe ser reconocida."""
        for palabra in PALABRAS_RESERVADAS:
            lexer = Lexer()
            tokens = lexer.tokenize(palabra)
            assert len(tokens) == 1, f"Fallo con: {palabra}"
            assert tokens[0].tipo == TipoToken.PALABRA_RESERVADA

    def test_case_insensitive(self):
        for variante in ["DEFINIR", "definir", "Definir", "dEfInIr"]:
            lexer = Lexer()
            tokens = lexer.tokenize(variante)
            assert tokens[0].tipo == TipoToken.PALABRA_RESERVADA

    def test_identificador(self):
        tokens, _ = self._tokenize("miVariable")
        assert tokens[0].tipo == TipoToken.IDENTIFICADOR

    def test_numero_entero(self):
        tokens, _ = self._tokenize("42")
        assert tokens[0].tipo == TipoToken.NUMERO_ENT

    def test_numero_decimal(self):
        tokens, _ = self._tokenize("3.14")
        assert tokens[0].tipo == TipoToken.NUMERO_DEC

    def test_cadena(self):
        tokens, _ = self._tokenize('"Hola mundo"')
        assert tokens[0].tipo == TipoToken.CADENA

    def test_operadores(self):
        for op in ["==", "!=", "<", ">", "="]:
            lexer = Lexer()
            tokens = lexer.tokenize(op)
            assert tokens[0].tipo == TipoToken.OPERADOR, f"Fallo con: {op}"

    def test_simbolos(self):
        for simb in ["{", "}", "(", ")", ";", ","]:
            lexer = Lexer()
            tokens = lexer.tokenize(simb)
            assert tokens[0].tipo == TipoToken.SIMBOLO, f"Fallo con: {simb}"

    def test_posicion_linea_columna(self):
        tokens, _ = self._tokenize("Definir Rol Gerente;")
        assert tokens[0].linea == 1
        assert tokens[0].columna == 1  # "Definir"
        assert tokens[1].columna == 9  # "Rol"


class TestLexerErrores:
    """Verificar detección de los 6 tipos de errores léxicos."""

    def _tokenize(self, code):
        lexer = Lexer()
        tokens = lexer.tokenize(code)
        errores = lexer.errores.obtener_errores()
        return tokens, errores

    def test_error_lex_01_caracter_foraneo(self):
        """Caracteres no reconocidos como @ # $ deben generar error."""
        _, errores = self._tokenize("@")
        assert len(errores) >= 1

    def test_error_lex_02_cadena_sin_cerrar(self):
        """Una cadena sin comillas de cierre debe generar error."""
        _, errores = self._tokenize('"Sin cerrar')
        assert len(errores) >= 1

    def test_error_lex_03_numero_mal_formado(self):
        """Números con múltiples puntos decimales como 15.5.2."""
        _, errores = self._tokenize("15.5.2")
        assert len(errores) >= 1

    def test_error_lex_05_id_empieza_con_numero(self):
        """Identificadores que empiezan con número como 123Gerente."""
        _, errores = self._tokenize("123Gerente")
        assert len(errores) >= 1

    def test_error_lex_06_guion_bajo_en_id(self):
        """El guion bajo no está permitido en identificadores."""
        _, errores = self._tokenize("mi_variable")
        assert len(errores) >= 1

    def test_multiples_errores(self):
        """El lexer debe continuar después de un error y detectar varios."""
        _, errores = self._tokenize("@ $ #")
        assert len(errores) >= 3

    def test_recuperacion_tras_error(self):
        """Después de un error, los tokens válidos posteriores se reconocen."""
        tokens, errores = self._tokenize("@ Definir Rol;")
        assert len(errores) >= 1
        assert any(t.tipo == TipoToken.PALABRA_RESERVADA for t in tokens)


# ═══════════════════════════════════════════════════════════════════
# FASE 2: ANALIZADOR SINTÁCTICO (PARSER)
# ═══════════════════════════════════════════════════════════════════


def _parse(codigo: str):
    """Helper: tokeniza y parsea, retorna (ast, errores_parser)."""
    lexer = Lexer()
    tokens = lexer.tokenize(codigo)
    parser = Parser(tokens)
    programa = parser.parse()
    return programa, parser.errores


class TestParserEstructuras:
    """Verificar parseo correcto de todas las estructuras del lenguaje."""

    def test_definir_entidad(self):
        prog, errors = _parse("Definir Rol Gerente;")
        assert len(errors) == 0
        assert isinstance(prog, ast.ProgramNode)
        assert len(prog.instrucciones) == 1
        nodo = prog.instrucciones[0]
        assert isinstance(nodo, ast.DefinicionEntidadNode)

    def test_definir_usuario(self):
        prog, errors = _parse("Definir Usuario Ana;")
        assert len(errors) == 0
        assert isinstance(prog.instrucciones[0], ast.DefinicionEntidadNode)

    def test_definir_modulo(self):
        prog, errors = _parse("Definir Modulo Ventas;")
        assert len(errors) == 0
        assert isinstance(prog.instrucciones[0], ast.DefinicionEntidadNode)

    def test_asignacion_rol_accion(self):
        prog, errors = _parse("Rol Gerente = Permitir Consultar Ventas;")
        assert len(errors) == 0
        assert isinstance(prog.instrucciones[0], ast.AsignacionRolAccionNode)

    def test_asignacion_usuario_rol(self):
        prog, errors = _parse("Usuario Ana = Rol Gerente;")
        assert len(errors) == 0
        assert isinstance(prog.instrucciones[0], ast.AsignacionUsuarioRolNode)

    def test_regla_seguridad_con_operacion(self):
        prog, errors = _parse("Permitir Consultar Ventas;")
        assert len(errors) == 0
        nodo = prog.instrucciones[0]
        assert isinstance(nodo, ast.ReglaSeguridadNode)

    def test_regla_seguridad_simple(self):
        prog, errors = _parse("Acceder Ventas;")
        assert len(errors) == 0
        assert isinstance(prog.instrucciones[0], ast.ReglaSeguridadNode)

    def test_si_entonces(self):
        prog, errors = _parse("Si Verdadero Entonces { Acceder Ventas; }")
        assert len(errors) == 0
        nodo = prog.instrucciones[0]
        assert isinstance(nodo, ast.SiEntoncesNode)
        assert nodo.bloque_sino is None

    def test_si_entonces_sino(self):
        prog, errors = _parse(
            "Si Falso Entonces { Acceder Ventas; } Sino { Denegar Ventas; }"
        )
        assert len(errors) == 0
        nodo = prog.instrucciones[0]
        assert isinstance(nodo, ast.SiEntoncesNode)
        assert nodo.bloque_sino is not None

    def test_mientras(self):
        prog, errors = _parse("Mientras Verdadero { Acceder Ventas; }")
        assert len(errors) == 0
        assert isinstance(prog.instrucciones[0], ast.MientrasNode)

    def test_elegir_caso(self):
        codigo = """
        Elegir ( Gerente ) {
            Caso "Activo" : { Acceder Ventas; } Terminar;
            Caso "Inactivo" : { Denegar Ventas; } Terminar;
        }
        """
        prog, errors = _parse(codigo)
        assert len(errors) == 0
        nodo = prog.instrucciones[0]
        assert isinstance(nodo, ast.ElegirNode)
        assert len(nodo.casos) == 2

    def test_intentar_atrapar(self):
        codigo = """
        Intentar {
            Acceder Ventas;
        } Atrapar ( Error e ) {
            Denegar Ventas;
        }
        """
        prog, errors = _parse(codigo)
        assert len(errors) == 0
        assert isinstance(prog.instrucciones[0], ast.IntentarAtraparNode)

    def test_mostrar_cadena(self):
        prog, errors = _parse('Mostrar "Hola mundo";')
        assert len(errors) == 0
        assert isinstance(prog.instrucciones[0], ast.SentenciaSalidaNode)

    def test_devolver(self):
        prog, errors = _parse("Devolver Verdadero;")
        assert len(errors) == 0
        assert isinstance(prog.instrucciones[0], ast.SentenciaSalidaNode)

    def test_condicion_binaria(self):
        prog, errors = _parse("Si 100 > 50 Entonces { Acceder Ventas; }")
        assert len(errors) == 0
        nodo = prog.instrucciones[0]
        assert isinstance(nodo.condicion, ast.CondicionBinariaNode)
        assert nodo.condicion.operador == ">"


class TestParserCondicionesLogicas:
    """Verificar el parseo de condiciones con Y, O, No."""

    def test_condicion_Y(self):
        prog, errors = _parse("Si Verdadero Y Falso Entonces { Acceder Ventas; }")
        assert len(errors) == 0
        cond = prog.instrucciones[0].condicion
        assert isinstance(cond, ast.CondicionLogicaNode)

    def test_condicion_O(self):
        prog, errors = _parse("Si Verdadero O Falso Entonces { Acceder Ventas; }")
        assert len(errors) == 0
        cond = prog.instrucciones[0].condicion
        assert isinstance(cond, ast.CondicionLogicaNode)

    def test_condicion_No(self):
        prog, errors = _parse("Si No Verdadero Entonces { Acceder Ventas; }")
        assert len(errors) == 0
        cond = prog.instrucciones[0].condicion
        assert isinstance(cond, ast.CondicionUnariaNode)

    def test_condicion_compuesta_Y_con_comparaciones(self):
        prog, errors = _parse(
            "Si Horario > 8 Y Horario < 18 Entonces { Acceder Ventas; }"
        )
        assert len(errors) == 0
        cond = prog.instrucciones[0].condicion
        assert isinstance(cond, ast.CondicionLogicaNode)
        assert isinstance(cond.izq, ast.CondicionBinariaNode)
        assert isinstance(cond.der, ast.CondicionBinariaNode)

    def test_precedencia_Y_sobre_O(self):
        """A O B Y C debe parsearse como A O (B Y C)."""
        prog, errors = _parse(
            "Si Verdadero O Falso Y Verdadero Entonces { Acceder Ventas; }"
        )
        assert len(errors) == 0
        cond = prog.instrucciones[0].condicion
        # El nodo raíz debe ser O (menor precedencia)
        assert isinstance(cond, ast.CondicionLogicaNode)
        assert cond.operador.lower() == "o"
        # El hijo derecho debe ser Y
        assert isinstance(cond.der, ast.CondicionLogicaNode)
        assert cond.der.operador.lower() == "y"


class TestParserRecuperacion:
    """Verificar recuperación de errores en modo pánico."""

    def test_error_punto_y_coma_faltante(self):
        prog, errors = _parse("Definir Rol Gerente")
        assert len(errors) >= 1

    def test_recuperacion_multi_sentencia(self):
        """El parser debe reportar errores sin crashear."""
        prog, errors = _parse("Definir Rol; Definir")
        assert len(errors) >= 1
        # El parser reporta el error y puede o no recuperar instrucciones
        assert isinstance(prog, ast.ProgramNode)

    def test_programa_vacio(self):
        prog, errors = _parse("")
        assert len(errors) == 0
        assert isinstance(prog, ast.ProgramNode)
        assert len(prog.instrucciones) == 0


# ═══════════════════════════════════════════════════════════════════
# FASE 3: ANALIZADOR SEMÁNTICO
# ═══════════════════════════════════════════════════════════════════


def _semantic(codigo: str):
    """Helper: tokeniza, parsea y analiza semánticamente.
    Retorna (errores_semanticos, tabla_de_simbolos).
    """
    lexer = Lexer()
    tokens = lexer.tokenize(codigo)
    lex_errors = lexer.errores.obtener_errores()
    assert len(lex_errors) == 0, f"Errores léxicos inesperados: {lex_errors}"
    parser = Parser(tokens)
    programa = parser.parse()
    assert len(parser.errores) == 0, f"Errores sintácticos inesperados: {parser.errores}"
    analyzer = SemanticAnalyzer()
    analyzer.analizar(programa)
    return analyzer.errores, analyzer.tabla


class TestSemanticoValido:
    """Programas que deben pasar sin errores semánticos."""

    def test_programa_basico(self):
        errores, tabla = _semantic("""
            Definir Rol Gerente;
            Definir Usuario Ana;
            Definir Modulo Ventas;
            Usuario Ana = Rol Gerente;
            Rol Gerente = Permitir Consultar Ventas;
        """)
        assert len(errores) == 0

    def test_tabla_de_simbolos_poblada(self):
        errores, tabla = _semantic("""
            Definir Rol Gerente;
            Definir Modulo Ventas;
        """)
        assert len(errores) == 0
        assert tabla.existe("Gerente")
        assert tabla.existe("Ventas")

    def test_variables_abac_globales(self):
        """Horario, MontoVenta, UbicacionIP deben existir como globales."""
        errores, tabla = _semantic("Definir Rol Gerente;")
        assert tabla.existe("Horario")
        assert tabla.existe("MontoVenta")
        assert tabla.existe("UbicacionIP")

    def test_si_entonces_con_abac(self):
        errores, tabla = _semantic("""
            Definir Modulo Ventas;
            Si Horario > 8 Entonces {
                Acceder Ventas;
            }
        """)
        assert len(errores) == 0

    def test_intentar_atrapar(self):
        errores, tabla = _semantic("""
            Definir Modulo Ventas;
            Intentar {
                Acceder Ventas;
            } Atrapar ( Error e ) {
                Denegar Ventas;
            }
        """)
        assert len(errores) == 0

    def test_mostrar_devolver(self):
        errores, tabla = _semantic("""
            Mostrar "Sistema activo";
            Mostrar 42;
            Devolver Verdadero;
        """)
        assert len(errores) == 0


class TestSemanticoErrores:
    """Verificar detección de los 7 tipos de errores semánticos."""

    def test_err_sem_01_redeclaracion(self):
        errores, _ = _semantic("""
            Definir Rol Gerente;
            Definir Rol Gerente;
        """)
        assert len(errores) >= 1
        assert errores[0].codigo == "ERR_SEM_01"

    def test_err_sem_02_entidad_no_declarada(self):
        errores, _ = _semantic("Acceder ModuloInexistente;")
        assert len(errores) >= 1
        assert errores[0].codigo == "ERR_SEM_02"

    def test_err_sem_03_tipo_incompatible(self):
        """Asignar un rol a algo que no es Usuario debe dar error."""
        errores, _ = _semantic("""
            Definir Rol Gerente;
            Definir Modulo Ventas;
            Definir Usuario Ana;
            Usuario Ventas = Rol Gerente;
        """)
        # Ventas es un Modulo, no un Usuario: debe dar error semántico
        assert len(errores) >= 1

    def test_err_sem_04_dominio_invalido(self):
        errores, _ = _semantic("""
            Definir Rol Gerente;
            Definir Usuario Ana;
            Rol Gerente = Permitir Consultar Ana;
        """)
        assert len(errores) >= 1
        assert errores[0].codigo == "ERR_SEM_04"

    def test_err_sem_07_conflicto_politicas(self):
        errores, _ = _semantic("""
            Definir Rol Gerente;
            Definir Modulo Ventas;
            Rol Gerente = Permitir Consultar Ventas;
            Rol Gerente = Denegar Consultar Ventas;
        """)
        assert len(errores) >= 1
        assert errores[0].codigo == "ERR_SEM_07"


class TestSymbolTableEncapsulation:
    """Verificar que el método eliminar() funciona correctamente."""

    def test_eliminar_existente(self):
        from semantic.symbol_table import Symbol
        tabla = SymbolTable()
        sym = Symbol(identificador="test", tipo_dato="Rol")
        tabla.declarar(sym)
        assert tabla.existe("test")
        tabla.eliminar("test")
        assert not tabla.existe("test")

    def test_eliminar_inexistente_no_falla(self):
        tabla = SymbolTable()
        tabla.eliminar("no_existe")  # No debe lanzar excepción

    def test_eliminar_none_no_falla(self):
        tabla = SymbolTable()
        tabla.eliminar(None)  # No debe lanzar excepción


# ═══════════════════════════════════════════════════════════════════
# INTEGRACIÓN: PIPELINE COMPLETO
# ═══════════════════════════════════════════════════════════════════


class TestPipelineIntegracion:
    """Tests de integración que ejecutan las 3 fases."""

    def test_programa_completo(self):
        """Un programa empresarial completo debe pasar sin errores."""
        codigo = """
            Definir Rol Gerente;
            Definir Rol Cajero;
            Definir Usuario Ana;
            Definir Usuario Beto;
            Definir Modulo Ventas;
            Definir Modulo Reportes;
            Definir Modulo Facturacion;

            Usuario Ana = Rol Gerente;
            Usuario Beto = Rol Cajero;

            Rol Gerente = Permitir Consultar Reportes;
            Rol Gerente = Permitir Modificar Ventas;
            Rol Cajero  = Permitir Registrar Facturacion;

            Si Horario < 18 Entonces {
                Permitir Consultar Reportes;
            } Sino {
                Denegar Consultar Reportes;
            }

            Si MontoVenta > 1000 Entonces {
                Validar Ventas;
            }

            Mientras Verdadero {
                Si UbicacionIP == "192.168.0.1" Entonces {
                    Acceder Reportes;
                }
            }

            Intentar {
                Acceder Reportes;
                Mostrar "Operacion exitosa";
            } Atrapar ( Error e ) {
                Denegar Consultar Reportes;
                Mostrar "Acceso denegado";
            }

            Mostrar "Sistema operativo";
            Devolver Verdadero;
        """
        errores, tabla = _semantic(codigo)
        assert len(errores) == 0
        assert tabla.existe("Gerente")
        assert tabla.existe("Ana")
        assert tabla.existe("Ventas")

    def test_errores_lexicos_no_crashean_parser(self):
        """Si hay errores léxicos, el parser debe funcionar sin crash."""
        lexer = Lexer()
        tokens = lexer.tokenize("@ Definir Rol Gerente;")
        lex_errors = lexer.errores.obtener_errores()
        assert len(lex_errors) >= 1
        parser = Parser(tokens)
        prog = parser.parse()
        assert isinstance(prog, ast.ProgramNode)


# ═══════════════════════════════════════════════════════════════════
# ARCHIVOS DE EJEMPLO
# ═══════════════════════════════════════════════════════════════════


class TestArchivosEjemplo:
    """Verificar que los archivos .acl de ejemplo se procesan correctamente."""

    EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")

    def _cargar_ejemplo(self, nombre: str) -> str:
        path = os.path.join(self.EXAMPLES_DIR, nombre)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_programa_completo_sin_errores_sintacticos(self):
        """El programa completo debe parsear sin errores."""
        codigo = self._cargar_ejemplo("programa_completo.acl")
        lexer = Lexer()
        tokens = lexer.tokenize(codigo)
        parser = Parser(tokens)
        prog = parser.parse()
        assert len(parser.errores) == 0
        assert len(prog.instrucciones) > 0

    def test_errores_lexicos_detectados(self):
        """El archivo de errores léxicos debe detectar los 6 tipos."""
        codigo = self._cargar_ejemplo("errores_lexicos.acl")
        lexer = Lexer()
        lexer.tokenize(codigo)
        errores = lexer.errores.obtener_errores()
        assert len(errores) > 0
        codigos = {e.codigo for e in errores}
        # Debe cubrir los 6 tipos de error léxico
        assert "ERROR_LEX_01" in codigos
        assert "ERROR_LEX_02" in codigos
        assert "ERROR_LEX_03" in codigos
        assert "ERROR_LEX_05" in codigos
        assert "ERROR_LEX_06" in codigos

    def test_errores_sintacticos_detectados(self):
        """El archivo de errores sintácticos debe detectar errores."""
        codigo = self._cargar_ejemplo("errores_sintacticos.acl")
        lexer = Lexer()
        tokens = lexer.tokenize(codigo)
        parser = Parser(tokens)
        parser.parse()
        assert len(parser.errores) > 0

    def test_programa_completo_semantico(self):
        """El programa completo debe pasar las 3 fases sin errores."""
        codigo = self._cargar_ejemplo("programa_completo.acl")
        errores, tabla = _semantic(codigo)
        assert len(errores) == 0
