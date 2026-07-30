# Guía Completa de Uso — Cerebro Antropológico

Guía paso a paso para utilizar el sistema de extracción de conocimiento y visualización en grafo.

---

## ¿Qué es este proyecto?

Un sistema que toma PDFs académicos de antropología, extrae entidades (autores, obras, conceptos, culturas, etc.) y sus relaciones usando inteligencia artificial, las almacena en una base de datos, y las visualiza como un grafo interactivo en el navegador.

---

## Requisitos

- Python 3.12+
- Node.js 18+
- Una API key de Google Gemini **o** OpenRouter

---

## Instalación

```bash
# Clonar
git clone https://github.com/decrackill/Cerebro-Antropol-gico.git
cd Cerebro-Antropol-gico

# Dependencias Python
pip install -r requirements.txt

# Dependencias JavaScript
npm install

# Configurar API keys
cp pipeline/.env.example pipeline/.env
# Editar pipeline/.env con tu API key

# Visualizar el frontend
npm run dev
```

---

## El Flujo Completo

```
1. Colocar PDF en libros/
2. Extraer entidades con IA
3. Revisar candidatos
4. Limpiar duplicados
5. Auditar la base de datos
6. Exportar a JSON
7. Visualizar en el navegador
```

---

## Paso 1: Preparar el PDF

### Ubicación

Colocar el archivo PDF en la carpeta `libros/`:

```bash
cp /ruta/a/mi_libro.pdf libros/
```

### Formato Requerido

El PDF debe cumplir estas condiciones:

| Requisito | Detalle |
|-----------|---------|
| **Texto seleccionable** | Debe poder copiar texto del PDF. No sirven PDFs escaneados sin OCR |
| **Idioma** | Español preferentemente. El prompt está optimizado para textos académicos en español |
| **Tamaño máximo** | Recomendado: hasta 500 páginas. Funciona con más, pero tarda más |
| **Nombre del archivo** | Sin espacios ni caracteres especiales. Usar guiones bajos o guiones |
| **Contenido** | Texto académico de antropología: libros, artículos, tesis |

### Verificar que el PDF es legible

```bash
python3 -c "import fitz; doc=fitz.open('libros/mi_libro.pdf'); print(f'{len(doc)} páginas'); doc.close()"
```

Si este comando falla, el PDF no es legible para el sistema.

---

## Paso 2: Extraer Entidades con IA

### Opción A: Extracción Automática (Recomendada)

Requiere una API key configurada en `pipeline/.env`.

```bash
python3 -m pipeline.extract.extractor libros/mi_libro.pdf
```

**Opciones adicionales:**

```bash
# Procesar solo los primeros 3 chunks (para probar)
python3 -m pipeline.extract.extractor libros/mi_libro.pdf --max-chunks 3

# Reiniciar desde cero (borrar progreso anterior)
python3 -m pipeline.extract.extractor libros/mi_libro.pdf --reset
```

**Qué hace:**
1. Lee el PDF y lo divide en fragmentos de ~40,000 caracteres
2. Envía cada fragmento a la IA (Gemini u OpenRouter)
3. La IA extrae autores, obras, conceptos, culturas y sus relaciones
4. Guarda los candidatos en `runtime/cache/candidatos_pendientes.json`
5. Guarda un checkpoint para poder reanudar si se interrumpe

**Rotación de API keys:**
Si configuras múltiples keys (GEMINI_API_KEY, GEMINI_API_KEY_2, etc.), el sistema rota automáticamente cuando una se queda sin cuota.

### Opción B: Extracción Manual (Sin API)

Para cuando no tienes API key o se agotaron los tokens:

```bash
# Paso 1: Generar el prompt para el siguiente chunk
python3 -m pipeline.extract.modo_manual libros/mi_libro.pdf generar

# Paso 2: Copiar el prompt generado a un chat (ChatGPT, Claude, Gemini)
# Abrir el archivo prompt_manual_chunk_1.txt y copiar todo su contenido

# Paso 3: Pegar la respuesta JSON en el terminal
python3 -m pipeline.extract.modo_manual libros/mi_libro.pdf pegar
```

