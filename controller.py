"""
controller.py — Mediador entre la GUI y los analizadores.
=========================================================
Coordina las cuatro fases del compilador:

    Fase 1 (Léxico)      →  lexer/lexer.py
    Fase 2 (Sintáctico)  →  parser/parser.py
    Fase 3 (Semántico)   →  semantic/semantic_analyzer.py
    Fase 4 (Generación)  →  codegen/policy_exporter.py

Modos disponibles:
    • Modo Rápido (Ctrl+Enter)  →  ejecuta todo y enfoca la pestaña relevante.
    • Modo Didáctico (F10)      →  animación paso-a-paso con resaltado.
    • Live Compile (debounced)  →  pipeline silencioso al editar el código,
      mantiene tokens, AST, tabla de símbolos y errores siempre frescos.
    • Exportar JSON (Ctrl+E)   →  genera archivo .json con políticas compiladas.
"""

from enum import Enum

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QFileDialog

from gui.main_window import MainWindow
from gui.icons import Icons
from lexer.lexer import Lexer
from lexer.tokens import TipoToken
from parser.parser import Parser
from semantic import SemanticAnalyzer
from codegen.policy_exporter import PolicyExporter


# ─────────────────────────────────────────────────────────────────────
# Indicadores de fase
# ─────────────────────────────────────────────────────────────────────

class AnimationState(Enum):
    INACTIVE = 1
    PLAYING = 2
    PAUSED = 3


class AnimationPhase(Enum):
    """Fases del modo didáctico."""
    LEXER = 1
    SYNTAX = 2
    SEMANTIC = 3


# Índices de pestaña en el QTabWidget de resultados (sin "AST Texto")
TAB_TOKENS = 0
TAB_AST_GRAFICO = 1
TAB_TABLA_SIMBOLOS = 2


# ─────────────────────────────────────────────────────────────────────
# Controller
# ─────────────────────────────────────────────────────────────────────

