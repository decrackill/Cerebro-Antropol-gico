import cytoscape from 'cytoscape'
import fcose from 'cytoscape-fcose'

cytoscape.use(fcose)

let cy = null
let datosOriginales = { nodos: [], relaciones: [] }

const COLOR_POR_TIPO = {
  autor: '#D85A30',
  obra: '#1D9E75',
  concepto: '#7F77DD',
  escuela: '#BA7517',
  cultura: '#639922',
  debate: '#D4537E',
}

export function inicializarVisualizacion(nodos, relaciones) {
  datosOriginales = { nodos, relaciones }

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
          width: (ele) => 24 + ele.degree() * 6,
          height: (ele) => 24 + ele.degree() * 6,
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
      {
        selector: '.atenuado',
        style: { opacity: 0.15 },
      },
    ],
    layout: {
      name: 'fcose',
      randomize: true,
      animate: true,
      animationDuration: 800,
      nodeRepulsion: 8000,
      idealEdgeLength: 100,
      edgeElasticity: 0.1,
      gravity: 0.3,
      numIter: 2500,
      tile: true,
      packComponents: true,
      componentSpacing: 150,
    },
  })

  cy.on('tap', 'node', (evt) => mostrarPanel(evt.target.data()))
  cy.on('mouseover', 'edge', (evt) => evt.target.addClass('resaltada'))
  cy.on('mouseout', 'edge', (evt) => evt.target.removeClass('resaltada'))
  document.getElementById('cerrar-panel').addEventListener('click', ocultarPanel)
}

function mostrarPanel(nodo) {
  document.getElementById('panel-titulo').textContent = nodo.label
  document.getElementById('panel-tipo').textContent = nodo.tipo
  document.getElementById('panel-desc').textContent = nodo.resumen || ''

  const ul = document.getElementById('panel-relaciones')
  ul.innerHTML = ''
  const conectadas = cy.getElementById(nodo.id).connectedEdges()
  conectadas.forEach((edge) => {
    const otroId = edge.data('source') === nodo.id ? edge.data('target') : edge.data('source')
    const otro = cy.getElementById(otroId).data('label')

    const li = document.createElement('li')
    li.textContent = `${edge.data('label')} → ${otro}`
    li.classList.add('relacion-link')
    li.addEventListener('click', () => saltarANodo(otroId))
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
  cy.nodes().unselect()
  nodo.select()
  mostrarPanel(nodo.data())
}

function ocultarPanel() {
  document.getElementById('panel').classList.add('oculto')
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
  cy.nodes().forEach((n) => {
    const coincide = n.data('label').toLowerCase().includes(q)
    n.toggleClass('oculto-filtro', !coincide)
  })
}
