# Plan de Validación Empírica — Hipótesis H1-H6

**Fecha**: 2026-07-21
**Estado**: Plan de ejecución — sin modificaciones al sistema

---

## Referencia

Este plan reutiliza el [EXTRACTION_ROADMAP.md](../reports/EXTRACTION_ROADMAP.md) como base.
Las hipótesis, umbrales de aceptación y criterios de decisión están definidos allí.

---

## Resumen de Hipótesis

| ID | Hipótesis | Requiere Datos | Prioridad |
|----|-----------|----------------|-----------|
| H1 | LLM inventa citas_textual | SÍ | ALTA |
| H2 | Conceptos sobreextraídos | SÍ | MEDIA |
| H3 | Debates subextraídos | SÍ | MEDIA |
| H4 | Chunking sin overlap pierde contexto | SÍ | BAJA |
| H5 | Sesgos ontológicos en relaciones | SÍ | MEDIA |
| H6 | SequenceMatcher insuficiente para duplicados | SÍ | BAJA |

---

## Protocolo General

### Selección de Libros

**Criterios**:
1. Al menos 3 subcampos distintos de antropología
2. Al menos 2 libros con debates conocidos
3. Al menos 1 libro con terminología técnica densa
4. Todos en español (idioma del prompt)

**Libros mínimos**: 5
**Libros recomendados**: 10

### Proceso por Libro

1. Crear backup de DB
2. Extraer libro completo
3. Revisar candidatos manualmente
4. Registrar métricas (ver [QUALITY_METRICS.md](QUALITY_METRICS.md))
5. No insertar en DB hasta completar revisión

### Muestreo para Revisión Manual

Para cada hipótesis que requiera revisión manual:
- Tomar muestra de 50-100 entidades/relaciones
- Revisar cada una contra el texto fuente
- Registrar verdaderos positivos y falsos positivos

---

## H1: LLM Inventa citations_textual

### Objetivo

Determinar porcentaje de citas textuales que coinciden con el texto fuente.

### Datos Necesarios

- 3 libros completos extraídos
- 100 relaciones con cita_textual (muestra)

### Procedimiento

1. Extraer 3 libros completos
2. Seleccionar 100 relaciones al azar que tengan `cita_textual`
3. Para cada relación:
   a. Identificar el chunk fuente (campo `fuente`: "libro.pdf, p.X-Y")
   b. Buscar la `cita_textual` en el texto del chunk
   c. Registrar: exacta / parcial / no encontrada
4. Calcular porcentaje de verificabilidad

### Métricas

| Métrica | Fórmula | Umbral |
|---------|---------|--------|
| % citas exactas | (citas exactas / total) × 100 | >80% |
| % citas verificables | (exactas + parciales / total) × 100 | >95% |
| % citas inventadas | (no encontradas / total) × 100 | <5% |

### Criterio de Aceptación

- **Se confirma H1**: Si % inventadas >5%
- **Se rechaza H1**: Si % inventadas ≤5%

### Tiempo Estimado

- Extracción: 3 horas (1h por libro)
- Revisión: 2 horas (muestreo y verificación)
- **Total**: ~5 horas

### Decisión

| Resultado | Acción |
|-----------|--------|
| H1 confirmada | Implementar P4 (validación de citas) en v1.3 |
| H1 rechazada | No se necesita acción |

---

## H2: Conceptos Sobreextraídos

### Objetivo

Determinar tasa de falsos positivos en extracción de conceptos.

### Datos Necesarios

- 5 libros completos extraídos
- 100 conceptos extraídos (muestra)

### Procedimiento

1. Extraer 5 libros completos
2. Seleccionar 100 conceptos al azar
3. Para cada concepto:
   a. Verificar que es un término establecido en antropología
   b. Verificar que existe fuera del libro (glosarios, Wikipedia, manuales)
   c. Verificar que se puede nombrar en 1-4 palabras
   d. Registrar: válido / cuestionable / inválido
