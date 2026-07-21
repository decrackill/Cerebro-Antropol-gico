# Plan de Evolución del Frontend — Versión Depurada

**Fecha**: 2026-07-21
**Estado**: Análisis depurado — sin modificaciones al código

---

## Filosofía

> **Mantener el frontend extremadamente simple mientras sea posible.**

Cada propuesta se evalúa con estos criterios:

- **Beneficio real**: ¿Resuelve un problema que existe HOY?
- **Riesgo**: ¿Puede romper algo existente?
- **Deuda técnica**: ¿Cuánto mantenimiento agrega?
- **Complejidad cognitiva**: ¿Cuánto complica la interfaz?
- **KISS**: ¿Mantiene la simplicidad?
- **YAGNI**: ¿Es necesario AHORA?

---

## Categoría A: Implementar Inmediatamente

Estas mejoras resuelven problemas que ya existen con 394 nodos.

### A1. Centrar nodo al buscar

| Campo | Valor |
|-------|-------|
| **Problema** | Después de buscar, el usuario no ve el resultado |
| **Causa** | `buscarNodo()` solo filtra, no centra |
| **Solución** | Después de filtrar, hacer zoom al primer resultado |
| **Beneficio real** | ALTO — La búsqueda se vuelve útil |
| **Riesgo** | BAJO — Solo agrega comportamiento |
| **Deuda técnica** | NINGUNA |
| **Complejidad cognitiva** | NULA — Comportamiento esperado |
| **KISS** | ✅ Mantiene simplicidad |
| **YAGNI** | ✅ Necesario ahora |

### A2. Resaltar aristas conectadas al seleccionar

| Campo | Valor |
|-------|-------|
| **Problema** | No se ve qué aristas pertenecen al nodo seleccionado |
| **Causa** | Solo se resalta el panel, no el grafo |
| **Solución** | Agregar clase `seleccionado` al nodo y sus aristas |
| **Beneficio real** | ALTO — Claridad visual inmediata |
| **Riesgo** | BAJO — Solo CSS + una línea de JS |
| **Deuda técnica** | NINGUNA |
| **Complejidad cognitiva** | NULA — Comportamiento esperado |
| **KISS** | ✅ Mantiene simplicidad |
| **YAGNI** | ✅ Necesario ahora |

### A3. Resaltar vecinos al seleccionar

| Campo | Valor |
|-------|-------|
| **Problema** | No se ve qué nodos están conectados directamente |
| **Causa** | No hay feedback visual de vecindario |
| **Solución** | Atenuar nodos no relacionados, resaltar vecinos |
| **Beneficio real** | ALTO — Exploración visual |
| **Riesgo** | BAJO — Solo clases CSS |
| **Deuda técnica** | NINGUNA |
| **Complejidad cognitiva** | BAJA — Patrón estándar |
| **KISS** | ✅ Mantiene simplicidad |
| **YAGNI** | ✅ Necesario ahora |

### A4. Mostrar grado en panel

| Campo | Valor |
|-------|-------|
| **Problema** | No se sabe cuántas relaciones tiene un nodo sin contar |
| **Causa** | El panel no muestra el grado |
| **Solución** | Agregar línea "Grado: X" en el panel |
| **Beneficio real** | MEDIO — Info inmediata |
| **Riesgo** | NULO |
| **Deuda técnica** | NINGUNA |
| **Complejidad cognitiva** | NULA |
| **KISS** | ✅ Mantiene simplicidad |
| **YAGNI** | ✅ Necesario ahora |

### A5. Loading spinner

| Campo | Valor |
|-------|-------|
| **Problema** | No hay feedback al cargar 263KB de JSON |
| **Causa** | Sin estados de carga |
| **Solución** | Spinner simple mientras carga datos.json |
| **Beneficio real** | BAJO — Pero es práctica básica |
| **Riesgo** | NULO |
| **Deuda técnica** | NINGUNA |
| **Complejidad cognitiva** | NULA |
| **KISS** | ✅ Mantiene simplicidad |
| **YAGNI** | ✅ Práctica básica |

---

## Categoría B: Depende de Evidencia Futura

Solo implementar cuando las métricas demuestren el problema.

### B1. Debounce en búsqueda

| Campo | Valor |
|-------|-------|
| **Problema** | Cada tecla ejecuta filtrado inmediatamente |
| **Evidencia necesaria** | ¿El usuario siente lag al buscar? ¿Con cuántos nodos? |
| **Umbral de activación** | >2,000 nodos o quejas de usuario |
| **Beneficio real** | DESCONOCIDO — No hay evidencia de lag actual |
| **Riesgo** | BAJO |
| **Deuda técnica** | MÍNIMA |
| **KISS** | ⚠️ Agrega lógica |
| **YAGNI** | ⚠️ No sabemos si es necesario |

