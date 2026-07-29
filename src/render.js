import cytoscape from 'cytoscape'
import fcose from 'cytoscape-fcose'

cytoscape.use(fcose)

const LIBROS = {
  'argonautas.pdf': 'Los argonautas del Pacífico Occidental',
  'boas-f-1911-cuestiones-fundamentales-de-antropologia-cultural.pdf': 'Cuestiones fundamentales de antropología cultural',
}

function limpiarFuente(fuente) {
  if (!fuente) return { libro: null, texto: fuente }
  for (const [pdf, libro] of Object.entries(LIBROS)) {
    if (fuente.includes(pdf)) {
      return { libro, texto: fuente.replace(pdf, libro) }
    }
  }
  return { libro: null, texto: fuente }
}

let cy = null
let nodoActual = null
let focusedNode = null
let focusAnim = null
let focusedOriginalSize = null


// V3 — Grosor de Aristas por Nivel Ontológico
const NIVEL_A = new Set([
  'autor_de', 'influenciado_por', 'critica_a', 'desarrolla_concepto',
  'redefine_a', 'precursor_de', 'pertenece_a', 'estudia_a',
  'contemporaneo_de', 'parte_del_debate', 'es_mentor_de', 'colabora_con'
])

const NIVEL_B = new Set([
  'contradice', 'relacionado_con', 'depende_de'
])
const COLOR_POR_TIPO = {
  autor: '#D85A30',
  obra: '#1D9E75',
  concepto: '#7F77DD',
  escuela: '#BA7517',
  cultura: '#639922',
  debate: '#D4537E',
  poblacion: '#3A9BDC',
  corriente: '#C9A227',
}

const SHAPE_POR_TIPO = {
  autor: 'round-triangle',
  obra: 'round-rectangle',
  concepto: 'diamond',
  escuela: 'hexagon',
  cultura: 'pentagon',
  debate: 'round-diamond',
  poblacion: 'barrel',
  corriente: 'star',
}

const COLOR_POR_RELACION = {
  autor_de: '#e74c3c',
  influenciado_por: '#3498db',
  critica_a: '#e67e22',
  desarrolla_concepto: '#2ecc71',
  redefine_a: '#9b59b6',
  precursor_de: '#1abc9c',
  pertenece_a: '#f1c40f',
  estudia_a: '#2980b9',
  contemporaneo_de: '#d35400',
  parte_del_debate: '#8e44ad',
  es_mentor_de: '#16a085',
  colabora_con: '#27ae60',
  contradice: '#c0392b',
  relacionado_con: '#7f8c8d',
  depende_de: '#95a5a6',
}

