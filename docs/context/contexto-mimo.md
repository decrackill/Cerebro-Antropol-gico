# Cerebro Antropológico — Contexto Completo

/context ~/Descargas/Obsidian Vault/Cerebro/Columna del Proyecto/Estructura del Proyecto.md

---

## ¿Qué es?

Grafo de conocimiento antropológico. Extrae entidades (autores, obras, conceptos, etc.) de PDFs académicos usando LLMs (Gemini 2.5 Flash), las almacena en SQLite con validación ontológica, y las visualiza como grafo interactivo en el navegador.

---

## Arquitectura del Proyecto

```
Cerebro-antropologico/
├── pipeline/                        # Python — backend
│   ├── __init__.py
│   ├── core/                        # Config, DB, utilidades
│   │   ├── config.py                # Paths, tipos válidos, aliases, umbrales
│   │   ├── db.py                    # CRUD, fusion, validacion centralizada
│   │   └── utils.py                 # Texto, duplicados, UI helpers
│   ├── extract/                     # Extracción PDF → LLM
│   │   ├── extractor.py             # Pipeline automático (API Gemini/OpenRouter)
│   │   ├── modo_manual.py           # Modo manual (generar prompt / pegar respuesta)
│   │   └── prompts.py               # System prompts para Gemini
│   ├── review/                      # Revisión y limpieza
│   │   ├── revision.py              # Revisión de candidatos 1x1 y bulk
│   │   ├── limpieza.py              # Fusión, ruido, recuperación de relaciones
│   │   └── auditoria.py             # Diagnóstico completo del grafo
│   └── cli/
│       └── menu.py                  # Menú principal (punto de entrada)
├── scripts/                         # Utilidades standalone
│   ├── export_json.py               # SQLite → frontend/public/datos.json
│   ├── init_db.py                   # Crear esquema DB desde cero
│   ├── check_models.py              # Verificar tipos (bug: busca .env en scripts/)
│   └── verificar_extraccion.py      # Ver cobertura de extracción por PDF
├── frontend/                        # Aplicación web (Vite + Cytoscape.js)
│   ├── index.html                   # HTML principal (con #stats header)
│   ├── src/                         # JS/CSS del frontend
│   │   ├── main.js                  # init(), carga stats
│   │   ├── render.js                # Visualización Cytoscape, panel lateral, mapeo de libros
│   │   ├── grafo.js                 # Carga de datos (fetch datos.json)
│   │   └── style.css                # Estilos
│   └── public/
│       └── datos.json               # Datos curados para producción (394 nodos, 371 rel)
├── archive/                         # Scripts one-off y docs históricas
├── libros/                          # PDFs fuente (gitignored)
├── data/
│   └── grafo.db                     # SQLite principal (gitignored)
├── runtime/
│   ├── cache/                       # candidatos_pendientes.json, procesados_*.json
│   ├── logs/                        # extraccion_log_*.json
│   └── state/                       # checkpoint_*.json, revision_estado.json, limpieza_estado.json
├── tests/                           # pytest (107 tests)
├── vite.config.js                   # root: 'frontend', proxy /api
├── package.json                     # npm deps (vite, cytoscape, etc.)
├── requirements.txt                 # Python deps
├── wrangler.toml                    # Cloudflare Pages, build: frontend/dist
├── README.md                        # Documentación principal
├── docs/
│   ├── context/GUIA_DE_USO.md       # Guía de usuario
├── DOCUMENTATION_INDEX.md           # Índice de docs
├── CONTRIBUTING.md                  # Guía de contribución
└── contexto-mimo.md                 # Este archivo
```

---

## Ontología (Manifiesto v1.1)

### 8 tipos de nodo

| Tipo | Descripción |
|------|-------------|
| `autor` | Persona académica/intelectual |
| `obra` | Libro, artículo, texto |
| `concepto` | Idea o noción (1–4 palabras) |
| `escuela` | Institución/sede/miembros identificables |
| `corriente` | Tendencia de pensamiento sin organización formal |
| `cultura` | Prácticas/creencias/organización social |
| `poblacion` | Origen/demografía/ubicación (NUNCA se fusiona con cultura) |
| `debate` | Discusión/tensión entre posiciones |

### 12 relaciones canónicas (Nivel A)

