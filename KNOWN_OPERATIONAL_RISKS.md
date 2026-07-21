# Riesgos Operativos Conocidos

**Fecha**: 2026-07-21
**Versión del sistema**: v1.1

---

## Propósito

Documentar todos los riesgos conocidos al utilizar el sistema en producción.
Para cada riesgo se indica probabilidad, impacto, detección, mitigación y recuperación.

No se proponen cambios de código. Solo procedimientos.

---

## 1. Errores Humanos

### R1.1: Ejecutar extracción sin backup previo

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Alto |
| **Cómo detectarlo** | No hay backup reciente en `data/` |
| **Cómo mitigarlo** | Seguir EXTRACTION_PROTOCOL.md (FASE B siempre) |
| **Cómo recuperarse** | Si no hay backup, no se puede recuperar |

### R1.2: Eliminar nodos importantes por error

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Alto |
| **Cómo detectarlo** | Auditoría muestra nodos faltantes |
| **Cómo mitigarlo** | Crear backup antes de eliminar. Usar revisión total con cuidado |
| **Cómo recuperarse** | Restaurar backup y re-insertar nodos eliminados |

### R1.3: Fusionar nodos que son entidades distintas

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Medio |
| **Cómo detectarlo** | Duplicados detectados en auditoría que no deberían estarlo |
| **Cómo mitigarlo** | Revisar cada par antes de fusionar. No usar fusión automática para nodos con relaciones |
| **Cómo recuperarse** | Restaurar backup antes de la fusión |

### R1.4: Usar opción incorrecta del menú

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Variable |
| **Cómo detectarlo** | Resultados inesperados |
| **Cómo mitigarlo** | Leer descripción de cada opción antes de ejecutar. Usar simulación primero |
| **Cómo recuperarse** | Restaurar backup si el daño es significativo |

---

## 2. Uso Incorrecto del Menú

### R2.1: Ejecutar limpieza automática sin revisar primero

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Alto |
| **Cómo detectarlo** | Nodos importantes eliminados |
| **Cómo mitigarlo** | Siempre ejecutar auditoría primero. Usar simulación antes de aplicar |
| **Cómo recuperarse** | Restaurar backup |

### R2.2: Ejecutar conexión automática sin simular primero

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Alto |
| **Cómo detectarlo** | Miles de nodos nuevos inesperados |
| **Cómo mitigarlo** | Siempre simular primero. Revisar resultados de la simulación |
| **Cómo recuperarse** | Restaurar backup |

### R2.3: Saltarse la revisión manual en el primer libro

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Medio |
| **Cómo detectarlo** | Nodos basura en la DB |
| **Cómo mitigarlo** | Siempre revisar manualmente el primer libro de cada campaña |
| **Cómo recuperarse** | Revisar y eliminar nodos incorrectos |

---

## 3. PDFs Corruptos o Ilegibles

### R3.1: PDF escaneado sin OCR

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Alto |
| **Cómo detectarlo** | extractor.py falla o devuelve texto vacío |
| **Cómo mitigarlo** | Verificar que el PDF contiene texto antes de procesar |
| **Cómo recuperarse** | Obtener versión con OCR del PDF |

### R3.2: PDF con protección contra copia

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Alto |
| **Cómo detectarlo** | PyMuPDF no puede extraer texto |
| **Cómo mitigarlo** | Verificar permisos del PDF antes de procesar |
| **Cómo recuperarse** | Obtener versión sin protección |

### R3.3: PDF con estructura compleja (tablas, imágenes)

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Medio |
| **Cómo detectarlo** | Texto extraído es incoherente |
| **Cómo mitigarlo** | Revisar calidad del texto extraído antes de procesar |
| **Cómo recuperarse** | Obtener versión simplificada del PDF |

---

## 4. Respuestas Inválidas del LLM

### R4.1: LLM devuelve JSON inválido

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Bajo |
| **Cómo detectarlo** | Log de errores en extractor (razon: json_invalido) |
| **Cómo mitigarlo** | El sistema maneja esto automáticamente (omite el chunk) |
| **Cómo recuperarse** | Re-ejecutar extractor (retoma desde el chunk fallido) |

