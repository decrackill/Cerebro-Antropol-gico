---
description: Run comprehensive security review
agent: security-reviewer
subtask: true
---

# Security Command

Ejecutar revisión de seguridad: $ARGUMENTS

## Tu Tarea

1. Revisar cambios recientes con `git diff`
2. Buscar vulnerabilidades OWASP Top 10
3. Generar reporte con severidades

## Checklist

### CRITICAL
- [ ] API keys hardcodeadas
- [ ] Inyección SQL en queries
- [ ] Command injection
- [ ] Secrets en commits/logs

### HIGH
- [ ] Path traversal
- [ ] Input sin validar
- [ ] Mensajes de error con info interna

### MEDIUM
- [ ] Dependencias vulnerables
- [ ] Debug info en producción

## Reporte
```
[SEVERIDAD] Título
Archivo: ruta:línea
Problema: [descripción]
Fix: [código específico]
```
