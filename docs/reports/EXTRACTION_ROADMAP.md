# Roadmap de Evolución — Sistema de Extracción

**Fecha**: 2026-07-21
**Versión actual**: v1.1
**Estado**: Plan de evolución — sin modificaciones al código

---

## Clasificación de Observaciones

Cada hallazgo de la auditoría se clasifica en una de tres categorías:

- **EVIDENCIA**: Demostrado por inspección del código, medición directa o pruebas ejecutadas.
- **HIPÓTESIS**: Razonable pero requiere validación empírica (mediciones reales, experimentos con datos).
- **PROPUESTA**: Mejora propuesta que requiere diseño e implementación.

---

## 1. Observaciones Basadas en Evidencia

Estas afirmaciones están demostradas por inspección del código o pruebas.

### E1. Firewall epistemológico está completo y correcto

- **Evidencia**: Inspección de `db.py:179-201`. Todas las funciones de validación existen y son llamadas desde `validar_relacion()`.
- **Verificación**: Tests `test_firewall.py` (60 tests) cubren todas las reglas.
- **Conclusión**: No requiere acción.

### E2. Todos los caminos de inserción de relaciones pasan por `validar_relacion()`

- **Evidencia**: Inspección de `revision.py:214`, `revision.py:319`, `limpieza.py:303`.
- **Verificación**: Los caminos que NO insertan relaciones (`herramienta_revision_total`, `herramienta_limpieza_asistida`) solo modifican nodos.
- **Conclusión**: No requiere acción.

### E3. La revisión manual es interactiva y no automatizable

- **Evidencia**: Inspección de `revision.py:36-231`. La función `herramienta_revisar()` usa `input()` y `pedir_opcion()` en cada iteración.
- **Verificación**: No existe ningún parámetro `--auto` o `--batch`.
- **Conclusión**: Requiere nueva funcionalidad (v1.2).

### E4. `detectar_duplicados()` es O(n²) por tipo

- **Evidencia**: Inspección de `utils.py:68-84`. Doble loop anidado sobre `items`.
- **Verificación**: Complejidad teórica confirmada por análisis de código.
- **Conclusión**: Requiere optimización con datos reales (v1.2).

### E5. `_validar_firewall_poblacion()` y `_validar_compatibilidad_nodos()` ejecutan queries repetidas

- **Evidencia**: Inspección de `db.py:186` y `db.py:210`. Ambas funciones ejecutan `SELECT id, tipo FROM nodos` en cada llamada.
- **Verificación**: `validar_relacion()` llama a ambos validadores secuencialmente.
- **Conclusión**: Requiere caché (v1.2).

### E6. `revision.py` tiene 453 líneas y mezcla responsabilidades

- **Evidencia**: Inspección directa del archivo. Mezcla UI (input/output), lógica de negocio, y persistencia.
- **Verificación**: Imports condicionales en línea 353.
- **Conclusión**: Refactorización necesaria (v1.3).

### E7. Hay 48 aliases de tipos de relación definidos

- **Evidencia**: Conteo directo de `config.py:50-98`.
- **Verificación**: Cobertura razonable de variaciones lingüísticas.
- **Conclusión**: Monitorear en uso real.

### E8. El catálogo de nodos se carga una vez por sesión de extracción

- **Evidencia**: Inspección de `extractor.py:109-122` (`cargar_nodos_existentes()`) y `extractor.py:302` (llamada única).
- **Verificación**: correcto para la sesión actual, pero los nodos extraídos en chunks anteriores solo están en `nodos_acumulados`.
- **Conclusión**: Limitación conocida del diseño actual.

---

## 2. Hipótesis Requeren Validación Empírica

Estas afirmaciones son razonables pero no están demostradas. Requieren experimentos con datos reales.

### H1. El LLM puede inventar `cita_textual`

- **Hipótesis**: El LLM genera citas que no existen en el texto fuente.
- **Por qué es razonable**: Los LLMs son conocidos por alucinar. No hay verificación cruzada en el pipeline.
- **Cómo validar**:
  1. Tomar 100 relaciones extraídas de un libro real.
  2. Buscar cada `cita_textual` en el texto fuente del chunk correspondiente.
  3. Medir % de citas que coinciden exactamente.
