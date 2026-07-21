# Cerebro Antropológico

Grafo de conocimiento interactivo para antropología. Extrae entidades de PDFs académicos usando LLMs, las almacena en SQLite y las visualiza como grafo navegable en el navegador.

## Autoridad Máxima

El [MANIFIESTO_ONTOLOGICO.md](docs/ontology/MANIFIESTO_ONTOLOGICO.md) (v1.1) es la **fuente de verdad** del proyecto.
Define la ontología, las reglas de clasificación y las restricciones del grafo.
Toda implementación debe adaptarse al Manifiesto, nunca al revés.

## Instalación

### Requisitos
- Python 3.12+
- Node.js 18+
- API keys de Google Gemini u OpenRouter

### Pasos

```bash
# Clonar el repositorio
git clone https://github.com/decrackill/Cerebro-Antropol-gico.git
cd Cerebro-Antropol-gico

# Instalar dependencias Python
pip install -r requirements.txt

# Instalar dependencias JavaScript
npm install

# Configurar variables de entorno
cp pipeline/.env.example pipeline/.env
# Editar pipeline/.env con tus API keys

# Inicializar la base de datos
python3 scripts/init_db.py
```

## Uso

### Pipeline de extracción

```bash
# Extraer entidades de un PDF
python -m pipeline.extract.extractor libros/mi_libro.pdf

# Modo manual (sin API)
python -m pipeline.extract.modo_manual libros/mi_libro.pdf generar

# Gestionar candidatos
python -m pipeline.cli.menu
```

### Frontend

```bash
# Desarrollo
npm run dev

# Producción
npm run build
npm run preview
```

## Ontología

El grafo se basa en una ontología formal con:

- **8 tipos de nodo**: autor, obra, concepto, escuela, corriente, cultura, poblacion, debate
- **12 relaciones canónicas (Nivel A)**: autor_de, influenciado_por, critica_a, desarrolla_concepto, redefine_a, precursor_de, pertenece_a, estudia_a, contemporaneo_de, parte_del_debate, es_mentor_de, colabora_con
- **3 relaciones conceptuales (Nivel B)**: contradice, relacionado_con, depende_de
- **Firewall epistemológico**: `poblacion` solo puede ser destino de `estudia_a` u origen de `parte_del_debate`

Ver [MANIFIESTO_ONTOLOGICO.md](docs/ontology/MANIFIESTO_ONTOLOGICO.md) para la especificación completa.

## Sistema de Validación

Toda inserción de relaciones pasa por `validar_relacion()` que verifica:
1. Tipo de relación canónico
2. No reflexividad (un nodo no se conecta a sí mismo)
3. Firewall epistemológico (restricciones sobre `poblacion`)
4. Compatibilidad origen/destino
5. Evidencia documental (fuente o cita_textual)

Ver [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) para detalles de implementación.

## Estructura del Proyecto

```
Cerebro-antropologico/
├── pipeline/                    # Código Python
│   ├── core/                    # Config, DB, utils, validar_relacion()
│   ├── extract/                 # Extracción PDF→LLM
│   ├── review/                  # Revisión y limpieza
│   └── cli/                     # Menú principal
├── scripts/                     # Utilidades standalone
├── src/                         # Frontend (JS/CSS)
├── tests/                       # Tests automatizados (107 tests)
├── data/                        # Base de datos SQLite [ignorado]
├── libros/                      # PDFs fuente [ignorado]
├── runtime/                     # Datos de ejecución [ignorado]
├── docs/                        # Documentación
│   ├── ontology/                # Manifiesto Ontológico v1.1
│   ├── architecture/            # Arquitectura técnica y ROADMAP
│   └── reports/                 # Reportes y guías
└── README.md                    # Este archivo
```

## Ejecución de Tests

```bash
# Ejecutar todos los tests (107 tests)
pytest

# Ejecutar tests del firewall ontológico
pytest tests/test_firewall.py -v

# Ejecutar tests de DB
pytest tests/test_database.py -v

# Ejecutar sin verbosidad
pytest -q
```

## Variables de Entorno

Copiar `pipeline/.env.example` a `pipeline/.env` y configurar:

| Variable | Descripción |
|----------|-------------|
| `GEMINI_API_KEY` | API key de Google Gemini |
| `GEMINI_API_KEY_2` a `_5` | Keys adicionales para rotación |
| `OPENROUTER_API_KEY` | API key de OpenRouter |

## Convenciones

- **Idioma**: Código y UI en español
- **Nomenclatura**: snake_case para Python, camelCase para JS
- **Paths**: Usar `pathlib.Path`
- **DB**: Siempre con `PRAGMA foreign_keys = ON`
- **Validación**: Siempre pasar por `validar_relacion()` antes de INSERT
- **Tests**: pytest, archivos en `tests/`

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [MANIFIESTO_ONTOLOGICO.md](docs/ontology/MANIFIESTO_ONTOLOGICO.md) | Ontología formal, reglas, firewall |
| [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | Arquitectura técnica, sistema de validación |
| [ROADMAP.md](docs/architecture/ROADMAP.md) | Estado del proyecto, trabajo pendiente |
| [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) | Índice completo de documentación |

## Licencia

Proyecto privado.
