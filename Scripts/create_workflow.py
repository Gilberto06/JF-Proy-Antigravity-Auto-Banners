#!/usr/bin/env python3
"""
Crea el workflow AutoBannersV1 en n8n vía REST API.
Ejecutar: source .env && python3 create_workflow.py
"""

import json
import os
import sys
import urllib.request
import urllib.error

# ─── Configuración ────────────────────────────────────────────────────────────
N8N_BASE_URL = os.environ.get("N8N_BASE_URL", "").rstrip("/")
N8N_API_KEY  = os.environ.get("N8N_API_KEY", "")

GOOGLE_DRIVE_CRED_ID   = "eihzq0eXVZRT939G"
GOOGLE_DRIVE_CRED_NAME = "GDrive GFWebs GFQ"

if not N8N_BASE_URL or not N8N_API_KEY:
    print("ERROR: N8N_BASE_URL y N8N_API_KEY deben estar en el entorno.")
    print("Ejecuta:  source .env && python3 create_workflow.py")
    sys.exit(1)

# ─── Código de nodos ──────────────────────────────────────────────────────────

CODE_SESSION_ROUTER = r"""
const update = $input.first().json;
const staticData = $workflow.staticData;
if (!staticData.sessions) staticData.sessions = {};

const chatId = String(
  update.message?.chat?.id ??
  update.callback_query?.from?.id ??
  'unknown'
);

const session = staticData.sessions[chatId] ?? {
  state: 'new',
  url: null,
  selectedFormats: [],
  selectorMessageId: null
};

let action = 'ignore';

if (update.callback_query) {
  const cbData = update.callback_query.data ?? '';
  if (cbData === 'fmt_confirm') {
    action = session.selectedFormats.length > 0 ? 'confirm_generate' : 'empty_formats';
  } else if (cbData === 'fmt_all') {
    action = 'toggle_format';
    session.selectedFormats = ['1080x1920', '600x600', '1280x720', '1080x1080'];
  } else if (cbData.startsWith('fmt_')) {
    action = 'toggle_format';
    const fmt = cbData.replace('fmt_', '');
    const idx = session.selectedFormats.indexOf(fmt);
    if (idx >= 0) session.selectedFormats.splice(idx, 1);
    else session.selectedFormats.push(fmt);
  }
} else if (update.message) {
  const text = update.message.text ?? '';
  if (session.state === 'waiting_formats') {
    action = 'ignore';
  } else if (text.match(/^https?:\/\//i)) {
    action = 'url_received';
    session.url = text;
    session.state = 'waiting_formats';
    session.selectedFormats = [];
  } else {
    action = 'greet';
    session.state = 'waiting_url';
  }
}

staticData.sessions[chatId] = session;

return [{ json: {
  raw: update,
  action,
  chatId,
  url: session.url,
  selectedFormats: session.selectedFormats,
  callbackQueryId: update.callback_query?.id,
  callbackMessageId: update.callback_query?.message?.message_id
}}];
""".strip()

CODE_BUILD_KEYBOARD = r"""
function buildKeyboard(selected) {
  const allFormats = ['1080x1920', '600x600', '1280x720', '1080x1080'];
  const allSelected = allFormats.every(f => selected.includes(f));
  const btn = (label, fmt) => ({
    text: selected.includes(fmt) ? `✅ ${label}` : label,
    callback_data: `fmt_${fmt}`
  });
  return {
    inline_keyboard: [
      [btn('1080x1920', '1080x1920'), btn('600x600', '600x600')],
      [btn('1280x720', '1280x720'), btn('1080x1080', '1080x1080')],
      [{ text: allSelected ? '✅ Todos los formatos' : '📦 Todos los formatos', callback_data: 'fmt_all' }],
      [{ text: '✅ Generar banners', callback_data: 'fmt_confirm' }]
    ]
  };
}

const selectedFormats = $json.selectedFormats || [];
const keyboard = buildKeyboard(selectedFormats);
return [{ json: { ...$json, keyboard: JSON.stringify(keyboard) } }];
""".strip()

