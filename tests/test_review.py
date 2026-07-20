"""Tests del sistema de revisión."""


def test_normalizar_tipo_relacion():
    from pipeline.core.utils import normalizar_tipo_relacion
    # Tipo canonical directo
    assert normalizar_tipo_relacion("influenciado_por") == "influenciado_por"
    assert normalizar_tipo_relacion("critica_a") == "critica_a"
    assert normalizar_tipo_relacion("desarrolla_concepto") == "desarrolla_concepto"
    assert normalizar_tipo_relacion("pertenece_a") == "pertenece_a"
    assert normalizar_tipo_relacion("estudia_a") == "estudia_a"
    assert normalizar_tipo_relacion("contemporaneo_de") == "contemporaneo_de"
    assert normalizar_tipo_relacion("precursor_de") == "precursor_de"
    assert normalizar_tipo_relacion("parte_del_debate") == "parte_del_debate"
    assert normalizar_tipo_relacion("redefine_a") == "redefine_a"
    
    # Alias correctos (sinónimos reales)
    assert normalizar_tipo_relacion("influyó_en") == "influenciado_por"
    assert normalizar_tipo_relacion("influye_en") == "influenciado_por"
    assert normalizar_tipo_relacion("refuta") == "critica_a"
    assert normalizar_tipo_relacion("estudio") == "estudia_a"
    assert normalizar_tipo_relacion("localizado_en") == "pertenece_a"
    assert normalizar_tipo_relacion("origen_de") == "precursor_de"
    
    # Tipos que NO deben cambiar (ya no son aliases)
    assert normalizar_tipo_relacion("autor_de") == "autor_de"
    assert normalizar_tipo_relacion("colabora_con") == "colabora_con"
    assert normalizar_tipo_relacion("es_mentor_de") == "es_mentor_de"
    assert normalizar_tipo_relacion("clasifica_como_activo") == "clasifica_como_activo"
    assert normalizar_tipo_relacion("contribuye_a") == "contribuye_a"
    assert normalizar_tipo_relacion("relacionado_con") == "relacionado_con"
    assert normalizar_tipo_relacion("defiende_superioridad_de") == "defiende_superioridad_de"
    assert normalizar_tipo_relacion("limita") == "limita"
    
    # Minúsculas y espacios
    assert normalizar_tipo_relacion("  CRITICA_A  ") == "critica_a"
    assert normalizar_tipo_relacion(" Influyó_En ") == "influenciado_por"


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
