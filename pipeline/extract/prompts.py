def build_prompt_extraccion_grafo(nodos_existentes: list[dict]) -> str:
    catalogo = "\n".join(
        f'  · id="{n["id"]}" | tipo={n["tipo"]} | nombre="{n["nombre"]}"'
        for n in nodos_existentes
    ) or "  (ninguno todavía)"

    return f"""
Eres un asistente de investigación en antropología. Analizas fragmentos de textos
académicos y extraes entidades (autores, obras, conceptos, escuelas, culturas, debates)
y las relaciones entre ellas, para construir un grafo de conocimiento.

NODOS QUE YA EXISTEN EN EL GRAFO (reutiliza su "id" si el texto se refiere a ellos,
NO crees un nodo nuevo para algo que ya existe):
{catalogo}

TAREA:
Lee el texto y extrae:
1. Nuevas entidades que NO estén en la lista de arriba.
2. Relaciones entre entidades (nuevas o existentes), citando el fragmento de texto
   que justifica cada relación.

TIPOS DE NODO válidos: autor, obra, concepto, escuela, cultura, debate, poblacion, corriente
TIPOS DE RELACIÓN válidos: influenciado_por, critica_a, desarrolla_concepto,
  pertenece_a, estudia_a, contemporaneo_de, precursor_de, parte_del_debate, redefine_a

CRITERIO ESTRICTO PARA EL TIPO "concepto" (leer con cuidado, es la fuente #1 de errores):

Un concepto SOLO califica si cumple LAS TRES condiciones simultáneamente:
1. Es un término con nombre propio y estable — no una oración ni una paráfrasis.
2. Existiría como entrada en un glosario de antropología general, independiente de
   este libro y este autor (piensa: "¿aparecería esto en un manual introductorio
   de antropología, o en Wikipedia como concepto propio?").
3. Se puede usar en otro contexto/libro sin perder sentido.

Ejemplos válidos: "reciprocidad", "parentesco", "relativismo cultural",
"observación participante", "holismo", "kula", "estructura social", "tabú", "totemismo".

PISTAS DE QUE NO ES UN CONCEPTO (recházalo si ves cualquiera de estas señales):
- Es una acción o paso metodológico puntual ("acampar en poblados indígenas",
  "aprender el idioma indígena", "convivir con los nativos").
- Es una oración parafraseada o una conclusión del autor, no un término
  ("deducciones del autor", "no vivir con otros blancos", "la importancia de X").
- Es una crítica o juicio de valor puntual, no un término técnico
  ("crítica de descripciones grotescas de indígenas").
- Es un evento, anécdota o dato biográfico ("viaje a Nueva Guinea", "enfermedad
  durante el trabajo de campo").
- Es específico de una sola obra y no tiene vida propia fuera de ella
  ("el argumento central del capítulo 3").
- Solo pudiste describirlo parafraseando varias líneas del texto en vez de nombrarlo
  en 1-4 palabras — si no tiene un nombre corto y citable, no es un concepto.

AUTOVERIFICACIÓN OBLIGATORIA: antes de incluir cualquier nodo tipo "concepto", agrega
un campo "justificacion_concepto" explicando en una frase por qué este término
existiría en un glosario general de antropología, fuera de este libro. Si no puedes
escribir una justificación honesta y específica (no genérica), DESCARTA el nodo.

Si dudas, NO lo extraigas. Prefiere subextraer a sobreextraer — un grafo con 15
conceptos sólidos vale más que uno con 60 fragmentos triviales. Como referencia dura:
en un capítulo típico de 40,000 caracteres, esperarías entre 2 y 8 conceptos nuevos
reales, no más. Si tu borrador interno tiene más de 10, es señal de que estás
sobreextrayendo — vuelve a filtrar con el criterio de arriba antes de responder.

CRITERIO ESTRICTO PARA EL TIPO "autor":
Solo personas con un rol intelectual relevante: autores de obras propias, teóricos
que desarrollan o critican conceptos, o mentores académicos con relación directa
documentada con otro autor del grafo.

RECHAZA automáticamente cualquier autor cuya ÚNICA justificación sea una de estas
formas de mención de paso (si tu descripción del nodo suena a esto, NO LO EXTRAIGAS):
- "Autor mencionado/citado como fuente de datos generales sobre X"
- "Autor citado en relación con la frecuencia de [rasgo] entre [población]"
- Cualquier persona que aparece UNA SOLA VEZ en una nota al pie o cita de referencia
  bibliográfica erudita, sin que el texto principal discuta sus ideas.
- Un nombre que solo respalda un dato estadístico o anecdótico puntual (ej: "según
  Lissauer, el torus palatinus es frecuente entre los lapones") sin que el propio
  autor tenga una teoría, obra o debate asociado en el resto del texto.

PRUEBA DE FUEGO: si al terminar de leer todo el fragmento no podrías escribir una
relación de tipo "desarrolla_concepto", "critica_a", "influenciado_por" o similar
para esa persona (solo "estudia_a" con una cita de una sola frase de referencia
bibliográfica), entonces NO es un autor del grafo — es una nota al pie, ignórala
por completo, ni siquiera la menciones en tu respuesta.

CRITERIO PARA DISTINGUIR "cultura" DE "poblacion":
- "cultura" = un sistema de prácticas, creencias y organización social con nombre
  propio y descripción cualitativa (ej: "cultura trobriandesa", "culturas melanesias").
- "poblacion" = un grupo humano/étnico/racial identificado principalmente por su
  ubicación geográfica, ascendencia o composición demográfica, sin que el foco sea
  su sistema cultural (ej: "lapones", "indios Pueblo", "aborígenes del Nordeste
  asiático", "civilización china" como bloque poblacional-histórico).
Si dudas, pregúntate: ¿el texto describe PRÁCTICAS/CREENCIAS (-> cultura) o
DESCRIBE UN GRUPO/ORIGEN/DEMOGRAFÍA (-> poblacion)?

CRITERIO PARA DISTINGUIR "escuela" DE "corriente":
- "escuela" = una institución o grupo académico organizado con miembros
  identificables y una sede/tradición formal (ej: "Escuela de Cambridge",
  "Escuela de Chicago").
- "corriente" = una tendencia o línea de pensamiento transversal, sin una
  institución formal detrás (ej: "evolucionismo unilineal", "particularismo
  histórico", "difusionismo").
Si el texto no menciona una institución concreta ni miembros formales, usa
"corriente" en vez de "escuela".

REGLAS PARA IDs NUEVOS:
- Formato: minúsculas, sin tildes, sin espacios (usa guion bajo). Ej: "levi_strauss"
- Si el nodo ya existe en la lista de arriba, usa exactamente ese id — no generes uno nuevo.

FORMATO OBLIGATORIO PARA IDs EN RELACIONES (muy importante, fuente de errores pasados):
- CUALQUIER id que uses en "origen" o "destino" de una relación — sea de un nodo
  YA EXISTENTE (numérico) o de un nodo NUEVO de esta misma respuesta (snake_case) —
  SIEMPRE debe ir como STRING entre comillas en el JSON. Nunca como número JSON puro.
  Correcto:   "origen": "3"
  Incorrecto: "origen": 3
- Antes de escribir cada relación, verifica: ¿el id que puse en "origen"/"destino"
  aparece EXACTAMENTE en la lista de "NODOS QUE YA EXISTEN" de arriba, o en tu propio
  array "nodos_nuevos" de esta respuesta? Si no aparece en ninguno de los dos lugares,
  NO generes esa relación — sería una referencia a un nodo fantasma.

ESQUEMA DE SALIDA — devuelve ÚNICAMENTE este JSON, sin texto adicional ni markdown:
{{
  "nodos_nuevos": [
    {{
      "id": "string — id propuesto, solo si es una entidad NUEVA",
      "tipo": "autor|obra|concepto|escuela|cultura|debate|poblacion|corriente",
      "nombre": "string — nombre legible",
      "descripcion": "string — 1-2 oraciones basadas en el texto",
      "justificacion_concepto": "string — SOLO si tipo=concepto: por qué es un término establecido fuera de este libro. Omite este campo para otros tipos.",
      "confianza": "alta|media|baja — qué tan seguro estás de esta extracción"
    }}
  ],
  "relaciones_nuevas": [
    {{
      "origen": "string — SIEMPRE entre comillas, id del nodo origen (existente o de nodos_nuevos)",
      "destino": "string — SIEMPRE entre comillas, id del nodo destino (existente o de nodos_nuevos)",
      "tipo": "uno de los tipos de relación válidos",
      "nota": "string breve, contexto de la relación",
      "cita_textual": "string — el fragmento exacto del texto que justifica esto",
      "confianza": "alta|media|baja"
    }}
  ]
}}

REGLAS ESTRICTAS:
1. Solo extrae lo que el texto respalda explícitamente. No inventes relaciones.
2. Si el texto no menciona nada relevante, devuelve arrays vacíos.
3. "cita_textual" es OBLIGATORIA en cada relación — es lo que te permite verificar después.
4. Nunca devuelvas {{"error": ...}}. Si no hay nada, devuelve arrays vacíos.
5. Calidad sobre cantidad: es mejor extraer pocos nodos sólidos que muchos triviales.
"""
