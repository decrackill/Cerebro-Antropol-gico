"""Paso 7: Limpiar nodos aislados - eliminar ruido, preservar válidos."""
import sqlite3, json, sys
from pathlib import Path

db = Path(__file__).parent.parent / 'data' / 'grafo.db'
conn = sqlite3.connect(str(db), timeout=30)
conn.execute('PRAGMA foreign_keys = ON')

# 1. Eliminar aislados cultura/poblacion con contenido racial obsoleto
nombres_raciales = [
    'Alemanes del norte',
    'Antiguos habitantes de la India',
    'Asiáticos occidentales',
    'Clase educada de negros de América',
    'Egipcia',
    'Gitano',
    'Grupos de cabeza alargada',
    'Grupos de cabeza redonda',
    'Indios educados de la América española',
    'Indostánica',
    'Irlandés',
    'Judía',
    'Nobleza europea y gente común',
    'Patricios y plebeyos (Roma antigua)',
    'Población de Gales',
    'Población de Irlanda',
    'Población de Turkestán',
    'Población del África al sur del Sahara',
    'Pueblo de África del norte',
    'Suecos',
    'Árabes',
]

# También eliminar por patrón en descripción
cur = conn.execute('''
SELECT id, nombre FROM nodos n
WHERE n.tipo IN ('poblacion','cultura')
  AND NOT EXISTS (SELECT 1 FROM relaciones WHERE origen_id=n.id OR destino_id=n.id)
  AND (
    n.nombre IN ({})
    OR (n.descripcion LIKE '%clasificación racial%')
    OR (n.descripcion LIKE '%raza activa%')
    OR (n.descripcion LIKE '%raza pasiva%')
    OR (n.descripcion LIKE '%Carus otorgaba primacía%')
  )
'''.format(','.join('?' for _ in nombres_raciales)), nombres_raciales)

ids_eliminar = [r[0] for r in cur.fetchall()]
nombres_eliminar = [r[1] for r in cur.fetchall()]

# Re-fetch
cur = conn.execute('''
SELECT id, nombre, tipo FROM nodos n
WHERE n.tipo IN ('poblacion','cultura')
  AND NOT EXISTS (SELECT 1 FROM relaciones WHERE origen_id=n.id OR destino_id=n.id)
  AND (
    n.nombre IN ({0})
    OR (n.descripcion LIKE '%clasificación racial%')
    OR (n.descripcion LIKE '%raza activa%')
    OR (n.descripcion LIKE '%raza pasiva%')
    OR (n.descripcion LIKE '%Carus otorgaba primacía%')
  )
'''.format(','.join('?' for _ in nombres_raciales)), nombres_raciales)

to_delete = cur.fetchall()
print(f'Eliminando {len(to_delete)} nodos raciales aislados:')
for r in to_delete:
    print(f'  id={r[0]:>4}  [{r[2]:<10}] {r[1]}')
    conn.execute('DELETE FROM nodos WHERE id=?', (r[0],))

conn.commit()
print(f'\nTotal eliminados: {len(to_delete)}')

# 2. Eliminar conceptos aislados sin descripción o con nombres genéricos/sin valor
cur = conn.execute('''
SELECT id, nombre, descripcion FROM nodos n
WHERE n.tipo='concepto'
  AND NOT EXISTS (SELECT 1 FROM relaciones WHERE origen_id=n.id OR destino_id=n.id)
  AND (
    n.descripcion IS NULL OR n.descripcion = '' OR LENGTH(n.descripcion) < 20
    OR n.nombre LIKE '%(concepto)%'
  )
ORDER BY n.nombre
''')
conceptos_vacios = cur.fetchall()
print(f'\nConceptos aislados vacíos/genéricos: {len(conceptos_vacios)}')
for r in conceptos_vacios[:30]:
    desc = (r[2][:60] + '...') if r[2] else '(sin descripción)'
    print(f'  id={r[0]:>4}  {r[1]:<50} | {desc}')
if len(conceptos_vacios) > 30:
    print(f'  ... y {len(conceptos_vacios)-30} más')

eliminar_ids = [r[0] for r in conceptos_vacios]
for nid in eliminar_ids:
    conn.execute('DELETE FROM nodos WHERE id=?', (nid,))
conn.commit()
print(f'  Eliminados: {len(eliminar_ids)}')

# Estadísticas finales
cur = conn.execute('SELECT tipo, COUNT(*) FROM nodos GROUP BY tipo ORDER BY tipo')
print('\n=== Estado final nodos ===')
total_n = 0
for r in cur.fetchall():
    print(f'  {r[0]:<15} {r[1]}')
    total_n += r[1]
print(f'  {"TOTAL":<15} {total_n}')

cur = conn.execute('SELECT COUNT(*) FROM relaciones')
print(f'\nRelaciones: {cur.fetchone()[0]}')

cur = conn.execute('SELECT COUNT(*) FROM nodos n WHERE NOT EXISTS (SELECT 1 FROM relaciones WHERE origen_id=n.id OR destino_id=n.id)')
aislados = cur.fetchone()[0]
print(f'Aislados: {aislados} ({aislados*100/total_n:.1f}%)')

cur = conn.execute('SELECT tipo, COUNT(*) FROM nodos n WHERE NOT EXISTS (SELECT 1 FROM relaciones WHERE origen_id=n.id OR destino_id=n.id) GROUP BY tipo ORDER BY COUNT(*) DESC')
print('Aislados por tipo:')
for r in cur.fetchall():
    print(f'  {r[0]:<15} {r[1]}')

conn.close()
PYEOF