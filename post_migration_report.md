# Post-Migration Report

**Fecha**: 2026-07-21
**Migración**: `scripts/migrate_relacion_types.py`

---

## Comparación ANTES vs DESPUÉS

| Métrica | ANTES | DESPUÉS | Cambio |
|---------|-------|---------|--------|
| Total relaciones | 371 | 371 | 0 |
| Tipos distinct | 81 | 34 | -47 |
| Relaciones normalizadas | — | 105 | — |
| Integridad | ok | ok | — |

## Tipos Canonizados (post-migración)

| Tipo | ANTES | DESPUÉS | Delta |
|------|-------|---------|-------|
| desarrolla_concepto | 44 | 85 | +41 |
| estudia_a | 44 | 67 | +23 |
| critica_a | 34 | 45 | +11 |
| pertenece_a | 8 | 28 | +20 |
| influenciado_por | 18 | 26 | +8 |
| precursor_de | 8 | 10 | +2 |
| contemporaneo_de | 5 | 5 | 0 |
| redefine_a | 7 | 7 | 0 |
| parte_del_debate | 0 | 0 | 0 |

## Tipos NO canónicos restantes (34 tipos)

Estos tipos permanecen en la DB sin normalizar:

| Tipo | Frecuencia | Estado |
|------|------------|--------|
| autor_de | 21 | No canonizado (decisión: mantener) |
| clasifica_como_activo | 11 | No canonizado |
| relacionado_con | 8 | No canonizado |
| contribuye_a | 8 | No canonizado |
| escribió | 6 | No canonizado |
| representado_por | 5 | No canonizado |
| es_mentor_de | 5 | No canonizado |
| presenta_rasgo | 4 | No canonizado |
| clasifica_como_pasivo | 4 | No canonizado |
| otorga_primacia_a | 3 | No canonizado |
| colabora_con | 3 | No canonizado |
| es_discípulo_de | 2 | No canonizado |
| desarrollada_por | 2 | No canonizado |
| defiende_superioridad_de | 2 | No canonizado |
| colaboro_con | 2 | No canonizado |
| afecta_a | 2 | No canonizado |
| (18 tipos con 1 ocurrencia c/u) | 18 | No canonizados |

## Verificaciones

- [x] `pytest` — 33/33 passed
- [x] `compileall` — OK
- [x] `PRAGMA integrity_check` — ok
- [x] Total relaciones sin cambio (371)
- [x] Backup creado: `data/grafo.db.bak`
