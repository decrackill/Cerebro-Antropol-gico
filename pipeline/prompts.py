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

TIPOS DE NODO válidos: autor, obra, concepto, escuela, cultura, debate
TIPOS DE RELACIÓN válidos: influenciado_por, critica_a, desarrolla_concepto,
  pertenece_a, estudia_a, contemporaneo_de, precursor_de, parte_del_debate, redefine_a

CRITERIO ESTRICTO PARA EL TIPO "concepto":
Un concepto SOLO califica si es un término teórico establecido, citable y con nombre
propio dentro de la disciplina — algo que un antropólogo reconocería y usaría en otro
contexto, independiente de este libro. Ejemplos válidos: "reciprocidad", "parentesco",
"relativismo cultural", "observación participante", "holismo", "kula", "estructura social".

NO califica como concepto:
- Pasos o técnicas descriptivas de un método (ej: "acampar en poblados indígenas",
  "aprender el idioma indígena" — estos son DETALLES de cómo se practica la
  "observación participante", no conceptos en sí mismos).
- Oraciones o ideas parafraseadas del texto que no son términos establecidos
  (ej: "deducciones del autor", "no vivir con otros blancos").
- Críticas o argumentos puntuales de un autor sin ser un término reconocido
  (ej: "crítica de descripciones grotescas de indígenas").

Si dudas si algo es un concepto real o solo una idea de paso, NO lo extraigas.
Prefiere subextraer a sobreextraer. Es mejor un grafo con 15 conceptos sólidos
que con 60 fragmentos triviales.

CRITERIO ESTRICTO PARA EL TIPO "autor":
Solo personas con un rol intelectual relevante (autores, teóricos, mentores académicos).
NO incluyas menciones incidentales como financistas, editores técnicos, traductores,
o comerciantes que aparecen una sola vez sin aporte teórico — esos, si quieres
preservarlos, van en el campo "nota" de una relación, no como nodo propio.

REGLAS PARA IDs NUEVOS:
- Formato: minúsculas, sin tildes, sin espacios (usa guion bajo). Ej: "levi_strauss"
- Si el nodo ya existe en la lista de arriba, usa exactamente ese id — no generes uno nuevo.

ESQUEMA DE SALIDA — devuelve ÚNICAMENTE este JSON, sin texto adicional ni markdown:
{{
  "nodos_nuevos": [
    {{
      "id": "string — id propuesto, solo si es una entidad NUEVA",
      "tipo": "autor|obra|concepto|escuela|cultura|debate",
      "nombre": "string — nombre legible",
      "descripcion": "string — 1-2 oraciones basadas en el texto",
      "confianza": "alta|media|baja — qué tan seguro estás de esta extracción"
    }}
  ],
  "relaciones_nuevas": [
    {{
      "origen": "id del nodo origen (existente o de nodos_nuevos)",
      "destino": "id del nodo destino (existente o de nodos_nuevos)",
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
