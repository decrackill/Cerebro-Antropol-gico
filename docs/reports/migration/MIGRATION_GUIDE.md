# Guía de Migración Ontológica — Cerebro Antropológico

**Versión**: 1.0
**Fecha**: 2026-07-20
**Objetivo**: Migrar la base de datos existente al Manifiesto Ontológico v1.1
**Estado**: Prototipo validado, pendiente de aplicación al repositorio principal

---

## Resumen Ejecutivo

La base de datos actual contiene 371 relaciones con 34 tipos distintos.
El Manifiesto v1.1 define 12 tipos canónicos.
Esta guía documenta cómo migrar los 69 tipos no canónicos (18.6%) a los 12 canónicos.

| Métrica | Valor |
|---------|-------|
| Relaciones totales | 371 |
| Relaciones canónicas | 302 (81.4%) |
| Relaciones a migrar | 69 (18.6%) |
| Tipos no canónicos | 23 |
| Riesgo general | BAJO-MEDIO |

---

## Orden de Implementación

### 1. Preparación (sin cambios en DB)

**Archivos a crear:**
- `scripts/migrate_v1.1.py` — Script de migración parametrizado
- `tests/test_migration.py` — Tests de migración

**Archivos a modificar:**
- Ninguno (código ya actualizado)

**Verificaciones:**
```bash
# Ejecutar todos los tests
pytest tests/ -v

# Verificar que validar_relacion() funciona
python3 -c "from pipeline.core.db import validar_relacion; print('OK')"
```

### 2. Backup

```bash
# Crear backup
cp data/grafo.db data/grafo.db.backup_pre_v1.1

# Verificar backup
sqlite3 data/grafo.db.backup_pre_v1.1 "SELECT COUNT(*) FROM relaciones"
# Debe imprimir: 371
```

### 3. Migración Automática (23 relaciones, riesgo BAJO)

**Relaciones a migrar:**

| Tipo original | Frecuencia | Tipo destino | Invertir dirección |
|---------------|------------|--------------|-------------------|
| `escribió` | 6 | `autor_de` | No |
| `es_autor_de` | 1 | `autor_de` | No |
| `publica` | 1 | `autor_de` | No |
| `mentor_de` | 1 | `es_mentor_de` | No |
| `es_discípulo_de` | 2 | `es_mentor_de` | **Sí** |
| `colaboro_con` | 2 | `colabora_con` | No |
| `defiende_superioridad_de` | 2 | `critica_a` | No |
| `influyó_en` | 4 | `influenciado_por` | **Sí** |
| `influye_en` | 1 | `influenciado_por` | **Sí** |
| `influencio_a` | 1 | `influenciado_por` | **Sí** |
| `facilito_por` | 1 | `influenciado_por` | **Sí** |
| `condiciona` | 1 | `influenciado_por` | **Sí** |
| `refuta` | 2 | `critica_a` | No |
| `lucha_contra` | 1 | `critica_a` | No |
| `opuesto_a` | 1 | `critica_a` | No |
| `contrasta_con` | 2 | `critica_a` | No |
| `malinterpreta_a` | 2 | `critica_a` | No |
| `subestima_concepto` | 1 | `critica_a` | No |
| `manipula_concepto` | 1 | `critica_a` | No |
| `es_respuesta_a` | 1 | `critica_a` | No |

**Script SQL (ejemplo para `escribió` → `autor_de`):**
```sql
UPDATE relaciones SET tipo = 'autor_de' WHERE tipo = 'escribió';
```

**Script con inversión de dirección (ejemplo para `influyó_en` → `influenciado_por`):**
```sql
UPDATE relaciones 
SET origen_id = destino_id, destino_id = origen_id, tipo = 'influenciado_por' 
WHERE tipo = 'influyó_en';
```

### 4. Migración Semi-Automática (8 relaciones, riesgo MEDIO)

**Relaciones a migrar con verificación:**

