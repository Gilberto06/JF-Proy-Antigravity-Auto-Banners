[C — CONTEXTO]
Una agencia de medios produce aproximadamente 100 campañas de autopromoción al mes. Para cada campaña se generan entre 3 y 8 formatos de banner (horizontal, vertical, cuadrado). El proceso actual consume 45 minutos por campaña: el equipo creativo selecciona manualmente los assets fotográficos, adapta los textos al espacio de cada formato y genera los banners. Esto representa 75 horas/mes en trabajo mecánico a un coste estimado de 1.875 €/mes (22.500 €/año), además del coste invisible de bloquear perfiles creativos en tareas repetitivas.

El proceso ya ha sido analizado y clasificado en 8 tareas:
- Automatizables con Make/N8N (sin criterio): entrada de datos en formulario, aprobación/rechazo por el ejecutivo, registro en Google Sheets con enlace de descarga, notificación por email.
- Requieren IA (con criterio creativo): selección de la mejor foto según el contenido del artículo, redacción de textos y CTA adaptados al tono de marca y al espacio disponible, composición del primer formato para revisión, generación del resto de formatos con reencuadre y reajuste de texto.

El equipo trabaja con ejecutivos que introducen el artículo y aprueban los resultados, y un flujo de revisión humana antes de generar todos los formatos.

[R — ROL]
Actúa como Arquitecto de Producto Senior especializado en aplicaciones de IA generativa y automatización de workflows creativos. Tienes experiencia diseñando herramientas SaaS para equipos de producción de contenido, con conocimiento profundo de flujos human-in-the-loop, integración de LLMs y pipelines de generación de imágenes.

[E — ESPECIFICACIONES]
El PRD debe cubrir obligatoriamente los siguientes bloques:

1. RESUMEN EJECUTIVO
   - Problema core, solución propuesta y propuesta de valor.

2. OBJETIVOS DEL PRODUCTO
   - OBJ-01: Reducir el tiempo de producción por campaña de 45 min a ≤10 min.
   - OBJ-02: Lograr que al menos el 75% de los banners pasen la aprobación del cliente en primera revisión.
   - OBJ-03: Recuperar las 75 horas/mes actualmente invertidas en trabajo mecánico.

3. USUARIOS Y CASOS DE USO
   - Perfil de usuario primario: ejecutivo de cuentas (no técnico).
   - Perfil de usuario secundario: supervisor creativo (aprueba resultados).
   - Casos de uso principales: creación de campaña desde artículo, revisión y aprobación, descarga de assets.

4. FLUJO FUNCIONAL DETALLADO (los 8 pasos ya clasificados)
   - Indicar para cada paso: actor responsable, tipo (automatizado / IA), input, output y herramienta sugerida (Make/N8N para automatizables, LLM/imagen IA para los que requieren criterio).

5. REQUISITOS FUNCIONALES
   - Formulario de entrada (artículo + formatos deseados).
   - Motor de selección de imagen con justificación visible al ejecutivo.
   - Generador de textos y CTA con edición inline antes de aprobar.
   - Renderizador de banners multi-formato (al menos: 1200×628, 1080×1080, 1080×1920).
   - Panel de revisión con vista previa, opción de aprobar o solicitar cambios con comentario.
   - Exportación en ZIP con nomenclatura estándar por campaña.
   - Registro automático en Google Sheets con metadatos de campaña y enlace de descarga.
   - Notificación por email a los involucrados al completar el flujo.

6. REQUISITOS NO FUNCIONALES
   - Tiempo de respuesta del sistema: generación de primer formato en ≤60 segundos.
   - Disponibilidad: 99.5% en horario laboral.
   - Seguridad: acceso por roles (ejecutivo / supervisor).
   - Escalabilidad: soportar picos de 20 campañas simultáneas.

7. MÉTRICAS DE ÉXITO (KPIs de producto)
   - Tiempo medio por campaña (objetivo ≤10 min).
   - Tasa de aprobación en primera revisión (objetivo ≥75%).
   - Horas recuperadas por mes (objetivo ≥75 h).
   - Adopción: % de campañas procesadas por la herramienta vs. proceso manual.

8. RESTRICCIONES Y SUPUESTOS
   - No debe requerir conocimiento técnico del usuario final.
   - Debe mantener los estándares de calidad visuales existentes.
   - El criterio creativo final siempre recae en el supervisor humano (human-in-the-loop obligatorio antes de generar todos los formatos).

9. DEPENDENCIAS TÉCNICAS SUGERIDAS
   - Orquestador de flujos: Make o N8N.
   - LLM para textos: GPT-4o o Claude 3.5 Sonnet.
   - Generación/composición de imagen: herramienta con API (Imagen, DALL-E, Stable Diffusion o similar con soporte de templates).
   - Almacenamiento y registro: Google Sheets + Google Drive o equivalente.

10. FUERA DE ALCANCE (v1)
    - Integración directa con plataformas de publicación de ads.
    - Personalización de plantillas de diseño por el usuario final.
    - Analítica de rendimiento de los banners publicados.

[A — ACCIÓN]
Genera un documento PRD completo, estructurado y listo para ser usado como especificación técnica de desarrollo. Usa lenguaje claro y orientado a producto. Cada sección debe ser accionable: evita descripciones genéricas y prioriza detalles que un equipo de ingeniería o una IA generadora de aplicaciones pueda implementar directamente. Incluye user stories en formato "Como [rol], quiero [acción], para [beneficio]" en la sección de casos de uso. El tono debe ser profesional, directo y sin ambigüedad.