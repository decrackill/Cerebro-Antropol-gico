import { cargarGrafo } from './grafo.js'
import { inicializarVisualizacion, filtrarPorTipo, buscarNodo, setTotalCounts, mostrarAutocomplete, ocultarAutocomplete } from './render.js'

async function init() {
  try {
    const { nodos, relaciones } = await cargarGrafo()
    inicializarVisualizacion(nodos, relaciones)
    setTotalCounts(nodos.length, relaciones.length)

    document.getElementById('stats').textContent = `${nodos.length} nodos · ${relaciones.length} conexiones`
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

  const searchInput = document.getElementById('buscar')
  searchInput.addEventListener('input', (e) => {
    buscarNodo(e.target.value)
    mostrarAutocomplete(e.target.value)
  })
  searchInput.addEventListener('focus', (e) => {
    if (e.target.value.trim()) mostrarAutocomplete(e.target.value)
  })
  searchInput.addEventListener('blur', () => ocultarAutocomplete())
}

init()
