# Plan: Implementar Vault Obsidian al Proyecto

> Basado en: `Respuesta IA/00_COMPARATIVA_CEREBRO_VS_RESPUESTA_IA.md`
> Estado actual: Ontología 100%, F3~60%, F4~60%, F5~75%, F6~45%, F7~30%, F8~0%

---

## Fase 0: Preparación (contexto para agente nuevo)

**Contexto:** Proyecto Cerebro Antropológico — grafo de conocimiento antropológico. Backend Python con pipeline de extracción PDF→LLM→SQLite. Frontend Vite + Cytoscape.js desplegado en Cloudflare Pages + D1. Ontología v1.1 con 8 tipos de nodo, 12+3 relaciones, firewall epistemológico. Código en español. Base de datos en `data/grafo.db` (~1433 nodos, 1137 relaciones).

**Archivos clave:**
- `contexto-mimo.md` — contexto completo del proyecto
- `instructions/INSTRUCTIONS.md` — reglas globales
- `pipeline/core/config.py` — tipos válidos, aliases, compatibilidad
- `pipeline/core/db.py` — validación, fusión, CRUD
- `pipeline/review/auditoria.py` — diagnóstico del grafo

---

## Orden de Ejecución

```
Fase 0 — Descontaminación (⚡ urgente, orden cerrado)
  │
  ├── ⚡ PASO 1: Limpiar términos raciales de cultura/poblacion
  ├── ⚡ PASO 3: Auditoría cultura→poblacion (inmediato tras cambio)
  ├── ⚡ PASO 5: Limpiar relaciones con tipos raciales (antes de backlog)
  └── ⚡ PASO 2: Distinción escuela↔corriente (tema distinto, cierra el bloque)
  │
  ├── PASO 4: Revisar redefine_a
  │
  ├── PASO 6: Revisar ~535 candidatos pendientes
  ├── PASO 7: Resolver ~376 nodos aislados
  ├── PASO 8: Resolver ~84 relaciones no resolubles
  │
  ├── PASO 9: Bloqueo relaciones-hasta-nodos-revisados (post-backlog)
  ├── PASO 10: Backfill cita_textual
  ├── PASO 11: Fase 7 restante (ecosistema, validación, cierre)
  ├── PASO 12: Validación Final (Fase 8 — 6 subfases)
  └── PASO 13: Exportar + deploy
```

**Nota sobre Paso 9 vs 6-8:** El bloqueo es una salvaguarda *permanente* (no un paso único). Se activa después de 6-8 porque si estuviera activo durante la resolución de aislados y candidatos, impediría crear relaciones hacia nodos que todavía no han pasado revisión formal (efecto huevo-gallina). Una vez que el backlog está resuelto, el bloqueo evita que nuevo código reintroduzca el mismo problema.

---

## ⚡ Paso 1: Limpiar términos raciales de cultura/poblacion

**Objetivo:** Eliminar/convertir ~122 nodos `cultura` que contienen contenido racial (tipos raciales del s. XIX que no son cultura). Esto es lo más urgente porque contamina el grafo.

**Tareas:**
1. Ejecutar auditoría (opción 4 del menú) para ver estado actual
2. Hacer query SQL para listar nodos tipo `cultura` con nombres sospechosos de contenido racial
3. Reclasificar como `poblacion` los que sean demográficos, eliminar los que sean ruido biomédico
4. Verificar que `EXCLUSIONES_FUSION_NOMBRES_NOMBRES` cubra los casos necesarios

**Verificación:** `python3 -m pipeline.cli.menu` → opción 4. Nodos cultura deben bajar de ~122, nodos poblacion deben aumentar.

**Branch:** `feat/limpiar-tipos-raciales`

---

## ⚡ Paso 2 (antes Paso 3): Auditoría de cultura → posibles poblacion

**Objetivo:** Inmediatamente después del cambio en Paso 1, auditar que los ~122 nodos `cultura` restantes estén correctamente clasificados: cuáles son genuinamente cultura (prácticas/creencias) vs cuáles deberían ser `poblacion` (origen/demografía).

