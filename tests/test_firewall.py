"""Tests del sistema de validación ontológica (validar_relacion).

Cubre:
- Las 12 relaciones canónicas
- Compatibilidad origen/destino
- Firewall epistemológico (poblacion)
- No reflexividad
- Evidencia documental obligatoria
- Tipos de relación inválidos
"""
import sqlite3
import tempfile
from pathlib import Path

import pytest

from pipeline.core.db import validar_relacion, COMPATIBILIDAD_RELACIONES
from pipeline.core.config import TIPOS_VALIDOS_RELACION


# ── Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def db_validacion():
    """DB temporal con nodos de todos los tipos para tests de validación."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE nodos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            metadatos TEXT DEFAULT '{}'
        );
        CREATE TABLE relaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origen_id INTEGER NOT NULL,
            destino_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            peso REAL DEFAULT 1.0,
            fuente TEXT,
            cita_textual TEXT,
            FOREIGN KEY (origen_id) REFERENCES nodos(id),
            FOREIGN KEY (destino_id) REFERENCES nodos(id)
        );
    """)

    # Nodos de prueba: 2 de cada tipo para testear relaciones entre pares
    nodos_data = [
        ("autor", "Autor A"), ("autor", "Autor B"),
        ("obra", "Obra A"), ("obra", "Obra B"),
        ("concepto", "Concepto A"), ("concepto", "Concepto B"),
        ("escuela", "Escuela A"), ("escuela", "Escuela B"),
        ("corriente", "Corriente A"), ("corriente", "Corriente B"),
        ("cultura", "Cultura A"), ("cultura", "Cultura B"),
        ("poblacion", "Poblacion A"), ("poblacion", "Poblacion B"),
        ("debate", "Debate A"), ("debate", "Debate B"),
    ]
    for tipo, nombre in nodos_data:
        conn.execute("INSERT INTO nodos (tipo, nombre) VALUES (?, ?)", (tipo, nombre))
    conn.commit()

    yield conn

    conn.close()
    db_path.unlink(missing_ok=True)


@pytest.fixture
def nodos(db_validacion):
    """Dict con IDs de nodos de prueba. Cada tipo tiene A y B."""
    rows = db_validacion.execute("SELECT tipo, nombre, id FROM nodos ORDER BY id").fetchall()
    result = {}
    for tipo, nombre, id_ in rows:
        suffix = "A" if nombre.endswith("A") else "B"
        result[f"{tipo}_{suffix}"] = id_
    for tipo in ["autor", "obra", "concepto", "escuela", "corriente", "cultura", "poblacion", "debate"]:
        result[tipo] = result[f"{tipo}_A"]
    return result


# ── 1. Tipos de relación canónicos ─────────────────────────────────────

class TestTiposRelacion:
    """Verifica que las 12 relaciones canónicas existen y son válidas."""

    def test_12_tipos_canonicos(self):
        assert len(TIPOS_VALIDOS_RELACION) == 12

    def las_12_estan_definidas(self):
        esperadas = {
            "autor_de", "influenciado_por", "critica_a", "desarrolla_concepto",
            "redefine_a", "precursor_de", "pertenece_a", "estudia_a",
            "contemporaneo_de", "parte_del_debate", "es_mentor_de", "colabora_con",
        }
        assert TIPOS_VALIDOS_RELACION == esperadas

    def test_compatibilidad_definida_para_12(self):
        assert len(COMPATIBILIDAD_RELACIONES) == 12

    def test_tipo_invalido_rechazado(self, db_validacion, nodos):
        ok, err = validar_relacion(db_validacion, nodos["autor"], nodos["obra"],
                                   "tipo_inexistente", "fuente", "cita")
        assert not ok
        assert "no es canónico" in err

    def test_tipo_vacio_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["obra"],
                                 "", "fuente", "cita")
        assert not ok


# ── 2. No reflexividad ─────────────────────────────────────────────────

class TestNoReflexividad:
    """Un nodo no puede conectarse a sí mismo."""

    def test_autor_se_conecta_a_si_mismo(self, db_validacion, nodos):
        ok, err = validar_relacion(db_validacion, nodos["autor_A"], nodos["autor_A"],
                                   "autor_de", "fuente", "cita")
        assert not ok
        assert "no puede conectarse a sí mismo" in err

    def test_concepto_se_conecta_a_si_mismo(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["concepto_A"], nodos["concepto_A"],
                                 "redefine_a", "fuente", "cita")
        assert not ok

    def test_nodos_diferentes_si_permitidos(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor_A"], nodos["obra_A"],
                                 "autor_de", "fuente", "cita")
        assert ok


# ── 3. Firewall epistemológico ──────────────────────────────────────────

