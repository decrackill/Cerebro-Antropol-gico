# Cerebro Antropológico — Ayuda Rápida

## Primera vez

1. Coloca un PDF en `libros/`
2. Ejecuta `python3 -m pipeline.cli.menu`
3. Elige `e1` para extraer entidades del PDF
4. Sigue con opción `1` para revisar candidatos
5. Luego `2` (conectar), `4` (auditar), `11` (exportar)
6. Visualiza con `npm run dev`

## Menú de Opciones

### Extracción
| Opción | Descripción |
|--------|-------------|
| `e1` | Extracción automática con Gemini API |
| `e2` | Modo manual: generar prompt o pegar respuesta |
| `e3` | Verificar cobertura de extracción por PDF |

### Revisión
| Opción | Descripción |
|--------|-------------|
| `1` | Revisar candidatos pendientes uno por uno |
| `15` | Revisión total de TODOS los nodos en DB |
| `16` | Marcar nodos como ontológicamente revisados (batch) |

### Conexiones
| Opción | Descripción |
|--------|-------------|
| `2` | Resolver relaciones candidate → DB en bulk |
| `3` | Recuperar relaciones de caché histórica |

### Limpieza
| Opción | Descripción |
|--------|-------------|
| `5` | Limpieza automática segura (fusión + ruido) |
| `6` | Fusionar duplicados manualmente uno por uno |
| `7` | Fusión automática sin preguntar |
| `8` | Limpieza asistida de nodos aislados |
| `9` | Eliminación agresiva de ruido biomédico |

### Diagnóstico
| Opción | Descripción |
|--------|-------------|
| `4` | Auditoría completa del grafo |
| `10` | Re-ejecutar diagnóstico |

### Mantenimiento
| Opción | Descripción |
|--------|-------------|
| `11` | Exportar DB → `public/datos.json` |
| `12` | Crear/verificar índices de la DB |
| `13` | Limpiar archivos temporales y logs |
| `14` | Mantenimiento automático completo |

## Conceptos Clave

### Ontología v1.1
- **8 tipos de nodo**: autor, obra, concepto, escuela, corriente, cultura, poblacion, debate
- **12 relaciones Nivel A**: autor_de, influenciado_por, critica_a, desarrolla_concepto, redefine_a, precursor_de, pertenece_a, estudia_a, contemporaneo_de, parte_del_debate, es_mentor_de, colabora_con
- **3 relaciones Nivel B**: contradice, relacionado_con, depende_de

### Firewall Epistemológico
- `poblacion` solo es **destino** de `estudia_a`
- `poblacion` solo es **origen** de `parte_del_debate`

### Validación de Relaciones
Toda relación pasa por 6 validadores:
1. Tipo canónico
2. No reflexividad
3. Firewall epistemológico
4. Compatibilidad origen/destino
5. Evidencia documental (fuente o cita)
6. Revisión ontológica de nodos

## Comandos

```bash
# Menú principal
python3 -m pipeline.cli.menu

# Tests
pytest -q              # Rápido
pytest -v              # Verboso

# Frontend
npm run dev            # Desarrollo
npm run build          # Build
npm run preview        # Preview build

# Export manual
python3 scripts/export_json.py
```

## Arquitectura

```
pipeline/        → Backend Python (extracción, DB, revisión)
  core/          → Config, DB, utilidades
  extract/       → Extracción PDF → LLM
  review/        → Revisión y limpieza
  cli/           → Interfaz de menú
src/             → Frontend Vite + Cytoscape.js
libros/          → PDFs fuente (gitignored)
data/grafo.db    → SQLite (gitignored)
public/datos.json → Datos curados para producción
```
