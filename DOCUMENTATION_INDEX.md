# Índice de Documentación — Cerebro Antropológico

**Última actualización**: 2026-07-21
**Autoridad máxima**: [docs/ontology/MANIFIESTO_ONTOLOGICO.md](docs/ontology/MANIFIESTO_ONTOLOGICO.md)

---

## Estructura del Proyecto

```
Cerebro-antropologico/
│
├── README.md                          # Guía de inicio
├── CONTRIBUTING.md                    # Guía de contribución
├── package.json                       # Dependencias JavaScript
├── requirements.txt                   # Dependencias Python
│
├── docs/                              # Toda la documentación
│   ├── ontology/                      # Documentación ontológica
│   ├── architecture/                  # Arquitectura técnica
│   ├── reports/                       # Reportes por área
│   ├── audits/                        # Auditorías realizadas
│   ├── certification/                 # Certificaciones
│   ├── historical/                    # Documentación histórica
│   └── generated/                     # Reportes generados automáticamente
│
├── pipeline/                          # Código Python
├── scripts/                           # Scripts de utilidad
├── tests/                             # Tests automatizados
├── src/                               # Frontend (JS/CSS)
├── data/                              # Base de datos SQLite
└── runtime/                           # Datos de ejecución
```

---

## Documentación Oficial

Estos documentos definen el proyecto y deben consultarse regularmente.

| Documento | Propósito | Ubicación |
|-----------|-----------|-----------|
| README.md | Guía de inicio para nuevos desarrolladores | Raíz |
| CONTRIBUTING.md | Convenciones de código y ontología | Raíz |
| MANIFIESTO_ONTOLOGICO.md | **Autoridad máxima** — Ontología formal v1.1 | docs/ontology/ |
| MANIFIESTO_CHANGELOG.md | Registro de evolución de la ontología | docs/ontology/ |
| ARCHITECTURE.md | Arquitectura técnica del sistema | docs/architecture/ |
| ROADMAP.md | Estado del proyecto y trabajo pendiente | docs/architecture/ |

---

## Documentación Técnica

### Ontología

| Documento | Propósito |
|-----------|-----------|
| MANIFIESTO_ONTOLOGICO.md | Definición formal de la ontología (8 nodos, 12 relaciones) |
| MANIFIESTO_CHANGELOG.md | Historial de cambios en la ontología |

### Arquitectura

| Documento | Propósito |
|-----------|-----------|
| ARCHITECTURE.md | Estructura del proyecto, pipeline, sistema de validación |
| ROADMAP.md | Fases completadas y pendientes |

---

## Reportes

### Migración

| Documento | Propósito |
|-----------|-----------|
| MIGRATION_GUIDE.md | Guía técnica para ejecutar la migración |
| MIGRATION_REPORT.md | Reporte de la migración ejecutada |
| PRE_MIGRATION_CHECKLIST.md | Checklist previo a la migración |

### Exportación

| Documento | Propósito |
|-----------|-----------|
| EXPORT_VALIDATION.md | Validación del proceso de exportación |
| EXPORT_REPORT.md | Reporte de la exportación ejecutada |

### Frontend

| Documento | Propósito |
|-----------|-----------|
| FRONTEND_VALIDATION.md | Validación funcional del frontend |

---

## Auditorías

| Documento | Propósito |
|-----------|-----------|
| COMPATIBILITY_REPORT.md | Auditoría de compatibilidad entre repositorios |
| PREPRODUCTION_REVIEW.md | Certificación preproducción del migrador |
| POST_MIGRATION_VALIDATION.md | Validación post-migración en entorno espejo |
| VALIDACION_MIGRACION.md | Análisis semántico de cada tipo de migración |
| INTEGRATION_PLAN.md | Plan de integración al repositorio principal |

---

## Certificaciones

| Documento | Propósito |
|-----------|-----------|
| READY_FOR_PRODUCTION.md | Estado del repositorio antes de la migración |
| PROJECT_CERTIFICATION.md | Certificación final del proyecto completo |

---

## Documentación Histórica

Estos documentos se conservan por trazabilidad pero no son activos.

| Documento | Propósito | Fecha |
|-----------|-----------|-------|
| cierre_migracion_ontologica.md | Cierre de la migración ontológica anterior | 2026-07-20 |
| estado_actual.md | Estado de la DB en momento de auditoría | 2026-07-20 |
| post_migration_report.md | Reporte post-migración anterior | 2026-07-20 |
| verificacion_migracion.md | Verificación de migración anterior | 2026-07-20 |
| relaciones_pendientes.md | Tipos no canónicos pendientes de decisión | 2026-07-20 |

---

## Reportes Generados

Estos documentos se generaron automáticamente durante la ejecución.

| Documento | Generado por |
|-----------|--------------|
| reporte_migracion_apply_*.md | migrate_v1_1.py --apply |
| reporte_migracion_dryrun_*.md | migrate_v1_1.py --dry-run |

---

## Orden Recomendado de Lectura

Para nuevos desarrolladores:

1. **README.md** — Visión general del proyecto
2. **docs/ontology/MANIFIESTO_ONTOLOGICO.md** — Ontología formal
3. **docs/architecture/ARCHITECTURE.md** — Arquitectura técnica
4. **CONTRIBUTING.md** — Convenciones de código
5. **docs/architecture/ROADMAP.md** — Estado del proyecto

Para entender la migración:

1. **docs/ontology/MANIFIESTO_ONTOLOGICO.md** — Ontología v1.1
2. **docs/reports/migration/MIGRATION_GUIDE.md** — Cómo se migró
3. **docs/audits/VALIDACION_MIGRACION.md** — Por qué se migró así

---

## Autoridad Máxima

El [MANIFIESTO_ONTOLOGICO.md](docs/ontology/MANIFIESTO_ONTOLOGICO.md) es la **única fuente de verdad** para:

- Tipos de nodo
- Tipos de relación
- Firewall epistemológico
- Reglas de validación

Cualquier cambio en el código debe ser consistente con el Manifiesto.
