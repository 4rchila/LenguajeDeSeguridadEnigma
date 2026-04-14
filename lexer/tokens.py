from enum import Enum, auto
from dataclasses import dataclass

class TipoToken(Enum):
    """
    Enumeración que define todas las categorías léxicas (tokens)
    reconocidas por nuestro Mini-Compilador de Control de Accesos.
    """
    # 1. Palabras Reservadas (Keywords)
    PALABRA_RESERVADA = auto()  # Agrupa todas las keywords por simplicidad en esta fase

    # 2. Identificadores (Nombres definidos por usuario: modVentas2, cajero_1)
    IDENTIFICADOR = auto()

    # 3. Literales Numéricos
    NUMERO_ENT = auto()  # Ej: 1, 25, 100
    NUMERO_DEC = auto()  # Ej: 15.5

    # 4. Cadenas de Texto
    CADENA = auto()      # Ej: "Gerente", "Ventas"

    # 5. Operadores
    OPERADOR = auto()    # Agrupa Lógicos, Relacionales y de Asignación (=, ==, !=, <, >, =>, =<)

    # 6. Símbolos de Agrupación y Delimitadores
    SIMBOLO = auto()     # ( ) { } [ ] ; , \

    # 7. Errores Léxicos
    ERROR_LEXICO = auto() # Caracteres foráneos, cadenas abiertas, etc.

@dataclass
class Token:
    """
    Estructura de datos que representa una unidad léxica ya procesada.
    Se utiliza @dataclass para obtener automáticamente un constructor (__init__)
    y una representación en cadena (__repr__) limpia.
    """
    lexema: str
    tipo: TipoToken
    linea: int
    columna: int
    start_index: int = -1
    end_index: int = -1  # Final absoluto del token en el documento

# Diccionario de Palabras Reservadas para búsqueda rápida O(1).
# Todas deben estar en MINÚSCULAS porque nuestro lenguaje es Case-Insensitive.
PALABRAS_RESERVADAS = {
    # Estructura y Definición
    "definir", "rol", "usuario", "modulo",
    
    # Lógica de Seguridad (Acciones de Permisos)
    "permitir", "denegar", "acceder", "validar",
    
    # Acciones de Negocio
    "consultar", "registrar", "modificar", "eliminar", "insertar",
    
    # Control de Flujo
    "si", "entonces", "sino", "mientras", "elegir", "caso", "terminar",
    
    # Manejo de Errores
    "intentar", "atrapar", "error",
    
    # Tipos y Valores Lógicos
    "cadena", "caracter", "horario", "verdadero", "falso",
    
    # Operadores Lógicos (como palabras)
    "y", "o", "no",
    
    # Salida del sistema
    "mostrar", "devolver"
}
