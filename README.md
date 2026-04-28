# Compilador — Lenguaje de Control de Accesos Empresarial (Enigma)

## ¿Qué es?
Este proyecto es la implementación completa de las **3 Fases** de un compilador para el **Lenguaje de Control de Accesos Empresarial (Enigma)**:

1. **Fase 1 — Analizador Léxico:** Escaneo de tokens y detección de errores léxicos.
2. **Fase 2 — Analizador Sintáctico:** Construcción del Árbol de Sintaxis Abstracta (AST).
3. **Fase 3 — Analizador Semántico:** Validación de reglas RBAC/ABAC y generación de Tabla de Símbolos.

La aplicación incluye una **GUI PyQt6** avanzada que proporciona una experiencia de desarrollo interactiva y visual para entender cómo un compilador analiza el código, incluyendo un **Modo Didáctico** con animaciones en tiempo real.

### Características Principales Implementadas:
- **Analizador Léxico Completo:** Escaneo de tokens, reconocimiento de patrones, y detección de 6 tipos de errores léxicos (con soporte de recuperación y distancia Levenshtein para sugerencias).
- **Analizador Sintáctico Descendente (Recursive Descent):** Construcción estructurada del AST implementada en base a la gramática BNF del lenguaje, con soporte de condiciones lógicas compuestas (Y, O, No).
- **Recuperación de Errores Sintácticos (Modo Pánico):** Si el código tiene un error sintáctico, el compilador sincroniza sobre delimitadores (`;`, `{}`) para seguir analizando y encontrar más errores sin colapsar.
- **Analizador Semántico con 7 Validaciones:** Unicidad de entidades, integridad referencial, compatibilidad de tipos, coherencia RBAC, expresiones booleanas, operaciones entre tipos, y conflicto de políticas.
- **Tabla de Símbolos:** Registro de entidades (Roles, Usuarios, Módulos) con políticas de seguridad y variables ABAC globales (Horario, MontoVenta, UbicacionIP).
- **Modo Didáctico Animado:** Simulación paso a paso con 3 fases:
  1. *Fase Léxica:* Reconocimiento token por token sincronizado con el código.
  2. *Fase Sintáctica:* Construcción iterativa (nodo a nodo) del AST visual.
  3. *Fase Semántica:* Validación de reglas de negocio.
- **Error Lens e Interfaz Dinámica:** Subrayado de errores en tiempo real y ocultamiento inteligente del panel de errores.
- **Visor de AST Gráfico y Estructurado:** Vista de árbol clásica y diagrama interactivo con nodos circulares y arcos.
- **Tabla de Símbolos Visual:** Pestaña dedicada mostrando Identificador, Tipo, Sub-Tipo, Rol Vinculado y Políticas.

---

## Arquitectura (Capas)

El sistema se divide en módulos fuertemente cohesivos y desacoplados:

### 1) Capa `lexer/` (Motor Léxico)
- `lexer/tokens.py`: Define tipos de tokens (`TipoToken`) y diccionarios de palabras reservadas (case-insensitive).
- `lexer/error_handler.py`: Gestiona los errores léxicos permitiendo al escáner reportar en cadena sin interrumpir a la primera.
- `lexer/lexer.py`: Clase principal `Lexer` que consume código mediante expresiones regulares priorizadas y emite una lista de `Token`.

### 2) Capa `parser/` (Motor Sintáctico)
- `parser/ast_nodes.py`: Define 14 tipos de nodos del AST que representan todas las expresiones y comandos del lenguaje (`ProgramNode`, `DefinicionEntidadNode`, `SiEntoncesNode`, `CondicionLogicaNode`, etc.).
- `parser/parser.py`: Clase principal `Parser`. Analizador descendente predictivo (recursive descent) con precedencia de operadores lógicos (O < Y < No < relacionales).

### 3) Capa `semantic/` (Motor Semántico)
- `semantic/semantic_analyzer.py`: Analizador que recorre el AST con patrón Visitor y valida 7 reglas semánticas (ERR_SEM_01 a ERR_SEM_07).
- `semantic/symbol_table.py`: Tabla de Símbolos con registro de entidades, políticas RBAC, y variables de entorno ABAC globales.
- `semantic/semantic_errors.py`: Catálogo de 7 errores semánticos con códigos y mensajes descriptivos.

### 4) Capa `gui/` (Interfaz Gráfica - PyQt6)
- `gui/main_window.py`: Ventana principal con layout dual (editor + paneles de resultados).
- `gui/code_editor.py`: Editor de texto con numeración de líneas, syntax highlighting, y Error Lens (subrayado ondulado rojo).
- `gui/token_table.py` & `ErrorPanel`: Tablas de tokens y listado de errores (léxicos, sintácticos y semánticos diferenciados con íconos).
- `gui/ast_tree_viewer.py`: Árbol jerárquico tipo carpetas del AST.
- `gui/ast_graph_widget.py`: Motor gráfico personalizado con nodos circulares, flechas y animación paso a paso.
- `gui/symbol_table_widget.py`: Visualización tabular de la Tabla de Símbolos (Fase 3).
- `gui/icons.py`: Biblioteca de 15 íconos vectoriales dibujados con QPainter (sin dependencias externas).

### 5) Capa `controller.py` (Coordinador)
- Orquesta las 3 fases del pipeline de compilación.
- Gestiona el Modo Didáctico con máquina de estados (Léxico → Sintáctico → Semántico).
- Implementa Live Compile (compilación silenciosa debounced al editar).

---

## Archivos de Prueba

### Carpeta `examples/` (16 archivos `.acl`)
1. `01-05`: Ejemplos básicos del lenguaje.
2. `06_estructuras_correctas.acl`: **Todas** las estructuras gramaticales válidas.
3. `07_errores_lexicos.acl`: Todos los errores de escáner posibles.
4. `08_errores_sintacticos.acl`: Prueba del Modo Pánico (7 errores sin crash).
5. `09-16`: Ejemplos semánticos, incluyendo cada uno de los 7 errores semánticos y un programa empresarial completo.

### Carpeta `test/` (Pruebas Automatizadas)
- `test/test_case.py`: Suite de 60 tests con pytest cubriendo las 3 fases.

---

## Ejecución del compilador

### Requisitos Previos
- Python 3.11 o superior.
- Instalar las dependencias:
```bash
pip install -r requirements.txt
```

### Iniciar la App
```bash
python main.py
```
> **Nota de uso:** El panel de errores en la parte inferior derecha estará oculto de forma inteligente. Solamente aparecerá cuando el archivo tenga algún código erróneo.

### Ejecutar Tests
```bash
python -m pytest test/test_case.py -v
```