**Tareas:**
1. Query SQL: `SELECT * FROM nodos WHERE tipo = 'cultura' ORDER BY nombre`
2. Clasificar cada uno: cultura genuina (prácticas/creencias) vs poblacion (origen/demografía)
3. Ejecutar reclasificación masiva para los que cambien de tipo
4. Verificar que el firewall epistemológico no se rompa (poblacion solo destino de estudia_a u origen de parte_del_debate)

**Verificación:** No debe haber `poblacion` relacionada con relaciones no permitidas por el firewall.

**Branch:** `feat/auditar-cultura`

---

## ⚡ Paso 3 (antes Paso 5): Limpiar relaciones con tipos raciales

**Objetivo:** Eliminar o reemplazar relaciones que usen tipos no canónicos como `clasifica_como_activo`, `clasifica_como_pasivo` (taxonomías raciales obsoletas). Se ejecuta aquí —antes de tocar backlog— para que nodos y relaciones estén limpios antes de revisar candidatos.

**Tareas:**
1. Buscar en DB relaciones con tipos no canónicos
2. Eliminar las que sean terminología racial del s. XIX
3. Verificar que no dejen nodos huérfanos
4. Actualizar aliases en config.py si es necesario

**Verificación:** `python3 -m pipeline.cli.menu` → opción 4. Tipos de relación deben ser solo los 15 canónicos (12A+3B).

**Branch:** `feat/limpiar-relaciones-raciales`

---

## ⚡ Paso 4 (antes Paso 2): Distinción escuela ↔ corriente

**Objetivo:** Resolver la ambigüedad entre ~12 `escuela` y ~6 `corriente`. Según la ontología: escuela = institución/sede/miembros identificables; corriente = tendencia sin organización formal.

**Tareas:**
1. Listar todos los nodos de tipo `escuela` y `corriente` con sus descripciones
2. Revisar cada uno contra el criterio ontológico
3. Reclasificar los que estén mal tipados
4. Actualizar descripciones de los ambiguos

**Verificación:** Cada `escuela` debe tener miembros identificables o sede. Cada `corriente` no debe tener organización formal.

**Branch:** `feat/escuela-corriente`

---

## Paso 5 (antes Paso 4): Revisar redefine_a

**Objetivo:** La ontología dice que `redefine_a` es una relación conceptual (Nivel B) que va de autor/obra/concepto → concepto. Verificar que no haya asimetrías o usos incorrectos.

**Tareas:**
1. Query SQL: listar todas las relaciones tipo `redefine_a`
2. Verificar que origen sea autor/obra/concepto y destino sea concepto
3. Corregir las que violen la compatibilidad
4. Decidir si `redefine_a` debe ser Nivel A o B según el Manifiesto

**Verificación:** Todas las `redefine_a` deben cumplir la matriz de compatibilidad.

**Branch:** `feat/redefine-a`

---

## Paso 6: Revisar candidatos pendientes (~535)

**Objetivo:** Procesar los ~535 candidatos en `runtime/cache/candidatos_pendientes.json` para reducir el backlog de relaciones sin resolver.

**Tareas:**
1. Ejecutar opción 1 del menú (revisión 1x1) para una muestra
2. Para lotes obvios, usar opción 2 (conexión automática bulk)
3. Identificar patrones de candidatos que siempre fallan
4. Decidir si ajustar prompts.py para mejor calidad de extracción

**Verificación:** El archivo `candidatos_pendientes.json` debe reducirse significativamente.

**Branch:** `feat/revisar-candidatos`

---

## Paso 7: Resolver nodos aislados (~376)

**Objetivo:** Conectar o eliminar los ~376 nodos que no tienen ninguna relación (26.2% del total).

**Tareas:**
1. Auditoría (opción 4) para lista actual de aislados
2. Revisar los que son ruido biomédico → eliminarlos (opción 9)
3. Revisar los que son nodos válidos pero sin relaciones → buscar relaciones potenciales en caché
4. Ejecutar opción 3 (recuperar relaciones) para rescatar relaciones perdidas

**Verificación:** El porcentaje de aislados debe bajar del 26.2% al menos al 15%.

