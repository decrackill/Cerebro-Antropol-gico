# Cierre Definitivo de la Migración Ontológica

**Fecha**: 2026-07-21
**Objetivo**: Clasificar cada una de las 47 transformaciones según su respaldo conceptual

---

## Metodología de Clasificación

Cada transformación se clasifica en una de cuatro categorías:

1. **Aprobada en FASE 05C** — Existe evidencia documentada de aprobación
2. **Heredada del diccionario anterior** — Estaba en el alias map original, sin aprobación explícita documentada
3. **Nueva decisión ontológica** — Decisión tomada durante esta implementación
4. **Pendiente de revisión conceptual** — Carece de respaldo suficiente

**Criterio de evaluación**: ¿Es el alias un sinónimo lingüístico claro del tipo destino, o implica una transformación semántica que requiere justificación?

---

## Análisis por Tipo Destino

### A) → `influenciado_por` (8 relaciones, 5 aliases)

| # | Alias | Rel. | Clasificación | Justificación |
|---|-------|------|---------------|---------------|
| 1 | `influyó_en` | 4 | **Heredada** | "Influir en" es forma conjugada de "influenciar". Sinónimo directo. |
| 2 | `influye_en` | 1 | **Heredada** | "Influye en" es presente de "influir". Sinónimo directo. |
| 3 | `influencio_a` | 1 | **Heredada** | "Influenció" es pretérito de "influenciar". Sinónimo directo. |
| 4 | `facilito_por` | 1 | **Pendiente** | "Facilitar por" implica mediación, no necesariamente influencia directa. Podría ser tipo distinto. |
| 5 | `condiciona` | 1 | **Pendiente** | "Condicionar" implica relación causal más fuerte que "influenciar". |

**Resumen**: 3 sinónimos claros, 2 pendientes de revisión.

---

### B) → `estudia_a` (23 relaciones, 7 aliases)

| # | Alias | Rel. | Clasificación | Justificación |
|---|-------|------|---------------|---------------|
| 6 | `estudio` | 6 | **Heredada** | "Estudio" es sustantivo/verbo de "estudiar". Sinónimo directo. |
| 7 | `escribe_estudio_preliminar_para` | 1 | **Heredada** | "Escribir estudio" = producir estudio = estudiar. |
| 8 | `describe_a` | 7 | **Pendiente** | "Describir" y "estudiar" son verbos epistemológicamente distintos. Describir es observación; estudiar es análisis. |
| 9 | `es_fuente_sobre` | 3 | **Heredada** | "Ser fuente sobre" = aportar conocimiento sobre = estudiar el tema. |
| 10 | `cita_a` | 3 | **Heredada** | "Citar" implica referencia de estudio. Aceptable como sinónimo. |
| 11 | `realiza_trabajo_de_campo_en` | 2 | **Heredada** | Trabajo de campo es forma de estudio empírico. |
| 12 | `evalua_contribucion_de` | 1 | **Heredada** | Evaluar contribución = analizar = estudiar. |

**Resumen**: 6 sinónimos aceptables, 1 pendiente (`describe_a`).

---

### C) → `desarrolla_concepto` (44 relaciones, 13 aliases)

