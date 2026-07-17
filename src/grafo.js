// Carga el grafo desde el JSON exportado de SQLite (ver scripts/export_json.py)

export async function cargarGrafo() {
  const respuesta = await fetch('/src/datos.json')
  const datos = await respuesta.json()
  return datos // { nodos: [...], relaciones: [...] }
}
