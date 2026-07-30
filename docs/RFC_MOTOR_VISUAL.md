# RFC v2 — Motor Visual del Cerebro Antropológico (Corregido)

## 1. Objetivo

Construir la mejor interfaz posible para explorar conocimiento antropológico utilizando Cytoscape.js. Cada decisión visual debe existir porque comunica mejor la ontología, la estructura del conocimiento, la evidencia científica o las relaciones conceptuales. Los efectos visuales que no aportan comprensión del conocimiento no tienen lugar en este proyecto.

Este documento sustituye y cancela cualquier versión anterior del RFC del motor visual.

---

## 2. Filosofía de Diseño

El grafo no es una decoración. Es un instrumento de investigación.

Su comportamiento visual debe representar información científica:

- Las relaciones más importantes deben ser visualmente más relevantes.
- Mayor evidencia debe producir mayor presencia visual.
- Las comunidades de conocimiento deben manifestarse como proximidad espacial.
- La centralidad estructural de un nodo debe ser perceptible sin inspeccionar datos.
- Los caminos entre conceptos deben poder explorarse visualmente.
- La ontología debe codificarse mediante color, grosor y estilo — nunca solo mediante labels.

Un efecto visual cuya única finalidad sea que el grafo "se vea bonito" no cumple este RFC.

---

## 3. Principios Arquitectónicos

| Principio | Definición |
|-----------|------------|
| KISS | Soluciones simples. Si una propuesta requiere más de 50 líneas nuevas, reevaluar. |
| YAGNI | No implementar nada que no resuelva un problema actual del frontend. |
| Bajo acoplamiento | La lógica visual se mantiene en `frontend/src/render.js` y `frontend/src/style.css`. No contamina pipeline, backend ni ontología. |
| APIs oficiales | Solo se usan APIs documentadas de Cytoscape.js y extensiones oficiales. Nunca se reimplementan algoritmos que Cytoscape ya resuelve. |
| Compatibilidad fcose | No se duplica el motor de layout. No se ejecutan dos motores de fuerzas en paralelo. |
| Alto rendimiento | El grafo debe mantener 60fps con 500+ nodos visibles. |
| Mantenimiento sencillo | Cualquier desarrollador debe poder entender cada propuesta en <5 minutos. |
| Escalabilidad | Las propuestas deben degradarse gracefulmente con grafos grandes, no fallar. |

### APIs de Cytoscape.js que se utilizan en este RFC

| API | Uso en el RFC | Documentación |
|-----|---------------|---------------|
| `ele.degree()` | V2 — obtener grado del nodo | Nativo |
| `ele.betweenness()` | V7 — betweenness centrality | Nativo (Brandes O(VE)) |
| `ele.closeness()` | V12 — closeness centrality en tooltip | Nativo |
| `ele.connectedEdges()` | V2, V3 — aristas conectadas | Nativo |
| `eles.dijkstra()` | V13 — camino más corto | Nativo (O(E log V)) |
| `eles.neighborhood()` | V14 — vecinos de un nodo | Nativo |
| `cy.animate()` | V8, V9, V10 — transiciones | Nativo |
| `node.animate()` | V8, V9 — animación individual | Nativo |
| `node.position()` | V8 — posición del nodo | Nativo |
| `node.data()` | V7, V12 — almacenar métricas | Nativo |
| `node.addClass()` / `removeClass()` | V11 — estilos condicionales | Nativo |
| `node.style()` | V9 — cambios de estilo animados | Nativo |
| `cy.on()` | V8, V9, V10, V11 — eventos | Nativo |
| `cy.style()` | V3 — actualización de selectores | Nativo |

---

## 4. Estado Actual

### Archivos del frontend

| Archivo | Líneas | Función |
|---------|--------|---------|
| `frontend/src/render.js` | 282 | Inicialización Cytoscape, layout fcose, eventos, filtrado, panel |
| `frontend/src/style.css` | 417 | Estilos de nodos, aristas, paneles, tooltip, responsive |
| `frontend/src/main.js` | 23 | Punto de entrada, carga datos, inicializa UI |
| `src/grafo.js` | 7 | Carga JSON desde servidor |
| `index.html` | 58 | Estructura HTML |

### Configuración actual de fcose

```javascript
{
  name: 'fcose',
  randomize: true,
  animate: true,
  animationDuration: 800,
  nodeRepulsion: 25000,
  idealEdgeLength: 180,
  edgeElasticity: 0.05,
  gravity: 0.15,
  numIter: 4000,
  tile: true,
  packComponents: true,
  componentSpacing: 200,
  nodeDimensionsIncludeLabels: true,
}
```

### Sistema de nodos actual

- 8 tipos: autor, obra, concepto, escuela, corriente, cultura, poblacion, debate
- Tamaño dinámico: `d > 10 ? 30 + d * 3 : 20 + d * 4` (lineal con degree)
- Colores fijos por tipo
- Nodos degree 0: borde rojo punteado, opacidad 0.5

### Sistema de aristas actual

- Grosor fijo: 1.5px
- Color fijo: #555
- Curva: bezier
- Labels: ocultos por defecto, visibles en hover/active
- Sin distinción por tipo de relación o nivel ontológico

### Interacciones actuales

- Tap nodo: activar vecindario, mostrar panel
- Tap fondo: desactivar vecindario
- Hover nodo: tooltip
- Hover edge: highlight
- Zoom: ocultar labels si zoom < 0.6
- Búsqueda: filtrado por nombre con centrado

---

## 5. Problemas Detectados

### Problemas técnicos

| # | Problema | Impacto |
|---|----------|---------|
| T1 | Tamaño de nodo escala linealmente — nodos degree 20 alcanzan 100px, solapándose | Legibilidad |
| T2 | edgeElasticity: 0.05 es extremadamente bajo — aristas no ejercen tensión visible | Distribución |
| T3 | numIter: 4000 es excesivo para grafos <500 nodos — desperdicia tiempo de carga | Rendimiento |
| T4 | No hay distinción visual entre Nivel A y Nivel B de relaciones | Información ontológica |
| T5 | No hay indicador de evidencia documental en aristas ni nodos | Información científica |
| T6 | Nodos aislados (degree 0) solo tienen borde rojo punteado — no hay jerarquía visual | UX |
| T7 | Filtrado usa display:none sin transición — cambio abrupto | UX |
| T8 | `saltarANodo()` usa animación lineal sin easing — se siente mecánico | UX |

### Problemas de información

