# Informe de Validación — Plan de Migración v1.1

**Fecha**: 2026-07-20
**Estado**: Validación completada, pendiente de aprobación
**Objetivo**: Validar cada regla de migración antes de implementar el script

---

## Resumen Ejecutivo

| Categoría | Relaciones | Recomendación |
|-----------|------------|---------------|
| Migrar automáticamente | 44 | Sinónimos lingüísticos claros |
| Migrar con verificación | 15 | Requieren inspección de citas |
| Mantener (Nivel B) | 6 | concepto→concepto válido |
| Escalar al Autor | 18 | Contenido clasificatorio racial |
| Corregir tipografía | 1 | Error de ortografía |
| **Total** | **84** | |

---

## Tabla Completa de Validación

### A. Migración Automática (44 relaciones, confianza ALTA)

| Tipo original | Frec. | Destino | Confianza | Justificación | Ejemplo |
|---------------|-------|---------|-----------|---------------|---------|
| `escribió` | 6 | `autor_de` | Alta | Sinónimo directo | Lévi-Strauss escribió Tristes Trópicos |
| `es_autor_de` | 1 | `autor_de` | Alta | Variante con prefijo 'es_' | Boas es_autor_de Cuestiones fundamentales |
| `mentor_de` | 1 | `es_mentor_de` | Alta | Variante sin 'es_' | Seligman mentor_de Malinowski |
| `es_discípulo_de` | 2 | `es_mentor_de` | Alta | Relación inversa (invertir) | Lowie es_discípulo_de Boas → Boas es_mentor_de Lowie |
| `colaboro_con` | 2 | `colabora_con` | Alta | Variante conjugada | Combe colaboro_con Morton |
| `defiende_superioridad_de` | 2 | `critica_a` | Media | Oposición documentada | Gobineau defiende_superioridad_de Europeo noroccidental |
| `influyó_en` | 4 | `influenciado_por` | Alta | Forma conjugada (invertir) | A influyó en B → B es influenciado_por A |
| `influye_en` | 1 | `influenciado_por` | Alta | Presente de 'influir' (invertir) | A influye_en B → B es influenciado_por A |
| `influencio_a` | 1 | `influenciado_por` | Alta | Pretérito de 'influenciar' (invertir) | A influencio_a B → B es influenciado_por A |
| `facilito_por` | 1 | `influenciado_por` | Media | Influencia mediática (invertir) | A facilito_por B → B es influenciado_por A |
| `condiciona` | 1 | `influenciado_por` | Media | Influencia causal fuerte (invertir) | A condiciona B → B es influenciado_por A |
| `refuta` | 2 | `critica_a` | Alta | Sinónimo claro | A refuta B → A critica_a B |
| `lucha_contra` | 1 | `critica_a` | Alta | Oposición explícita | A lucha_contra B → A critica_a B |
| `opuesto_a` | 1 | `critica_a` | Alta | Oposición documentada | A opuesto_a B → A critica_a B |
| `contrasta_con` | 2 | `critica_a` | Alta | Diferencias significativas | A contrasta_con B → A critica_a B |
| `malinterpreta_a` | 2 | `critica_a` | Alta | Crítica implícita | A malinterpreta_a B → A critica_a B |
| `subestima_concepto` | 1 | `critica_a` | Alta | Crítica sobre importancia | A subestima_concepto B → A critica_a B |
| `manipula_concepto` | 1 | `critica_a` | Alta | Crítica negativa | A manipula_concepto B → A critica_a B |
| `es_respuesta_a` | 1 | `critica_a` | Media | Réplica/crítica | A es_respuesta_a B → A critica_a B |
| `estudio` | 5 | `estudia_a` | Alta | Sinónimo directo | Autor estudio Cultura → estudia_a |
| `escribe_estudio_preliminar_para` | 1 | `estudia_a` | Media | Examen/estudio implícito | Autor escribe_estudio_preliminar_para Obra |
| `es_fuente_sobre` | 3 | `estudia_a` | Alta | Fuente implica estudio | Autor es_fuente_sobre Tema |
| `cita_a` | 3 | `estudia_a` | Media | Cita implica referencia | Autor cita_a Autor2 |
| `realiza_trabajo_de_campo_en` | 2 | `estudia_a` | Alta | Trabajo de campo = estudio empírico | Autor realiza_trabajo_de_campo_en Cultura |
| `evalua_contribucion_de` | 1 | `estudia_a` | Media | Evaluar = analizar/estudiar | Autor evalua_contribucion_de Autor2 |

**Total**: 44 relaciones con confianza alta/media

---

### B. Migración con Verificación (15 relaciones)

