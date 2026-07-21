# Informe de Compatibilidad — Repositorio Principal vs Entorno Certificado

**Fecha**: 2026-07-20
**Repositorio principal**: `/home/deivis/Cerebro-antropologico`
**Entorno certificado**: `/home/deivis/Escritorio/Manifiesto Ontologico/Cerebro-antropologico`
**Estado**: Análisis completado, sin modificaciones

---

## Resumen Ejecutivo

| Categoría | Compatible | Requiere Adaptación | Bloqueante |
|-----------|------------|---------------------|------------|
| Estructura de carpetas | ✅ | 0 | 0 |
| Pipeline | ⚠️ | 5 | 0 |
| Base de datos | ✅ | 0 | 0 |
| Documentación | ⚠️ | 6 | 0 |
| Tests | ⚠️ | 2 | 0 |
| Scripts | ⚠️ | 1 | 0 |
| **Total** | **1** | **14** | **0** |

**No hay bloqueantes.** Todos los cambios son compatibles y pueden aplicarse incrementalmente.

---

## 1. Estructura de Carpetas

| Elemento | Principal | Certificado | Estado |
|----------|-----------|-------------|--------|
| `pipeline/core/` | ✅ | ✅ | Compatible |
| `pipeline/extract/` | ✅ | ✅ | Compatible |
| `pipeline/review/` | ✅ | ✅ | Compatible |
| `pipeline/cli/` | ✅ | ✅ | Compatible |
| `scripts/` | ✅ | ✅ | Compatible |
| `tests/` | ✅ | ✅ | Compatible |
| `src/` | ✅ | ✅ | Compatible |
| `data/` | ✅ | ✅ | Compatible |
| `runtime/` | ✅ | ✅ | Compatible |
| `docs/` | ❌ | ✅ | **Requiere adaptación** |

**Conclusión**: La estructura base es idéntica. Solo falta la carpeta `docs/historico/`.

---

## 2. Pipeline

### 2.1. `pipeline/core/config.py`

| Elemento | Principal | Certificado | Estado |
|----------|-----------|-------------|--------|
| `TIPOS_VALIDOS_NODO` | 8 tipos | 8 tipos | ✅ Compatible |
| `TIPOS_VALIDOS_RELACION` | 9 tipos | **12 tipos** | ⚠️ Requiere adaptación |
| `TIPOS_ALIAS_RELACION` | Presente | Presente | ✅ Compatible |
| `COMPATIBILIDAD_RELACIONES` | **Ausente** | Presente | ⚠️ Requiere adaptación |

**Detalle de la diferencia**:
- **Principal**: `influenciado_por, critica_a, desarrolla_concepto, pertenece_a, estudia_a, contemporaneo_de, precursor_de, parte_del_debate, redefine_a`
- **Certificado**: + `autor_de`, `es_mentor_de`, `colabora_con`

### 2.2. `pipeline/core/db.py`

| Elemento | Principal | Certificado | Estado |
|----------|-----------|-------------|--------|
| `conectar_db()` | ✅ | ✅ | Compatible |
| `fusionar_nodos()` | ✅ | ✅ | Compatible |
| `eliminar_nodo_cascada()` | ✅ | ✅ | Compatible |
| `validar_relacion()` | **Ausente** | Presente | ⚠️ Requiere adaptación |
| `_validar_firewall_poblacion()` | **Ausente** | Presente | ⚠️ Requiere adaptación |
| `_validar_no_reflexividad()` | **Ausente** | Presente | ⚠️ Requiere adaptación |
| `_validar_compatibilidad_nodos()` | **Ausente** | Presente | ⚠️ Requiere adaptación |
| `_validar_evidencia()` | **Ausente** | Presente | ⚠️ Requiere adaptación |

### 2.3. `pipeline/extract/prompts.py`

| Elemento | Principal | Certificado | Estado |
|----------|-----------|-------------|--------|
| Lista de tipos válidos | 9 tipos | **12 tipos** | ⚠️ Requiere adaptación |
| Instrucción firewall | **Ausente** | Presente | ⚠️ Requiere adaptación |

