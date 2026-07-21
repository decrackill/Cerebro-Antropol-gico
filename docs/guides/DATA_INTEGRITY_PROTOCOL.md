# Protocolo de Integridad de Datos

**Fecha**: 2026-07-21
**Objetivo**: Proteger la base de datos durante campañas de extracción

---

## Reglas Fundamentales

1. **NUNCA** modificar la DB sin backup previo
2. **NUNCA** ejecutar limpieza sin backup previo
3. **NUNCA** eliminar nodos sin verificar que no tienen relaciones importantes
4. **SIEMPRE** crear backup antes de cada operación destructiva
5. **SIEMPRE** verificar el estado de la DB después de cada operación

---

## Cuándo Realizar Backups

| Momento | Obligatorio | Comando |
|---------|-------------|---------|
| Antes de cada extracción | **SÍ** | `cp data/grafo.db "data/grafo_backup_$(date +%Y%m%d_%H%M%S).db"` |
| Antes de revisión manual | Recomendado | Igual |
| Antes de conexión automática | **SÍ** | Igual |
| Antes de limpieza automática | **SÍ** | Igual |
| Antes de fusión de duplicados | **SÍ** | Igual |
| Antes de eliminación de nodos | **SÍ** | Igual |
| Después de cada libro completado | Recomendado | Igual |
| Al finalizar la jornada | Recomendado | Igual |

---

## Cuándo Crear Snapshots

Un snapshot es un backup completo del estado de la DB en un momento dado.

**Crear snapshot**:
- Al inicio de cada campaña de extracción
- Después de procesar cada lote de 5 libros
- Antes de ejecutar la migración v1.1 (si aún no se ejecutó)
- Después de completar una auditoría importante

**Comando**:
```bash
cp data/grafo.db "data/grafo_snapshot_$(date +%Y%m%d_%H%M%S).db"
```

---

## Cómo Nombrar Backups

### Formato

```
data/grafo_backup_YYYYMMDD_HHMMSS.db
```

### Ejemplos

```
data/grafo_backup_20260721_143022.db    # Backup antes de extracción
data/grafo_backup_20260721_150045.db    # Backup antes de limpieza
data/grafo_snapshot_20260721_180000.db  # Snapshot al final del día
```

### Convenciones

- `backup_*` — Backup antes de una operación
- `snapshot_*` — Snapshot del estado completo
- `pre_*` — Backup antes de una operación específica (opcional)
- `post_*` — Backup después de una operación específica (opcional)

---

## Cuándo Exportar Datos

Exportar datos después de:
- Cada libro completado
- Cada limpieza/deduplicación
- Cada auditoría importante
- Al final de cada jornada

**Comando**:
```bash
python3 scripts/export_json.py
```

---

## Cómo Volver al Último Estado Estable

### Paso 1: Identificar el último backup válido

```bash
ls -lt data/grafo_backup_*.db | head -5
```

### Paso 2: Restaurar desde el backup

```bash
cp data/grafo_backup_<timestamp>.db data/grafo.db
```

### Paso 3: Verificar restauración

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('data/grafo.db')
n = conn.execute('SELECT COUNT(*) FROM nodos').fetchone()[0]
r = conn.execute('SELECT COUNT(*) FROM relaciones').fetchone()[0]
print(f'Restaurado: {n} nodos, {r} relaciones')
conn.close()
"
```

### Paso 4: Re-exportar JSON

```bash
python3 scripts/export_json.py
```

---

## Cómo Detectar una Extracción Defectuosa

### Señales de Alerta

| Señale | Qué Significa | Acción |
|--------|---------------|--------|
| Miles de nodos nuevos de golpe | Extracción defectuosa o sobreextracción | Restaurar backup |
| Miles de relaciones nuevas | Posible alucinación del LLM | Restaurar backup |
| Nodos con nombres sin sentido | Respuesta inválida del LLM | Revisar y eliminar |
| Relaciones sin cita_textual | Falta de evidencia documental | Revisar y eliminar |
| Relaciones con tipos no canónicos | Tipos no normalizados | Ejecutar normalización |
| Errores en `validar_relacion()` | Violación de firewall o compatibilidad | Revisar cada caso |

### Proceso de Detección

```bash
# 1. Ejecutar auditoría
python3 -m pipeline.cli.menu
# Opción 4: Auditoría

# 2. Verificar estadísticas
python3 -c "
import sqlite3
conn = sqlite3.connect('data/grafo.db')
print('=== ESTADÍSTICAS ===')
print(f'Nodos: {conn.execute(\"SELECT COUNT(*) FROM nodos\").fetchone()[0]}')
print(f'Relaciones: {conn.execute(\"SELECT COUNT(*) FROM relaciones\").fetchone()[0]}')
print()
print('Tipos de nodo:')
for tipo, c in conn.execute('SELECT tipo, COUNT(*) FROM nodos GROUP BY tipo').fetchall():
    print(f'  {tipo}: {c}')
print()
print('Top tipos de relación:')
for tipo, c in conn.execute('SELECT tipo, COUNT(*) FROM relaciones GROUP BY tipo ORDER BY COUNT(*) DESC LIMIT 10').fetchall():
    print(f'  {tipo}: {c}')
