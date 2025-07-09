# services.py

import requests
import sett
import json
import time
import random
import re
import os

# ----------------------------------------
# Estado global para sesiones AMPARA
# ----------------------------------------
session_states = {}

# ----------------------------------------
# Keywords para cada flujo
# ----------------------------------------
TOPIC_KEYWORDS = {
    "ansiedad": [
        "preocupación", "anticipatoria", "excesiva",
        "taquicardia", "tensión", "opresión",
        "sueño", "evitación", "miedo", "agotamiento"
    ],
    # Puedes añadir más topics aquí...
}

# ----------------------------------------
# Definición de flujos
# ----------------------------------------
FLOWS = {
    "ansiedad": {
        "steps": [
            {   # Paso 0: pedir descripción libre
                "type": "text",
                "prompt": (
                    "🟢 *Describí los síntomas o sensaciones* que estás experimentando.\n"
                    "(Por ejemplo: “Me cuesta respirar”, “Siento mucha tensión”, etc.)"
                )
            },
            {   # Paso 1: confirmación detección
                "type": "confirm",
                "prompt": (
                    "🌿 *Detección de ansiedad*\n\n"
                    "Lo que describiste coincide con patrones de *ansiedad*. "
                    "¿Querés revisar contenidos psicoeducativos sobre ansiedad?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: guardar + preguntar sensación
                "type": "text",
                "prompt": (
                    "Gracias. Guardaré tu descripción para tu terapeuta.\n"
                    "Luego descarga el archivo y envíalo a tu psicólogo.\n\n"
                    "¿Qué sensación se asemeja más a lo que describiste?"
                ),
                "options": [
                    "Presión en el pecho",
                    "Pensamiento catastrófico",
                    "Alteraciones del sueño",
                    "Evitación por miedo",
                    "Agotamiento mental"
                ]
            },
            {   # Paso 3: entregar contenido
                "type": "text",
                "content_fn": lambda choice: {
                    "Presión en el pecho":
                        "Respuesta fisiológica al estrés y cómo reducirla.\n[Audio 4-7-8 + infografía]",
                    "Pensamiento catastrófico":
                        "Ejercicio guiado y rueda del control.\n[Cápsula educativa]",
                    "Alteraciones del sueño":
                        "Higiene del sueño + ejercicios.\n[Audio relajación]",
                    "Evitación por miedo":
                        "Exposición gradual.\n[Guía descargable]",
                    "Agotamiento mental":
                        "Mindfulness y autocuidado.\n[Frases + audio]"
                }.get(choice, "Aquí tenés información sobre ese tema.")
            },
            {   # Paso 4: cierre
                "type": "text",
                "prompt": (
                    "✅ *Cierre:*\n"
                    "Estos recursos pueden ayudarte día a día.\n"
                    "¿Querés un recordatorio con esta cápsula?"
                )
            }
        ]
    }
}

# ----------------------------------------
# Menú principal
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
        "Content-Type": "application/json",
        "Authorization": f"Bearer {sett.WHATSAPP_TOKEN}"
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
            "reply": {"id": f"{sedd}_btn_{i+1}", "title": title}
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

def markRead_Message(messageId):
    return json.dumps({
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": messageId
    })

def replyReaction_Message(number, messageId, emoji):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "reaction",
        "reaction": {"message_id": messageId, "emoji": emoji}
    })

