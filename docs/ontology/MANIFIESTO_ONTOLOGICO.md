# MANIFIESTO ONTOLÓGICO — PROYECTO CEREBRO ANTROPOLÓGICO
**Versión**: 1.1 (Especificación Técnica Normativa)
**Fecha**: 2026-07-20
**Estado**: Estable / Fuente de Verdad Absoluta
**Cambios vs v1.0**: Reincorporación de `estudia_a`, aclaración de estatus de relaciones conceptuales, tabla de compatibilidad completa

---

## 1. PROPÓSITO Y ALCANCE
Esta especificación técnica define formalmente la ontología del **Cerebro Antropológico**. Su función es actuar como la norma máxima para la clasificación, validación e integración de conocimiento dentro del grafo. 

Cualquier sistema (humano o IA) que interactúe con este repositorio DEBE seguir estas reglas para garantizar la integridad semántica del proyecto.

---

## 2. FILOSOFÍA Y PRINCIPIOS FUNDAMENTALES

### 2.1. Primacía Ontológica
La ontología representa el modelo conceptual puro. El software y la base de datos son implementaciones técnicas subordinadas. En caso de conflicto, **el Manifiesto siempre prevalece**. El código contradictorio será considerado deuda técnica. [Origen: Autor/05/3]

### 2.2. Realismo Crítico y Neutralidad
El grafo documenta **afirmaciones de conocimiento**, no "verdades" objetivas.
*   **Principio de Trazabilidad**: Cada relación representa una relación epistemológica respaldada por evidencia documental (fuente + cita). [Origen: Autor/05/11]
*   **Neutralidad Descriptiva**: Las valoraciones pertenecen al autor de la fuente, nunca al objeto descrito. ESTÁ PROHIBIDO incorporar juicios evaluativos como atributos de nodo. [Origen: Autor/05/5]

### 2.3. Mínima Complejidad
La ontología DEBE mantenerse tan pequeña como sea posible y tan expresiva como sea necesario. NO DEBEN añadirse tipos ni reglas por utilidad futura sin evidencia actual. [Origen: Autor/05/12]

### 2.4. Independencia del Corpus
Una relación no podrá eliminarse únicamente porque tenga pocos ejemplos en la base de datos actual. La ontología se diseña para representar correctamente el dominio de conocimiento, no para ajustarse al tamaño del corpus existente. [Origen: Auditoría v1.1]

---

## 3. MODELO CONCEPTUAL: ARQUITECTURA DIMENSIONAL
El grafo se estructura en dos dimensiones complementarias e inseparables:

### 3.1. Dimensión Histórica (Agencia)
Describe la producción histórica del conocimiento.
*   **Función**: Modelar actos intelectuales realizados por agentes.
*   **Orígenes Válidos**: `autor`, `obra`, y excepcionalmente `escuela` o `corriente`. [Origen: Autor/05/2]

### 3.2. Dimensión Conceptual (Semántica)
Describe la organización lógica de las ideas.
*   **Función**: Modelar relaciones lógicas, oposiciones y dependencias entre conceptos.
*   **Orígenes Válidos**: `concepto`. [Origen: Autor/05/2]

---

## 4. ESPECIFICACIÓN DE NODOS (ENTIDADES)

### 4.1. Reglas Generales de Clasificación
*   **Identidad Única**: Cada nodo DEBE pertenecer a un único tipo. NO SE PERMITE la doble categorización. [Origen: Autor/05/1]
*   **Clasificación Principal**: Se DEBE elegir el tipo que mejor represente la función epistemológica principal de la entidad. [Origen: Autor/05/1]

### 4.2. Tipos de Nodo

| Tipo | Definición Formal | Uso Correcto | Contraejemplo |
|------|-------------------|--------------|---------------|
| **autor** | Agente histórico productor de conocimiento. | Individuos con obra. | Grupos o instituciones. |
| **obra** | Objeto textual con identidad bibliográfica. | Libros, artículos, traducciones. | Conceptos descritos en la obra. |
| **concepto** | Unidad teórica o categoría de análisis. | Términos técnicos, ideas. | El autor que acuñó la idea. |
| **escuela** | Tradición delimitada por linaje o institución. | Escuela Boasiana, Chicago. | Paradigmas generales. |
| **corriente** | Paradigma teórico que atraviesa escuelas. | Funcionalismo, Evolucionismo. | Grupos de personas específicos. |
| **cultura** | Grupo humano definido etnográficamente. | Pueblos, sociedades, etnias. | Categorías raciales-históricas. |
| **poblacion** | Categoría clasificatoria histórica/racial. | Conjuntos definidos como raza. | Identidades culturales activas. |
| **debate** | Controversia académica documentada. | Disputas con participantes. | Temas de interés general. |

