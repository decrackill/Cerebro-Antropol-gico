"""Limpieza de relaciones con tipos raciales (Paso 3 del plan).

Elimina relaciones con tipos no canónicos que son taxonomía racial del s. XIX:
- clasifica_como_activo (11) — Klemm clasifica pueblos como 'activos'
- clasifica_como_pasivo (4) — Klemm clasifica pueblos como 'pasivos'

También limpia otros tipos no canónicos obvios:
- presenta_rasgo (4) — pueblos presentan rasgos raciales
- venera_concepto (1)
- invadio (1)
- limita_expansion_a (1)
- afecta_a (2)
- descubierta_por (1)
- es_discípulo_de (1)
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data/grafo.db')
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'runtime/logs/limpieza_relaciones_raciales_log.json')

TIPOS_RACIALES = {
    'clasifica_como_activo',
    'clasifica_como_pasivo',
    'presenta_rasgo',
    'venera_concepto',
    'invaidio',
    'limita_expansion_a',
    'afecta_a',
    'descubierta_por',
    'es_discípulo_de',
    'desarrollada_por',
    'otorga_primacia_a',
    'representado_por',
    'contribuye_a',
    'usa_enfoque',
    'limita',
    'aplicado_a',
    'considera_indispensable',
}

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    
    # Listar relaciones con estos tipos
    placeholders = ','.join('?' for _ in TIPOS_RACIALES)
    c.execute(f'''
    SELECT r.id, r.tipo, n1.nombre as origen, n2.nombre as destino, r.fuente, r.cita_textual
    FROM relaciones r
    JOIN nodos n1 ON r.origen_id = n1.id
    JOIN nodos n2 ON r.destino_id = n2.id
    WHERE r.tipo IN ({placeholders})
    ORDER BY r.tipo
    ''', list(TIPOS_RACIALES))
    
    rows = c.fetchall()
    print(f'Relaciones a eliminar: {len(rows)}')
    print()
    
    log = []
    for r in rows:
        rel_id, tipo, origen, destino, fuente, cita = r
        cita_short = (cita[:80] + '...') if cita and len(cita) > 80 else (cita or '')
        print(f'  ✗ [{tipo:<25}] {origen:<35} → {destino:<35} | {fuente or ""}')
        if cita_short:
            print(f'    Cita: {cita_short}')
        
        # Eliminar
        c.execute("DELETE FROM relaciones WHERE id = ?", (rel_id,))
        log.append({
            "id": rel_id, "tipo": tipo, "origen": origen, "destino": destino,
            "fuente": fuente, "cita": cita, "accion": "eliminar"
        })
    
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM relaciones")
    rels_final = c.fetchone()[0]
    print(f'\nRelaciones restantes: {rels_final}')
    
    conn.close()
    
    with open(LOG_PATH, 'w') as f:
        json.dump({"timestamp": datetime.now().isoformat(), "eliminadas": log}, f, indent=2, ensure_ascii=False)
    print(f'Log guardado en {LOG_PATH}')

if __name__ == '__main__':
    main()