### R4.2: LLM devuelve estructura JSON incorrecta

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Bajo |
| **Cómo detectarlo** | Errores al procesar candidatos_pendientes.json |
| **Cómo mitigarlo** | Revisar JSON antes de procesar |
| **Cómo recuperarse** | Corregir JSON manualmente o re-ejecutar extractor |

### R4.3: LLM alucina entidades inexistentes

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Medio |
| **Cómo detectarlo** | Revisión manual descubre entidades falsas |
| **Cómo mitigarlo** | Revisar candidatos contra el PDF. Verificar citas textuales |
| **Cómo recuperarse** | Eliminar entidades falsas durante la revisión |

### R4.4: LLM inventa citas textuales

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Alto |
| **Cómo detectarlo** | Búsqueda de la cita en el texto fuente falla |
| **Cómo mitigarlo** | Verificar citas manualmente (muestreo) |
| **Cómo recuperarse** | Eliminar relaciones con citas inventadas |

### R4.5: LLM sobreextrae conceptos

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Alta |
| **Impacto** | Medio |
| **Cómo detectarlo** | Revisión manual descubre conceptos que no son tales |
| **Cómo mitigarlo** | Aplicar criterio estricto del prompt. Rechazar conceptos dudosos |
| **Cómo recuperarse** | Eliminar o reclasificar conceptos incorrectos |

---

## 5. Interrupciones durante la Extracción

### R5.1: Corte de energía

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Bajo |
| **Cómo detectarlo** | Proceso se detiene inesperadamente |
| **Cómo mitigarlo** | El checkpoint preserva el progreso |
| **Cómo recuperarse** | Re-ejecutar extractor (retoma desde último chunk) |

### R5.2: Error de red (API no disponible)

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Bajo |
| **Cómo detectarlo** | Errores de conexión en log |
| **Cómo mitigarlo** | El sistema rota automáticamente entre API keys |
| **Cómo recuperarse** | Re-ejecutar extractor cuando la red esté disponible |

### R5.3: Límite de cuota de API

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Alta |
| **Impacto** | Bajo |
| **Cómo detectarlo** | Errores 429 o RESOURCE_EXHAUSTED en log |
| **Cómo mitigarlo** | Usar múltiples API keys. Esperar entre llamadas |
| **Cómo recuperarse** | Re-ejecutar extractor (rotará a siguiente key) |

### R5.4: Proceso eliminado por el usuario

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Bajo |
| **Cómo detectarlo** | Proceso no está corriendo |
| **Cómo mitigarlo** | No interrumpir procesos largos |
| **Cómo recuperarse** | Re-ejecutar extractor (retoma desde checkpoint) |

---

## 6. Inconsistencias Detectadas durante Revisión

### R6.1: Tipo de nodo no reconocido

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Bajo |
| **Cómo detectarlo** | Validación de tipos falla |
| **Cómo mitigarlo** | Verificar tipos en `config.py` |
| **Cómo recuperarse** | Reclasificar nodo con tipo válido |

### R6.2: Tipo de relación no canónico

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Bajo |
| **Cómo detectarlo** | `validar_relacion()` rechaza la relación |
| **Cómo mitigarlo** | Normalizar tipo antes de insertar |
| **Cómo recuperarse** | Ejecutar `migrate_relacion_types.py` |

### R6.3: Relación con nodos de tipos incompatibles

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Bajo |
| **Cómo detectarlo** | `validar_relacion()` rechaza la relación |
| **Cómo mitigarlo** | Verificar compatibilidad antes de insertar |
| **Cómo recuperarse** | Corregir tipos de nodo o eliminar relación |

---

## 7. Dificultades de Identificación de Duplicados

### R7.1: Duplicados con nombres diferentes

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Alta |
| **Impacto** | Medio |
| **Cómo detectarlo** | Auditoría muestra nodos sospechosos |
| **Cómo mitigarlo** | Revisar duplicados manualmente. Usar fusión con cuidado |
| **Cómo recuperarse** | Fusionar retroactivamente si se confirma que son iguales |

### R7.2: Duplicados con acentos diferentes

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Bajo |
| **Cómo detectarlo** | Búsqueda manual de variantes |
| **Cómo mitigarlo** | Normalizar nombres al comparar |
| **Cómo recuperarse** | Fusionar duplicados detectados |