export function inicializarVisualizacion(nodos, relaciones) {
  const elementos = [
    ...nodos.map((n) => ({
      data: { id: n.id, label: n.nombre, tipo: n.tipo, resumen: n.descripcion || n.resumen, metadata: n.metadatos || n.metadata },
    })),
    ...relaciones.map((r) => ({
      data: {
        id: `rel-${r.id}`,
        source: r.origen_id || r.origen,
        target: r.destino_id || r.destino,
        label: r.tipo,
        nota: r.nota || r.fuente,
        cita: r.cita_textual || '',
      },
    })),
  ]

  initTheme()

  cy = cytoscape({
    container: document.getElementById('grafo'),
    elements: elementos,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': (ele) => COLOR_POR_TIPO[ele.data('tipo')] || '#888',
          shape: (ele) => SHAPE_POR_TIPO[ele.data('tipo')] || 'ellipse',
          label: 'data(label)',
          color: '#fff',
          'font-size': 11,
          'font-weight': 600,
          'text-valign': 'bottom',
          'text-margin-y': 6,
          'text-background-color': '#1a1a2e',
          'text-background-opacity': 0.7,
          'text-background-padding': 3,
          'text-background-shape': 'round-rectangle',
          width: (ele) => 14 + Math.min(ele.degree() * 2.5, 36),
          height: (ele) => 14 + Math.min(ele.degree() * 2.5, 36),
          'border-width': (ele) => { const c = Number(ele.data('centralidad')) || 0; return 1 + c * 8; },
          'border-color': (ele) => COLOR_POR_TIPO[ele.data('tipo')] || '#888',
          'shadow-blur': 12,
          'shadow-color': (ele) => COLOR_POR_TIPO[ele.data('tipo')] || '#888',
          'shadow-offset-x': 0,
          'shadow-offset-y': 0,
          'shadow-opacity': 0.5,
        },
      },
      {
        selector: 'edge',
        style: {
          width: 1.5,
          'line-color': (ele) => COLOR_POR_RELACION[ele.data('label')] || '#555',
          'target-arrow-color': (ele) => COLOR_POR_RELACION[ele.data('label')] || '#555',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'edge-distances': 'node-position',
          label: 'data(label)',
          'font-size': 9,
          color: '#999',
          'text-rotation': 'autorotate',
          'text-opacity': 0,
          'line-style': (ele) => {
            const ev = ele.data('evidencia')
            if (ev === 'cita') return 'solid'
            if (ev === 'fuente') return 'dashed'
            return 'dotted'
          },
        },
      },
      {
        selector: 'edge[tipoedge = "Nivel_A"]',
        style: { width: 2.0 },
      },
      {
        selector: 'edge[tipoedge = "Nivel_B"]',
        style: { width: 1.0 },
      },
      {
        selector: 'edge[evidencia = "cita"]',
        style: { opacity: 0.9 },
      },
      {
        selector: 'edge[evidencia = "fuente"]',
        style: { opacity: 0.7 },
      },
      {
        selector: 'edge[evidencia = "ninguna"]',
        style: { opacity: 0.4 },
      },
      {
        selector: 'edge:active, edge.resaltada',
        style: { 'text-opacity': 1, 'line-color': '#fff', 'target-arrow-color': '#fff', color: '#fff', 'z-index': 10 },
      },
      {
        selector: 'node[[degree = 0]]',
        style: {
          'border-width': 2,
          'border-style': 'dashed',
          'border-color': '#ff5555',
          opacity: 0.5,
        },
      },
      {
        selector: '.oculto-filtro',
        style: { display: 'none' },
      },
      {
        selector: '.leyenda-oculto',
        style: { opacity: 0.12 },
      },
      {
        selector: 'node.seleccionado',
        style: {
          'border-width': 5,
          'border-color': '#00e5ff',
          'border-opacity': 1,
          'shadow-blur': 30,
          'shadow-color': '#00e5ff',
          'shadow-opacity': 0.8,
          'z-index': 12,
        },
      },
      {
        selector: '.tipo-destacado',
        style: {
          'shadow-blur': 20,
          'shadow-color': (ele) => COLOR_POR_TIPO[ele.data('tipo')] || '#888',
          'shadow-opacity': 0.6,
          'border-width': 3,
          'border-color': (ele) => COLOR_POR_TIPO[ele.data('tipo')] || '#888',
          'border-opacity': 0.7,
          'z-index': 9,
        },
      },
      {
        selector: 'node.hovered',
        style: {
          'border-width': 4,
          'border-opacity': 1,
          'border-color': (ele) => COLOR_POR_TIPO[ele.data('tipo')] || '#e94560',
          'shadow-blur': 24,
          'shadow-color': (ele) => COLOR_POR_TIPO[ele.data('tipo')] || '#e94560',
          'shadow-opacity': 0.8,
          'transition-property': 'border-width, border-opacity, shadow-blur, shadow-opacity',
          'transition-duration': '0.12s',
          'z-index': 10,
        },
      },
    ],
  })

  cy.layout({
    name: 'fcose',
    randomize: true,
    animate: true,
    animationDuration: 500,
    quality: nodos.length > 3000 ? 'draft' : nodos.length > 1000 ? 'default' : 'proof',
    nodeRepulsion: 18000,
    idealEdgeLength: 160,
    edgeElasticity: 0.15,
    gravity: 0.35,
    gravityRange: 2.5,
    numIter: nodos.length > 3000 ? 1000 : nodos.length > 1000 ? 1500 : 2000,
    tile: true,
    packComponents: true,
    componentSpacing: 150,
    nodeDimensionsIncludeLabels: true,
    padding: 30,
  }).run()

  // Apply initial theme colors to cy elements
  const temaInicial = localStorage.getItem(TEMA_KEY) || 'oscuro'
  if (temaInicial === 'claro') {
    cy.nodes().style('color', '#222')
    cy.edges().style('color', '#555')
    cy.style()
      .selector('edge:active, edge.resaltada')
      .style('line-color', '#333')
      .style('target-arrow-color', '#333')
      .style('color', '#222')
      .update()
  }

  // V7 — Representación de Centralidad
  const bc = cy.elements().betweennessCentrality()
  cy.nodes().forEach(nodo => {
    nodo.data('centralidad', bc.betweennessNormalized(nodo))
  })

  cy.on('tap', 'node', (evt) => {
    activarVecindario(evt.target)
    mostrarPanel(evt.target.data())
    bounceNode(evt.target)
  })

  cy.on('tap', (evt) => {
    if (evt.target === cy) {
      desactivarVecindario()
      ocultarPanel()
    }
  })

  cy.on('mouseover', 'node', (evt) => {
    evt.target.addClass('hovered')
    mostrarTooltip(evt.originalEvent, evt.target.data())
  })
  cy.on('mouseout', 'node', (evt) => {
    evt.target.removeClass('hovered')
    ocultarTooltip()
  })
  cy.on('mouseover', 'edge', (evt) => evt.target.addClass('resaltada'))
  cy.on('mouseout', 'edge', (evt) => evt.target.removeClass('resaltada'))
  cy.on('mousemove', (evt) => moverTooltip(evt.originalEvent))

  document.getElementById('cerrar-panel').addEventListener('click', () => {
    desactivarVecindario()
    ocultarPanel()
  })

  document.getElementById('zoom-in').addEventListener('click', () => {
    cy.zoom({ level: cy.zoom() * 1.4 })
  })
  document.getElementById('zoom-out').addEventListener('click', () => {
    cy.zoom({ level: cy.zoom() / 1.4 })
  })
  document.getElementById('zoom-fit').addEventListener('click', () => {
    cy.fit(50)
  })

  document.querySelectorAll('#leyenda [data-tipo]').forEach(el => {
    el.addEventListener('click', () => {
      const tipo = el.dataset.tipo
      document.querySelector(`#filtros button[data-tipo="${tipo}"]`)?.click()
    })
    el.addEventListener('mouseenter', () => {
      const tipo = el.dataset.tipo
      cy.nodes(`[tipo != "${tipo}"]`).addClass('leyenda-oculto')
      cy.nodes(`[tipo = "${tipo}"]`).addClass('tipo-destacado')
    })
    el.addEventListener('mouseleave', () => {
      cy.nodes().removeClass('leyenda-oculto tipo-destacado')
    })
  })

  cy.on('zoom', () => {
    const zoomActual = cy.zoom()
    cy.style()
      .selector('node')
      .style('label', zoomActual > 0.6 ? 'data(label)' : '')
      .update()
  })

  // V8 — Inercia al Arrastrar
  let grabPos = null
  let grabTime = null
  let inertiaAnim = null

  cy.on('grab', 'node', (e) => {
    if (inertiaAnim) {
      inertiaAnim.stop()
      inertiaAnim = null
    }
    grabPos = e.target.position()
    grabTime = Date.now()
  })

  cy.on('drag', 'node', (e) => {
    grabPos = e.target.position()
    grabTime = Date.now()
  })

  cy.on('free', 'node', (e) => {
    if (!grabPos || !grabTime) return
    const now = Date.now()
    const dt = now - grabTime
    if (dt > 100 || dt === 0) return
    const pos = e.target.position()
    const vx = (pos.x - grabPos.x) / dt * 16
    const vy = (pos.y - grabPos.y) / dt * 16
    const speed = Math.sqrt(vx * vx + vy * vy)
    const maxDist = 100
    const dist = Math.min(speed * 0.3, maxDist)
    const angle = Math.atan2(vy, vx)
    const destino = {
      x: pos.x + Math.cos(angle) * dist,
      y: pos.y + Math.sin(angle) * dist
    }
    e.target.animate({
      position: destino,
      duration: 250,
      easing: 'ease-out'
    })
    setTimeout(() => { inertiaAnim = null }, 260)
  })
}

