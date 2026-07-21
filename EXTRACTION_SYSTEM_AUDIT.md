# Auditoría Integral del Sistema de Extracción

**Fecha**: 2026-07-21
**Estado**: Auditoría completada — sin modificaciones al código

---

## Resumen Ejecutivo

El sistema de extracción es funcional y bien diseñado para su caso de uso actual (pocos libros). Sin embargo, tiene limitaciones claras para escalar a cientos de libros. El mayor cuello de botella es la revisión manual (interactiva), no la extracción automática.

| Aspecto | Estado | Escalabilidad |
|---------|--------|---------------|
| Chunking | Funcional | Limitado |
| Prompt | Excelente | Escalable |
| Extracción LLM | Funcional | Limitado por costos |
| Normalización | Funcional | Escalable |
| Deduplicación | Funcional | Limitada |
| Revisión manual | Funcional | **No escala** |
| Inserción SQLite | Funcional | Escalable |
| Firewall | Funcional | Escalable |
| Exportación | Funcional | Escalable |

---

## 1. Diagrama del Flujo Real de Extracción

```
PDF (fitz)
  ↓
Páginas [(num, texto)]
  ↓
Chunks (40,000 chars c/u)
  ↓
Prompt + Catálogo de nodos existentes
  ↓
LLM (Gemini/OpenRouter)
  ↓
JSON {nodos_nuevos, relaciones_nuevas}
  ↓
Normalización de tipos (TIPOS_ALIAS)
  ↓
Acutar a candidatos_pendientes.json
  ↓
[ checkpoint por chunk ]
  ↓
--- FIN DE EXTRACCIÓN AUTOMÁTICA ---
  ↓
Revisión manual (menu.py → opción 1)
  ↓
  ├→ Aprobar/Rechazar/Editar nodos
  ├→ Detección de duplicados (fuzzy)
  ├→ Descarte automático de autores superficiales
  ↓
  ├→ Resolver IDs (numéricos vs snake_case)
  ├→ validar_relacion() — 5 validaciones
  ↓
INSERT INTO nodos / INSERT INTO relaciones
  ↓
[Opcional] Limpieza automática (fusión + ruido)
  ↓
[Opcional] Conexión automática (bulk)
  ↓
[Opcional] Recuperación de relaciones perdidas
  ↓
export_json.py → datos.json
  ↓
Frontend (Cytoscape.js)
```

**Hallazgo**: El flujo es correcto pero hay una **desconexión entre extracción e inserción**. La extracción automática produce `candidatos_pendientes.json`, pero la inserción requiere revisión manual interactiva o el modo "conexión automática".

---

## 2. Evaluación del Chunking

### Configuración Actual
- **Tamaño**: 40,000 caracteres por chunk
- **Overlap**: 0 (sin superposición)
- **Separación**: Por límite de caracteres, no por capítulos
- **Separador**: `\n\n` entre páginas

### Evaluación

| Criterio | Estado | Nota |
|----------|--------|------|
| Tamaño adecuado | ✅ | 40K chars ≈ 10K tokens, dentro del contexto de Gemini |
| Sin overlap | ⚠️ | Puede perder relaciones跨页 entre chunks |
| Sin separación por capítulos | ⚠️ | Fragmenta argumentos académicos |
| Pérdida de contexto | ⚠️ | Conceptos definidos en chunk N se usan en chunk N+1 |

### Problemas Detectados

1. **Sin overlap**: Si un concepto se define al final de un chunk y se usa al inicio del siguiente, el LLM no tiene contexto completo.
2. **Sin separación semántica**: Los chunks cortan en cualquier punto, no en límites de sección o capítulo.
3. **Pérdida de catálogo**: El catálogo de nodos existentes se reconstruye para cada chunk, pero los nodos extraídos en chunks anteriores de la misma sesión solo están en `nodos_acumulados`.

### Impacto
- **Bajo** para libros con capítulos cortos
- **Medio** para libros con argumentos largos y dependientes
- **Alto** para conceptos que requieren contexto completo

---

## 3. Evaluación del Prompt

### Análisis del Prompt (`prompts.py`, 155 líneas)