Repetir hasta procesar todos los chunks.

---

## Paso 3: Revisar Candidatos

Después de la extracción, los candidatos necesitan revisión humana antes de insertarse en la base de datos.

### Abrir el Menú Principal

```bash
python3 -m pipeline.cli.menu
```

### Revisión Manual (Opción 1)

La opción más segura. Revisa cada candidato uno por uno:

```
Opción: 1
```

**Para cada nodo la IA pregunta:**
- `s` — Aprobar e insertar
- `n` — Rechazar
- `editar` — Cambiar nombre, descripción o tipo antes de insertar

**Para cada relación la IA pregunta:**
- `s` — Aprobar e insertar
- `n` — Rechazar

**Consejos durante la revisión:**
- Verificar que los conceptos son realmente conceptos antropológicos
- Verificar que los autores tienen relevancia intelectual (no solo menciones de paso)
- Verificar que las citas textuales existen en el PDF
- Los nodos con confianza "baja" requieren revisión cuidadosa

### Conexión Automática (Opción 2)

Para libros donde confías en la calidad de la extracción:

```
Opción: 2
```

**Primero simular:**
```
¿Simular o aplicar? simular
```

Revisar los resultados de la simulación antes de aplicar de verdad.

---

## Paso 4: Limpiar y Deduplicar

### Detección de Duplicados (Opción 6)

```
Opción: 6
```

Presenta pares de nodos sospechosos de ser el mismo:
- `a` — Mantener el nodo A
- `b` — Mantener el nodo B
- `n` — No fusionar

### Limpieza Automática (Opción 5)

Fusión segura de duplicados + eliminación de ruido biomédico:

```
Opción: 5
```

**Primero simular** antes de aplicar.

### Eliminación de Ruido (Opción 9)

Elimina nodos aislados que coinciden con vocabulario médico/biológico:

```
Opción: 9
```

**Precaución:** Esta operación es irreversible. Crear backup antes.

---

## Paso 5: Auditar

```
Opción: 4
```

Muestra:
- Estadísticas por tipo de nodo y relación
- Integridad referencial (relaciones rotas)
- Nodos aislados
- Duplicados sospechosos
- Cobertura de páginas por libro

---

## Paso 6: Exportar a JSON

```
Opción: 11
```

O directamente:

```bash
python3 scripts/export_json.py
```

Esto genera `src/datos.json` que el frontend consume.

---

## Paso 7: Visualizar en el Navegador

```bash
# Desarrollo
npm run dev

# Abrir http://localhost:5173
```

### Cómo Usar el Grafo

| Acción | Cómo |
|--------|------|
| **Explorar** | Arrastrar el fondo para mover el grafo |
| **Hacer zoom** | Rueda del mouse |
| **Seleccionar nodo** | Hacer clic en un nodo |
| **Ver relaciones** | El panel lateral muestra las relaciones del nodo seleccionado |
| **Navegar a otro nodo** | Hacer clic en una relación en el panel |
| **Volver al grafo completo** | Hacer clic en el fondo del grafo |
| **Buscar** | Escribir en el buscador (centra automáticamente en el resultado) |
| **Filtrar por tipo** | Usar los botones del header |
| **Ver tooltip** | Pasar el mouse sobre un nodo |

### Comportamiento del Vecindario

Al hacer clic en un nodo:
- El nodo seleccionado se resalta con borde rojo
- Solo se muestran sus vecinos directos
- Todo lo demás se vuelve casi invisible
- Las aristas conectadas se muestran en rojo con su tipo

---

## El Menú de Herramientas

```bash
python3 -m pipeline.cli.menu
```

