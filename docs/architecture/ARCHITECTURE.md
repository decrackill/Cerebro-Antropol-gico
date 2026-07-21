# Arquitectura — Cerebro Antropológico

**Autoridad máxima**: [MANIFIESTO_ONTOLOGICO.md](MANIFIESTO_ONTOLOGICO.md) v1.1

## Visión General

Aplicación de grafo de conocimiento interactivo para antropología.
Extrae entidades de PDFs académicos usando LLMs (Gemini/OpenRouter), las almacena en SQLite
y las visualiza como grafo navegable en el navegador via Cytoscape.js.

La ontología del grafo está definida formalmente en el Manifiesto Ontológico v1.1.
Este documento describe la implementación técnica, no la ontología.

## Estructura del Proyecto

```
Cerebro-antropologico/
│
├── pipeline/                    # Código Python del pipeline
│   ├── core/                    # Módulos fundamentales
│   │   ├── config.py           # Constantes, paths, umbrales, tipos canónicos
│   │   ├── db.py               # CRUD, fusión, cascada, validar_relacion()
│   │   └── utils.py            # Similitud, normalización, UI helpers
│   │
│   ├── extract/                 # Extracción de PDFs
│   │   ├── extractor.py        # Motor PDF→LLM
│   │   ├── prompts.py          # Templates de prompt (incluye firewall)
│   │   └── modo_manual.py      # Modo manual sin API
│   │
│   ├── review/                  # Revisión y limpieza
│   │   ├── revision.py         # Revisión de candidatos + revisión total
│   │   ├── limpieza.py         # Limpieza, deduplicación, recuperación
│   │   └── auditoria.py        # Diagnóstico de integridad
│   │
│   ├── cli/                     # Interfaz de línea de comandos
│   │   └── menu.py             # Menú principal
│   │
│   ├── check_models.py         # Verificador de modelos API
│   ├── verificar_extraccion.py # Verificador de extracción
│   └── cerebro.py              # Wrapper de compatibilidad
│
├── runtime/                     # Datos de ejecución (no versionados)
│   ├── logs/                   # Logs de extracción
│   ├── state/                  # Checkpoints y estado
│   └── cache/                  # Candidatos y datos temporales
│
├── scripts/                     # Utilidades standalone
│   ├── init_db.py              # Inicialización de DB
│   ├── export_json.py          # Export DB→JSON
│   └── ...
│
├── src/                         # Frontend
│   ├── main.js                 # Entry point
│   ├── grafo.js                # Carga de datos
│   ├── render.js               # Visualización Cytoscape.js
│   └── style.css               # Estilos
│
├── data/                        # Base de datos SQLite
│   └── grafo.db
│
├── tests/                       # Tests automatizados
│   ├── test_firewall.py        # Tests de validación ontológica (56)
│   ├── test_database.py        # Tests de DB
│   ├── test_review.py          # Tests de revisión
│   └── ...
│
├── libros/                      # PDFs fuente
│
├── MANIFIESTO_ONTOLOGICO.md     # Fuente de verdad ontológica (v1.1)
├── ARCHITECTURE.md              # Este archivo
├── ROADMAP.md                   # Roadmap del proyecto
├── README.md                    # Guía de inicio
├── requirements.txt
└── .gitignore
```

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│  index.html → main.js → grafo.js → render.js       │
│  (Vite + Cytoscape.js + fcose layout)              │
└──────────────────────┬──────────────────────────────┘
                       │ fetch datos.json
┌──────────────────────▼──────────────────────────────┐
│                  SCRIPTS                             │
│  export_json.py ← data/grafo.db → init_db.py       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               PIPELINE (Python)                      │
│                                                      │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐           │
│  │  core   │  │ extract │  │  review  │           │
│  │config   │  │extractor│  │ revision │           │
│  │db       │  │prompts  │  │ limpieza │           │
│  │utils    │  │manual_m │  │ auditoria│           │
│  └────┬────┘  └────┬────┘  └────┬─────┘           │
│       │            │            │                   │
│  ┌────▼────────────▼────────────▼─────┐            │
│  │        validar_relacion()          │            │
│  │  (validación ontológica central)   │            │
│  └────────────────────────────────────┘            │
│  ┌────────────────────────────────────┐            │
│  │           cli/menu.py              │            │
│  └────────────────────────────────────┘            │
└──────────────────────┬──────────────────────────────┘
                       │ API calls
┌──────────────────────▼──────────────────────────────┐
│              EXTERNAL SERVICES                       │
│  Google Gemini API  |  OpenRouter API                │
└─────────────────────────────────────────────────────┘
```

## Flujo de Datos

```
PDF → extractor.py → runtime/cache/candidatos_pendientes.json
                         │
                    cli/menu.py (review)
                         │
                    validar_relacion()  ← validación ontológica
                         │
                    data/grafo.db
                         │
                    scripts/export_json.py
                         │
                    src/datos.json
                         │
                    Frontend (Cytoscape.js)