class TestFirewallPoblacion:
    """Reglas del Manifiesto §5.3 sobre poblacion."""

    def test_poblacion_origen_estudia_a_rechazado(self, db_validacion, nodos):
        """poblacion como origen con estudia_a: PROHIBIDO"""
        ok, err = validar_relacion(db_validacion, nodos["poblacion"], nodos["cultura"],
                                   "estudia_a", "fuente", "cita")
        assert not ok
        assert "firewall" in err.lower() or "poblacion" in err.lower()

    def test_poblacion_origen_critica_a_rechazado(self, db_validacion, nodos):
        """poblacion como origen con critica_a: PROHIBIDO"""
        ok, _ = validar_relacion(db_validacion, nodos["poblacion"], nodos["autor"],
                                 "critica_a", "fuente", "cita")
        assert not ok

    def test_poblacion_origen_influenciado_por_rechazado(self, db_validacion, nodos):
        """poblacion como origen con influenciado_por: PROHIBIDO"""
        ok, _ = validar_relacion(db_validacion, nodos["poblacion"], nodos["concepto"],
                                 "influenciado_por", "fuente", "cita")
        assert not ok

    def test_poblacion_origen_desarrolla_concepto_rechazado(self, db_validacion, nodos):
        """poblacion como origen con desarrolla_concepto: PROHIBIDO"""
        ok, _ = validar_relacion(db_validacion, nodos["poblacion"], nodos["concepto"],
                                 "desarrolla_concepto", "fuente", "cita")
        assert not ok

    def test_poblacion_origen_pertenece_a_rechazado(self, db_validacion, nodos):
        """poblacion como origen con pertenece_a: PROHIBIDO"""
        ok, _ = validar_relacion(db_validacion, nodos["poblacion"], nodos["corriente"],
                                 "pertenece_a", "fuente", "cita")
        assert not ok

    def test_poblacion_origen_parte_del_debate_permitido(self, db_validacion, nodos):
        """poblacion como origen con parte_del_debate: PERMITIDO"""
        ok, _ = validar_relacion(db_validacion, nodos["poblacion"], nodos["debate"],
                                 "parte_del_debate", "fuente", "cita")
        assert ok

    def test_poblacion_destino_estudia_a_permitido(self, db_validacion, nodos):
        """poblacion como destino con estudia_a: PERMITIDO"""
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["poblacion"],
                                 "estudia_a", "libro.pdf", "cita")
        assert ok

    def test_poblacion_destino_critica_a_rechazado(self, db_validacion, nodos):
        """poblacion como destino con critica_a: PROHIBIDO"""
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["poblacion"],
                                 "critica_a", "fuente", "cita")
        assert not ok

    def test_poblacion_destino_influenciado_por_rechazado(self, db_validacion, nodos):
        """poblacion como destino con influenciado_por: PROHIBIDO"""
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["poblacion"],
                                 "influenciado_por", "fuente", "cita")
        assert not ok

    def test_poblacion_destino_pertenece_a_rechazado(self, db_validacion, nodos):
        """poblacion como destino con pertenece_a: PROHIBIDO"""
        ok, _ = validar_relacion(db_validacion, nodos["concepto"], nodos["poblacion"],
                                 "pertenece_a", "fuente", "cita")
        assert not ok

    def test_poblacion_destino_desarrolla_concepto_rechazado(self, db_validacion, nodos):
        """poblacion como destino con desarrolla_concepto: PROHIBIDO"""
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["poblacion"],
                                 "desarrolla_concepto", "fuente", "cita")
        assert not ok


# ── 4. Compatibilidad origen/destino ───────────────────────────────────

