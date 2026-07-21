# Changelog — Evolución de la Ontología

Registro trazable de todos los cambios en la ontología del proyecto.
Cualquier evolución futura debe registrarse aquí.

**Autoridad máxima**: [MANIFIESTO_ONTOLOGICO.md](MANIFIESTO_ONTOLOGICO.md)

---

## v1.1 — 2026-07-20

### Cambios realizados

1. **Reincorporación de `estudia_a`** como relación canónica de Nivel A (#8)
   - Estaba documentada en el Vault (§3.8) pero ausente del Manifiesto v1.0
   - Fundamento: relación estructural para el firewall epistemológico
   - Sin sustituto semántico posible

2. **Reclasificación de relaciones conceptuales**
   - `contradice`, `relacionado_con`, `depende_de` → Nivel B (experimental)
   - No son parte del núcleo canónico
   - Se definen como "capa adicional" para modelar relaciones entre conceptos

3. **Tabla de compatibilidad completa**
   - Se documentaron dominio, rango y simetría para las 12 relaciones
   - Fuente: Vault §4.1

4. **Nuevo principio arquitectónico §2.4**
   - "Independencia del corpus": una relación no se elimina por tener pocos ejemplos

5. **Sistema de validación centralizada**
   - `validar_relacion()` en `pipeline/core/db.py`
   - 5 validadores: tipo, reflexividad, firewall, compatibilidad, evidencia

### Impacto sobre el código

| Archivo | Cambio |
|---------|--------|
| `pipeline/core/config.py` | 9 → 12 tipos en `TIPOS_VALIDOS_RELACION` |
| `pipeline/core/db.py` | +150 líneas: `validar_relacion()` + validadores |
| `pipeline/extract/prompts.py` | Lista 12 tipos + instrucción firewall |
| `pipeline/review/revision.py` | 2 INSERT protegidos por `validar_relacion()` |
| `pipeline/review/limpieza.py` | 1 INSERT protegido por `validar_relacion()` |
| `scripts/init_db.py` | CHECK constraint 9 → 12 tipos |
| `tests/conftest.py` | CHECK constraint 9 → 12 tipos |
| `tests/test_firewall.py` | Nuevo: 56 tests de validación ontológica |

### Impacto sobre la base de datos

- CHECK constraint actualizado a 12 tipos canónicos
- DB existente: pendiente migración en Fase 4

### Compatibilidad con versiones anteriores

- **Parcialmente compatible**: la DB existente tiene 34 tipos no canónicos
- Se requiere migración para alinear DB con Manifiesto v1.1
- No hay pérdida de datos si la migración se ejecuta correctamente

---

## v1.0 — 2026-07-20 (versión inicial del Manifiesto)

### Contenido

- 8 tipos de nodo
- 7 relaciones de Nivel A (autor_de, desarrolla_concepto, critica_a, redefine_a, parte_del_debate, es_mentor_de, colabora_con)
- 4 relaciones de Nivel B (contradice, relacionado_con, depende_de, influenciado_por)
- Firewall epistemológico
- Reglas de integridad

### Observaciones

- `influenciado_por` estaba en Nivel B pero es canónica según el Vault → corregida en v1.1
- `estudia_a` faltaba → reincorporada en v1.1
- `pertenece_a`, `contemporaneo_de`, `precursor_de` faltaban → reincorporadas en v1.1

---

## Plantilla para futuros cambios

```markdown
## vX.Y — YYYY-MM-DD

### Cambios realizados
- [descripción del cambio]

### Impacto sobre el código
- [archivos modificados]

### Impacto sobre la base de datos
- [cambios en schema o datos]

### Compatibilidad con versiones anteriores
- [si es compatible o requiere migración]
```