CODE_TOGGLE_KEYBOARD = r"""
function buildKeyboard(selected) {
  const allFormats = ['1080x1920', '600x600', '1280x720', '1080x1080'];
  const allSelected = allFormats.every(f => selected.includes(f));
  const btn = (label, fmt) => ({
    text: selected.includes(fmt) ? `✅ ${label}` : label,
    callback_data: `fmt_${fmt}`
  });
  return {
    inline_keyboard: [
      [btn('1080x1920', '1080x1920'), btn('600x600', '600x600')],
      [btn('1280x720', '1280x720'), btn('1080x1080', '1080x1080')],
      [{ text: allSelected ? '✅ Todos los formatos' : '📦 Todos los formatos', callback_data: 'fmt_all' }],
      [{ text: '✅ Generar banners', callback_data: 'fmt_confirm' }]
    ]
  };
}

const selectedFormats = $json.selectedFormats || [];
const keyboard = buildKeyboard(selectedFormats);

const answerCbBody = JSON.stringify({
  callback_query_id: $json.callbackQueryId,
  text: ''
});

const editMarkupBody = JSON.stringify({
  chat_id: parseInt($json.chatId),
  message_id: $json.callbackMessageId,
  reply_markup: keyboard
});

return [{ json: { ...$json, keyboard: JSON.stringify(keyboard), answerCbBody, editMarkupBody } }];
""".strip()

CODE_CONFIRM = r"""
const session = $json;
const body = {
  model: 'gpt-4o-mini',
  messages: [
    {
      role: 'system',
      content: 'Eres un clasificador de intención para un servicio de generación de banners.\nDevuelve ÚNICAMENTE un JSON sin texto adicional:\n{"case_type": 1} → el usuario proporcionó una URL (con o sin imagen)\n{"case_type": 2} → el usuario proporcionó solo una imagen sin URL'
    },
    { role: 'user', content: session.url || '' }
  ],
  response_format: { type: 'json_object' }
};
const answerCbBody = JSON.stringify({
  callback_query_id: session.callbackQueryId,
  text: '⏳ Procesando...'
});
return [{ json: {
  url: session.url,
  chatId: session.chatId,
  selectedFormats: session.selectedFormats,
  callbackQueryId: session.callbackQueryId,
  openaiBody: JSON.stringify(body),
  answerCbBody
}}];
""".strip()

CODE_EXTRACT_CASE = r"""
const content = $json.choices?.[0]?.message?.content || '{"case_type": 1}';
let caseType = 1;
try { caseType = JSON.parse(content).case_type || 1; } catch(e) {}
const confData = $('Preparar Confirmación').first().json;
return [{ json: {
  case_type: caseType,
  url: confData.url,
  chatId: confData.chatId,
  selectedFormats: confData.selectedFormats
}}];
""".strip()

CODE_EXTRACT_COPY = r"""
const content = $json.choices?.[0]?.message?.content || '{}';
let copy = {};
try { copy = JSON.parse(content); } catch(e) {}
const caseData = $('Extraer Caso').first().json;
return [{ json: {
  chatId: caseData.chatId,
  selectedFormats: caseData.selectedFormats,
  image_url: copy.image_url || '',
  headline: copy.headline || '',
  subheadline: copy.subheadline || '',
  cta: copy.cta || ''
}}];
""".strip()

CODE_TIMESTAMP = r"""
const now = new Date();
const pad = n => String(n).padStart(2, '0');
const jobId = `${now.getFullYear()}${pad(now.getMonth()+1)}${pad(now.getDate())}` +
              `${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
const copyData = $('Extraer Copy').first().json;
return [{ json: {
  job_id: jobId,
  chatId: copyData.chatId,
  selectedFormats: copyData.selectedFormats,
  image_url: copyData.image_url,
  headline: copyData.headline,
  subheadline: copyData.subheadline,
  cta: copyData.cta
}}];
""".strip()

CODE_ITEMS = r"""
const tsData = $('Generar Timestamp Job').first().json;
const folderData = $('Crear Carpeta Job').first().json;

const templateMap = {
  '1080x1920': $env.PLACID_TEMPLATE_1080x1920,
  '600x600':   $env.PLACID_TEMPLATE_600x600,
  '1280x720':  $env.PLACID_TEMPLATE_1280x720,
  '1080x1080': $env.PLACID_TEMPLATE_1080x1080
};

return (tsData.selectedFormats || []).map(format => ({
  json: {
    format,
    job_id:        tsData.job_id,
    folder_id:     folderData.id,
    template_uuid: templateMap[format],
    image_url:     tsData.image_url,
    headline:      tsData.headline,
    subheadline:   tsData.subheadline,
    cta:           tsData.cta,
    chatId:        tsData.chatId
  }
}));
""".strip()

