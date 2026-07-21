import cytoscape from 'cytoscape'
import fcose from 'cytoscape-fcose'

cytoscape.use(fcose)

let cy = null
let nodoActual = null

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

  cy = cytoscape({
    container: document.getElementById('grafo'),
    elements: elementos,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': (ele) => COLOR_POR_TIPO[ele.data('tipo')] || '#888',
          label: 'data(label)',
          color: '#eee',
          'font-size': 11,
          'text-valign': 'bottom',
          'text-margin-y': 6,
          width: (ele) => {
            const d = ele.degree()
            return d > 10 ? 30 + d * 3 : 20 + d * 4
          },
          height: (ele) => {
            const d = ele.degree()
            return d > 10 ? 30 + d * 3 : 20 + d * 4
          },
        },
      },
      {
        selector: 'edge',
        style: {
          width: 1.5,
          'line-color': '#555',
          'target-arrow-color': '#555',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          label: 'data(label)',
          'font-size': 9,
          color: '#999',
          'text-rotation': 'autorotate',
          'text-opacity': 0,
        },
      },
      {
        selector: 'edge:active, edge.resaltada',
        style: { 'text-opacity': 1, 'line-color': '#aaa' },
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
    ],
    layout: {
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
    },
  })

  cy.on('tap', 'node', (evt) => {
    activarVecindario(evt.target)
    mostrarPanel(evt.target.data())
  })

  cy.on('tap', (evt) => {
    if (evt.target === cy) {
      desactivarVecindario()
      ocultarPanel()
    }
  })

  cy.on('mouseover', 'node', (evt) => mostrarTooltip(evt.originalEvent, evt.target.data()))
  cy.on('mouseout', 'node', () => ocultarTooltip())
  cy.on('mouseover', 'edge', (evt) => evt.target.addClass('resaltada'))
  cy.on('mouseout', 'edge', (evt) => evt.target.removeClass('resaltada'))
  cy.on('mousemove', (evt) => moverTooltip(evt.originalEvent))

  document.getElementById('cerrar-panel').addEventListener('click', () => {
    desactivarVecindario()
    ocultarPanel()
  })

  cy.on('zoom', () => {
    const zoomActual = cy.zoom()
    cy.style()
      .selector('node')
      .style('label', zoomActual > 0.6 ? 'data(label)' : '')
      .update()
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

  document.getElementById('panel-titulo').textContent = nodo.label
  document.getElementById('panel-tipo').textContent = `${nodo.tipo} · Grado: ${grado}`
  document.getElementById('panel-desc').textContent = nodo.resumen || ''

  const ul = document.getElementById('panel-relaciones')
  ul.innerHTML = ''
  const conectadas = cy.getElementById(nodo.id).connectedEdges()
  conectadas.forEach((edge) => {
    const otroId = edge.data('source') === nodo.id ? edge.data('target') : edge.data('source')
    const otro = cy.getElementById(otroId).data('label')
    const cita = edge.data('cita')

    const li = document.createElement('li')
    li.classList.add('relacion-link')
    li.textContent = `${edge.data('label')} → ${otro}`
    if (cita) {
      li.title = cita
    }
    li.addEventListener('click', () => {
      saltarANodo(otroId)
      if (cita) {
        mostrarCita(edge.data('label'), otro, cita)
      }
    })
    ul.appendChild(li)
  })

  document.getElementById('panel').classList.remove('oculto')
}

function saltarANodo(id) {
  const nodo = cy.getElementById(id)
  cy.animate({
    center: { eles: nodo },
    zoom: 1.2,
    duration: 400,
  })
  activarVecindario(nodo)
  mostrarPanel(nodo.data())
}

function ocultarPanel() {
  document.getElementById('panel').classList.add('oculto')
  ocultarCita()
}

function mostrarCita(tipo, destino, cita) {
  const div = document.getElementById('panel-cita')
  div.textContent = ''
  const strong = document.createElement('strong')
  strong.textContent = 'Cita textual: '
  const em = document.createElement('em')
  em.textContent = `"${cita}"`
  div.appendChild(strong)
  div.appendChild(em)
  div.classList.remove('oculto')
}

function ocultarCita() {
  const div = document.getElementById('panel-cita')
  if (div) div.classList.add('oculto')
}

function mostrarTooltip(event, nodo) {
  const tooltip = document.getElementById('tooltip')
  document.getElementById('tooltip-tipo').textContent = nodo.tipo
  document.getElementById('tooltip-nombre').textContent = nodo.label
  document.getElementById('tooltip-desc').textContent = nodo.resumen || ''
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

export function filtrarPorTipo(tipo) {
  if (!cy) return
  if (tipo === 'todos') {
    cy.nodes().removeClass('oculto-filtro')
    return
  }
  cy.nodes().forEach((n) => {
    n.toggleClass('oculto-filtro', n.data('tipo') !== tipo)
  })
}

export function buscarNodo(texto) {
  if (!cy) return
  const q = texto.trim().toLowerCase()
  if (!q) {
    cy.nodes().removeClass('oculto-filtro')
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
}