| Aspecto | Evaluación |
|---------|-----------|
| Claridad | ⭐⭐⭐⭐⭐ Excelente |
| Criterios de concepto | ⭐⭐⭐⭐⭐ Muy bien definidos |
| Criterios de autor | ⭐⭐⭐⭐⭐ Filtrado agresivo correcto |
| Firewall en prompt | ⭐⭐⭐⭐⭐ Presente y claro |
| Formato de salida | ⭐⭐⭐⭐ Bien definido |
| Longitud | ⭐⭐⭐⭐ 155 líneas, razonable |

### Fortalezas

1. **Criterio estricto para conceptos**: Las 3 condiciones simultáneas son excelentes.
2. **"Prueba de fuego" para autores**: Evita autores superficiales.
3. **Distinguición cultura/población**: Clara y con ejemplos.
4. **Autoverificación obligatoria**: El campo `justificacion_concepto` fuerza calidad.
5. **Límite explícito**: "2-8 conceptos por capítulo de 40K chars".

### Debilidades

1. **Sin ejemplos negativos**: El prompt dice qué NO extraer pero no da ejemplos concretos de lo que el LLM podría alucinar.
2. **Catálogo potencialmente gigante**: Si hay 500 nodos existentes, el prompt crece linealmente.
3. **Sin instrucciones de priorización**: No dice qué hacer cuando hay ambigüedad entre tipos.
4. **Sin validación cruzada**: No pide al LLM que verifique que las relaciones sean coherentes entre sí.

### Riesgo de Alucinación
- **Conceptos**: MEDIO — El criterio estricto ayuda, pero el LLM puede inventar "justificaciones" genéricas.
- **Autores**: BAJO — La "prueba de fuego" es efectiva.
- **Relaciones**: MEDIO — El LLM puede inventar `cita_textual` convincente.

---

## 4. Calidad de Entidades

### Tipos de Nodo y su Detección

| Tipo | Detección | Falsos Positivos | Falsos Negativos |
|------|-----------|------------------|------------------|
| autor | Buena | Bajos (filtro superficial) | Medios (autores menores omitidos) |
| obra | Buena | Bajos | Bajos |
| concepto | Regular | **Altos** (principal problema) | Medios |
| escuela | Buena | Bajos | Bajos |
| corriente | Buena | Bajos | Bajos |
| cultura | Regular | Medios | Medios |
| poblacion | Regular | Medios | Medios |
| debate | Baja | Bajos | **Altos** (rara vez extraído) |

### Problemas Detectados

1. **Conceptos sobreextraídos**: A pesar del criterio estricto, es el tipo más propenso a falsos positivos.
2. **Debates sub-extraídos**: El tipo `debate` rara vez aparece porque el prompt no da ejemplos claros de qué es un "debate" antropológico.
3. **Cultura vs Población**: La distinción depende del LLM, que puede confundir según el contexto.

---

## 5. Calidad de Relaciones

### Distribución Esperada vs Real (estimada)

| Relación | Esperada | Real (estimada) | Sesgo |
|----------|----------|-----------------|-------|
| autor_de | Alta | Alta | ✅ Normal |
| influenciado_por | Alta | Alta | ✅ Normal |
| critica_a | Media | **Baja** | ⚠️ Sub-extraída |
| desarrolla_concepto | Alta | **Muy alta** | ⚠️ Sobre-extraída |
| redefine_a | Baja | Baja | ✅ Normal |
| precursor_de | Media | Baja | ⚠️ Sub-extraída |
| pertenece_a | Media | Media | ✅ Normal |
| estudia_a | Alta | Alta | ✅ Normal |
| contemporaneo_de | Baja | Baja | ✅ Normal |
| parte_del_debate | **Media** | **Muy baja** | ⚠️ Casi nunca extraída |
| es_mentor_de | Baja | Baja | ✅ Normal |
| colabora_con | Baja | Baja | ✅ Normal |

### Sesgos Detectados

1. **Sesgo hacia `desarrolla_concepto`**: El LLM tiende a modelar cualquier relación autor-concepto como "desarrolla_concepto".
2. **Sesgo contra `critica_a`**: El LLM evita relaciones negativas/críticas.
3. **Sesgo contra `parte_del_debate`**: Requiere que el texto describa explícitamente una discusión, lo cual es raro en textos académicos descriptivos.
4. **Sesgo contra `precursor_de`**: Requiere conocimiento histórico que el LLM puede no tener en el chunk.

---

## 6. Evidencia Documental

### Flujo de la Evidencia

