# Documento de Requisitos del Producto (PRD)

## Sistema de Generación Automatizada de Banners Creativos (GenBanner IA)
**Versión:** 1.0 (MVP Operacional)  
**Fecha:** Mayo 2026  
**Autor:** Arquitecto de Producto Senior  
**Estado:** Listo para Revisión Técnica  

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Objetivos del Producto y Métricas de Éxito](#2-objetivos-del-producto-y-métricas-de-éxito)
3. [Usuarios, Roles y Casos de Uso](#3-usuarios-roles-y-casos-de-uso)
4. [Flujo Funcional Detallado](#4-flujo-funcional-detallado)
5. [Requerimientos Funcionales](#5-requerimientos-funcionales)
6. [Requerimientos No Funcionales](#6-requerimientos-no-funcionales)
7. [Arquitectura y Dependencias Técnicas Sugeridas](#7-arquitectura-y-dependencias-técnicas-sugeridas)
8. [Restricciones y Supuestos](#8-restricciones-y-supuestos)
9. [Fuera de Alcance (v1.0)](#9-fuera-de-alcance-v10)
10. [Glosario](#10-glosario)

---

## 1. Resumen Ejecutivo

### Problema Core
La agencia de medios produce ~100 campañas de autopromoción al mes. Cada campaña requiere entre 3 y 8 formatos de banner (horizontal, vertical, cuadrado). Actualmente, el equipo creativo realiza este proceso de forma 100% manual (selección de assets, adaptación de copys a los contenedores y reescalado de formatos). Este flujo artesanal consume **45 minutos por campaña**, traduciéndose en **75 horas/mes** de trabajo puramente mecánico, un coste operativo directo de **1.875 €/mes (22.500 €/año)** y el bloqueo de perfiles creativos en tareas repetitivas de nulo valor añadido.

### Solución Propuesta
**GenBanner IA** es una plataforma web interna *Human-in-the-Loop* que combina la automatización lógica de workflows con Inteligencia Artificial Generativa (LLMs y APIs de procesamiento de imágenes). El sistema ingiere un artículo base, selecciona los assets fotográficos óptimos mediante visión artificial, redacta copys adaptados al tono de marca/espacio, y renderiza automáticamente las variantes de banners necesarias.

### Propuesta de Valor
Eliminar el trabajo mecánico de maquetación y adaptación multiformato. La IA asume la ejecución del borrador inicial y el reescalado, mientras que el equipo humano retiene el control de calidad, la edición fina y la aprobación estratégica.

---

## 2. Objetivos del Producto y Métricas de Éxito

| ID | Objetivo del Producto | Métrica de Éxito (KPI) | Línea Base (Actual) | Impacto Esperado |
|---|---|---|---|---|
| **OBJ-01** | Reducir drásticamente el tiempo de producción por campaña. | Tiempo medio de extremo a extremo por campaña. | 45 minutos | **≤ 10 minutos** |
| **OBJ-02** | Garantizar la calidad y alineación creativa del sistema. | Tasa de aprobación del supervisor en la primera revisión. | N/A (Manual) | **≥ 75% de aprobación** |
| **OBJ-03** | Minimizar el coste operativo de tareas mecánicas. | Horas mensuales dedicadas a la adaptación de formatos. | 75 horas / mes | **0 horas mecánicas** (reasignadas a estrategia) |
| **OBJ-04** | Asegurar la adopción interna de la herramienta. | % de campañas mensuales procesadas a través del sistema. | 0% | **≥ 90% de las campañas** |

---

## 3. Usuarios, Roles y Casos de Uso

### 3.1 Matriz de Roles y Permisos

| Acción dentro de GenBanner IA | Ejecutivo de Cuentas | Supervisor Creativo |
|--------|:---:|:---:|
| Ingestar artículo y solicitar campaña | ✅ | ❌ |
| Editar copys y CTAs generados por IA en el borrador | ✅ | ✅ |
| Visualizar justificación creativa de la imagen | ✅ | ✅ |
| Aprobar borrador inicial para mutación de formatos | ❌ | ✅ |
| Rechazar borrador con comentarios de ajuste | ❌ | ✅ |
| Descargar paquete ZIP definitivo de banners | ✅ | ✅ |
| Visualizar logs de campaña en Google Sheets | ✅ | ✅ |

### 3.2 Historias de Usuario (User Stories)

#### Como Ejecutivo de Cuentas...
* **US-01:** *Como* Ejecutivo de Cuentas, *quiero* introducir la URL o texto de un artículo y seleccionar los formatos requeridos en un formulario simple, *para* iniciar la solicitud de una campaña sin depender de conocimientos técnicos ni de diseño.
* **US-02:** *Como* Ejecutivo de Cuentas, *quiero* revisar y editar inline los textos y CTAs propuestos por la IA antes de enviarlos a revisión, *para* corregir manualmente imprecisiones de datos o ajustar el enfoque comercial rápidamente.

#### Como Supervisor Creativo...
* **US-03:** *Como* Supervisor Creativo, *quiero* visualizar el primer formato maquetado junto con la justificación de la IA sobre la foto elegida, *para* validar si el concepto visual se alinea con la dirección de arte de la agencia.
* **US-04:** *Como* Supervisor Creativo, *quiero* aprobar el diseño base con un solo clic *para* que el sistema dispare la generación en lote de los 7 formatos restantes de forma automática, o rechazarlo añadiendo un comentario de cambio.

---

## 4. Flujo Funcional Detallado

El flujo consta de las 8 tareas identificadas, estructuradas de forma secuencial bajo el paradigma *Human-in-the-Loop*:

[Paso 1: Formulario] ──> [Paso 2: Selección Foto (IA)] ──> [Paso 3: Redacción Textos (IA)]
│
▼
[Paso 5: Revisión Humana] <── [Paso 4: Composición 1º Formato (IA)] ◄┘
│
├─── [Rechazado] ──> Volver al Paso 3 (con feedback)
│
└─── [Aprobado] ──> [Paso 6: Mutación Formatos (IA)] ──> [Paso 7: Registro] ──> [Paso 8: Email]

### Tabla de Especificación del Workflow

| Paso | Nombre de la Tarea | Actor Responsable | Tipo | Inputs | Outputs | Herramienta Sugerida |
|---|---|---|---|---|---|---|
| **1** | Entrada de datos de campaña | Ejecutivo de Cuentas | Automatizado | Texto/URL del artículo + Formatos requeridos (Checkboxes). | Payload JSON con los datos base de la campaña. | Formulario Web (Next.js) -> webhook a N8N. |
| **2** | Selección inteligente de imagen | Motor de IA | IA (Con criterio) | Texto del artículo + Repositorio/DAM de fotos de la agencia. | ID de la imagen óptima + Texto de justificación creativa. | LLM con Visión (GPT-4o) o embeddings vectoriales de imágenes. |
| **3** | Generación de Copys y CTAs | Motor de IA | IA (Con criterio) | Texto del artículo + Restricciones de caracteres por formato. | 3 opciones de titular corto, cuerpo y CTA adaptados. | OpenAI API (GPT-4o) / Anthropic (Claude 3.5 Sonnet). |
| **4** | Composición del primer formato base | Motor de IA / Render | IA (Con criterio) | Imagen elegida (Paso 2) + Copy seleccionado (Paso 3) + Plantilla. | URL de vista previa del primer banner (ej. 1200×628). | API de Composición de Imágenes (Bannerbear / Placid). |
| **5** | Revisión y Validation Humana | Supervisor Creativo | **Human-in-the-Loop** | Vista previa del formato base + Justificación de imagen + Input de edición. | **Aprobación** (Dispara paso 6) o **Rechazo** (Ajuste manual/re-generación). | Interfaz UI de la aplicación web (Next.js). |
| **6** | Mutación automática multiformato | Motor de IA / Render | IA (Con criterio) | Assets aprobados en Paso 5 + Listado de formatos adicionales. | Archivos de imagen individuales redimensionados y reencuadrados. | API de Composición (Bannerbear / Placid) con auto-layout. |
| **7** | Registro de campaña y empaquetado | Orquestador | Automatizado | Banners finales (Paso 6) + Metadatos de la campaña. | Archivo `.zip` en Drive + Fila insertada en Google Sheets con links. | Nodo Google Drive/Sheets en N8N / Make. |
| **8** | Notificación de cierre de entrega | Orquestador | Automatizado | Email del Ejecutivo + Link de descarga. | Correo electrónico con confirmación y enlace directo al ZIP. | Nodo Gmail / SendGrid en N8N o Make. |

---

## 5. Requerimientos Funcionales

### RF-01: Módulo de Ingesta y Formulario de Entrada
* **RF-01.1:** El sistema dispondrá de un campo de entrada para texto plano o extracción automática de contenido mediante URL del artículo.
* **RF-01.2:** Interfaz interactiva mediante componentes tipo *checkbox* para seleccionar los formatos de salida requeridos (mínimo obligatorio: Horizontal 1200×628, Cuadrado 1080×1080, Vertical 1080×1920).

### RF-02: Motor de Selección de Imagen (IA Visual)
* **RF-02.1:** El sistema analizará semánticamente el artículo e identificará las entidades y conceptos clave.
* **RF-02.2:** Cruzará dicho análisis con el banco de imágenes de la agencia para seleccionar el asset más idóneo.
* **RF-02.3:** Expondrá obligatoriamente en la interfaz un bloque de texto titulado `"Justificación Creativa de la IA"`, donde detallará los motivos de la elección de esa imagen específica frente al contenido del texto.

### RF-03: Generador de Copys y Edición Inline
* **RF-03.1:** El LLM generará variantes de textos optimizados (Titular, Subtítulo, CTA) limitando la longitud de caracteres según restricciones físicas del diseño.
* **RF-03.2:** La interfaz presentará campos de texto editables (*inputs/textareas*) prellenados con la propuesta de la IA. El Ejecutivo de Cuentas podrá reescribir cualquier campo directamente sobre la pantalla antes de consolidar el borrador.

### RF-04: Panel de Revisión Avanzada (Human-in-the-Loop)
* **RF-04.1:** Bloqueo estricto de workflow: El sistema no podrá iniciar la generación en lote de los formatos adicionales (Paso 6) hasta que el Supervisor Creativo emita una aprobación explícita sobre el formato base.
* **RF-04.2:** El panel contará con un botón de "Aprobar y Renderizar Todo" y un botón de "Rechazar / Solicitar Cambios". Al presionar este último, se desplegará obligatoriamente un cuadro de comentarios para retroalimentar al sistema o al ejecutivo.

### RF-05: Renderizador Multi-Formato y Manejo de Layouts
* **RF-05.1:** El backend se conectará con la API de renderizado para inyectar dinámicamente los textos finales y la imagen validada en las capas correspondientes de las plantillas preconfiguradas.
* **RF-05.2:** Aplicará reglas de *smart cropping* (reencuadre inteligente centrado en el sujeto) al mutar la imagen a formatos extremos (ej. pasar de horizontal a vertical 1080×1920).

### RF-06: Consolidación, Almacenamiento y Notificaciones
* **RF-06.1:** Una vez renderizados todos los formatos, el sistema los agrupará y creará un archivo comprimido `.zip`.
* **RF-06.2:** Nomenclatura normalizada obligatoria para el archivo y los elementos internos:  
    `[AAAA-MM-DD]_[NombreCampaña]_[ID_Campaña].zip`  
    `├── 1200x628_[NombreCampaña].png`  
    `├── 1080x1080_[NombreCampaña].png`  
    `└── 1080x1920_[NombreCampaña].png`
* **RF-06.3:** El orquestador subirá el archivo a la carpeta designada de Google Drive y extraerá la URL pública de descarga.
* **RF-06.4:** El sistema añadirá una nueva fila a un libro maestro de Google Sheets persistiendo: Fecha, ID, Nombre Campaña, Ejecutivo Solicitante, Supervisor Aprobador, Cantidad de Formatos y URL de descarga del ZIP.
* **RF-06.5:** Envío automatizado de correo electrónico informando de la finalización de la campaña con formato HTML limpio y enlace directo de descarga.

---

## 6. Requerimientos No Funcionales

### RNF-01: Rendimiento y Tiempos de Respuesta
* **RNF-01.1:** El tiempo máximo para procesar el artículo, generar los copys y renderizar la vista previa del *primer formato base* (Pasos 1 al 4) debe ser **≤ 60 segundos**.
* **RNF-01.2:** El renderizado final del lote completo de banners adicionales (Paso 6) tras la aprobación humana debe ejecutarse en menos de **120 segundos**.

### RNF-02: Disponibilidad y Soporte Operativo
* **RNF-02.1:** El sistema mantendrá una disponibilidad del **99.5%** durante la ventana crítica de horario laboral de la agencia (Lunes a Viernes, 08:00 a 19:00).

### RNF-03: Seguridad y Control de Accesos
* **RNF-03.1:** Autenticación básica mediante cuenta corporativa. El sistema leerá el rol del usuario (Ejecutivo / Supervisor) desde la sesión para habilitar o deshabilitar los botones de acción del Panel de Revisión Avanzada.

### RNF-04: Escalabilidad y Concurrencia
* **RNF-04.1:** La arquitectura del orquestador de flujos debe ser capaz de gestionar picos de carga de hasta **20 campañas ejecutándose de manera simultánea** sin degradación de tiempos de respuesta ni pérdida de webhooks.

---

## 7. Arquitectura y Dependencias Técnicas Sugeridas

El stack tecnológico está seleccionado para garantizar velocidad de desarrollo (MVP) y escalabilidad modular sin necesidad de código propietario pesado para el renderizado gráfico.

* **Frontend Aplicación Web:** Next.js (App Router) + Tailwind CSS. Proporciona la interfaz de usuario para formularios, edición inline y el panel de aprobación para los supervisores.
* **Orquestación de Workflows:** **N8N** (o en su defecto Make) autohospedado o Cloud. Actúa como el motor de enrutamiento que recibe los webhooks del frontend, realiza las llamadas consecutivas a las APIs de IA, gestiona los condicionales lógicos de aprobación/rechazo y conecta con las herramientas de Google.
* **Procesamiento de Lenguaje Natural (LLM):** **GPT-4o** de OpenAI o **Claude 3.5 Sonnet** de Anthropic (consumidos vía API). Encargados de la lectura comprensiva del artículo, la redacción de los copys bajo parámetros de longitud (*max_tokens* o *system prompts* estrictos) y la generación del JSON de justificación de imagen.
* **Capa de Diseño y Renderizado Gráfico:** **Bannerbear** o **Placid.app** vía API. Estas herramientas permiten diseñar plantillas maestras reutilizables directamente en una interfaz gráfica web (colocando capas de texto con ids como `titulo`, `cta`, y capas de imagen como `background`). La API recibe los textos modificados y la imagen seleccionada y devuelve los archivos PNG finales renderizados con calidad profesional instantáneamente.
* **Persistencia y Repositorio de Datos:** Sistema corporativo de Google Workspace (**Google Sheets** como base de datos ligera de control de logs y **Google Drive** para el almacenamiento de objetos de los archivos estructurados).

---

## 8. Restricciones y Supuestos

### Supuestos
1.  La agencia cuenta con un banco de imágenes corporativo (DAM/Drive) con metadatos legibles o nombres de archivo descriptivos que facilitan la indexación o búsqueda por parte del LLM.
2.  Las plantillas de diseño base (layouts horizontales, verticales y cuadrados) ya están preconfiguradas en la plataforma de renderizado gráfico (Bannerbear/Placid) con las fuentes tipográficas y logotipos corporativos fijados por el equipo de diseño global.
3.  El usuario final posee competencias digitales básicas de navegación web de nivel usuario; el sistema abstrae completamente llamadas a APIs o formatos JSON complejos.

### Restricciones
1.  **Garantía de Calidad Visual:** Ningún banner puede ser generado fuera del ecosistema de plantillas validadas previamente para evitar alteraciones accidentales de la identidad de marca (colores incorrectos, fuentes erróneas).
2.  **Control Humano Obligatorio:** El sistema restringe el bypass automático. Bajo ninguna circunstancia una campaña pasará directamente del formulario de entrada al empaquetado final sin haber cruzado la pantalla de validación del Supervisor Creativo.

---

## 9. Fuera de Alcance (v1.0)

Las siguientes características quedan explícitamente excluidas de esta versión de desarrollo y se evaluarán para el roadmap de versiones futuras (v2.0+):

* Conexión directa e inserción automatizada en plataformas de compra de anuncios externos (Meta Ads Manager, Google Ads, Twitter Ads, etc.).
* Herramienta de edición gráfica avanzada tipo lienzo (Canvas vacío) dentro de la aplicación para que el usuario mueva capas de forma libre.
* Módulo de analítica avanzada o recolección de métricas de rendimiento (CTR, impresiones) de los banners una vez publicados en los canales de destino.
* Generación de assets multimedia dinámicos adicionales, tales como formatos de video MP4, animaciones HTML5 complejas o archivos GIF animados.

---

## 10. Glosario

* **Human-in-the-Loop (HITL):** Modelo de diseño de procesos interactivos donde la Inteligencia Artificial ejecuta tareas automatizadas complejas pero requiere obligatoriamente de la intervención, revisión y validación de un operador humano antes de finalizar o consolidar el flujo de trabajo.
* **Bannerbear / Placid:** Servicios SaaS especializados que exponen una API robusta para automatizar la generación de imágenes a partir de plantillas de diseño gráfico preestablecidas, sustituyendo dinámicamente textos y fotos mediante peticiones HTTP.
* **Smart Cropping:** Algoritmo informático basado en visión artificial capaz de identificar de manera autónoma el centro de atención o el sujeto principal de una fotografía para recortar o reencuadrar el lienzo de forma coherente al cambiar entre diferentes relaciones de aspecto (ej. de formato apaisado a formato vertical de historia).
* **CTA (Call To Action):** Llamada a la acción. Elemento de texto corto y directo (ej. *"Regístrate Aquí"*, *"Saber Más"*) diseñado específicamente para incentivar al usuario final a realizar un clic sobre la pieza publicitaria.
* **Orquestador de Flujos:** Software encargado de interconectar herramientas independientes estructurando un pipeline lógico de datos. Escucha eventos, consume APIs externas, valida reglas condicionales y unifica los inputs/outputs de un ecosistema digital.