# ----------------------------------------
# Dispatcher de flujos
# ----------------------------------------
def dispatch_flow(number, messageId, text, topic):
    cfg = session_states.get(number)
    if not cfg:
        # Creamos la sesión en paso 0
        session_states[number] = {
            "topic": topic, "step": 0,
            "last_input": None, "last_choice": None
        }
        cfg = session_states[number]

    step = cfg["step"]
    steps = FLOWS[topic]["steps"]

    # Paso 0: enviamos el prompt de descripción libre
    if step == 0:
        cfg["step"] = 1
        return enviar_Mensaje_whatsapp(text_Message(number, steps[0]["prompt"]))

    # Paso 1: recibimos descripción en `text`, contamos keywords y enviamos botones
    if step == 1:
        cfg["last_input"] = text.lower()
        kws = TOPIC_KEYWORDS[topic]
        cnt = sum(
            bool(re.search(rf"\b{re.escape(kw)}\b", cfg["last_input"], re.IGNORECASE))
            for kw in kws
        )
        print(f"🔍 detectadas {cnt} keywords para '{topic}' en: {cfg['last_input']}")
        if cnt < 1:
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(
                number,
                "No detecté síntomas claros de ansiedad.\n"
                "Podés describir más o consultar a un profesional."
            ))
        # avanzamos a confirmación
        cfg["step"] = 2
        return enviar_Mensaje_whatsapp(
            buttonReply_Message(
                number,
                steps[1]["options"],
                steps[1]["prompt"],
                topic.capitalize(),
                f"{topic}_confirm",
                messageId
            )
        )

    # Paso 2: procesamos respuesta del botón (ID termina en _btn_1 o _btn_2)
    if step == 2:
        if text.endswith("_btn_2"):   # “No”
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(number, "¡Gracias por usar AMPARA!"))
        # asumimos “Sí” (_btn_1)
        cfg["step"] = 3
        return enviar_Mensaje_whatsapp(text_Message(number, steps[2]["prompt"]))

    # Paso 3: guardamos descripción y mostramos opciones de sensación
    if step == 3:
        cfg["last_input"] = text
        # escribimos archivo
        fname = f"/mnt/data/{number}_{topic}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(text)
        cfg["step"] = 4
        return enviar_Mensaje_whatsapp(
            buttonReply_Message(
                number,
                steps[2]["options"],
                steps[2]["prompt"],
                topic.capitalize(),
                f"{topic}_sens",
                messageId
            )
        )

    # Paso 4: entregamos contenido personalizado y cierre
    if step == 4:
        cfg["last_choice"] = text
        cont = steps[3]["content_fn"](text)
        enviar_Mensaje_whatsapp(text_Message(number, cont))
        cierre = steps[4]["prompt"]
        session_states.pop(number)
        return enviar_Mensaje_whatsapp(text_Message(number, cierre))

# ----------------------------------------
# Dispatcher principal
# ----------------------------------------
def administrar_chatbot(text, number, messageId, name):
    # 1) marcar leído + reacción
    enviar_Mensaje_whatsapp(markRead_Message(messageId))
    enviar_Mensaje_whatsapp(replyReaction_Message(number, messageId, "🧠"))
    time.sleep(random.uniform(0.3, 0.7))

    txt = text.strip().lower()
    # 2) saludo y menú
    if txt in ['hola', 'buenos días', 'buenas tardes', 'buenas noches']:
        body = (
            f"¡Hola {name}! Soy *AMPARA IA*, tu asistente virtual.\n"
            "¿Qué deseas hacer?\n"
            "1. Psicoeducación Interactiva\n"
            "2. Informe al Terapeuta\n"
            "3. Recordatorios Terapéuticos"
        )
        return enviar_Mensaje_whatsapp(
            buttonReply_Message(
                number,
                MICROSERVICES,
                body,
                "AMPARA IA",
                "main_menu",
                messageId
            )
        )

    # 3) selección de menú
    if text == "main_menu_btn_1":
        # arrancamos el flujo de ansiedad
        return dispatch_flow(number, messageId, "", "ansiedad")

    # 4) si ya hay sesión activa, delegamos al dispatcher
    if number in session_states:
        topic = session_states[number]["topic"]
        return dispatch_flow(number, messageId, text, topic)

    # 5) fallback
    return enviar_Mensaje_whatsapp(
        text_Message(number, "No entendí. Escribí 'hola' para volver al menú.")
    )