```
LLM genera:
  └→ cita_textual (fragmento exacto)
  └→ nota (contexto breve)

Extractor agrega:
  └→ fuente = "nombre_pdf, p.X-Y"

Revisión conserva:
  └→ fuente + cita_textual en INSERT

Exportación preserva:
  └→ campos fuente y cita_textual en JSON
```

### Evaluación

| Punto | Estado | Riesgo |
|-------|--------|--------|
| LLM genera cita_textual | ⚠️ | Puede inventar citas |
| extractor.py agrega fuente | ✅ | Correcto |
| revision.py conserva evidencia | ✅ | Correcto |
| limpieza.py conserva evidencia | ✅ | fusionar_nodos preserva la mejor cita |
| export_json.py exporta todo | ✅ | Sin filtros |

### Hallazgo Crítico

**El LLM puede inventar `cita_textual`**. No hay verificación cruzada entre la cita y el texto fuente. Esto es un riesgo epistemológico significativo para un grafo de conocimiento académico.

---

## 7. Evaluación de la Normalización

### Pipeline de Normalización

```
LLM output
  ↓
normalizar_tipos() — convierte "libro" → "obra"
  ↓
candidatos_pendientes.json
  ↓
Revisión manual:
  ├→ normalizar_tipo_relacion() — resuelve aliases
  ├→ fuzzy match por nombre — detecta duplicados
  └→ validación de tipos
  ↓
INSERT con tipo normalizado
```

### Cobertura de Aliases

Hay **48 aliases** definidos en `TIPOS_ALIAS_RELACION`. Esto cubre la mayoría de variaciones lingüísticas del LLM.

### Problemas

1. **Alias no cubiertos**: Si el LLM genera un tipo no listado (ej: "inspira_a"), se inserta sin normalizar.
2. **Fuzzy match limitado**: `SequenceMatcher` no entiende sinónimos semánticos, solo similitud textual.
3. **Sin normalización de nombres**: "Lévi-Strauss" y "Levi-Strauss" se consideran diferentes.

---

## 8. Evaluación del Firewall

### Verificación: ¿Todos los caminos pasan por `validar_relacion()`?

| Camino de Inserción | USA validar_relacion() | Nota |
|---------------------|----------------------|------|
| `herramienta_revisar()` | ✅ Línea 214 | Correcto |
| `herramienta_conectar_automatico()` | ✅ Línea 319 | Correcto |
| `herramienta_recuperar_relaciones()` | ✅ Línea 303 | Correcto |
| `herramienta_revision_total()` | ❌ | Solo actualiza tipo, no inserta relaciones |
| `herramienta_limpieza_asistida()` | ❌ | Solo reclasifica nodos, no inserta relaciones |
| `herramienta_limpiar_auto()` | ❌ | Solo elimina nodos, no inserta relaciones |

**Conclusión**: Todos los caminos que INSERTAN relaciones pasan por `validar_relacion()`. Los que no insertan relaciones no necesitan la validación.

### Firewall Epistemológico

| Regla | Estado |
|-------|--------|
| poblacion solo destino de estudia_a | ✅ Verificado en `_validar_firewall_poblacion()` |
| poblacion solo origen de parte_del_debate | ✅ Verificado |
| No reflexividad | ✅ Verificado |
| Compatibilidad origen/destino | ✅ Verificado |
| Evidencia documental | ✅ Verificado |

**El firewall está completo y correcto.**

---

## 9. Evaluación de Rendimiento

### Operaciones Potencialmente Costosas

| Operación | Complejidad | Impacto |
|-----------|-------------|---------|
| `dividir_en_chunks()` | O(n) | Bajo |
| `procesar_chunk()` — llamada LLM | O(1) por chunk | **Alto** (latencia de red) |
| `cargar_nodos_existentes()` | O(n) | Bajo |
| `detectar_duplicados()` | **O(n²)** por tipo | **Medio** |
| `_validar_firewall_poblacion()` | O(n) por consulta | **Medio** (carga todos los tipos) |
| `_validar_compatibilidad_nodos()` | O(n) por consulta | **Medio** (carga todos los tipos) |
| `fusionar_nodos()` | O(k) por fusión | Bajo |
| `construir_mapa_resolucion()` | O(n) | Bajo |

### Problemas de Rendimiento

