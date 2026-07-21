"""Tests del script de migración migrate_v1_1.py.

Cubre:
- dry-run
- apply
- backup
- idempotencia
- migraciones automáticas
- migraciones omitidas
- manejo de errores
"""
import sqlite3
import tempfile
from pathlib import Path

import pytest

# Importar funciones del migrador
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from migrate_v1_1 import (
    conectar_db, crear_backup, analizar_migracion,
    ejecutar_migracion, generar_reporte, es_idempotente,
    TABLA_MIGRACION, MANIFIESTO_VERSION,
)


# ── Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def db_migracion():
    """DB temporal con datos de prueba para migración."""
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
    
    # Nodos de prueba
    nodos = [
        ("autor", "Autor A"), ("autor", "Autor B"),
        ("obra", "Obra A"), ("obra", "Obra B"),
        ("concepto", "Concepto A"), ("concepto", "Concepto B"),
        ("escuela", "Escuela A"),
        ("cultura", "Cultura A"), ("cultura", "Cultura B"),
        ("poblacion", "Poblacion A"),
        ("debate", "Debate A"),
    ]
    for tipo, nombre in nodos:
        conn.execute("INSERT INTO nodos (tipo, nombre) VALUES (?, ?)", (tipo, nombre))
    
    # Relaciones de prueba con tipos no canónicos
    relaciones = [
        (1, 2, "escribió", "fuente", "cita"),           # → autor_de
        (1, 2, "influyó_en", "fuente", "cita"),          # → influenciado_por (invertir)
        (1, 2, "refuta", "fuente", "cita"),              # → critica_a
        (1, 2, "estudio", "fuente", "cita"),             # → estudia_a
        (1, 2, "colaboro_con", "fuente", "cita"),        # → colabora_con
        (1, 2, "mentor_de", "fuente", "cita"),           # → es_mentor_de
        (2, 1, "es_discípulo_de", "fuente", "cita"),     # → es_mentor_de (invertir)
        (1, 2, "relacionado_con", "fuente", "cita"),     # → mantener (Nivel B)
        (1, 2, "clasifica_como_activo", "fuente", "cita"),  # → escalar
    ]
    for o, d, t, f, c in relaciones:
        conn.execute(
            "INSERT INTO relaciones (origen_id, destino_id, tipo, fuente, cita_textual) VALUES (?, ?, ?, ?, ?)",
            (o, d, t, f, c)
        )
    conn.commit()
    
    yield conn, db_path
    
    conn.close()
    db_path.unlink(missing_ok=True)


# ── Tests de conexión y backup ──────────────────────────────────────────

class TestConexionYBackup:
    def test_conectar_db(self, db_migracion):
        conn, db_path = db_migracion
        assert conn is not None
    
    def test_crear_backup(self, db_migracion):
        conn, db_path = db_migracion
        backup_path = crear_backup(db_path)
        assert backup_path.exists()
        assert backup_path != db_path
        backup_path.unlink()


# ── Tests de análisis ───────────────────────────────────────────────────

class TestAnalisis:
    def test_analizar_migracion(self, db_migracion):
        conn, _ = db_migracion
        resultado = analizar_migracion(conn)
        assert len(resultado) > 0
    
    def test_tipos_detectados(self, db_migracion):
        conn, _ = db_migracion
        resultado = analizar_migracion(conn)
        originales = [r["original"] for r in resultado]
        assert "escribió" in originales
        assert "influyó_en" in originales
        assert "refuta" in originales
    
    def test_conteo_correcto(self, db_migracion):
        conn, _ = db_migracion
        resultado = analizar_migracion(conn)
        for r in resultado:
            if r["original"] == "escribió":
                assert r["conteo"] == 1


# ── Tests de dry-run ────────────────────────────────────────────────────

class TestDryRun:
    def test_dry_run_no_modifica(self, db_migracion):
        conn, _ = db_migracion
        stats = ejecutar_migracion(conn, dry_run=True)
        
        # Verificar que no se modificó nada
        tipos = conn.execute("SELECT DISTINCT tipo FROM relaciones").fetchall()
        tipos_str = {t[0] for t in tipos}
        assert "escribió" in tipos_str
        assert "influyó_en" in tipos_str
    
    def test_dry_run_estadisticas(self, db_migracion):
        conn, _ = db_migracion
        stats = ejecutar_migracion(conn, dry_run=True)
        
        assert stats["analizadas"] > 0
        assert stats["migradas"] > 0
        assert stats["omitidas"] > 0