class TestCompatibilidadOrigenDestino:
    """Cada tipo de relación solo acepta ciertos tipos de nodo como origen/destino."""

    def test_autor_de_origen_autor_destino_obra(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["obra"],
                                 "autor_de", "fuente", "cita")
        assert ok

    def test_autor_de_origen_obra_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["obra"], nodos["obra"],
                                 "autor_de", "fuente", "cita")
        assert not ok

    def test_autor_de_destino_concepto_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["concepto"],
                                 "autor_de", "fuente", "cita")
        assert not ok

    def test_desarrolla_concepto_origen_autor_destino_concepto(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["concepto"],
                                 "desarrolla_concepto", "fuente", "cita")
        assert ok

    def test_desarrolla_concepto_destino_obra_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["obra"],
                                 "desarrolla_concepto", "fuente", "cita")
        assert not ok

    def test_pertenece_a_origen_autor_destino_escuela(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["escuela"],
                                 "pertenece_a", "fuente", "cita")
        assert ok

    def test_pertenece_a_origen_debate_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["debate"], nodos["corriente"],
                                 "pertenece_a", "fuente", "cita")
        assert not ok

    def test_estudia_a_origen_autor_destino_cultura(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["cultura"],
                                 "estudia_a", "libro.pdf", "cita")
        assert ok

    def test_estudia_a_origen_concepto_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["concepto"], nodos["cultura"],
                                 "estudia_a", "fuente", "cita")
        assert not ok

    def test_estudia_a_destino_debate_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["debate"],
                                 "estudia_a", "fuente", "cita")
        assert not ok

    def test_contemporaneo_de_ambos_autores(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor_A"], nodos["autor_B"],
                                 "contemporaneo_de", "fuente", "cita")
        assert ok

    def test_contemporaneo_de_origen_obra_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["obra"], nodos["autor"],
                                 "contemporaneo_de", "fuente", "cita")
        assert not ok

    def test_parte_del_debate_origen_poblacion_destino_debate(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["poblacion"], nodos["debate"],
                                 "parte_del_debate", "fuente", "cita")
        assert ok

    def test_parte_del_debate_destino_concepto_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["concepto"],
                                 "parte_del_debate", "fuente", "cita")
        assert not ok

    def test_es_mentor_de_ambos_autores(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor_A"], nodos["autor_B"],
                                 "es_mentor_de", "fuente", "cita")
        assert ok

    def test_es_mentor_de_origen_obra_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["obra"], nodos["autor"],
                                 "es_mentor_de", "fuente", "cita")
        assert not ok

    def test_colabora_con_ambos_autores(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor_A"], nodos["autor_B"],
                                 "colabora_con", "fuente", "cita")
        assert ok

    def test_colabora_con_origen_concepto_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["concepto"], nodos["autor"],
                                 "colabora_con", "fuente", "cita")
        assert not ok

    def test_redefine_a_origen_concepto_destino_concepto(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["concepto_A"], nodos["concepto_B"],
                                 "redefine_a", "fuente", "cita")
        assert ok

    def test_redefine_a_destino_obra_rechazado(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["obra"],
                                 "redefine_a", "fuente", "cita")
        assert not ok

    def test_precursor_de_origen_autor_destino_autor(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor_A"], nodos["autor_B"],
                                 "precursor_de", "fuente", "cita")
        assert ok

    def test_influenciado_por_origen_concepto_destino_concepto(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["concepto_A"], nodos["concepto_B"],
                                 "influenciado_por", "fuente", "cita")
        assert ok


# ── 5. Evidencia documental obligatoria ────────────────────────────────

class TestEvidenciaDocumental:
    """Manifiesto §6.2: toda relación DEBE registrar fuente y/o cita_textual."""

    def test_sin_fuente_ni_cita_rechazado(self, db_validacion, nodos):
        ok, err = validar_relacion(db_validacion, nodos["autor"], nodos["obra"],
                                   "autor_de", None, None)
        assert not ok
        assert "evidencia" in err.lower()

    def test_con_fuente_sin_cita_permitido(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["obra"],
                                 "autor_de", "libro.pdf", None)
        assert ok

    def test_con_cita_sin_fuente_permitido(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["obra"],
                                 "autor_de", None, "cita textual")
        assert ok

    def test_con_fuente_y_cita_permitido(self, db_validacion, nodos):
        ok, _ = validar_relacion(db_validacion, nodos["autor"], nodos["obra"],
                                 "autor_de", "libro.pdf", "cita textual")
        assert ok


# ── 6. Las 12 relaciones canónicas funcionan ────────────────────────────

class TestLas12Relaciones:
    """Cada una de las 12 relaciones canónicas debe ser válida con nodos correctos."""

    @pytest.mark.parametrize("tipo,origen_tipo,destino_tipo", [
        ("autor_de", "autor_A", "obra_A"),
        ("influenciado_por", "autor_A", "autor_B"),
        ("critica_a", "autor_A", "autor_B"),
        ("desarrolla_concepto", "autor_A", "concepto_A"),
        ("redefine_a", "concepto_A", "concepto_B"),
        ("precursor_de", "autor_A", "autor_B"),
        ("pertenece_a", "autor_A", "escuela_A"),
        ("estudia_a", "autor_A", "cultura_A"),
        ("contemporaneo_de", "autor_A", "autor_B"),
        ("parte_del_debate", "autor_A", "debate_A"),
        ("es_mentor_de", "autor_A", "autor_B"),
        ("colabora_con", "autor_A", "autor_B"),
    ])
    def test_relacion_canonica_valida(self, db_validacion, nodos, tipo, origen_tipo, destino_tipo):
        ok, err = validar_relacion(db_validacion, nodos[origen_tipo], nodos[destino_tipo],
                                   tipo, "fuente", "cita")
        assert ok, f"{tipo} debería ser válida: {err}"