### B2. Mostrar total de nodos visibles

| Campo | Valor |
|-------|-------|
| **Problema** | No se sabe cuántos nodos están visibles |
| **Evidencia necesaria** | ¿El usuario necesita saber esto? ¿Lo consulta? |
| **Umbral de activación** | Cuando el usuario lo pida o cuando >1,000 nodos |
| **Beneficio real** | DESCONOCIDO — Puede ser ruido visual |
| **Riesgo** | NULO |
| **Deuda técnica** | NINGUNA |
| **KISS** | ⚠️ Agrega info visual |
| **YAGNI** | ⚠️ No sabemos si es necesario |

### B3. Métricas en panel

| Campo | Valor |
|-------|-------|
| **Problema** | No se ven métricas de calidad del grafo |
| **Evidencia necesaria** | ¿El investigador necesita ver métricas en el panel? |
| **Umbral de activación** | Cuando el usuario lo pida |
| **Beneficio real** | DESCONOCIDO — Puede ser ruido |
| **Riesgo** | NULO |
| **Deuda técnica** | MÍNIMA |
| **KISS** | ⚠️ Agrega info |
| **YAGNI** | ⚠️ No sabemos si es necesario |

### B4. Historial de navegación (back/forward)

| Campo | Valor |
|-------|-------|
| **Problema** | No se puede volver al nodo anterior |
| **Evidencia necesaria** | ¿El usuario necesita volver atrás? ¿Con qué frecuencia? |
| **Umbral de activación** | Cuando el usuario lo pida o cuando >500 nodos |
| **Beneficio real** | DESCONOCIDO — Puede no ser necesario si el panel muestra todo |
| **Riesgo** | MEDIO — Agrega estado complejo |
| **Deuda técnica** | MEDIA — Requiere stack de navegación |
| **KISS** | ❌ Agrega estado significativo |
| **YAGNI** | ⚠️ No sabemos si es necesario |

### B5. Breadcrumbs

| Campo | Valor |
|-------|-------|
| **Problema** | No se sabe cómo se llegó al nodo actual |
| **Evidencia necesaria** | ¿El usuario se pierde en exploración profunda? |
| **Umbral de activación** | Cuando el usuario lo pida |
| **Beneficio real** | DESCONOCIDO — Puede ser ruido |
| **Riesgo** | BAJO |
| **Deuda técnica** | MÍNIMA |
| **KISS** | ⚠️ Agrega UI |
| **YAGNI** | ⚠️ No sabemos si es necesario |

### B6. Filtros combinables

| Campo | Valor |
|-------|-------|
| **Problema** | Solo se puede filtrar por un tipo a la vez |
| **Evidencia necesaria** | ¿Alguien necesita ver autores Y conceptos juntos? |
| **Umbral de activación** | Cuando el usuario lo pida |
| **Beneficio real** | DESCONOCIDO — Puede no ser necesario |
| **Riesgo** | BAJO |
| **Deuda técnica** | MÍNIMA |
| **KISS** | ✅ Checkboxes son simples |
| **YAGNI** | ⚠️ No sabemos si es necesario |

### B7. Información al hover

| Campo | Valor |
|-------|-------|
| **Problema** | No se ve info del nodo al pasar el mouse |
| **Evidencia necesaria** | ¿El usuario necesita info al hover? |
| **Umbral de activación** | Cuando el usuario lo pida |
| **Beneficio real** | DESCONOCIDO — Puede ser distracción |
| **Riesgo** | BAJO |
| **Deuda técnica** | MÍNIMA |
| **KISS** | ✅ Comportamiento estándar |
| **YAGNI** | ⚠️ No sabemos si es necesario |

### B8. Atajos de teclado

| Campo | Valor |
|-------|-------|
| **Problema** | Todo se hace con mouse |
| **Evidencia necesaria** | ¿Hay usuarios que usen el sistema horas seguidas? |
| **Umbral de activación** | Cuando el usuario lo pida |
| **Beneficio real** | DESCONOCIDO — Solo para power users |
| **Riesgo** | BAJO |
| **Deuda técnica** | MÍNIMA |
| **KISS** | ✅ No cambia UI |
| **YAGNI** | ⚠️ No sabemos si es necesario |

### B9. Botón "fit to content"