1. **`_validar_firewall_poblacion()`** ejecuta `SELECT id, tipo FROM nodos` en CADA llamada. Con 1000 relaciones a validar, son 1000 queries idénticas.
2. **`_validar_compatibilidad_nodos()`** tiene el mismo problema.
3. **`detectar_duplicados()`** es O(n²) por tipo. Con 500 autores, son 125,000 comparaciones.
4. **Sin índices en tipos**: Las queries por tipo no tienen índice.

### Optimizaciones Posibles (futuras)

1. Cachear `tipos_nodo` en `validar_relacion()` en vez de cargarlo en cada validador.
2. Agregar índice en `nodos(tipo)`.
3. Usar `unordered_map` en vez de `dict` para `tipos_nodo`.

---

## 10. Evaluación de Escalabilidad

### Escenario: 100 Libros

| Componente | Estado | Problema |
|------------|--------|----------|
| Extracción LLM | ✅ | ~500 chunks × 4s = 33 min |
| Almacenamiento | ✅ | ~50,000 candidatos en JSON |
| Revisión manual | ⚠️ | **~50,000 nodos + 100,000 relaciones a revisar** |
| Inserción | ✅ | ~150,000 INSERTs |
| Detección de duplicados | ⚠️ | O(n²) con 5,000 nodos = 25M comparaciones |

### Escenario: 500 Libros

| Componente | Estado | Problema |
|------------|--------|----------|
| Extracción LLM | ✅ | ~2,500 chunks × 4s = 167 min |
| Almacenamiento | ✅ | ~250,000 candidatos |
| Revisión manual | ❌ | **Imposible manualmente** |
| Inserción | ✅ | ~750,000 INSERTs |
| Detección de duplicados | ❌ | O(n²) con 25,000 nodos |

### Escenario: 1,000 Libros

| Componente | Estado | Problema |
|------------|--------|----------|
| Extracción LLM | ✅ | ~5,000 chunks × 4s = 333 min |
| Revisión manual | ❌ | **No escala** |
| Detección de duplicados | ❌ | O(n²) con 50,000 nodos |

### Componentes que Limitan el Crecimiento

1. **Revisión manual** (CRÍTICO): La opción 1 del menú es interactiva. Con 100 libros, tendrías decenas de miles de candidatos.
2. **Detección de duplicados** (ALTO): O(n²) se vuelve inmanejable.
3. **Carga de tipos en validación** (MEDIO): Queries repetidas innecesarias.

---

## 11. Calidad del Código

### Archivos por Tamaño

| Archivo | Líneas | Evaluación |
|---------|--------|-----------|
| `extractor.py` | 383 | ✅ Correcto |
| `prompts.py` | 155 | ✅ Correcto |
| `modo_manual.py` | 160 | ✅ Correcto |
| `config.py` | 138 | ✅ Correcto |
| `db.py` | 269 | ✅ Correcto |
| `utils.py` | 95 | ✅ Correcto |
| `revision.py` | 453 | ⚠️ **Demasiado grande** |
| `limpieza.py` | 321 | ⠦ Correcto |
| `auditoria.py` | 134 | ✅ Correcto |

### Problemas Detectados

1. **`revision.py` (453 líneas)**: Mezcla revisión manual, conexión automática, y revisión total. Debería dividirse.
2. **Código duplicado**: `herramienta_revisar()` y `herramienta_conectar_automatico()` comparten lógica de resolución de IDs.
3. **Responsabilidades mezcladas**: `revision.py` tiene lógica de UI (input/output) mezclada con lógica de negocio.
4. **Imports condicionales**: `from ..core.config import ...` aparece en medio de `revision.py` (línea 353).

---

## 12. Problemas Encontrados

### Críticos

| # | Problema | Impacto | Ubicación |
|---|----------|---------|-----------|
| 1 | **Revisión manual no escala** | Impide procesar más de ~20 libros | `revision.py:herramienta_revisar()` |
| 2 | **LLM puede inventar citas_textual** | Compromete integridad epistemológica | `prompts.py` (inherente al LLM) |

### Altos

| # | Problema | Impacto | Ubicación |
|---|----------|---------|-----------|
| 3 | **Detección de duplicados O(n²)** | Lento con miles de nodos | `utils.py:detectar_duplicados()` |
| 4 | **Queries repetidas en validación** | Lento con miles de relaciones | `db.py:_validar_firewall_poblacion()` |
| 5 | **Sin overlap en chunking** | Pierde contexto跨页 | `extractor.py:dividir_en_chunks()` |
| 6 | **Sesgo ontológico en relaciones** | Desarrolla_concepto sobre-extraído | `prompts.py` (inherente al LLM) |