function activarVecindario(nodo) {
  nodoActual = nodo
  const vecinos = nodo.neighborhood().nodes()
  const aristasConectadas = nodo.connectedEdges()

  cy.nodes().removeClass('seleccionado vecino fuera-vecindario')
  cy.edges().removeClass('arista-conectada arista-fuera')

  nodo.addClass('seleccionado')
  vecinos.addClass('vecino')
  cy.nodes().not(nodo).not(vecinos).addClass('fuera-vecindario')

  aristasConectadas.addClass('arista-conectada')
  cy.edges().not(aristasConectadas).addClass('arista-fuera')
}

function desactivarVecindario() {
  nodoActual = null
  cy.nodes().removeClass('seleccionado vecino fuera-vecindario')
  cy.edges().removeClass('arista-conectada arista-fuera')
}

function mostrarPanel(nodo) {
  const nodoElem = cy.getElementById(nodo.id)
  const grado = nodoElem.degree()
  const color = COLOR_POR_TIPO[nodo.tipo] || '#888'

  const badge = document.getElementById('panel-badge')
  badge.style.background = color
  document.getElementById('panel-titulo').textContent = ''
  document.getElementById('panel-titulo').append(badge, nodo.label)
  document.getElementById('panel-tipo').textContent = `${nodo.tipo} · Grado: ${grado}`
  document.getElementById('panel-desc').textContent = nodo.resumen || ''

  const ul = document.getElementById('panel-relaciones')
  ul.innerHTML = ''
  const conectadas = cy.getElementById(nodo.id).connectedEdges()
  conectadas.forEach((edge) => {
    const otroId = edge.data('source') === nodo.id ? edge.data('target') : edge.data('source')
    const otro = cy.getElementById(otroId).data('label')
    const cita = edge.data('cita')
    const fuente = edge.data('nota')
    const { libro, texto: fuenteLimpia } = limpiarFuente(fuente)

    const li = document.createElement('li')
    li.classList.add('relacion-link')
    li.textContent = `${edge.data('label')} → ${otro}`
    li.addEventListener('click', () => {
      saltarANodo(otroId)
      mostrarDetalleRelacion(edge.data('label'), otro, cita, fuenteLimpia, libro)
    })
    ul.appendChild(li)
  })

  ocultarCita()
  const panel = document.getElementById('panel')
  panel.classList.remove('oculto')
  panel.offsetHeight
  panel.classList.add('panel-visible')
}