| Tipo original | Frecuencia | Tipo destino | Nota |
|---------------|------------|--------------|------|
| `estudio` | 5 | `estudia_a` | Verificar que destino sea poblacion/cultura |
| `escribe_estudio_preliminar_para` | 1 | `estudia_a` | Verificar |
| `es_fuente_sobre` | 3 | `estudia_a` | Verificar |
| `cita_a` | 3 | `estudia_a` | Verificar |
| `realiza_trabajo_de_campo_en` | 2 | `estudia_a` | Verificar |
| `evalua_contribucion_de` | 1 | `estudia_a` | Verificar |
| `describe_a` | 7 | **REVISAR** | Puede ser `desarrolla_concepto` |

**Nota sobre `describe_a`:**
El Vault (FASE 05C) identificó que estas 7 relaciones contienen rankings raciales evaluativos (Morton). NO deben migrarse a `estudia_a` (que es neutra). Requieren decisión ontológica manual.

### 5. Migración Manual (38 relaciones, riesgo ALTO)

**Relaciones que requieren decisión caso por caso:**

| Tipo | Frecuencia | Riesgo | Nota |
|------|------------|--------|------|
| `clasifica_como_activo` | 11 | ALTO | Contenido racial evaluativo |
| `clasifica_como_pasivo` | 4 | ALTO | Contenido racial evaluativo |
| `contribuye_a` | 8 | MEDIO | Ambiguo: puede ser varios tipos |
| `representado_por` | 5 | MEDIO | Puede ser `desarrolla_concepto` |
| `presenta_rasgo` | 4 | ALTO | Contenido clasificatorio |
| `otorga_primacia_a` | 3 | ALTO | Ranking racial evaluativo |
| `desarrollada_por` | 2 | BAJO | Inversión de `desarrolla_concepto` |
| `afecta_a` | 2 | MEDIO | Puede ser `influenciado_por` |
| `venera_concepto` | 1 | ALTO | Carga valorativa |
| `usa_enfoque` | 1 | MEDIO | Puede ser varios tipos |
| `limita` | 1 | MEDIO | Puede ser `critica_a` |
| `limita_expansion_a` | 1 | MEDIO | Puede ser `critica_a` |
| `invadio` | 1 | BAJO | Error tipográfico probable |
| `descubierta_por` | 1 | BAJO | Inversión de `precursor_de` |
| `considera_indispensable` | 1 | ALTO | Carga valorativa |
| `aplicado_a` | 1 | MEDIO | Puede ser varios tipos |

### 6. Relaciones Nivel B (8 relaciones, riesgo BAJO)

| Tipo | Frecuencia | Acción |
|------|------------|--------|
| `relacionado_con` | 8 | Mantener como Nivel B o eliminar |

### 7. Verificación Post-Migración

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Verificar que no quedan tipos no canónicos
python3 -c "
import sqlite3
conn = sqlite3.connect('data/grafo.db')
tipos = [t[0] for t in conn.execute('SELECT DISTINCT tipo FROM relaciones').fetchall()]
canonicos = {'autor_de', 'influenciado_por', 'critica_a', 'desarrolla_concepto',
             'redefine_a', 'precursor_de', 'pertenece_a', 'estudia_a',
             'contemporaneo_de', 'parte_del_debate', 'es_mentor_de', 'colabora_con'}
no_canon = set(tipos) - canonicos
if no_canon:
    print(f'⚠ Tipos no canónicos restantes: {no_canon}')
else:
    print('✓ Todos los tipos son canónicos')
"

# Verificar firewall
python3 -c "
import sqlite3
conn = sqlite3.connect('data/grafo.db')
violaciones = conn.execute('''
    SELECT COUNT(*) FROM relaciones r
    JOIN nodos n1 ON r.origen_id = n1.id
    JOIN nodos n2 ON r.destino_id = n2.id
    WHERE n1.tipo = \"poblacion\" AND n2.tipo IN (\"cultura\", \"concepto\")
    AND r.tipo != \"parte_del_debate\"
''').fetchone()[0]
print(f'Violaciones firewall: {violaciones}')
"

