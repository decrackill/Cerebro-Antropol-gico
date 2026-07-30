# Generator State — Iteración Completa (Pasos 9-12)

## Resumen

Implementé los Pasos 9, 10, 11 y 12 del plan, culminando con 94 tests pasando (antes: 89).

## Paso 9 — Salvaguarda de Revisión Ontológica

### Qué se construyó
- **Migración DB**: columna `revision_estado TEXT DEFAULT 'pendiente'` en tabla `nodos`
- **Validador #6** en `validar_relacion()`: bloquea relaciones si origen o destino tienen `revision_estado != 'ok'`, excepto si el nodo no existe (es flexible para recién creados)
- **`marcar_nodos_revisados()`**: función batch que acepta `ids`, `tipo` o todos los nodos
- **`migrar_revision_estado()`**: agrega columna idempotentemente, marca nodos existentes como `ok`
- **Opción 16** en menú: "Marcar revisados" con filtros interactivos (por tipo/todos/pendientes)
- **4 tests** en `TestRevisionEstado`: pendiente bloquea, ok permite, ambos pendientes bloquea, inexistente bloquea

### Archivos modificados
- `pipeline/core/db.py` — +60 líneas (migrar_revision_estado, marcar_nodos_revisados, _validar_revision_estado, 6to validador en cadena)
- `pipeline/cli/menu.py` — +30 líneas (opción 16)
- `tests/test_firewall.py` — +40 líneas, 4 tests nuevos

## Paso 10 — Menú Optimizado

### Cambios
- **Colores ANSI**: encabezados en `BOLD`, opciones en `CYAN`, descripciones en `DIM`, errores en `RED`, éxito en `GREEN`. Sin dependencias externas.
- **Estadísticas en header**: muestra "X nodos · Y relaciones · Z pendientes" en tiempo real
- **Agrupación lógica**: secciones EXTRACCIÓN, REVISIÓN, CONEXIONES, LIMPIEZA, DIAGNÓSTICO, MANTENIMIENTO
- **Nueva estructura de datos**: `SECCIONES` (lista de tuplas) + `OPCIONES_DICT` (dict plano para búsqueda rápida)
- **Comando `help`**: muestra ruta a HELP.md y comandos rápidos

### Archivos modificados
- `pipeline/cli/menu.py` — reescritura completa de la UI
- `tests/test_menu.py` — actualizado para nueva estructura
- `tests/test_imports.py` — actualizado para `OPCIONES_DICT`

## Paso 11 — Documentación Técnica

### Cambios
- **`HELP.md`**: guía rápida con tabla de opciones, conceptos ontológicos, comandos y arquitectura
- **Docstrings mejorados**: `conectar_db()` ahora con sección Returns
- **Integración en menú**: comando `help` muestra ruta al archivo

## Paso 12 — Comando 'flujo' Interactivo

### Cambios
- `mostrar_flujo()` ahora lee estado real de la DB para mostrar progreso
- Cada paso muestra `✓` (completado) u `○` (pendiente) con sugerencias
- Detecta: existencia de PDFs en `libros/`, candidatos pendientes, nodos extraídos, relaciones, aislados, revisión ontológica, exportación
- Resumen al final con 1401 nodos · 1071 relaciones · 386 aislados · 0 pendientes

## Tests
- **94 tests total** (antes: 89)
- `test_firewall.py`: 60 → 64 tests (+4 para revisión ontológica)
- `test_menu.py`: 4 → 5 tests (+1 para secciones cubren todo)
- Todos pasando

## Estado de la DB
- 1401 nodos (todos con revision_estado='ok')
- 1071 relaciones
- 386 nodos aislados
- 4 índices activos (1 único + 2 de rendimiento + PKs)