CODE_CONSOLIDATE = r"""
const items       = $input.all();
const jobId       = items[0].json.job_id;
const folderId    = items[0].json.folder_id;
const folderUrl   = `https://drive.google.com/drive/folders/${folderId}`;
const chatId      = items[0].json.chatId;
const formatsList = items.map(i => i.json.format).join(', ');
return [{ json: {
  job_id:            jobId,
  drive_folder_url:  folderUrl,
  banners_count:     items.length,
  formats_processed: formatsList,
  chatId
}}];
""".strip()

COPY_SYSTEM_PROMPT = (
    "Eres un experto en copywriting para banners publicitarios.\n"
    "A partir del contenido de una landing page genera:\n"
    "- headline: máximo 8 palabras, directo e impactante\n"
    "- subheadline: máximo 15 palabras\n"
    "- cta: texto del botón, máximo 4 palabras\n"
    "- image_url: URL de la imagen principal (busca og:image o imagen hero)\n\n"
    "Devuelve ÚNICAMENTE un JSON con estos cuatro campos. Sin texto adicional."
)

STICKY_SECURITY = (
    "⚠️ PRODUCCIÓN BLOQUEADA: este workflow no tiene autenticación activa.\n"
    "Antes del primer cliente real, implementar verificación de chat_id contra\n"
    "PostgreSQL (tabla clients, campo telegram_chat_ids).\n"
    "La demo puede ejecutarse sin autenticación bajo supervisión directa."
)

STICKY_ARCH = (
    "ℹ️ DECISIÓN DE ARQUITECTURA:\n"
    "Sesión multi-turno gestionada con $workflow.staticData (clave: chat_id).\n"
    "Persistida en la DB de n8n, sobrevive reinicios del proceso.\n"
    "No es distribuida: válida para instancia única. Para escalar, migrar a Supabase/Redis.\n"
    "Trigger único acepta 'message' + 'callback_query'. El Session Router enruta la acción."
)

STICKY_FASE2 = (
    "🔧 FASE 2: el ramal Caso 2 está estructurado pero no implementado.\n"
    "Requiere: Supabase Storage para alojar la imagen del cliente,\n"
    "URL pública accesible por Placid, y limpieza automática a las 24h."
)

STICKY_PLACID = (
    "ℹ️ Placid puede devolver status \"queued\" para renders lentos.\n"
    "En producción implementar: nodo Wait (5s) + HTTP Request de polling\n"
    "hasta status === \"finished\". El prototipo asume respuesta síncrona."
)

# ─── Definición del workflow ───────────────────────────────────────────────────
def make_switch_rule(field_expr, value, output_key, value_type="string"):
    return {
        "conditions": {
            "options": {
                "caseSensitive": True,
                "leftValue": "",
                "typeValidation": "strict",
                "version": 1
            },
            "conditions": [{
                "leftValue": field_expr,
                "rightValue": value,
                "operator": {"type": value_type, "operation": "equals"}
            }],
            "combinator": "and"
        },
        "renameOutput": True,
        "outputKey": output_key
    }

TG_CRED  = {"telegramApi":       {"id": "xEvH9i18CyTfhWXY", "name": "Telegram GFQ"}}
OAI_CRED = {"openAiApi":         {"id": "gSTdZvC64XJsl3ra", "name": "OpenAI GFWebs GFQ"}}
GM_CRED  = {"gmailOAuth2":       {"id": "gqIQxLfW3Ic0C9lE", "name": "Gmail GFWebs GFQ"}}
GD_CRED  = {"googleDriveOAuth2Api": {"id": GOOGLE_DRIVE_CRED_ID, "name": GOOGLE_DRIVE_CRED_NAME}}

