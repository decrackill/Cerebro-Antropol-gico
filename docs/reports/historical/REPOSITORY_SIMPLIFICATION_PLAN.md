# Plan de Simplificación del Repositorio

**Fecha**: 2026-07-21
**Estado**: Plan de ejecución

---

## Análisis Actual

### Documentación: 27 archivos markdown en docs/ + 3 en raíz

**Problemas detectados:**

1. **`docs/audits/`** (5 archivos) — Todos describen la MIGMA MISMA migración v1.1 desde distintos ángulos. Son 1,200+ líneas de contenido altamente solapado.
2. **`docs/certification/`** (3 archivos) — `READY_FOR_PRODUCTION.md` y `PROJECT_CERTIFICATION.md` se superponen enormemente. `REPOSITORY_ORGANIZATION_REPORT.md` ya no refleja la realidad.
3. **`docs/reports/migration/`** (3 archivos) — `MIGRATION_GUIDE.md` (319 líneas), `MIGRATION_REPORT.md` (182), `PRE_MIGRATION_CHECKLIST.md` (263) cubren el mismo proceso.
4. **`docs/reports/export/`** (2 archivos) — `EXPORT_REPORT.md` y `EXPORT_VALIDATION.md` se superponen.
5. **`docs/generated/migration/`** (2 archivos) — Reportes temporales de una ejecución puntual.

### Scripts: 7 archivos en scripts/

**Clasificación:**

| Script | Clasificación | Acción |
|--------|--------------|--------|
| `init_db.py` | **Permanente** | Conservar |
| `export_json.py` | **Permanente** | Conservar |
| `migrate_v1_1.py` | **Migración** | Conservar (aún relevante) |
| `migrate_relacion_types.py` | **Migración** | Archivar (suplantado por migrate_v1_1) |
| `migrate_add_cita_textual.py` | **Migración** | Archivar (ya ejecutado) |
| `backfill_cita_textual.py` | **Migración** | Archivar (ya ejecutado) |
| `test_cita_textual.py` | **Prueba** | Archivar (prueba de una migración puntual) |

### Pipeline: Estructura correcta

- `pipeline/cerebro.py` — Wrapper de compatibilidad. Considerar si es necesario.
- `pipeline/check_models.py` — Script de diagnóstico. Mover a scripts/.
- `pipeline/verificar_extraccion.py` — Script de verificación. Mover a scripts/.
- `pipeline/extract/modo_manual.py` — Parte legítima del pipeline.

---

## Plan de Acción

### 1. Consolidar `docs/audits/` → `docs/reports/historical/`

Los 5 archivos de auditoría son históricos (la migración ya se ejecutó). Mover todos a `docs/reports/historical/`.

### 2. Consolidar `docs/certification/` → `docs/reports/historical/`

Los 3 archivos de certificación son históricos. Mover todos a `docs/reports/historical/`.

### 3. Consolidar `docs/reports/migration/` → 2 archivos

- `MIGRATION_GUIDE.md` → **Conservar** (guía reutilizable)
- `MIGRATION_REPORT.md` → **Fusionar en** MIGRATION_GUIDE.md (agregar sección "Ejecución")
- `PRE_MIGRATION_CHECKLIST.md` → **Mover a** `docs/reports/historical/`

### 4. Consolidar `docs/reports/export/` → 1 archivo

- `EXPORT_REPORT.md` + `EXPORT_VALIDATION.md` → **Fusionar en** `EXPORT_VALIDATION.md`

### 5. Mover `docs/generated/` → `docs/reports/historical/`

Reportes temporales de una ejecución puntual.

### 6. Archivar scripts en `scripts/archive/`

Mover scripts de migración ya completados y scripts de prueba.

### 7. Mover scripts de pipeline a `scripts/`

- `pipeline/check_models.py` → `scripts/check_models.py`
- `pipeline/verificar_extraccion.py` → `scripts/verificar_extraccion.py`
- `pipeline/cerebro.py` → Eliminar (wrapper obsoleto)

### 8. Actualizar DOCUMENTATION_INDEX.md

Reflejar la nueva estructura.

### 9. Actualizar README.md

Enlazar solo documentación relevante.

---

## Estructura Final Deseada

```
docs/
├── ontology/               # Autoridad máxima
│   ├── MANIFIESTO_ONTOLOGICO.md
│   └── MANIFIESTO_CHANGELOG.md
│
├── architecture/           # Arquitectura técnica
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
│
├── guides/                 # Guías de uso
│   ├── CONTRIBUTING.md     (referencia a raíz)
│   └── MIGRATION_GUIDE.md
│
└── reports/                # Reportes
    ├── migration/
    │   └── MIGRATION_GUIDE.md (consolidado)
    ├── export/
    │   └── EXPORT_VALIDATION.md (consolidado)
    ├── frontend/
    │   └── FRONTEND_VALIDATION.md
    └── historical/         # Todo lo histórico
        ├── COMPATIBILITY_REPORT.md
        ├── INTEGRATION_PLAN.md
        ├── POST_MIGRATION_VALIDATION.md
        ├── PREPRODUCTION_REVIEW.md
        ├── VALIDACION_MIGRACION.md
        ├── PROJECT_CERTIFICATION.md
        ├── READY_FOR_PRODUCTION.md
        ├── REPOSITORY_ORGANIZATION_REPORT.md
        ├── PRE_MIGRATION_CHECKLIST.md
        ├── MIGRATION_REPORT.md
        ├── EXPORT_REPORT.md
        ├── reporte_migracion_*.md
        ├── cierre_migracion_ontologica.md
        ├── estado_actual.md
        ├── post_migration_report.md
        ├── verificacion_migracion.md
        └── relaciones_pendientes.md

scripts/
├── init_db.py             # Permanente
├── export_json.py         # Permanente
├── migrate_v1_1.py        # Permanente
├── check_models.py        # Diagnóstico
├── verificar_extraccion.py # Verificación
└── archive/               # Scripts completados
    ├── backfill_cita_textual.py
    ├── migrate_add_cita_textual.py
    ├── migrate_relacion_types.py
    └── test_cita_textual.py
```

---

## Conservar / Archivar / Eliminar

### Conservar (documentación activa)
- README.md
- CONTRIBUTING.md
- DOCUMENTATION_INDEX.md
- docs/ontology/MANIFIESTO_ONTOLOGICO.md
- docs/ontology/MANIFIESTO_CHANGELOG.md
- docs/architecture/ARCHITECTURE.md
- docs/architecture/ROADMAP.md

### Conservar (reportes útiles)
- docs/reports/migration/MIGRATION_GUIDE.md (consolidado)
- docs/reports/export/EXPORT_VALIDATION.md (consolidado)
- docs/reports/frontend/FRONTEND_VALIDATION.md

### Archivar en docs/reports/historical/
- 5 archivos de audits/
- 3 archivos de certification/
- 2 archivos de generated/
- 1 archivo de reports/migration/ (PRE_MIGRATION_CHECKLIST)
- 1 archivo de reports/migration/ (MIGRATION_REPORT → fusionar)
- 1 archivo de reports/export/ (EXPORT_REPORT → fusionar)
- 5 archivos históricos existentes

### Eliminar
- pipeline/cerebro.py (wrapper obsoleto)
