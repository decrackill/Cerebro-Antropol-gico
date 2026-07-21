# Roadmap — Cerebro Antropológico

**Fuente de verdad**: [MANIFIESTO_ONTOLOGICO.md](MANIFIESTO_ONTOLOGICO.md) v1.1

## Estado Actual

| Componente | Estado |
|------------|--------|
| Ontología (Manifiesto v1.1) | ✅ Completa |
| Tipos de nodo (8) | ✅ Implementados |
| Relaciones canónicas (12) | ✅ Implementadas |
| Firewall epistemológico | ✅ Implementado y testeado |
| Tests de validación | ✅ 89 tests passing |
| Documentación técnica | ✅ Actualizada |

## Fases Completadas

### Fase 0: Fundamentos ✅
- [x] Schema SQLite con cita_textual
- [x] Pipeline de extracción funcional
- [x] Frontend con visualización Cytoscape.js
- [x] Backfill de datos existentes
- [x] Auditorías de integridad

### Fase 1: Modularización ✅
- [x] Crear `pipeline/config.py` con constantes
- [x] Crear `pipeline/db.py` con CRUD
- [x] Crear `pipeline/utils.py` con utilidades
- [x] Migrar funciones de `cerebro.py` a módulos
- [x] Crear `pipeline/menu.py` como entry point
- [x] Corregir XSS en render.js
- [x] Crear ARCHITECTURE.md

### Fase 2: Reorganización Arquitectónica ✅
- [x] Crear estructura core/extract/review/cli
- [x] Mover archivos a módulos por dominio
- [x] Fusionar full_revision.py → revision.py
- [x] Fusionar recovery.py → limpieza.py
- [x] Eliminar extraction.py y maintenance.py (wrappers)
- [x] Convertir cerebro.py en wrapper de compatibilidad
- [x] Separar datos runtime a runtime/
- [x] Actualizar .gitignore
- [x] Unificar convención de nombres (español)

### Fase 3: Alineación con Manifiesto v1.1 ✅
- [x] Sincronizar 12 tipos canónicos en config.py
- [x] Actualizar prompts.py con 12 tipos + firewall
- [x] Actualizar CHECK constraint en init_db.py
- [x] Actualizar CHECK constraint en conftest.py
- [x] Implementar `validar_relacion()` centralizada
- [x] Integrar validación en revision.py
- [x] Integrar validación en limpieza.py
- [x] Crear tests del firewall ontológico (56 tests)
- [x] Actualizar ARCHITECTURE.md
- [x] Actualizar README.md

## Fases Pendientes

### Fase 4: Migración de Base de Datos
- [ ] Migrar DB existente: 34 tipos no canónicos → 12 canónicos
- [ ] Resolver 158 relaciones con tipos no canónicos
- [ ] Decidir sobre aliases (estudia_concepto, etc.)
- [ ] Verificar integridad post-migración

### Fase 5: Calidad de Código
- [ ] Agregar type hints a todas las funciones públicas
- [ ] Eliminar dead code
- [ ] Pinar versiones en requirements.txt
- [ ] Configurar pytest para tests automatizados

### Fase 6: Frontend Mejorado
- [ ] Dividir render.js en graph.js + panel.js + filters.js
- [ ] Agregar manejo de errores en fetch
- [ ] Mejorar UX del panel de citas
- [ ] Responsive design

### Fase 7: Pipeline Mejorado
- [ ] Re-extracción de PDFs faltantes
- [ ] Mejorar manejo de errores en extractor.py
- [ ] Logging estructurado
- [ ] Configuración via archivo YAML/TOML

### Fase 8: Documentación
- [x] ARCHITECTURE.md
- [x] README.md
- [ ] Completar docstrings a todas las funciones
- [ ] Guía de contribución completa
- [ ] Ejemplos de uso

## Estadísticas

| Métrica | Fase 0 | Fase 1 | Fase 2 | Fase 3 |
|---------|--------|--------|--------|--------|
| Tipos de nodo | 8 | 8 | 8 | 8 |
| Relaciones canónicas | 9 | 9 | 9 | **12** |
| Tests | 0 | 33 | 33 | **89** |
| Validación ontológica | No | No | No | **Sí** |
| Firewall | No | No | No | **Sí** |
