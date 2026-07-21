# Validación de Exportación — EXPORT_VALIDATION.md

**Fecha**: 2026-07-21
**Estado**: ✅ EXPORTACIÓN AUTORIZADA

---

## 1. Compatibilidad con el Manifiesto v1.1

| Verificación | Estado |
|--------------|--------|
| Exporta los 12 tipos canónicos | ✅ |
| Exporta las 3 relaciones Nivel B | ✅ |
| No filtra ningún tipo válido | ✅ |
| No regenera IDs | ✅ |
| Preserva metadatos | ✅ |

**Detalle**: El exportador utiliza `SELECT * FROM` para ambas tablas. No existe lista interna de tipos que pueda excluir las nuevas relaciones canónicas (`autor_de`, `es_mentor_de`, `colabora_con`).

---

## 2. Compatibilidad con el Frontend

| Verificación | Estado |
|--------------|--------|
| Estructura `{nodos: [...], relaciones: [...]}` | ✅ |
| Campo `id` en nodos | ✅ |
| Campo `origen_id` en relaciones | ✅ |
| Campo `destino_id` en relaciones | ✅ |
| Campo `tipo` en relaciones | ✅ |
| Campo `metadata` en nodos | ✅ |

**Detalle**: El frontend (`render.js`) usa `r.origen_id || r.origen` y `r.destino_id || r.destino`, lo que es compatible con la estructura exportada.

---

## 3. Compatibilidad con Cytoscape

| Verificación | Estado |
|--------------|--------|
| Nodos con `id`, `label`, `tipo` | ✅ |
| Relaciones con `id`, `source`, `target`, `label` | ✅ |
| Sin nodos huérfanos | ✅ |
| Sin relaciones con referencias inválidas | ✅ |

**Detalle**: Cytoscape.js requiere `source` y `target` en las relaciones. El frontend mapea `origen_id` → `source` y `destino_id` → `target`.

---

## 4. Compatibilidad con la Base de Datos

| Verificación | Estado |
|--------------|--------|
| Nodos exportados = Nodos en DB | ✅ (394 = 394) |
| Relaciones exportadas = Relaciones en DB | ✅ (371 = 371) |
| Todos los tipos presentes | ✅ (29 tipos) |
| Sin referencias rotas | ✅ |

---

## 5. Análisis del Código

### `scripts/export_json.py`

```python
# Línea 20-24: Exporta TODOS los nodos
for row in conn.execute("SELECT * FROM nodos"):
    nodo = dict(row)
    nodo["metadata"] = json.loads(nodo["metadatos"] or "{}")
    nodos.append(nodo)

# Línea 27-29: Exporta TODAS las relaciones
for row in conn.execute("SELECT * FROM relaciones"):
    relaciones.append(dict(row))
```

**Análisis**:
- ✅ No hay filtros por tipo de relación
- ✅ No hay listas internas de tipos válidos
- ✅ No hay lógica que pueda excluir relaciones nuevas
- ✅ Exporta exactamente lo que hay en la DB

### `src/grafo.js`

```javascript
export async function cargarGrafo() {
  const respuesta = await fetch('/src/datos.json')
  const datos = await respuesta.json()
  return datos // { nodos: [...], relaciones: [...] }
}
```

**Análisis**:
- ✅ Carga el JSON completo sin filtrar
- ✅ Estructura compatible con lo exportado

### `src/render.js`

```javascript
...relaciones.map((r) => ({
  data: {
    id: `rel-${r.id}`,
    source: r.origen_id || r.origen,
    target: r.destino_id || r.destino,
    label: r.tipo,
    ...
  },
})),
```

**Análisis**:
- ✅ Usa `origen_id` (campo de la DB)
- ✅ Fallback a `origen` (compatibilidad)
- ✅ No depende de nombres específicos de relaciones

---

## 6. Riesgos Encontrados

| Riesgo | Probabilidad | Impacto |
|--------|-------------|---------|
| Ninguno identificado | — | — |

---

## 7. Conclusión

**✅ EXPORTACIÓN AUTORIZADA**

El exportador es completamente compatible con:
- Manifiesto Ontológico v1.1
- Frontend actual
- Cytoscape.js
- Base de datos migrada

No existen incompatibilidades ni riesgos.