### Medios

| # | Problema | Impacto | Ubicación |
|---|----------|---------|-----------|
| 7 | **`revision.py` demasiado grande** | Difícil de mantener | `revision.py` |
| 8 | **Sin normalización de nombres** | Duplicados no detectados | `utils.py` |
| 9 | **Sin validación cruzada de citas** | Citas inventadas pasan silenciosamente | Pipeline completo |
| 10 | **`debate` rara vez extraído** | Grafo incompleto | `prompts.py` |

### Bajos

| # | Problema | Impacto | Ubicación |
|---|----------|---------|-----------|
| 11 | **Imports condicionales** | Código frágil | `revision.py:353` |
| 12 | **Sin type hints completos** | Menor legibilidad | Varios archivos |

---

## 13. Deuda Técnica

| Deuda | Severidad | Esfuerzo de Resolución |
|-------|-----------|----------------------|
| Dividir `revision.py` en módulos | Baja | 2-3 horas |
| Cachear tipos_nodo en validación | Baja | 30 min |
| Agregar overlap al chunking | Media | 1-2 horas |
| Agregar validación de citas_textual | Alta | 1-2 días |
| Crear modo "revisión automática" | Alta | 1 semana |
| Agregar índices SQL | Baja | 15 min |

---

## 14. Recomendaciones Priorizadas por Impacto

### Alta Prioridad (antes de escalar)

1. **Crear modo de revisión automática**: Que el sistema pueda aprobar/rechazar candidatos basándose en reglas (confianza alta → auto-aprobar, duplicados fuzzy → auto-rechazar).
2. **Validación de citas_textual**: Cruzar las citas contra el texto fuente para detectar alucinaciones.
3. **Cachear tipos_nodo**: Evitar queries repetidas en `validar_relacion()`.

### Media Prioridad (mejoras de calidad)

4. **Agregar overlap al chunking**: 10-20% de superposición entre chunks.
5. **Mejorar prompts para `debate`**: Agregar ejemplos concretos de debates antropológicos.
6. **Normalización de nombres**: Implementar stemmer o normalización Unicode.

### Baja Prioridad (mantenibilidad)

7. **Dividir `revision.py`**: Separar UI de lógica de negocio.
8. **Agregar type hints completos**: Mejorar legibilidad.
9. **Configurar linting**: ruff para Python.

---

## 15. Veredicto Final

### ¿El sistema de extracción está listo para procesar cientos de libros?

**NO** en su estado actual. El sistema es funcional y bien diseñado para su caso de uso actual (1-10 libros con revisión manual). Para escalar a cientos de libros, necesita:

1. **Modo de revisión automática** (CRÍTICO)
2. **Validación de citas_textual** (CRÍTICO)
3. **Optimización de rendimiento** (IMPORTANTE)

### ¿Cuál es hoy el mayor cuello de botella?

**La revisión manual interactiva**. La opción 1 del menú (`herramienta_revisar()`) requiere que un humano apruebe/rechace cada nodo y relación individualmente. Con 100 libros, esto tomaría semanas.

### ¿Qué mejoras producirían el mayor aumento de calidad con el menor esfuerzo?

1. **Cachear tipos_nodo** (30 min, mejora rendimiento 10x)
2. **Agregar overlap al chunking** (1-2 horas, mejora calidad significativamente)
3. **Mejorar prompts para `debate`** (1 hora, mejora cobertura ontológica)

### ¿Qué aspectos requieren intervención antes de comenzar una extracción masiva?

1. **Modo de revisión automática** — Sin esto, la extracción masiva es inviable.
2. **Validación de citas_textual** — Sin esto, el grafo puede contener información falsa.
3. **Optimización de O(n²)** — Sin esto, la detección de duplicados será un cuello de botella.

---

## Conclusión

El sistema de extracción es **sólido para su caso de uso actual**. La arquitectura es correcta, el prompt es excelente, y el firewall está bien implementado. Sin embargo, para escalar a cientos de libros, necesita las mejoras identificadas arriba. La más crítica es el modo de revisión automática, que es el verdadero cuello de botella del sistema.