---

## 5. ESPECIFICACIÓN DE RELACIONES (CONEXIONES)

### 5.1. Relaciones de Agencia — Nivel A (Canónicas)

Las 12 relaciones de Nivel A constituyen el **núcleo canónico** de la ontología. Son obligatorias para toda implementación válida.

| # | Relación | Significado Epistemológico | Simetría | Origen Válido | Destino Válido |
|---|----------|---------------------------|----------|---------------|----------------|
| 1 | **autor_de** | Atribución de autoría. | Asimétrica | `autor` | `obra` |
| 2 | **influenciado_por** | Impacto intelectual general. | Asimétrica | `autor`, `obra`, `escuela`, `corriente`, `concepto` | `autor`, `obra`, `escuela`, `corriente`, `concepto` |
| 3 | **critica_a** | Expresión documentada de desacuerdo. | Asimétrica | `autor`, `obra`, `escuela`, `corriente` | `autor`, `obra`, `escuela`, `corriente`, `concepto` |
| 4 | **desarrolla_concepto** | Exposición original de una idea. | Asimétrica | `autor`, `obra`, `escuela`, `corriente` | `concepto` |
| 5 | **redefine_a** | Modificación semántica de un término. | Asimétrica | `autor`, `obra`, `concepto` | `concepto` |
| 6 | **precursor_de** | Juicio retrospectivo de antecesión. | Asimétrica | `autor`, `obra`, `escuela`, `corriente`, `concepto` | `autor`, `obra`, `escuela`, `corriente`, `concepto` |
| 7 | **pertenece_a** | Afiliación o membresía. | Asimétrica | `autor`, `concepto`, `escuela` | `escuela`, `corriente` |
| 8 | **estudia_a** | Examen/objeto de estudio, sin implicar causalidad. | Asimétrica | `autor`, `obra` | `poblacion`, `cultura` |
| 9 | **contemporaneo_de** | Relación temporal de solapamiento. | Simétrica | `autor` | `autor` |
| 10 | **parte_del_debate** | Participación en una controversia. | Asimétrica | `autor`, `obra`, `concepto`, `poblacion`, `escuela`, `corriente` | `debate` |
| 11 | **es_mentor_de** | Linaje pedagógico directo. | Asimétrica | `autor` | `autor` |
| 12 | **colabora_con** | Trabajo conjunto documentado. | Simétrica | `autor` | `autor` |

#### Notas sobre simetría:
- **Simétricas** (se almacenan una sola vez por par): `contemporaneo_de`, `colabora_con`
- **Asimétricas** (se almacenan con dirección explícita): todas las demás
- `es_mentor_de` es asimétrica pero solo se almacena en dirección mentor→discípulo; la inversa es lectura de interfaz, no tipo separado

### 5.2. Relaciones Conceptuales — Nivel B (Capa Adicional)

Las relaciones de Nivel B son una **capa ontológica adicional** para modelar relaciones entre conceptos. No son parte del núcleo canónico pero pueden activarse para enriquecer la dimensión conceptual del grafo.

| Relación | Significado Epistemológico | Simetría | Origen Válido | Destino Válido |
|----------|---------------------------|----------|---------------|----------------|
| **contradice** | Incompatibilidad lógica/teórica entre conceptos. | Asimétrica | `concepto` | `concepto` |
| **relacionado_con** | Vínculo semántico general entre conceptos. | Simétrica | `concepto` | `concepto` |
| **depende_de** | Requisito teórico previo para la comprensión. | Asimétrica | `concepto` | `concepto` |

#### Estado de estabilidad:
- **Nivel A**: ESTABLE — núcleo de 12 relaciones canónicas
- **Nivel B**: EXPERIMENTAL — relaciones conceptuales sujetas a revisión

### 5.3. Relaciones Prohibidas (Firewall Epistemológico)

**Regla absoluta:** Ninguna relación puede conectar directamente un nodo `poblacion` con un nodo `cultura` o `concepto`, **excepto**:
- `estudia_a` (destino): un autor examina la categoría sin implicar causalidad
- `parte_del_debate` (origen): la categoría es objeto de disputa

**Nunca existirá** un tipo de relación que exprese explicación causal con `poblacion` como origen (nada como "determina", "explica", "causa").

**Justificación:** Esta restricción impide que el grafo pueda representar, aunque sea accidentalmente, una afirmación de determinismo racial como un hecho neutral. [Origen: Autor/05/2, Vault/Fase 2]