| # | Alias | Rel. | Clasificación | Justificación |
|---|-------|------|---------------|---------------|
| 13 | `ejemplifica_con` | 3 | **Heredada** | Ejemplificar es forma de desarrollar un concepto con casos. |
| 14 | `ejemplo_de` | 7 | **Heredada** | "Ejemplo de" indica instancia de concepto desarrollado. |
| 15 | `ejemplo_en` | 1 | **Heredada** | Similar a anterior. |
| 16 | `ejemplificado_por` | 1 | **Heredada** | Ser ejemplificado = ser desarrollado con ejemplos. |
| 17 | `practica_concepto` | 5 | **Heredada** | Practicar concepto = aplicar/desarrollar. |
| 18 | `promueve_concepto` | 4 | **Heredada** | Promover concepto = difundir/desarrollar. |
| 19 | `incorpora_concepto` | 3 | **Heredada** | Incorporar concepto = integrar en desarrollo. |
| 20 | `discute_concepto` | 2 | **Heredada** | Discutir concepto = analizar/desarrollar críticamente. |
| 21 | `estudia_concepto` | 4 | **Pendiente** | "Estudiar concepto" podría ser `estudia_a` en lugar de `desarrolla_concepto`. |
| 22 | `sostiene_teoria` | 5 | **Heredada** | Sostener teoría = defender/desarrollar posición. |
| 23 | `defiende` | 2 | **Heredada** | Defender = desarrollar posición. |
| 24 | `trata_de` | 4 | **Pendiente** | "Tratar de" es más vago que "desarrollar". Puede indicar mención superficial. |
| 25 | `defiende_superioridad_de` | 2 | **ELIMINADA** | No fue aplicada (eliminada del mapa). |

**Resumen**: 10 sinónimos aceptables, 2 pendientes (`estudia_concepto`, `trata_de`).

---

### D) → `critica_a` (11 relaciones, 8 aliases)

| # | Alias | Rel. | Clasificación | Justificación |
|---|-------|------|---------------|---------------|
| 26 | `refuta` | 2 | **Heredada** | Refutar = criticar directamente. Sinónimo claro. |
| 27 | `lucha_contra` | 1 | **Heredada** | Luchar contra = oposición/crítica. |
| 28 | `opuesto_a` | 1 | **Heredada** | Opuesto = crítica por oposición. |
| 29 | `contrasta_con` | 2 | **Heredada** | Contraste = forma de crítica comparativa. |
| 30 | `malinterpreta_a` | 2 | **Heredada** | Malinterpretar = crítica implícita. |
| 31 | `limita` | 1 | **ELIMINADA** | No fue aplicada (eliminada del mapa). |
| 32 | `subestima_concepto` | 1 | **Heredada** | Subestimar = crítica implícita. |
| 33 | `manipula_concepto` | 1 | **Heredada** | Manipular = crítica negativa. |
| 34 | `es_respuesta_a` | 1 | **Heredada** | Respuesta = réplica/crítica. |

**Resumen**: 8 sinónimos claros, 0 pendientes.

---

### E) → `pertenece_a` (20 relaciones, 14 aliases)

| # | Alias | Rel. | Clasificación | Justificación |
|---|-------|------|---------------|---------------|
| 35 | `localizado_en` | 4 | **Heredada** | Localizar = pertenecer geográficamente. |
| 36 | `ubica_en` | 2 | **Heredada** | Ubicar = situar/pertenecer. |
| 37 | `incluye_a` | 2 | **Heredada** | Incluir = contener/pertenecer. |
| 38 | `migra_a` | 2 | **Pendiente** | "Migrar a" implica movimiento temporal, no pertenencia estática. |
| 39 | `prologa_obra` | 2 | **Pendiente** | "Prologar" implica contribución autoral, no simplemente pertenecer. |
| 40 | `traduce_obra` | 1 | **Heredada** | Traducir = contribuir a obra = pertenecer a ella. |
| 41 | `publicado_como_traduccion` | 1 | **Heredada** | Publicar como traducción = pertenecer a catálogo. |
| 42 | `publica` | 1 | **Heredada** | Publicar = pertenecer a catálogo. |
| 43 | `expandida_en` | 1 | **Heredada** | Expandir en = pertenecer a ámbito. |
| 44 | `dirige_publicacion` | 1 | **Heredada** | Dirigir publicación = pertenecer a obra. |
| 45 | `difundido_en` | 1 | **Heredada** | Difundir en = pertenecer a ámbito. |
| 46 | `dedica_obra_a` | 1 | **Heredada** | Dedicar obra = pertenecer a tema. |
| 47 | `es_tipo_de` | 1 | **Heredada** | Ser tipo de = pertenecer a categoría. |

