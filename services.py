# services_ampara.py

import requests
import sett
import json
import time
import random

# ----------------------------------------
# Estado global para sesiones AMPARA
# ----------------------------------------
# Cada sesión almacena: topic (str), step (int), last_choice (str)
session_states = {}

# ----------------------------------------
# Definición de flujos de psicoeducación
# ----------------------------------------
FLOWS = {
    "ansiedad": {
        "steps": [
            {  # Paso 0: Entrada libre
                "type": "text",
                "prompt": (
                    "*Tema: Ansiedad*\n\n"
                    "🟢 Entrada libre (en contexto terapéutico):\n"
                    "(Cuéntame con tus palabras cómo te sientes)"
                )
            },
            {  # Paso 1: Extracción y ejemplo
                "type": "text",
                "prompt": lambda state: (
                    "🌱 Extracción de temas:\n\n" +
                    " • ".join([
                        "Preocupación anticipatoria excesiva",
                        "Síntomas físicos persistentes",
                        "Alteraciones del sueño",
                        "Evitación por miedo",
                        "Agotamiento mental"
                    ]) +
                    "\n\n🌿 Ejemplo integrador:\n"
                    "AMPARA IA: Lo que describes puede estar relacionado con estados de ansiedad. "
                    "¿Te gustaría revisar contenidos?"
                )
            },
            {  # Paso 2: Selección de módulo
                "type": "button",
                "prompt": "¿Qué quieres trabajar hoy?",
                "options": [
                    "¿Por qué lo siento si no hay peligro?",
                    "¿Cómo calmar el cuerpo?",
                    "¿Cómo manejar pensamientos?",
                    "¿Cómo explicarlo a un cercano?",
                    "Ejercicio breve"
                ]
            },
            {  # Paso 3: Entrega de contenido
                "type": "text",
                "content_fn": lambda choice: {
                    "¿Por qué lo siento si no hay peligro?":
                        "La ansiedad aparece cuando la señal de alerta se activa sin peligro real...",
                    "¿Cómo calmar el cuerpo?":
                        "Prueba la respiración 4-7-8: inhala 4s, mantén 7s, exhala 8s...",
                    "¿Cómo manejar pensamientos?":
                        "Identifica pensamientos automáticos y ponlos a prueba...",
                    "¿Cómo explicarlo a un cercano?":
                        "Usa lenguaje sencillo: \"Mi cuerpo reacciona porque percibe amenaza\"...",
                    "Ejercicio breve":
                        "Te envío un ejercicio breve de atención plena de 1 minuto..."
                }.get(choice, "Aquí tienes información sobre ese tema.")
            },
            {  # Paso 4: Cierre
                "type": "text",
                "prompt": (
                    "✅ Cierre:\n"
                    "Lo que sientes es señal de que tu cuerpo necesita sentirse seguro. "
                    "¿Quieres una cápsula para esta semana?"
                )
            }
        ]
    }
}

# ----------------------------------------
# Constantes del menú principal
# ----------------------------------------
MICROSERVICES = [
    "Psicoeducación Interactiva",
    "Informe al Terapeuta",
    "Recordatorios Terapéuticos"
]

# ----------------------------------------
# Helpers de WhatsApp
# ----------------------------------------
def obtener_Mensaje_whatsapp(message):
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
    return resp

def text_Message(number, text):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {"body": text}
    })

def buttonReply_Message(number, options, body, footer, sedd, messageId):
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
            "action": {"button": "Ver Opciones", "sections": [{"title": "Secciones", "rows": rows}]}
        }
    })

def replyReaction_Message(number, messageId, emoji):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "reaction",
        "reaction": {"message_id": messageId, "emoji": emoji}
    })

def markRead_Message(messageId):
    return json.dumps({
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": messageId
    })

# ----------------------------------------
# Manejador genérico de flujos
# ----------------------------------------
def dispatch_flow(number, messageId, text, topic):
    cfg = session_states.get(number)
    if not cfg:
        session_states[number] = {"topic": topic, "step": 0, "last_choice": None}
        cfg = session_states[number]
    flow_steps = FLOWS[topic]["steps"]
    step = cfg["step"]
    current = flow_steps[step]

    # Determinar y enviar mensaje según tipo
    if current["type"] == "text":
        # prompt estático o dinámico
        prompt = current.get("prompt")
        if callable(prompt):
            prompt = prompt(cfg)
        # si es entrega de contenido
        if "content_fn" in current:
            prompt = current["content_fn"](cfg["last_choice"])
        enviar_Mensaje_whatsapp(text_Message(number, prompt))

    elif current["type"] == "button":
        enviar_Mensaje_whatsapp(buttonReply_Message(
            number,
            current["options"],
            current["prompt"],
            topic.capitalize(),
            f"{topic}_step",
            messageId
        ))
        cfg["last_choice"] = text  # guardamos la elección

    # Avanzar paso
    cfg["step"] += 1
    # Si se completó el flujo, limpiar estado
    if cfg["step"] >= len(flow_steps):
        session_states.pop(number, None)

# ----------------------------------------
# Dispatcher principal
# ----------------------------------------
def administrar_chatbot(text, number, messageId, name):
    # 1) Marca leído y reacciona
    enviar_Mensaje_whatsapp(markRead_Message(messageId))
    enviar_Mensaje_whatsapp(replyReaction_Message(number, messageId, "🧠"))
    time.sleep(random.uniform(0.4, 1.0))

    txt = text.strip().lower()
    # 2) Saludo y menú principal
    if txt in ['hola', 'buenos días', 'buenas tardes', 'buenas noches']:
        body = (
            f"¡Hola {name}! Soy *AMPARA IA*, tu asistente virtual. ¿Qué deseas hacer?\n\n"
            "1. Psicoeducación Interactiva\n"
            "2. Informe al Terapeuta\n"
            "3. Recordatorios Terapéuticos"
        )
        enviar_Mensaje_whatsapp(buttonReply_Message(
            number, MICROSERVICES, body, "AMPARA IA", "main_menu", messageId
        ))
        return

    # 3) Selección de microservicio
    if text == "main_menu_btn_1":
        dispatch_flow(number, messageId, text, "ansiedad")
        return
    if text == "main_menu_btn_2":
        enviar_Mensaje_whatsapp(text_Message(number, "🏥 Informe al Terapeuta: aquí inicia tu flujo..."))
        return
    if text == "main_menu_btn_3":
        enviar_Mensaje_whatsapp(text_Message(number, "⏰ Recordatorios Terapéuticos: aquí inicia tu flujo..."))
        return

    # 4) Continuar flujo activo
    cfg = session_states.get(number)
    if cfg:
        dispatch_flow(number, messageId, text, cfg["topic"])
        return

    # 5) Fallback
    enviar_Mensaje_whatsapp(text_Message(number, "No entendí tu opción. Escribe 'hola' para volver al menú."))
