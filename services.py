# services_ampara.py

import requests
import sett
import json
import time
import random

# ----------------------------------------
# Estado global para sesiones AMPARA
# ----------------------------------------
session_states = {}
appointment_sessions = {}
medication_sessions = {}

# ----------------------------------------
# Configuración de psicoeducación y microservicios
# ----------------------------------------
PSICO_CATEGORIES = [
    "Ansiedad", "Depresión", "Autismo", "TDAH", "TLP", "TEPT",
    "Trastornos del Sueño", "Trastornos de la Conducta Alimentaria", "TOC"
]
MICROSERVICES = [
    "Psicoeducación Interactiva",
    "Informe al Terapeuta",
    "Recordatorios Terapéuticos"
]

# ----------------------------------------
# Helpers de WhatsApp
# ----------------------------------------
def obtener_Mensaje_whatsapp(message):
    """Obtiene el texto o el ID de respuesta de un mensaje de WhatsApp."""
    if 'type' not in message:
        return 'mensaje no reconocido'
    t = message['type']
    if t == 'text':
        return message['text']['body']
    if t == 'button':
        return message['button']['text']
    if t == 'interactive':
        ip = message['interactive']
        if ip['type'] == 'list_reply':
            return ip['list_reply']['id']
        if ip['type'] == 'button_reply':
            return ip['button_reply']['id']
    return 'mensaje no procesado'