| Relación | Origen | Destino |
|----------|--------|---------|
| `autor_de` | autor | obra |
| `influenciado_por` | autor, obra, escuela, corriente, concepto | autor, obra, escuela, corriente, concepto |
| `critica_a` | autor, obra, escuela, corriente | autor, obra, escuela, corriente, concepto |
| `desarrolla_concepto` | autor, obra, escuela, corriente | concepto |
| `redefine_a` | autor, obra, concepto | concepto |
| `precursor_de` | autor, obra, escuela, corriente, concepto | autor, obra, escuela, corriente, concepto |
| `pertenece_a` | autor, concepto, escuela | escuela, corriente |
| `estudia_a` | autor, obra | poblacion, cultura |
| `contemporaneo_de` | autor | autor |
| `parte_del_debate` | autor, obra, concepto, poblacion, escuela, corriente | debate |
| `es_mentor_de` | autor | autor |
| `colabora_con` | autor | autor |

### 3 relaciones conceptuales (Nivel B)
`contradice`, `relacionado_con`, `depende_de`
(menos restrictivas, para relaciones que no encajan en Nivel A)

### Firewall epistemológico
- `poblacion` solo puede ser **destino** de `estudia_a`
- `poblacion` solo puede ser **origen** de `parte_del_debate`

### Aliases de relación (~40 en `config.py:TIPOS_ALIAS_RELACION`)
Gemini genera tipos no canónicos; los aliases los normalizan. Si no hay alias, la relación es rechazada.

| Alias → Canónico |
|---|
| `influyó_en`, `influye_en`, `influencio_a` → `influenciado_por` |
| `estudio`, `describe_a`, `cita_a`, `realiza_trabajo_de_campo_en`, `evalua_contribucion_de` → `estudia_a` |
| `ejemplifica_con`, `ejemplo_de`, `practica_concepto`, `promueve_concepto`, `discute_concepto`, `trata_de` → `desarrolla_concepto` |
| `refuta`, `lucha_contra`, `opuesto_a`, `contrasta_con`, `es_respuesta_a` → `critica_a` |
| `localizado_en`, `ubica_en`, `incluye_a`, `migra_a`, `prologa_obra`, `publica`, `dirige_publicacion`, `difundido_en`, `es_tipo_de` → `pertenece_a` |
| `origen_de`, `atribuye_origen_a` → `precursor_de` |
| `condiciona`, `facilito_por` → `influenciado_por` |

---

## Base de Datos SQLite (`data/grafo.db`)

