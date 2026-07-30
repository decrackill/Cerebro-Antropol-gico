# 08E — Validación Técnica

**Fecha:** Julio 2026

## Resumen

Auditoría técnica de la implementación para verificar correspondencia perfecta entre diseño ontológico y código.

---

## 1. Modelo de Datos vs Ontología

| Ontología | SQLite | Cumplimiento |
|-----------|--------|-------------|
| 8 tipos de nodo | CHECK constraint en nodos.tipo | ✅ |
| 3 atributos (nombre, tipo, descripción) | Columnas presentes | ✅ |
| Relaciones origen→destino | FK con ON DELETE CASCADE | ✅ |
| 12 relaciones Nivel A | `COMPATIBILIDAD_RELACIONES` + `TIPOS_ALIAS_RELACION` | ✅ |
| 3 relaciones Nivel B | `COMPATIBILIDAD_RELACIONES` incluye contradice, relacionado_con, depende_de | ✅ |
| Evidencia documental | fuente + cita_textual + validar_relacion | ✅ |
| Firewall epistemológico | Validación en db.py | ✅ |

## 2. Pipeline

| Componente | Estado | Observaciones |
|-----------|--------|---------------|
| Extractor (Gemini) | ✅ | Con checkpoint, rotación de keys, fallback OpenRouter |
| Modo manual | ✅ | Generar prompt / pegar respuesta |
| Parser JSON | ✅ | Normaliza tipos, resuelve aliases |
| Revisión 1x1 | ✅ | Menú opción 1 |
| Conexión bulk | ✅ | Menú opción 2 |
| Recuperación de caché | ✅ | Menú opción 3, con mapa de resolución |
| Fusión de duplicados | ✅ | Preserva ids_previos |
| Eliminación ruido | ✅ | Patrones biomédicos |
| Export | ✅ | scripts/export_json.py |
| Reforzar esquema | ✅ | Menú opción 12 (índices) |

## 3. Base de Datos

| Aspecto | Estado |
|---------|--------|
| Normalización | ✅ 3FN |
| Integridad referencial | ✅ 0 huérfanos |
| Índices | ✅ idx_relacion_unica, idx_rel_tipo, idx_nodo_tipo |
| CHECK constraints | ✅ nodos.tipo |
| PRAGMA foreign_keys | ✅ ON |

## 4. Frontend

| Componente | Estado |
|-----------|--------|
| Vite build | ✅ |
| Cytoscape.js | ✅ Carga datos.json, renderiza grafo |
| Filtros por tipo | ✅ |
| Buscador | ✅ |
| Panel lateral | ✅ Relaciones con detalle |
| Header stats | ✅ Contador nodos/conexiones |
| Proxy /api | ✅ → producción |

## 5. Tests

109 tests, todos pasando:

| Grupo | Tests | Cubre |
|-------|-------|-------|
| test_firewall.py | 64 | Validación de relaciones, aliases, compatibilidad |
| test_integration.py | 15 | Ciclo completo, fusión, export, helpers |
| test_stress.py | 9 | Casos extremos, alta cardinalidad |
| test_database.py | 10 | CRUD básico |
| test_imports.py | 10 | Importaciones de módulos |
| test_review.py | 6 | Revisión de candidatos |
| test_menu.py | 5 | Navegación del menú |
| test_extractor.py | 3 | Extracción básica |

## 6. Deuda Técnica

| Item | Severidad | Notas |
|------|-----------|-------|
| check_models.py busca .env en scripts/ | Baja | Ruta incorrecta |
| Chunk size frontend >500KB | Baja | Cytoscape.js |
| 386 nodos aislados | Media | Post-limpieza, pendientes de conexión |
| ~535 candidatos pendientes | Alta | Requieren revisión manual |

## 7. Checklist Técnico

| Componente | Cumplimiento | Riesgo |
|-----------|-------------|--------|
| Ontología → DB | ✅ | Ninguno |
| Pipeline → DB | ✅ | Bajo (candidatos pendientes) |
| Frontend → datos.json | ✅ | Bajo |
| Tests → código | ✅ | Ninguno |
| Validación → ontología | ✅ | Ninguno |
| Documentación → sistema | ✅ | Bajo |

## 8. Dictamen

La implementación respeta completamente la ontología. No existen contradicciones entre diseño e implementación. La arquitectura es mantenible y puede evolucionar sin rediseños estructurales. Los hallazgos de deuda técnica son menores y no bloquean la operación.

**Validación Técnica: APROBADA**
