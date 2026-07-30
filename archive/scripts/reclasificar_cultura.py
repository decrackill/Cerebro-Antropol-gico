"""Reclasificación de nodos 'cultura' → 'poblacion' o eliminación.

Criterios:
- POBLACION: grupos demográficos, geográficos, étnicos (origen/ubicación)
- CULTURA (mantener): prácticas, creencias, organización social, regiones culturales
- ELIMINAR: términos de tipología racial del s. XIX que son pseudociencia
- CONCEPTO: términos raciales abstractos (e.g. 'Raza caucásica')
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data/grafo.db')
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'runtime/logs/reclasificacion_cultura_log.json')

# Categorización manual de cada nodo cultura
RECLASIFICAR_A_POBLACION = {
    # Grupos étnicos/demográficos claramente poblacionales
    "Aborígenes australianos",
    "Aborígenes del Nordeste asiático",
    "Alemanes del norte",
    "Antiguos habitantes de la India",
    "Asia occidental",
    "Asia oriental",
    "Asiáticos occidentales",
    "Australianos",
    "Bereberes arabizados",
    "Bornú",
    "Bosquimanos",
    "Celtas",
    "Cherqueses",
    "Egipcia",
    "Egipcios",
    "Españoles",
    "Esquimal de Smith Sound",
    "Esquimales",
    "Estados Unidos",
    "Europeo noroccidental",
    "Europeos",
    "Europeos del período Neolítico",
    "Europeos modernos",
    "Francos",
    "Griegos",
    "Incas del Perú",
    "Indios americanos",
    "Indios californianos",
    "Indios Chippewa",
    "Indios Pueblo",
    "Indostánica",
    "Italianos del norte",
    "Italianos del sud",
    "Japoneses",
    "Japoneses de Hawái",
    "Judía",
    "Judíos",
    "Mailu",
    "Malayos",
    "Massim meridionales",
    "Motu",
    "Negros Americanos",
    "Negros de África",
    "Negros del Océano Pacífico",
    "Norteamérica",
    "Papúe-melanesios",
    "Papúes",
    "Patricios",
    "Persas",
    "Plebeyos",
    "Población de Asia Meridional",
    "Población de Turkestán",
    "Población de la Península Malaya",
    "Población de las Islas Andamán",
    "Población de las Islas Filipinas",
    "Población del África al sur del Sahara",
    "Población del África del Sud",
    "Polinesios",
    "Pueblo de África del norte",
    "Pueblo de la India",
    "Pueblos africanos",
    "Pueblos de Asia Central",
    "Pueblos germánicos",
    "República Argentina",
    "Romanos",
    "Suecos",
    "Tasmanios",
    "Tribus del golfo de Papua",
    "Tribus hamíticas",
    "Trobriand",
    "Trobriandeses",
    "Turcos",
    "Tártaros",
    "África noroccidental",
    "Árabes",
    "América",
    "América Central",
}

RECLASIFICAR_A_CONCEPTO = {
    # Términos raciales abstractos (conceptos raciales históricos)
    "Raza caucásica",
    "Raza nórdica",
    "Razas negras",
    "Australiano (tipo humano)",
    "Mongólicos",
}

ELIMINAR = {
    # Términos de tipología racial ofensiva/obsoleta del s. XIX
    "Australoides de Asia meridional",
    "Bastardos Sudafricanos",
    "Castas de Bengala",
    "Kurdos rubios",
    "Pueblo de cabeza alargada de la costa de Siria",
    "Pueblo de cabeza redonda del Asia Central",
}

# Mantener como cultura
MANTENER_CULTURA = {
    "Antiguo Perú",
    "Civilización china",
    "Civilización moderna",
    "Columbia Británica",
    "Cultura Paleolítica",
    "Cultura de Méjico",
    "Cultura de Nuevo Méjico",
    "Cultura de la Costa Noroccidental de América",
    "Cultura de la Costa de Alaska",
    "Cultura de la India",
    "Cultura de la Isla de Vancouver",
    "Cultura de la Madeleine (Francia)",
    "Cultura de África",
    "Cultura del árido Sudoeste",
    "Cultura europea",
    "Cultura mexicana precolombina",
    "Cultura peruana precolombina",
    "Culturas americanas primitivas",
    "Culturas antiguas de Argentina y Nuevo Méjico",
    "Culturas melanesias",
    "Egipto antiguo",
    "Estrecho de Davis",
    "Europa feudal",
    "Islas del Almirantazgo",
    "Islas Marquesas",
    "Malasia",
    "Noroeste de América (región cultural)",
    "Península de Cumberland",
    "Río Columbia de Norte América (región cultural)",
    "Roma",
    "Sud América (región cultural)",
    "Sudán occidental",
    "Tradición europea occidental",
    "Yucatán",
}

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    
    # Check: todos los nodos cultura existen
    c.execute("SELECT id, nombre FROM nodos WHERE tipo = 'cultura' ORDER BY nombre")
    todos = {r[1]: r[0] for r in c.fetchall()}
    
    todos_nombres = set(todos.keys())
    categorizados = RECLASIFICAR_A_POBLACION | RECLASIFICAR_A_CONCEPTO | ELIMINAR | MANTENER_CULTURA
    
    no_categorizados = todos_nombres - categorizados
    if no_categorizados:
        print(f"⚠️  Nodos sin categorizar ({len(no_categorizados)}):")
        for n in sorted(no_categorizados):
            print(f"     {n}")
        print()
    
    # Verificar que no haya nombres en múltiples categorías
    for nombre in todos_nombres:
        cats = []
        if nombre in RECLASIFICAR_A_POBLACION: cats.append("POBLACION")
        if nombre in RECLASIFICAR_A_CONCEPTO: cats.append("CONCEPTO")
        if nombre in ELIMINAR: cats.append("ELIMINAR")
        if nombre in MANTENER_CULTURA: cats.append("CULTURA")
        if len(cats) > 1:
            print(f"❌ CONFLICTO: {nombre} está en {cats}")
    
    # Ejecutar reclasificaciones
    log = []
    
    # 1. Reclasificar a poblacion
    for nombre in RECLASIFICAR_A_POBLACION:
        if nombre in todos:
            nid = todos[nombre]
            c.execute("UPDATE nodos SET tipo = 'poblacion' WHERE id = ?", (nid,))
            log.append({"id": nid, "nombre": nombre, "tipo_anterior": "cultura", "tipo_nuevo": "poblacion", "accion": "reclasificar"})
            print(f"  → poblacion: {nombre} (id={nid})")
    
    # 2. Reclasificar a concepto
    for nombre in RECLASIFICAR_A_CONCEPTO:
        if nombre in todos:
            nid = todos[nombre]
            c.execute("UPDATE nodos SET tipo = 'concepto' WHERE id = ?", (nid,))
            log.append({"id": nid, "nombre": nombre, "tipo_anterior": "cultura", "tipo_nuevo": "concepto", "accion": "reclasificar"})
            print(f"  → concepto: {nombre} (id={nid})")
    
    # 3. Eliminar (cascada: borra relaciones primero)
    for nombre in ELIMINAR:
        if nombre in todos:
            nid = todos[nombre]
            # Verificar si tiene relaciones
            c.execute("SELECT COUNT(*) FROM relaciones WHERE origen_id = ? OR destino_id = ?", (nid, nid))
            rel_count = c.fetchone()[0]
            if rel_count > 0:
                print(f"  ⚠  {nombre} (id={nid}) tiene {rel_count} relación(es) - se borrarán en cascada")
            c.execute("DELETE FROM relaciones WHERE origen_id = ? OR destino_id = ?", (nid, nid))
            c.execute("DELETE FROM nodos WHERE id = ?", (nid,))
            log.append({"id": nid, "nombre": nombre, "tipo_anterior": "cultura", "tipo_nuevo": None, "accion": "eliminar"})
            print(f"  ✗ eliminado: {nombre} (id={nid})")
    
    conn.commit()
    
    # Estadísticas finales
    c.execute("SELECT tipo, COUNT(*) FROM nodos GROUP BY tipo ORDER BY tipo")
    print(f"\n=== Estado final de nodos por tipo ===")
    for r in c.fetchall():
        print(f"  {r[0]:<15} {r[1]}")
    
    c.execute("SELECT COUNT(*) FROM nodos WHERE tipo = 'cultura'")
    cultura_final = c.fetchone()[0]
    print(f"\nCultura: 122 → {cultura_final}")
    
    conn.close()
    
    # Guardar log
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, 'w') as f:
        json.dump({"timestamp": datetime.now().isoformat(), "acciones": log}, f, indent=2)
    print(f"\nLog guardado en {LOG_PATH}")

if __name__ == '__main__':
    main()
