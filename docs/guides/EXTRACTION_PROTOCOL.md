# Protocolo de Extracción — Cerebro Antropológico

**Versión**: 1.0
**Fecha**: 2026-07-21
**Sistema**: v1.1 (sin modificaciones)

---

## Estado Actual del Sistema

| Métrica | Valor |
|---------|-------|
| Nodos en DB | 394 |
| Relaciones en DB | 371 |
| Tipos de nodo | 6 de 8 |
| Tipos de relación | 29 (12 canónicos + 17 no canónicos) |
| Backups existentes | 2 (`grafo_backup_20260721_003616.db`, `grafo.db.bak`) |

---

## Flujo Completo de Procesamiento

```
1. PREPARACIÓN
   └→ Verificar PDF
   └→ Crear backup de DB
   └→ Verificar entorno

2. EXTRACCIÓN
   └→ python3 -m pipeline.extract.extractor <pdf>
   └→ O: python3 -m pipeline.extract.modo_manual <pdf> generar/pegar

3. REVISIÓN
   └→ python3 -m pipeline.cli.menu → opción 1 (manual)
   └→ O: python3 -m pipeline.cli.menu → opción 2 (automática)

4. LIMPIEZA (opcional)
   └→ python3 -m pipeline.cli.menu → opción 5 (limpieza automática)
   └→ O: python3 -m pipeline.cli.menu → opción 6 (fusionar duplicados)

5. AUDITORÍA
   └→ python3 -m pipeline.cli.menu → opción 4

6. EXPORTACIÓN
   └→ python3 scripts/export_json.py

7. VERIFICACIÓN
   └→ npm run build
   └→ npm run dev
```

---

## FASE A — Preparación del PDF

### A1. Ubicación del PDF

```bash
# Colocar el PDF en la carpeta libros/
cp /ruta/al/libro.pdf libros/
```

**Restricciones**:
- El PDF debe ser legible (no imagen escaneada sin OCR)
- Tamaño máximo recomendado: 500 páginas
- El nombre del archivo se usará como identificador

### A2. Verificación del PDF

```bash
# Verificar que el PDF existe
ls -la libros/<nombre>.pdf

# Verificar que PyMuPDF puede leerlo
python3 -c "import fitz; doc=fitz.open('libros/<nombre>.pdf'); print(f'{len(doc)} páginas'); doc.close()"
```

---

## FASE B — Respaldo de la Base de Datos

### B1. Backup Obligatorio

**ANTES de cada extracción**, crear un backup:

```bash
# Crear backup con timestamp
cp data/grafo.db "data/grafo_backup_$(date +%Y%m%d_%H%M%S).db"

# Verificar que el backup se creó
ls -la data/grafo_backup_*.db
```

### B2. Verificar Integridad del Backup

```bash
# Verificar que el backup es una DB válida
python3 -c "
import sqlite3
conn = sqlite3.connect('data/grafo_backup_$(date +%Y%m%d_%H%M%S).db')
n = conn.execute('SELECT COUNT(*) FROM nodos').fetchone()[0]
r = conn.execute('SELECT COUNT(*) FROM relaciones').fetchone()[0]
print(f'Backup válido: {n} nodos, {r} relaciones')
conn.close()
"
```

---

## FASE C — Verificación del Entorno

### C1. Dependencias Python

```bash
# Verificar que las dependencias están instaladas
pip3 list | grep -E "google-genai|openai|python-dotenv|PyMuPDF"
```

Salida esperada:
```
google-genai==2.12.1
openai==2.46.0
python-dotenv==1.2.2
PyMuPDF==1.27.2.3
```

### C2. API Keys

```bash
# Verificar que las API keys están configuradas
cat pipeline/.env | grep -E "^(GEMINI_API_KEY|OPENROUTER_API_KEY)"
```

**Mínimo requerido**: Al menos una API key configurada.

### C3. Tests

```bash
# Verificar que todos los tests pasan
python3 -m pytest --tb=short -q
```

Salida esperada: `107 passed`

---

## FASE D — Extracción

### D1. Extracción Automática (con API)