### R7.3: Entidades legítimas confundidas con duplicados

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Medio |
| **Cómo detectarlo** | Revisión manual identifica error |
| **Cómo mitigarlo** | Verificar que las entidades son realmente distintas antes de fusionar |
| **Cómo recuperarse** | Separar entidades fusionadas por error |

---

## 8. Pérdida de Evidencia Documental

### R8.1: Relaciones insertadas sin cita_textual

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Alto |
| **Cómo detectarlo** | Auditoría muestra relaciones sin evidencia |
| **Cómo mitigarlo** | Siempre verificar que la relación tiene fuente o cita antes de insertar |
| **Cómo recuperarse** | Buscar evidencia en el PDF y agregar manualmente |

### R8.2: Citas textuales que no coinciden con el texto

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media |
| **Impacto** | Alto |
| **Cómo detectarlo** | Búsqueda manual de la cita en el PDF |
| **Cómo mitigarlo** | Verificar muestras de citas durante la revisión |
| **Cómo recuperarse** | Corregir o eliminar citas incorrectas |

### R8.3: Fuente de la relación incorrecta

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Baja |
| **Impacto** | Medio |
| **Cómo detectarlo** | Auditoría muestra fuentes inconsistentes |
| **Cómo mitigarlo** | Verificar que la fuente indica el PDF y páginas correctas |
| **Cómo recuperarse** | Corregir campo fuente manualmente |

---

## 9. Problemas de Rendimiento

### R9.1: Detección de duplicados lenta con miles de nodos

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Alta (con muchos libros) |
| **Impacto** | Medio |
| **Cómo detectarlo** | Detección de duplicados toma minutos |
| **Cómo mitigarlo** | Ejecutar detección por lotes, no sobre toda la DB |
| **Cómo recuperarse** | Esperar o reducir umbral de similitud |

### R9.2: Queries de validación lentas

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Media (con muchos libros) |
| **Impacto** | Bajo |
| **Cómo detectarlo** | Revisión manual toma más tiempo del esperado |
| **Cómo mitigarlo** | Procesar en lotes pequeños |
| **Cómo recuperarse** | Esperar |

---

## 10. Riesgos de Escalabilidad

### R10.1: Reviert manual no escala a cientos de libros

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Certa (con muchos libros) |
| **Impacto** | Alto |
| **Cómo detectarlo** | La revisión manual toma días |
| **Cómo mitigarlo** | Usar conexión automática para libros de baja ambigüedad |
| **Cómo recuperarse** | Priorizar revisión de candidatos de alta confianza |

### R10.2: Cantidad de candidatos acumulados

| Campo | Valor |
|-------|-------|
| **Probabilidad** | Alta (con muchos libros) |
| **Impacto** | Medio |
| **Cómo detectarlo** | candidatos_pendientes.json crece mucho |
| **Cómo mitigarlo** | Procesar libros uno por uno, no acumular muchos |
| **Cómo recuperarse** | Dividir candidatos por libro y procesar por separado |

---

## Matriz de Riesgos Resumen

| Riesgo | Probabilidad | Impacto | Prioridad |
|--------|-------------|---------|-----------|
| R1.1: Sin backup | Media | Alto | **ALTA** |
| R1.2: Eliminar nodos importantes | Baja | Alto | **MEDIA** |
| R1.3: Fusionar entidades distintas | Media | Medio | **MEDIA** |
| R4.4: LLM inventa citas | Media | Alto | **ALTA** |
| R4.5: Sobreextracción de conceptos | Alta | Medio | **MEDIA** |
| R5.3: Límite de cuota | Alta | Bajo | **BAJA** |
| R7.1: Duplicados difíciles | Alta | Medio | **MEDIA** |
| R8.1: Sin evidencia documental | Baja | Alto | **MEDIA** |
| R10.1: Revisión manual no escala | Cierta | Alto | **ALTA** |

---

## Recomendaciones Operativas

### Antes de cada sesión

1. Crear backup
2. Verificar estado de la DB
3. Ejecutar auditoría rápida

### Durante la sesión

1. Revisar candidatos con cuidado
2. Verificar citas textuales (muestreo)
3. No ejecutar limpieza sin backup

### Después de cada sesión

1. Crear backup
2. Exportar JSON
3. Documentar cambios
