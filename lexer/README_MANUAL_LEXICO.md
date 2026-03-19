# 📖 Manual de Integración: Motor Léxico (Scanner)

**Proyecto:** Mini-Compilador de Control de Accesos
**Módulo:** Fase 1 - Analizador Léxico
**Responsable:** Jordi Garcia

Este documento explica detalladamente cómo funciona el núcleo del Analizador Léxico y cómo deben interactuar las demás capas (GUI de Víctor y Tests de German) con él. El analizador se divide en tres archivos ubicados en la carpeta `lexer/` y ha sido diseñado de manera desacoplada para facilitar la integración.

---

## 1. `tokens.py` - *El Diccionario y las Estructuras de Datos*
Este archivo es el cimiento estructural y define cómo se ven de forma abstracta los datos que las demás capas van a recibir y procesar.

### ¿Qué contiene?
- **`TipoToken` (Enum):** Clasifica los tokens en familias principales: `PALABRA_RESERVADA`, `IDENTIFICADOR`, `NUMERO_ENT`, `NUMERO_DEC`, `CADENA`, `OPERADOR`, `SIMBOLO` y `ERROR_LEXICO`.
- **`Token` (Dataclass):** Es el objeto que empaqueta la información de cada unidad lógica del código. Cada token procesado entrega:
  - `lexema` (str): El texto exacto capturado (por ejemplo, `"Definir"`, `15.5`, `;`).
  - `tipo` (TipoToken): La categoría a la que pertenece dictada por el Enum anterior.
  - `linea` (int): En qué línea del código fuente original se encontró.
  - `columna` (int): En qué columna (carácter exacto) empieza dentro de la línea.
- **`PALABRAS_RESERVADAS` (Diccionario):** Un conjunto optimizado `set` de las palabras clave del lenguaje. Esto es crucial para diferenciar eficientemente O(1) si un lexema como `gerente` es el nombre de una variable (identificador), o si `definir` es una instrucción nativa (keyword).

### ¿Para qué le sirve al equipo?
- **Víctor (Interfaz - GUI):** Podrá leer la propiedad `tipo` de cada `Token` devuelto para aplicar el resaltado de sintaxis correspondiente en el Componente del Editor de Texto.
- **German (Integración y Tests - Controller):** Usará `TipoToken` en sus aserciones (`assert`) de Pytest para evaluar automáticamente que el flujo de los casos de prueba funcione correctamente.

---

## 2. `error_handler.py` - *El Gestor de Crisis Léxicas*
Para mantener el procesador fluido, este script se encarga de recolectar, estructurar y describir cualquier cosa que el usuario escriba mal o que no pertenezca a nuestro alfabeto empresarial, permitiendo al lexer continuar su trabajo y no crashear la aplicación de interfaz gráfica.

### ¿Qué contiene?
- **`ErrorLexico` (Dataclass):** Define la anatomía del reporte de un incidente. Guarda el código del error (ej. `"ERROR_LEX_01"`), el carácter o fragmento que lo provocó, la línea, la columna y un mensaje descriptivo fácil de entender para el usuario.
- **`ErrorHandler` (Clase Gestora):** Es la clase contenedora encargada de registrar los errores en memoria (`self.errores = []`). Tiene un método principal `registrar_error(codigo, caracter, linea, columna, mensaje)` que crea un nuevo incidente y lo acumula.

**Contempla errores léxicos específicos:**
1. `ERROR_LEX_01`: Caracteres Foráneos o Símbolos no definidos (como `@` , `#`, `$`, etc).
2. `ERROR_LEX_02`: Cadenas Abiertas. Si se detecta una comilla de apertura `"` pero el lexer no detecta el cierre.
3. `ERROR_LEX_03`: Números Mal Formados, por ejemplo, los que contienen varios puntos decimales `15.5.2`.
4. `ERROR_LEX_04`: Palabras reservadas mal escritas (distancia de edición 1 con sugerencia).
5. `ERROR_LEX_05`: Identificador mal formado: comienza con número (p. ej. `123Gerente`).
6. `ERROR_LEX_06`: Identificador mal formado: uso de `_` no permitido (p. ej. `_usuario`).

### ¿Para qué le sirve al equipo?
- **Víctor (Interfaz - GUI):** Si existen errores, podrá llamar al panel inferior en la ventana principal, iterando sobre la lista que le provee el método `.obtener_errores()` del manejador, e indicando la gravedad y la posición del error para ayudar al usuario.

---

## 3. `lexer.py` - *El Motor de Análisis de Texto (El Corazón)*
Aquí es donde ocurre verdaderamente el análisis. Este archivo toma el texto fuente crudo insertado en la interfaz y lo descompone en la lista secuencial de objetos `Token`.

### ¿Cómo funciona la lógica de procesamiento?
1. **Reglas Léxicas (RegEx):** Utiliza Expresiones Regulares de la librería nativa `re` de Python, las cuales actúan como expresiones emparejadoras de patrones (`patrones_lexicos`). Por ejemplo, para atrapar números decimales, utiliza `r'[0-9]+\.[0-9]+'`. El orden en la lista `patrones_lexicos` prioriza qué coincidencia resolver antes en caso de ambigüedades.
2. **Normalización a Minúsculas (Case-Insensitivity):** Dado que la propuesta técnica exige que el entorno sea "Case-Insensitive" como medida de resiliencia ante errores de teclado de los operarios, justo antes de empezar la tokenización el código fuente es pasado por un `.lower()`. No obstante, la longitud de la cadena y posiciones se mantienen consistentes.
3. **Función Principal `tokenize(codigo_fuente)`:** 
   - Va barriendo el flujo de caracteres.
   - Si empareja un salto de línea, actualiza los marcadores de `linea_actual` y `columna`.
   - Ignora silenciosamente espacios en blanco.
   - Por cada otro emparejamiento válido, evalúa si es una Palabra Reservada (consultando con `tokens.py`) o un token genérico. Lo empaqueta usando la clase `Token` y lo adjunta a la lista base.
   - Si detecta errores léxicos específicos, delega el reporte al módulo `error_handler.py` de forma transparente.

---

## 🚀 ¿Cómo llamar e interactuar con el Lexer desde las otras Capas?
La integración entre los distintos módulos se debe mantener al nivel más sencillo. Los chicos de Controlador y GUI solo deben realizar la siguiente implementación para comunicarse con el lexer:

```python
# 1. Importar la clase principal del motor desde el paquete lexer
from lexer.lexer import Lexer

# 2. Instanciar el analizador léxico (generalmente en el Controller)
mi_lexer = Lexer()

# 3. Pasar el texto crudo simulando la entrada desde la GUI
codigo_escrito_por_el_usuario = '''
Definir Rol Gerente;
Rol Gerente = Acceder Reportes;
'''
lista_de_tokens = mi_lexer.tokenize(codigo_escrito_por_el_usuario)

# 4. Leer los resultados (Iterar) para llenar la UI o hacer las pruebas de German
for tok in lista_de_tokens:
    # Se ignora la impresión de errores porque están como tipo ERROR_LEXICO
    print(f"[{tok.linea}:{tok.columna}] -> {tok.lexema} : {tok.tipo.name}")
    
# 5. Extraer los errores para el Panel de Errores
if mi_lexer.errores.tiene_errores():
    print(f"Atención equipo, tenemos {len(mi_lexer.errores.obtener_errores())} fallos.")
    for err in mi_lexer.errores.obtener_errores():
        print(f"[{err.codigo}] - {err.mensaje} provocado por '{err.caracter}'")
```

---
*Fin del Manual de Integración.*
