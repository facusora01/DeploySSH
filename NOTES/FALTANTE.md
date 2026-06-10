# WhatsApp Integration - Decisión Final

## Decisión: WhatsApp Deshabilitado en Docker

**Fecha**: 2026-05-27  
**Razón**: Email funciona perfectamente (US-09 ✅). WhatsApp requiere infraestructura compleja en Docker.

### Intentos Realizados

1. **pywhatkit** → KeyError: 'DISPLAY' (requiere GUI)
2. **Xvfb + pywhatkit** → Chrome cierra inmediatamente  
3. **Selenium + Chrome + headless** → Session not created error
4. **Migrando whatsapp-web.js** → Arquitectura muy compleja

### Raíz del Problema

Selenium + Chrome headless en Docker requiere:
- Imagen base especializada (selenium/standalone-chrome) O
- Servicio docker-compose separado O
- Arquitectura mucho más compleja

**Costo**: 3-4 horas adicionales para configuración compleja con alto riesgo de fallos.

---

## Estado Actual

```
✅ Email:     Confirmación de cita llega al inbox
✅ Scheduler: Ejecuta cada minuto
✅ Frontend:  Permite crear citas
✅ Auth:      Login funciona
⏸️ WhatsApp:  Deshabilitado (infraestructura)
```

---

## Soluciones Viables para Implementar WhatsApp

### Opción A: Node.js Service (Recomendado)
Agregar servicio Node.js separado con whatsapp-web.js:

```yaml
services:
  whatsapp-service:
    build: ./whatsapp-service  # Node.js
    environment:
      BACKEND_URL: http://app_back:8000
  back:
    depends_on:
      - whatsapp-service
```

**Ventajas**:
- Usa whatsapp-web.js directamente (probado y confiable)
- LocalAuth guarda sesión persistente
- Python comunica vía API REST

**Tiempo**: 2-3 horas  
**Complejidad**: Media

---

### Opción B: Selenium Service Container
Agregar contenedor Selenium especializado:

```yaml
services:
  selenium:
    image: selenium/standalone-chrome:latest
  back:
    depends_on:
      - selenium
```

**Ventajas**:
- Imagen oficial de Selenium
- Ya tiene Chrome + ChromeDriver configurado
- Remote WebDriver en Python

**Tiempo**: 1-2 horas  
**Complejidad**: Baja  
**Desventaja**: Más lento (comunicación remota)

---

### Opción C: WhatsApp Business API (Producción)
Usar API oficial de WhatsApp:

```python
# Requiere:
# - Cuenta comercial WhatsApp
# - Token de acceso
# - Número de teléfono verificado
```

**Ventajas**:
- Más confiable para producción
- Soporte oficial
- Sin problemas de scraping

**Desventaja**:
- Costo por mensajes
- Requiere setup externo
- Más burocracia

**Tiempo**: 1-2 horas (si cuenta ya existe)  
**Complejidad**: Baja

---

## Recomendación

| Escenario | Opción | Por qué |
|---|---|---|
| **MVP/Testing** | B (Selenium Service) | Rápido, simple, suficiente |
| **Desarrollo** | A (Node.js Service) | Flexible, confiable |
| **Producción** | C (WhatsApp API) | Escalable, soporte oficial |

---

## Implementación Actual

Código en `backend/app/services/whatsapp.py`:
- Funciones están presentes pero retornan `False`
- Endpoints en `appointments.py` listos pero deshabilitados
- No generan errores, solo logs de info

Esto permite implementar WhatsApp después sin cambios en dependencias o arquitectura.

---

## Siguiente Paso

Hacer commit ahora con Email funcionando (US-09 ✅).  
WhatsApp queda documentado para implementación futura cuando se elija arquitectura.

Archivos listos para refactor:
- `backend/app/services/whatsapp.py` (reescribir)
- `backend/app/api/v1/appointments.py` (endpoints ya existen)
- `docker-compose.yml` (agregar servicio)
