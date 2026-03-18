from dataclasses import dataclass

@dataclass
class ErrorLexico:
    """
    Representa un error léxico detectado por el analizador.
    """
    codigo: str       # Ej: "ERROR_LEX_01"
    caracter: str     # El fragmento o carácter infractor
    linea: int        # Línea donde ocurrió
    columna: int      # Columna donde ocurrió
    mensaje: str      # Descripción del error

class ErrorHandler:
    """
    Clase central para registrar y acumular errores durante el proceso 
    de compilación léxica. Permite al lexer continuar analizando el resto del 
    código a pesar de encontrar tokens inválidos.
    """

    def __init__(self):
        self.errores = []

    def registrar_error(self, codigo: str, caracter: str, linea: int, columna: int, mensaje: str):
        """
        Crea una instancia de ErrorLexico y lo agrega a la lista interna.
        """
        nuevo_error = ErrorLexico(
            codigo=codigo,
            caracter=caracter,
            linea=linea,
            columna=columna,
            mensaje=mensaje
        )
        self.errores.append(nuevo_error)

    def print_errores(self):
        """
        Imprime los errores en consola, útil para depuración.
        """
        for err in self.errores:
            print(f"[{err.codigo}] Línea {err.linea}:{err.columna} - {err.mensaje}: '{err.caracter}'")

    def tiene_errores(self) -> bool:
        """
        Retorna True si hay errores léxicos acumulados.
        """
        return len(self.errores) > 0

    def obtener_errores(self) -> list[ErrorLexico]:
        """
        Devuelve la lista actual de errores.
        """
        return self.errores

    def limpiar_errores(self):
        """
        Limpia la estructura de datos, útil si se desea re-escanear sin reiniciar la app.
        """
        self.errores.clear()
