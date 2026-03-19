# LenguajeDeSeguridadEnigma

## ¿Qué es?
LenguajeDeSeguridadEnigma es un **analizador léxico (lexer)** para el **Lenguaje de Control de Accesos Empresarial** (fase 1 del proyecto).  
Convierte el código fuente escrito por el usuario en una lista de `Token` y reporta **errores léxicos con línea y columna**.

La aplicación incluye una **GUI PyQt6** para:
- Escribir/cargar un archivo `.acl`
- Ver la tabla de tokens identificados
- Ver errores léxicos
- Subrayar errores léxicos en vivo dentro del editor (estilo Error Lens)

## Documentación de referencia (PDFs)
- `Propuesta_Analizador_Lexico.pdf` (arquitectura y tokens esperados)
- `Proyecto Mini Compilador.pdf` (alfabeto, símbolos válidos y gramática)
- `casos_prueba_analizador.pdf` (casos 1–16 para validar)

Además, se creó la documentación de verificación:
- `lexer/CUMPLIMIENTO_LENGUAJE.md` (lexer vs el documento del lenguaje)
- `lexer/README_MANUAL_LEXICO.md` (explicación de componentes del lexer)

## Arquitectura (capas)
El sistema se divide en módulos acoplados de forma simple:

### 1) Capa `lexer/` (motor léxico)
- `lexer/tokens.py`
  - Define `TipoToken` y `Token`
  - Contiene el set `PALABRAS_RESERVADAS` (case-insensitive)
- `lexer/error_handler.py`
  - Define `ErrorLexico` y el acumulador `ErrorHandler`
  - Permite al lexer continuar aun encontrando errores
- `lexer/lexer.py`
  - Implementa `Lexer.tokenize(codigo: str) -> list[Token]`
  - Produce tokens y llena `lexer.errores` con errores léxicos

### 2) Capa `gui/` (interfaz)
- `gui/main_window.py`
  - Ventana principal con splitter (editor / resultados)
  - Toolbar: `Analizar`, `Limpiar`, `Cargar archivo`
  - Panel de errores con navegación a línea
- `gui/code_editor.py`
  - `QPlainTextEdit` con numeración de líneas
  - `QSyntaxHighlighter` para resaltado básico
  - **Error Lens**: subrayado ondulado rojo para errores léxicos
- `gui/token_table.py`
  - `QTableWidget` con columnas: `Lexema`, `Tipo de Token`, `Línea`, `Columna`
  - `ErrorPanel` para listar errores léxicos

### 3) Capa `controller.py` (conexión GUI ↔ lexer)
- Actúa como mediador:
  - Al presionar `Analizar`: lee el texto del editor, llama al lexer y actualiza la UI
  - En vivo (debounce + timer): recalcula errores y actualiza el subrayado del editor

## Cómo funciona el lexer
### Case-insensitive
El lexer normaliza el código a minúsculas para reconocer palabras reservadas sin importar mayúsculas/minúsculas.

### Reconocimiento por Regex (orden de patrones)
El lexer utiliza una lista de `patrones_lexicos` y los combina en una regex maestra.  
El **orden es importante** para resolver ambigüedades. En particular:
- Se reconocen errores “especiales” primero cuando aplican (p. ej. cadenas sin cerrar, identificadores mal formados).
- Luego se reconocen tokens válidos: identificadores, operadores, símbolos, números, cadenas.

### Reglas léxicas principales
- **Palabras reservadas**: están en `PALABRAS_RESERVADAS`
  - Se tokenizan como `TipoToken.PALABRA_RESERVADA`
- **Identificadores (`IDENTIFICADOR`)**:
  - Solo letras seguidas de letras o números
  - **NO se permite `_`** (para cumplir el Caso 7 del documento)
- **Números**:
  - `NUMERO_ENT`: enteros (`[0-9]+`)
  - `NUMERO_DEC`: decimales (`[0-9]+\.[0-9]+`)
- **Cadenas**:
  - `CADENA`: `"..."` sin saltos de línea
  - `CADENA_SIN_CERRAR`: `"..."` sin cerrar dentro de la misma línea
- **Operadores**:
  - Relacionales: `== != => =< >= <= > <`
  - Asignación: `=`
