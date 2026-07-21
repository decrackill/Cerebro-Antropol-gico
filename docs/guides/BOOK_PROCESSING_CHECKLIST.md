# Checklist de Procesamiento de Libro

**Fecha**: 2026-07-21
**Versión del sistema**: v1.1

---

## Uso

Marcar cada paso con [x] cuando se complete.
Este checklist garantiza que un libro quedó completamente procesado.

---

## ANTES DE COMENZAR

### Preparación

- [ ] El PDF está en `libros/` y es legible
- [ ] El nombre del archivo es descriptivo (sin espacios especiales)
- [ ] Se verificó que PyMuPDF puede leer el PDF:
  ```bash
  python3 -c "import fitz; doc=fitz.open('libros/<nombre>.pdf'); print(f'{len(doc)} páginas'); doc.close()"
  ```
- [ ] Las API keys están configuradas en `pipeline/.env`
- [ ] Los tests pasan:
  ```bash
  python3 -m pytest --tb=short -q
  ```

### Respaldo

- [ ] Se creó backup de la DB:
  ```bash
  cp data/grafo.db "data/grafo_backup_$(date +%Y%m%d_%H%M%S).db"
  ```
- [ ] Se verificó que el backup es válido:
  ```bash
  python3 -c "import sqlite3; conn=sqlite3.connect('data/grafo_backup_*.db'); print(f'Backup: {conn.execute(\"SELECT COUNT(*) FROM nodos\").fetchone()[0]} nodos'); conn.close()"
  ```

### Estado Inicial

- [ ] Se registró el estado de la DB antes de comenzar:
  ```bash
  python3 -c "import sqlite3; conn=sqlite3.connect('data/grafo.db'); print(f'ANTES: {conn.execute(\"SELECT COUNT(*) FROM nodos\").fetchone()[0]} nodos, {conn.execute(\"SELECT COUNT(*) FROM relaciones\").fetchone()[0]} relaciones'); conn.close()"
  ```

---

## EXTRACCIÓN

### Extracción Automática

- [ ] Se ejecutó el extractor:
  ```bash
  python3 -m pipeline.extract.extractor libros/<nombre>.pdf
  ```
- [ ] La extracción completó sin errores fatales
- [ ] Se verificó que se creó `runtime/cache/candidatos_pendientes.json`

**O** extracción manual (si no hay API):

- [ ] Se generaron prompts para cada chunk:
  ```bash
  python3 -m pipeline.extract.modo_manual libros/<nombre>.pdf generar
  ```
- [ ] Se pegaron las respuestas JSON:
  ```bash
  python3 -m pipeline.extract.modo_manual libros/<nombre>.pdf pegar
  ```
- [ ] Se repitió hasta procesar todos los chunks

### Verificación Post-Extracción

- [ ] Los candidatos tienen sentido general (no basura)
- [ ] Hay al menos 1 nodo nuevo por cada 10 páginas
- [ ] Hay relaciones entre entidades (no solo nodos aislados)
- [ ] Los conceptos extraídos parecen términos reales
- [ ] Los autores extraídos tienen relevancia

---

## REVISIÓN

### Revisión Manual

- [ ] Se inició la revisión manual:
  ```bash
  python3 -m pipeline.cli.menu
  # Opción 1: Revisar candidatos
  ```
- [ ] Se revisaron TODOS los nodos candidatos
- [ ] Se revisaron TODAS las relaciones candidatas
- [ ] Se verificó que las citas textuales existen en el PDF
- [ ] Se verificó que los conceptos son realmente conceptos
- [ ] Se verificó que los autores tienen relevancia intelectual

**O** conexión automática (para libros de baja ambigüedad):

- [ ] Se ejecutó conexión automática primero en modo simulación
- [ ] Se verificaron los resultados de la simulación
- [ ] Se aplicó la conexión automática
- [ ] Se verificó que no se insertaron nodos basura

### Verificación de Inserción