def enviar_Mensaje_whatsapp(payload):
    """Envía un payload JSON a la API de WhatsApp Cloud, con debug."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {sett.WHATSAPP_TOKEN}"
    }
    print("--- Enviando JSON ---")
    try:
        print(json.dumps(json.loads(payload), indent=2, ensure_ascii=False))
    except:
        print(payload)
    print("---------------------")
    resp = requests.post(sett.WHATSAPP_URL, headers=headers, data=payload)
    if resp.status_code == 200:
        print("✅ Mensaje enviado correctamente")
    else:
        print(f"❌ Error {resp.status_code}: {resp.text}")
    return resp.text, resp.status_code

def text_Message(number, text):
    """Construye un mensaje de texto simple."""
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {"body": text}
    })

def buttonReply_Message(number, options, body, footer, sedd, messageId):
    """Construye un mensaje interactivo tipo botón, truncando títulos a 20 caracteres."""
    buttons = []
    for i, opt in enumerate(options):
        title = opt if len(opt) <= 20 else opt[:20]
        buttons.append({
            "type": "reply",
            "reply": {
                "id": f"{sedd}_btn_{i+1}",
                "title": title
            }
        })
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "footer": {"text": footer},
            "action": {"buttons": buttons}
        }
    })

def listReply_Message(number, options, body, footer, sedd, messageId):
    """Construye un mensaje interactivo tipo lista."""
    rows = []
    for i, opt in enumerate(options):
        title = opt if len(opt) <= 24 else opt[:24]
        desc = "" if len(opt) <= 24 else opt
        rows.append({
            "id": f"{sedd}_row_{i+1}",
            "title": title,
            "description": desc
        })
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body},
            "footer": {"text": footer},
            "action": {
                "button": "Ver Opciones",
                "sections": [{"title": "Secciones", "rows": rows}]
            }
        }
    })

def replyReaction_Message(number, messageId, emoji):
    """Envía una reacción (emoji) a un mensaje existente."""
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "reaction",
        "reaction": {"message_id": messageId, "emoji": emoji}
    })

def markRead_Message(messageId):
    """Marca un mensaje como leído."""
    return json.dumps({
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": messageId
    })

# ----------------------------------------
# Flujos de AMPARA
# ----------------------------------------
def start_psico(number, messageId):
    session_states[number] = {'flow': 'psico', 'step': 'select_diagnosis'}
    return listReply_Message(
        number, PSICO_CATEGORIES,
        "Selecciona el diagnóstico con el que quieres trabajar:",
        "Psicoeducación Interactiva", "psico_select", messageId
    )

def handle_psico(text, number, messageId):
    state = session_states.get(number)
    if not state or state.get('flow') != 'psico':
        return None

    step = state['step']
    if step == 'select_diagnosis':
        state['diagnosis'] = text.strip()
        state['step'] = 'input_user'
        return text_Message(number,
            f"*Tema: {state['diagnosis']}*\n\n"
            "🟢 *Entrada libre del usuario* (en contexto terapéutico):\n\n"
            "(Escribe cómo te sientes en tus propias palabras)"
        )
    if step == 'input_user':
        state['user_input'] = text.strip()
        extracted = [
            "Preocupación anticipatoria excesiva",
            "Síntomas físicos persistentes (taquicardia, tensión torácica)",
            "Alteraciones del sueño",
            "Evitación de situaciones por miedo",
            "Agotamiento mental"
        ]
        state['step'] = 'example_flow'
        return text_Message(number,
            "🌱 *Extracción de temas para reforzar en psicoeducación:*\n\n"
            + " • ".join(extracted)
            + "\n\n🌿 *Ejemplo de flujo clínico integrado*:\n\n"
            "AMPARA IA:\n"
            "Hola. Lo que describiste puede estar relacionado con estados de ansiedad. "
            "¿Te gustaría revisar algunos contenidos para reforzar lo trabajado?"
        )
    if step == 'example_flow':
        state['step'] = 'choose_content'
        options = [
            "¿Por qué siento esto si no pasa nada real?",
            "¿Cómo calmar el cuerpo cuando estoy ansioso/a?",
            "¿Cómo manejar pensamientos anticipatorios?",
            "¿Cómo explicarlo a un cercano?",
            "Ejercicio breve para practicar"
        ]
        return buttonReply_Message(
            number, options,
            "¿Qué quieres trabajar hoy?", "Guía Ansiedad",
            "psico_options", messageId
        )
    if step == 'choose_content':
        contents = {
            "¿Por qué siento esto si no pasa nada real?":
                "La ansiedad aparece cuando la señal de alerta se activa sin peligro real...",
            "¿Cómo calmar el cuerpo cuando estoy ansioso/a?":
                "Prueba la respiración 4-7-8: inhala 4s, mantén 7s, exhala 8s...",
            "¿Cómo manejar pensamientos anticipatorios?":
                "Identifica pensamientos automáticos y ponlos a prueba...",
            "¿Cómo explicarlo a un cercano?":
                "Usa lenguaje sencillo: \"Mi cuerpo reacciona porque percibe amenaza\"...",
            "Ejercicio breve para practicar":
                "Te envío un ejercicio breve de atención plena de 1 minuto..."
        }
        resp = contents.get(text, "Aquí tienes información sobre ese tema.")
        state['step'] = 'closing'
        return text_Message(number, resp)
    if step == 'closing':
        session_states.pop(number, None)
        return text_Message(number,
            "✅ *Cierre del flujo:*\n"
            "Lo que sientes es una señal de tu cuerpo. Aprender sobre ansiedad "
            "puede ayudarte a normalizar estas sensaciones. ¿Quieres una cápsula para esta semana?"
        )
    return None

def handle_informe(number, messageId):
    session_states[number] = {'flow': 'informe'}
    return text_Message(number, "🏥 Informe al Terapeuta: aquí inicia tu flujo...")

def handle_recordatorios(number, messageId):
    session_states[number] = {'flow': 'recordatorios'}
    return text_Message(number, "⏰ Recordatorios Terapéuticos: aquí inicia tu flujo...")

# ----------------------------------------
# Dispatcher principal
# ----------------------------------------
def administrar_chatbot(text, number, messageId, name):
    # 1) marcar leído y reacción
    enviar_Mensaje_whatsapp(markRead_Message(messageId))
    enviar_Mensaje_whatsapp(replyReaction_Message(number, messageId, "🧠"))
    time.sleep(random.uniform(0.4, 1.0))

    txt = text.strip().lower()
    # 2) saludo y menú
    saludos = ['hola', 'buenos días', 'buenas tardes', 'buenas noches']
    if txt in saludos:
        body = (
            f"¡Hola {name}! Soy *AMPARA IA*, tu asistente virtual. ¿Qué deseas hacer?\n\n"
            "1. Psicoeducación Interactiva\n"
            "2. Informe al Terapeuta\n"
            "3. Recordatorios Terapéuticos"
        )
        menu = buttonReply_Message(
            number, MICROSERVICES, body, "AMPARA IA", "main_menu", messageId
        )
        enviar_Mensaje_whatsapp(menu)
        return

    # 3) selección por button_reply.id
    # (En app.py extrae message['interactive']['button_reply']['id'] como btn_id)
    # Aquí asumimos que text==btn_id
    if text == "main_menu_btn_1":
        enviar_Mensaje_whatsapp(start_psico(number, messageId))
        return
    if text == "main_menu_btn_2":
        enviar_Mensaje_whatsapp(handle_informe(number, messageId))
        return
    if text == "main_menu_btn_3":
        enviar_Mensaje_whatsapp(handle_recordatorios(number, messageId))
        return

    # 4) flujos activos
    if number in session_states:
        flow = session_states[number]['flow']
        if flow == 'psico':
            resp = handle_psico(text, number, messageId)
            if resp:
                enviar_Mensaje_whatsapp(resp)
            return
        # aquí puedes manejar 'informe' y 'recordatorios'

    # 5) fallback
    enviar_Mensaje_whatsapp(text_Message(number, "No entendí tu opción. Escribe 'hola' para volver al menú."))
