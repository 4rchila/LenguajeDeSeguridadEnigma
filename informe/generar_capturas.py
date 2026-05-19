"""Orquesta la captura de todas las pantallas invocando capturar_uno.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
INFORME_DIR = ROOT_DIR / "informe"
SCREENSHOTS_DIR = INFORME_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

CAPTURAR_UNO = INFORME_DIR / "capturar_uno.py"


# (nombre, archivo.acl, pestaña 0=tokens 1=ast 2=tabla)
ESCENARIOS = [
    ("01_programa_completo_tokens.png",   "examples/programa_completo.acl",   0),
    ("02_programa_completo_ast.png",      "examples/programa_completo.acl",   1),
    ("03_programa_completo_simbolos.png", "examples/programa_completo.acl",   2),
    ("04_empresa_ventas_tokens.png",      "examples/empresa_ventas.acl",      0),
    ("05_empresa_ventas_ast.png",         "examples/empresa_ventas.acl",      1),
    ("06_empresa_ventas_simbolos.png",    "examples/empresa_ventas.acl",      2),
    ("07_errores_lexicos.png",            "examples/errores_lexicos.acl",     0),
    ("08_errores_sintacticos.png",        "examples/errores_sintacticos.acl", 1),
    ("09_errores_semanticos.png",         "examples/errores_semanticos.acl",  2),
]


def main() -> int:
    for nombre, ruta_rel, pestana in ESCENARIOS:
        archivo = (ROOT_DIR / ruta_rel).as_posix()
        salida = (SCREENSHOTS_DIR / nombre).as_posix()
        print(f"\n=== Generando: {nombre} (pestaña {pestana}) ===")
        result = subprocess.run(
            [sys.executable, str(CAPTURAR_UNO), archivo, str(pestana), salida],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.stdout:
            print(result.stdout.strip())
        if result.returncode != 0:
            print(f"[FALLA] Código de salida: {result.returncode}")
            if result.stderr:
                print(result.stderr.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
