# Relaciones Pendientes de Decisión

**Fecha**: 2026-07-21
**Contexto**: Tipos que permanecen en la DB sin ser canónicos ni aliases

---

## Tipos sin mapeo (34 tipos, 158 relaciones)

### Frecuencia ≥ 5

| Tipo | Frecuencia | Ejemplo | Recomendación |
|------|------------|---------|---------------|
| `autor_de` | 21 | "Boas autor_de Antropología Cultural" | Pendiente: ¿es `pertenece_a` o tipo propio? |
| `clasifica_como_activo` | 11 | "Boas clasifica_como_activo Determinismo racial" | Pendiente: ¿es `desarrolla_concepto` o tipo propio? |
| `relacionado_con` | 8 | "Cultura relacionado_con Sociedad" | Pendiente: ¿es `contemporaneo_de` o tipo propio? |
| `contribuye_a` | 8 | "Autor contribuye_a Obra" | Pendiente: ¿es `desarrolla_concepto` o tipo propio? |
| `escribió` | 6 | "Boas escribió Antropología Cultural" | Pendiente: ¿es `pertenece_a` o tipo propio? |
| `representado_por` | 5 | "Concepto representado_por Ejemplo" | Pendiente: ¿es `desarrolla_concepto` o tipo propio? |
| `es_mentor_de` | 5 | "Boas es_mentor_de Kroeber" | Pendiente: ¿es `precursor_de` o tipo propio? |

### Frecuencia 2-4

| Tipo | Frecuencia |
|------|------------|
| `presenta_rasgo` | 4 |
| `clasifica_como_pasivo` | 4 |
| `otorga_primacia_a` | 3 |
| `colabora_con` | 3 |
| `es_discípulo_de` | 2 |
| `desarrollada_por` | 2 |
| `defiende_superioridad_de` | 2 |
| `colaboro_con` | 2 |
| `afecta_a` | 2 |

### Frecuencia 1

| Tipo | Frecuencia |
|------|------------|
| `venera_concepto` | 1 |
| `usa_enfoque` | 1 |
| `mentor_de` | 1 |
| `limita_expansion_a` | 1 |
| `limita` | 1 |
| `invadio` | 1 |
| `es_autor_de` | 1 |
| `descubierta_por` | 1 |
| `considera_indispensable` | 1 |
| `aplicado_a` | 1 |

---

## Resumen

- **Total tipos no canónicos**: 34
- **Total relaciones afectadas**: 158 de 371 (42.6%)
- **Tipos con más frecuencia**: `autor_de` (21), `clasifica_como_activo` (11), `relacionado_con` (8)

Estos tipos requieren decisión conceptual para determinar si:
1. Deben agregarse como aliases a un tipo canónico existente
2. Deben agregarse como nuevos tipos canónicos
3. Deben permanecer como están (tipos libres del LLM)
