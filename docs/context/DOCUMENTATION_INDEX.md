# Índice de Documentación — Cerebro Antropológico

**Última actualización**: 2026-07-21
**Autoridad máxima**: [docs/ontology/MANIFIESTO_ONTOLOGICO.md](docs/ontology/MANIFIESTO_ONTOLOGICO.md)

---

## Qué leer primero

1. **README.md** — Visión general del proyecto
2. **docs/ontology/MANIFIESTO_ONTOLOGICO.md** — Ontología formal v1.1
3. **docs/architecture/ARCHITECTURE.md** — Arquitectura técnica
4. **CONTRIBUTING.md** — Convenciones de código

---

## Documentación Normativa

| Documento | Propósito |
|-----------|-----------|
| [MANIFIESTO_ONTOLOGICO.md](docs/ontology/MANIFIESTO_ONTOLOGICO.md) | **Autoridad máxima** — Ontología formal |
| [MANIFIESTO_CHANGELOG.md](docs/ontology/MANIFIESTO_CHANGELOG.md) | Registro de evolución de la ontología |

---

## Documentación Técnica

| Documento | Propósito |
|-----------|-----------|
| [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | Estructura del proyecto, pipeline, validación |
| [ROADMAP.md](docs/architecture/ROADMAP.md) | Fases completadas y pendientes |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Convenciones de código y ontología |

---

## Guías

| Documento | Propósito |
|-----------|-----------|
| [MIGRATION_GUIDE.md](docs/reports/migration/MIGRATION_GUIDE.md) | Cómo ejecutar la migración ontológica |
| [EXTRACTION_PROTOCOL.md](docs/guides/EXTRACTION_PROTOCOL.md) | Procedimiento completo de extracción |
| [BOOK_PROCESSING_CHECKLIST.md](docs/guides/BOOK_PROCESSING_CHECKLIST.md) | Checklist de verificación por libro |
| [DATA_INTEGRITY_PROTOCOL.md](docs/guides/DATA_INTEGRITY_PROTOCOL.md) | Protección de la base de datos |

---

## Operaciones

| Documento | Propósito |
|-----------|-----------|
| [QUALITY_METRICS.md](docs/operations/QUALITY_METRICS.md) | Definición de métricas de calidad |
| [KNOWN_OPERATIONAL_RISKS.md](docs/operations/KNOWN_OPERATIONAL_RISKS.md) | Riesgos y procedimientos de recuperación |
| [EXTRACTION_EXPERIMENT_PLAN.md](docs/operations/EXTRACTION_EXPERIMENT_PLAN.md) | Validación de hipótesis H1-H6 |

---

## Reportes Activos

| Documento | Propósito |
|-----------|-----------|
| [EXPORT_VALIDATION.md](docs/reports/export/EXPORT_VALIDATION.md) | Validación del proceso de exportación |
| [FRONTEND_VALIDATION.md](docs/reports/frontend/FRONTEND_VALIDATION.md) | Validación funcional del frontend |
| [EXTRACTION_SYSTEM_AUDIT.md](docs/reports/EXTRACTION_SYSTEM_AUDIT.md) | Auditoría del sistema de extracción |
| [EXTRACTION_ROADMAP.md](docs/reports/EXTRACTION_ROADMAP.md) | Roadmap de evolución v1.2/v1.3/v2.0 |

---

## Documentación Histórica

Estos documentos se conservan por trazabilidad pero no son activos.

| Documento | Propósito |
|-----------|-----------|
| [COMPATIBILITY_REPORT.md](docs/reports/historical/COMPATIBILITY_REPORT.md) | Auditoría de compatibilidad entre repositorios |
| [INTEGRATION_PLAN.md](docs/reports/historical/INTEGRATION_PLAN.md) | Plan de integración al repositorio principal |
| [POST_MIGRATION_VALIDATION.md](docs/reports/historical/POST_MIGRATION_VALIDATION.md) | Validación post-migración en entorno espejo |
| [PREPRODUCTION_REVIEW.md](docs/reports/historical/PREPRODUCTION_REVIEW.md) | Certificación preproducción del migrador |
| [VALIDACION_MIGRACION.md](docs/reports/historical/VALIDACION_MIGRACION.md) | Análisis semántico de cada tipo de migración |
| [PROJECT_CERTIFICATION.md](docs/reports/historical/PROJECT_CERTIFICATION.md) | Certificación final del proyecto |
| [READY_FOR_PRODUCTION.md](docs/reports/historical/READY_FOR_PRODUCTION.md) | Estado del repositorio pre-migración |
| [REPOSITORY_ORGANIZATION_REPORT.md](docs/reports/historical/REPOSITORY_ORGANIZATION_REPORT.md) | Reporte de organización previo |
| [PRE_MIGRATION_CHECKLIST.md](docs/reports/historical/PRE_MIGRATION_CHECKLIST.md) | Checklist previo a la migración |
| [MIGRATION_REPORT.md](docs/reports/historical/MIGRATION_REPORT.md) | Reporte de la migración ejecutada |
| [EXPORT_REPORT.md](docs/reports/historical/EXPORT_REPORT.md) | Reporte de la exportación ejecutada |
| [PROJECT_MAINTAINABILITY_REVIEW.md](docs/reports/historical/PROJECT_MAINTAINABILITY_REVIEW.md) | Revisión de mantenibilidad |
| [REPOSITORY_SIMPLIFICATION_PLAN.md](docs/reports/historical/REPOSITORY_SIMPLIFICATION_PLAN.md) | Plan de simplificación del repositorio |

---

## Autoridad Máxima

El [MANIFIESTO_ONTOLOGICO.md](docs/ontology/MANIFIESTO_ONTOLOGICO.md) es la **única fuente de verdad** para:

- Tipos de nodo
- Tipos de relación
- Firewall epistemológico
- Reglas de validación

Cualquier cambio en el código debe ser consistente con el Manifiesto.
