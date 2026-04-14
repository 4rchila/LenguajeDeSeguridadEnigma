# Compilador — Lenguaje de Control de Accesos Empresarial (Enigma)

## ¿Qué es?
Este proyecto es la implementación de las **Fase 1 (Analizador Léxico)** y **Fase 2 (Analizador Sintáctico)** de un compilador para el **Lenguaje de Control de Accesos Empresarial (Enigma)**.

La aplicación incluye una **GUI PyQt6** avanzada que proporciona una experiencia de desarrollo interactiva y visual para entender cómo un compilador analiza el código, incluyendo un **Modo Didáctico** con animaciones en tiempo real.

### Características Principales Implementadas:
- **Analizador Léxico Completo:** Escaneo de tokens, reconocimiento de patrones, y detección de errores léxicos específicos (con soporte de recuperación/distancia Levenshtein).
- **Analizador Sintáctico Descendente (Recursive Descent):** Construcción estructurada del Árbol de Sintaxis Abstracta (AST) implementada en base a la norma BNF del lenguaje.
- **Recuperación de Errores Sintácticos (Modo Pánico / Synchronization):** Si el código tiene un error sintáctico, el compilador sincroniza sobre delimitadores (bloques `{}`) u operadores clave para seguir analizando y encontrar más errores sin colapsar en el primero.
- **Modo Didáctico Animado:** Simulación paso a paso:
  1. *Fase Léxica:* Reconocimiento token por token sincronizado con el código.
  2. *Fase Sintáctica:* Construcción iterativa (nodo a nodo) del AST visual.
- **Error Lens e Interfaz Dinámica:** Subrayado de errores en tiempo real y ocultamiento inteligente del panel de errores (solo visible si se encuentran errores en el código).
- **Visor de AST Gráfico y Estructurado:** El análisis produce tanto una vista de árbol clásica como un diagrama interactivo con nodos circulares y arcos autoajustables.

---

## Arquitectura (Capas)

El sistema se divide en módulos fuertemente cohesivos y desacoplados:

### 1) Capa `lexer/` (Motor Léxico)
- `lexer/tokens.py`: Define tipos de tokens (`TipoToken`) y diccionarios de palabras reservadas (case-insensitive).
- `lexer/error_handler.py`: Gestiona los errores léxicos permitiendo al escáner reportar en cadena sin interrumpir a la primera.
- `lexer/lexer.py`: Clase principal `Lexer` que consume código mediante expresiones regulares priorizadas y emite una lista de `Token`.

### 2) Capa `parser/` (Motor Sintáctico)
- `parser/ast_nodes.py`: Define el modelo de datos (las ramas y hojas) que representan todas y cada una de las expresiones y comandos (`Node`, `DeclaracionNode`, `SiNode`, `AsignacionNode`, etc.).
- `parser/parser.py`: Clase principal `Parser`. Un analizador descendente predictivo (recursive descent). Consume la lista de tokens proveniente del lexer y los traduce en reglas gramaticales para conformar el AST o en su defecto recolectar los errores sintácticos detectados.

### 3) Capa `gui/` (Interfaz Gráfica - PyQt6)
- `gui/main_window.py`: Ventana principal en pantalla completa. Aloja los páneles, los menús de control (Modo rápido / Modo didáctico) y el gestor de layout que oculta el panel de errores si no son necesarios.
- `gui/code_editor.py`: Editor de texto con numeración de líneas que subraya en rojo ondulado los errores ("Error Lens") y cuenta con resaltos con color verde (léxico) y violeta (sintáctico) para el modo didáctico.
- `gui/token_table.py` & `ErrorPanel`: Visualización en tablas de tokens y listado de errores de sistema con navegación activa.
- `gui/ast_tree_viewer.py`: Árbol jerárquico tipo JSON/Carpetas de la sintaxis del lenguaje.
- `gui/ast_graph_widget.py`: Motor gráfico personalizado de dibujo en Canvas que dibuja el AST de abajo hacia arriba de forma óptima usando círculos enlazados y flechas para denotar relaciones lógicas.

### 4) Capa `controller.py` (Coordinador)
- Orquesta las interacciones. Configura los Timers y el pipeline cuando se interactúa con las animaciones en Modo Didáctico (pasando por estado Léxico y Estado Sintáctico de forma segura).

---

## Archivos de Prueba Incorporados

Dentro de la subcarpeta `@examples/` se han incorporado archivos de pruebas exhaustivas.
1. `06_estructuras_correctas.acl`: Contiene **absolutamente todos** los flujos gramaticales correctos que el código puede aceptar en el diseño del lenguaje.
2. `07_errores_lexicos.acl`: Provisto de todos los posibles errores de escáner en caracteres aislados o cadenas sin cerrar.
3. `08_errores_sintacticos.acl`: Estructuras desfasadas (faltan parentesis, palabras fuera de orden gramatical, múltiples tipos de llaves de cierre rotas). Su prueba corrobora que el *Analizador Sintáctico aplica Modo Pánico logrando reportar los 7 errores sin fracasar desde el primero*.

---

## Ejecución del compilador

### Requisitos Previos
- Instalar Python 3.10 o superior.
- Instalar la interfaz PyQt6:
```bash
pip install PyQt6
```

### Iniciar la App
Para correr el software localmente, ubicar la consola en la carpeta raíz y accionar el punto de entrada:

```bash
python main.py
```
> **Nota de uso:** El panel de errores en la parte inferior derecha estará oculto de forma intencionada e inteligente. Solamente aparecerá cuando el archivo tenga algún código erróneo.