| Tipo original | Frec. | Destino propuesto | Confianza | Justificación | Nota |
|---------------|-------|-------------------|-----------|---------------|------|
| `contribuye_a` | 8 | `parte_del_debate` | Media | Contribuir a debate = participar | Verificar que destino sea debate |
| `representado_por` | 5 | `desarrolla_concepto` | Media | Representar = encarnar/desarrollar | Verificar que destino sea concepto |
| `presenta_rasgo` | 4 | `desarrolla_concepto` | Media | Presentar rasgo = encarnar concepto | Verificar que destino sea concepto |
| `desarrollada_por` | 2 | `desarrolla_concepto` | Alta | Inversión de 'desarrolla_concepto' | Invertir dirección |
| `afecta_a` | 2 | `influenciado_por` | Baja | Afectar ≈ influir | Requiere decisión ontológica |
| `usa_enfoque` | 1 | `desarrolla_concepto` | Media | Usar enfoque = desarrollarlo | Verificar semántica |
| `aplicado_a` | 1 | `desarrolla_concepto` | Media | Aplicar = desarrollar | Verificar semántica |
| `descubierta_por` | 1 | `precursor_de` | Media | Inversión de 'precursor_de' | Invertir dirección |

**Total**: 15 relaciones que requieren verificación caso por caso

---

### C. Mantener como Nivel B (6 relaciones)

| Tipo | Frec. | Origen | Destino | Justificación |
|------|-------|--------|---------|---------------|
| `relacionado_con` | 6 | concepto | concepto | Nivel B válido: vínculo semántico entre conceptos |

**Nota**: 2 relaciones `relacionado_con` tienen destino cultura/obra y requieren revisión separada.

---

### D. Escalar al Autor (18 relaciones)

| Tipo | Frec. | Problema | Ejemplo |
|------|-------|----------|---------|
| `clasifica_como_activo` | 11 | Contenido racial evaluativo | Klemm clasifica_como_activo Europeos |
| `clasifica_como_pasivo` | 4 | Contenido racial evaluativo | Klemm clasifica_como_pasivo Mongólicos |
| `otorga_primacia_a` | 3 | Ranking racial evaluativo | Carus otorga_primacia_a Indostánica |
| `venera_concepto` | 1 | Carga valorativa explícita | Esquimales venera_concepto Sedna |
| `considera_indispensable` | 1 | Carga valorativa explícita | Lévi-Strauss considera_indispensable Participación etnográfica |
| `limita` | 1 | Relación causal no capturada | Caza y recolección limita Densidad de población |
| `limita_expansion_a` | 1 | Relación causal no capturada | Población de Turkestán limita_expansion_a Europeos |
| `invadio` | 1 | Error tipográfico + decisión semántica | Tribus hamíticas invadio África noroccidental |

**Total**: 18 relaciones que requieren decisión del Autor

---

### E. Corregir Tipografía (1 relación)

| Tipo | Frec. | Corrección | Justificación |
|------|-------|------------|---------------|
| `invadio` | 1 | `invadió` | Error de ortografía evidente |

**Nota**: Además de corregir la ortografía, se debe decidir el tipo semántico apropiado.

---

## Casos Ambiguos (requieren decisión explícita)

### 1. `clasifica_como_activo` / `clasifica_como_pasivo` (15 relaciones)

**Problema**: Contenido clasificatorio racial evaluativo de Klemm.

**Alternativas**:
| Alternativa | Ventajas | Desventajas |
|-------------|----------|-------------|
| `desarrolla_concepto` | Simplifica ontología | Blanquea contenido racista |
| ELIMINAR | Consistente con firewall | Pierde información histórica |
| Mantener como no canónico | Preserva semántica | Rompe ontología de 12 tipos |

**Recomendación**: Escalar al Autor para decidir cómo modelar clasificaciones raciales.

### 2. `afecta_a` (2 relaciones)

**Problema**: 'Afectar' es más fuerte que 'influenciar'.

**Alternativas**:
| Alternativa | Ventajas | Desventajas |
|-------------|----------|-------------|
| `influenciado_por` | Captura influencia | Pierde intensidad causal |
| Mantener como no canónico | Preserva semántica | Rompe ontología |

**Recomendación**: Escalar al Autor por ambigüedad semántica.

### 3. `limita` / `limita_expansion_a` (2 relaciones)

**Problema**: Relación causal no capturada por tipos canónicos.

**Alternativas**:
| Alternativa | Ventajas | Desventajas |
|-------------|----------|-------------|
| `critica_a` | Captura oposición | 'Limitar' no es 'criticar' |
| Mantener como no canónico | Preserva semántica | Rompe ontología |

**Recomendación**: Escalar al Autor por falta de tipo canónico adecuado.

---

## Recomendación Final por Tipo

