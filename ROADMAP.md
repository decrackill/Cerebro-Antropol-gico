# Roadmap — Cerebro Antropológico

## Fase 0: Fundamentos (Completada)
- [x] Schema SQLite con cita_textual
- [x] Pipeline de extracción funcional
- [x] Frontend con visualización Cytoscape.js
- [x] Backfill de datos existentes
- [x] Auditorías de integridad

## Fase 1: Modularización (Completada)
- [x] Crear `pipeline/config.py` con constantes
- [x] Crear `pipeline/db.py` con CRUD
- [x] Crear `pipeline/utils.py` con utilidades
- [x] Migrar funciones de `cerebro.py` a módulos
- [x] Crear `pipeline/menu.py` como entry point
- [x] Corregir XSS en render.js
- [x] Crear ARCHITECTURE.md

## Fase 2: Reorganización Arquitectónica (Completada)
- [x] Crear estructura core/extract/review/cli
- [x] Mover archivos a módulos por dominio
- [x] Fusionar full_revision.py → revision.py
- [x] Fusionar recovery.py → limpieza.py
- [x] Eliminar extraction.py y maintenance.py (wrappers)
- [x] Convertir cerebro.py en wrapper de compatibilidad
- [x] Separar datos runtime a runtime/
- [x] Actualizar .gitignore (data/grafo.db, runtime/)
- [x] Unificar convención de nombres (español)
- [x] Actualizar ARCHITECTURE.md
- [x] Actualizar ROADMAP.md

## Fase 3: Calidad de Código (Próxima)
- [ ] Agregar type hints a todas las funciones públicas
- [ ] Eliminar dead code
- [ ] Pinar versiones en requirements.txt
- [ ] Configurar pytest para tests automatizados

## Fase 4: Tests
- [ ] Tests unitarios para core/db.py
- [ ] Tests unitarios para core/utils.py
- [ ] Tests de integración para review/revision.py
- [ ] Tests de integración para review/limpieza.py
- [ ] CI pipeline (GitHub Actions)

## Fase 5: Frontend Mejorado
- [ ] Dividir render.js en graph.js + panel.js + filters.js
- [ ] Agregar manejo de errores en fetch
- [ ] Mejorar UX del panel de citas
- [ ] Responsive design

## Fase 6: Pipeline Mejorado
- [ ] Re-extracción de PDFs faltantes (Argonautas + Boas)
- [ ] Mejorar manejo de errores en extractor.py
- [ ] Logging estructurado
- [ ] Configuración via archivo YAML/TOML

## Fase 7: Documentación
- [x] ARCHITECTURE.md
- [x] ROADMAP.md
- [ ] Completar docstrings a todas las funciones
- [ ] Guía de contribution
- [ ] Ejemplos de uso

## Estadísticas

| Métrica | Fase 0 | Fase 1 | Fase 2 |
|---------|--------|--------|--------|
| Archivos Python (pipeline/) | 6 | 18 | 12 |
| Líneas totales | ~3,300 | ~3,974 | ~2,100 |
| Módulos especializados | 0 | 11 | 8 |
| Redundancia (cerebro.py) | 100% | 100% | 0% (wrapper) |
| Runtime data en pipeline/ | Sí | Sí | No |