workflow = {
    "name": "AutoBannersV1",
    "settings": {
        "executionOrder": "v1",
        "saveManualExecutions": True,
        "callerPolicy": "workflowsFromSameOwner",
        "errorWorkflow": ""
    },
    "staticData": None,
    "nodes": [
        # ── Trigger ──────────────────────────────────────────────────────────
        {
            "id": "tg-trigger",
            "name": "Telegram Trigger",
            "type": "n8n-nodes-base.telegramTrigger",
            "typeVersion": 1.1,
            "position": [240, 300],
            "parameters": {
                "updates": ["message", "callback_query"],
                "additionalFields": {}
            },
            "credentials": TG_CRED
        },
        # ── Session Router ────────────────────────────────────────────────────
        {
            "id": "session-router",
            "name": "Session Router",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [480, 300],
            "parameters": {"jsCode": CODE_SESSION_ROUTER}
        },
        # ── Switch: Acción ────────────────────────────────────────────────────
        {
            "id": "sw-action",
            "name": "Switch: Acción",
            "type": "n8n-nodes-base.switch",
            "typeVersion": 3,
            "position": [720, 300],
            "parameters": {
                "rules": {"values": [
                    make_switch_rule("={{ $json.action }}", "greet",            "greet"),
                    make_switch_rule("={{ $json.action }}", "url_received",     "url_received"),
                    make_switch_rule("={{ $json.action }}", "toggle_format",    "toggle_format"),
                    make_switch_rule("={{ $json.action }}", "empty_formats",    "empty_formats"),
                    make_switch_rule("={{ $json.action }}", "confirm_generate", "confirm_generate"),
                ]},
                "fallbackOutput": "none",
                "options": {}
            }
        },
        # ── Saludo ────────────────────────────────────────────────────────────
        {
            "id": "tg-greet",
            "name": "Saludo",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [960, 100],
            "parameters": {
                "chatId": "={{ $json.chatId }}",
                "text": (
                    "👋 ¡Hola! Soy el asistente de GFWebs para generación de banners.\n\n"
                    "Envíame la URL de la landing page o producto y me pondré a trabajar. 🚀"
                ),
                "additionalFields": {"appendAttribution": False}
            },
            "credentials": TG_CRED
        },
        # ── Construir Teclado (url_received) ──────────────────────────────────
        {
            "id": "code-build-kbd",
            "name": "Construir Teclado",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [960, 300],
            "parameters": {"jsCode": CODE_BUILD_KEYBOARD}
        },
        # ── Seleccionar Formatos ───────────────────────────────────────────────
        {
            "id": "tg-formats",
            "name": "Seleccionar Formatos",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [1200, 300],
            "parameters": {
                "chatId": "={{ $json.chatId }}",
                "text": (
                    "📐 Selecciona los formatos de banner que necesitas.\n"
                    "Puedes elegir uno o varios. Cuando termines pulsa ✅ Generar."
                ),
                "additionalFields": {
                    "appendAttribution": False,
                    "reply_markup": "={{ $json.keyboard }}"
                }
            },
            "credentials": TG_CRED
        },
        # ── Actualizar Teclado (toggle_format) ────────────────────────────────
        {
            "id": "code-toggle-kbd",
            "name": "Actualizar Teclado",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [960, 500],
            "parameters": {"jsCode": CODE_TOGGLE_KEYBOARD}
        },
        # ── Answer Callback Toggle ────────────────────────────────────────────
        {
            "id": "http-answer-cb",
            "name": "Answer Callback Toggle",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1200, 500],
            "parameters": {
                "method": "POST",
                "url": "=https://api.telegram.org/bot{{ $env.TELEGRAM_BOT_TOKEN }}/answerCallbackQuery",
                "sendBody": True,
                "contentType": "raw",
                "rawContentType": "application/json",
                "body": "={{ $json.answerCbBody }}",
                "options": {}
            }
        },
        # ── Editar Markup ─────────────────────────────────────────────────────
        {
            "id": "http-edit-markup",
            "name": "Editar Markup",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1440, 500],
            "parameters": {
                "method": "POST",
                "url": "=https://api.telegram.org/bot{{ $env.TELEGRAM_BOT_TOKEN }}/editMessageReplyMarkup",
                "sendBody": True,
                "contentType": "raw",
                "rawContentType": "application/json",
                "body": "={{ $('Actualizar Teclado').first().json.editMarkupBody }}",
                "options": {}
            }
        },
        # ── Answer Callback Vacío ─────────────────────────────────────────────
        {
            "id": "http-answer-empty",
            "name": "Answer Callback Vacío",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [960, 700],
            "parameters": {
                "method": "POST",
                "url": "=https://api.telegram.org/bot{{ $env.TELEGRAM_BOT_TOKEN }}/answerCallbackQuery",
                "sendBody": True,
                "contentType": "raw",
                "rawContentType": "application/json",
                "body": "={{ JSON.stringify({ callback_query_id: $json.callbackQueryId, text: '⚠️ Selecciona al menos un formato antes de continuar.', show_alert: true }) }}",
                "options": {}
            }
        },
        # ── Aviso sin Formatos ────────────────────────────────────────────────
        {
            "id": "tg-empty-warn",
            "name": "Aviso sin Formatos",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [1200, 700],
            "parameters": {
                "chatId": "={{ $('Session Router').first().json.chatId }}",
                "text": "⚠️ Selecciona al menos un formato antes de continuar.",
                "additionalFields": {"appendAttribution": False}
            },
            "credentials": TG_CRED
        },
        # ── Preparar Confirmación ─────────────────────────────────────────────
        {
            "id": "code-confirm",
            "name": "Preparar Confirmación",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [960, 900],
            "parameters": {"jsCode": CODE_CONFIRM}
        },
        # ── Answer Callback Confirmar ─────────────────────────────────────────
        {
            "id": "http-answer-confirm",
            "name": "Answer Callback Confirmar",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1200, 900],
            "parameters": {
                "method": "POST",
                "url": "=https://api.telegram.org/bot{{ $env.TELEGRAM_BOT_TOKEN }}/answerCallbackQuery",
                "sendBody": True,
                "contentType": "raw",
                "rawContentType": "application/json",
                "body": "={{ $('Preparar Confirmación').first().json.answerCbBody }}",
                "options": {}
            }
        },
        # ── Clasificar Caso ───────────────────────────────────────────────────
        {
            "id": "http-classify",
            "name": "Clasificar Caso",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1440, 900],
            "parameters": {
                "method": "POST",
                "url": "https://api.openai.com/v1/chat/completions",
                "authentication": "predefinedCredentialType",
                "nodeCredentialType": "openAiApi",
                "sendBody": True,
                "contentType": "raw",
                "rawContentType": "application/json",
                "body": "={{ $('Preparar Confirmación').first().json.openaiBody }}",
                "options": {}
            },
            "credentials": OAI_CRED
        },
        # ── Extraer Caso ──────────────────────────────────────────────────────
        {
            "id": "code-extract-case",
            "name": "Extraer Caso",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1680, 900],
            "parameters": {"jsCode": CODE_EXTRACT_CASE}
        },
        # ── Switch: Caso ──────────────────────────────────────────────────────
        {
            "id": "sw-case",
            "name": "Switch: Caso",
            "type": "n8n-nodes-base.switch",
            "typeVersion": 3,
            "position": [1920, 900],
            "parameters": {
                "rules": {"values": [
                    make_switch_rule("={{ $json.case_type }}", 1, "caso1", "number"),
                    make_switch_rule("={{ $json.case_type }}", 2, "caso2", "number"),
                ]},
                "fallbackOutput": "none",
                "options": {}
            }
        },
        # ── Firecrawl Scrape ──────────────────────────────────────────────────
        {
            "id": "http-firecrawl",
            "name": "Firecrawl Scrape",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [2160, 800],
            "parameters": {
                "method": "POST",
                "url": "https://api.firecrawl.dev/v1/scrape",
                "sendHeaders": True,
                "headerParameters": {"parameters": [
                    {"name": "Authorization", "value": "=Bearer {{ $env.FIRECRAWL_API_KEY }}"}
                ]},
                "sendBody": True,
                "contentType": "raw",
                "rawContentType": "application/json",
                "body": "={{ JSON.stringify({ url: $json.url, formats: ['markdown', 'screenshot'], onlyMainContent: true }) }}",
                "options": {}
            }
        },
        # ── Generar Copy ──────────────────────────────────────────────────────
        {
            "id": "http-copy",
            "name": "Generar Copy",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [2400, 800],
            "parameters": {
                "method": "POST",
                "url": "https://api.openai.com/v1/chat/completions",
                "authentication": "predefinedCredentialType",
                "nodeCredentialType": "openAiApi",
                "sendBody": True,
                "contentType": "raw",
                "rawContentType": "application/json",
                "body": (
                    "={{ JSON.stringify({ model: 'gpt-4o-mini', messages: ["
                    "{ role: 'system', content: " + json.dumps(COPY_SYSTEM_PROMPT) + " }, "
                    "{ role: 'user', content: ($json.data?.markdown || $json.markdown || '') }"
                    "], response_format: { type: 'json_object' } }) }}"
                ),
                "options": {}
            },
            "credentials": OAI_CRED
        },
        # ── Extraer Copy ──────────────────────────────────────────────────────
        {
            "id": "code-extract-copy",
            "name": "Extraer Copy",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [2640, 800],
            "parameters": {"jsCode": CODE_EXTRACT_COPY}
        },
        # ── Fase 2 Stub ───────────────────────────────────────────────────────
        {
            "id": "tg-fase2",
            "name": "Fase 2 Stub",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [2160, 1060],
            "parameters": {
                "chatId": "={{ $json.chatId }}",
                "text": "⚙️ La generación desde imagen propia estará disponible próximamente.",
                "additionalFields": {"appendAttribution": False}
            },
            "credentials": TG_CRED
        },
        # ── Generar Timestamp Job ─────────────────────────────────────────────
        {
            "id": "code-timestamp",
            "name": "Generar Timestamp Job",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [2880, 800],
            "parameters": {"jsCode": CODE_TIMESTAMP}
        },
        # ── Crear Carpeta Job ─────────────────────────────────────────────────
        {
            "id": "drive-folder",
            "name": "Crear Carpeta Job",
            "type": "n8n-nodes-base.googleDrive",
            "typeVersion": 3,
            "position": [3120, 800],
            "parameters": {
                "resource": "folder",
                "operation": "create",
                "name": "={{ $json.job_id }}",
                "driveId": {"__rl": True, "value": "My Drive", "mode": "list"},
                "folderId": {"__rl": True, "value": "={{ $env.GOOGLE_DRIVE_ROOT_FOLDER_ID }}", "mode": "id"},
                "options": {}
            },
            "credentials": GD_CRED
        },
        # ── Preparar Items por Formato ────────────────────────────────────────
        {
            "id": "code-items",
            "name": "Preparar Items por Formato",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [3360, 800],
            "parameters": {"jsCode": CODE_ITEMS}
        },
        # ── Placid Generar Banner ─────────────────────────────────────────────
        {
            "id": "http-placid",
            "name": "Placid Generar Banner",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [3600, 800],
            "parameters": {
                "method": "POST",
                "url": "https://api.placid.app/api/rest/images",
                "sendHeaders": True,
                "headerParameters": {"parameters": [
                    {"name": "Authorization", "value": "=Bearer {{ $env.PLACID_API_KEY }}"}
                ]},
                "sendBody": True,
                "contentType": "raw",
                "rawContentType": "application/json",
                "body": (
                    "={{ JSON.stringify({ template_uuid: $json.template_uuid, layers: {"
                    " background_image: { image: $json.image_url },"
                    " headline: { text: $json.headline },"
                    " subheadline: { text: $json.subheadline },"
                    " cta_button: { text: $json.cta }"
                    " } }) }}"
                ),
                "options": {}
            }
        },
        # ── Descargar Banner ──────────────────────────────────────────────────
        {
            "id": "http-download",
            "name": "Descargar Banner",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [3840, 800],
            "parameters": {
                "method": "GET",
                "url": "={{ $json.image_url }}",
                "options": {
                    "response": {
                        "response": {"responseFormat": "file"}
                    }
                }
            }
        },
        # ── Subir Banner a Drive ──────────────────────────────────────────────
        {
            "id": "drive-upload",
            "name": "Subir Banner a Drive",
            "type": "n8n-nodes-base.googleDrive",
            "typeVersion": 3,
            "position": [4080, 800],
            "parameters": {
                "resource": "file",
                "operation": "upload",
                "name": "=banner_{{ $('Preparar Items por Formato').item.json.format }}_{{ $('Preparar Items por Formato').item.json.job_id }}.webp",
                "driveId": {"__rl": True, "value": "My Drive", "mode": "list"},
                "folderId": {"__rl": True, "value": "={{ $('Preparar Items por Formato').item.json.folder_id }}", "mode": "id"},
                "inputDataFieldName": "data",
                "options": {}
            },
            "credentials": GD_CRED
        },
        # ── Consolidar Resultados ─────────────────────────────────────────────
        {
            "id": "code-consolidate",
            "name": "Consolidar Resultados",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [4320, 800],
            "parameters": {
                "mode": "runOnceForAllItems",
                "jsCode": CODE_CONSOLIDATE
            }
        },
        # ── Email Notificación ────────────────────────────────────────────────
        {
            "id": "gmail-notify",
            "name": "Email Notificación",
            "type": "n8n-nodes-base.gmail",
            "typeVersion": 2,
            "position": [4560, 800],
            "parameters": {
                "sendTo": "gilberto@gfwebs.com",
                "subject": "=✅ Banners generados — Job {{ $json.job_id }}",
                "emailType": "html",
                "message": (
                    "=<h2>Banners generados correctamente</h2>"
                    "<p><strong>Job ID:</strong> {{ $json.job_id }}</p>"
                    "<p><strong>Formatos:</strong> {{ $json.formats_processed }}</p>"
                    "<p><strong>Total banners:</strong> {{ $json.banners_count }}</p>"
                    "<p><a href=\"{{ $json.drive_folder_url }}\">📁 Ver carpeta en Google Drive</a></p>"
                    "<hr>"
                    "<p style=\"color:#888;font-size:12px;\">GFWebs Banner Automation Service — AutoBannersV1</p>"
                ),
                "options": {}
            },
            "credentials": GM_CRED
        },
        # ── Respuesta Final ───────────────────────────────────────────────────
        {
            "id": "tg-final",
            "name": "Respuesta Final",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [4800, 800],
            "parameters": {
                "chatId": "={{ $json.chatId }}",
                "text": (
                    "=✅ ¡Tus banners están listos!\n\n"
                    "📁 Ver en Drive: {{ $json.drive_folder_url }}\n"
                    "🗂 Job ID: {{ $json.job_id }}\n\n"
                    "Formatos generados: {{ $json.formats_processed }}\n"
                    "Total: {{ $json.banners_count }} banners\n\n"
                    "También te hemos enviado un email de confirmación a gilberto@gfwebs.com 📧"
                ),
                "additionalFields": {"appendAttribution": False}
            },
            "credentials": TG_CRED
        },
        # ── Sticky Notes ──────────────────────────────────────────────────────
        {
            "id": "sticky-seg",
            "name": "🔴 SEGURIDAD — Autenticación pendiente",
            "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1,
            "position": [240, 560],
            "parameters": {"content": STICKY_SECURITY, "height": 180, "width": 420, "color": 3}
        },
        {
            "id": "sticky-arch",
            "name": "🟡 ARQUITECTURA — Conversación multi-turno",
            "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1,
            "position": [720, 560],
            "parameters": {"content": STICKY_ARCH, "height": 180, "width": 460, "color": 4}
        },
        {
            "id": "sticky-fase2",
            "name": "🔵 FASE 2 — Caso 2 (imagen propia)",
            "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1,
            "position": [2160, 1260],
            "parameters": {"content": STICKY_FASE2, "height": 140, "width": 420, "color": 2}
        },
        {
            "id": "sticky-placid",
            "name": "🟢 FASE 2 — Placid polling",
            "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1,
            "position": [3600, 1020],
            "parameters": {"content": STICKY_PLACID, "height": 140, "width": 420, "color": 5}
        },
    ],

    # ─── Conexiones ──────────────────────────────────────────────────────────
    "connections": {
        "Telegram Trigger": {
            "main": [[{"node": "Session Router", "type": "main", "index": 0}]]
        },
        "Session Router": {
            "main": [[{"node": "Switch: Acción", "type": "main", "index": 0}]]
        },
        "Switch: Acción": {
            "main": [
                [{"node": "Saludo",                  "type": "main", "index": 0}],
                [{"node": "Construir Teclado",        "type": "main", "index": 0}],
                [{"node": "Actualizar Teclado",       "type": "main", "index": 0}],
                [{"node": "Answer Callback Vacío",    "type": "main", "index": 0}],
                [{"node": "Preparar Confirmación",    "type": "main", "index": 0}],
            ]
        },
        "Construir Teclado": {
            "main": [[{"node": "Seleccionar Formatos", "type": "main", "index": 0}]]
        },
        "Actualizar Teclado": {
            "main": [[{"node": "Answer Callback Toggle", "type": "main", "index": 0}]]
        },
        "Answer Callback Toggle": {
            "main": [[{"node": "Editar Markup", "type": "main", "index": 0}]]
        },
        "Answer Callback Vacío": {
            "main": [[{"node": "Aviso sin Formatos", "type": "main", "index": 0}]]
        },
        "Preparar Confirmación": {
            "main": [[{"node": "Answer Callback Confirmar", "type": "main", "index": 0}]]
        },
        "Answer Callback Confirmar": {
            "main": [[{"node": "Clasificar Caso", "type": "main", "index": 0}]]
        },
        "Clasificar Caso": {
            "main": [[{"node": "Extraer Caso", "type": "main", "index": 0}]]
        },
        "Extraer Caso": {
            "main": [[{"node": "Switch: Caso", "type": "main", "index": 0}]]
        },
        "Switch: Caso": {
            "main": [
                [{"node": "Firecrawl Scrape", "type": "main", "index": 0}],
                [{"node": "Fase 2 Stub",      "type": "main", "index": 0}],
            ]
        },
        "Firecrawl Scrape": {
            "main": [[{"node": "Generar Copy", "type": "main", "index": 0}]]
        },
        "Generar Copy": {
            "main": [[{"node": "Extraer Copy", "type": "main", "index": 0}]]
        },
        "Extraer Copy": {
            "main": [[{"node": "Generar Timestamp Job", "type": "main", "index": 0}]]
        },
        "Generar Timestamp Job": {
            "main": [[{"node": "Crear Carpeta Job", "type": "main", "index": 0}]]
        },
        "Crear Carpeta Job": {
            "main": [[{"node": "Preparar Items por Formato", "type": "main", "index": 0}]]
        },
        "Preparar Items por Formato": {
            "main": [[{"node": "Placid Generar Banner", "type": "main", "index": 0}]]
        },
        "Placid Generar Banner": {
            "main": [[{"node": "Descargar Banner", "type": "main", "index": 0}]]
        },
        "Descargar Banner": {
            "main": [[{"node": "Subir Banner a Drive", "type": "main", "index": 0}]]
        },
        "Subir Banner a Drive": {
            "main": [[{"node": "Consolidar Resultados", "type": "main", "index": 0}]]
        },
        "Consolidar Resultados": {
            "main": [[{"node": "Email Notificación", "type": "main", "index": 0}]]
        },
        "Email Notificación": {
            "main": [[{"node": "Respuesta Final", "type": "main", "index": 0}]]
        },
    }
}

