# Arquitectura — Cerebro Antropológico

## Visión General

Aplicación de grafo de conocimiento interactivo para antropología.
Extrae entidades de PDFs académicos usando LLMs (Gemini/OpenRouter), las almacena en SQLite
y las visualiza como grafo navegable en el navegador via Cytoscape.js.

## Estructura del Proyecto

```
Cerebro-antropologico/
│
├── pipeline/                    # Código Python del pipeline
│   ├── core/                    # Módulos fundamentales
│   │   ├── config.py           # Constantes, paths, umbrales
│   │   ├── db.py               # Conexión CRUD, fusión, cascada
│   │   └── utils.py            # Similitud, normalización, UI helpers
│   │
│   ├── extract/                 # Extracción de PDFs
│   │   ├── extractor.py        # Motor PDF→LLM
│   │   ├── prompts.py          # Templates de prompt
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
├── libros/                      # PDFs fuente
│
├── ARCHITECTURE.md
├── ROADMAP.md
├── README.md
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
                    data/grafo.db
                         │
                    scripts/export_json.py
                         │
                    src/datos.json
                         │
                    Frontend (Cytoscape.js)
```

## Módulos del Pipeline

| Módulo | Responsabilidad | Líneas |
|--------|-----------------|--------|
| `core/config.py` | Constantes, paths, umbrales | ~140 |
| `core/db.py` | Conexión CRUD, fusión, cascada | ~140 |
| `core/utils.py` | Similitud, normalización, UI helpers | ~100 |
| `extract/extractor.py` | Motor de extracción PDF→LLM | ~380 |
| `extract/prompts.py` | Templates de prompt LLM | ~150 |
| `extract/modo_manual.py` | Modo manual sin API | ~160 |
| `review/revision.py` | Revisión de candidatos + total | ~440 |
| `review/limpieza.py` | Limpieza, deduplicación, recuperación | ~310 |
| `review/auditoria.py` | Diagnóstico de integridad | ~130 |
| `cli/menu.py` | CLI menu system | ~180 |

## Convenciones

- **Idioma**: Código y UI en español (funciones, variables, constantes)
- **Nomenclatura**: snake_case para Python, camelCase para JS
- **Paths**: Usar `pathlib.Path`, nunca strings
- **DB**: Siempre con `PRAGMA foreign_keys = ON`
- **Context managers**: Usar `with` para conexiones DB
- **Runtime data**: En `runtime/`, nunca en el código

## Base de Datos

### Tabla `nodos`
- `id` (INTEGER PK AUTOINCREMENT)
- `tipo` (TEXT NOT NULL, CHECK en 8 tipos válidos)
- `nombre` (TEXT NOT NULL UNIQUE)
- `descripcion` (TEXT)
- `metadatos` (TEXT DEFAULT '{}')

### Tabla `relaciones`
- `id` (INTEGER PK AUTOINCREMENT)
- `origen_id` (INTEGER NOT NULL, FK → nodos)
- `destino_id` (INTEGER NOT NULL, FK → nodos)
- `tipo` (TEXT NOT NULL, CHECK en 9 tipos válidos)
- `peso` (REAL DEFAULT 1.0)
- `fuente` (TEXT)
- `cita_textual` (TEXT)

### Tipos de Nodo (8)
autor, obra, concepto, escuela, cultura, debate, poblacion, corriente

### Tipos de Relación (9)
influenciado_por, critica_a, desarrolla_concepto, pertenece_a,
estudia_a, contemporaneo_de, precursor_de, parte_del_debate, redefine_a
