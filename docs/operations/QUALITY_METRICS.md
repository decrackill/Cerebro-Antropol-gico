# Métricas de Calidad — Campañas de Extracción

**Fecha**: 2026-07-21
**Estado**: Definición — sin implementación

---

## Propósito

Este documento define todas las métricas que se registrarán durante las campañas de extracción.
Las métricas se recogen manualmente o se calculan a partir de los datos existentes.

No se implementa código nuevo. Solo se definen las métricas.

---

## 1. Métricas de Tiempo

| Métrica | Descripción | Cómo Medir | Unidad |
|---------|-------------|------------|--------|
| `tiempo_extraccion_libro` | Tiempo total de extracción de un libro | Cronómetro desde `extractor.py` hasta candidatos | minutos |
| `tiempo_por_chunk` | Tiempo promedio por chunk procesado | tiempo_extraccion / # chunks | segundos |
| `tiempo_revision_manual` | Tiempo de revisión manual de candidatos | Cronómetro en `herramienta_revisar()` | minutos |
| `tiempo_limpieza` | Tiempo de limpieza/deduplicación | Cronómetro en herramientas de limpieza | minutos |
| `tiempo_total_por_libro` | Tiempo completo de procesamiento | extracción + revisión + limpieza + auditoría + exportación | minutos |

---

## 2. Métricas de Extracción