- [ ] Se verificó que los nodos se insertaron:
  ```bash
  python3 -c "import sqlite3; conn=sqlite3.connect('data/grafo.db'); print(f'DESPUÉS: {conn.execute(\"SELECT COUNT(*) FROM nodos\").fetchone()[0]} nodos, {conn.execute(\"SELECT COUNT(*) FROM relaciones\").fetchone()[0]} relaciones'); conn.close()"
  ```
- [ ] El incremento de nodos es razonable (no miles)
- [ ] El incremento de relaciones es razonable (no miles)

---

## LIMPIEZA (Opcional pero Recomendada)

### Detección de Duplicados

- [ ] Se ejecutó detección de duplicados:
  ```bash
  python3 -m pipeline.cli.menu
  # Opción 6: Fusionar duplicados
  ```
- [ ] Se revisaron los pares sospechosos
- [ ] Se fusionaron los duplicados confirmados
- [ ] No se fusionaron pares que son entidades distintas

### Eliminación de Ruido (Opcional)

- [ ] Se verificó que no hay nodos biomédicos
- [ ] Se eliminaron nodos ruido si existían:
  ```bash
  # Menú → opción 9 (eliminación agresiva)
  ```

**Precaución**: Esta operación es irreversible. Solo ejecutar si se está seguro.

---

## AUDITORÍA

- [ ] Se ejecutó la auditoría completa:
  ```bash
  python3 -m pipeline.cli.menu
  # Opción 4: Auditoría
  ```
- [ ] No hay relaciones rotas
- [ ] No hay nodos con 0 relaciones (excepto los recién insertados que aún no se conectaron)
- [ ] La distribución de tipos es razonable
- [ ] No hay duplicados sospechosos

---

## EXPORTACIÓN

- [ ] Se exportó el JSON:
  ```bash
  python3 scripts/export_json.py
  ```
- [ ] Se verificó que el JSON es válido:
  ```bash
  python3 -c "import json; d=json.load(open('src/datos.json')); print(f'{len(d[\"nodos\"])} nodos, {len(d[\"relaciones\"])} relaciones')"
  ```
- [ ] El JSON contiene las nuevas entidades

---

## VERIFICACIÓN DEL FRONTEND

- [ ] Se ejecutó el build:
  ```bash
  npm run build
  ```
- [ ] El build completó sin errores
- [ ] Se inició el servidor de desarrollo:
  ```bash
  npm run dev
  ```
- [ ] Se verificó en el navegador:
  - [ ] El grafo se carga correctamente
  - [ ] Las nuevas entidades aparecen
  - [ ] Los filtros funcionan
  - [ ] La búsqueda encuentra las nuevas entidades
  - [ ] El panel de detalles muestra información correcta

---

## VERIFICACIÓN FINAL

### Integridad de Datos

- [ ] No hay relaciones con origen o destino inexistente
- [ ] No hay nodos duplicados con el mismo nombre y tipo
- [ ] Todas las relaciones tienen fuente o cita_textual
- [ ] Los tipos de relación son canónicos (o están en la lista de aliases)

### Consistencia

- [ ] El conteo de nodos en DB coincide con el JSON exportado
- [ ] El conteo de relaciones en DB coincide con el JSON exportado
- [ ] El frontend muestra la información correcta

### Documentación

- [ ] Se registraron las métricas de calidad (ver [QUALITY_METRICS.md](../operations/QUALITY_METRICS.md))
- [ ] Se anotaron problemas encontrados (si los hubo)
- [ ] Se creó backup final

---

## BACKUP FINAL

- [ ] Se creó backup después de completar el procesamiento:
  ```bash
  cp data/grafo.db "data/grafo_backup_$(date +%Y%m%d_%H%M%S).db"
  ```

---

## RESUMEN DEL PROCESAMIENTO

| Campo | Valor |
|-------|-------|
| Libro procesado | |
| Fecha de inicio | |
| Fecha de finalización | |
| Nodos antes | |
| Nodos después | |
| Relaciones antes | |
| Relaciones después | |
| Tiempo total | |
| Problemas encontrados | |
| Notas | |

---

## FIRMA

- [ ] Procesamiento completado exitosamente
- [ ] Todos los pasos verificados
- [ ] Backup final creado

**Responsable**: _________________ **Fecha**: ___________
