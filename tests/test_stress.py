"""Stress Testing Intelectual (08C).

Pruebas de escenarios extremos, casos límite y condiciones de borde
del modelo ontológico y la DB.
"""

import sqlite3

import pytest
from pipeline.core.db import (
    validar_relacion, fusionar_nodos, cargar_grados, relacion_ya_existe,
    eliminar_nodo_cascada, COMPATIBILIDAD_RELACIONES,
)


# ── Fixture ─────────────────────────────────────────────────────────

@pytest.fixture
def db():
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


# ── Escenario 1: Autor con múltiples corrientes simultáneas ─────────

class TestAutorMultiplesCorrientes:
    """Un autor puede pertenecer a varias corrientes/escuelas a la vez."""

    def test_autor_en_dos_corrientes(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Autor", "autor"))
        autor = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Corriente A", "corriente"))
        c1 = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Corriente B", "corriente"))
        c2 = cur.lastrowid

        for c in [c1, c2]:
            ok, err = validar_relacion(db, autor, c, "pertenece_a", "f", "c")
            assert ok
            db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                       "VALUES (?, ?, ?, ?, ?)", (autor, c, "pertenece_a", "f", "c"))
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 2

        grados = cargar_grados(db)
        assert grados.get(autor) == 2


# ── Escenario 2: Concepto redefinido múltiples veces ────────────────

class TestRedefinicionMultiple:
    """Un concepto puede ser redefinido por varios autores/obras."""

    def test_cinco_redefiniciones(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Cultura", "concepto"))
        concepto = cur.lastrowid
        for i in range(5):
            cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                             (f"Autor {i}", "autor"))
            auth = cur.lastrowid
            ok, err = validar_relacion(db, auth, concepto, "redefine_a", "f", "c")
            assert ok
            db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                       "VALUES (?, ?, ?, ?, ?)", (auth, concepto, "redefine_a", "f", "c"))
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 5


# ── Escenario 3: Obra colectiva con múltiples autores ───────────────

class TestObraColectiva:
    """Una obra puede tener múltiples autores (autor_de desde varios)."""

    def test_diez_autores_misma_obra(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Obra Colectiva", "obra"))
        obra = cur.lastrowid
        for i in range(10):
            cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                             (f"Autor {i}", "autor"))
            auth = cur.lastrowid
            db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                       "VALUES (?, ?, ?, ?, ?)", (auth, obra, "autor_de", "f", "c"))
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 10
        grados = cargar_grados(db)
        assert grados.get(obra) == 10


# ── Escenario 4: Relaciones circulares ─────────────────────────────

class TestRelacionesCirculares:
    """A→B→C→A debe ser permitido (no es un árbol, es un grafo)."""

    def test_ciclo_tres_nodos(self, db):
        ids = []
        for name, typ in [("A", "autor"), ("B", "obra"), ("C", "concepto")]:
            cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)", (name, typ))
            ids.append(cur.lastrowid)
        a, b, c = ids

        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                   "VALUES (?, ?, ?, ?, ?)", (a, b, "autor_de", "f", "c"))
        ok, err = validar_relacion(db, b, c, "desarrolla_concepto", "f", "c")
        assert ok
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                   "VALUES (?, ?, ?, ?, ?)", (b, c, "desarrolla_concepto", "f", "c"))
        ok, err = validar_relacion(db, c, a, "influenciado_por", "f", "c")
        assert ok
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                   "VALUES (?, ?, ?, ?, ?)", (c, a, "influenciado_por", "f", "c"))
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 3


# ── Escenario 5: Concepto con alta cardinalidad ────────────────────

class TestConceptoAltamenteConectado:
    """Un concepto puede tener muchas relaciones entrantes."""

    def test_concepto_con_100_relaciones(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Concepto Central", "concepto"))
        centro = cur.lastrowid
        for i in range(100):
            cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                             (f"Obra {i}", "obra"))
            oid = cur.lastrowid
            db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                       "VALUES (?, ?, ?, ?, ?)",
                       (oid, centro, "desarrolla_concepto", "f", "c"))
        db.commit()
        grados = cargar_grados(db)
        assert grados.get(centro) == 100


