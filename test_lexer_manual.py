import sys
from lexer.lexer import Lexer

def probar_lexer():
    # Código de ejemplo sacado de la sección 7.1 del PDF junto con el error del 7.3
    codigo_prueba = """
    Definir Rol Gerente;
    Rol Gerente = Acceder Reportes;
    Si Verdadero Entonces { Permitir Consultar; }
    Mostrar "Acceso concedido";
    // Este es un comentario de prueba que el lexer debe ignorar por completo.
    
    Rol#Gerente = Acceder;
    "Test de cadena sin cerrar
    15.5.2
    """
    
    print("Iniciando prueba manual del Analizador Léxico...")
    print("-" * 50)
    
    lexer = Lexer()
    tokens = lexer.tokenize(codigo_prueba)
    
    print("\\nTOKENS OBTENIDOS:")
    print("-" * 50)
    for t in tokens:
        print(f"[{t.linea}:{t.columna}] {t.tipo.name} -> '{t.lexema}'")
        
    print("\\nERRORES ENCONTRADOS:")
    print("-" * 50)
    if lexer.errores.tiene_errores():
        lexer.errores.print_errores()
    else:
        print("No se encontraron errores léxicos.")
        
if __name__ == "__main__":
    probar_lexer()