4. Calcular tasa de falsos positivos

### Métricas

| Métrica | Fórmula | Umbral |
|---------|---------|--------|
| % conceptos válidos | (válidos / total) × 100 | >90% |
| % falsos positivos | (inválidos / total) × 100 | <10% |
| Promedio por capítulo | total / (# capítulos) | 2-8 |

### Criterio de Aceptación

- **Se confirma H2**: Si % falsos positivos >10%
- **Se rechaza H2**: Si % falsos positivos ≤10%

### Tiempo Estimado

- Extracción: 5 horas (1h por libro)
- Revisión: 4 horas (muestreo y verificación)
- **Total**: ~9 horas

### Decisión

| Resultado | Acción |
|-----------|--------|
| H2 confirmada | Implementar P9 (ejemplos negativos en prompt) en v1.3 |
| H2 rechazada | No se necesita acción |

---

## H3: Debates Subextraídos

### Objetivo

Determinar recall de extracción de debates (debates reales vs extraídos).

### Datos Necesarios

- 5 libros que contengan debates conocidos
- Lista de debates esperados por libro (preparada manualmente)

### Procedimiento

1. Seleccionar 5 libros con debates conocidos
2. Preparar lista de debates esperados (máximo 5 por libro)
3. Extraer cada libro
4. Contar cuántos debates se extrajeron
5. Calcular recall

### Métricas

| Métrica | Fórmula | Umbral |
|---------|---------|--------|
| Recall de debates | (debates extraídos / debates esperados) × 100 | >50% |
| F1 de debates | 2 × (precision × recall) / (precision + recall) | >0.4 |

### Criterio de Aceptación

- **Se confirma H3**: Si recall <50%
- **Se rechaza H3**: Si recall ≥50%

### Tiempo Estimado

- Preparación: 2 horas (lista de debates esperados)
- Extracción: 5 horas (1h por libro)
- Revisión: 3 horas
- **Total**: ~10 horas

### Decisión

| Resultado | Acción |
|-----------|--------|
| H3 confirmada | Implementar P5 (ejemplos de debates en prompt) en v1.3 |
| H3 rechazada | No se necesita acción |

---

## H4: Chunking Sin Overlap Pierde Contexto

### Objetivo

Determinar si el overlap entre chunks mejora la calidad de extracción.

### Datos Necesarios

- 1 libro procesado dos veces (con y sin overlap)
- Misma configuración de API y prompts

### Procedimiento

1. Seleccionar 1 libro (recomendado: libro largo, >200 páginas)
2. Extraer con configuración actual (sin overlap)
3. Anotar: nodos, relaciones, tiempo
4. **NOTA**: No se puede modificar el código. Este experimento requiere:
   - Opción A: Extraer el mismo libro dos veces y comparar (no hay variación)
   - Opción B: Hipótesis no testeable sin modificar código
5. **Decisión**: Esta hipótesis NO puede validarse sin modificar `dividir_en_chunks()`

### Limitación

**H4 no es testeable con el sistema actual**. El código no tiene parámetro de overlap.

### Alternativa

Evaluar H4 indirectamente:
1. Revisar las relaciones extraídas
2. Buscar conceptos que aparecen en un chunk pero se usan en otro
3. Si se encuentran muchos casos → H4 es relevante
4. Si se encuentran pocos casos → H4 es menos relevante

### Tiempo Estimado

- Revisión indirecta: 2 horas

### Decisión

| Resultado | Acción |
|-----------|--------|
| Muchos casos encontrados | Priorizar P3 en v1.2 |
| Pocos casos encontrados | Postergar P3 |

---

## H5: Sesgos Ontológicos en Relaciones

### Objetivo

Determinar si la distribución de tipos de relación es equilibrada.

### Datos Necesarios

- 10 libros completos extraídos
- Conteo de tipos de relación por libro

### Procedimiento

1. Extraer 10 libros completos
2. Para cada libro, contar distribución de tipos de relación
3. Calcular distribución promedio
4. Comparar con distribución esperada (basada en dominio)

### Métricas

| Métrica | Fórmula | Umbral |
|---------|---------|--------|
| % máximo por tipo | max(count_tipo) / total × 100 | <30% |
| Shannon entropy | -Σ(p × log(p)) | >2.0 |
| Tipos con 0 instancias | count(tipos con 0) | <3 |

### Distribución Esperada (referencia)

| Tipo | % Esperado |
|------|-----------|
| autor_de | 15-25% |
| influenciado_por | 15-25% |
| estudia_a | 10-20% |
| desarrolla_concepto | 10-20% |
| critica_a | 5-15% |
| pertenece_a | 5-10% |
| parte_del_debate | 3-8% |
| Otros | <5% cada uno |

### Criterio de Aceptación

- **Se confirma H5**: Si algún tipo >30% o Shannon entropy <2.0
- **Se rechaza H5**: Si todos los tipos <30% y Shannon entropy ≥2.0

### Tiempo Estimado

- Extracción: 10 horas (1h por libro)
- Análisis: 2 horas
- **Total**: ~12 horas

### Decisión

| Resultado | Acción |
|-----------|--------|
| H5 confirmada | Ajustar prompt para equilibrar distribución en v1.3 |
| H5 rechazada | No se necesita acción |

---

## H6: SequenceMatcher Insuficiente

### Objetivo

Determinar si `SequenceMatcher` falla en detectar duplicados con variantes de acentos.

### Datos Necesarios

- 1 libro extraído
- Búsqueda de pares de nombres con acentos diferentes

### Procedimiento

1. Extraer 1 libro
2. Buscar en la DB pares de nombres que:
   - Tengan el mismo tipo
   - Difieran solo en acentos/tildes (ej: "Lévi-Strauss" vs "Levi-Strauss")
3. Verificar si `detectar_duplicados()` los detectó
4. Calcular tasa de no-detección

### Métricas

| Métrica | Fórmula | Umbral |
|---------|---------|--------|
| % duplicados detectados | (detectados / total duplicados) × 100 | >95% |
| % duplicados no detectados | (no detectados / total duplicados) × 100 | <5% |

### Criterio de Aceptación

- **Se confirma H6**: Si % no detectados >5%
- **Se rechaza H6**: Si % no detectados ≤5%

### Tiempo Estimado

- Extracción: 1 hora
- Búsqueda: 1 hora
- **Total**: ~2 horas

### Decisión

| Resultado | Acción |
|-----------|--------|
| H6 confirmada | Implementar P6 (normalización Unicode) en v1.3 |
| H6 rechazada | No se necesita acción |

---

## Resumen de Tiempos

| Hipótesis | Libros | Tiempo Total |
|-----------|--------|--------------|
| H1 | 3 | 5 horas |
| H2 | 5 | 9 horas |
| H3 | 5 | 10 horas |
| H4 | 1 | 2 horas |
| H5 | 10 | 12 horas |
| H6 | 1 | 2 horas |
| **Total** | **10-15 libros** | **~40 horas** |

**Nota**: Algunos libros pueden reutilizarse entre hipótesis. El tiempo real puede ser menor.

---

## Orden de Ejecución Recomendado

1. **H6** (2h) — Más rápido, resultado inmediato
2. **H4** (2h) — Revisión indirecta
3. **H1** (5h) — Mayor prioridad
4. **H2** (9h) — Requiere más libros
5. **H3** (10h) — Requiere libros específicos
6. **H5** (12h) — Requiere más libros

---

## Registro de Resultados

Los resultados de cada hipótesis se registrarán en:

```
runtime/state/hipotesis_resultados.json
```

Formato:
```json
{
  "H1": {
    "estado": "confirmada|rechazada",
    "fecha": "2026-XX-XX",
    "metrica_principal": 0.0,
    "datos": { ... }
  },
  ...
}
```