| Campo | Valor |
|-------|-------|
| **Problema** | No se puede recuperar vista después de hacer zoom extremo |
| **Evidencia necesaria** | ¿El usuario se pierde después de hacer zoom? |
| **Umbral de activación** | Cuando el usuario lo pida |
| **Beneficio real** | DESCONOCIDO |
| **Riesgo** | NULO |
| **Deuda técnica** | NINGUNA |
| **KISS** | ✅ Un botón simple |
| **YAGNI** | ⚠️ No sabemos si es necesario |

### B10. Diferenciación visual por tipo de arista

| Campo | Valor |
|-------|-------|
| **Problema** | Todas las aristas son iguales visualmente |
| **Evidencia necesaria** | ¿El usuario necesita distinguir tipos de relación? |
| **Umbral de activación** | Cuando el usuario lo pida |
| **Beneficio real** | DESCONOCIDO — Puede ser ruido visual |
| **Riesgo** | MEDIO — Agrega complejidad visual |
| **Deuda técnica** | MÍNIMA |
| **KISS** | ⚠️ Agrega complejidad visual |
| **YAGNI** | ⚠️ No sabemos si es necesario |

### B11. Aislamiento de vecindario

| Campo | Valor |
|-------|-------|
| **Problema** | Imposible ver solo las conexiones de un nodo |
| **Evidencia necesaria** | ¿El grafo completo es ilegible con cuántos nodos? |
| **Umbral de activación** | >2,000 nodos |
| **Beneficio real** | DESCONOCIDO — Aún no tenemos suficientes nodos |
| **Riesgo** | MEDIO — Agrega lógica compleja |
| **Deuda técnica** | MEDIA |
| **KISS** | ❌ Agrega herramienta compleja |
| **YAGNI** | ⚠️ No sabemos si es necesario todavía |

### B12. Autocompletado en búsqueda

| Campo | Valor |
|-------|-------|
| **Problema** | No hay dropdown de sugerencias |
| **Evidencia necesaria** | ¿El usuario necesita encontrar nodos por nombre parcial? |
| **Umbral de activación** | >1,000 nodos |
| **Beneficio real** | DESCONOCIDO |
| **Riesgo** | BAJO |
| **Deuda técnica** | MÍNIMA |
| **KISS** | ✅ Comportamiento estándar |
| **YAGNI** | ⚠️ No sabemos si es necesario |

---

## Categoría C: Arquitectura a Largo Plazo

No planificar estas mejoras todavía. Solo documentarlas como posibles líneas futuras.

### C1. Virtualización de nodos

- **Cuándo**: >5,000 nodos
- **Qué es**: Solo renderizar nodos visibles en el viewport
- **Por qué no ahora**: Con 394 nodos no hay problema de performance

### C2. Lazy loading de datos

- **Cuándo**: >10,000 nodos
- **Qué es**: Cargar datos bajo demanda desde el backend
- **Por qué no ahora**: 263KB se cargan instantáneamente

### C3. Backend real con API

- **Cuándo**: >20,000 nodos
- **Qué es**: REST API con paginación y filtros
- **Por qué no ahora**: El JSON estático funciona perfectamente

### C4. Layout incremental

- **Cuándo**: >10,000 nodos
- **Qué es**: Calcular layout solo para nodos nuevos
- **Por qué no ahora**: fcose funciona rápido con 394 nodos

### C5. Clustering visual

- **Cuándo**: >5,000 nodos
- **Qué es**: Agrupar nodos por tipo/relación en clusters
- **Por qué no ahora**: El grafo actual es manejable

### C6. Modo tabla/lista

- **Cuándo**: Cuando el usuario lo pida
- **Qué es**: Alternativa de vista en tabla
- **Por qué no ahora**: El grafo visual es la mejor interfaz para 394 nodos

### C7. Comparación dual de nodos

- **Cuándo**: Cuando el usuario lo pida
- **Qué es**: Panel para comparar dos nodos lado a lado
- **Por qué no ahora**: No hay evidencia de que sea necesario

### C8. Panel de análisis de camino

- **Cuándo**: Cuando el usuario lo pida
- **Qué es**: Herramienta para encontrar caminos entre nodos
- **Por qué no ahora**: No hay evidencia de que sea necesario

### C9. Guardar/cargar vistas

- **Cuándo**: Cuando el usuario lo pida
- **Qué es**: Persistencia de estado del grafo
- **Por qué no ahora**: No hay evidencia de que sea necesario

### C10. Minimapa

- **Cuándo**: >5,000 nodos
- **Qué es**: Indicador de posición en el grafo
- **Por qué no ahora**: Con 394 nodos es fácil orientarse

### C11. Responsive design