# ─── Despliegue ───────────────────────────────────────────────────────────────
payload = json.dumps(workflow).encode("utf-8")
url = f"{N8N_BASE_URL}/api/v1/workflows"
req = urllib.request.Request(
    url,
    data=payload,
    headers={
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json"
    },
    method="POST"
)

print(f"POST {url}")
try:
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read())
        wf_id = body["id"]
        print(f"\n✅ Workflow creado: {wf_id}")
        print(f"   URL:    {N8N_BASE_URL}/workflow/{wf_id}")
        print(f"   Nombre: {body['name']}")
        print(f"   Activo: {body['active']}")
        print(f"\nNodos creados ({len(workflow['nodes'])}):")
        for n in workflow["nodes"]:
            t = n["type"].replace("n8n-nodes-base.", "")
            print(f"  - {n['name']} [{t} v{n['typeVersion']}]")
        print("\n⚠️  PENDIENTE antes de activar:")
        print("  1. Configurar env vars en el servidor n8n (TELEGRAM_BOT_TOKEN,")
        print("     OPENAI_API_KEY, FIRECRAWL_API_KEY, PLACID_API_KEY,")
        print("     PLACID_TEMPLATE_*, GOOGLE_DRIVE_ROOT_FOLDER_ID)")
        print("  2. Verificar nombres de capas en templates de Placid:")
        print("     background_image, headline, subheadline, cta_button")
except urllib.error.HTTPError as e:
    err = e.read().decode()
    print(f"❌ HTTP {e.code}: {err}")
    sys.exit(1)
