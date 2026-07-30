# 08B — Validación de Consistencia Global

**Fecha:** Julio 2026

## Resumen

Auditoría integral del proyecto como sistema unificado: ontología ↔ DB ↔ pipeline ↔ frontend ↔ tests.

---

## 1. Consistencia Conceptual

| Verificación | Resultado |
|-------------|-----------|
| Definiciones compatibles entre capas | ✅ |
| Terminología uniforme en código | ✅ (español consistente) |
| Conceptos duplicados en ontología | ✅ (0 detectados) |
| Reglas contradictorias | ✅ (0 encontradas) |

## 2. Consistencia Estructural

| Capa | Estado |
|------|--------|
| Ontología (8 tipos, 12+3 relaciones) | ✅ |
| DB SQLite (CHECK constraints, FK, índices) | ✅ |
| Pipeline (extracción → validación → inserción) | ✅ |
| Frontend (Cytoscape, filtros, panel lateral) | ✅ |
| Export (datos.json → frontend) | ✅ |

## 3. Consistencia Funcional

| Flujo | Resultado |
|-------|-----------|
| Extracción → candidatos_pendientes.json | ✅ |
| Revisión 1x1 → nodos en DB | ✅ |
| Conexión bulk → relaciones en DB | ✅ |
| Recuperación de relaciones desde caché | ✅ |
| Fusión de duplicados → ids_previos preservados | ✅ |
| Export → datos.json → Cytoscape | ✅ |

## 4. Consistencia del Pipeline

| Etapa | Entrega | Compatible con |
|-------|---------|----------------|
| Extractor (Gemini → JSON) | candidatos | Parser/review |
| Revisión 1x1 | nodos validados | DB |
| Conexión automática | relaciones validadas | DB |
| Recuperación de caché | relaciones rescatadas | DB |
| Fusión | deduplicación | DB |
| Export | datos.json | Frontend |

No se detectaron pérdidas de información entre etapas.

## 5. Consistencia Tecnológica

| Componente | Compatible con |
|------------|----------------|
| SQLite | ✅ Toda la pila |
| Pipeline Python | ✅ SQLite + JSON |
| Frontend JS | ✅ datos.json |
| Vite dev server | ✅ Proxy a producción |

## 6. Tests

**109 tests, 0 fallos:**

| Archivo | Tests | Cubre |
|---------|-------|-------|
| test_firewall.py | 64 | Validación, aliases, compatibilidad |
| test_integration.py | 15 | Ciclo completo, fusión, export, helpers |
| test_database.py | 10 | CRUD básico |
| test_imports.py | 10 | Importaciones de módulos |
| test_review.py | 6 | Revisión de candidatos |
| test_menu.py | 5 | Navegación del menú |
| test_extractor.py | 3 | Extracción básica |

## 7. Frontend

- Build: ✅ (vite build exitoso)
- Cytoscape.js: carga datos.json, renderiza grafo
- Filtros: por tipo de nodo
- Buscador: resalta nodos por nombre
- Panel lateral: relaciones con detalle
- Header stats: contador de nodos y conexiones

## 8. Riesgos Sistémicos

| Riesgo | Criticidad | Mitigación |
|--------|-----------|-----------|
| 386 nodos aislados | Media | Previsto en auditoría post-limpieza |
| Chunk size >500KB | Baja | Cytoscape.js es grande por naturaleza |
| Sin GraphRAG ni embeddings | Baja | Previsto como feature futuro |
| ~535 candidatos pendientes | Alta | Deben revisarse manualmente |

## 9. Dictamen

El sistema completo es consistente: todas las capas (ontología, DB, pipeline, frontend, tests) son compatibles entre sí. No existen contradicciones críticas. El conocimiento conserva su significado durante todo el ciclo de vida (extracción → almacenamiento → visualización).

**Consistencia global: VERIFICADA**