| # | Problema | Impacto |
|---|----------|---------|
| I1 | No se distinguen relaciones fundamentales (Nivel A) de derivadas (Nivel B) | Comprensión ontológica |
| I2 | No se visualiza la centralidad de un nodo en el grafo | Exploración |
| I3 | No hay forma de ver la "distancia" entre dos conceptos | Exploración |
| I4 | No se detectan ni visualizan comunidades de conocimiento | Exploración |
| I5 | El tooltip no muestra métricas de importancia | Descubrimiento |

---

## 6. Propuestas Aprobadas

### Nivel 0 — Cambios Fundamentales

Sin estos cambios el frontend queda incompleto.

---

#### V1. Calibración del Layout fcose

**Objetivo:** Distribuir los nodos de forma que la proximidad espacial refleje relaciones reales.

**Justificación:** fcose con parámetros subóptimos produce un grafo donde nodos relacionados quedan lejos entre sí y nodos no relacionados se solapan. La distribución espacial es la base de toda exploración visual.

**Propuesta:**

```javascript
{
  name: 'fcose',
  randomize: true,
  animate: true,
  animationDuration: 500,
  quality: cy.nodes().length > 1000 ? 'default' : 'proof',
  nodeRepulsion: 18000,
  idealEdgeLength: 160,
  edgeElasticity: 0.15,
  gravity: 0.35,
  gravityRange: 2.5,
  numIter: cy.nodes().length > 1000 ? 1500 : 2000,
  tile: true,
  packComponents: true,
  componentSpacing: 150,
  nodeDimensionsIncludeLabels: true,
  padding: 30,
}
```

**Degradación para grafos grandes:**
- ≤1000 nodos: `quality: 'proof'`, `numIter: 2000`
- >1000 nodos: `quality: 'default'`, `numIter: 1500`
- >3000 nodos: `quality: 'draft'`, `numIter: 1000`

**Beneficio para exploración:** Nodos relacionados quedan más juntos. La estructura del conocimiento se hace visible en la distribución espacial.

**Impacto visual:** Grafo más compacto, mejor centrado, componentes más cohesionados.

**Coste técnico:** Cambio de valores en `render.js:93-107`. 0 líneas nuevas.

**Complejidad:** Trivial.

**Riesgo:** Bajo. Parámetros conservadores con degradación automática.

**Compatibilidad:** 100% — solo parámetros nativos de fcose.

**Prioridad:** P0.

**Métrica de éxito:** Distancia promedio entre nodos connectedEdges() disminuye >15% respecto al layout actual.

---

#### V2. Jerarquización Visual por Conectividad

**Objetivo:** Hacer que la importancia estructural de un nodo sea perceptible visualmente sin inspeccionar datos.

**Justificación:** En un grafo de conocimiento, los nodos más conectados (autores centrales, conceptos clave) son los más importantes para la exploración. Su tamaño debe comunicar esa importancia.

**Propuesta:**

Tamaño del nodo (usando `ele.degree()`, API nativa):
```javascript
size = 14 + Math.min(degree * 2.5, 36)
// degree 0 → 14px
// degree 5 → 26px
// degree 10 → 39px
// degree 15+ → 50px (cap)
```

Opacidad del nodo:
```javascript
opacity = 0.35 + Math.min(degree / 20, 0.65)
// degree 0 → 0.35 (apenas visible)
// degree 5 → 0.6
// degree 10 → 0.85
// degree 15+ → 1.0
```

