"""Utilidades compartidas del pipeline.

Funciones de texto, UI y detección de duplicados.
"""
import re
from difflib import SequenceMatcher

from .config import (
    UMBRAL_SIMILITUD,
    EXCLUSIONES_FUSION_NOMBRES_NOMBRES,
    TIPOS_VALIDOS_RELACION,
    TIPOS_ALIAS_RELACION,
)


def similitud(a: str, b: str) -> float:
    """Similitud de texto entre 0 y 1 (SequenceMatcher), usada para detectar duplicados."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def normalizar(nombre: str) -> str:
    """Quita acentos-safe, puntuación y mayúsculas para comparar nombres de forma laxa."""
    return re.sub(r"[^\wáéíóúñ ]", "", nombre.lower()).strip()


def normalizar_tipo_relacion(tipo: str) -> str:
    """Normaliza un tipo de relación: minúsculas, sin espacios extra,
    resuelto contra TIPOS_ALIAS_RELACION."""
    t = tipo.strip().lower().replace(" ", "_")
    if t in TIPOS_VALIDOS_RELACION:
        return t
    if t in TIPOS_ALIAS_RELACION:
        return TIPOS_ALIAS_RELACION[t]
    return t


def pedir_opcion(mensaje: str, validas: set, alias: dict = None) -> str:
    """Pide una respuesta hasta que sea válida; nunca deja pasar algo ambiguo sin avisar."""
    alias = alias or {}
    while True:
        resp = input(mensaje).strip().lower()
        if resp in alias:
            resp = alias[resp]
        if resp in validas:
            return resp
        print(f"  ⚠ No entendí '{resp}'. Opciones: {', '.join(sorted(validas))}")


def es_exclusion_fusion(nombre_a: str, nombre_b: str) -> bool:
    """True si el par de nombres está en la lista de exclusión de fusión."""
    return frozenset({nombre_a, nombre_b}) in EXCLUSIONES_FUSION_NOMBRES_NOMBRES


def barra_progreso(hechos: int, total: int, ancho: int = 30) -> str:
    """Genera una barra de progreso visual."""
    if total == 0:
        return "[sin candidatos]"
    prop = hechos / total
    llenos = int(ancho * prop)
    return f"[{'█' * llenos}{'░' * (ancho - llenos)}] {hechos}/{total} ({prop*100:.0f}%)"


def clave_relacion(r: dict) -> str:
    """Crea una clave única string para un registro de relación."""
    return f"{r['origen']}->{r['destino']}::{r['tipo']}::{r.get('cita_textual', '')[:60]}"


def detectar_duplicados(por_tipo: dict, umbral: float = None) -> list[tuple]:
    """
    Detecta pares de nodos similares dentro de cada tipo.
    Devuelve lista de (id_a, nombre_a, id_b, nombre_b, tipo, score).
    """
    if umbral is None:
        umbral = UMBRAL_SIMILITUD
    duplicados = []
    for tipo, items in por_tipo.items():
        for i, (id_a, nombre_a) in enumerate(items):
            for id_b, nombre_b in items[i + 1:]:
                if es_exclusion_fusion(nombre_a, nombre_b):
                    continue
                score = similitud(nombre_a, nombre_b)
                if score >= umbral:
                    duplicados.append((id_a, nombre_a, id_b, nombre_b, tipo, score))
    return duplicados


def es_nodo_ruido(nombre: str, descripcion: str, grados: int) -> bool:
    """Detecta si un nodo es ruido biomédico o de baja calidad."""
    from .config import PATRONES_RUIDO
    return bool(PATRONES_RUIDO.search(nombre) or PATRONES_RUIDO.search(descripcion or ""))


def es_nodo_ruido_aislado(nombre: str, descripcion: str, grados: int) -> bool:
    """Detecta nodos ruido que además están aislados o con descripción corta."""
    return es_nodo_ruido(nombre, descripcion, grados) or (grados <= 1 and len(descripcion or "") < 60)
