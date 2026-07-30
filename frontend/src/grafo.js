export async function cargarGrafo() {
  const respuesta = await fetch('/api/datos')
  if (!respuesta.ok) {
    throw new Error(`Error HTTP ${respuesta.status}`)
  }
  const datos = await respuesta.json()
  if (!datos.ok) {
    throw new Error(datos.error || 'Error del servidor')
  }
  const { nodos, relaciones } = datos
  return { nodos, relaciones }
}