- **Umbral de aceptación**: >95% de citas verificables.
- **Si se confirma**: Implementar validación de citas (v1.3).
- **Si NO se confirma**: No se necesita acción.
- **Prioridad**: ALTA — Si se confirma, es un problema epistemológico serio.

### H2. Los conceptos están sobreextraídos

- **Hipótesis**: El LLM extrae más conceptos de los que debería (falsos positivos).
- **Por qué es razonable**: El prompt da un rango de "2-8 conceptos por capítulo" pero no hay métricas reales.
- **Cómo validar**:
  1. Extraer un libro completo (10+ capítulos).
  2. Contar conceptos extraídos por capítulo.
  3. Comparar con el rango esperado (2-8).
  4. Revisar manualmente una muestra de 20 conceptos.
- **Umbral de aceptación**: <10% de falsos positivos en muestra.
- **Si se confirma**: Ajustar prompt o agregar filtro post-extracción (v1.3).
- **Si NO se confirma**: No se necesita acción.
- **Prioridad**: MEDIA — Afecta calidad del grafo.

### H3. Los debates están subextraídos

- **Hipótesis**: El tipo `debate` rara vez aparece en las extracciones.
- **Por qué es razonable**: El prompt no da ejemplos concretos de debates antropológicos.
- **Cómo validar**:
  1. Extraer 5 libros que contengan debates conocidos.
  2. Contar cuántos debates se extraen vs cuántos existen realmente.
  3. Calcular recall (debates extraídos / debates totales).
- **Umbral de aceptación**: >50% de recall.
- **Si se confirma**: Agregar ejemplos de debates al prompt (v1.3).
- **Si NO se confirma**: No se necesita acción.
- **Prioridad**: MEDIA — Afecta completitud del grafo.

### H4. El chunking sin overlap pierde relaciones跨页

- **Hipótesis**: Conceptos definidos al final de un chunk y usados al inicio del siguiente pierden contexto.
- **Por qué es razonable**: No hay superposición entre chunks.
- **Cómo validar**:
  1. Extraer un libro con y sin overlap (10%).
  2. Comparar entidades y relaciones extraídas.
  3. Medir diferencias.
- **Umbral de aceptación**: Diferencia <5% entre versiones.
- **Si se confirma**: Agregar overlap (v1.2).
- **Si NO se confirma**: No se necesita acción.
- **Prioridad**: BAJA — Afecta marginalmente la calidad.

### H5. Los sesgos ontológicos en relaciones son significativos

- **Hipótesis**: El LLM favorece `desarrolla_concepto` sobre `critica_a` y `parte_del_debate`.
- **Por qué es razonable**: Los LLMs tienden a relaciones "positivas".
- **Cómo validar**:
  1. Extraer 10 libros.
  2. Contar distribución de tipos de relación.
  3. Comparar con distribución esperada (basada en dominio).
- **Umbral de aceptación**: Ningún tipo con >30% del total (excluyendo autor_de).
- **Si se confirma**: Ajustar prompt o agregar pesos (v1.3).
- **Si NO se confirma**: No se necesita acción.
- **Prioridad**: MEDIA — Afecta equilibrio del grafo.

### H6. La detección de duplicados con SequenceMatcher es insuficiente

- **Hipótesis**: "Lévi-Strauss" y "Levi-Strauss" no se detectan como duplicados.
- **Por qué es razonable**: `SequenceMatcher` no normaliza Unicode ni maneja acentos.
- **Cómo validar**:
  1. Buscar en la DB actual pares de nombres que difieran solo en acentos/tildes.
  2. Contar cuántos no se detectaron.
- **Umbral de aceptación**: <5% de duplicados no detectados.
- **Si se confirma**: Agregar normalización Unicode (v1.3).
- **Si NO se confirma**: No se necesita acción.
- **Prioridad**: BAJA — Afecta marginalmente la limpieza.

---

## 3. Propuestas de Mejora

Estas son mejoras propuestas que requieren diseño e implementación.

### P1. Modo de revisión automática

- **Descripción**: Crear `herramienta_revision_automatica()` que apruebe/rechace candidatos basándose en reglas.
- **Reglas propuestas**:
  - Confianza "alta" + no duplicado → auto-aprobar
  - Confianza "baja" → auto-rechazar
  - Duplicado fuzzy >0.90 → auto-rechazar
  - Confianza "media" → revisión manual
