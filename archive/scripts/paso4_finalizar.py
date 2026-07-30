"""Paso 4 (completar): eliminar UNESCO, fusionar Racionalistas, verificar estado."""
import sqlite3, os, json

db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data/grafo.db')
conn = sqlite3.connect(db, timeout=10)
conn.execute('PRAGMA foreign_keys = ON')

# 1. Eliminar UNESCO (0 relaciones, no es tipo ontológico)
cur = conn.execute('SELECT id, nombre FROM nodos WHERE id=1407')
r = cur.fetchone()
print(f'Eliminando: {r[1]} (id={r[0]})')
conn.execute('DELETE FROM nodos WHERE id=1407')

# 2. Fusionar Racionalistas del siglo XVIII (id=380) → Racionalismo del siglo XVIII (id=784)
# Re-apuntar relaciones (aunque ambas tienen 0)
conn.execute('UPDATE relaciones SET origen_id=784 WHERE origen_id=380 AND destino_id!=784')
conn.execute('UPDATE relaciones SET destino_id=784 WHERE destino_id=380 AND origen_id!=784')
# Eliminar duplicadas
conn.execute('''
DELETE FROM relaciones WHERE id IN (
    SELECT r1.id FROM relaciones r1
    JOIN relaciones r2 ON r1.origen_id=r2.origen_id AND r1.destino_id=r2.destino_id AND r1.tipo=r2.tipo
    WHERE r1.id < r2.id AND (r1.origen_id=784 OR r1.destino_id=784)
)''')
# Eliminar nodo 380
conn.execute('DELETE FROM nodos WHERE id=380')
print('Fusionado: Racionalistas s.XVIII (380) → Racionalismo s.XVIII (784)')

# Preservar histórico
cur = conn.execute('SELECT metadatos FROM nodos WHERE id=784')
md = cur.fetchone()[0]
meta = json.loads(md) if md and md != '{}' else {}
ids_previos = meta.get('ids_previos', [])
ids_previos.append(380)
meta['ids_previos'] = ids_previos
conn.execute('UPDATE nodos SET metadatos=? WHERE id=784', (json.dumps(meta, ensure_ascii=False),))

conn.commit()

# Verificar
cur = conn.execute('SELECT tipo, COUNT(*) FROM nodos GROUP BY tipo ORDER BY tipo')
print('\n=== NODOS ===')
total_n = 0
for r in cur.fetchall():
    print(f'  {r[0]:<15} {r[1]}')
    total_n += r[1]
print(f'  {"TOTAL":<15} {total_n}')

cur = conn.execute('SELECT COUNT(*) FROM relaciones')
print(f'\nRelaciones: {cur.fetchone()[0]}')

cur = conn.execute('SELECT COUNT(*) FROM nodos n WHERE NOT EXISTS (SELECT 1 FROM relaciones WHERE origen_id=n.id OR destino_id=n.id)')
isol = cur.fetchone()[0]
print(f'Aislados: {isol} ({isol*100/total_n:.1f}%)')

# Verificar no-canónicas
cur = conn.execute('''
SELECT r.tipo, COUNT(*) FROM relaciones r
WHERE r.tipo NOT IN (
    'autor_de','influenciado_por','critica_a','desarrolla_concepto',
    'redefine_a','precursor_de','pertenece_a','estudia_a',
    'contemporaneo_de','parte_del_debate','es_mentor_de','colabora_con',
    'contradice','relacionado_con','depende_de')
GROUP BY r.tipo
''')
remaining = cur.fetchall()
if remaining:
    print(f'\n⚠️  No-canónicas: {remaining}')
else:
    print('\n✓ Todas las relaciones son canónicas')

# Escuelas y corrientes final
cur = conn.execute('SELECT id, nombre, tipo FROM nodos WHERE tipo IN ("escuela","corriente") ORDER BY tipo, nombre')
print('\n=== Escuelas y Corrientes ===')
for r in cur.fetchall():
    print(f'  {r[2]:<10} id={r[0]:>4}  {r[1]}')

conn.close()
