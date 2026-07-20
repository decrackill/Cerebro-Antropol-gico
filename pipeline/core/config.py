"""Configuración centralizada del pipeline.

Todas las constantes, paths, umbrales y patrones en un solo lugar.
"""
import logging
import re
from pathlib import Path

# ── Logging ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("cerebro")

# ── Paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent
BASE_DIR = PROJECT_ROOT / "pipeline"
DATA_DIR = PROJECT_ROOT / "data"
LIBROS_DIR = PROJECT_ROOT / "libros"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
LOGS_DIR = RUNTIME_DIR / "logs"
STATE_DIR = RUNTIME_DIR / "state"
CACHE_DIR = RUNTIME_DIR / "cache"

DB_PATH = DATA_DIR / "grafo.db"
ENV_PATH = BASE_DIR / ".env"
CANDIDATOS_PATH = CACHE_DIR / "candidatos_pendientes.json"
REVISION_ESTADO_PATH = STATE_DIR / "revision_estado.json"
LIMPIEZA_ESTADO_PATH = STATE_DIR / "limpieza_estado.json"
RECUPERACION_ESTADO_PATH = STATE_DIR / "recuperacion_estado.json"
REVISION_TOTAL_ESTADO_PATH = STATE_DIR / "revision_total_estado.json"
REVISION_TOTAL_LOG_PATH = LOGS_DIR / "revision_total_log.csv"

# ── Tipos válidos ─────────────────────────────────────────────────────
TIPOS_VALIDOS_NODO = {
    "autor", "obra", "concepto", "escuela",
    "cultura", "debate", "poblacion", "corriente",
}

TIPOS_VALIDOS_RELACION = {
    "influenciado_por", "critica_a", "desarrolla_concepto", "pertenece_a",
    "estudia_a", "contemporaneo_de", "precursor_de", "parte_del_debate",
    "redefine_a",
}

# ── Aliases de tipos de relación ───────────────────────────────────────
TIPOS_ALIAS_RELACION = {
    "influyó_en": "influenciado_por",
    "influye_en": "influenciado_por",
    "influencio_a": "influenciado_por",
    "autor_de": "pertenece_a",
    "es_autor_de": "pertenece_a",
    "estudio": "estudia_a",
    "escribe_estudio_preliminar_para": "estudia_a",
    "describe_a": "estudia_a",
    "ejemplifica_con": "desarrolla_concepto",
    "ejemplo_de": "desarrolla_concepto",
    "ejemplo_en": "desarrolla_concepto",
    "ejemplificado_por": "desarrolla_concepto",
    "practica_concepto": "desarrolla_concepto",
    "promueve_concepto": "desarrolla_concepto",
    "incorpora_concepto": "desarrolla_concepto",
    "discute_concepto": "desarrolla_concepto",
    "estudia_concepto": "desarrolla_concepto",
    "sostiene_teoria": "desarrolla_concepto",
    "defiende": "desarrolla_concepto",
    "defiende_superioridad_de": "critica_a",
    "refuta": "critica_a",
    "lucha_contra": "critica_a",
    "opuesto_a": "critica_a",
    "contrasta_con": "critica_a",
    "malinterpreta_a": "critica_a",
    "limita": "critica_a",
    "limita_expansion_a": "critica_a",
    "subestima_concepto": "critica_a",
    "manipula_concepto": "critica_a",
    "colabora_con": "contemporaneo_de",
    "colaboro_con": "contemporaneo_de",
    "es_mentor_de": "precursor_de",
    "mentor_de": "precursor_de",
    "es_discípulo_de": "influenciado_por",
    "clasifica_como_activo": "desarrolla_concepto",
    "clasifica_como_pasivo": "desarrolla_concepto",
    "presenta_rasgo": "desarrolla_concepto",
    "representado_por": "desarrolla_concepto",
    "relacionado_con": "contemporaneo_de",
    "contribuye_a": "desarrolla_concepto",
    "trata_de": "desarrolla_concepto",
    "es_fuente_sobre": "estudia_a",
    "cita_a": "estudia_a",
    "localizado_en": "pertenece_a",
    "ubica_en": "pertenece_a",
    "incluye_a": "pertenece_a",
    "realiza_trabajo_de_campo_en": "estudia_a",
    "migra_a": "pertenece_a",
    "prologa_obra": "pertenece_a",
    "otorga_primacia_a": "desarrolla_concepto",
    "venera_concepto": "desarrolla_concepto",
    "usa_enfoque": "desarrolla_concepto",
    "traduce_obra": "pertenece_a",
    "publicado_como_traduccion": "pertenece_a",
    "publica": "pertenece_a",
    "origen_de": "precursor_de",
    "facilito_por": "influenciado_por",
    "expandida_en": "pertenece_a",
    "evalua_contribucion_de": "estudia_a",
    "dirige_publicacion": "pertenece_a",
    "difundido_en": "pertenece_a",
    "descubierta_por": "desarrolla_concepto",
    "dedica_obra_a": "pertenece_a",
    "considera_indispensable": "desarrolla_concepto",
    "condiciona": "influenciado_por",
    "atribuye_origen_a": "precursor_de",
    "aplicado_a": "desarrolla_concepto",
    "es_respuesta_a": "critica_a",
    "es_tipo_de": "pertenece_a",
}