function focusNode(nodo) {
  if (focusAnim) {
    focusAnim.stop()
    if (focusedNode && focusedOriginalSize) {
      focusedNode.style({ width: focusedOriginalSize.w, height: focusedOriginalSize.h })
    }
    focusAnim = null
  }
  focusedNode = nodo
  focusedOriginalSize = { w: nodo.width(), h: nodo.height() }
  const w = focusedOriginalSize.w
  const h = focusedOriginalSize.h
  focusAnim = nodo.animate({
    style: { width: w * 1.15, height: h * 1.15 },
    duration: 400,
    easing: 'ease-in-out',
  })
  setTimeout(() => {
    if (!focusAnim) return
    focusAnim = nodo.animate({
      style: { width: w, height: h },
      duration: 400,
      easing: 'ease-in-out',
      complete: () => {
        focusAnim = null
        focusedNode = null
        focusedOriginalSize = null
      }
    })
  }, 400)
}

function bounceNode(nodo) {
  const w = nodo.width()
  const h = nodo.height()
  nodo.animate({
    style: { width: w * 1.25, height: h * 1.25 },
    duration: 120,
    easing: 'ease-out',
    complete: () => {
      nodo.animate({
        style: { width: w, height: h },
        duration: 120,
        easing: 'ease-in',
      })
    },
  })
}

function saltarANodo(id) {
  const nodo = cy.getElementById(id)
  cy.animate({
    center: { eles: nodo },
    zoom: 1.2,
    duration: 500,
    easing: 'ease-in-out-cubic',
  })
  activarVecindario(nodo)
  mostrarPanel(nodo.data())
  bounceNode(nodo)
}

function ocultarPanel() {
  const panel = document.getElementById('panel')
  panel.classList.remove('panel-visible')
  panel.classList.add('oculto')
  ocultarCita()
}

