# Plan de Integración — Repositorio Principal

**Fecha**: 2026-07-20
**Repositorio**: `/home/deivis/Cerebro-antropologico`
**Entorno certificado**: `/home/deivis/Escritorio/Manifiesto Ontologico/Cerebro-antropologico`

---

## Archivos Nuevos

| # | Archivo | Propósito | Prioridad | Justificación |
|---|---------|-----------|-----------|---------------|
| 1 | `MANIFIESTO_ONTOLOGICO.md` | Fuente de verdad ontológica v1.1 | Crítica | Define la ontología que el código debe implementar |
| 2 | `MANIFIESTO_CHANGELOG.md` | Registro de evolución de la ontología | Media | Trazabilidad de cambios futuros |
| 3 | `tests/test_firewall.py` | 56 tests de validación ontológica | Alta | Verifica firewall, compatibilidad, invariantes |
| 4 | `tests/test_migration.py` | 18 tests del migrador | Alta | Verifica idempotencia, dry-run, apply |
| 5 | `scripts/migrate_v1_1.py` | Script de migración seguro | Alta | Migración de tipos no canónicos |
| 6 | `MIGRATION_GUIDE.md` | Guía técnica de migración | Media | Documentación para futuras ejecuciones |
| 7 | `POST_MIGRATION_VALIDATION.md` | Validación post-migración | Media | Evidencia de que la migración funciona |
| 8 | `PREPRODUCTION_REVIEW.md` | Certificación preproducción | Media | Auditoría completa del migrador |
| 9 | `VALIDACION_MIGRACION.md` | Análisis semántico de cada tipo | Media | Justificación de cada migración |

---

## Archivos Modificados

| # | Archivo | Cambio | Líneas Afectadas | Riesgo |
|---|---------|--------|------------------|--------|
| 1 | `pipeline/core/config.py` | +3 tipos canónicos | 43-45 | Bajo |
| 2 | `pipeline/core/db.py` | +import, +validar_relacion, +COMPATIBILIDAD_RELACIONES, +5 validadores | 8, 139+ | Bajo |
| 3 | `pipeline/extract/prompts.py` | +3 tipos, +instrucción firewall | 23-30 | Bajo |
| 4 | `pipeline/review/revision.py` | +import, +validar_relacion en 2 INSERT | 15, 213-224, 307-334 | Bajo |
| 5 | `pipeline/review/limpieza.py` | +import, +validar_relacion en 1 INSERT | 16, 283, 298-321 | Bajo |
| 6 | `scripts/init_db.py` | CHECK constraint 9→12 tipos | 32-34 | Medio |
| 7 | `tests/conftest.py` | CHECK constraint 9→12 tipos | 44-46 | Bajo |
| 8 | `ARCHITECTURE.md` | 12 tipos, firewall, validar_relacion | Reescritura | Bajo |
| 9 | `README.md` | Referencia al Manifiesto | Reescritura | Bajo |
| 10 | `CONTRIBUTING.md` | Sección ontología | Agregar sección | Bajo |
| 11 | `ROADMAP.md` | Fase 3 completada | Reescritura | Bajo |

---

## Dependencias entre Cambios

```
1. MANIFIESTO_ONTOLOGICO.md (sin dependencias)
   ↓
2. config.py (+3 tipos)
   ↓
3. prompts.py (+3 tipos + firewall)
   ↓
4. init_db.py (CHECK 12)
5. conftest.py (CHECK 12)
   ↓
6. db.py (+validar_relacion)
   ↓
7. revision.py (+validar_relacion)
8. limpieza.py (+validar_relacion)
   ↓
9. test_firewall.py
10. test_migration.py
   ↓
11. migrate_v1_1.py
   ↓
12. Documentación (ARCHITECTURE, README, CONTRIBUTING, ROADMAP)
```

---

## Riesgos Identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| CHECK constraint rompe DB existente | Media | Crítica | Migrar CHECK después de config.py |
| Tests fallan por cambios en esquema | Media | Media | Actualizar conftest.py primero |
| Firewall bloquea relaciones válidas | Baja | Alta | Verificar contra §5.3 del Manifiesto |
| Imports rotos | Baja | Media | Verificar después de cada cambio |

---

## Diferencias Detectadas

### Diferencia 1: config.py — Tipos de relación

**Principal**: 9 tipos
**Certificado**: 12 tipos (+autor_de, es_mentor_de, colabora_con)

**Estrategia**: Agregar los 3 tipos faltantes al conjunto existente. No sobrescribir.

### Diferencia 2: db.py — Funciones de validación

**Principal**: Solo CRUD básico
**Certificado**: +validar_relacion +5 validadores +COMPATIBILIDAD_RELACIONES

**Estrategia**: Agregar las nuevas funciones al final del archivo. No modificar las existentes.

### Diferencia 3: prompts.py — Firewall

**Principal**: Sin instrucciones de firewall
**Certificado**: Con instrucciones de firewall

**Estrategia**: Agregar bloque de firewall después de la lista de tipos.

### Diferencia 4: revision.py/limpieza.py — Validación

**Principal**: INSERT sin validación
**Certificado**: INSERT con validar_relacion()

**Estrategia**: Modificar los puntos de INSERT para incluir validación.

---

## Archivos Candidatos a Archivarse

| Archivo | Razón | Recomendación |
|---------|-------|---------------|
| `cierre_migracion_ontologica.md` | Referencia histórica | Archivar en docs/historico/ |
| `estado_actual.md` | Obsoleto post-migración | Archivar en docs/historico/ |
| `post_migration_report.md` | Referencia histórica | Archivar en docs/historico/ |
| `verificacion_migracion.md` | Referencia histórica | Archivar en docs/historico/ |

**Nota**: No se eliminan, solo se marcan para archivado futuro.
