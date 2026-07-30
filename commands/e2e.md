---
description: Generate and run E2E tests with Playwright
agent: e2e-runner
subtask: true
---

# E2E Command

Generar/ejecutar tests end-to-end: $ARGUMENTS

## Tu Tarea

1. Iniciar servidor: `npm run dev`
2. Ejecutar tests Playwright
3. Reportar resultados

## Flujos a Testear

### Carga del Grafo
- Header muestra stats
- Cytoscape.js renderiza

### Filtros y Búsqueda
- Botones de filtro funcionan
- Buscador resalta nodos

### Panel Lateral
- Click en nodo muestra detalles
- Relaciones se despliegan

## Comandos
```bash
npm run dev  # en background
npx playwright test
```

## Reporte
- Tests pasados/fallados
- Screenshots si hay fallos
- Tiempo de ejecución