---

## 6. REGLAS NORMATIVAS Y RESTRICCIONES

### 6.1. El Firewall Epistemológico
1.  **Aislamiento de Población**: ESTÁ PROHIBIDO crear relaciones de causalidad o influencia que partan de un nodo `poblacion` hacia `cultura` o `concepto`. [Origen: Vault/Fase 2]
2.  **Protección de Agencia**: Un `concepto` NO DEBE realizar acciones históricas contra un `autor` (ej. un concepto no critica autores). [Origen: Autor/05/2]

### 6.2. Reglas de Integridad
*   **Evidencia**: Toda relación DEBE registrar `cita_textual` y `fuente`.
*   **No Reflexividad**: ESTÁ PROHIBIDO que un nodo se conecte a sí mismo.
*   **Invarianza**: Si existe duda en la clasificación, se DEBE escalar al Autor antes de forzar un tipo.

### 6.3. Propiedades Formales de las Relaciones

| Propiedad | Definición | Relaciones que la cumplen |
|-----------|------------|---------------------------|
| **Simetría** | A→B implica B→A (almacenamiento único) | `contemporaneo_de`, `colabora_con`, `relacionado_con` |
| **Asimetría** | A→B no implica B→A (dirección explícita) | Todas las demás |
| **Transitividad** | A→B y B→C implica A→C | Ninguna (por diseño) |
| **Reflexividad** | A→A es válida | Ninguna (prohibida explícitamente) |

---

## 7. TRAZABILIDAD DE DECISIONES (DOR)

| Regla / Decisión | Origen Primario | Justificación |
|------------------|-----------------|---------------|
| **No doble categorización** | Autor (05/1) | Evitar ambigüedad estructural en el grafo. |
| **Conceptos como origen** | Autor (05/13) | Habilitar la Dimensión Conceptual independiente de la historia. |
| **Traducciones como nodos** | Autor (05/6) | Preservar identidad bibliográfica y matices de traducción. |
| **Eliminación de Evento/Inst.** | Autor (05/9) | Principio de mínima complejidad. |
| **Población vs Cultura** | Vault (Fase 2) | Firewall contra el racismo científico histórico. |
| **Código = Deuda Técnica** | Autor (05/3) | Garantizar que el software no dicte la ontología. |
| **12 relaciones canónicas** | Vault (Fase 2 §3) | Diseño completo del sistema relacional. |
| **`estudia_a` canónica** | Vault (Fase 2 §3.8), Auditoría v1.1 | Fundamental para firewall epistemológico; sin sustituto semántico. |
| **Nivel B como capa adicional** | Vault (Fase 8), Auditoría v1.1 | Relaciones conceptuales experimentales, no núcleo canónico. |
| **Independencia del corpus** | Auditoría v1.1 | La ontología se diseña para el dominio, no para el corpus actual. |

---

## 8. NIVELES DE ESTABILIDAD

*   **ESTABLE**: Núcleo de 8 tipos de nodo y 12 relaciones de Nivel A (canónicas).
*   **EXPERIMENTAL**: Relaciones conceptuales de Nivel B (contradice, relacionado_con, depende_de).
*   **FUTURA EXPANSIÓN**: Temporalidad, roles de coautoría, integración externa (OpenAlex, Wikidata).

---

## 9. COMPATIBILIDAD CON CÓDIGO

### 9.1. Tipos de nodo
El código (`TIPOS_VALIDOS_NODO`) valida los 8 tipos definidos en §4.2. **Estado: CONSISTENTE.**

### 9.2. Tipos de relación
El código (`TIPOS_VALIDOS_RELACION`) implementa 9 de las 12 relaciones canónicas:

| Relación | ¿En código? | Estado |
|----------|-------------|--------|
| autor_de | ❌ | PENDIENTE |
| influenciado_por | ✅ | OK |
| critica_a | ✅ | OK |
| desarrolla_concepto | ✅ | OK |
| redefine_a | ✅ | OK |
| precursor_de | ✅ | OK |
| pertenece_a | ✅ | OK |
| estudia_a | ✅ | OK |
| contemporaneo_de | ✅ | OK |
| parte_del_debate | ✅ | OK |
| es_mentor_de | ❌ | PENDIENTE |
| colabora_con | ❌ | PENDIENTE |

**Deuda técnica**: `autor_de`, `es_mentor_de` y `colabora_con` existen en la DB pero no están validadas por el código.

---

**Certificación de Autoridad**: Este documento es la Constitución Ontológica del proyecto Cerebro Antropológico. Cualquier implementación que ignore estas reglas se considera inválida.
