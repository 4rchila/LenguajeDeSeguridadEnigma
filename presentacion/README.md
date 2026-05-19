# Presentación Ejecutiva — Compilador ENIGMA

Página web que sirve como soporte visual para la presentación final del proyecto
**Compilador del Lenguaje de Seguridad Empresarial "ENIGMA"** (Universidad Rafael Landívar, 2026).

## Cómo abrirla

Es estática (HTML + CSS + JS, sin build). Hay dos formas:

1. **Doble click** en `presentacion/index.html` — se abre en el navegador.
2. **Servidor local** (recomendado para que las capturas carguen sin advertencias):
   ```bash
   # Desde la carpeta del proyecto
   cd presentacion
   python -m http.server 8000
   # luego abrir http://localhost:8000
   ```

## Estructura

```
presentacion/
├── index.html               ← Página principal (15 diapositivas)
├── css/styles.css           ← Estilos completos
├── js/main.js               ← Navegación, timer, overview, lightbox
└── assets/
    ├── logo.png             ← Logo ENIGMA
    └── capturas/            ← 9 screenshots del compilador
```

## Atajos de teclado

| Acción | Tecla |
|---|---|
| Siguiente diapositiva | `→` `↓` `Espacio` `PageDown` |
| Anterior diapositiva | `←` `↑` `PageUp` |
| Primera / última | `Home` / `End` |
| Ir a diapositiva N | `1`…`9` |
| Resumen de slides | `O` |
| Cerrar overlay | `Esc` |
| Iniciar/parar timer | `T` (doble click en el timer para reiniciar) |
| Ayuda | `?` |
| Pantalla completa | `F` |

## Cobertura de los lineamientos

La presentación está dividida en **15 diapositivas** organizadas según los cuatro
pilares solicitados:

1. **Contexto del compilador** — problema, objetivo, lenguaje y aplicación real.
2. **Explicación de las fases** — léxico, sintáctico, semántico, tabla de símbolos
   y generación de código (JSON RBAC/ABAC).
3. **Integración del sistema** — pipeline orquestado por `Controller`, pruebas
   realizadas y errores detectados.
4. **Demostración funcional** — capturas del compilador en ejecución y caso real
   "Tech-Store".

El timer está pre-configurado a **13:00** para respetar la duración exacta de la
exposición. Los tres integrantes (Jordi García, Víctor Morales, Germán Archila)
están acreditados en la portada y el cierre.