- **Impacto**: CRÍTICO — Permite escalar a cientos de libros.
- **Esfuerzo**: 1 semana (diseño + implementación + tests).
- **Riesgo**: MEDIO — Puede aprobar nodos incorrectos si las reglas son demasiado permisivas.
- **Dependencias**: Ninguna.
- **Requiere datos previos**: NO — Se puede implementar ahora.
- **Versión**: v1.2

### P2. Caché de tipos_nodo en validación

- **Descripción**: Cargar `tipos_nodo` una vez en `validar_relacion()` y pasar como parámetro a los validadores.
- **Impacto**: ALTO — Reduce queries de O(n) a O(1) por validación.
- **Esfuerzo**: 30 minutos.
- **Riesgo**: BAJO — Cambio mínimo con alto beneficio.
- **Dependencias**: Ninguna.
- **Requiere datos previos**: NO.
- **Versión**: v1.2

### P3. Overlap en chunking

- **Descripción**: Agregar 10-20% de superposición entre chunks.
- **Implementación**: Cada chunk incluye las últimas N líneas del chunk anterior.
- **Impacto**: MEDIO — Mejora contexto跨页.
- **Esfuerzo**: 1-2 horas.
- **Riesgo**: BAJO — Solo afecta extracción, no inserción.
- **Dependencias**: Requiere validación empírica (H4).
- **Requiere datos previos**: SÍ — Confirmar que el overlap mejora calidad antes de implementar.
- **Versión**: v1.2 (si H4 se confirma).

### P4. Validación de citas_textual

- **Descripción**: Después de la extracción, verificar que cada `cita_textual` exista en el chunk fuente.
- **Implementación**: Búsqueda de substring con tolerancia a variaciones menores.
- **Impacto**: ALTO — Previene alucinaciones epistemológicas.
- **Esfuerzo**: 1-2 días.
- **Riesgo**: MEDIO — Puede rechazar citas válidas que el LLM parafraseó levemente.
- **Dependencias**: Requiere validación empírica (H1).
- **Requiere datos previos**: SÍ — Confirmar que H1 es un problema real.
- **Versión**: v1.3 (si H1 se confirma).

### P5. Mejorar prompts para `debate`

- **Descripción**: Agregar ejemplos concretos de debates antropológicos al prompt.
- **Ejemplos propuestos**: "funcionalismo vs estructuralismo", "evolucionismo vs particularismo".
- **Impacto**: MEDIO — Mejora cobertura ontológica.
- **Esfuerzo**: 1 hora.
- **Riesgo**: BAJO — Solo agrega ejemplos al prompt.
- **Dependencias**: Requiere validación empírica (H3).
- **Requiere datos previos**: SÍ — Confirmar que H3 es un problema real.
- **Versión**: v1.3 (si H3 se confirma).

### P6. Normalización de nombres (Unicode)

- **Descripción**: Normalizar nombres para detectar duplicados con variantes de acentos/tildes.
- **Implementación**: `unicodedata.normalize('NFKD', nombre)` + filtro de combining characters.
- **Impacto**: BAJO — Mejora detección de duplicados.
- **Esfuerzo**: 1-2 horas.
- **Riesgo**: BAJO — Solo afecta detección de duplicados.
- **Dependencias**: Requiere validación empírica (H6).
- **Requiere datos previos**: SÍ — Confirmar que H6 es un problema real.
- **Versión**: v1.3 (si H6 se confirma).

### P7. Dividir `revision.py`

- **Descripción**: Separar en `revision_manual.py`, `conexion_automatica.py`, `revision_total.py`.
- **Impacto**: BAJO — Mejora mantenibilidad.
- **Esfuerzo**: 2-3 horas.
- **Riesgo**: BAJO — Refactorización mecánica.
- **Dependencias**: Ninguna.
- **Requiere datos previos**: NO.
- **Versión**: v1.3.

### P8. Índices SQL para tipos

- **Descripción**: Agregar `CREATE INDEX idx_nodo_tipo ON nodos(tipo)`.
- **Impacto**: MEDIO — Acelera queries por tipo.
- **Esfuerzo**: 5 minutos.
- **Riesgo**: BAJO — Solo lectura.
- **Dependencias**: Ninguna.
- **Requiere datos previos**: NO.
- **Versión**: v1.2.