```

## Ontología (implementada)

Ver [MANIFIESTO_ONTOLOGICO.md](MANIFIESTO_ONTOLOGICO.md) para la especificación completa.

### Tipos de Nodo (8)

| Tipo | Definición |
|------|------------|
| `autor` | Agente histórico productor de conocimiento |
| `obra` | Objeto textual con identidad bibliográfica |
| `concepto` | Unidad teórica o categoría de análisis |
| `escuela` | Tradición delimitada por linaje o institución |
| `corriente` | Paradigma teórico que atraviesa escuelas |
| `cultura` | Grupo humano definido etnográficamente |
| `poblacion` | Categoría clasificatoria histórica/racial |
| `debate` | Controversia académica documentada |

### Relaciones Canónicas — Nivel A (12)

| # | Relación | Simetría | Origen | Destino |
|---|----------|----------|--------|---------|
| 1 | `autor_de` | Asimétrica | autor | obra |
| 2 | `influenciado_por` | Asimétrica | autor, obra, escuela, corriente, concepto | autor, obra, escuela, corriente, concepto |
| 3 | `critica_a` | Asimétrica | autor, obra, escuela, corriente | autor, obra, escuela, corriente, concepto |
| 4 | `desarrolla_concepto` | Asimétrica | autor, obra, escuela, corriente | concepto |
| 5 | `redefine_a` | Asimétrica | autor, obra, concepto | concepto |
| 6 | `precursor_de` | Asimétrica | autor, obra, escuela, corriente, concepto | autor, obra, escuela, corriente, concepto |
| 7 | `pertenece_a` | Asimétrica | autor, concepto, escuela | escuela, corriente |
| 8 | `estudia_a` | Asimétrica | autor, obra | poblacion, cultura |
| 9 | `contemporaneo_de` | Simétrica | autor | autor |
| 10 | `parte_del_debate` | Asimétrica | autor, obra, concepto, poblacion, escuela, corriente | debate |
| 11 | `es_mentor_de` | Asimétrica | autor | autor |
| 12 | `colabora_con` | Simétrica | autor | autor |

### Relaciones Conceptuales — Nivel B (3, experimentales)

| Relación | Simetría | Origen | Destino |
|----------|----------|--------|---------|
| `contradice` | Asimétrica | concepto | concepto |
| `relacionado_con` | Simétrica | concepto | concepto |
| `depende_de` | Asimétrica | concepto | concepto |

### Firewall Epistemológico

**Regla absoluta** (Manifiesto §5.3):
- `poblacion` como **origen** → solo `parte_del_debate`
- `poblacion` como **destino** → solo `estudia_a`

## Sistema de Validación

Toda inserción de relaciones pasa por `validar_relacion()` en `pipeline/core/db.py`.

### Flujo de validación

```
INSERT INTO relaciones
    │
    ▼
validar_relacion(conn, origen_id, destino_id, tipo, fuente, cita_textual)
    │
    ├── 1. Tipo de relación canónico (TIPOS_VALIDOS_RELACION)
    ├── 2. No reflexividad (origen ≠ destino)
    ├── 3. Firewall epistemológico (poblacion)
    ├── 4. Compatibilidad origen/destino (COMPATIBILIDAD_RELACIONES)
    └── 5. Evidencia documental (fuente o cita_textual)
    │
    ▼
(True, None)  → INSERT permitido
(False, error) → INSERT rechazado
```

### Puntos de integración

| Archivo | Función | Punto de INSERT |
|---------|---------|-----------------|
| `review/revision.py` | `herramienta_revisar()` | Línea ~214 |
| `review/revision.py` | `herramienta_conectar_automatico()` | Línea ~312 |
| `review/limpieza.py` | `herramienta_recuperar_relaciones()` | Línea ~302 |

## Base de Datos

### Tabla `nodos`
- `id` (INTEGER PK AUTOINCREMENT)
- `tipo` (TEXT NOT NULL, CHECK en 8 tipos)
- `nombre` (TEXT NOT NULL UNIQUE)
- `descripcion` (TEXT)
- `metadatos` (TEXT DEFAULT '{}')

### Tabla `relaciones`
- `id` (INTEGER PK AUTOINCREMENT)
- `origen_id` (INTEGER NOT NULL, FK → nodos)
- `destino_id` (INTEGER NOT NULL, FK → nodos)
- `tipo` (TEXT NOT NULL, CHECK en 12 tipos canónicos)
- `peso` (REAL DEFAULT 1.0)
- `fuente` (TEXT)
- `cita_textual` (TEXT)

## Convenciones

- **Idioma**: Código y UI en español (funciones, variables, constantes)
- **Nomenclatura**: snake_case para Python, camelCase para JS
- **Paths**: Usar `pathlib.Path`, nunca strings
- **DB**: Siempre con `PRAGMA foreign_keys = ON`
- **Context managers**: Usar `with` para conexiones DB
- **Runtime data**: En `runtime/`, nunca en el código
- **Validación**: Siempre pasar por `validar_relacion()` antes de INSERT

## Módulos del Pipeline

| Módulo | Responsabilidad |
|--------|-----------------|
| `core/config.py` | Constantes, paths, umbrales, tipos canónicos |
| `core/db.py` | Conexión CRUD, fusión, cascada, `validar_relacion()` |
| `core/utils.py` | Similitud, normalización, UI helpers |
| `extract/extractor.py` | Motor de extracción PDF→LLM |
| `extract/prompts.py` | Templates de prompt LLM (incluye firewall) |
| `extract/modo_manual.py` | Modo manual sin API |
| `review/revision.py` | Revisión de candidatos + total |
| `review/limpieza.py` | Limpieza, deduplicación, recuperación |
| `review/auditoria.py` | Diagnóstico de integridad |
| `cli/menu.py` | CLI menu system |
