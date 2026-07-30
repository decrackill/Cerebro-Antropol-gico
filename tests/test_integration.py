"""Tests de integración del pipeline completo (Fase 7E).

Verifica el flujo completo: creación de nodos → inserción de relaciones
→ validación → exportación, simulando el ciclo real de extracción.
"""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from pipeline.core.db import (
    conectar_db, validar_relacion, fusionar_nodos,
    cargar_grados, construir_mapa_resolucion, migrar_revision_estado,
    marcar_nodos_revisados, relacion_ya_existe, relaciones_de,
    eliminar_nodo_cascada, COMPATIBILIDAD_RELACIONES,
)


# ── Fixture: DB en memoria ──────────────────────────────────────────

@pytest.fixture
def db():
    """Crea DB limpia en memoria con esquema completo."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE nodos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('autor','obra','concepto','escuela','corriente','cultura','poblacion','debate')),
            descripcion TEXT,
            metadatos TEXT DEFAULT '{}',
            revision_estado TEXT DEFAULT 'ok',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE relaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origen_id INTEGER NOT NULL REFERENCES nodos(id) ON DELETE CASCADE,
            destino_id INTEGER NOT NULL REFERENCES nodos(id) ON DELETE CASCADE,
            tipo TEXT NOT NULL,
            fuente TEXT,
            cita_textual TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE actividad_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accion TEXT NOT NULL,
            detalle TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    yield conn
    conn.close()


# ── Test 1: Ciclo completo de creación y validación ─────────────────

class TestCicloCompleto:
    """Simula el flujo real: extracción → nodos → relaciones → validación."""

    def test_crear_nodos_y_relaciones_validas(self, db):
        """Simula extracción: crear nodos y conectarlos con validación."""
        # Paso 1: Crear nodos (como haría el extractor)
        cur = db.execute(
            "INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
            ("Franz Boas", "autor")
        )
        boas = cur.lastrowid
        cur = db.execute(
            "INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
            ("Antropología Cultural", "obra")
        )
        obra = cur.lastrowid
        cur = db.execute(
            "INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
            ("Relativismo Cultural", "concepto")
        )
        concepto = cur.lastrowid

        # Paso 2: Validar y crear relaciones
        ok, err = validar_relacion(db, boas, obra, "autor_de",
                                   "libro.pdf", "Boas escribió esta obra")
        assert ok, f"autor_de debería ser válida: {err}"
        db.execute(
            "INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
            "VALUES (?, ?, ?, ?, ?)",
            (boas, obra, "autor_de", "libro.pdf", "Boas escribió esta obra")
        )

        ok, err = validar_relacion(db, boas, concepto, "desarrolla_concepto",
                                   "libro.pdf", "Boas desarrolló este concepto")
        assert ok
        db.execute(
            "INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
            "VALUES (?, ?, ?, ?, ?)",
            (boas, concepto, "desarrolla_concepto", "libro.pdf",
             "Boas desarrolló este concepto")
        )

        ok, err = validar_relacion(db, obra, concepto, "desarrolla_concepto",
                                   "libro.pdf", "La obra desarrolla el concepto")
        assert ok
        db.execute(
            "INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
            "VALUES (?, ?, ?, ?, ?)",
            (obra, concepto, "desarrolla_concepto", "libro.pdf",
             "La obra desarrolla el concepto")
        )

        db.commit()

        # Paso 3: Verificar
        assert db.execute("SELECT COUNT(*) FROM nodos").fetchone()[0] == 3
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 3
        grados = cargar_grados(db)
        assert grados.get(boas) == 2  # autor_de + desarrolla_concepto
        assert grados.get(obra) == 2  # autor_de + desarrolla_concepto

    def test_relacion_invalida_no_se_inserta(self, db):
        """Validación rechaza relación inválida y no se inserta."""
        cur = db.execute(
            "INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
            ("Obra Sola", "obra")
        )
        oid = cur.lastrowid
        ok, err = validar_relacion(db, oid, oid, "autor_de", "f", "c")
        assert not ok
        assert "reflexividad" in err
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 0

    def test_firewall_poblacion_en_ciclo(self, db):
        """Firewall se activa al insertar poblacion como origen indebido."""
        cur = db.execute(
            "INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
            ("Pueblo X", "poblacion")
        )
        pob = cur.lastrowid
        cur = db.execute(
            "INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
            ("Debate Y", "debate")
        )
        deb = cur.lastrowid

        # poblacion → debate: solo parte_del_debate
        ok, err = validar_relacion(db, pob, deb, "influenciado_por", "f", "c")
        assert not ok
        assert "Firewall" in err

        ok, err = validar_relacion(db, pob, deb, "parte_del_debate", "f", "c")
        assert ok


# ── Test 2: Fusión y resolución histórica ───────────────────────────

class TestFusionYMapa:
    """Verifica que fusionar_nodos y construir_mapa_resolucion funcionan juntos."""

    def test_fusion_preserva_ids_previos(self, db):
        """Fusión guarda ids_previos y el mapa los resuelve."""
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Franz Boas", "autor"))
        boas = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo, metadatos) VALUES (?, ?, ?)",
                         ("Franz Boas (antropólogo)", "autor",
                          '{"id_gemini": "boas_gemini_123"}'))
        dupe = cur.lastrowid

        # Crear relación al dupe
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Obra", "obra"))
        obra = cur.lastrowid
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente) "
                   "VALUES (?, ?, ?, ?)", (dupe, obra, "autor_de", "test"))
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 1

        # Fusionar
        fusionar_nodos(db, boas, dupe)

        # Verificar: relación redirigida a boas
        assert db.execute("SELECT origen_id FROM relaciones").fetchone()[0] == boas
        assert db.execute("SELECT COUNT(*) FROM nodos").fetchone()[0] == 2  # boas + obra

        # Verificar: mapa resuelve el id_gemini
        mapa = construir_mapa_resolucion(db)
        assert mapa.get(str(dupe)) == boas
        assert mapa.get("boas_gemini_123") == boas

    def test_fusion_id_inexistente_no_falla(self, db):
        """Fusionar con ID ya eliminado no lanza error."""
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Nodo Solo", "autor"))
        sid = cur.lastrowid
        fusionar_nodos(db, sid, 99999)
        assert db.execute("SELECT COUNT(*) FROM nodos").fetchone()[0] == 1


# ── Test 3: Exportación simulada ────────────────────────────────────

class TestExportSimulado:
    """Verifica que la exportación produce JSON válido para Cytoscape."""

    def test_export_formato_correcto(self, db):
        """Simula export_json.py y verifica el formato Cytoscape."""
        # Crear grafo pequeño
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Autor A", "autor"))
        a = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Obra B", "obra"))
        b = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Concepto C", "concepto"))
        c = cur.lastrowid
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                   "VALUES (?, ?, ?, ?, ?)", (a, b, "autor_de", "libro.pdf", "cita"))
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente) "
                   "VALUES (?, ?, ?, ?)", (a, c, "desarrolla_concepto", "libro.pdf"))

        # Construir JSON como export_json.py
        nodos = db.execute("SELECT id, nombre, tipo, descripcion FROM nodos").fetchall()
        relaciones = db.execute(
            "SELECT r.id, no.nombre AS origen, nd.nombre AS destino, r.tipo, "
            "r.fuente, r.cita_textual FROM relaciones r "
            "JOIN nodos no ON r.origen_id = no.id "
            "JOIN nodos nd ON r.destino_id = nd.id"
        ).fetchall()

        elements = []
        for n in nodos:
            elements.append({
                "data": {"id": str(n[0]), "nombre": n[1], "tipo": n[2], "descripcion": n[3] or ""}
            })
        for r in relaciones:
            elements.append({
                "data": {
                    "id": str(r[0]), "source": str(r[1]), "target": str(r[2]),
                    "tipo": r[3], "fuente": r[4] or "", "cita_textual": r[5] or ""
                }
            })

        json_str = json.dumps({"elements": elements}, ensure_ascii=False, indent=2)
        parsed = json.loads(json_str)

        assert len(parsed["elements"]) == 5  # 3 nodos + 2 relaciones
        nodes = [e for e in parsed["elements"] if "source" not in e.get("data", {})]
        edges = [e for e in parsed["elements"] if "source" in e.get("data", {})]
        assert len(nodes) == 3
        assert len(edges) == 2
        assert edges[0]["data"]["tipo"] == "autor_de"

    def test_export_sin_relaciones(self, db):
        """Export con grafo vacío produce JSON válido."""
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Autor Único", "autor"))
        elements = [{"data": {"id": str(cur.lastrowid), "nombre": "Autor Único", "tipo": "autor"}}]
        json_str = json.dumps({"elements": elements})
        parsed = json.loads(json_str)
        assert len(parsed["elements"]) == 1


# ── Test 4: Relaciones duplicadas post-fusión ───────────────────────

class TestDedupPostFusion:
    """Verifica que fusionar_nodos elimina relaciones duplicadas."""

    def test_duplicados_se_limpian(self, db):
        """Dos nodos con misma relación al fusionar dejan solo una."""
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Boas", "autor"))
        b1 = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Franz Boas", "autor"))
        b2 = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Obra", "obra"))
        obra = cur.lastrowid

        # Ambos conectados a la misma obra
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo) VALUES (?, ?, ?)",
                   (b1, obra, "autor_de"))
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo) VALUES (?, ?, ?)",
                   (b2, obra, "autor_de"))
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 2

        # Fusionar
        fusionar_nodos(db, b1, b2)

        # Solo 1 relación debe quedar
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 1


# ── Test 5: Funciones helper ────────────────────────────────────────

class TestHelperFunctions:
    """Unit tests para funciones auxiliares."""

    def test_relacion_ya_existe(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("A", "autor"))
        a = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("B", "obra"))
        b = cur.lastrowid
        assert not relacion_ya_existe(db, a, b, "autor_de")
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo) VALUES (?, ?, ?)",
                   (a, b, "autor_de"))
        assert relacion_ya_existe(db, a, b, "autor_de")

    def test_relaciones_de(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("A", "autor"))
        a = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("B", "obra"))
        b = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("C", "obra"))
        c = cur.lastrowid
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo) VALUES (?, ?, ?)",
                   (a, b, "autor_de"))
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo) VALUES (?, ?, ?)",
                   (c, a, "influenciado_por"))
        rels = relaciones_de(db, a)
        assert len(rels) == 2
        assert any(r["direccion"] == "saliente" and r["tipo"] == "autor_de" for r in rels)
        assert any(r["direccion"] == "entrante" and r["tipo"] == "influenciado_por" for r in rels)

    def test_eliminar_nodo_cascada(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("A", "autor"))
        a = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("B", "obra"))
        b = cur.lastrowid
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo) VALUES (?, ?, ?)",
                   (a, b, "autor_de"))
        eliminar_nodo_cascada(db, a)
        assert db.execute("SELECT COUNT(*) FROM nodos").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 0

    def test_cargar_grados_grafo_vacio(self, db):
        assert cargar_grados(db) == {}

    def test_migrar_revision_marca_ok(self, db):
        """migrar_revision_estado marca nodos existentes como ok."""
        db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("A", "autor"))
        migrar_revision_estado(db)
        estado = db.execute("SELECT revision_estado FROM nodos").fetchone()[0]
        assert estado == "ok"

    def test_marcar_revisados_por_tipo(self, db):
        db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("A", "autor"))
        db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("B", "obra"))
        cnt = marcar_nodos_revisados(db, tipo="autor")
        assert cnt == 1

    def test_marcar_revisados_por_ids(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("A", "autor"))
        a = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", ("B", "autor"))
        b = cur.lastrowid
        cnt = marcar_nodos_revisados(db, ids=[a, b])
        assert cnt == 2