class Controller:
    """Coordina los analizadores y refresca la GUI."""

    DEBOUNCE_MS = 350

    def __init__(self, window: MainWindow):
        self.window = window
        self.lexer = Lexer()

        # Live compile (debounced)
        self._live_timer = QTimer(self.window)
        self._live_timer.setSingleShot(True)
        self._live_timer.timeout.connect(self._live_compile)

        # Modo Didáctico — estado
        self.anim_state = AnimationState.INACTIVE
        self.anim_phase = AnimationPhase.LEXER
        self.anim_delay = 400
        self.anim_timer = QTimer(self.window)
        self.anim_timer.timeout.connect(self._didactic_step)
        self.didactic_tokens = []
        self.didactic_errors = []
        self.didactic_current_idx = 0

        # Estado sintáctico para la animación didáctica
        self.syntax_ast = None
        self.syntax_parser_errors = []

        # Estado de exportación (Fase 4)
        self._last_valid_ast = None
        self._last_valid_tabla = None
        self._source_file = ""

        self._connect_signals()

    # ─────────────────────────────────────────────────────────────
    # Wiring de señales
    # ─────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self.window.action_analyze.triggered.connect(self.on_analyze)
        self.window.action_analyze_step.triggered.connect(self.on_analyze_didactic)
        self.window.action_pause.triggered.connect(self.on_pause_toggle)
        self.window.action_stop.triggered.connect(self.on_stop_didactic)
        self.window.action_clear.triggered.connect(self.on_clear)
        self.window.action_export.triggered.connect(self.on_export)
        self.window.error_panel.navigate_to_line.connect(self.window.navigate_to_line)
        self.window.code_editor.textChanged.connect(self._on_text_changed)

    # ─────────────────────────────────────────────────────────────
    # Comandos de toolbar
    # ─────────────────────────────────────────────────────────────

    def on_clear(self):
        if self.anim_state != AnimationState.INACTIVE:
            self._stop_animation()
        self.window.lbl_analyzer.setText("Estado: Esperando…")
        self.window.statusBar().clearMessage()
        self.window._on_clear()
        self.window.ast_graph.clear_graph()
        self.window.symbol_table_widget.clear_table()
        self._last_valid_ast = None
        self._last_valid_tabla = None
        self.window.action_export.setEnabled(False)

    def on_analyze(self):
        """Ejecuta el pipeline completo y enfoca la pestaña relevante."""
        if self.anim_state != AnimationState.INACTIVE:
            self._stop_animation()

        code = self.window.get_code().strip()
        if not code:
            self.window.statusBar().showMessage(
                "El editor está vacío. Escribe código para analizar.", 3000
            )
            return

        try:
            ok, fase = self._run_pipeline(code, focus_tabs=True, silent=False)
        except Exception as exc:
            self.window.statusBar().showMessage(
                f"Error inesperado durante el análisis: {exc}", 6000
            )
            return

        if ok:
            self.window.statusBar().showMessage(
                "Análisis Léxico, Sintáctico y Semántico completados con éxito.",
                5000,
            )
        elif fase == "lexico":
            self.window.statusBar().showMessage(
                "Errores léxicos detectados — fases siguientes bloqueadas.", 6000,
            )
        elif fase == "sintactico":
            self.window.statusBar().showMessage(
                "Errores sintácticos detectados — fase semántica bloqueada.", 8000,
            )
        elif fase == "semantico":
            self.window.statusBar().showMessage(
                "Análisis abortado en la fase semántica.", 9000,
            )

    def on_export(self):
        """Fase 4 — Exportar las políticas compiladas a un archivo JSON."""
        if self._last_valid_ast is None or self._last_valid_tabla is None:
            self.window.statusBar().showMessage(
                "No hay políticas compiladas para exportar. Analiza primero.", 4000
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Exportar Políticas Compiladas",
            "politicas_enigma.json",
            "Archivos JSON (*.json);;Todos (*)",
        )
        if not path:
            return

        try:
            exporter = PolicyExporter(
                arbol=self._last_valid_ast,
                tabla=self._last_valid_tabla,
                source_file=self._source_file,
            )
            json_content = exporter.exportar_json(indent=2)

            with open(path, "w", encoding="utf-8") as f:
                f.write(json_content)

            self.window.statusBar().showMessage(
                f"Políticas exportadas exitosamente → {path}", 6000
            )
            self.window.lbl_analyzer.setText(
                "Estado: Exportación Completa — Fase 4 (JSON)"
            )
        except Exception as exc:
            self.window.statusBar().showMessage(
                f"Error al exportar: {exc}", 6000
            )

    def on_stop_didactic(self):
        if self.anim_state != AnimationState.INACTIVE:
            self._stop_animation(finished=True)
            self.window.lbl_analyzer.setText("Estado: Análisis Finalizado")
            self.window.statusBar().clearMessage()

    def on_analyze_didactic(self):
        if self.anim_state != AnimationState.INACTIVE:
            self._stop_animation()

        code = self.window.get_code().strip()
        if not code:
            self.window.statusBar().showMessage(
                "El editor está vacío. Escribe código para analizar.", 3000
            )
            return

        try:
            self.didactic_tokens = self.lexer.tokenize(code)
            self.didactic_errors = self.lexer.errores.obtener_errores()
            self.didactic_current_idx = 0

            self.window.token_table.clear_table()
            self.window.error_panel.clear_panel()
            self.window.ast_graph.clear_graph()
            self.window.symbol_table_widget.clear_table()
            self.window.lbl_tokens.setText("Tokens: 0")
            self.window.lbl_errors.setText("Errores: 0")

            self.syntax_ast = None
            self.syntax_parser_errors = []

            self.window.code_editor.setReadOnly(True)
            self.anim_state = AnimationState.PLAYING
            self.anim_phase = AnimationPhase.LEXER
            self.window.lbl_analyzer.setText("Estado: Modo Didáctico — Analizador Léxico")
            self.window.action_pause.setVisible(True)
            self.window.action_pause.setEnabled(True)
            self.window.action_pause.setIcon(Icons.pause("#fb923c"))
            self.window.action_pause.setText("Pausa")
            self.window.action_stop.setVisible(True)
            self.window.statusBar().clearMessage()

            # Siempre iniciar mostrando la pestaña de Tokens
            self.window.resultado_tabs.setCurrentIndex(TAB_TOKENS)

            self.anim_timer.start(self.anim_delay)
        except Exception as exc:
            self.window.statusBar().showMessage(
                f"Error al iniciar Modo Didáctico: {exc}", 6000
            )

    def on_pause_toggle(self):
        if self.anim_state == AnimationState.PLAYING:
            self.anim_state = AnimationState.PAUSED
            self.anim_timer.stop()
            self.window.action_pause.setIcon(Icons.play("#fb923c"))
            self.window.action_pause.setText("Continuar")
            phase_name = "Léxico" if self.anim_phase == AnimationPhase.LEXER else "Sintáctico"
            self.window.lbl_analyzer.setText(f"Estado: Modo Didáctico — Pausa ({phase_name})")
        elif self.anim_state == AnimationState.PAUSED:
            self.anim_state = AnimationState.PLAYING
            self.anim_timer.start(self.anim_delay)
            self.window.action_pause.setIcon(Icons.pause("#fb923c"))
            self.window.action_pause.setText("Pausa")
            phase_name = "Léxico" if self.anim_phase == AnimationPhase.LEXER else "Sintáctico"
            self.window.lbl_analyzer.setText(f"Estado: Modo Didáctico — Analizador {phase_name}")

    # ─────────────────────────────────────────────────────────────
    # Pipeline unificado (usado por on_analyze y _live_compile)
    # ─────────────────────────────────────────────────────────────

    def _run_pipeline(self, code: str, focus_tabs: bool, silent: bool):
        """
        Ejecuta lex → parser → semántico de manera secuencial.

        Args:
            code:        Texto fuente.
            focus_tabs:  Cambia automáticamente a la pestaña relevante.
            silent:      Si True, no muestra mensajes en la status bar
                         (modo live compile).

        Returns:
            (ok, fase) — `ok` es True si todo el pipeline pasó.
                         `fase` ∈ {"lexico", "sintactico", "semantico", None}.
        """
        # ── Fase 1: Léxico ─────────────────────────────────────
        tokens = self.lexer.tokenize(code)
        lex_errors = self.lexer.errores.obtener_errores()

        # Subrayado tipo Error Lens (siempre)
        self.window.code_editor.set_lexical_errors(lex_errors)

        # Pinta tokens y contadores
        self.window.token_table.populate(tokens)
        self.window.lbl_tokens.setText(f"Tokens: {len(tokens)}")

        if lex_errors:
            self.window.error_panel.populate(lex_errors)
            self.window.lbl_errors.setText(f"Errores: {len(lex_errors)}")
            self.window.show_error_panel()
            self.window.ast_graph.clear_graph()
            self.window.symbol_table_widget.clear_table()
            self.window.lbl_analyzer.setText(
                f"Errores Léxicos: {len(lex_errors)} — fase sintáctica bloqueada"
            )
            if focus_tabs:
                self.window.resultado_tabs.setCurrentIndex(TAB_TOKENS)
            return False, "lexico"

        # ── Fase 2: Sintáctico ─────────────────────────────────
        parser = Parser(tokens)
        arbol = parser.parse()

        if parser.errores:
            self.window.error_panel.populate(parser.errores)
            self.window.lbl_errors.setText(f"Errores: {len(parser.errores)}")
            self.window.show_error_panel()
            self.window.ast_graph.clear_graph()
            self.window.symbol_table_widget.clear_table()
            self.window.lbl_analyzer.setText(
                f"Errores Sintácticos: {len(parser.errores)} — fase semántica bloqueada"
            )
            if focus_tabs:
                self.window.resultado_tabs.setCurrentIndex(TAB_TOKENS)
            return False, "sintactico"

        # AST sintácticamente válido — pintarlo siempre.
        self.window.ast_graph.set_ast(arbol)

        # ── Fase 3: Semántico ──────────────────────────────────
        analizador = SemanticAnalyzer()
        sem_ok = analizador.analizar(arbol)

        # La tabla de símbolos siempre se publica (refleja el estado parcial
        # registrado hasta el momento del fallo).
        self.window.symbol_table_widget.populate(analizador.tabla)

        if not sem_ok:
            err = analizador.errores[0]
            self.window.error_panel.populate(analizador.errores)
            self.window.lbl_errors.setText(f"Errores: {len(analizador.errores)}")
            self.window.show_error_panel()
            self.window.lbl_analyzer.setText(
                f"Error Semántico · {err.codigo} — {err.mensaje[:60]}…"
            )
            if focus_tabs:
                self.window.resultado_tabs.setCurrentIndex(TAB_TABLA_SIMBOLOS)
            self._last_valid_ast = None
            self._last_valid_tabla = None
            self.window.action_export.setEnabled(False)
            return False, "semantico"

        # Pipeline OK — habilitar exportación (Fase 4)
        self.window.error_panel.clear_panel()
        self.window.lbl_errors.setText("Errores: 0")
        self.window.hide_error_panel()
        self.window.lbl_analyzer.setText(
            "Estado: Análisis Completo — Léxico · Sintáctico · Semántico"
        )
        self._last_valid_ast = arbol
        self._last_valid_tabla = analizador.tabla
        self.window.action_export.setEnabled(True)
        if focus_tabs:
            self.window.resultado_tabs.setCurrentIndex(TAB_TABLA_SIMBOLOS)
        return True, None

    # ─────────────────────────────────────────────────────────────
    # Live Compile (debounced)
    # ─────────────────────────────────────────────────────────────

    def _on_text_changed(self):
        """Pospone el live compile hasta que el usuario deja de escribir."""
        # Mientras la animación está activa el editor está en read-only,
        # pero por si algún flujo dispara textChanged, lo ignoramos.
        if self.anim_state != AnimationState.INACTIVE:
            return
        self._live_timer.stop()
        self._live_timer.start(self.DEBOUNCE_MS)

    def _live_compile(self):
        """
        Ejecuta el pipeline completo en silencio mientras el usuario edita.
        Mantiene tokens, AST, tabla de símbolos y errores siempre vivos.
        """
        if self.anim_state != AnimationState.INACTIVE:
            return

        code = self.window.get_code()
        if not code.strip():
            self.window.code_editor.set_lexical_errors([])
            self.window.token_table.clear_table()
            self.window.ast_graph.clear_graph()
            self.window.symbol_table_widget.clear_table()
            self.window.error_panel.clear_panel()
            self.window.hide_error_panel()
            self.window.lbl_tokens.setText("Tokens: 0")
            self.window.lbl_errors.setText("Errores: 0")
            self.window.lbl_analyzer.setText("Estado: Esperando…")
            return

        try:
            self._run_pipeline(code, focus_tabs=False, silent=True)
        except Exception:
            # No queremos espantar al usuario con tracebacks mientras teclea.
            pass

    # ─────────────────────────────────────────────────────────────
    # Modo Didáctico — paso a paso
    # ─────────────────────────────────────────────────────────────

    def _didactic_step(self):
        if self.anim_phase == AnimationPhase.LEXER:
            self._lexer_step()
        elif self.anim_phase == AnimationPhase.SYNTAX:
            self._syntax_step()

    def _lexer_step(self):
        if self.didactic_current_idx >= len(self.didactic_tokens):
            self._on_lexer_finished()
            return

        token = self.didactic_tokens[self.didactic_current_idx]
        is_error = token.tipo == TipoToken.ERROR_LEXICO
        self.window.code_editor.set_didactic_highlight(token.start_index, token.end_index, is_error)

        current_tokens = self.didactic_tokens[: self.didactic_current_idx + 1]
        self.window.token_table.populate(current_tokens)

        if is_error:
            err_sublist = [
                e for e in self.didactic_errors
                if getattr(e, 'linea', 0) < token.linea or
                   (getattr(e, 'linea', 0) == token.linea and
                    getattr(e, 'columna', 0) <= token.columna)
            ]
            self.window.error_panel.populate(err_sublist)
            self.window.lbl_errors.setText(f"Errores: {len(err_sublist)}")
            self.window.show_error_panel()

        self.window.lbl_tokens.setText(f"Tokens: {len(current_tokens)}")
        self.didactic_current_idx += 1

    def _on_lexer_finished(self):
        """Transición de la fase léxica a la fase sintáctica."""
        self.window.code_editor.set_didactic_highlight(-1, -1)

        if self.didactic_errors:
            self.window.error_panel.populate(self.didactic_errors)
            self.window.lbl_errors.setText(f"Errores: {len(self.didactic_errors)}")
            self.window.show_error_panel()
            self.window.lbl_analyzer.setText(
                "Estado: Errores Léxicos detectados — fase sintáctica bloqueada"
            )
            self._stop_animation(finished=False)
            return

        parser = Parser(self.didactic_tokens)
        self.syntax_ast = parser.parse()
        self.syntax_parser_errors = list(parser.errores)

        if self.syntax_parser_errors:
            self.window.error_panel.populate(self.syntax_parser_errors)
            self.window.lbl_errors.setText(f"Errores: {len(self.syntax_parser_errors)}")
            self.window.show_error_panel()
            self.window.lbl_analyzer.setText("Estado: Error Sintáctico Detectado")
            self.window.statusBar().showMessage(
                f"Se encontraron {len(self.syntax_parser_errors)} error(es) sintáctico(s).",
                8000,
            )
            self._stop_animation(finished=False)
            return

        self.anim_phase = AnimationPhase.SYNTAX
        self.window.lbl_analyzer.setText("Estado: Modo Didáctico — Analizador Sintáctico")
        self.window.ast_graph.prepare_animation(self.syntax_ast)
        # Auto-cambiar a la pestaña del Árbol Sintáctico
        self.window.resultado_tabs.setCurrentIndex(TAB_AST_GRAFICO)

    def _syntax_step(self):
        ast_node = self.window.ast_graph.animate_next_node()
        if ast_node is None:
            self._on_syntax_finished()
            return

        start_token = getattr(ast_node, 'start_token', None)
        end_token = getattr(ast_node, 'end_token', None)

        if start_token and end_token:
            start_idx = getattr(start_token, 'start_index', -1)
            end_idx = getattr(end_token, 'end_index', -1)
            if start_idx >= 0 and end_idx >= 0:
                self.window.code_editor.set_didactic_highlight(start_idx, end_idx, False, phase='syntax')
        elif start_token:
            start_idx = getattr(start_token, 'start_index', -1)
            end_idx = getattr(start_token, 'end_index', start_idx + 1)
            if start_idx >= 0:
                self.window.code_editor.set_didactic_highlight(start_idx, end_idx, False, phase='syntax')

        total = self.window.ast_graph.get_total_nodes()
        current = self.window.ast_graph.get_visible_count()
        self.window.statusBar().showMessage(
            f"Construyendo AST… nodo {current} de {total}", 2000
        )

    def _on_syntax_finished(self):
        """Animación sintáctica terminada → disparar Fase 3."""
        self.window.code_editor.set_didactic_highlight(-1, -1)

        # Auto-cambiar a la pestaña de Tabla de Símbolos para la fase semántica
        self.window.resultado_tabs.setCurrentIndex(TAB_TABLA_SIMBOLOS)

        analizador = SemanticAnalyzer()
        ok = analizador.analizar(self.syntax_ast)
        self.window.symbol_table_widget.populate(analizador.tabla)

        if not ok:
            err = analizador.errores[0]
            self.window.error_panel.populate(analizador.errores)
            self.window.lbl_errors.setText(f"Errores: {len(analizador.errores)}")
            self.window.show_error_panel()
            self.window.lbl_analyzer.setText(
                f"Error Semántico · {err.codigo}"
            )
            self.window.statusBar().showMessage(
                f"Análisis abortado en la fase semántica · {err.codigo}", 8000
            )
            self.window.resultado_tabs.setCurrentIndex(TAB_TABLA_SIMBOLOS)
        else:
            self.window.error_panel.clear_panel()
            self.window.hide_error_panel()
            self.window.lbl_errors.setText("Errores: 0")
            self.window.lbl_analyzer.setText(
                "Estado: Análisis Completo — Léxico · Sintáctico · Semántico"
            )
            self.window.statusBar().showMessage(
                "Análisis completo — AST y tabla de símbolos generados con éxito.",
                5000,
            )
            self.window.resultado_tabs.setCurrentIndex(TAB_TABLA_SIMBOLOS)

        self._stop_animation(finished=False)

    def _stop_animation(self, finished: bool = False):
        self.anim_state = AnimationState.INACTIVE
        self.anim_timer.stop()
        self.window.code_editor.setReadOnly(False)
        self.window.code_editor.set_didactic_highlight(-1, -1)
        self.window.action_pause.setEnabled(False)
        self.window.action_pause.setVisible(False)
        self.window.action_stop.setVisible(False)
        self.window.action_pause.setIcon(Icons.pause("#fb923c"))
        self.window.action_pause.setText("Pausa")

        if finished:
            # "Finalizar" presionado → completamos pipeline restante.
            self.window.error_panel.populate(self.didactic_errors)
            self.window.lbl_errors.setText(f"Errores: {len(self.didactic_errors)}")

            if not self.didactic_errors:
                if self.syntax_ast is None:
                    parser = Parser(self.didactic_tokens)
                    self.syntax_ast = parser.parse()
                    self.syntax_parser_errors = list(parser.errores)

                if self.syntax_parser_errors:
                    self.window.error_panel.populate(self.syntax_parser_errors)
                    self.window.lbl_errors.setText(f"Errores: {len(self.syntax_parser_errors)}")
                    self.window.show_error_panel()
                    self.window.lbl_analyzer.setText("Estado: Error Sintáctico Detectado")
                    self.window.symbol_table_widget.clear_table()
                else:
                    self.window.ast_graph.set_ast(self.syntax_ast)

                    analizador = SemanticAnalyzer()
                    ok = analizador.analizar(self.syntax_ast)
                    self.window.symbol_table_widget.populate(analizador.tabla)

                    if not ok:
                        err = analizador.errores[0]
                        self.window.error_panel.populate(analizador.errores)
                        self.window.lbl_errors.setText(f"Errores: {len(analizador.errores)}")
                        self.window.show_error_panel()
                        self.window.lbl_analyzer.setText(
                            f"Error Semántico · {err.codigo}"
                        )
                        self.window.resultado_tabs.setCurrentIndex(TAB_TABLA_SIMBOLOS)
                    else:
                        self.window.hide_error_panel()
                        self.window.resultado_tabs.setCurrentIndex(TAB_TABLA_SIMBOLOS)
                        self.window.lbl_analyzer.setText(
                            "Estado: Análisis Completo — Léxico · Sintáctico · Semántico"
                        )
            else:
                self.window.show_error_panel()
                self.window.symbol_table_widget.clear_table()
                self.window.lbl_analyzer.setText(
                    "Estado: Errores Léxicos detectados — fase sintáctica bloqueada"
                )