- **Símbolos (`SIMBOLO`)**:
  - Agrupación y delimitadores: `(` `)` `{` `}` `[` `]` `;` `,` `\` `:`
  - Se aceptó `:` para soportar el formato del `switch` en los casos de prueba (`Caso "X":`).

## Tipos de errores léxicos
Los errores léxicos se reportan como objetos `ErrorLexico` (almacenados en `lexer.errores`), con:
- `codigo` (ej. `ERROR_LEX_01`)
- `caracter` (fragmento causante)
- `linea` y `columna`
- `mensaje` descriptivo

Errores implementados:
1. `ERROR_LEX_01` — carácter no reconocido (foráneo)
   - Ej.: `Rol#Gerente`, `Usuario@1`, `Permitir$`
2. `ERROR_LEX_02` — cadena sin comilla de cierre
   - Ej.: `Mostrar "Acceso concedido;`
3. `ERROR_LEX_03` — número mal formado (múltiples puntos decimales)
   - Ej.: `15.5.2`
4. `ERROR_LEX_04` — palabra reservada mal escrita
   - Se detecta por **distancia de edición 1 (Levenshtein)** y se sugiere una corrección.
   - Ej.: `Rool` -> `Rol`, `Sii` -> `Si`
   - Para evitar falsos positivos, la detección:
     - No sugiere si hay dígitos (ej. `Usuario1`)
     - No sugiere si la longitud es demasiado corta
5. `ERROR_LEX_05` — identificador mal formado: comienza con número
   - Ej.: `123Gerente`
6. `ERROR_LEX_06` — identificador mal formado: uso de `_` no permitido
   - Ej.: `_usuario`

## Error Lens (subrayado en vivo)
Dentro del editor (`gui/code_editor.py`) se implementó un subrayado ondulado rojo para los errores léxicos:
- `controller.py` usa un `QTimer` con debounce (`DEBOUNCE_MS = 450`)
- Tras dejar de escribir, el controller ejecuta el lexer y envía errores a:
  - `CodeEditor.set_lexical_errors(errors)`
- El editor calcula la posición por `linea` + `columna` y subraya el lexema con:
  - `QTextCharFormat.UnderlineStyle.WaveUnderline`

Al presionar `Limpiar`, se ejecuta `set_lexical_errors([])` para borrar los subrayados.

## Ejemplos incluidos
En `examples/` se agregaron programas **completos** en el lenguaje (para demostrar categorías y flujo general).

Archivos:
- `examples/01_roles_y_usuarios.acl`
- `examples/02_reglas_seguridad.acl`
- `examples/03_control_flujo.acl`
- `examples/04_manejo_errores_y_salida.acl`
- `examples/05_programa_completo.acl`
- `examples/README.md` (descripción de cada ejemplo)

Cómo probar:
1. Ejecutar `python main.py`
2. Click en **Cargar archivo** (📂)
3. Seleccionar uno de los `.acl` en `examples/`
4. Pulsar **▶ Analizar**

## Verificación contra los casos de prueba (1–16)
Se validó el lexer **programáticamente** contra los casos del PDF `casos_prueba_analizador.pdf`:
- Los casos marcados “válidos” generan **0 errores**
- Los casos con errores generan el número esperado de errores léxicos (y los tipos correctos)

Esto incluye los ajustes necesarios:
- Aceptar `:` como símbolo para el `switch` (`Caso "X":`)
- Restringir identificadores para que `_` no sea válido
- Arreglar el manejo de cadenas sin cerrar para que no “se coma” el siguiente `Mostrar ...`
- Evitar falsos positivos en la sugerencia de palabras reservadas mal escritas

## Ejecución
### Requisitos
- Python 3.11+ (en el entorno se usa Python 3.12)
- Dependencia principal: PyQt6

### Instalar dependencias
```bash
pip install PyQt6
```

### Ejecutar la GUI
```bash
python main.py
```

## Probar el lexer sin GUI (opcional)
Existe un script de prueba manual en:
- `test/test_lexer_manual.py`

Se puede ejecutar con:
```bash
python test_lexer_manual.py
```

## Archivos importantes
- `main.py` (arranque)
- `controller.py` (conexión + Error Lens en vivo)
- `lexer/lexer.py` (scanner/lexer)
- `gui/main_window.py`, `gui/code_editor.py`, `gui/token_table.py`

## Estado final
El sistema quedó **listo y funcional**:
- Lexer conectado correctamente con GUI
- Errores léxicos reportados con línea/columna
- Error Lens subrayando errores en vivo
- Coincidencia con la especificación de los PDFs
- Coincidencia con los casos 1–16 del documento de pruebas