### Tabla `nodos`
```sql
CREATE TABLE nodos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('autor','obra','concepto','escuela','corriente','cultura','poblacion','debate')),
    descripcion TEXT,
    metadatos TEXT DEFAULT '{}',    -- JSON: id_gemini, ids_previos, revision_estado, etc.
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tabla `relaciones`
```sql
CREATE TABLE relaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origen_id INTEGER NOT NULL REFERENCES nodos(id) ON DELETE CASCADE,
    destino_id INTEGER NOT NULL REFERENCES nodos(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL,              -- tipo canónico
    fuente TEXT,                     -- ej. "boas-f-1911-esp.pdf, p.45-47"
    cita_textual TEXT,               -- cita textual del PDF
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tabla `actividad_log`
```sql
CREATE TABLE actividad_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    accion TEXT NOT NULL,
    detalle TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Índices (creados con opción 12 del menú)
```sql
CREATE UNIQUE INDEX idx_relacion_unica ON relaciones (origen_id, destino_id, tipo);
CREATE INDEX idx_rel_tipo ON relaciones(tipo);
CREATE INDEX idx_nodo_tipo ON nodos(tipo);
```

---

## Pipeline de Extracción

### Flujo `extractor.py`
1. Abre PDF con PyMuPDF (`fitz`), extrae texto página por página
2. Divide en **chunks de ~40,000 caracteres** con rastreo de página inicio/fin
3. Para cada chunk:
   - Construye prompt con catálogo de nodos existentes (para evitar duplicados)
   - Llama a **Gemini 2.5 Flash** (o OpenRouter como fallback)
   - Parsea respuesta JSON
   - Normaliza tipos (`libro`→`obra`, `texto`→`obra`)
   - Guarda **checkpoint** (reanudable si se interrumpe)
   - Pausa 4s entre llamadas
4. Acumula resultados en `runtime/cache/candidatos_pendientes.json`
5. Guarda log en `runtime/logs/extraccion_log_<pdf>.json`

### Rotación de API Keys
- Lee `GEMINI_API_KEY`, `GEMINI_API_KEY_2`...`_5` y `OPENROUTER_API_KEY`
- Si una key da `429` (cuota agotada), rota automáticamente a la siguiente
- Si todas fallan, el chunk se omite (queda registrado en el log de fallos)

### Checkpoint system
- Archivo: `runtime/state/checkpoint_<pdf_stem>.json`
- Contiene: lista de índices de chunks ya procesados
- `--reset` para reiniciar desde cero
- `--max-chunks N` para procesar solo N chunks (pruebas)

### Modo manual (`modo_manual.py`)
- `generar`: imprime el prompt para copiar-pegar a Gemini en chat web
- `pegar`: pega la respuesta JSON de Gemini y la procesa igual que el automático

---

## Validación Centralizada (`db.py:validar_relacion()`)

Toda relación INSERT pasa por 5 validadores en cadena:

1. **Tipo canónico** — solo 12 tipos Nivel A + 3 Nivel B (resuelve alias primero)
2. **No reflexividad** — un nodo no se conecta a sí mismo
3. **Firewall epistemológico** — restricciones de `poblacion`
4. **Compatibilidad origen/destino** — según la matriz `COMPATIBILIDAD_RELACIONES`
5. **Evidencia documental** — requiere al menos `fuente` o `cita_textual`

Firma: `validar_relacion(conn, origen_id, destino_id, tipo, fuente=None, cita_textual=None) → (bool, str|None)`

---

## Fusión de Duplicados

### Política de `fusionar_nodos()` (`db.py:25-78`)
1. Redirige todas las relaciones del nodo a borrar hacia el nodo a mantener
2. Elimina relaciones duplicadas que se generen (prioriza la que tiene cita_textual)
3. Preserva **`ids_previos`** en metadatos del nodo mantenido (array con todos los IDs históricos)
4. Elimina el nodo borrado
5. **Commit explícito** al final

### Exclusiones de fusión (`config.py:EXCLUSIONES_FUSION_NOMBRES_NOMBRES`)
Pares que NUNCA se fusionan aunque sean similares:
- América ↔ Norteamérica
- América ↔ América Central
- Australianos ↔ Aborígenes australianos
- Japoneses ↔ Japoneses de Hawái

### Recuperación de relaciones (`herramienta_recuperar_relaciones`)
Busca en `runtime/cache/candidatos_procesados_*.json` relaciones que no se resolvieron (porque el nodo destino no existía en ese momento). Usa `construir_mapa_resolucion()` para mapear IDs históricos (incluyendo `ids_previos` de fusiones) a IDs actuales. **Importante**: busca en `CACHE_DIR`, no en `BASE_DIR` (bugfix de jul 2026).

---

## Frontend

```bash
npm run dev        # desarrollo en :5173
npm run build      # build → dist/
npm run preview    # preview del build
```

- **Vite** sirve `index.html`, proxy `/api/*` → `https://cerebro-antropologico.pages.dev`
- **No usa Wrangler local** — no hay Cloudflare Workers en desarrollo
- **Cytoscape.js** renderiza el grafo desde `frontend/public/datos.json`
- Header muestra `#stats`: "X nodos · Y conexiones"
- Filtros por tipo de nodo (botones en `#filtros`)
- Buscador (`#buscar`) para resaltar nodos por nombre
- Panel lateral: lista de relaciones `tipo → nombre`; al hacer clic despliega detalle (libro, fuente, cita textual)
- Mapeo de PDFs a títulos de libros en `render.js` (frontend-only, no modifica DB)

### `frontend/public/datos.json`
- Export manual con `scripts/export_json.py`
- Actual: **394 nodos, 371 relaciones** (curados)
- DB local tiene ~1433 nodos (pre-limpieza) pero **no se sirven a producción**
- Se mantiene separado para no exponer datos sin revisar

---

## Menú Principal

```bash
python3 -m pipeline.cli.menu   # ← siempre con -m para imports relativos
```

Las opciones e1/e2/e3 piden solo el **stem** del PDF (sin ruta ni extensión), lo buscan en `libros/`.

### Extracción
| Cmd | Nombre | Descripción |
|-----|--------|-------------|
| `e1` | Extraer | Automático con Gemini API (con checkpoint reanudable) |
| `e2` | Modo manual | Genera prompt para chat o pega respuesta JSON |
| `e3` | Verificar | Verifica cobertura de extracción por PDF |

### Herramientas
| Cmd | Nombre | Descripción |
|-----|--------|-------------|
| `1` | Revisar candidatos | Manual 1x1 desde `candidatos_pendientes.json` |
| `2` | Conectar automático | Bulk: resuelve relaciones candidate → DB |
| `3` | Recuperar relaciones | Rescata relaciones de `candidatos_procesados_*.json` |
| `4` | Auditoría | Diagnóstico completo (progreso, stats, integridad, aislados) |
| `5` | Limpieza segura | Fusión automática + eliminación de ruido biomédico |
| `6` | Fusionar duplicados | Manual 1x1 (pregunta cada par) |
| `7` | Fusión automática | Sin preguntar (usa umbrales) |
| `8` | Limpieza asistida | Revisión de nodos aislados |
| `9` | Limpiar ruido | Eliminación agresiva de ruido biomédico |
| `10` | Auditoría (repetir) | Re-ejecuta diagnóstico |
| `11` | Exportar | DB → `frontend/public/datos.json` |
| `12` | Reforzar esquema | Crea índices (run-once, seguro re-ejecutar) |
| `13` | Limpiar archivos | Elimina `candidatos_procesados_*.json` y logs |
| `14` | Mantenimiento | Cadena completa: limpieza → recuperación → export → auditoría |
| `15` | Revisión total | Revisar TODOS los nodos de la DB |

### Flujo recomendado
1. Colocar PDF en `libros/`
2. `e1` Extraer entidades
3. `1` Revisar candidatos (aprobar/rechazar/editar 1x1)
4. `2` Conectar automático (resolver relaciones bulk)
5. `3` Recuperar relaciones perdidas
6. `4` Auditoría (diagnóstico)
7. `5-9` Limpiar y deduplicar
8. `11` Exportar
9. `npm run dev` (visualizar en navegador)

---

## Estado Actual (jul 2026)

### Completado
- Pipeline de extracción funcional (automático + manual + checkpoint)
- Rotación de API keys con fallback OpenRouter
- Revisión de candidatos 1x1 y bulk
- Recuperación de relaciones desde caché con mapa de resolución histórica
- Fusión de duplicados con preservación de `ids_previos`
- Eliminación de ruido biomédico (patrones craneales/óseos)
- Auditoría de consistencia (integridad referencial, nodos aislados, duplicados)
- Firewall epistemológico en validación
- ~40 aliases de relación para normalizar salida de Gemini
- Frontend con Cytoscape, filtros, panel lateral con detalle
- Contador de stats en header
- 32 documentos en Obsidian vault con wikilinks completos
- Extracción completa del libro de Boas (16/16 chunks)
- Limpieza: 42 fusiones, 11 eliminaciones
- Auditoría post-limpieza: 1433 nodos, 1137 relaciones, 376 aislados

### Pendiente / Problemas Conocidos
- **404+ relaciones rechazadas** por tipos no canónicos (Gemini inventa `dirige`, `traduce`, `practica`, etc.)
- **84 relaciones no resolubles** en recuperación
- **~535 candidatos pendientes** de revisión en `runtime/cache/candidatos_pendientes.json`
- **~376 nodos aislados** en DB local
- `check_models.py` busca `.env` en `scripts/` en vez de `pipeline/` (bug menor)
- Curación manual necesaria para expandir datos de producción (hoy 394 nodos)

---

## Convenciones

| Aspecto | Regla |
|---------|-------|
| Idioma | Código, UI, comentarios en español |
| Python | `snake_case` |
| JavaScript | `camelCase` |
| Paths | `pathlib.Path` (no os.path ni strings) |
| DB | Siempre `PRAGMA foreign_keys = ON` |
| Validación | Siempre `validar_relacion()` antes de INSERT |
| Tests | `pytest` en `tests/` (107 tests) |
| Ejecución módulos | `python3 -m pipeline.cli.menu` (evita import relativo roto) |
| Git | Commits en español, descriptivos |
| Env | API keys en `pipeline/.env` (gitignored) |
| DB file | `data/grafo.db` (gitignored) |

---

## Variables de Entorno (`pipeline/.env`)

```
GEMINI_API_KEY=...
GEMINI_API_KEY_2=...      # Rotación automática
GEMINI_API_KEY_3=...
GEMINI_API_KEY_4=...
GEMINI_API_KEY_5=...
OPENROUTER_API_KEY=...    # Fallback si Gemini falla
```

---

## Despliegue

- **Cloudflare Pages** frontend en `https://cerebro-antropologico.pages.dev`
- Build: `npm run build` → sube carpeta `dist/`
- API: Cloudflare Functions en `functions/` proxy a SQLite (no usado localmente)
- Vite en local proxy `/api` a producción

---

## Documentación Clave en el Repo

| Documento | Ruta | Contenido |
|-----------|------|-----------|
| Manifiesto Ontológico | `docs/ontology/MANIFIESTO_ONTOLOGICO.md` | Ontología formal, reglas, firewall |
| Arquitectura técnica | `docs/architecture/ARCHITECTURE.md` | Sistema de validación, diseño |
| Roadmap | `docs/architecture/ROADMAP.md` | Estado, trabajo pendiente |
| Guía de uso | `GUIA_DE_USO.md` | Tutorial de uso del sistema |
| Índice docs | `DOCUMENTATION_INDEX.md` | Índice completo |
| RFC Motor Visual | `docs/RFC_MOTOR_VISUAL.md` | Propuesta de motor visual |

---

## Obsidian Vault

**Ubicación:** `~/Descargas/Obsidian Vault/Cerebro/`

9 carpetas, 32 archivos .md, todos interconectados con wikilinks (agregados jul 2026):

| Carpeta | Archivos |
|---------|----------|
| `1 y 2 - Aditoría y Diseño/` | `1. Auditoría Arquitectónica.md` (prompt FASE 1), `2. Diseño de la Ontología.md` (prompt FASE 2) |
| `3. Reorganización Conceptual/` | `03A Metodología de Reclasificación.md` → `03B Revisión de Categorías.md` → `03C Revisión de Nodos.md` → `03D Validación Conceptual.md` |
| `4. Reorganización de Relaciones/` | `04A Metodología.md`, `04B-1 Tipología de Relaciones.md`, `04B-2 Tipología de Relaciones.md`, `04B-3 Tipología de Relaciones.md` |
| `5. Auditoría Global/` | `05A Metodología de Auditoría.md` → `05B Auditoría Ontológica.md` → `05C Auditoría Estructural.md` → `05D Informe Final y Certificación.md` |
| `6. Blueprint/` | `06A Arquitectura de la Migración.md`, `06B Hoja Maestra de Implementación.md` |
| `7. Implementación Guiada/` | `07A Preparación.md` → `07B Plan Modularizado.md` → `07C Módulos.md` → `07D Ecosistema.md` → `07E Validación.md` → `07F Cierre.md` |
| `8. Validación Final/` | `08A Validación Ontológica.md` → `08B Consistencia Global.md` → `08C Stress Testing.md` → `08D Validación Científica.md` → `08E Validación Técnica.md` → `08F Certificación Final.md` |
| `Columna del Proyecto/` | `Estructura del Proyecto.md` (mapa completo con links), `Metodología y Principios Arquitectónicos.md`, `Rol permanente.md` |
| `Documentación/` | `Informe Fase 1.md`, `Informe fase 2.md` (resúmenes ejecutivos) |

---

## Cómo Usar Este Archivo

En futuras sesiones, una IA puede cargar todo el contexto ejecutando:

```
cat contexto-mimo.md
```

O en Obsidian, abrir `/context ~/Descargas/Obsidian Vault/Cerebro/Columna del Proyecto/Estructura del Proyecto.md` para navegar la estructura completa del proyecto.

### Comandos rápidos de inicio

```bash
# Ver estado del grafo
python3 -m pipeline.cli.menu   # opción 4 (auditoría)

### Extraer un nuevo PDF
python3 -m pipeline.cli.menu   # opción e1

### Revisar candidatos pendientes
python3 -m pipeline.cli.menu   # opción 1

### Ver visualización
npm run dev                     # abrir http://localhost:5173

### Exportar datos curados
python3 -m pipeline.cli.menu   # opción 11

### Mantenimiento completo
python3 -m pipeline.cli.menu   # opción 14

### Ejecutar tests
pytest -q

### Ver diferencias sin commit
git diff --stat
```