# ── Umbrales ──────────────────────────────────────────────────────────
UMBRAL_SIMILITUD = 0.80
UMBRAL_FUZZY = 0.80
UMBRAL_LIMPIEZA_AUTO = 0.50
CUTOFF_FUZZY_REVISION = 0.75

# ── Patrones de detección ────────────────────────────────────────────
PATRONES_RUIDO = re.compile(
    r"(cr[aá]neo|cef[aá]lic|torus|osteo|esquelet|patolog[ií]a|anatom[ií]a|"
    r"medici[oó]n corporal|antropometr[ií]a|índice cef[aá]lico|"
    r"malformaci[oó]n|enfermedad|hueso|dentici[oó]n|estatura promedio|"
    r"pigmentaci[oó]n|coeficiente craneal|prognatismo|distribuci[oó]n de variables)",
    re.IGNORECASE,
)

PATRON_AUTOR_SUPERFICIAL = re.compile(
    r"(autor (mencionad|citad)o (como|en relaci)|citad[oa] en relaci[oó]n con la frecuencia)",
    re.IGNORECASE,
)

# ── Exclusiones de fusión ────────────────────────────────────────────
EXCLUSIONES_FUSION_NOMBRES_NOMBRES = {
    frozenset({"América", "Norteamérica"}),
    frozenset({"América", "América Central"}),
    frozenset({"Australianos", "Aborígenes australianos"}),
    frozenset({"Japoneses", "Japoneses de Hawái"}),
}

# ── Criterios por tipo de nodo ────────────────────────────────────────
CRITERIOS_POR_TIPO = {
    "autor": "Si la única razón de existir es una mención de una línea sin relación real, no debería seguir como nodo propio.",
    "obra": "Confirmá que sea un título real y no una variante mal cortada de otro ya existente.",
    "concepto": "Debe poder nombrarse en 1-4 palabras sin parafrasear el texto. Si no, no es concepto.",
    "escuela": "Requiere institución/sede/miembros identificables. Si no los tiene, probablemente sea 'corriente'.",
    "corriente": "Tendencia de pensamiento sin organización formal. Es la opción segura cuando dudás entre escuela y corriente.",
    "cultura": "El foco debe ser prácticas/creencias/organización social, no origen o demografía.",
    "poblacion": "El foco debe ser origen/demografía/ubicación, no un sistema cultural. Nunca se fusiona con un nodo cultura.",
    "debate": "Debe representar una discusión/tensión entre posiciones, no un concepto aislado.",
}