### 2.4. `pipeline/review/revision.py`

| Elemento | Principal | Certificado | Estado |
|----------|-----------|-------------|--------|
| Import `validar_relacion` | **Ausente** | Presente | ⚠️ Requiere adaptación |
| Validación antes de INSERT | **Ausente** | Presente | ⚠️ Requiere adaptación |

### 2.5. `pipeline/review/limpieza.py`

| Elemento | Principal | Certificado | Estado |
|----------|-----------|-------------|--------|
| Import `validar_relacion` | **Ausente** | Presente | ⚠️ Requiere adaptación |
| Validación antes de INSERT | **Ausente** | Presente | ⚠️ Requiere adaptación |

---

## 3. Base de Datos

| Métrica | Principal | Certificado | Estado |
|---------|-----------|-------------|--------|
| Nodos | 394 | 394 | ✅ Idéntico |
| Relaciones | 371 | 371 | ✅ Idéntico |
| Tipos de nodo | 6 de 8 | 6 de 8 | ✅ Idéntico |
| Tipos de relación | 34 | 34 | ✅ Idéntico |

**Conclusión**: La base de datos es **idéntica**. No requiere cambios antes de la migración.

---

## 4. Documentación

| Archivo | Principal | Certificado | Estado |
|---------|-----------|-------------|--------|
| `MANIFIESTO_ONTOLOGICO.md` | **Ausente** | Presente (v1.1) | ⚠️ Requiere adaptación |
| `ARCHITECTURE.md` | 9 tipos | 12 tipos + firewall | ⚠️ Requiere adaptación |
| `README.md` | Sin mención Manifiesto | Con referencia | ⚠️ Requiere adaptación |
| `CONTRIBUTING.md` | Sin sección ontología | Con sección | ⚠️ Requiere adaptación |
| `ROADMAP.md` | Fase 2 | Fase 3 completada | ⚠️ Requiere adaptación |
| `MANIFIESTO_CHANGELOG.md` | Ausente | Presente | ⚠️ Requiere adaptación |
| `MIGRATION_GUIDE.md` | Ausente | Presente | ⚠️ Requiere adaptación |
| `POST_MIGRATION_VALIDATION.md` | Ausente | Presente | ⚠️ Requiere adaptación |
| `PREPRODUCTION_REVIEW.md` | Ausente | Presente | ⚠️ Requiere adaptación |

---

## 5. Tests

| Archivo | Principal | Certificado | Estado |
|---------|-----------|-------------|--------|
| `test_database.py` | ✅ | ✅ | Compatible |
| `test_extractor.py` | ✅ | ✅ | Compatible |
| `test_imports.py` | ✅ | ✅ | Compatible |
| `test_menu.py` | ✅ | ✅ | Compatible |
| `test_review.py` | ✅ | ✅ | Compatible |
| `test_firewall.py` | **Ausente** | 56 tests | ⚠️ Requiere adaptación |
| `test_migration.py` | **Ausente** | 18 tests | ⚠️ Requiere adaptación |
| `conftest.py` | 9 tipos | **12 tipos** | ⚠️ Requiere adaptación |

---

## 6. Scripts

| Archivo | Principal | Certificado | Estado |
|---------|-----------|-------------|--------|
| `init_db.py` | 9 tipos | **12 tipos** | ⚠️ Requiere adaptación |
| `export_json.py` | ✅ | ✅ | Compatible |
| `migrate_v1_1.py` | **Ausente** | Presente | ⚠️ Requiere adaptación |
| `migrate_relacion_types.py` | Presente | Presente | ✅ Compatible |

---

## 7. Archivos que Deben Incorporarse

### 7.1. Nuevos (no existen en principal)