# ── Escenario 6: Nombres homónimos con distinto tipo ───────────────

class TestHomonimos:
    """Mismo nombre, distinto tipo, deben ser nodos separados."""

    def test_mismo_nombre_distinto_tipo(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Evolución", "concepto"))
        c1 = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Evolución", "obra"))
        c2 = cur.lastrowid
        assert c1 != c2
        # Deben poder relacionarse entre sí
        ok, err = validar_relacion(db, c2, c1, "desarrolla_concepto", "f", "c")
        assert ok


# ── Escenario 7: Debate con múltiples participantes ────────────────

class TestDebateMultiParticipante:
    """Un debate puede tener muchos participantes de distintos tipos."""

    def test_debate_10_participantes(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Gran Debate", "debate"))
        debate = cur.lastrowid
        participantes = []
        for i in range(5):
            cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                             (f"Autor {i}", "autor"))
            participantes.append(("autor", cur.lastrowid))
        for i in range(3):
            cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                             (f"Obra {i}", "obra"))
            participantes.append(("obra", cur.lastrowid))
        for i in range(2):
            cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                             (f"Concepto {i}", "concepto"))
            participantes.append(("concepto", cur.lastrowid))

        for typ, nid in participantes:
            db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                       "VALUES (?, ?, ?, ?, ?)",
                       (nid, debate, "parte_del_debate", "f", "c"))
        db.commit()
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 10


# ── Escenario 8: Citas contradictorias ─────────────────────────────

class TestContradiccionesFuentes:
    """Fuentes distintas pueden decir cosas distintas sobre el mismo par."""

    def test_dos_relaciones_mismo_par_distinto_tipo(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Boas", "autor"))
        a = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Kroeber", "autor"))
        b = cur.lastrowid

        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                   "VALUES (?, ?, ?, ?, ?)", (a, b, "influenciado_por", "f1", "Boas influenció a Kroeber"))
        db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                   "VALUES (?, ?, ?, ?, ?)", (b, a, "es_mentor_de", "f2", "Kroeber fue mentor"))
        db.commit()

        rels = db.execute("SELECT origen_id, destino_id, tipo FROM relaciones").fetchall()
        assert len(rels) == 2
        assert relacion_ya_existe(db, a, b, "influenciado_por")
        assert relacion_ya_existe(db, b, a, "es_mentor_de")
        assert not relacion_ya_existe(db, a, b, "es_mentor_de")


# ── Escenario 9: Fusión de nodos muy conectados ────────────────────

class TestFusionNodoMuyConectado:
    """Fusionar un nodo con 50 relaciones no debe perder datos."""

    def test_fusion_nodo_con_50_relaciones(self, db):
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Principal", "autor"))
        main = cur.lastrowid
        cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                         ("Duplicado", "autor"))
        dupe = cur.lastrowid

        others = []
        for i in range(50):
            cur = db.execute("INSERT INTO nodos (nombre, tipo) VALUES (?, ?)",
                             (f"Otro {i}", "concepto"))
            oid = cur.lastrowid
            others.append(oid)
            db.execute("INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) "
                       "VALUES (?, ?, ?, ?, ?)", (dupe, oid, "desarrolla_concepto", "f", "c"))

        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 50

        fusionar_nodos(db, main, dupe)

        assert db.execute("SELECT COUNT(*) FROM nodos").fetchone()[0] == 51  # main + 50 others
        assert db.execute("SELECT COUNT(*) FROM relaciones").fetchone()[0] == 50
        assert all(
            r[0] == main
            for r in db.execute("SELECT origen_id FROM relaciones").fetchall()
        )