- **Cuándo**: Cuando el usuario necesite usar en móvil
- **Qué es**: Adaptar interfaz a pantallas pequeñas
- **Por qué no ahora**: No hay evidencia de uso móvil

### C12. Exportación de subgrafo

- **Cuándo**: Cuando el usuario lo pida
- **Qué es**: Exportar selección del grafo
- **Por qué no ahora**: No hay evidencia de que sea necesario

---

## Categoría D: Descartar

Estas propuestas agregan complejidad innecesaria o violan principios.

### D1. Herramienta de medición

| Campo | Valor |
|-------|-------|
| **Propuesta** | Medir distancia entre nodos |
| **Por qué descartar** | No hay evidencia de que sea necesario. Agrega工具a que nadie pidió |
| **KISS** | ❌ Agrega工具a innecesaria |
| **YAGNI** | ❌ Nadie lo pidió |

### D2. Zoom a selección (como herramienta separada)

| Campo | Valor |
|-------|-------|
| **Propuesta** | Botón para hacer zoom a la selección actual |
| **Por qué descartar** | `saltarANodo()` ya hace zoom. Agregar otro botón es redundante |
| **KISS** | ❌ Duplica funcionalidad |
| **YAGNI** | ❌ Ya existe funcionalidad similar |

### D3. Barra de estado dedicada

| Campo | Valor |
|-------|-------|
| **Propuesta** | Barra inferior con métricas en tiempo real |
| **Por qué descartar** | Con 394 nodos es innecesario. Puede implementarse como opción si se necesita |
| **KISS** | ❌ Agrega UI permanente |
| **YAGNI** | ⚠️ No sabemos si es necesario |

### D4. Mostrar/ocultar leyenda

| Campo | Valor |
|-------|-------|
| **Propuesta** | Botón para ocultar la leyenda |
| **Por qué descartar** | La leyenda ocupa poco espacio. Agregar un botón para ocultarla es over-engineering |
| **KISS** | ❌ Agrega UI innecesaria |
| **YAGNI** | ❌ Nadie pidió ocultar la leyenda |

### D5. Layout circular/jerárquico

| Campo | Valor |
|-------|-------|
| **Propuesta** | Alternar entre layout force-directed y circular |
| **Por qué descartar** | fcose es el mejor layout para exploración. Otros layouts son peores para grafo de conocimiento |
| **KISS** | ❌ Agrega opciones innecesarias |
| **YAGNI** | ❌ fcose funciona bien |

### D6. Colores personalizables

| Campo | Valor |
|-------|-------|
| **Propuesta** | Permitir al usuario cambiar colores |
| **Por qué descartar** | Los colores están bien diseñados. Personalizarlos agrega complejidad sin beneficio |
| **KISS** | ❌ Agrega configuración innecesaria |
| **YAGNI** | ❌ Nadie pidió cambiar colores |

### D7. Tema claro/oscuro

| Campo | Valor |
|-------|-------|
| **Propuesta** | Alternar entre tema claro y oscuro |
| **Por qué descartar** | El tema oscuro es mejor para grafos (menos fatiga visual). No hay razón para cambiar |
| **KISS** | ❌ Agrega configuración innecesaria |
| **YAGNI** | ❌ El tema oscuro funciona bien |

### D8. Persistencia de estado en localStorage

| Campo | Valor |
|-------|-------|
| **Propuesta** | Guardar posiciones y configuración en localStorage |
| **Por qué descartar** | El layout se recalcula en cada carga. Guardar posiciones puede causar inconsistencias |
| **KISS** | ❌ Agrega estado complejo |
| **YAGNI** | ❌ No hay evidencia de que sea necesario |

---

## Resumen de Decisión

| Categoría | Cantidad | Acción |
|-----------|----------|--------|
| **A: Inmediato** | 5 | Implementar ahora |
| **B: Evidencia futura** | 12 | Esperar métricas |
| **C: Largo plazo** | 12 | No planificar |
| **D: Descartar** | 8 | No implementar |

### Próximos Pasos

1. Implementar solo las 5 mejoras de categoría A
2. Recolectar métricas de uso con 394 nodos
3. Procesar más libros y observar problemas reales
4. Recién então evaluar si alguna categoría B es necesaria

### Lo Que NO Hacer

- No implementar nada de categoría C todavía
- No implementar nada de categoría D nunca
- No diseñar para 100,000 nodos sin evidencia
- No agregar funcionalidades "por si acaso"
- No violar KISS ni YAGNI

---

## Criterio de Éxito

> **El frontend debe seguir siendo un solo archivo render.js de ~250 líneas que cualquier desarrollador pueda entender en 10 minutos.**

Si alguna mejora rompe este criterio, no se implementa.