# Verificar integridad referencial
python3 -c "
import sqlite3
conn = sqlite3.connect('data/grafo.db')
rotas = conn.execute('''
    SELECT COUNT(*) FROM relaciones r
    WHERE r.origen_id NOT IN (SELECT id FROM nodos)
       OR r.destino_id NOT IN (SELECT id FROM nodos)
''').fetchone()[0]
print(f'Relaciones rotas: {rotas}')
"
```

---

## Archivos que Deben Modificarse

| Archivo | Cambio | Estado |
|---------|--------|--------|
| `pipeline/core/config.py` | 12 tipos canónicos | ✅ Ya implementado |
| `pipeline/core/db.py` | `validar_relacion()` | ✅ Ya implementado |
| `pipeline/extract/prompts.py` | 12 tipos + firewall | ✅ Ya implementado |
| `pipeline/review/revision.py` | Validación en INSERT | ✅ Ya implementado |
| `pipeline/review/limpieza.py` | Validación en INSERT | ✅ Ya implementado |
| `scripts/init_db.py` | CHECK constraint 12 tipos | ✅ Ya implementado |
| `tests/conftest.py` | CHECK constraint 12 tipos | ✅ Ya implementado |
| `scripts/migrate_v1.1.py` | Script de migración | ⏳ Por crear |

## Archivos Nuevos que Deben Crearse

| Archivo | Propósito |
|---------|-----------|
| `scripts/migrate_v1.1.py` | Script de migración parametrizado |
| `tests/test_migration.py` | Tests de migración |

## Scripts que Deben Ejecutarse

```bash
# 1. Crear backup
cp data/grafo.db data/grafo.db.backup_pre_v1.1

# 2. Ejecutar migración
python3 scripts/migrate_v1.1.py

# 3. Verificar
pytest tests/ -v

# 4. Si todo OK, eliminar backup antiguo
# rm data/grafo.db.backup_pre_v1.1
```

---

## Incompatibilidades Conocidas

1. **DB existente**: La DB actual tiene 23 tipos no canónicos que serán migrados
2. **Scripts externos**: Cualquier script que lea tipos directamente de la DB verá los tipos cambiados
3. **Frontend**: El frontend no se ve afectado (lee tipos raw)
4. **Export JSON**: Los tipos en `datos.json` cambiarán después de la migración

---

## Riesgos Conocidos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Pérdida de datos | Baja | Crítico | Backup antes de migrar |
| Tipos incorrectos | Media | Alto | Verificación post-migración |
| Firewall roto | Baja | Crítico | Tests de firewall |
| Integridad referencial | Baja | Alto | Verificación post-migración |
| Decisión ontológica incorrecta | Media | Alto | Revisión manual de casos dudosos |

---

## Procedimiento de Rollback

### Si la migración falla:

```bash
# 1. Restaurar desde backup
cp data/grafo.db.backup_pre_v1.1 data/grafo.db

# 2. Verificar restauración
sqlite3 data/grafo.db "SELECT COUNT(*) FROM relaciones"
# Debe imprimir: 371

# 3. Ejecutar tests
pytest tests/ -v
```

### Si hay problemas post-migración:

```bash
# 1. Identificar el problema
python3 -c "from pipeline.core.db import validar_relacion; ..."

# 2. Restaurar desde backup si es necesario
cp data/grafo.db.backup_pre_v1.1 data/grafo.db

# 3. Revisar y corregir el script de migración
# 4. Re-ejecutar migración
```

---

## Pruebas que Deben Pasar

Antes de dar la migración por finalizada:

1. ✅ `pytest tests/ -v` — Todos los 89 tests deben pasar
2. ✅ `validar_relacion()` debe funcionar para todas las relaciones
3. ✅ No debe haber tipos no canónicos en la DB
4. ✅ No debe haber violaciones del firewall
5. ✅ No debe haber relaciones rotas (integridad referencial)
6. ✅ La exportación JSON debe funcionar correctamente

---

## Plantilla de Registro de Migración

```markdown
# Registro de Migración v1.1

**Fecha**: YYYY-MM-DD
**Ejecutado por**: [nombre]
**Resultado**: ÉXITO / FALLO

## Resumen
- Relaciones migradas: X
- Relaciones sin cambio: X
- Errores: X

## Detalle por tipo
[Tipo original] → [Tipo destino]: X relaciones

## Verificación
- Tests: X/X pasaron
- Firewall: X violaciones
- Integridad: X relaciones rotas

## Observaciones
[Notas adicionales]
```