function mostrarDetalleRelacion(tipo, destino, cita, fuente, libro) {
  const div = document.getElementById('panel-cita')
  div.innerHTML = ''
  if (libro) {
    const p = document.createElement('p')
    p.style.cssText = 'font-size:0.8rem;color:#e94560;margin-bottom:4px;font-weight:500'
    p.textContent = libro
    div.appendChild(p)
  }
  if (fuente && fuente !== libro) {
    const p = document.createElement('p')
    p.style.cssText = 'font-size:0.7rem;color:#999;margin-bottom:4px'
    p.textContent = fuente
    div.appendChild(p)
  }
  if (cita) {
    const strong = document.createElement('strong')
    strong.textContent = 'Cita: '
    const em = document.createElement('em')
    em.textContent = `"${cita}"`
    div.appendChild(strong)
    div.appendChild(em)
  }
  div.classList.remove('oculto')
}

function ocultarCita() {
  const div = document.getElementById('panel-cita')
  if (div) div.classList.add('oculto')
}

function mostrarTooltip(event, nodo) {
  const tooltip = document.getElementById('tooltip')
  tooltip.style.borderColor = COLOR_POR_TIPO[nodo.tipo] || '#0f3460'
  const nodoElem = cy.getElementById(nodo.id)
  const degree = nodoElem.degree()
  const centralidad = Number(nodoElem.data('centralidad')) || 0
  const edges = nodoElem.connectedEdges()
  let nivelA = 0, nivelB = 0
  edges.forEach(e => {
    if (e.data('tipoedge') === 'Nivel_A') nivelA++
    else if (e.data('tipoedge') === 'Nivel_B') nivelB++
  })
  let evCita = 0, evFuente = 0, evNinguna = 0
  edges.forEach(e => {
    const ev = e.data('evidencia')
    if (ev === 'cita') evCita++
    else if (ev === 'fuente') evFuente++
    else evNinguna++
  })
  const evLabel = evCita > 0 ? evCita + ' con cita' : evFuente > 0 ? evFuente + ' con fuente' : 'Sin evidencia'

  document.getElementById('tooltip-tipo').textContent = nodo.tipo
  document.getElementById('tooltip-nombre').textContent = nodo.label
  document.getElementById('tooltip-desc').textContent = nodo.resumen || ''
  document.getElementById('tooltip-metricas').innerHTML =
    'Grado: ' + degree + ' | Centralidad: ' + centralidad.toFixed(2) +
    '<br>Relaciones: ' + nivelA + ' A / ' + nivelB + ' B' +
    '<br>Evidencia: ' + evLabel

  tooltip.classList.remove('oculto')
  tooltip.style.left = (event.clientX + 15) + 'px'
  tooltip.style.top = (event.clientY + 15) + 'px'
}

function ocultarTooltip() {
  document.getElementById('tooltip').classList.add('oculto')
}

function moverTooltip(event) {
  const tooltip = document.getElementById('tooltip')
  if (!tooltip.classList.contains('oculto')) {
    tooltip.style.left = (event.clientX + 15) + 'px'
    tooltip.style.top = (event.clientY + 15) + 'px'
  }
}

// Theme toggle
const TEMA_KEY = 'cerebro-tema'
function initTheme() {
  const tema = localStorage.getItem(TEMA_KEY) || 'oscuro'
  document.body.classList.toggle('tema-claro', tema === 'claro')
  document.getElementById('tema-toggle').textContent = tema === 'claro' ? '☀️' : '🌙'
}

document.getElementById('tema-toggle')?.addEventListener('click', () => {
  const esClaro = document.body.classList.toggle('tema-claro')
  const tema = esClaro ? 'claro' : 'oscuro'
  document.getElementById('tema-toggle').textContent = esClaro ? '☀️' : '🌙'
  localStorage.setItem(TEMA_KEY, tema)
  if (cy) {
    cy.nodes().style('color', esClaro ? '#222' : '#fff')
    cy.edges().style('color', esClaro ? '#555' : '#999')
    cy.style()
      .selector('edge:active, edge.resaltada')
      .style('line-color', esClaro ? '#333' : '#fff')
      .style('target-arrow-color', esClaro ? '#333' : '#fff')
      .style('color', esClaro ? '#222' : '#fff')
      .update()
  }
})

let transitionId = 0
let totalNodeCount = 0
let totalEdgeCount = 0

export function setTotalCounts(nodos, edges) {
  totalNodeCount = nodos
  totalEdgeCount = edges
}