```bash
# Ejecutar extractor
python3 -m pipeline.extract.extractor libros/<nombre>.pdf

# Opción: limitar chunks para prueba
python3 -m pipeline.extract.extractor libros/<nombre>.pdf --max-chunks 3

# Opción: reiniciar desde cero
python3 -m pipeline.extract.extractor libros/<nombre>.pdf --reset
```

**Salida esperada**:
- Número de páginas extraídas
- Número de chunks
- Nodos y relaciones propuestos
- Checkpoint guardado

### D2. Extracción Manual (sin API)

```bash
# Paso 1: Generar prompt para el siguiente chunk
python3 -m pipeline.extract.modo_manual libros/<nombre>.pdf generar

# Paso 2: Copiar el prompt generado a un chat (ChatGPT/Claude/Gemini)
# Paso 3: Pegar la respuesta JSON en el terminal
python3 -m pipeline.extract.modo_manual libros/<nombre>.pdf pegar

# Repetir hasta procesar todos los chunks
```

### D3. Verificación Post-Extracción

```bash
# Verificar que se creó el archivo de candidatos
ls -la runtime/cache/candidatos_pendientes.json

# Verificar contenido (primeros 100 lines)
head -100 runtime/cache/candidatos_pendientes.json
```

---

## FASE E — Revisión

### E1. Revisión Manual (Recomendada para el primer libro)

```bash
# Iniciar menú
python3 -m pipeline.cli.menu

# Seleccionar opción 1: Revisar candidatos
# Seguir las instrucciones en pantalla:
# - Para cada nodo: s (aprobar) / n (rechazar) / editar
# - Para cada relación: s (aprobar) / n (rechazar)
```

**Puntos de atención**:
- Verificar que los conceptos son realmente conceptos
- Verificar que los autores tienen relevancia intelectual
- Verificar que las citas textuales existen en el PDF
- Los nodos con confianza "baja" requieren revisión cuidadosa

### E2. Conexión Automática (Para libros subsiguientes)

```bash
# Iniciar menú
python3 -m pipeline.cli.menu

# Seleccionar opción 2: Conexión automática
# Responder:
# - Umbral de similitud [0.80]
# - ¿Simular o aplicar? (recomendar: simular primero)
```

**Precaución**: La conexión automática inserta nodos sin revisión manual. Solo usar para libros donde se confía en la calidad de la extracción.

### E3. Verificación de Inserción

```bash
# Verificar que los nodos se insertaron
python3 -c "
import sqlite3
conn = sqlite3.connect('data/grafo.db')
n = conn.execute('SELECT COUNT(*) FROM nodos').fetchone()[0]
r = conn.execute('SELECT COUNT(*) FROM relaciones').fetchone()[0]
print(f'DB actual: {n} nodos, {r} relaciones')
conn.close()
"
```

---

## FASE F — Limpieza (Opcional)

### F1. Limpieza Automática

```bash
# Menú → opción 5
# Esto detecta y fusiona duplicados automáticamente
# Solo fusiona cuando un nodo tiene 0 relaciones
```

### F2. Fusión Manual de Duplicados

```bash
# Menú → opción 6
# Presenta pares sospechosos uno por uno
# Decisión: a (mantener a) / b (mantener b) / n (no fusionar)
```

### F3. Eliminación de Ruido

```bash
# Menú → opción 9 (eliminación agresiva)
# Elimina nodos aislados que coinciden con vocabulario biomédico
```

**Precaución**: Esta operación es irreversible. Crear backup antes.

---

## FASE G — Auditoría

### G1. Ejecutar Auditoría

```bash
# Menú → opción 4
```

**Salida esperada**:
- Progreso de revisión pendiente
- Estadísticas por tipo
- Integridad referencial
- Nodos aislados
- Cobertura de páginas por libro
- Duplicados sospechosos

### G2. Verificar Integridad

Verificar que:
- No hay relaciones rotas (apuntan a nodos inexistentes)
- No hay nodos con 0 relaciones (excepto los recién insertados)
- La distribución de tipos es razonable

---

## FASE H — Exportación

### H1. Exportar a JSON

```bash
python3 scripts/export_json.py
```

**Salida esperada**:
```
Exportado a src/datos.json
  394 nodos, 371 relaciones
```

