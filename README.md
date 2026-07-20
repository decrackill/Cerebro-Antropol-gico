# Cerebro Antropológico

Grafo de conocimiento interactivo para antropología. Extrae entidades de PDFs académicos usando LLMs, las almacena en SQLite y las visualiza como grafo navegable en el navegador.

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

## Estructura del Proyecto

```
Cerebro-antropologico/
├── pipeline/                    # Código Python
│   ├── core/                    # Config, DB, utils
│   ├── extract/                 # Extracción PDF→LLM
│   ├── review/                  # Revisión y limpieza
│   └── cli/                     # Menú principal
├── scripts/                     # Utilidades standalone
├── src/                         # Frontend (JS/CSS)
├── tests/                       # Tests automatizados
├── data/                        # Base de datos SQLite
├── libros/                      # PDFs fuente
└── runtime/                     # Datos de ejecución
```

## Ejecución de Tests

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests específicos
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
- **Tests**: pytest, archivos en `tests/`

## Licencia

Proyecto privado.