function actualizarStats() {
  if (!cy) return
  const visibles = cy.nodes(':visible').length
  const stats = document.getElementById('stats')
  const base = `${totalNodeCount} nodos · ${totalEdgeCount} conexiones`
  if (visibles < totalNodeCount) {
    stats.textContent = `${visibles} / ${base}`
  } else {
    stats.textContent = base
  }
}

export function filtrarPorTipo(tipo) {
  if (!cy) return
  const currentTransition = ++transitionId
  cy.nodes().stop(true)

  if (tipo === 'todos') {
    const ocultos = cy.nodes().filter('.oculto-filtro')
    if (ocultos.length === 0) return
    ocultos.removeClass('oculto-filtro')
    ocultos.forEach((n) => {
      n.animate({ style: { opacity: 1 }, duration: 200 })
    })
    actualizarStats()
    return
  }

  const aOcultar = cy.nodes().filter((n) => !n.hasClass('oculto-filtro') && n.data('tipo') !== tipo)
  const aMostrar = cy.nodes().filter((n) => n.hasClass('oculto-filtro') && n.data('tipo') === tipo)

  if (aOcultar.length === 0 && aMostrar.length === 0) return

  aOcultar.forEach((n) => {
    n.animate({ style: { opacity: 0 }, duration: 200, complete: () => {
      if (transitionId !== currentTransition) return
      n.addClass('oculto-filtro')
    }})
  })

  if (aMostrar.length > 0) {
    const waitMs = aOcultar.length > 0 ? 200 : 0
    setTimeout(() => {
      if (transitionId !== currentTransition) return
      aMostrar.forEach((n) => {
        n.removeClass('oculto-filtro')
        n.animate({ style: { opacity: 1 }, duration: 200 })
      })
    }, waitMs)
  }
  actualizarStats()
}

export function buscarNodo(texto) {
  if (!cy) return
  const q = texto.trim().toLowerCase()
  if (!q) {
    cy.nodes().removeClass('oculto-filtro')
    actualizarStats()
    return
  }
  let primerResultado = null
  cy.nodes().forEach((n) => {
    const coincide = n.data('label').toLowerCase().includes(q)
    n.toggleClass('oculto-filtro', !coincide)
    if (coincide && !primerResultado) {
      primerResultado = n
    }
  })
  if (primerResultado) {
    cy.animate({ center: { eles: primerResultado }, zoom: 1.2, duration: 400 })
  }
  actualizarStats()
}

let autocompleteHideTimer = null

export function mostrarAutocomplete(texto) {
  const container = document.getElementById('autocomplete')
  clearTimeout(autocompleteHideTimer)

  if (!cy || !texto.trim()) {
    container.classList.remove('visible')
    container.innerHTML = ''
    return
  }

  const q = texto.trim().toLowerCase()
  const matches = cy.nodes().filter(n => n.data('label').toLowerCase().includes(q))

  if (matches.length === 0) {
    container.classList.remove('visible')
    container.innerHTML = ''
    return
  }

  const maxMostrar = 20
  container.innerHTML = ''
  matches.slice(0, maxMostrar).forEach(n => {
    const item = document.createElement('div')
    item.className = 'autocomplete-item'
    const color = COLOR_POR_TIPO[n.data('tipo')] || '#888'
    item.innerHTML = `
      <span class="punto" style="background:${color}"></span>
      <span>${n.data('label')}</span>
      <span class="tipo-tag">${n.data('tipo')}</span>
    `
    item.addEventListener('click', () => {
      saltarANodo(n.id())
      container.classList.remove('visible')
      container.innerHTML = ''
      document.getElementById('buscar').value = ''
    })
    container.appendChild(item)
  })

  if (matches.length > maxMostrar) {
    const mas = document.createElement('div')
    mas.className = 'autocomplete-item'
    mas.style.cursor = 'default'
    mas.style.color = 'var(--text-secondary)'
    mas.textContent = `... y ${matches.length - maxMostrar} más`
    container.appendChild(mas)
  }

  container.classList.add('visible')
}

export function ocultarAutocomplete() {
  const container = document.getElementById('autocomplete')
  autocompleteHideTimer = setTimeout(() => {
    container.classList.remove('visible')
    container.innerHTML = ''
  }, 200)
}