| Archivo | Propósito | Prioridad |
|---------|-----------|-----------|
| `MANIFIESTO_ONTOLOGICO.md` | Fuente de verdad ontológica | **Crítica** |
| `tests/test_firewall.py` | Tests de validación ontológica | **Alta** |
| `tests/test_migration.py` | Tests del migrador | **Alta** |
| `scripts/migrate_v1_1.py` | Script de migración | **Alta** |
| `MANIFIESTO_CHANGELOG.md` | Evolución de la ontología | **Media** |
| `MIGRATION_GUIDE.md` | Guía de migración | **Media** |
| `POST_MIGRATION_VALIDATION.md` | Validación post-migración | **Media** |
| `PREPRODUCTION_REVIEW.md` | Certificación preproducción | **Media** |
| `docs/historico/README.md` | Índice de docs históricos | **Baja** |

### 7.2. Existentes que requieren actualización

| Archivo | Cambio Requerido | Prioridad |
|---------|------------------|-----------|
| `pipeline/core/config.py` | +3 tipos canónicos + COMPATIBILIDAD_RELACIONES | **Crítica** |
| `pipeline/core/db.py` | +validar_relacion() + validadores | **Crítica** |
| `pipeline/extract/prompts.py` | +3 tipos + firewall | **Crítica** |
| `pipeline/review/revision.py` | +validar_relacion() en INSERT | **Crítica** |
| `pipeline/review/limpieza.py` | +validar_relacion() en INSERT | **Crítica** |
| `scripts/init_db.py` | CHECK constraint 12 tipos | **Crítica** |
| `tests/conftest.py` | CHECK constraint 12 tipos | **Alta** |
| `ARCHITECTURE.md` | 12 tipos + firewall + validar_relacion | **Alta** |
| `README.md` | Referencia al Manifiesto | **Alta** |
| `CONTRIBUTING.md` | Sección ontología | **Media** |
| `ROADMAP.md` | Fase 3 completada | **Media** |

---

## 8. Orden de Implementación Recomendado

### Fase 1: Documentación normativa (sin dependencias)
1. Copiar `MANIFIESTO_ONTOLOGICO.md`
2. Copiar `MANIFIESTO_CHANGELOG.md`

### Fase 2: Núcleo ontológico (depende de Fase 1)
3. Actualizar `config.py` (+3 tipos + COMPATIBILIDAD_RELACIONES)
4. Actualizar `prompts.py` (+3 tipos + firewall)
5. Actualizar `init_db.py` (CHECK 12 tipos)
6. Actualizar `conftest.py` (CHECK 12 tipos)

### Fase 3: Validación ontológica (depende de Fase 2)
7. Actualizar `db.py` (+validar_relacion + validadores)
8. Actualizar `revision.py` (+validar_relacion)
9. Actualizar `limpieza.py` (+validar_relacion)

### Fase 4: Tests (depende de Fase 3)
10. Copiar `test_firewall.py`
11. Copiar `test_migration.py`

### Fase 5: Migración (depende de Fase 4)
12. Copiar `migrate_v1_1.py`
13. Ejecutar `--dry-run`
14. Ejecutar `--apply` (cuando se autorice)

### Fase 6: Documentación técnica (depende de Fase 5)
15. Actualizar `ARCHITECTURE.md`
16. Actualizar `README.md`
17. Actualizar `CONTRIBUTING.md`
18. Actualizar `ROADMAP.md`
19. Copiar `MIGRATION_GUIDE.md`
20. Copiar `POST_MIGRATION_VALIDATION.md`
21. Copiar `PREPRODUCTION_REVIEW.md`
22. Crear `docs/historico/`

---

## 9. Riesgos Identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| CHECK constraint rompe DB existente | Alta | Crítica | Script de migración antes de actualizar |
| Tests fallan por cambios en esquema | Media | Media | Actualizar conftest.py primero |
| Firewall bloquea relaciones válidas | Baja | Alta | Revisar lógica contra §5.3 del Manifiesto |

---

## 10. Conclusión

**El repositorio principal es compatible con el entorno certificado.**

No hay diferencias bloqueantes. Las 14 adaptaciones requeridas son:
- 5 en pipeline (config, db, prompts, revision, limpieza)
- 6 en documentación
- 2 en tests
- 1 en scripts

La base de datos es idéntica (394 nodos, 371 relaciones, 34 tipos).

**Recomendación**: Aplicar las adaptaciones en el orden especificado en la Fase 8.
