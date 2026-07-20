"""Tests del extractor."""


def test_build_prompt():
    from pipeline.extract.prompts import build_prompt_extraccion_grafo
    nodos_existentes = [{"id": 1, "tipo": "autor", "nombre": "Test"}]
    prompt = build_prompt_extraccion_grafo(nodos_existentes)
    assert isinstance(prompt, str)
    assert len(prompt) > 100


def test_dividir_en_chunks():
    from pipeline.extract.extractor import dividir_en_chunks
    paginas = [(1, "Texto de prueba página 1. " * 100)]
    chunks = dividir_en_chunks(paginas)
    assert isinstance(chunks, list)
    assert len(chunks) >= 1


def test_normalizar_tipos():
    from pipeline.extract.extractor import normalizar_tipos
    resultado = {"nodos_nuevos": [{"tipo": "libro", "nombre": "Test"}]}
    resultado = normalizar_tipos(resultado)
    assert resultado["nodos_nuevos"][0]["tipo"] == "obra"