### P9. Prompt con ejemplos negativos

- **Descripción**: Agregar al prompt ejemplos concretos de lo que el LLM NO debe extraer.
- **Impacto**: MEDIO — Reduce falsos positivos.
- **Esfuerzo**: 1 hora.
- **Riesgo**: BAJO — Solo agrega texto al prompt.
- **Dependencias**: Requiere validación empírica (H2).
- **Requiere datos previos**: SÍ — Confirmar que H2 es un problema real.
- **Versión**: v1.3 (si H2 se confirma).

### P10. Métricas de calidad automáticas

- **Descripción**: Script que mida calidad de extracción (distribución de tipos, % de nodos aislados, etc.).
- **Impacto**: MEDIO — Permite monitoreo continuo.
- **Esfuerzo**: 1 día.
- **Riesgo**: BAJO — Solo lectura.
- **Dependencias**: Ninguna.
- **Requiere datos previos**: NO.
- **Versión**: v1.3.

---

## 4. Plan por Versión

### v1.2 — Optimización y Escalabilidad Básica

**Objetivo**: Preparar el sistema para procesar 20-50 libros.

| # | Cambio | Tipo | Impacto | Esfuerzo | Requiere Datos |
|---|--------|------|---------|----------|----------------|
| P1 | Modo de revisión automática | PROPUESTA | Crítico | 1 semana | NO |
| P2 | Caché de tipos_nodo | PROPUESTA | Alto | 30 min | NO |
| P8 | Índices SQL | PROPUESTA | Medio | 5 min | NO |
| P3 | Overlap en chunking | PROPUESTA | Medio | 1-2h | SÍ (H4) |

**Fecha estimada**: Después de procesar 5 libros y validar H4.

**Criterio de salida**:
- [ ] `herramienta_revision_automatica()` implementada y testeada
- [ ] `validar_relacion()` usa caché de tipos_nodo
- [ ] Índice `idx_nodo_tipo` creado
- [ ] H4 validada (overlap es/necesario)

### v1.3 — Calidad y Mantenibilidad

**Objetivo**: Mejorar calidad de extracción y preparar para 100+ libros.

| # | Cambio | Tipo | Impacto | Esfuerzo | Requiere Datos |
|---|--------|------|---------|----------|----------------|
| P4 | Validación de citas_textual | PROPUESTA | Alto | 1-2 días | SÍ (H1) |
| P5 | Mejorar prompts para debate | PROPUESTA | Medio | 1h | SÍ (H3) |
| P9 | Prompt con ejemplos negativos | PROPUESTA | Medio | 1h | SÍ (H2) |
| P6 | Normalización Unicode | PROPUESTA | Bajo | 1-2h | SÍ (H6) |
| P7 | Dividir revision.py | PROPUESTA | Bajo | 2-3h | NO |
| P10 | Métricas de calidad | PROPUESTA | Medio | 1 día | NO |

**Fecha estimada**: Después de procesar 20 libros y validar H1, H2, H3, H6.

**Criterio de salida**:
- [ ] H1 validada → P4 implementada (o descartada)
- [ ] H2 validada → P9 implementada (o descartada)
- [ ] H3 validada → P5 implementada (o descartada)
- [ ] H6 validada → P6 implementada (o descartada)
- [ ] `revision.py` dividido en módulos
- [ ] Métricas de calidad implementadas

### v2.0 — Escalabilidad Completa

**Objetivo**: Procesar 500+ libros de forma semi-automática.

**Requisitos previos**:
- v1.2 y v1.3 completados
- 50+ libros procesados
- Métricas de calidad estables

**Cambios planeados** (detalles a definir cuando se llegue):
- Pipeline de revisión automática con ML (clustering de entidades)
- Deduplicación semántica (embeddings)
- Procesamiento distribuido
- Dashboard de métricas

**Fecha estimada**: Depende de la velocidad de procesamiento de v1.2/v1.3.

---

## 5. Tabla Resumen de Decisiones

