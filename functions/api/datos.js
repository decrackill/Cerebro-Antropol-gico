const NIVEL_A = new Set([
  'autor_de', 'influenciado_por', 'critica_a', 'desarrolla_concepto',
  'redefine_a', 'precursor_de', 'pertenece_a', 'estudia_a',
  'contemporaneo_de', 'parte_del_debate', 'es_mentor_de', 'colabora_con'
])

export async function onRequest(context) {
  const { env } = context

  try {
    const [nodosRes, relsRes] = await Promise.all([
      env.GRAFO_DB.prepare('SELECT * FROM nodos').all(),
      env.GRAFO_DB.prepare('SELECT * FROM relaciones').all(),
    ])

    const nodos = nodosRes.results.map((n) => ({
      id: n.id,
      nombre: n.nombre,
      tipo: n.tipo,
      descripcion: n.descripcion || '',
      metadatos: n.metadatos || '{}',
    }))

    const relaciones = relsRes.results.map((r) => {
      let evidencia = 'ninguna'
      if (r.cita_textual) {
        evidencia = 'cita'
      } else if (r.fuente) {
        evidencia = 'fuente'
      }

      return {
        id: r.id,
        origen_id: r.origen_id,
        destino_id: r.destino_id,
        tipo: r.tipo,
        tipoedge: r.nivel || (NIVEL_A.has(r.tipo) ? 'Nivel_A' : 'Nivel_B'),
        evidencia,
        nota: r.fuente || '',
        fuente: r.fuente || '',
        cita_textual: r.cita_textual || '',
      }
    })

    return Response.json({
      ok: true,
      nodos,
      relaciones,
      metadatos: {
        total_nodos: nodos.length,
        total_relaciones: relaciones.length,
      },
    })
  } catch (error) {
    return Response.json(
      { ok: false, error: error.message, codigo: 'DB_ERROR' },
      { status: 500 },
    )
  }
}
