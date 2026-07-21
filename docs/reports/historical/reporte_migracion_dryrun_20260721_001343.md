# Reporte de Migración v1.1

**Fecha**: 2026-07-21 00:13:43
**Modo**: DRY-RUN
**Versión Manifiesto**: 1.1
**Versión Script**: 1.0
**Duración**: 0.00s

---

## Resumen

| Métrica | Valor |
|---------|-------|
| Relaciones analizadas | 69 |
| Relaciones migradas | 14 |
| Relaciones omitidas | 55 |
| - Revisión manual | 22 |
| - Mantener (Nivel B) | 8 |
| - Escalar al Autor | 25 |
| Errores | 0 |

---

## Migraciones Automáticas

| Original | Destino | Frec. | Invertir |
|----------|---------|-------|----------|
| `escribió` | `autor_de` | 6 | No |
| `es_autor_de` | `autor_de` | 1 | No |
| `mentor_de` | `es_mentor_de` | 1 | No |
| `es_discípulo_de` | `es_mentor_de` | 2 | Sí |
| `colaboro_con` | `colabora_con` | 2 | No |
| `defiende_superioridad_de` | `critica_a` | 2 | No |

---

## Migraciones Requieren Revisión

| Original | Frec. |
|----------|-------|
| `contribuye_a` | 8 |
| `representado_por` | 5 |
| `presenta_rasgo` | 4 |
| `desarrollada_por` | 2 |
| `usa_enfoque` | 1 |
| `aplicado_a` | 1 |
| `descubierta_por` | 1 |

---

## Mantener (Nivel B)

| Original | Frec. |
|----------|-------|
| `relacionado_con` | 8 |

---

## Escalar al Autor

| Original | Frec. |
|----------|-------|
| `clasifica_como_activo` | 11 |
| `clasifica_como_pasivo` | 4 |
| `otorga_primacia_a` | 3 |
| `afecta_a` | 2 |
| `venera_concepto` | 1 |
| `considera_indispensable` | 1 |
| `limita` | 1 |
| `limita_expansion_a` | 1 |
| `invadio` | 1 |

---

## Información del Sistema

- **Script**: migrate_v1_1.py v1.0
- **Manifiesto**: v1.1
- **Reglas de migración**: 42
- **Automáticas**: 25
- **Revisión**: 7
- **Mantener**: 1
- **Escalar**: 9