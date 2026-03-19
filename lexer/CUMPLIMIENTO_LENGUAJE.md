# Revisión: Lexer vs documento del lenguaje (Proyecto Mini Compilador)

Este documento verifica que el analizador léxico cumple con el alfabeto, símbolos y palabras reservadas definidos en el PDF del proyecto.

## Alfabeto

| Tipo | Documento PDF | Lexer | Estado |
|------|----------------|-------|--------|
| Alfabético | a-z, A-Z | `[a-zA-Z][a-zA-Z0-9]*` en identificadores (sin '_') | ✓ |
| Numérico | 0-9 | `NUMERO_ENT`, `NUMERO_DEC` | ✓ |
| Símbolos aceptados | " , ( ) { } [ ] ; \ = != == < > => =< : | Comillas en `CADENA`, `; , ( ) { } [ ] :` en `SIMBOLO`, `=`, `==`, `!=`, `=>`, `=<`, `>`, `<` en `OPERADOR`, `\` y `!` en `SIMBOLO` | ✓ |

El lenguaje es **case-insensitive** (mayúsculas/minúsculas); el lexer normaliza a minúsculas para reconocer palabras reservadas.

## Palabras reservadas

Todas las categorías del PDF están en `PALABRAS_RESERVADAS`:

- **Estructura:** Definir, Rol, Usuario, Modulo ✓  
- **Lógica de seguridad:** Permitir, Denegar, Acceder, Validar ✓  
- **Acciones de negocio:** Consultar, Registrar, Modificar, Eliminar, Insertar ✓  
- **Control de flujo:** Si, Entonces, Sino, Mientras, Elegir, Caso, Terminar ✓  
- **Manejo de errores:** Intentar, Atrapar, Error ✓  
- **Tipos y valores:** Cadena, Carácter, Verdadero, Falso, Horario ✓  
- **Operadores lógicos:** Y, O, No ✓  
- **Salida:** Mostrar, Devolver ✓  

## Símbolos terminales

- Operadores: `=`, `==`, `!=`, `=>`, `=<`, `>`, `<` (y `>=`, `<=`) ✓  
- Delimitadores: `( ) { } [ ] ; , : \ !` ✓  
- Cadenas: `"..."` con detección de cadenas sin cerrar (ERROR_LEX_02) ✓  

## Errores léxicos detectados

- **ERROR_LEX_01:** Carácter no reconocido (fuera del alfabeto).  
- **ERROR_LEX_02:** Cadena de texto sin comilla de cierre.  
- **ERROR_LEX_03:** Número mal formado (varios puntos decimales).  
- **ERROR_LEX_04:** Palabra reservada mal escrita (p. ej. `Rool` en vez de `Rol`, `Sii` en vez de `Si`). Se detectan por distancia de edición 1 y se sugiere la corrección.  
- **ERROR_LEX_05:** Identificador mal formado: empieza con número (p. ej. `123Gerente`).  
- **ERROR_LEX_06:** Identificador mal formado: uso de `_` no permitido (p. ej. `_usuario`).  

**Cadenas:** Las cadenas no pueden contener salto de línea; una cadena sin comilla de cierre se limita a la línea actual (Caso 8).  

## Cadenas de ejemplo del PDF

- Válidas: el lexer tokeniza correctamente (roles, asignaciones, condicionales).  
- Inválidas: `Rol#Gerente` → ERROR_LEXICO (# no permitido); `Usuario@1` → ERROR_LEXICO (@ no permitido).  

**Conclusión:** El lexer cumple con el alfabeto, palabras reservadas y símbolos definidos en el documento del lenguaje.