| Observación | Clasificación | Requiere Datos | Versión | Decisión |
|-------------|---------------|----------------|---------|----------|
| Firewall completo | EVIDENCIA | NO | — | No hacer nada |
| Inserciones pasan por validar_relacion() | EVIDENCIA | NO | — | No hacer nada |
| Revisión manual interactiva | EVIDENCIA | NO | v1.2 | Implementar P1 |
| O(n²) en duplicados | EVIDENCIA | NO | v1.2 | Optimizar con P2 |
| Queries repetidas en validación | EVIDENCIA | NO | v1.2 | Caché con P2 |
| revision.py demasiado grande | EVIDENCIA | NO | v1.3 | Dividir con P7 |
| 48 aliases definidos | EVIDENCIA | NO | — | Monitorear |
| Catálogo se carga por sesión | EVIDENCIA | NO | — | Limitación conocida |
| LLM inventa citas_textual | HIPÓTESIS | SÍ (H1) | v1.3 | P4 si se confirma |
| Conceptos sobreextraídos | HIPÓTESIS | SÍ (H2) | v1.3 | P9 si se confirma |
| Debates subextraídos | HIPÓTESIS | SÍ (H3) | v1.3 | P5 si se confirma |
| Chunking sin overlap pierde contexto | HIPÓTESIS | SÍ (H4) | v1.2 | P3 si se confirma |
| Sesgos ontológicos en relaciones | HIPÓTESIS | SÍ (H5) | v1.3 | Ajustar prompt |
| SequenceMatcher insuficiente | HIPÓTESIS | SÍ (H6) | v1.3 | P6 si se confirma |

---

## 6. Cómo Validar las Hipótesis

### Protocolo General

1. **Seleccionar 5-10 libros** de diferentes subcampos de antropología.
2. **Extraer cada libro completo** con el pipeline actual.
3. **Revisar manualmente una muestra** de 50-100 entidades por libro.
4. **Medir métricas** específicas para cada hipótesis.
5. **Decidir** si la hipótesis se confirma.

### Métricas a Medir

| Hipótesis | Métrica | Umbral | Cómo Medir |
|-----------|---------|--------|------------|
| H1 | % citas verificables | >95% | Búsqueda substring en chunk |
| H2 | % falsos positivos en conceptos | <10% | Revisión manual de muestra |
| H3 | Recall de debates | >50% | Contar debates reales vs extraídos |
| H4 | Diferencia con/sin overlap | <5% | Extraer mismo libro dos veces |
| H5 | Distribución de tipos | Ninguno >30% | Contar por tipo |
| H6 | Duplicados no detectados | <5% | Buscar pares por acentos |

### Costo Estimado de Validación

| Hipótesis | Libros Necesarios | Tiempo Estimado |
|-----------|-------------------|-----------------|
| H1 | 3 | 2 horas |
| H2 | 5 | 4 horas |
| H3 | 5 | 3 horas |
| H4 | 1 (extraído 2 veces) | 1 hora |
| H5 | 10 | 5 horas |
| H6 | 1 | 1 hora |

**Total estimado**: ~16 horas de trabajo para validar todas las hipótesis.

---

## 7. Regla de Decisión

> **No implementar mejoras basadas en hipótesis hasta que los datos las confirmen.**

Cada hipótesis (H1-H6) tiene un umbral de aceptación definido. Solo se implementa la propuesta correspondiente si la hipótesis se confirma con datos reales.

**Excepción**: P1 (revisión automática), P2 (caché), P7 (dividir revision.py), P8 (índices SQL), y P10 (métricas) NO dependen de hipótesis. Se implementan directamente en v1.2/v1.3.

---

## 8. Resumen Ejecutivo

| Versión | Objetivo | Cambios Clave | Requiere Datos |
|---------|----------|---------------|----------------|
| **v1.2** | Escalabilidad básica (20-50 libros) | Revisión automática, caché, índices, overlap (si H4) | H4 |
| **v1.3** | Calidad y mantenibilidad (100+ libros) | Validación de citas, prompts, Unicode, refactorizar | H1, H2, H3, H6 |
| **v2.0** | Escalabilidad completa (500+ libros) | ML, embeddings, distribuido | v1.2 + v1.3 completados |

**Próximo paso inmediato**: Ejecutar el protocolo de validación de hipótesis (sección 6) con 5-10 libros reales.