### H2. Verificar JSON

```bash
# Verificar que el JSON es válido
python3 -c "import json; d=json.load(open('src/datos.json')); print(f'{len(d[\"nodos\"])} nodos, {len(d[\"relaciones\"])} relaciones')"
```

---

## FASE I — Verificación del Frontend

### I1. Build de Producción

```bash
npm run build
```

**Salida esperada**: `✓ built in X.XXs`

### I2. Desarrollo

```bash
npm run dev
```

Abrir `http://localhost:5173` y verificar:
- El grafo se carga correctamente
- Los filtros funcionan
- La búsqueda funciona
- El panel de detalles se muestra al hacer clic

---

## FASE J — Verificación Final

### J1. Checklist de Completitud

```bash
# Verificar que el libro está completamente procesado
echo "=== VERIFICACIÓN FINAL ==="

# 1. PDF existe
ls -la libros/<nombre>.pdf

# 2. Backup creado
ls -la data/grafo_backup_*.db | tail -1

# 3. Candidatos procesados
cat runtime/cache/candidatos_pendientes.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Nodos: {len(d.get(\"nodos_nuevos\",[]))}, Relaciones: {len(d.get(\"relaciones_nuevas\",[]))}')"

# 4. DB actualizada
python3 -c "import sqlite3; conn=sqlite3.connect('data/grafo.db'); print(f'DB: {conn.execute(\"SELECT COUNT(*) FROM nodos\").fetchone()[0]} nodos, {conn.execute(\"SELECT COUNT(*) FROM relaciones\").fetchone()[0]} relaciones'); conn.close()"

# 5. JSON exportado
python3 -c "import json; d=json.load(open('src/datos.json')); print(f'JSON: {len(d[\"nodos\"])} nodos, {len(d[\"relaciones\"])} relaciones')"

# 6. Build exitoso
npm run build 2>&1 | tail -1
```

---

## Momentos de Backup

| Momento | Obligatorio | Comando |
|---------|-------------|---------|
| Antes de cada extracción | **SÍ** | `cp data/grafo.db "data/grafo_backup_$(date +%Y%m%d_%H%M%S).db"` |
| Antes de revisión manual | Recomendado | Igual que arriba |
| Antes de limpieza automática | **SÍ** | Igual que arriba |
| Antes de fusión de duplicados | **SÍ** | Igual que arriba |
| Después de cada libro completado | Recomendado | Igual que arriba |

---

## Recuperación del Sistema

### Si la extracción genera resultados inesperados

```bash
# 1. Identificar el último backup válido
ls -lt data/grafo_backup_*.db

# 2. Restaurar desde el backup
cp data/grafo_backup_<timestamp>.db data/grafo.db

# 3. Verificar restauración
python3 -c "import sqlite3; conn=sqlite3.connect('data/grafo.db'); print(f'Restaurado: {conn.execute(\"SELECT COUNT(*) FROM nodos\").fetchone()[0]} nodos'); conn.close()"

# 4. Re-exportar JSON
python3 scripts/export_json.py
```

### Si la revisión manual inserta nodos incorrectos

```bash
# 1. Usar opción 15 del menú (Revisión total) para reclasificar
# 2. O usar opción 8 (Limpieza asistida) para eliminar nodos aislados
# 3. O restaurar desde backup
```

### Si el proceso se interrumpe a mitad de extracción

```bash
# El checkpoint preserva el progreso
# Reanudar con:
python3 -m pipeline.extract.extractor libros/<nombre>.pdf

# El extractor retomará desde el último chunk procesado
```

---

## Orden Recomendado para el Primer Libro

1. **Preparar PDF** (FASE A)
2. **Crear backup** (FASE B)
3. **Verificar entorno** (FASE C)
4. **Extraer con --max-chunks 3** (prueba rápida)
5. **Revisar candidatos manualmente** (FASE E1)
6. **Auditar** (FASE G)
7. **Si todo está bien, extraer completo**
8. **Revisar todos los candidatos**
9. **Limpiar** (opcional)
10. **Auditar de nuevo**
11. **Exportar** (FASE H)
12. **Verificar frontend** (FASE I)
13. **Crear backup final**