| Opción | Nombre | Descripción |
|--------|--------|-------------|
| `0` | Flujo | Muestra el orden paso a paso |
| `1` | Revisar candidatos | Revisión manual uno por uno |
| `2` | Conectar automático | Inserción masiva sin revisión |
| `3` | Recuperar relaciones | Rescata relaciones no insertadas |
| `4` | Auditoría | Diagnóstico completo de la DB |
| `5` | Limpieza segura | Fusión automática + eliminación de ruido |
| `6` | Fusionar duplicados | Fusión manual uno por uno |
| `7` | Fusión automática | Fusión sin preguntar |
| `8` | Limpieza asistida | Revisión de nodos aislados |
| `9` | Limpiar ruido | Eliminación agresiva |
| `10` | Auditoría | Re-ejecutar diagnóstico |
| `11` | Exportar | DB → src/datos.json |
| `12` | Reforzar esquema | Crear índices (ejecutar una vez) |
| `13` | Limpiar archivos | Eliminar archivos temporales |
| `14` | Mantenimiento | Cadena automática completa |
| `15` | Revisión total | Revisar TODOS los nodos existentes |

---

## Respaldo de la Base de Datos

**SIEMPRE** crear backup antes de operaciones importantes:

```bash
# Crear backup con timestamp
cp data/grafo.db "data/grafo_backup_$(date +%Y%m%d_%H%M%S).db"

# Restaurar desde backup
cp data/grafo_backup_20260721_143022.db data/grafo.db
```

**Cuándo crear backup:**
- Antes de cada extracción
- Antes de revisión manual
- Antes de limpieza automática
- Antes de fusión de duplicados
- Después de cada libro completado

---

## Recuperación de Errores

### Si la extracción se interrumpe

El checkpoint preserva el progreso. Reanudar con:

```bash
python3 -m pipeline.extract.extractor libros/mi_libro.pdf
```

### Si aparecen miles de nodos inesperados

1. Restaurar backup:
   ```bash
   cp data/grafo_backup_<timestamp>.db data/grafo.db
   ```

2. Re-exportar:
   ```bash
   python3 scripts/export_json.py
   ```

### Si el frontend no muestra los cambios

```bash
# Re-exportar
python3 scripts/export_json.py

# Recargar el navegador (Ctrl+Shift+R)
```

---

## Estructura de Archivos

```
libros/                  ← Colocar PDFs aquí
data/grafo.db            ← Base de datos SQLite
pipeline/.env            ← API keys (no versionar)
runtime/cache/           ← Candidatos y checkpoints
runtime/logs/            ← Logs de extracción
runtime/state/           ← Estado de revisión
src/datos.json           ← JSON exportado para el frontend
```

---

## Ontología

### Tipos de Nodo

| Tipo | Descripción |
|------|-------------|
| `autor` | Personas con relevancia intelectual |
| `obra` | Libros, artículos, tesis |
| `concepto` | Términos antropológicos establecidos |
| `escuela` | Instituciones académicas organizadas |
| `corriente` | Tendencias de pensamiento |
| `cultura` | Sistemas de prácticas y creencias |
| `poblacion` | Grupos humanos por ubicación/demografía |
| `debate` | Discusiones entre posiciones |

### Tipos de Relación

| Tipo | Descripción |
|------|-------------|
| `autor_de` | Autor wrote obra |
| `influenciado_por` | Influencia entre entidades |
| `critica_a` | Crítica o oposición |
| `desarrolla_concepto` | Desarrollo de un concepto |
| `redefine_a` | Redefinición de concepto |
| `precursor_de` | Precursor histórico |
| `pertenece_a` | Pertenencia a escuela/corriente |
| `estudia_a` | Estudio de cultura/población |
| `contemporaneo_de` | Época compartida |
| `parte_del_debate` | Participación en debate |
| `es_mentor_de` | Relación mentor-discípulo |
| `colabora_con` | Colaboración directa |

### Firewall Epistemológico

El nodo `poblacion` solo puede ser:
- **Destino** de `estudia_a`
- **Origen** de `parte_del_debate`

---

## Comandos Rápidos

```bash
# Extraer un libro
python3 -m pipeline.extract.extractor libros/libro.pdf

# Abrir menú de herramientas
python3 -m pipeline.cli.menu

# Exportar a JSON
python3 scripts/export_json.py

# Ejecutar tests
python3 -m pytest

# Ver frontend
npm run dev

# Build de producción
npm run build
```