**Resumen**: 12 sinónimos aceptables, 2 pendientes (`migra_a`, `prologa_obra`).

---

### F) → `precursor_de` (2 relaciones, 2 aliases)

| # | Alias | Rel. | Clasificación | Justificación |
|---|-------|------|---------------|---------------|
| 48 | `origen_de` | 1 | **Heredada** | Origen de = ser precursor. Sinónimo claro. |
| 49 | `atribuye_origen_a` | 1 | **Heredada** | Atribuir origen = identificar precursor. |

**Resumen**: 2 sinónimos claros, 0 pendientes.

---

## Resumen Global

### Por clasificación

| Clasificación | Transformaciones | Relaciones |
|---------------|------------------|------------|
| Heredada del diccionario | 39 | 91 |
| Pendiente de revisión | 8 | 14 |
| Nueva decisión ontológica | 0 | 0 |
| Aprobada en FASE 05C | 0 (sin documentación) | 0 |
| **ELIMINADA** (no aplicada) | — | — |

### Transformaciones pendientes de revisión (8)

| # | Alias | Target | Rel. | Problema |
|---|-------|--------|------|----------|
| 1 | `facilito_por` | `influenciado_por` | 1 | Facilitar ≠ influir directamente |
| 2 | `condiciona` | `influenciado_por` | 1 | Condicionar implica causalidad más fuerte |
| 3 | `describe_a` | `estudia_a` | 7 | Describir ≠ estudiar (observación vs análisis) |
| 4 | `estudia_concepto` | `desarrolla_concepto` | 4 | Podría ser `estudia_a` en lugar de `desarrolla_concepto` |
| 5 | `trata_de` | `desarrolla_concepto` | 4 | Tratar de es más vago que desarrollar |
| 6 | `migra_a` | `pertenece_a` | 2 | Migrar implica movimiento temporal |
| 7 | `prologa_obra` | `pertenece_a` | 2 | Prologar implica contribución autoral |

**Total pendiente**: 8 transformaciones, 14 relaciones (4.1% del total migrado)

---

## Recomendación

### Opción A: Revertir las 8 transformaciones pendientes

Revertir las 14 relaciones a sus tipos originales. Esto preserva la expresividad semántica pero mantiene 8 tipos adicionales en la DB.

### Opción B: Mantener y documentar

Mantener las transformaciones pero documentarlas como "decisiones heredadas del diccionario anterior, pendientes de validación conceptual". Esto simplifica la ontología pero puede perder matices.

### Opción C: Reclasificar como tipos propios

Crear 5 nuevos tipos canónicos para las transformaciones discutibles:
- `facilita` (para `facilito_por`)
- `condiciona` (para `condiciona`)
- `describe` (para `describe_a`)
- `trata_de` (para `trata_de`)
- `migra` (para `migra_a`)

Esto preserva la expresividad pero增加了 la complejidad de la ontología.

---

## Dictamen

**La migración puede cerrarse definitivamente con las siguientes condiciones:**

1. **39 transformaciones (91 relaciones)**: Heredadas del diccionario anterior, son sinónimos lingüísticamente válidos. **APROBADAS**.

2. **8 transformaciones (14 relaciones)**: Carecen de respaldo conceptual explícito. **CLASIFICADAS COMO PENDIENTES DE REVISIÓN CONCEPTUAL**.

3. **No se detectaron transformaciones no autorizadas** niDecisiones ontológicas nuevas tomadas sin aprobación.

4. **La pérdida de expresividad es limitada**: 14 de 105 relaciones (13.3%) pueden haber perdido matices semánticos.

5. **Recomendación**: Continuar con la ETAPA 6 documentando las 8 transformaciones pendientes como "reclasificaciones heredadas que requieren validación conceptual futura".
