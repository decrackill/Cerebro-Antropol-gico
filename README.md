# Cerebro Antropológico

Grafo de conocimiento interactivo de antropología. Extrae entidades (autores, obras, conceptos, escuelas, culturas, debates, poblaciones, corrientes) y relaciones de textos PDF académicos usando LLM, y las visualiza como un grafo navegable en el navegador.

## Instalación

### Frontend
```bash
npm install
npm run dev
```

### Pipeline (extracción y gestión)
```bash
pip install -r requirements.txt
```

## Uso

1. Colocar PDFs en `libros/`
2. Extraer entidades: `python pipeline/extractor.py libros/ejemplo.pdf`
3. Gestionar candidatos: `python pipeline/cerebro.py`
4. Visualizar en el navegador con `npm run dev`

## Estructura

- `pipeline/` — Extracción y gestión de entidades
- `scripts/` — Inicialización de DB y exportación
- `src/` — Frontend (Vite + Cytoscape.js)
- `data/` — Base de datos SQLite