**Branch:** `feat/resolver-aislados`

---

## Paso 8: Resolver relaciones no resolubles (~84)

**Objetivo:** Las ~84 relaciones que la herramienta de recuperación no pudo resolver porque el nodo destino no existía o el ID histórico no se pudo mapear.

**Tareas:**
1. Leer `herramienta_recuperar_relaciones` para entender el mapa de resolución
2. Revisar cada una de las 84 contra la DB actual
3. Para las que el nodo destino ahora existe, insertarlas manualmente
4. Para las que el nodo destino no existe, decidir si crear el nodo o descartar

**Verificación:** Las 84 relaciones deben quedar resueltas o explícitamente descartadas.

**Branch:** `feat/relaciones-no-resolubles`

---

## Paso 9: Implementar bloqueo relaciones-hasta-nodos-revisados

**Objetivo:** Que el pipeline no permita conectar relaciones si los nodos involucrados no han pasado revisión ontológica.

**Tareas:**
1. Añadir campo `revision_estado` en nodos (pendiente/revisado/ok)
2. Modificar `validar_relacion()` para bloquear si origen o destino no están revisados
3. Agregar opción en el menú para marcar nodos como revisados en lote
4. Actualizar tests

**Verificación:** Intentar conectar relación con nodo no-revisado debe fallar con mensaje claro.

**Branch:** `feat/bloqueo-relaciones`

---

## Paso 10: Backfill cita_textual

**Objetivo:** Recuperar citas textuales para relaciones que no tienen (opcional, mejora la calidad del grafo).

**Tareas:**
1. Query SQL: contar relaciones con/sin cita_textual
2. Buscar en `runtime/cache/candidatos_procesados_*.json` las citas originales
3. Hacer UPDATE masivo para las que se encuentren
4. Marcar las que definitivamente no tienen cita como `fuente_only`

**Verificación:** `SELECT COUNT(*) FROM relaciones WHERE cita_textual IS NOT NULL` debe aumentar.

**Branch:** `feat/backfill-citas`

---

## Paso 11: Backend — ecosistema, validación y cierre (07D, 07E, 07F)

**Objetivo:** Completar la documentación e implementación de los componentes faltantes de la Fase 7.

**Tareas:**
1. Leer/crear `07D. Implementación del Ecosistema.md` — plugins, exportaciones, APIs
2. Leer/crear `07E. Validación de la Implementación.md` — tests de integración
3. Leer/crear `07F. Cierre de Implementación.md` — documentación final
4. Implementar cualquier componente faltante identificado

**Verificación:** Los 3 documentos deben existir en Respuesta IA/ y el código debe cubrir lo que documentan.

**Branch:** `feat/fase7-restante`

---

## Paso 12: Validación Final (Fase 8 completa)

**Objetivo:** Ejecutar las 6 validaciones finales del Manifiesto: ontológica, consistencia, stress testing, científica, técnica, certificación.

**Tareas:**
1. **08A** — Validación ontológica: verificar cada nodo contra la ontología formal
2. **08B** — Consistencia global: integridad referencial, índices, unicidad
3. **08C** — Stress testing: cargar el grafo completo, medir tiempos de query
4. **08D** — Validación científica: los conceptos/relaciones tienen sentido antropológico
5. **08E** — Validación técnica: cobertura de tests, rendimiento, seguridad
6. **08F** — Certificación: informe final de conformidad

**Verificación:** Cada subfase produce un informe de PASS/FAIL. 08F solo pasa si todas las anteriores pasan.

**Branch:** `feat/validacion-final`

---

## Paso 13: Actualizar frontend con datos de producción

**Objetivo:** Exportar la DB limpia → `public/datos.json` → desplegar.

**Tareas:**
1. Opción 11 del menú (exportar)
2. Verificar que el JSON sea válido (formato que espera Cytoscape)
3. `npm run build && npm run preview` para probar local
4. Commit + push → deploy automático por CI/CD

**Verificación:** `https://cerebro-antropologico.pages.dev` muestra el grafo actualizado.

**Branch:** (se hace en main tras cada export)