| Tipo | Frec. | Recomendación | Acción |
|------|-------|---------------|--------|
| `escribió` | 6 | Migrar automáticamente | `UPDATE SET tipo='autor_de'` |
| `es_autor_de` | 1 | Migrar automáticamente | `UPDATE SET tipo='autor_de'` |
| `mentor_de` | 1 | Migrar automáticamente | `UPDATE SET tipo='es_mentor_de'` |
| `es_discípulo_de` | 2 | Migrar automáticamente | Invertir + `UPDATE SET tipo='es_mentor_de'` |
| `colaboro_con` | 2 | Migrar automáticamente | `UPDATE SET tipo='colabora_con'` |
| `defiende_superioridad_de` | 2 | Migrar automáticamente | `UPDATE SET tipo='critica_a'` |
| `influyó_en` | 4 | Migrar automáticamente | Invertir + `UPDATE SET tipo='influenciado_por'` |
| `influye_en` | 1 | Migrar automáticamente | Invertir + `UPDATE SET tipo='influenciado_por'` |
| `influencio_a` | 1 | Migrar automáticamente | Invertir + `UPDATE SET tipo='influenciado_por'` |
| `facilito_por` | 1 | Migrar automáticamente | Invertir + `UPDATE SET tipo='influenciado_por'` |
| `condiciona` | 1 | Migrar automáticamente | Invertir + `UPDATE SET tipo='influenciado_por'` |
| `refuta` | 2 | Migrar automáticamente | `UPDATE SET tipo='critica_a'` |
| `lucha_contra` | 1 | Migrar automáticamente | `UPDATE SET tipo='critica_a'` |
| `opuesto_a` | 1 | Migrar automáticamente | `UPDATE SET tipo='critica_a'` |
| `contrasta_con` | 2 | Migrar automáticamente | `UPDATE SET tipo='critica_a'` |
| `malinterpreta_a` | 2 | Migrar automáticamente | `UPDATE SET tipo='critica_a'` |
| `subestima_concepto` | 1 | Migrar automáticamente | `UPDATE SET tipo='critica_a'` |
| `manipula_concepto` | 1 | Migrar automáticamente | `UPDATE SET tipo='critica_a'` |
| `es_respuesta_a` | 1 | Migrar automáticamente | `UPDATE SET tipo='critica_a'` |
| `estudio` | 5 | Migrar automáticamente | `UPDATE SET tipo='estudia_a'` |
| `escribe_estudio_preliminar_para` | 1 | Migrar automáticamente | `UPDATE SET tipo='estudia_a'` |
| `es_fuente_sobre` | 3 | Migrar automáticamente | `UPDATE SET tipo='estudia_a'` |
| `cita_a` | 3 | Migrar automáticamente | `UPDATE SET tipo='estudia_a'` |
| `realiza_trabajo_de_campo_en` | 2 | Migrar automáticamente | `UPDATE SET tipo='estudia_a'` |
| `evalua_contribucion_de` | 1 | Migrar automáticamente | `UPDATE SET tipo='estudia_a'` |
| `contribuye_a` | 8 | Migrar con verificación | Verificar destino='debate' |
| `representado_por` | 5 | Migrar con verificación | Verificar destino='concepto' |
| `presenta_rasgo` | 4 | Migrar con verificación | Verificar destino='concepto' |
| `desarrollada_por` | 2 | Migrar con verificación | Invertir dirección |
| `afecta_a` | 2 | **Escalar al Autor** | Ambigüedad semántica |
| `usa_enfoque` | 1 | Migrar con verificación | Verificar semántica |
| `aplicado_a` | 1 | Migrar con verificación | Verificar semántica |
| `descubierta_por` | 1 | Migrar con verificación | Invertir dirección |
| `relacionado_con` | 6 | **Mantener (Nivel B)** | concepto→concepto válido |
| `relacionado_con` | 2 | **Escalar al Autor** | concepto→cultura/obra |
| `clasifica_como_activo` | 11 | **Escalar al Autor** | Contenido racial |
| `clasifica_como_pasivo` | 4 | **Escalar al Autor** | Contenido racial |
| `otorga_primacia_a` | 3 | **Escalar al Autor** | Ranking racial |
| `venera_concepto` | 1 | **Escalar al Autor** | Carga valorativa |
| `considera_indispensable` | 1 | **Escalar al Autor** | Carga valorativa |
| `limita` | 1 | **Escalar al Autor** | Relación causal |
| `limita_expansion_a` | 1 | **Escalar al Autor** | Relación causal |
| `invadio` | 1 | **Escalar al Autor** | Error tipográfico |

---

## Resumen de Acciones

| Acción | Relaciones | Porcentaje |
|--------|------------|------------|
| Migrar automáticamente | 44 | 52.4% |
| Migrar con verificación | 15 | 17.9% |
| Mantener (Nivel B) | 6 | 7.1% |
| Escalar al Autor | 18 | 21.4% |
| Corregir tipografía | 1 | 1.2% |
| **Total** | **84** | **100%** |

---

## Próximos Pasos

1. **Esperar aprobación del Autor** para los 18 casos escalados
2. **Crear script de migración** solo para las 44 relaciones automáticas
3. **Ejecutar verificación** para las 15 relaciones semi-automáticas
4. **Postergar** las 18 relaciones que requieren decisión ontológica
