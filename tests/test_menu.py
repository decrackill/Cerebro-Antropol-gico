"""Tests del menú principal."""


def test_extrac_dict():
    from pipeline.cli.menu import EXTRAE
    assert len(EXTRAE) == 3
    assert "e1" in EXTRAE
    assert "e2" in EXTRAE
    assert "e3" in EXTRAE


def test_opciones_dict():
    from pipeline.cli.menu import OPCIONES_DICT, SECCIONES
    # Verificar que todas las claves están en el dict
    todas_secciones = [c for s in SECCIONES for c, _, _, _ in s[1]]
    assert len(OPCIONES_DICT) == len(todas_secciones)
    assert "1" in OPCIONES_DICT
    assert "15" in OPCIONES_DICT
    assert "16" in OPCIONES_DICT


def test_secciones_cubren_todo():
    """Todas las claves de OPCIONES_DICT aparecen en alguna sección."""
    from pipeline.cli.menu import OPCIONES_DICT, SECCIONES
    todas = set()
    for _seccion, items in SECCIONES:
        for clave, _, _, _ in items:
            todas.add(clave)
    assert todas == set(OPCIONES_DICT.keys())


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
