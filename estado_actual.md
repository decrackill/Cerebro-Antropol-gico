# Estado Actual — Auditoría Técnica Inicial

**Fecha**: 2026-07-21
**Base de datos**: `data/grafo.db`

---

## 1. Estadísticas de la DB

| Métrica | Valor |
|---------|-------|
| Nodos totales | 394 |
| Relaciones totales | 371 |
| Tipos de nodo distinct | 6 |
| Tipos de relación distinct | 70 |
| Nodos aislados | 68 (17%) |
| Integridad | OK |

## 2. Distribución por Tipo de Nodo

| Tipo | Cantidad |
|------|----------|
| autor | 132 |
| concepto | 117 |
| cultura | 99 |
| obra | 34 |
| escuela | 11 |
| debate | 1 |
| **poblacion** | **0** |
| **corriente** | **0** |

## 3. Top 15 Relaciones por Frecuencia

| Tipo | Cantidad | ¿Canonical? |
|------|----------|-------------|
| estudia_a | 44 | ✅ SÍ |
| desarrolla_concepto | 44 | ✅ SÍ |
| critica_a | 34 | ✅ SÍ |
| autor_de | 21 | ❌ NO |
| influenciado_por | 18 | ✅ SÍ |
| clasifica_como_activo | 11 | ❌ NO |
| relacionado_con | 8 | ❌ NO |
| precursor_de | 8 | ✅ SÍ |
| pertenece_a | 8 | ✅ SÍ |
| contribuye_a | 8 | ❌ NO |
| redefine_a | 7 | ✅ SÍ |
| ejemplo_de | 7 | ❌ NO |
| describe_a | 7 | ❌ NO |
| estudio | 6 | ❌ NO |
| escribió | 6 | ❌ NO |

## 4. Tipos Canonical (TIPOS_VALIDOS_RELACION)

```python
{"influenciado_por", "critica_a", "desarrolla_concepto", "pertenece_a",
 "estudia_a", "contemporaneo_de", "precursor_de", "parte_del_debate", "redefine_a"}
```

**Total: 9 tipos**

## 5. Tipos en DB que NO son canónicos

De los 70 tipos distinct en la DB:
- **9 son canónicos** (estudia_a, desarrolla_concepto, critica_a, influenciado_por, pertenece_a, precursor_de, contemporaneo_de, redefine_a, parte_del_debate)
- **61 son no-canónicos** (requieren alias o decisión)

## 6. `parte_del_debate`

- Definido en `TIPOS_VALIDOS_RELACION`: ✅
- Ocurrencias en DB: **0**
- Alias que apuntan a él: **0**

## 7. Código Localizado

| Elemento | Ubicación |
|----------|-----------|
| `TIPOS_VALIDOS_RELACION` | `pipeline/core/config.py:42-46` |
| `TIPOS_ALIAS_RELACION` | `pipeline/core/config.py:49-119` (70 entradas) |
| `normalizar_tipo_relacion()` | `pipeline/core/utils.py:26-34` |
| INSERT INTO relaciones | 4 ubicaciones |
| Llamadas a normalizar_tipo_relacion | 7 ubicaciones |
| Tests de normalización | `tests/test_review.py:4-12` |

## 8. Tipos sin mapeo (pasan sin normalizar)

| Tipo | Ocurrencias |
|------|-------------|
| desarrollada_por | 2 |
| escribió | 6 |
| invadio | 1 |
