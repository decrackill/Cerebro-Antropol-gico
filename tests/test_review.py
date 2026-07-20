"""Tests del sistema de revisión."""


def test_normalizar_tipo_relacion():
    from pipeline.core.utils import normalizar_tipo_relacion
    # Tipo directo
    assert normalizar_tipo_relacion("influenciado_por") == "influenciado_por"
    # Alias
    assert normalizar_tipo_relacion("autor_de") == "pertenece_a"
    assert normalizar_tipo_relacion("influyó_en") == "influenciado_por"
    # Minúsculas y espacios
    assert normalizar_tipo_relacion("  CRITICA_A  ") == "critica_a"


def test_similitud():
    from pipeline.core.utils import similitud
    # Textos idénticos
    assert similitud("hola", "hola") == 1.0
    # Textos diferentes
    assert similitud("hola", "adiós") < 0.5
    # Case insensitive
    assert similitud("Hola", "hola") == 1.0


def test_detectar_duplicados():
    from pipeline.core.utils import detectar_duplicados
    por_tipo = {
        "autor": [
            (1, "Juan Pérez"),
            (2, "Juan Perez"),
            (3, "María García"),
        ]
    }
    duplicados = detectar_duplicados(por_tipo, umbral=0.80)
    assert len(duplicados) >= 1
    # Juan Pérez y Juan Perez deberían ser detectados
    nombres = [(d[1], d[3]) for d in duplicados]
    assert any("Juan" in n[0] and "Juan" in n[1] for n in nombres)


def test_es_exclusion_fusion():
    from pipeline.core.utils import es_exclusion_fusion
    assert es_exclusion_fusion("América", "Norteamérica") == True
    assert es_exclusion_fusion("Autor A", "Autor B") == False


def test_barra_progreso():
    from pipeline.core.utils import barra_progreso
    resultado = barra_progreso(5, 10)
    assert "[" in resultado
    assert "5/10" in resultado
    assert "50%" in resultado


def test_clave_relacion():
    from pipeline.core.utils import clave_relacion
    r = {"origen": "a", "destino": "b", "tipo": "estudia_a", "cita_textual": "cita"}
    clave = clave_relacion(r)
    assert "a->b" in clave
    assert "estudia_a" in clave
