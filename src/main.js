import { cargarGrafo } from './grafo.js'
import { inicializarVisualizacion, filtrarPorTipo, buscarNodo } from './render.js'

async function init() {
  try {
    const { nodos, relaciones } = await cargarGrafo()
    inicializarVisualizacion(nodos, relaciones)

    document.getElementById('loading').classList.add('oculto')
  } catch (e) {
    document.getElementById('loading').textContent = `Error al cargar: ${e.message}`
    return
  }

  document.querySelectorAll('#filtros button').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#filtros button').forEach(b => b.classList.remove('activo'))
      btn.classList.add('activo')
      filtrarPorTipo(btn.dataset.tipo)
    })
  })

  document.getElementById('buscar').addEventListener('input', (e) => {
    buscarNodo(e.target.value)
  })
}

init()