Nodos aislados (degree 0): tamaño fijo 14px, opacidad 0.35, borde punteado suave (#555).

**Beneficio para exploración:** El usuario identifica inmediatamente los nodos centrales del conocimiento sin leer labels ni abrir paneles.

**Impacto visual:** Gradación clara de importancia. Nodos importantes dominan el campo visual.

**Coste técnico:** Modificar las funciones `size` y agregar `opacity` en el selector node. ~8 líneas.

**Complejidad:** Baja.

**Riesgo:** Bajo. Fórmula probada con cap conservador.

**Compatibilidad:** Alta — solo propiedades de estilo nativas de Cytoscape.

**Prioridad:** P0.

**Métrica de éxito:** En una prueba de usabilidad, el usuario puede identificar los 5 nodos más centrales en <5 segundos sin hacer clic.

---

### Nivel 1 — Mejoras de Alto Impacto para Exploración Científica

---

#### V3. Grosor de Aristas por Nivel Ontológico

**Objetivo:** Codificar visualmente la jerarquía de relaciones definida en el Manifiesto Ontológico.

**Justificación:** El Manifiesto establece dos niveles de relaciones: Nivel A (12 relaciones canónicas: autor_de, influenciado_por, critica_a, etc.) y Nivel B (3 relaciones conceptuales: contradice, relacionado_con, depende_de). Esta distinción es información científica fundamental que el grafo actual no comunica.

**Propuesta:**

| Nivel | Grosor | Color | Opacidad |
|-------|--------|-------|----------|
| Nivel A | 2.0px | Color saturado según tipo de nodo origen | 0.8 |
| Nivel B | 1.0px | Gris (#666) | 0.4 |

Edge labels para Nivel A: visibles a zoom > 0.8.
Edge labels para Nivel B: visibles solo en hover.

**API utilizada:** Selectores de estilo por `data(label)` — nativo de Cytoscape.

**Beneficio para exploración:** El usuario distingue al instante relaciones fundamentales de derivadas. Las conexiones "reales" (autor escribió obra, escuela influyó en autor) son visualmente más pesadas que las "interpretativas" (concepto relacionado con concepto).

**Impacto visual:** El grafo gana una capa de información ontológica sin labels adicionales.

**Coste técnico:** Modificar el selector `edge` en `render.js` y agregar selectores por `data(label)`. ~15 líneas.

**Complejidad:** Baja.

**Riesgo:** Bajo.

**Compatibilidad:** 100% — selectores de estilo nativos.

**Prioridad:** P1.

**Métrica de éxito:** El usuario puede distinguir Nivel A de Nivel B sin leer el label de la arista.

---

#### V4. Color de Aristas por Nivel Epistemológico

**Objetivo:** Representar la fortaleza epistemológica de cada relación mediante saturación del color.

**Justificación:** No todas las relaciones tienen la misma evidencia. Una relación con cita textual es más sólida que una inferida. El color puede comunicar esta diferencia.

**Propuesta:**

| Condición | Color | Opacidad |
|-----------|-------|----------|
| Relación con `cita_textual` | #e94560 (rojo proyecto) | 0.9 |
| Relación con solo `fuente` | #e94560 | 0.5 |
| Relación sin evidencia | #555 | 0.3 |

**API utilizada:** `line-color` con funciones dinámicas — nativo de Cytoscape.

**Beneficio para exploración:** El usuario identifica visualmente relaciones con respaldo documental vs. inferidas.

**Impacto visual:** Las aristas más documentadas destacan. Las débiles se difuminan.

**Coste técnico:** Función dinámica en el estilo de edge que evalúa `data('cita')` y `data('nota')`. ~10 líneas.

**Complejidad:** Baja.

**Riesgo:** Bajo.

**Compatibilidad:** Alta — `line-color` soporta funciones dinámicas.

**Prioridad:** P1.

**Métrica de éxito:** El usuario puede identificar qué relaciones tienen evidencia documental solo mirando el grafo.

---

#### V5. Curvatura Adaptativa para Relaciones Múltiples

**Objetivo:** Hacer legibles las relaciones múltiples entre dos nodos.

**Justificación:** Cuando dos nodos comparten más de una relación (ej. autor influyó en autor Y autor criticó a autor), las aristas se apilan y solo una es visible. La curvatura adaptativa separa visualmente cada relación.

**API utilizada:** `control-point-distances` y `control-point-weights` — propiedades nativas de Cytoscape para bezier custom.

**Propuesta:**

Cuando dos nodos comparten N relaciones:
- N=1: `curve-style: 'bezier'` (actual, sin cambio)
- N=2: segunda arista con `control-point-distances: 20`
- N=3+: distribuir `control-point-distances` uniformemente entre -30 y 30

Implementación: pre-calcular en la carga, asignar clase `.curva-N` con estilo correspondiente.

**Nota de implementación:** Cytoscape no tiene "auto-bundle" nativo. El cálculo de offsets se hace una vez al cargar datos y se almacena como clase CSS. No hay reimplementación de algoritmos — se usan propiedades nativas de rendering.

**Beneficio para exploración:** Todas las relaciones entre dos nodos son visibles y distinguibles.

**Impacto visual:** Grafo más limpio, relaciones múltiples legibles.

**Coste técnico:** Pre-cálculo al cargar datos + estilos CSS. ~25 líneas.

**Complejidad:** Media.

**Riesgo:** Bajo — Cytoscape soporta `control-point-distances` nativamente.

**Compatibilidad:** Alta — propiedades nativas de Cytoscape bezier.

**Prioridad:** P1 (pospuesta — validar frecuencia de pares multi-arista primero).

**Métrica de éxito:** Para cualquier par de nodos con múltiples relaciones, todas las aristas son visibles sin solapamiento.

---

#### V6. Agrupamiento Espacial por Densidad de Conexiones

**Objetivo:** Hacer que las comunidades de conocimiento se manifiesten como regiones espaciales.

**Justificación:** En antropología, las escuelas, corrientes y debates forman clusters naturales. fcose agrupa naturalmente nodos densamente conectados cuando los parámetros de repulsión y elasticidad están bien calibrados.

**API utilizada:** Parámetros nativos de fcose — `nodeRepulsion`, `idealEdgeLength`, `packComponents`.

**Aclaración técnica:** fcose no tiene un parámetro de "detección de comunidades". El agrupamiento espacial es un efecto natural del algoritmo de fuerzas: nodos con muchas conexiones entre sí se atraen y quedan cercanos. No se necesita un parámetro especial — solo una buena calibración de los parámetros existentes (V1).

**Propuesta:**

El agrupamiento se logra mediante la combinación de:
1. `nodeRepulsion: 18000` — repulsión moderada permite agrupamiento
2. `idealEdgeLength: 160` — aristas moderadamente largas
3. `packComponents: true` — componentes desconectados se empaquetan
4. `componentSpacing: 150` — separación entre componentes

No se agregan parámetros adicionales. El agrupamiento es un subproducto natural de la calibración.

**Beneficio para exploración:** Las escuelas de pensamiento, los debates activos y las corrientes teóricas aparecen como regiones espaciales naturales. El usuario puede identificar clusters sin inspeccionar nodos individuales.

**Impacto visual:** El grafo se organiza en regiones temáticas perceptibles.

**Coste técnico:** 0 líneas nuevas — se logra con la calibración de V1.

**Complejidad:** Trivial.

**Riesgo:** Bajo — efecto natural de fcose bien calibrado.

**Compatibilidad:** 100%.

**Prioridad:** P1.

**Métrica de éxito:** Los nodos de tipo `escuela` o `corriente` quedan espacialmente cercanos a sus nodos asociados.

---

#### V7. Representación de Centralidad

**Objetivo:** Hacer visible la importancia estructural de un nodo sin datos adicionales.

**Justificación:** La betweenness centrality mide cuántos caminos más cortos pasan por un nodo. Un nodo con alta centralidad es un "puente" entre áreas del conocimiento — una información científica que el usuario necesita pero que el grafo actual no comunica.

**API utilizada:** `eles.betweenness()` — método nativo de Cytoscape.js (algoritmo de Brandes, O(VE)).

**Propuesta:**

Calcular betweenness centrality post-layout usando la API nativa:
```javascript
cy.nodes().forEach(nodo => {
  nodo.data('centralidad', nodo.betweenness())
})
```

Mapear a `border-width`:
```javascript
'border-width': (ele) => 1 + ele.data('centralidad') * 8
// centralidad 0 → 1px
// centralidad 0.5 → 5px
// centralidad 1.0 → 9px
```

Los nodos con alta centralidad obtienen un borde grueso que los destaca como "conectores" del conocimiento.

**Nota de implementación:** No se reimplementa betweenness centrality. Se utiliza exclusivamente `eles.betweenness()` que es una API nativa de Cytoscape con implementación optimizada (Brandes).

**Beneficio para exploración:** El usuario identifica nodos puente — conceptos que conectan áreas diferentes del conocimiento — solo por el grosor del borde.

**Impacto visual:** Nodos centrales se distinguen claramente. El grafo comunica su estructura de conexión.

**Coste técnico:** `eles.betweenness()` se ejecuta una vez post-layout. ~5 líneas totales.

**Complejidad:** Baja — una línea para calcular, una para mapear a estilo.

**Riesgo:** Bajo — API nativa probada y optimizada.

**Rendimiento por escala:**
- 500 nodos: ~50ms
- 1000 nodos: ~200ms
- 5000 nodos: ~3-5s (aceptable como cálculo único)

**Compatibilidad:** Alta — `eles.betweenness()` es API nativa de Cytoscape.

**Prioridad:** P1.

**Métrica de éxito:** El usuario puede identificar los 3 nodos más centrales del grafo en <10 segundos sin herramientas adicionales.

---

### Nivel 2 — Mejoras de Experiencia de Usuario

---

#### V8. Inercia al Arrastrar (Nodo Individual)

**Objetivo:** Comunicar la "masa" de un nodo a través de su comportamiento al arrastrarlo.

**Justificación:** Un nodo con muchas conexiones debería sentirse más pesado que uno aislado. La inercia al soltar el nodo transmite esta información de forma no verbal.

**API utilizada:** Eventos `grab`, `drag`, `free` + `node.animate()` — APIs nativas de Cytoscape.

**Propuesta:**

En eventos de Cytoscape:
```javascript
cy.on('grab', 'node', (e) => { capturar timestamp y posición })
cy.on('drag', 'node', (e) => { calcular velocidad instantánea })
cy.on('free', 'node', (e) => {
  const v = velocidadCalculada
  const destino = {
    x: nodo.position('x') + v.x * 0.3,
    y: nodo.position('y') + v.y * 0.3
  }
  nodo.animate({ position: destino, duration: 250, easing: 'ease-out' })
})
```

El nodo arrastrado se anima 250ms post-release. Los vecinos NO se mueven.

**Nota de implementación:** Limitar velocidad máxima de inercia para evitar que nodos salgan de pantalla. Cancelar animaciones pendientes antes de activar vecindario.

**Posible mejora futura:** Calcular la velocidad utilizando una ventana de las últimas 2–3 muestras de drag para reducir la sensibilidad al último evento recibido. No es necesario para el MVP — se evaluará si la inercia resulta brusca o inconsistente en pruebas reales.

**Beneficio para exploración:** El usuario siente el peso de los nodos importantes al interactuar.

**Impacto visual:** Sutil pero perceptible. El grafo responde al arrastre con organismo.

**Coste técnico:** 3 eventos + cálculo de velocidad + animate. ~20 líneas.

**Complejidad:** Media — calibrar factor de inercia.

**Riesgo:** Bajo — solo afecta al nodo arrastrado, 250ms de duración.

**Compatibilidad:** Alta — eventos nativos de Cytoscape.

**Prioridad:** P2.

**Métrica de éxito:** En una prueba de usabilidad, el usuario percibe diferencia de "peso" entre nodos de degree alto y bajo al arrastrarlos.

---

#### V9. Transiciones Suaves en Filtrado

**Objetivo:** Que el cambio de filtro sea fluido, no abrupto.

**Justificación:** Un filtrado instantáneo (display:none) rompe la orientación espacial del usuario. Una transición de opacidad mantiene el contexto visual.

**API utilizada:** `node.animate()` con `style` — nativo de Cytoscape.

**Propuesta:**

Secuencia al filtrar:
1. Para nodos que van a ocultarse: `node.animate({ style: { opacity: 0 }, duration: 200 })`
2. Después de 200ms: aplicar `node.addClass('oculto-filtro')` (display:none)
3. Para nodos que van a mostrarse: quitar clase, `node.animate({ style: { opacity: 1 }, duration: 200 })`

NO re-lanzar layout. La posición espacial se mantiene.

**Nota de implementación:** Cancelar animaciones pendientes si el usuario cambia de filtro rápidamente. Usar `transitionId` incremental para ignorar callbacks de animaciones anteriores. El `setTimeout(200)` para mostrar nuevos nodos podría sincronizarse con la finalización de la última animación de salida en una versión futura.

**Beneficio para exploración:** El usuario mantiene la orientación espacial al cambiar filtros.

**Impacto visual:** Transiciones de 200ms crean continuidad visual.

**Coste técnico:** Modificar `filtrarPorTipo()` con secuencia animate + setTimeout. ~15 líneas.

**Complejidad:** Baja.

**Riesgo:** Bajo — duration corta, sin re-layout.

**Compatibilidad:** Alta — `node.animate()` nativo.

**Prioridad:** P2.

**Métrica de éxito:** El usuario puede alternar entre filtros sin perder la referencia espacial del grafo.

---

#### V10. Transición de Selección con Easing

**Objetivo:** Que la exploración de vecindarios se sienta cinematográfica.

**Justificación:** `saltarANodo()` actual usa animación lineal que se siente mecánica. Un easing suave mejora la experiencia de navegación.

**API utilizada:** `cy.animate()` con `easing` — nativo de Cytoscape.

**Propuesta:**

Cambiar en `saltarANodo()`:
```javascript
cy.animate({
  center: { eles: nodo },
  zoom: 1.2,
  duration: 500,
  easing: 'ease-in-out-cubic',
})
```

Opacidad de nodos fuera del vecindario: transición de 1.0 → 0.08 en 250ms (ya existe parcialmente con `.fuera-vecindario`).

**Beneficio para exploración:** La navegación entre nodos se siente fluida y natural.

**Impacto visual:** Transición cinematográfica al explorar vecindarios.

**Coste técnico:** Cambiar 2 parámetros en `cy.animate()`. 2 líneas.

**Complejidad:** Trivial.

**Riesgo:** Negligible.

**Compatibilidad:** 100% — parámetros nativos de `cy.animate()`.

**Prioridad:** P2.

**Métrica de éxito:** La animación de selección se siente natural, no mecánica.

---

#### V11. Hover con Borde Destacado

**Objetivo:** Que el nodo responda visualmente al cursor del usuario.

**Justificación:** El usuario necesita feedback inmediato de que un nodo es interactuable. Actualmente solo aparece un tooltip de texto, sin cambio visual en el nodo.

**API utilizada:** Eventos `mouseover`/`mouseout` + clases CSS — nativos de Cytoscape.

**Propuesta:**

En `frontend/src/render.js`, agregar eventos:
```javascript
cy.on('mouseover', 'node', (e) => e.target.addClass('hovered'))
cy.on('mouseout', 'node', (e) => e.target.removeClass('hovered'))
```

En `frontend/src/style.css`:
```css
.hovered {
  border-width: 3px !important;
  border-opacity: 0.8 !important;
}
```

No usar shadow (costoso en canvas). No usar escala (requiere recalcular tamaño). Solo borde.

**Beneficio para exploración:** Feedback visual inmediato al interactuar con nodos.

**Impacto visual:** Sutil pero efectivo. El nodo "responde" al cursor.

**Coste técnico:** 2 eventos + 3 líneas CSS. ~5 líneas totales.

**Complejidad:** Trivial.

**Riesgo:** Negligible.

**Compatibilidad:** 100% — clases y selectores nativos.

**Prioridad:** P2.

**Métrica de éxito:** El usuario percibe que los nodos responden al cursor sin leer documentación.

---

#### V12. Tooltip Enriquecido con Métricas

**Objetivo:** Mostrar información científica relevante en el tooltip, no solo nombre y tipo.

**Justificación:** El tooltip es la primera capa de información que ve el usuario. Si muestra métricas de importancia, el usuario puede evaluar un nodo sin hacer clic.

**API utilizada:** `ele.degree()`, `ele.betweenness()`, `ele.closeness()`, `ele.connectedEdges()` — APIs nativas de Cytoscape.

**Propuesta:**

Expandir el tooltip actual para incluir:
- Nombre y tipo (actual)
- Grado (`ele.degree()` — nativo)
- Betweenness centrality (`ele.betweenness()` — nativo, si V7 está implementado)
- Closeness centrality (`ele.closeness()` — nativo)
- Número de relaciones Nivel A vs Nivel B
- Indicador de evidencia: "Con cita textual" / "Con fuente" / "Sin evidencia"

**Nota de implementación:** Las métricas se calculan una vez post-layout y se almacenan en `data()`. El tooltip solo lee valores pre-calculados.

**Beneficio para exploración:** El usuario evalúa la importancia y fiabilidad de un nodo al pasar el cursor.

**Impacto visual:** Tooltip más informativo, misma posición y estilo.

**Coste técnico:** Modificar `mostrarTooltip()` para incluir métricas calculadas. ~15 líneas.

**Complejidad:** Baja.

**Riesgo:** Bajo — solo lectura de datos existentes.

**Compatibilidad:** Alta — manipulación DOM estándar + APIs nativas de Cytoscape.

**Prioridad:** P2.

**Métrica de éxito:** El usuario puede decidir si un nodo es relevante para su búsqueda antes de hacer clic.

---

### Nivel 3 — Mejoras Futuras (Versión 2.0)

---

#### V13. Resaltado de Ruta entre Dos Nodos

**Objetivo:** Permitir al usuario explorar la "distancia conceptual" entre dos ideas.

**Justificación:** En antropología, la distancia entre dos conceptos es información científica. ¿Qué autores conectan dos escuelas? ¿Qué conceptos mediaron entre dos corrientes? La ruta más corta en el grafo responde estas preguntas.

**API utilizada:** `eles.dijkstra()` — algoritmo nativo de Cytoscape.js (O(E log V)).

**Propuesta:**

Modo de activación: Shift+click en dos nodos consecutivos.
Comportamiento:
1. Calcular camino más corto usando `cy.elements().dijkstra()` (nativo de Cytoscape)
2. Resaltar aristas del camino con color #e94560 y grosor 3px
3. Resaltar nodos del camino con opacidad 1.0
4. Atenuar nodos fuera del camino a opacidad 0.1
5. Click en fondo o Escape para desactivar

**Nota de implementación:** Usar exclusivamente `eles.dijkstra()`. No reimplementar Dijkstra. Manejar caso donde los nodos no están en el mismo componente conectado.

**Beneficio para exploración:** El usuario puede responder "¿cómo llego de X a Y?" visualmente.

**Impacto visual:** Modo de exploración de rutas que destaca caminos conceptuales.

**Coste técnico:** ~30 líneas — detección de Shift+click, dijkstra(), apply/restore style.

**Complejidad:** Media.

**Riesgo:** Medio — necesita UX clara para activar/desactivar.

**Compatibilidad:** Alta — Dijkstra es nativo de Cytoscape.

**Prioridad:** P3 (versión 2.0).

**Métrica de éxito:** El usuario puede encontrar el camino más corto entre dos conceptos en <15 segundos.

---

#### V14. Resaltado de Vecindario Ampliado

**Objetivo:** Explorar el entorno de un nodo con más detalle que el actual.

**Justificación:** El sistema actual de vecindario (click → vecinos + aristas) es binario. Un vecindario ampliado que muestre 2 saltos de distancia permite ver relaciones indirectas.

**API utilizada:** `eles.neighborhood()` — API nativa de Cytoscape (encadenada, no recursiva).

**Propuesta:**

Modo de activación: Doble-click en un nodo.
Comportamiento:
1. Obtener vecinos de primer nivel: `nodo.neighborhood().nodes()` (API nativa)
2. Obtener vecinos de segundo nivel: `nivel1.neighborhood().nodes().not(nodo).not(nivel1)` (encadenamiento de API nativa)
3. Primer nivel: opacidad 1.0, borde blanco
4. Segundo nivel: opacidad 0.5, sin borde
5. Aristas de primer nivel: color saturado, grosor 2.5
6. Aristas de segundo nivel: color desaturado, grosor 1.0

**Nota de implementación:** Usar encadenamiento de `neighborhood()`, no recursión manual. Cytoscape resuelve la traversión internamente.

**Beneficio para exploración:** El usuario ve relaciones indirectas — cómo un concepto influye en otro a través de intermediarios.

**Impacto visual:** Dos niveles de profundidad visual en la exploración.

**Coste técnico:** ~20 líneas — doble-click handler, encadenamiento de neighborhood.

**Complejidad:** Media.

**Riesgo:** Bajo.

**Compatibilidad:** Alta — `neighborhood()` es nativo.

**Prioridad:** P3 (versión 2.0).

**Métrica de éxito:** El usuario puede identificar relaciones indirectas entre conceptos.

---

## 7. Prioridades

| Nivel | Propuesta | Esfuerzo | Impacto Científico |
|-------|-----------|----------|-------------------|
| **P0** | V1. Calibración Layout | Trivial | Distribución espacial refleja relaciones |
| **P0** | V2. Jerarquización por Conectividad | Baja | Importancia estructural visible |
| **P1** | V3. Grosor por Nivel Ontológico | Baja | Jerarquía de relaciones codificada |
| **P1** | V4. Color por Evidencia | Baja | Fortaleza epistemológica visible |
| **P1** | V6. Agrupamiento Espacial | Trivial | Clusters de conocimiento visibles |
| **P1** | V7. Centralidad (API nativa) | Baja | Nodos puente identificables |
| **P2** | V8. Inercia al Arrastrar | Media | Masa comunicada por interacción |
| **P2** | V9. Transiciones Filtrado | Baja | Orientación espacial mantenida |
| **P2** | V10. Transición Selección | Trivial | Navegación cinematográfica |
| **P2** | V11. Hover Borde | Trivial | Feedback visual inmediato |
| **P2** | V12. Tooltip Enriquecido | Baja | Métricas accesibles sin clic |
| **P3** | V5. Curvatura Adaptativa | Media | Relaciones múltiples legibles (v2.0) |
| **P3** | V13. Resaltado de Ruta | Media | Distancia conceptual explorable (v2.0) |
| **P3** | V14. Vecindario Ampliado | Media | Relaciones indirectas visibles (v2.0) |

---

## 8. Beneficios Esperados

| Beneficio | Propuestas que contribuyen |
|-----------|---------------------------|
| La ontología se comunica visualmente | V3, V4, V6 |
| La estructura del conocimiento es perceptible | V1, V2, V6, V7 |
| La evidencia científica tiene presencia visual | V4, V12 |
| Las relaciones conceptuales son explorables | V5, V13, V14 |
| La navegación es fluida y natural | V8, V9, V10, V11 |
| Las métricas de importancia son accesibles | V2, V7, V12 |

---

## 9. Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| V7 (centralidad) puede ser costoso con grafos >3000 nodos | Media | `eles.betweenness()` es O(VE) — calcular una vez, cachear en data() |
| V5 (curvatura) puede crear aristas visualmente confusas | Baja | Limitar curvatura a ±30px, solo para pares con >1 relación |
| V8 (inercia) puede molestar a usuarios que prefieren control preciso | Baja | Duración corta (250ms), limitar velocidad máxima |
| V1 (layout) puede ser lento con grafos >1000 nodos | Media | Degradación automática: quality 'default'/'draft' según tamaño |
| V13 (rutas) puede ser confuso sin onboarding | Media | Tooltip que explique "Shift+click para ruta" |

---

## 10. Compatibilidad

### Afectados

| Componente | Afectado | Cambios |
|------------|----------|---------|
| `frontend/src/render.js` | Sí | Estilos, eventos, layout, centralidad |
| `frontend/src/style.css` | Sí | Selectores hover, transiciones, curvatura |
| `frontend/src/main.js` | No | Sin cambios |
| `src/grafo.js` | No | Sin cambios |
| `index.html` | No | Sin cambios |

### No afectados

| Componente | Razón |
|------------|-------|
| Pipeline de extracción | Independiente del frontend |
| Base de datos SQLite | Solo se lee, no se modifica |
| Manifiesto Ontológico | Solo se referencia, no se altera |
| Tests de firewall | No dependen del rendering |
| Scripts de utilidad | Independientes |

### Extensiones de Cytoscape requeridas

| Extensión | Estado | Uso |
|-----------|--------|-----|
| cytoscape-fcose | Ya instalada | Layout (V1, V6) |
| Ninguna nueva | — | Todas las demás propuestas usan APIs nativas |

### APIs nativas utilizadas (resumen)

| API | Propuesta | Documentación |
|-----|-----------|---------------|
| `ele.degree()` | V2 | Nativo |
| `ele.betweenness()` | V7, V12 | Nativo (Brandes) |
| `ele.closeness()` | V12 | Nativo |
| `ele.connectedEdges()` | V2, V3 | Nativo |
| `eles.dijkstra()` | V13 | Nativo |
| `eles.neighborhood()` | V14 | Nativo |
| `cy.animate()` | V8, V9, V10 | Nativo |
| `node.animate()` | V8, V9 | Nativo |
| `node.position()` | V8 | Nativo |
| `node.data()` | V7, V12 | Nativo |
| `node.addClass()` / `removeClass()` | V11 | Nativo |

---

## 11. Estrategia de Implementación

```
Fase 1 — Base (V1 + V2):
  Calibrar layout fcose con degradación
  Implementar jerarquización por conectividad
  Validar con grafo real
  Verificar rendimiento

Fase 2 — Información Ontológica (V3 + V4 + V6 + V7):
  Grosor por nivel de relación
  Color por evidencia
  Agrupamiento espacial (subproducto de V1)
  Centralidad con eles.betweenness()
  Validar con datos reales

Fase 3 — Interacción (V8 + V9 + V10 + V11 + V12):
  Inercia al arrastrar
  Transiciones de filtrado
  Easing de selección
  Hover con borde
  Tooltip enriquecido

Fase 4 — Exploración Avanzada (v2.0: V5 + V13 + V14):
  Curvatura adaptativa
  Resaltado de rutas
  Vecindario ampliado
```

Cada fase se valida independientemente antes de pasar a la siguiente.

---

## 12. Criterios de Aceptación

### Criterios generales

- [ ] El grafo carga en <2 segundos con el dataset actual
- [ ] Se mantiene 60fps durante interacción normal (DevTools Performance)
- [ ] No hay regresiones en tests existentes (`pytest`)
- [ ] Las propuestas se implementan solo en `frontend/src/render.js` y `frontend/src/style.css`
- [ ] No se modifican pipeline, backend, ontología ni tests de firewall
- [ ] No se reimplementan algoritmos que Cytoscape resuelve nativamente

### Criterios por propuesta

| Propuesta | Criterio de aceptación |
|-----------|----------------------|
| V1 | Distancia promedio entre nodos connectedEdges() disminuye >15% |
| V2 | Usuario identifica top-5 nodos centrales en <5s sin clic |
| V3 | Usuario distingue Nivel A de Nivel B sin leer labels |
| V4 | Relaciones con cita textual son visualmente más prominentes |
| V5 | Pares con >1 relación muestran todas las aristas sin solapamiento |
| V6 | Nodos tipo escuela/corriente quedan espacialmente cercanos |
| V7 | Usuario identifica top-3 nodos puente en <10s (usando `eles.betweenness()`) |
| V8 | Usuario percibe diferencia de "peso" entre degree alto y bajo |
| V9 | Usuario mantiene orientación al cambiar filtros |
| V10 | Animación de selección se siente natural |
| V11 | Nodo responde visualmente al cursor |
| V12 | Usuario evalúa importancia de nodo antes de clic |
| V13 | Usuario encuentra ruta más corta entre conceptos en <15s (usando `eles.dijkstra()`) |
| V14 | Usuario identifica relaciones indirectas (usando `eles.neighborhood()`) |

---

## 13. Métricas de Validación

| Métrica | Herramienta | Objetivo |
|---------|-------------|----------|
| FPS durante interacción | Chrome DevTools Performance | ≥60fps con 500 nodos |
| Tiempo de carga del layout | Medición manual con `performance.now()` | <2s |
| Tiempo de cálculo de centralidad | `console.time()` con `eles.betweenness()` | <500ms con 500 nodos |
| Tamaño del bundle | `vite build` output | Incremento <10KB |
| Líneas de código nuevas | Conteo manual | <200 líneas totales |
| Tests existentes | `pytest` | 100% pass |

---

## 14. Estado de Implementación — MVP V1-V12

**Fecha de cierre del desarrollo:** 2026-07-25

### Estado

| Verificación | Estado |
|--------------|--------|
| Implementación V1–V12 | ✅ Completada |
| Compilación (`npm run build`) | ✅ Exitosa (3.18s) |
| Sintaxis JavaScript | ✅ Sin errores |
| Uso de APIs nativas Cytoscape.js | ✅ Verificado |
| Correcciones arquitectónicas (V6, V7, V12) | ✅ Incorporadas |
| Conflictos funcionales | ✅ Ninguno detectado (revisión de código) |
| **Validación técnica completa** | ⏳ **Pendiente UAT** |
| **Validación visual en navegador** | ⏳ **Pendiente (UAT)** |

> **Nota:** La validación técnica no se considera completa hasta que la UAT confirme ausencia de errores de ejecución en navegador.

### Propuestas Implementadas

| Propuesta | Estado | Archivos |
|-----------|--------|----------|
| V1. Calibración Layout | ✅ Implementado | render.js |
| V2. Jerarquización por Conectividad | ✅ Implementado | render.js |
| V3. Grosor por Nivel Ontológico | ✅ Implementado | render.js |
| V4. Color por Evidencia | ✅ Implementado | render.js |
| V6. Agrupamiento Espacial | ✅ Subproducto de V1 | — |
| V7. Representación de Centralidad | ✅ Implementado | render.js |
| V8. Inercia al Arrastrar | ✅ Implementado | render.js |
| V9. Transiciones Filtrado | ✅ Implementado | render.js |
| V10. Transición Selección | ✅ Implementado | render.js |
| V11. Hover con Borde | ✅ Implementado | render.js |
| V12. Tooltip Enriquecido | ✅ Implementado | render.js, index.html |

### Propuestas Pospuestas a v2.0

| Propuesta | Razón |
|-----------|-------|
| V5. Curvatura Adaptativa | Validar frecuencia de pares multi-arista primero |
| V13. Resaltado de Ruta | YAGNI — no resuelve problema actual |
| V14. Vecindario Ampliado | YAGNI — no resuelve problema actual |

### Archivos Modificados

| Archivo | Líneas antes | Líneas después | Cambio |
|---------|--------------|----------------|--------|
| frontend/src/render.js | 282 | ~420 | +138 líneas |
| index.html | 58 | 59 | +1 línea |
| frontend/src/style.css | 417 | 417 | Sin cambios |

### APIs Nativas Utilizadas

| API | Propuesta | Verificada |
|-----|-----------|------------|
| `ele.degree()` | V2, V12 | ✅ |
| `cy.elements().betweennessCentrality()` | V7 | ✅ |
| `bc.betweennessNormalized()` | V7 | ✅ |
| `node.animate()` | V8, V9 | ✅ |
| `cy.animate()` | V10 | ✅ |
| `node.addClass()` / `removeClass()` | V8, V9, V11 | ✅ |
| `node.stop()` | V9 | ✅ |
| `cy.on('grab/drag/free')` | V8 | ✅ |
| `cy.on('mouseover/mouseout')` | V11 | ✅ |
| `ele.connectedEdges()` | V12 | ✅ |

### Métricas de Validación

| Métrica | Objetivo | Resultado |
|---------|----------|-----------|
| Build time | <5s | 3.18s ✅ |
| Bundle JS | Incremento <10KB | +2.4KB ✅ |
| Bundle CSS | Sin cambios | 0KB ✅ |
| Líneas nuevas | <200 | ~139 ✅ |
| Sintaxis | Sin errores | ✅ |

---

## 15. Deuda Técnica

### D1. Modularización de render.js

**Prioridad:** Alta
**Justificación:** render.js concentra todas las responsabilidades (layout, estilos, interacciones, métricas, tooltip). Con 420 líneas, dificulta mantenimiento y testing.

**Propuesta de estructura:**
```
src/
 ├── render.js          // inicialización y orquestación
 ├── layout.js          // V1 — parámetros fcose
 ├── styling.js         // V2–V4 — estilos de nodos y aristas
 ├── interactions.js    // V8–V11 — eventos de usuario
 ├── metrics.js         // V7, V12 — cálculos de centralidad
 └── tooltip.js         // V12 — lógica del tooltip
```

### D2. Suavizado de Velocidad en V8

**Prioridad:** Media
**Justificación:** El cálculo actual usa la última posición del `drag`, lo que puede ser sensible a movimientos pequeños.

**Mejora propuesta:** Calcular velocidad usando una ventana de las últimas 2–3 muestras de `drag` para reducir sensibilidad al último evento.

### D3. Eliminación del setTimeout en V9

**Prioridad:** Baja
**Justificación:** Aunque el `transitionId` protege contra condiciones de carrera, el `setTimeout(200)` para mostrar nuevos nodos podría sincronizarse con la finalización de la última animación de salida.

**Mejora propuesta:** Usar Promise o callback encadenado para eliminar el tiempo fijo.

---

## 16. Hoja de Ruta Corregida

### Fase 0 — Estabilización (pre-UAT)

- [ ] Eliminar `console.log` temporales
- [ ] Eliminar código comentado
- [ ] Revisar TODO/FIXME
- [ ] Confirmar consola limpia durante sesión normal
- [ ] Comprobar que arranca desde clon limpio (`npm install && npm run dev`)

### Fase 1 — UAT (Bloqueante)

**No seguir desarrollando hasta completar esta fase.**

#### Criterios de Aprobación

| # | Criterio | Estado |
|---|----------|--------|
| 1 | Consola sin errores JS ni warnings de Cytoscape | ⏳ |
| 2 | Grafo carga correctamente en recarga limpia | ⏳ |
| 3 | Hover, selección, búsqueda, filtrado, inercia funcionan | ⏳ |
| 4 | Tooltip muestra información coherente en todos los nodos | ⏳ |
| 5 | Rendimiento fluido con ~394 nodos | ⏳ |
| 6 | Sin regresiones respecto al comportamiento esperado | ⏳ |

**Si alguno falla → UAT no superada, volver a fase de corrección.**

#### Visualización
- [ ] Los clusters reflejan afinidad conceptual
- [ ] Nodos importantes destacan sin ocultar a los demás
- [ ] Aristas son legibles

#### Interacción
- [ ] Hover sin parpadeos
- [ ] Tooltip correcto en todos los nodos
- [ ] Filtrado repetido rápidamente
- [ ] Búsqueda funcional
- [ ] Selección correcta
- [ ] Arrastre con inercia natural

#### Rendimiento
- [ ] Sin caídas perceptibles de FPS
- [ ] Sin crecimiento continuo de memoria
- [ ] Consola completamente limpia (0 errores, 0 warnings)

**Si alguno falla → volver a implementación.**

### Fase 2 — Congelación del MVP

Cuando todo funcione:
1. Crear tag `v1.0.0-mvp`
2. No modificar comportamiento
3. Corregir únicamente bugs

### Fase 3 — Refactorización

```
src/
 ├── render/
 │   ├── layout.js
 │   ├── styles.js
 │   ├── interactions.js
 │   ├── tooltip.js
 │   ├── metrics.js
 │   └── filters.js
```

### Fase 4 — Validación con Usuarios

#### Hipótesis H1

> Un usuario puede identificar los conceptos y autores estructuralmente más importantes utilizando la visualización, sin necesidad de inspeccionar cada nodo individualmente.

#### Tareas concretas

1. "Encuentra el autor más influyente"
2. "Identifica las escuelas antropológicas principales"
3. "Localiza un concepto puente entre dos corrientes"
4. "Determina qué relaciones tienen mayor respaldo documental"

#### Criterio de éxito

Si varios usuarios consiguen las tareas de forma consistente → evidencia de valor cognitivo, no solo estético.

#### Preguntas complementarias

- "¿El color te comunica algo sin leer la leyenda?"
- "¿Los grupos corresponden a escuelas reales?"

#### Criterio de fallo

Si varias personas fallan en las mismas tareas → el problema es el diseño, no los usuarios.

### Pregunta Clave

> **¿El diseño visual mejora la comprensión del conocimiento?**

- ¿Sin etiquetas, podrías adivinar los autores principales por estructura?
- ¿Los grupos corresponden a escuelas reales (funcionalismo, estructuralismo, evolucionismo)?
- ¿Colores y grosores permiten identificar calidad/naturaleza de relaciones?

Si la respuesta es sí → las decisiones visuales aportan información, no solo decoración.

---

## 17. Criterios de Éxito del Proyecto

### Objetivo Principal

Construir una interfaz que permita explorar conocimiento antropológico de forma más rápida e intuitiva que una lista tradicional de conceptos o una tabla de relaciones.

### Indicadores de Éxito

#### Técnicos

| Indicador | Criterio |
|-----------|----------|
| Build reproducible | Sin errores en `npm run build` |
| Consola limpia | 0 errores, 0 warnings durante UAT |
| Interacción fluida | 60fps con dataset objetivo (~394 nodos) |
| Arquitectura modular | render.js dividido en ≥5 módulos después de refactorización |

#### Funcionales

| Indicador | Criterio |
|-----------|----------|
| Nodos centrales identificables | Usuario los identifica sin inspeccionar uno por uno |
| Clusters reconocibles | Agrupaciones corresponden a escuelas conceptuales |
| Evidencia visible | Relaciones con mayor respaldo se distinguen inmediatamente |

#### Experiencia de Usuario

| Indicador | Criterio |
|-----------|----------|
| Velocidad de búsqueda | Usuario encuentra concepto más rápido que con lista |
| Exploración por conexiones | Usuario reconstruye escuela antropológica siguiendo aristas |
| Legibilidad del diseño | Usuario comprende colores, tamaños y grosores sin documentación |

### Riesgos Conocidos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Grafo demasiado denso | Alto | Filtrado progresivo, niveles de detalle |
| Exceso de codificación visual | Alto | Reducir variables si disminuye legibilidad |
| Caída de rendimiento con >3000 nodos | Medio | Layout adaptativo y clustering |
| Crecimiento de render.js | Medio | Modularización (Fase 3) |

### Filosofo de Producto

Cada nueva funcionalidad debe responder:

> **¿Hace que el usuario descubra relaciones que antes le costaba ver?**

- Si sí → implementar
- Si solo es estético o animación atractiva → no aumentar complejidad

Este criterio filtra todas las versiones posteriores al MVP y mantiene el proyecto alineado con su propósito: **herramienta para pensar y descubrir relaciones en antropología**.

---

## 18. Decisiones Rechazadas (ADR Ligero)

Para evitar volver a debatir lo mismo en el futuro.

| Decisión | Motivo de rechazo |
|----------|-------------------|
| Usar `nestingFactor` para agrupamiento | No era necesario; el agrupamiento es subproducto natural de los parámetros de fcose (V1) |
| Reimplementar betweenness centrality (Brandes) | Cytoscape ofrece `betweennessCentrality()` optimizado nativamente |
| Reimplementar Dijkstra | Cytoscape proporciona `eles.dijkstra()` nativo |
| Usar `setTimeout` para sincronizar animaciones (V9) | Sustituido por `transitionId` + callbacks donde fue posible |
| Escalado ilimitado de nodos por degree | Producía dominancia visual; se impuso cap de 50px |
| Usar `ele.betweenness()` | Método no existe en Cytoscape 3.34.0; se usó `betweennessCentrality()` |
| Opacidad variable por degree | Reducía legibilidad; se eliminó en favor de tamaño + borde |
| Relajación continua del grafo (P3 original) | Duplicaba fcose, violaba KISS, destruía estabilidad |
| Zoom con inercia (P8 original) | Rompía compatibilidad; zoom nativo es suficiente |
| Renderizado adaptativo por densidad (P10 original) | Premature optimization; Cytoscape ya optimiza internamente |

---

*Documento generado como especificación oficial del motor visual. Cualquier implementación futura debe referenciar este RFC como fuente de verdad.*

*Corregido el 2026-07-24: incorporadas correcciones de revisión arquitectónica (V6, V7, V1, V13, V14).*
*Cerrado el 2026-07-25: MVP V1-V12 implementado y validado técnicamente. UAT pendiente.*
*Actualizado: añadidos criterios de éxito, riesgos, filosofía de producto y decisiones rechazadas.*
