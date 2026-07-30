# 07F — Cierre de Implementación

**Fecha:** Julio 2026

## Estado del Proyecto

### Ontología (Manifiesto v1.1)
- ✅ 8 tipos de nodo implementados con CHECK constraint
- ✅ 12 relaciones Nivel A implementadas en `COMPATIBILIDAD_RELACIONES`
- ✅ 3 relaciones Nivel B (contradice, relacionado_con, depende_de) aceptadas
- ✅ ~40 aliases de relación normalizados en `config.py`
- ✅ Firewall epistemológico validado con 12 tests

### Modelo de Datos (SQLite)
- ✅ Tabla `nodos` con todos los campos requeridos
- ✅ Tabla `relaciones` con evidencia documental (fuente + cita_textual)
- ✅ Tabla `actividad_log` para auditoría
- ✅ Índices: idx_relacion_unica, idx_rel_tipo, idx_nodo_tipo
- ✅ Integridad referencial con ON DELETE CASCADE

### Pipeline
- ✅ Extracción automática con Gemini 2.5 Flash
- ✅ Checkpoint reanudable
- ✅ Rotación de 5 API keys + fallback OpenRouter
- ✅ Modo manual (generar prompt / pegar respuesta)
- ✅ Validación centralizada con 6 validadores en cadena
- ✅ Backfill de cita_textual desde caché

### Revisión y Limpieza
- ✅ Revisión de candidatos 1x1
- ✅ Conexión automática en bulk
- ✅ Recuperación de relaciones desde candidatos_procesados_*.json
- ✅ Fusión de duplicados con preservación de ids_previos
- ✅ Eliminación de ruido biomédico
- ✅ Marcado de revisión ontológica (revision_estado)

### Frontend
- ✅ Visualización Cytoscape.js
- ✅ Filtros por tipo de nodo
- ✅ Buscador
- ✅ Panel lateral con detalle de relaciones
- ✅ Stats en header
- ✅ Proxy Vite → producción

### Tests
- ✅ 109 tests total (94 previos + 15 integración)
- ✅ Cobertura: firewall (64), integración (15), DB (10), imports (10), review (6), menu (5), extractor (3)

## Componentes No Implementados (Futuro)

| Componente | Prioridad | Notas |
|-----------|-----------|-------|
| GraphRAG | Baja | Requiere embeddings + vector store |
| Embeddings | Baja | Para búsqueda semántica |
| OpenAlex | Media | Enriquecimiento bibliográfico |
| Wikidata | Media | Enriquecimiento ontológico |
| Monitoreo | Baja | Logs ya existen, falta dashboard |

## Deuda Técnica

| Item | Impacto | Urgencia |
|------|---------|----------|
| check_models.py busca .env en scripts/ | Bajo | Baja |
| 376 nodos aislados en DB local | Medio | Media |
| ~535 candidatos pendientes de revisión | Medio | Alta |
| 19 relaciones sin evidencia (sin_evidencia) | Bajo | Baja |
| 120 relaciones con solo fuente (fuente_only) | Bajo | Baja |

## Certificación

El sistema implementa correctamente el Manifiesto Ontológico v1.1. El pipeline de extracción, validación, limpieza y exportación funciona de extremo a extremo. La DB local contiene 1401 nodos y 1071 relaciones. Los datos de producción en `frontend/public/datos.json` tienen 394 nodos y 371 relaciones (curados).

**Estado: APTO para uso continuo.**