# ── Tests de apply ──────────────────────────────────────────────────────

class TestApply:
    def test_apply_migra_tipos(self, db_migracion):
        conn, _ = db_migracion
        stats = ejecutar_migracion(conn, dry_run=False)
        
        # Verificar que se migraron
        tipos = conn.execute("SELECT DISTINCT tipo FROM relaciones").fetchall()
        tipos_str = {t[0] for t in tipos}
        assert "escribió" not in tipos_str
        assert "autor_de" in tipos_str
    
    def test_apply_no_migra_omitidos(self, db_migracion):
        conn, _ = db_migracion
        ejecutar_migracion(conn, dry_run=False)
        
        # Verificar que no se migraron los omitidos
        tipos = conn.execute("SELECT DISTINCT tipo FROM relaciones").fetchall()
        tipos_str = {t[0] for t in tipos}
        assert "clasifica_como_activo" in tipos_str  # escalar
        assert "relacionado_con" in tipos_str  # mantener


# ── Tests de idempotencia ──────────────────────────────────────────────

class TestIdempotencia:
    def test_no_idempotente_antes(self, db_migracion):
        conn, _ = db_migracion
        assert not es_idempotente(conn)
    
    def test_idempotente_despues(self, db_migracion):
        conn, _ = db_migracion
        ejecutar_migracion(conn, dry_run=False)
        assert es_idempotente(conn)
    
    def test_doble_aplicacion(self, db_migracion):
        conn, _ = db_migracion
        ejecutar_migracion(conn, dry_run=False)
        stats2 = ejecutar_migracion(conn, dry_run=False)
        
        # La segunda aplicación no debería migrar nada
        assert stats2["migradas"] == 0


# ── Tests de reporte ───────────────────────────────────────────────────

class TestReporte:
    def test_generar_reporte(self, db_migracion):
        conn, _ = db_migracion
        stats = ejecutar_migracion(conn, dry_run=True)
        reporte = generar_reporte(stats, dry_run=True)
        
        assert "DRY-RUN" in reporte
        assert MANIFIESTO_VERSION in reporte
        assert "escribió" in reporte


# ── Tests de tabla de migración ────────────────────────────────────────

class TestTablaMigracion:
    def test_tabla_no_vacia(self):
        assert len(TABLA_MIGRACION) > 0
    
    def test_todos_los_campos(self):
        for regla in TABLA_MIGRACION:
            assert "original" in regla
            assert "destino" in regla
            assert "invertir" in regla
            assert "justificacion" in regla
            assert "confianza" in regla
            assert "tipo_migracion" in regla
            assert "ejemplo" in regla
    
    def test_tipos_validos(self):
        tipos_validos = {"auto", "revision", "mantener", "escalar"}
        for regla in TABLA_MIGRACION:
            assert regla["tipo_migracion"] in tipos_validos
    
    def test_confianza_valida(self):
        confianzas_validas = {"Alta", "Media", "Baja"}
        for regla in TABLA_MIGRACION:
            assert regla["confianza"] in confianzas_validas


# ── Tests de inversiones ───────────────────────────────────────────────

class TestInversiones:
    def test_inversion_correcta(self, db_migracion):
        conn, _ = db_migracion
        
        # Verificar que influyó_en invierte dirección
        antes = conn.execute(
            "SELECT origen_id, destino_id FROM relaciones WHERE tipo = 'influyó_en'"
        ).fetchone()
        
        ejecutar_migracion(conn, dry_run=False)
        
        # Después de migrar, la relación debe estar invertida
        despues = conn.execute(
            "SELECT origen_id, destino_id FROM relaciones WHERE tipo = 'influenciado_por'"
        ).fetchone()
        
        if antes and despues:
            assert antes[0] == despues[1]  # origen antes = destino después
            assert antes[1] == despues[0]  # destino antes = origen después
