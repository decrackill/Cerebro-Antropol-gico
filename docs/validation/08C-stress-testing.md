# 08C — Stress Testing Intelectual

**Fecha:** Julio 2026

## Resumen

Pruebas de falsación sistemática del modelo ontológico y la DB bajo escenarios extremos, casos límite y condiciones de borde.

---

## 1. Escenarios Probados

| Escenario | Tests | Resultado |
|-----------|-------|-----------|
| Autor con múltiples corrientes simultáneas | 1 | ✅ |
| Concepto redefinido 5 veces por distintos autores | 1 | ✅ |
| Obra colectiva con 10 autores | 1 | ✅ |
| Ciclo de relaciones A→B→C→A | 1 | ✅ |
| Concepto con 100 relaciones (alta cardinalidad) | 1 | ✅ |
| Nombres homónimos con distinto tipo | 1 | ✅ |
| Debate con 10 participantes de 3 tipos | 1 | ✅ |
| Citas contradictorias (mismo par, tipo distinto) | 1 | ✅ |
| Fusión de nodo con 50 relaciones | 1 | ✅ |

**Total: 9 stress tests, 9 passed**

## 2. Robustez del Modelo

| Aspecto | Comportamiento |
|---------|---------------|
| Cardinalidad alta | ✅ 100 relaciones al mismo nodo sin degradación |
| Ciclos en grafo | ✅ Permitidos por diseño (no es árbol) |
| Homonimia | ✅ Mismo nombre, tipos diferentes = nodos distintos |
| Contradicciones entre fuentes | ✅ `relacion_ya_existe` distingue por tipo |
| Fusión masiva | ✅ 50 relaciones redirigidas correctamente |
| Múltiples roles | ✅ Autor en 2 corrientes, obra con 10 autores |
| Debate multi-tipo | ✅ 3 tipos diferentes como participantes |

## 3. Límites Identificados

| Límite | Tipo | Mitigación |
|--------|------|-----------|
| Sin límite de relaciones por nodo | Arquitectónico | SQLite puede manejar millones |
| Sin límite de autores por obra | Ontológico | No necesario |
| Sin validación de contexto histórico | Epistemológico | Fuente + cita_textual preservan contexto |
| Sin detección automática de contradicciones | Funcional | Se registran ambas posturas |

## 4. Casos Imposibles (no representables)

| Caso | Razón | Impacto |
|------|-------|---------|
| Relaciones sin evidencia | Validación lo rechaza | Bajo (deseable) |
| Fusión poblacion↔cultura | EXCLUSIONES_FUSION | Bajo (deseable) |
| Relación no canónica | validar_relacion lo rechaza | Medio (Gemini inventa tipos) |

## 5. Dictamen

El sistema es robusto frente a escenarios extremos. Mantiene coherencia conceptual bajo alta cardinalidad, ciclos, contradicciones entre fuentes y fusión masiva. Los límites identificados están documentados y son aceptables para el dominio.

**Stress Testing: SUPERADO**