| Métrica | Descripción | Cómo Medir | Unidad |
|---------|-------------|------------|--------|
| `paginas_por_libro` | Número de páginas del PDF | `len(paginas)` en extractor | entero |
| `chunks_por_libro` | Número de chunks generados | `len(chunks)` en extractor | entero |
| `tamano_promedio_chunk` | Tamaño promedio de chunk en caracteres | suma(tamaños) / # chunks | caracteres |
| `entidades_por_chunk` | Entidades extraídas por chunk | nodos_nuevos / # chunks | float |
| `relaciones_por_chunk` | Relaciones extraídas por chunk | relaciones_nuevas / # chunks | float |
| `entidades_por_capitulo` | Entidades extraídas por capítulo (aproximado) | nodos_nuevos / (# páginas / 20) | float |
| `relaciones_por_capitulo` | Relaciones extraídas por capítulo (aproximado) | relaciones_nuevas / (# páginas / 20) | float |

---

## 3. Métricas de Calidad de Entidades

| Métrica | Descripción | Cómo Medir | Unidad |
|---------|-------------|------------|--------|
| `conceptos_extraidos` | Total de conceptos extraídos | COUNT(tipo='concepto') | entero |
| `conceptos_por_capitulo` | Promedio de conceptos por capítulo | conceptos / (# páginas / 20) | float |
| `autores_extraidos` | Total de autores extraídos | COUNT(tipo='autor') | entero |
| `debates_extraidos` | Total de debates extraídos | COUNT(tipo='debate') | entero |
| `entidades_por_tipo` | Distribución de entidades por tipo | GROUP BY tipo | dict |
| `entidades_confianza_alta` | Entidades con confianza "alta" | COUNT(metadatos.confianza='alta') | entero |
| `entidades_confianza_baja` | Entidades con confianza "baja" | COUNT(metadatos.confianza='baja') | entero |

---

## 4. Métricas de Calidad de Relaciones

| Métrica | Descripción | Cómo Medir | Unidad |
|---------|-------------|------------|--------|
| `relaciones_por_tipo` | Distribución de relaciones por tipo | GROUP BY tipo | dict |
| `porcentaje_canonicas` | % de relaciones con tipo canónico | (canonicas / total) × 100 | % |
| `relaciones_con_cita` | Relaciones que tienen cita_textual | COUNT(cita_textual IS NOT NULL) | entero |
| `porcentaje_con_cita` | % de relaciones con cita textual | (con_cita / total) × 100 | % |
| `relaciones_con_fuente` | Relaciones que tienen fuente | COUNT(fuente IS NOT NULL) | entero |
| `porcentaje_con_fuente` | % de relaciones con fuente | (con_fuente / total) × 100 | % |

---

## 5. Métricas de Validación

| Métrica | Descripción | Cómo Medir | Unidad |
|---------|-------------|------------|--------|
| `relaciones_rechazadas_firewall` | Relaciones rechazadas por firewall | Log de `validar_relacion()` | entero |
| `relaciones_rechazadas_compatibilidad` | Relaciones rechazadas por incompatible | Log de `validar_relacion()` | entero |
| `relaciones_rechazadas_reflexividad` | Relaciones rechazadas por reflexividad | Log de `validar_relacion()` | entero |
| `relaciones_rechazadas_evidencia` | Relaciones rechazadas por falta de evidencia | Log de `validar_relacion()` | entero |
| `total_rechazadas` | Total de relaciones rechazadas | suma de anteriores | entero |
| `tasa_rechazo` | % de relaciones rechazadas | (rechazadas / (aceptadas + rechazadas)) × 100 | % |

---

## 6. Métricas de Revisión Manual

| Métrica | Descripción | Cómo Medir | Unidad |
|---------|-------------|------------|--------|
| `candidatos_nodos_total` | Total de nodos candidatos | len(nodos_nuevos) en candidatos_pendientes | entero |
| `candidatos_nodos_aceptados` | Nodos aprobados en revisión | COUNT(decision='insertado') | entero |
| `candidatos_nodos_rechazados` | Nodos rechazados en revisión | COUNT(decision='descartado') | entero |
| `candidatos_nodos_editados` | Nodos editados en revisión | COUNT(decision='insertado' con edición) | entero |
| `candidatos_nodos_auto_rechazados` | Nodos rechazados automáticamente | COUNT(decision='descartado_auto') | entero |
| `candidatos_relaciones_total` | Total de relaciones candidatas | len(relaciones_nuevas) | entero |
| `candidatos_relaciones_aceptadas` | Relaciones aprobadas | COUNT(decision='aprobada') | entero |
| `candidatos_relaciones_rechazadas` | Relaciones rechazadas | COUNT(decision='rechazada') | entero |
| `tasa_aceptacion_nodos` | % de nodos aceptados | (aceptados / total) × 100 | % |
| `tasa_aceptacion_relaciones` | % de relaciones aceptadas | (aceptadas / total) × 100 | % |

---

## 7. Métricas de Duplicados

| Métrica | Descripción | Cómo Medir | Unidad |
|---------|-------------|------------|--------|
| `duplicados_detectados` | Pares de duplicados detectados | `detectar_duplicados()` | entero |
| `duplicados_fusionados` | Duplicados que se fusionaron | COUNT(fusiones aplicadas) | entero |
| `duplicados_no_detectados` | Duplicados que pasaron sin detectar | Revisión manual | entero |
| `tasa_deteccion` | % de duplicados detectados | (detectados / (detectados + no_detectados)) × 100 | % |

---

## 8. Métricas del Grafo

| Métrica | Descripción | Cómo Medir | Unidad |
|---------|-------------|------------|--------|
| `total_nodos` | Total de nodos en DB | COUNT(*) FROM nodos | entero |
| `total_relaciones` | Total de relaciones en DB | COUNT(*) FROM relaciones | entero |
| `nodos_por_tipo` | Distribución de nodos por tipo | GROUP BY tipo | dict |
| `relaciones_por_tipo` | Distribución de relaciones por tipo | GROUP BY tipo | dict |
| `grado_promedio` | Grado promedio de nodos | (total_relaciones × 2) / total_nodos | float |
| `nodos_aislados` | Nodos sin relaciones | Query de integridad | entero |
| `densidad_grafo` | Densidad del grafo | total_relaciones / (total_nodos × (total_nodos - 1) / 2) | float |

---

## 9. Métricas de Errores

| Métrica | Descripción | Cómo Medir | Unidad |
|---------|-------------|------------|--------|
| `chunks_fallidos` | Chunks que fallaron en extracción | log_fallos en extractor | entero |
| `errores_api` | Errores de API (429, rate_limit) | log_fallos.razon | entero |
| `json_invalidos` | Chunks que devolvieron JSON inválido | log_fallos.razon='json_invalido' | entero |
| `todas_keys_agotadas` | Chunks donde se agotaron las keys | log_fallos.razon='todas_las_keys_agotadas' | entero |
| `tasa_exito` | % de chunks exitosos | ((total_chunks - fallidos) / total_chunks) × 100 | % |

---

## 10. Métricas de Normalización

| Métrica | Descripción | Cómo Medir | Unidad |
|---------|-------------|------------|--------|
| `tipos_normalizados` | Relaciones cuyo tipo fue normalizado via alias | Conteo en `normalizar_tipo_relacion()` | entero |
| `tipos_no_cubiertos` | Tipos que no están en aliases ni en canónicos | Conteo de tipos no resueltos | entero |
| `aliases_utilizados` | Cuáles aliases se usaron más | GROUP BY tipo_original | dict |

---

## 11. Métricas de Evidencia

| Métrica | Descripción | Cómo Medir | Unidad |
|---------|-------------|------------|--------|
| `citas_verificables` | Citas que coinciden con texto fuente | Búsqueda substring | entero |
| `citas_inventadas` | Citas que no se encuentran en texto fuente | Búsqueda substring | entero |
| `porcentaje_verificabilidad` | % de citas verificables | (verificables / total) × 100 | % |

---

## 12. Registro de Métricas

### Formato de Registro

Las métricas se registrarán en un archivo JSON por campaña:

```
runtime/logs/metricas_campana_YYYYMMDD.json
```

### Ejemplo de Registro

```json
{
  "campana": "2026-07-21",
  "libros_procesados": 5,
  "metricas": {
    "tiempo_total_horas": 25,
    "tiempo_promedio_por_libro_min": 300,
    "total_nodos_extraidos": 500,
    "total_relaciones_extraidas": 800,
    "tasa_exito_chunks": 98.5,
    "tasa_rechazo_relaciones": 12.3,
    "porcentaje_canonicas": 85.0,
    "porcentaje_con_cita": 92.0,
    "grado_promedio": 2.1,
    "nodos_aislados": 15
  }
}
```

### Cómo Calcular sin Código Nuevo

Todas las métricas se pueden calcular con SQL básico:

```sql
-- Total de nodos por tipo
SELECT tipo, COUNT(*) FROM nodos GROUP BY tipo;

-- Total de relaciones por tipo
SELECT tipo, COUNT(*) FROM relaciones GROUP BY tipo;

-- Relaciones con cita_textual
SELECT COUNT(*) FROM relaciones WHERE cita_textual IS NOT NULL AND cita_textual != '';

-- Nodos aislados
SELECT COUNT(*) FROM nodos WHERE id NOT IN (SELECT origen_id FROM relaciones) AND id NOT IN (SELECT destino_id FROM relaciones);

-- Grado promedio
SELECT (SELECT COUNT(*) FROM relaciones) * 2.0 / (SELECT COUNT(*) FROM nodos);
```
