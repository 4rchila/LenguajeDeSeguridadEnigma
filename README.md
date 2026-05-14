# Compilador — Lenguaje de Control de Accesos Empresarial (Enigma)

## ¿Qué es?
Este proyecto es la implementación de las **tres fases de análisis** de un compilador para el **Lenguaje de Control de Accesos Empresarial (Enigma)**, más una **capa de salida** que exporta políticas compiladas a JSON:

1. **Fase 1 — Analizador Léxico:** Escaneo de tokens y detección de errores léxicos.
2. **Fase 2 — Analizador Sintáctico:** Construcción del Árbol de Sintaxis Abstracta (AST).
3. **Fase 3 — Analizador Semántico:** Validación de reglas RBAC/ABAC y generación de Tabla de Símbolos.
4. **Exportación (JSON):** Tras un análisis semántico exitoso, la GUI puede exportar políticas y metadatos mediante `codegen/policy_exporter.py` (atajo configurado en la aplicación).

La aplicación incluye una **GUI PyQt6** que ofrece una experiencia interactiva para ver cómo el compilador procesa el código, incluyendo un **Modo Didáctico** con animación paso a paso.

### Características principales implementadas
- **Analizador léxico:** Tokens por regex priorizada, errores léxicos catalogados y sugerencias por distancia de edición (Levenshtein) para palabras reservadas mal escritas.
- **Analizador sintáctico (descenso recursivo):** AST alineado con la gramática BNF del lenguaje; condiciones lógicas compuestas (Y, O, No) con precedencia definida.
- **Recuperación sintáctica (modo pánico):** Sincronización ante errores para seguir reportando sin colapsar.
- **Analizador semántico (7 reglas):** Unicidad de entidades, integridad referencial, compatibilidad de tipos, coherencia RBAC, expresiones booleanas en condiciones, operaciones entre tipos y conflicto de políticas (`ERR_SEM_01` … `ERR_SEM_07`).
- **Tabla de símbolos:** Roles, usuarios, módulos, políticas y variables ABAC globales (`Horario`, `MontoVenta`, `UbicacionIP`).
- **Modo didáctico:** Tres etapas animadas — tokens en el editor, construcción gráfica del AST, recorrido semántico con actualización de la tabla de símbolos.
- **Error Lens y panel de errores:** Subrayado léxico en el editor; panel de errores que se muestra solo cuando hay incidencias.
- **Visualización del AST:** En la ventana principal se usa el **diagrama interactivo** (`AstGraphWidget`: nodos, arcos y animación). El módulo `gui/ast_tree_viewer.py` (árbol tipo `QTreeWidget`) está en el repositorio como componente reutilizable **no conectado** actualmente a la ventana principal.
- **Tabla de símbolos en GUI:** Pestaña dedicada con identificador, tipo, subtipo, rol vinculado y políticas.

---

## Arquitectura (capas)

### 1) `lexer/` (motor léxico)
- `lexer/tokens.py`: `TipoToken`, `Token`, palabras reservadas (comparación case-insensitive en el flujo de análisis).
- `lexer/error_handler.py`: Acumulación de errores léxicos.
- `lexer/lexer.py`: Clase `Lexer` — tokenización del fuente.

### 2) `parser/` (motor sintáctico)
- `parser/ast_nodes.py`: Nodos del AST del lenguaje.
- `parser/parser.py`: Clase `Parser` — análisis descendente con precedencia de operadores lógicos (`O` más débil, luego `Y`, luego `No`, luego relacionales).

### 3) `semantic/` (motor semántico)
- `semantic/semantic_analyzer.py`: Visitor sobre el AST; validaciones y opción de historial para el modo didáctico.
- `semantic/symbol_table.py`: Tabla de símbolos e inyección de variables ABAC globales.
- `semantic/semantic_errors.py`: Códigos y tipo de error semántico.

### 4) `codegen/` (salida compilada)
- `codegen/policy_exporter.py`: Genera documento JSON (entidades, políticas RBAC, reglas condicionales del AST, matriz de acceso, metadatos).

### 5) `gui/` (PyQt6)
- `gui/main_window.py`: Ventana principal, pestañas (Tokens, Árbol sintáctico, Tabla de símbolos), toolbar y estilos.
- `gui/code_editor.py`: Editor con resaltado y marcado de errores léxicos / modo didáctico.
- `gui/token_table.py` y `ErrorPanel`: Lista de tokens y de errores (léxicos, sintácticos, semánticos).
- `gui/ast_graph_widget.py`: Vista gráfica del AST usada en la aplicación.
- `gui/ast_tree_viewer.py`: Visor de AST en árbol (no integrado en la ventana principal en esta versión).
- `gui/symbol_table_widget.py`: Tabla de símbolos visual.
- `gui/icons.py`: Iconos vectoriales con `QPainter`.
- `gui/__init__.py`: Reexporta componentes públicos del paquete.

### 6) `controller.py` (coordinador)
- Encadena léxico → sintáctico → semántico; refresca la GUI.
- Modo didáctico, análisis completo (toolbar) y compilación en vivo con debounce al editar.
- Habilita la exportación JSON cuando el pipeline semántico termina sin error.

### 7) Punto de entrada
- `main.py`: Arranque de `QApplication`, `MainWindow` y `Controller`.

---

## Archivos de prueba y ejemplos

### Carpeta `examples/` (5 archivos `.acl`)
| Archivo | Uso típico |
|---------|------------|
| `programa_completo.acl` | Programa de referencia con la mayoría de construcciones válidas del lenguaje. |
| `empresa_ventas.acl` | Escenario de dominio empresarial / ventas. |
| `errores_lexicos.acl` | Casos de error léxico. |
| `errores_sintacticos.acl` | Casos de error sintáctico y recuperación. |
| `errores_semanticos.acl` | Casos de error semántico. |

### Carpeta `test/`
- `test/test_case.py`: Suite **pytest** (61 pruebas) sobre las fases léxica, sintáctica y semántica.

### Carpeta `demo_erp/`
- `demo_erp/index.html`: Página estática de demostración / presentación de integración tipo ERP (HTML/CSS; no ejecuta el motor Python).

### Documentación adicional en la raíz
- `fase2_analizador_sintactico.md` — Especificación y BNF de la fase sintáctica.
- `fase3_analizador_semantico.md` — Diseño del analizador semántico y de la tabla de símbolos.
- `Presentacion_Enigma.html` — Presentación en HTML (Reveal.js vía CDN).

---

## Ejecución del compilador

### Requisitos previos
- Python 3.11 o superior.
- Instalar dependencias:

```bash
pip install -r requirements.txt
```

### Iniciar la aplicación

```bash
python main.py
```

> **Nota de uso:** El panel de errores inferior puede permanecer oculto hasta que existan errores o advertencias que mostrar.

### Ejecutar tests

```bash
python -m pytest test/test_case.py -v
```
