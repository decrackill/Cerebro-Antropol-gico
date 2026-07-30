"""Reparar firewall: revertir poblacion→cultura para nodos mal clasificados,
y eliminar relaciones inválidas restantes."""
import sqlite3, json
from pathlib import Path

db = Path(__file__).parent.parent / 'data' / 'grafo.db'
conn = sqlite3.connect(str(db), timeout=30)
conn.execute('PRAGMA foreign_keys = ON')

# Identificar violaciones de firewall
cur = conn.execute('''
SELECT r.id, r.tipo, n1.id as oid, n1.nombre as oname, n1.tipo as otype,
       n2.id as did, n2.nombre as dname, n2.tipo as dtype
FROM relaciones r
JOIN nodos n1 ON r.origen_id=n1.id
JOIN nodos n2 ON r.destino_id=n2.id
WHERE (n1.tipo='poblacion' AND r.tipo NOT IN ('parte_del_debate'))
   OR (n2.tipo='poblacion' AND r.tipo NOT IN ('estudia_a'))
''')

viols = cur.fetchall()
print(f'Violaciones de firewall: {len(viols)}')

# Agrupar por nodo poblacion origen para decidir
# Caso 1: nodos que son CULTURA (no poblacion) → revertir
revertir_a_cultura = {
    'Trobriand': 'Cultura de las islas Trobriand, estudiada por Malinowski',
    'Esquimales': 'Cultura y forma de vida de los pueblos esquimales',
    'Civilización china': 'Civilización china antigua',
    'Culturas melanesias': 'Culturas de la región de Melanesia',
    'Malayos': 'Pueblos y culturas malayas',
    'Indios americanos': 'Pueblos indígenas de América',
    'América Central': 'Región cultural de América Central',
    'Nuevo Mundo': 'Concepto histórico-cultural de las Américas',
    'Bosquimanos': 'Pueblos cazadores-recolectores del sur de África',
    'Población del África del Sud': 'Culturas del sur de África',
}

# Caso 2: nodos que deben seguir siendo poblacion pero sus relaciones deben eliminarse
eliminar_relaciones = {
    # Estas son relaciones incorrectas por el cambio de tipo
    'Europeos': ['Clasificación de razas'],
    'Europeo noroccidental': ['Edad de Piedra'],
    'Egipcios': ['Europeo noroccidental'],
    'Pueblo de la India': ['Barreras sociales'],
    'Razas mestizas': ['Bornú'],
}

# Identificar qué nodos de los violadores deben revertirse a cultura
nodos_a_revertir_ids = set()
for v in viols:
    if v[4] == 'poblacion' and v[3] in revertir_a_cultura:  # origen es poblacion
        nodos_a_revertir_ids.add(v[2])
    if v[7] == 'poblacion' and v[6] in revertir_a_cultura:  # destino es poblacion
        nodos_a_revertir_ids.add(v[5])

# Ejecutar reversiones
print(f'\nNodos a revertir a cultura: {len(nodos_a_revertir_ids)}')
for nid in nodos_a_revertir_ids:
    cur = conn.execute('SELECT nombre, descripcion FROM nodos WHERE id=?', (nid,))
    r = cur.fetchone()
    if r:
        new_desc = revertir_a_cultura.get(r[0], r[1] or '')
        conn.execute('UPDATE nodos SET tipo="cultura", descripcion=? WHERE id=?', (new_desc, nid))
        print(f'  id={nid}  {r[0]} → cultura')

conn.commit()

# Verificar firewall de nuevo
cur = conn.execute('''
SELECT COUNT(*) FROM relaciones r
JOIN nodos n1 ON r.origen_id=n1.id
JOIN nodos n2 ON r.destino_id=n2.id
WHERE (n1.tipo='poblacion' AND r.tipo NOT IN ('parte_del_debate'))
   OR (n2.tipo='poblacion' AND r.tipo NOT IN ('estudia_a'))
''')
restantes = cur.fetchone()[0]
print(f'\nViolaciones restantes después de revertir: {restantes}')

# Eliminar relaciones inválidas restantes
if restantes > 0:
    cur = conn.execute('''
    SELECT r.id, r.tipo, n1.nombre, n2.nombre
    FROM relaciones r
    JOIN nodos n1 ON r.origen_id=n1.id
    JOIN nodos n2 ON r.destino_id=n2.id
    WHERE (n1.tipo='poblacion' AND r.tipo NOT IN ('parte_del_debate'))
       OR (n2.tipo='poblacion' AND r.tipo NOT IN ('estudia_a'))
    ''')
    for v in cur.fetchall():
        print(f'  Eliminando: {v[1]:25} {v[2]:35} → {v[3]}')
        conn.execute('DELETE FROM relaciones WHERE id=?', (v[0],))
    conn.commit()

# Verificación final
cur = conn.execute('''
SELECT COUNT(*) FROM relaciones r
JOIN nodos n1 ON r.origen_id=n1.id
JOIN nodos n2 ON r.destino_id=n2.id
WHERE (n1.tipo='poblacion' AND r.tipo NOT IN ('parte_del_debate'))
   OR (n2.tipo='poblacion' AND r.tipo NOT IN ('estudia_a'))
''')
final = cur.fetchone()[0]
print(f'\nViolaciones de firewall finales: {final}')

# Stats
cur = conn.execute('SELECT tipo, COUNT(*) FROM nodos GROUP BY tipo ORDER BY tipo')
print('\nNodos:')
for r in cur.fetchall():
    print(f'  {r[0]:<15} {r[1]}')

cur = conn.execute('SELECT COUNT(*) FROM relaciones')
print(f'\nRelaciones: {cur.fetchone()[0]}')

cur = conn.execute('SELECT COUNT(*) FROM nodos n WHERE NOT EXISTS (SELECT 1 FROM relaciones WHERE origen_id=n.id OR destino_id=n.id)')
isol = cur.fetchone()[0]
cur2 = conn.execute('SELECT COUNT(*) FROM nodos')
total = cur2.fetchone()[0]
print(f'Aislados: {isol} ({isol*100/total:.1f}%)')

conn.close()
