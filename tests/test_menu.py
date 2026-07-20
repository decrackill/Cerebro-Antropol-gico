"""Tests del menú principal."""


def test_extrac_dict():
    from pipeline.cli.menu import EXTRAE
    assert len(EXTRAE) == 3
    assert "e1" in EXTRAE
    assert "e2" in EXTRAE
    assert "e3" in EXTRAE


def test_opciones_dict():
    from pipeline.cli.menu import OPCIONES
    assert len(OPCIONES) == 16
    assert "0" in OPCIONES
    assert "1" in OPCIONES
    assert "15" in OPCIONES


def test_mostrar_flujo():
    from pipeline.cli.menu import mostrar_flujo
    # No debe lanzar excepción
    mostrar_flujo()


def test_mostrar_ayuda():
    from pipeline.cli.menu import mostrar_ayuda
    # No debe lanzar excepción para opciones válidas
    mostrar_ayuda("1")
    mostrar_ayuda("e1")
    mostrar_ayuda("999")  # Opción inexistente
