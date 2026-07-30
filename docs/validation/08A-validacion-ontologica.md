# 08A — Validación Ontológica Profunda

**Fecha:** Julio 2026

## Resumen

Validación exhaustiva de la ontología del proyecto contra los 8 criterios del Manifiesto Ontológico v1.1. Se auditaron tipos de nodo, relaciones, restricciones, firewall epistemológico y compatibilidad con el modelo de datos.

---

## 1. Metamodelo

| Concepto | Definición | Estado |
|----------|-----------|--------|
| Nodo | Entidad con nombre, tipo, descripción, metadatos JSON | ✅ |
| Relación | Arista origen→destino con tipo, fuente, cita_textual | ✅ |
| Evidencia | fuente + cita_textual obligatorios en validación | ✅ |
| Afirmación | Cada relación representa una afirmación con trazabilidad | ✅ |

Las fronteras son claras. No hay contradicciones entre conceptos del metamodelo.

## 2. Tipos de Nodo

| Tipo | DB | CHECK | Precisión |
|------|-----|-------|-----------|
| autor | 204 | ✅ | Preciso: persona académica/intelectual |
| obra | 133 | ✅ | Preciso: libro, artículo, texto |
| concepto | 742 | ✅ | Adecuado para 1-4 palabras |
| escuela | 5 | ✅ | Institución/sede con miembros |
| corriente | 11 | ✅ | Tendencia sin organización formal |
| cultura | 41 | ✅ | Prácticas/creencias/organización social |
| poblacion | 262 | ✅ | Origen/demografía/ubicación |
| debate | 3 | ✅ | Discusión/tensión entre posiciones |

**Total nodos**: 1401  
**Solapamientos detectados**: Ninguno. Los 8 tipos son mutuamente excluyentes.  
**Casos límite**: `poblacion` vs `cultura` — el firewall epistemológico impide fusión y mantiene separación clara.

## 3. Relaciones

### Nivel A (canónicas)

| Relación | DB | Origen → Destino (según compatibilidad) |
|----------|-----|------------------------------------------|
| autor_de | 111 | autor → obra |
| influenciado_por | 30 | autor, obra, escuela, corriente, concepto → autor, obra, escuela, corriente, concepto |
| critica_a | 102 | autor, obra, escuela, corriente → autor, obra, escuela, corriente, concepto |
| desarrolla_concepto | 509 | autor, obra, escuela, corriente → concepto |
| redefine_a | 11 | autor, obra, concepto → concepto |
| precursor_de | 10 | autor, obra, escuela, corriente, concepto → autor, obra, escuela, corriente, concepto |
| pertenece_a | 22 | autor, concepto, escuela → escuela, corriente |
| estudia_a | 238 | autor, obra → poblacion, cultura |
| contemporaneo_de | 5 | autor → autor |
| parte_del_debate | 3 | autor, obra, concepto, poblacion, escuela, corriente → debate |
| es_mentor_de | 8 | autor → autor |
| colabora_con | 14 | autor → autor |

### Nivel B (conceptuales)

| Relación | DB | Nota |
|----------|-----|------|
| relacionado_con | 8 | Relación genérica aceptada |
| contradice | 0 | No detectada en corpus actual |
| depende_de | 0 | No detectada en corpus actual |

**Total relaciones**: 1071  
**Tipos canónicos**: 13 de 15 posibles en uso (12 Nivel A + 1 Nivel B).  
**Relaciones rechazadas históricamente**: varias (>400) por tipos no canónicos inventados por Gemini (dirige, traduce, practica, etc.). Esto es esperado — los ~40 aliases en `config.py` normalizan la mayoría.

## 4. Restricciones Ontológicas

### CHECK constraint en nodos.tipo
✅ 8 tipos validados en SQL — 0 nodos con tipo inválido.

### Firewall epistemológico
✅ `poblacion` solo aparece como destino de `estudia_a` y origen de `parte_del_debate`.  
✅ Implementado en `validar_relacion()` con 12 tests específicos en `test_firewall.py`.

### No reflexividad
✅ 0 relaciones auto-reflexivas.

### Evidencia documental
✅ 1071/1071 relaciones con cita_textual no NULL (post-backfill).

### Integridad referencial (0 huérfanos) vs. nodos aislados (386)
**Conceptos distintos:**
- **0 huérfanos** = integridad referencial de FK: toda relación apunta a nodos que existen. No hay `origen_id` ni `destino_id` huérfanos.
- **386 aislados** = nodos que existen en la tabla `nodos` pero no participan en ninguna relación (ni como origen ni como destino). Esto es normal post-limpieza y no viola ninguna restricción ontológica o de integridad.

## 5. Aliases de Relación

~40 aliases en `config.py:TIPOS_ALIAS_RELACION`. Cobertura de las variantes más comunes generadas por Gemini. Riesgo bajo: nuevas variantes no cubiertas simplemente son rechazadas por `validar_relacion()` sin daño.

## 6. Riesgos Epistemológicos

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|--------------|------------|
| Reificación indebida | Medio | Baja | cita_textual + firewall |
| Sesgos disciplinares | Bajo | Baja | Ontología revisada antropológicamente |
| Anacronismos | Medio | Media | revision_estado + trazabilidad |
| Esencialización | Alto | Baja | Firewall poblacion/cultura |
| Pérdida de contexto | Medio | Media | fuente y cita_textual requeridos |

## 7. Conclusión

La ontología es conceptualmente consistente, completa para el dominio antropológico y está correctamente implementada en SQL. No presenta contradicciones internas. Los riesgos epistemológicos están identificados y mitigados.

**Dictamen ontológico: VÁLIDA**
