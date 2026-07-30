# Cerebro Antropológico — Agentes Disponibles

| Agente | Propósito | Cuándo usarlo |
|--------|-----------|---------------|
| planner | Planificar implementación de features | Features complejas, refactors grandes |
| architect | Diseño de sistema y decisiones técnicas | Decisiones ontológicas, esquema DB, arquitectura |
| code-reviewer | Revisión de calidad y seguridad del código | Después de escribir/modificar código |
| python-reviewer | Revisión especializada de código Python | Cambios en pipeline/, scripts/ |
| security-reviewer | Detección de vulnerabilidades | Antes de commits, código sensible |
| tdd-guide | Desarrollo guiado por tests | Nuevas features, bug fixes |
| build-error-resolver | Corrección de errores de build/import | Cuando falla `python3 -m` o pytest |
| e2e-runner | Tests end-to-end con Playwright | Flujos críticos del frontend |
| database-reviewer | Optimización de esquema y consultas SQLite | Schema DB, migraciones, consultas |
| refactor-cleaner | Limpieza de código muerto y duplicados | Mantenimiento, post-limpieza |
| doc-updater | Actualización de documentación | Después de cambios en el proyecto |
| coder | Agente general de programación | Tareas de código no especializadas |
| reviewer | Code review general | Revisiones rápidas sin especialización |
| tester | Escritura de tests con pytest | Cuando hay que agregar cobertura de tests |