conn.close()
"
```

---

## Qué Hacer si Aparecen Miles de Nodos Inesperados

### Escenario 1: Extracción generó miles de nodos

1. **No insertar** en la DB
2. Revisar `runtime/cache/candidatos_pendientes.json`
3. Si los nodos son basura → eliminar el archivo y reintentar
4. Si los nodos tienen sentido → revisar manualmente antes de insertar

### Escenario 2: Conexión automática insertó miles de nodos

1. **Restaurar backup** inmediatamente
2. Investigar qué salió mal
3. Reintentar con umbral de similitud más alto

### Escenario 3: Limpieza eliminó nodos importantes

1. **Restaurar backup**
2. Revisar qué nodos se eliminaron
3. Reintentar limpieza con más cuidado

---

## Qué Hacer si Aparecen Relaciones Inválidas

### Escenario 1: Relaciones con tipos no canónicos

```bash
# Identificar relaciones no canónicas
python3 -c "
import sqlite3
from pipeline.core.config import TIPOS_VALIDOS_RELACION
conn = sqlite3.connect('data/grafo.db')
for tipo, c in conn.execute('SELECT tipo, COUNT(*) FROM relaciones GROUP BY tipo').fetchall():
    if tipo not in TIPOS_VALIDOS_RELACION:
        print(f'  NO CANÓNICO: {tipo} ({c} relaciones)')
conn.close()
"
```

**Acción**: Ejecutar `migrate_relacion_types.py` o normalizar manualmente.

### Escenario 2: Relaciones sin evidencia

```bash
# Identificar relaciones sin fuente ni cita
python3 -c "
import sqlite3
conn = sqlite3.connect('data/grafo.db')
sin_evidencia = conn.execute('SELECT COUNT(*) FROM relaciones WHERE fuente IS NULL AND (cita_textual IS NULL OR citation_textual = \"\")').fetchone()[0]
print(f'Relaciones sin evidencia: {sin_evidencia}')
conn.close()
"
```

**Acción**: Revisar cada caso. Opcionalmente eliminar relaciones sin evidencia.

### Escenario 3: Relaciones con nodos inexistentes

```bash
# Identificar relaciones rotas
python3 -c "
import sqlite3
conn = sqlite3.connect('data/grafo.db')
ids_validos = {row[0] for row in conn.execute('SELECT id FROM nodos')}
rotas = 0
for rel_id, origen, destino in conn.execute('SELECT id, origen_id, destino_id FROM relaciones'):
    if origen not in ids_validos or destino not in ids_validos:
        rotas += 1
        print(f'  Relación rota id={rel_id}: {origen}→{destino}')
print(f'Total rotas: {rotas}')
conn.close()
"
```

**Acción**: Eliminar relaciones rotas o restaurar nodos faltantes.

---

## Qué Hacer si el Proceso se Interrumpe a Mitad de una Extracción

### El checkpoint preserva el progreso

El extractor guarda un checkpoint por cada chunk procesado.

### Para reanudar

```bash
# Simplemente ejecutar el extractor de nuevo
python3 -m pipeline.extract.extractor libros/<nombre>.pdf

# El extractor retomará desde el último chunk procesado
```

### Para reiniciar desde cero

```bash
# Eliminar checkpoint
rm runtime/state/checkpoint_<nombre>.json

# Re-ejecutar extractor
python3 -m pipeline.extract.extractor libros/<nombre>.pdf --reset
```

### Para recuperar resultados parciales

Los resultados parciales se guardan en `runtime/cache/candidatos_pendientes.json`.

```bash
# Verificar qué se extrajo
python3 -c "
import json
d = json.load(open('runtime/cache/candidatos_pendientes.json'))
print(f'Nodos acumulados: {len(d.get(\"nodos_nuevos\", []))}')
print(f'Relaciones acumuladas: {len(d.get(\"relaciones_nuevas\", []))}')
"
```

---

## Procedimiento de Recuperación

### Nivel 1: Error menor (nodos basura, relaciones inválidas)

1. Identificar el problema
2. Revisar manualmente
3. Eliminar o corregir elementos problemáticos
4. No restaurar backup

### Nivel 2: Error moderado (miles de nodos inesperados)

1. Restaurar backup previo
2. Investigar la causa
3. Reintentar con precaución

### Nivel 3: Error grave (DB corrupta, pérdida de datos)

1. Restaurar último backup válido
2. Verificar integridad
3. Re-exportar JSON
4. Documentar el incidente

---

## Monitoreo Continuo

### Durante la extracción

- Verificar que los chunks se procesan correctamente
- Monitorear el log de errores
- Verificar que el checkpoint avanza

### Después de la extracción

- Ejecutar auditoría
- Verificar estadísticas
- Comparar con el estado anterior

### Al final de la jornada

- Crear backup
- Exportar JSON
- Documentar métricas

---

## Mantenimiento de Backups

### Cuándo eliminar backups antiguos

- Mantener los últimos 10 backups
- Mantener snapshots de hitos importantes
- Eliminar backups diarios antiguos (>30 días)

### Cómo eliminar backups antiguos

```bash
# Listar backups por fecha
ls -lt data/grafo_backup_*.db

# Eliminar backups antiguos (ejemplo: mantener solo los últimos 10)
ls -t data/grafo_backup_*.db | tail -n +11 | xargs rm -f
```

---

## Checklist de Integridad

Antes de cada sesión de trabajo:

- [ ] Verificar que la DB existe y es accesible
- [ ] Verificar que hay al menos un backup reciente
- [ ] Ejecutar auditoría rápida

Después de cada sesión de trabajo:

- [ ] Crear backup
- [ ] Exportar JSON
- [ ] Documentar cambios realizados
