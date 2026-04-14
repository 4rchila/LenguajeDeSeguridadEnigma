from enum import Enum
from PyQt6.QtCore import QTimer

from gui.main_window import MainWindow
from lexer.lexer import Lexer
from lexer.tokens import TipoToken
from parser.parser import Parser, ParserError


class AnimationState(Enum):
    INACTIVE = 1
    PLAYING = 2
    PAUSED = 3


class AnimationPhase(Enum):
    """Fases del modo didáctico."""
    LEXER = 1
    SYNTAX = 2


class Controller:
    """
    Mediador entre la GUI y el lexer/parser.
    Modo Rápido: Análisis instantáneo de todo el código.
    Modo Didáctico: Análisis paso a paso con animaciones y tracking de cursores.
    """

    DEBOUNCE_MS = 450

    def __init__(self, window: MainWindow):
        self.window = window
        self.lexer = Lexer()
        self._live_timer = QTimer(self.window)
        self._live_timer.setSingleShot(True)
        self._live_timer.timeout.connect(self._update_live_errors)
        
        # Modo Didáctico State
        self.anim_state = AnimationState.INACTIVE
        self.anim_phase = AnimationPhase.LEXER
        self.anim_delay = 400
        self.anim_timer = QTimer(self.window)
        self.anim_timer.timeout.connect(self._didactic_step)
        self.didactic_tokens = []
        self.didactic_errors = []
        self.didactic_current_idx = 0
        
        # Syntax animation state
        self.syntax_ast = None
        self.syntax_parser_errors = []
        
        self._connect_signals()

    def _connect_signals(self):
        self.window.action_analyze.triggered.connect(self.on_analyze)
        self.window.action_analyze_step.triggered.connect(self.on_analyze_didactic)
        self.window.action_pause.triggered.connect(self.on_pause_toggle)
        self.window.action_stop.triggered.connect(self.on_stop_didactic)
        self.window.action_clear.triggered.connect(self.on_clear)
        self.window.error_panel.navigate_to_line.connect(self.window.navigate_to_line)
        self.window.code_editor.textChanged.connect(self._on_text_changed)

    def on_clear(self):
        if self.anim_state != AnimationState.INACTIVE:
            self._stop_animation()
        self.window.lbl_analyzer.setText("Estado: Esperando...")
        self.window.statusBar().clearMessage()
        self.window._on_clear()
        self.window.ast_viewer.clear_tree()
        self.window.ast_graph.clear_graph()

    def on_analyze(self):
        if self.anim_state != AnimationState.INACTIVE:
            self._stop_animation()
            
        code = self.window.get_code().strip()
        if not code:
            self.window.statusBar().showMessage(
                "El editor está vacío. Escribe código para analizar.", 3000
            )
            return

        try:
            tokens = self.lexer.tokenize(code)
            errors = self.lexer.errores.obtener_errores()
            self.window.show_results(tokens, errors)
            
            if not errors:
                parser = Parser(tokens)
                arbol = parser.parse()
                if parser.errores:
                    self.window.ast_viewer.clear_tree()
                    self.window.ast_graph.clear_graph()
                    self.window.lbl_analyzer.setText("⚠️ Error Sintáctico Detectado")
                    self.window.error_panel.populate(parser.errores)
                    self.window.lbl_errors.setText(f"Errores: {len(parser.errores)}")
                    self.window.show_error_panel()
                    self.window.statusBar().showMessage(f"Se encontraron {len(parser.errores)} error(es) sintáctico(s).", 8000)
                else:
                    self.window.hide_error_panel()
                    self.window.ast_viewer.populate_from_ast(arbol)
                    self.window.ast_graph.set_ast(arbol)
                    self.window.lbl_analyzer.setText("⚙️ Ejecutando: Análisis Completo (Rápido)")
                    self.window.statusBar().showMessage("Análisis Sintáctico y Léxico Completados Exitosamente.", 4000)
                    self.window.resultado_tabs.setCurrentIndex(2)  # Mostrar árbol gráfico
            else:
                self.window.ast_viewer.clear_tree()
                self.window.ast_graph.clear_graph()
                self.window.lbl_analyzer.setText("⚙️ Ejecutando: Analizador Léxico (Rápido) [Errores previenen Sintaxis]")

        except Exception as exc:
            self.window.statusBar().showMessage(
                f"Error inesperado durante el análisis: {exc}", 6000
            )

    def on_stop_didactic(self):
        if self.anim_state != AnimationState.INACTIVE:
            self._stop_animation(finished=True)
            self.window.lbl_analyzer.setText("Estado: Automáticamente Finalizado")
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
            self.window.ast_viewer.clear_tree()
            self.window.ast_graph.clear_graph()
            self.window.lbl_tokens.setText("Tokens: 0")
            self.window.lbl_errors.setText("Errores: 0")
            
            # Reset syntax state
            self.syntax_ast = None
            self.syntax_parser_errors = []
            
            self.window.code_editor.setReadOnly(True)
            self.anim_state = AnimationState.PLAYING
            self.anim_phase = AnimationPhase.LEXER
            self.window.lbl_analyzer.setText("👁️ Ejecutando: Analizador Léxico (Modo Didáctico)")
            self.window.action_pause.setVisible(True)
            self.window.action_pause.setEnabled(True)
            self.window.action_pause.setText("⏸  Pausa")
            self.window.action_stop.setVisible(True)
            self.window.statusBar().clearMessage()
            
            self.anim_timer.start(self.anim_delay)
        except Exception as exc:
            self.window.statusBar().showMessage(
                f"Error al iniciar modo didáctico: {exc}", 6000
            )

    def on_pause_toggle(self):
        if self.anim_state == AnimationState.PLAYING:
            self.anim_state = AnimationState.PAUSED
            self.anim_timer.stop()
            self.window.action_pause.setText("▶  Continuar")
            phase_name = "Léxico" if self.anim_phase == AnimationPhase.LEXER else "Sintáctico"
            self.window.lbl_analyzer.setText(f"👁️ Analizador {phase_name} (Pausa)")
        elif self.anim_state == AnimationState.PAUSED:
            self.anim_state = AnimationState.PLAYING
            self.anim_timer.start(self.anim_delay)
            self.window.action_pause.setText("⏸  Pausa")
            phase_name = "Léxico" if self.anim_phase == AnimationPhase.LEXER else "Sintáctico"
            self.window.lbl_analyzer.setText(f"👁️ Ejecutando: Analizador {phase_name} (Modo Didáctico)")

    def _didactic_step(self):
        if self.anim_phase == AnimationPhase.LEXER:
            self._lexer_step()
        elif self.anim_phase == AnimationPhase.SYNTAX:
            self._syntax_step()

    # ── Fase Léxica ──

    def _lexer_step(self):
        if self.didactic_current_idx >= len(self.didactic_tokens):
            # Lexer terminó → decidir si continuar con sintaxis
            self._on_lexer_finished()
            return
            
        token = self.didactic_tokens[self.didactic_current_idx]
        is_error = token.tipo == TipoToken.ERROR_LEXICO
        
        self.window.code_editor.set_didactic_highlight(token.start_index, token.end_index, is_error)
        
        current_tokens = self.didactic_tokens[:self.didactic_current_idx + 1]
        self.window.token_table.populate(current_tokens)
        
        if is_error:
            err_sublist = [
                e for e in self.didactic_errors 
                if getattr(e, 'linea', 0) < token.linea or 
                   (getattr(e, 'linea', 0) == token.linea and getattr(e, 'columna', 0) <= token.columna)
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
            # Hay errores léxicos → no proceder con sintaxis
            self.window.error_panel.populate(self.didactic_errors)
            self.window.lbl_errors.setText(f"Errores: {len(self.didactic_errors)}")
            self.window.show_error_panel()
            self.window.lbl_analyzer.setText("Estado: Finalizado (Errores Léxicos bloquean el Sintáctico)")
            self._stop_animation(finished=False)
            return
        
        # Sin errores léxicos → parsear y preparar animación sintáctica
        parser = Parser(self.didactic_tokens)
        self.syntax_ast = parser.parse()
        self.syntax_parser_errors = list(parser.errores)
        
        if self.syntax_parser_errors:
            # Hay errores sintácticos → mostrar errores, no animar árbol
            self.window.error_panel.populate(self.syntax_parser_errors)
            self.window.lbl_errors.setText(f"Errores: {len(self.syntax_parser_errors)}")
            self.window.show_error_panel()
            self.window.lbl_analyzer.setText("⚠️ Error Sintáctico Detectado")
            self.window.statusBar().showMessage(
                f"Se encontraron {len(self.syntax_parser_errors)} error(es) sintáctico(s).", 8000
            )
            self._stop_animation(finished=False)
            return
        
        # Sin errores → iniciar animación del árbol sintáctico
        self.anim_phase = AnimationPhase.SYNTAX
        self.window.lbl_analyzer.setText("👁️ Ejecutando: Analizador Sintáctico (Modo Didáctico)")
        
        # Preparar el árbol gráfico para animación
        self.window.ast_graph.prepare_animation(self.syntax_ast)
        self.window.resultado_tabs.setCurrentIndex(2)  # Ir a pestaña del árbol gráfico
        
        # También llenar el tree viewer de texto completo
        self.window.ast_viewer.populate_from_ast(self.syntax_ast)

    # ── Fase Sintáctica ──

    def _syntax_step(self):
        """Revela el siguiente nodo del árbol y resalta el código correspondiente."""
        ast_node = self.window.ast_graph.animate_next_node()
        
        if ast_node is None:
            # Animación del árbol terminó
            self._on_syntax_finished()
            return
        
        # Resaltar el bloque de código correspondiente al nodo actual
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
        
        # Actualizar status bar con progreso
        total = self.window.ast_graph.get_total_nodes()
        current = self.window.ast_graph.get_visible_count()
        self.window.statusBar().showMessage(
            f"Construyendo AST... nodo {current} de {total}", 2000
        )

    def _on_syntax_finished(self):
        """El árbol sintáctico se terminó de animar."""
        self.window.code_editor.set_didactic_highlight(-1, -1)
        self.window.lbl_analyzer.setText("✅ Estado: Análisis Léxico y Sintáctico Finalizados")
        self.window.statusBar().showMessage("Análisis completo — árbol sintáctico construido exitosamente.", 5000)
        self._stop_animation(finished=False)

    def _stop_animation(self, finished=False):
        self.anim_state = AnimationState.INACTIVE
        self.anim_timer.stop()
        self.window.code_editor.setReadOnly(False)
        self.window.code_editor.set_didactic_highlight(-1, -1)
        self.window.action_pause.setEnabled(False)
        self.window.action_pause.setVisible(False)
        self.window.action_stop.setVisible(False)
        self.window.action_pause.setText("⏸  Pausa")
        
        if finished:
            # Botón "Finalizar" presionado — mostrar resultados completos
            self.window.error_panel.populate(self.didactic_errors)
            self.window.lbl_errors.setText(f"Errores: {len(self.didactic_errors)}")
            
            if not self.didactic_errors:
                # Completar análisis sintáctico si no se hizo
                if self.syntax_ast is None:
                    parser = Parser(self.didactic_tokens)
                    self.syntax_ast = parser.parse()
                    self.syntax_parser_errors = list(parser.errores)
                
                if self.syntax_parser_errors:
                    self.window.error_panel.populate(self.syntax_parser_errors)
                    self.window.lbl_errors.setText(f"Errores: {len(self.syntax_parser_errors)}")
                    self.window.show_error_panel()
                    self.window.lbl_analyzer.setText("⚠️ Error Sintáctico Detectado")
                else:
                    self.window.hide_error_panel()
                    self.window.ast_viewer.populate_from_ast(self.syntax_ast)
                    self.window.ast_graph.set_ast(self.syntax_ast)
                    self.window.resultado_tabs.setCurrentIndex(2)
                    self.window.lbl_analyzer.setText("✅ Estado: Análisis Finalizado")
            else:
                self.window.show_error_panel()
                self.window.lbl_analyzer.setText("Estado: Finalizado (Errores Léxicos)")

    def _on_text_changed(self):
        """Reinicia el timer para actualizar subrayados de errores al dejar de escribir."""
        self._live_timer.stop()
        self._live_timer.start(self.DEBOUNCE_MS)

    def _update_live_errors(self):
        """Ejecuta el lexer sobre el código actual y subraya errores en el editor."""
        code = self.window.get_code()
        if not code.strip():
            self.window.code_editor.set_lexical_errors([])
            return
        try:
            self.lexer.tokenize(code)
            errors = self.lexer.errores.obtener_errores()
            self.window.code_editor.set_lexical_errors(errors)
        except Exception:
            self.window.code_editor.set_lexical_errors([])
