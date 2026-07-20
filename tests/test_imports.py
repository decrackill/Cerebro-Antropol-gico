"""Tests de imports de todos los módulos principales."""


def test_import_config():
    from pipeline.core import config
    assert hasattr(config, 'PROJECT_ROOT')
    assert hasattr(config, 'DB_PATH')


def test_import_db():
    from pipeline.core import db
    assert hasattr(db, 'conectar_db')
    assert hasattr(db, 'fusionar_nodos')


def test_import_utils():
    from pipeline.core import utils
    assert hasattr(utils, 'similitud')
    assert hasattr(utils, 'normalizar_tipo_relacion')


def test_import_extractor():
    from pipeline.extract import extractor
    assert hasattr(extractor, 'dividir_en_chunks')


def test_import_prompts():
    from pipeline.extract import prompts
    assert hasattr(prompts, 'build_prompt_extraccion_grafo')


def test_import_modo_manual():
    from pipeline.extract import modo_manual
    assert hasattr(modo_manual, 'generar')


def test_import_revision():
    from pipeline.review import revision
    assert hasattr(revision, 'herramienta_revisar')


def test_import_limpieza():
    from pipeline.review import limpieza
    assert hasattr(limpieza, 'herramienta_limpieza_automatica')


def test_import_auditoria():
    from pipeline.review import auditoria
    assert hasattr(auditoria, 'herramienta_auditoria')


def test_import_menu():
    from pipeline.cli import menu
    assert hasattr(menu, 'main')
    assert hasattr(menu, 'EXTRAE')
    assert hasattr(menu, 'OPCIONES')
