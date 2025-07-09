import requests
import sett
import json
import time
import random
import re

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
    # Otros topics…
}

# ----------------------------------------
# Definición de flujos
# ----------------------------------------
FLOWS = {
    "ansiedad": {
        "steps": [
            {   # Paso 0: pedir descripción libre
                "prompt": (
                    "🟢 *Describí los síntomas o sensaciones* que estás experimentando.\n"
                    "(Por ejemplo: “Me cuesta respirar”, “Siento mucha tensión”, etc.)"
                )
            },
            {   # Paso 1: confirmación detección
                "prompt": (
                    "🌿 *Detección de ansiedad*\n\n"
                    "Lo que describiste coincide con patrones de *ansiedad*. "
                    "¿Querés revisar contenidos psicoeducativos sobre ansiedad?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: confirmación de envío por correo y preguntar sensación
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
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
def obtener_Mensaje_whatsapp(msg):
    t = msg.get("type")
    if t == "text":
        return msg["text"]["body"]
    if t == "button":
        return msg["button"]["text"]
    if t == "interactive":
        ip = msg["interactive"]
        if ip["type"] == "list_reply":
            return ip["list_reply"]["id"]
        if ip["type"] == "button_reply":
            return ip["button_reply"]["id"]
    return "mensaje no procesado"

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

def text_Message(number, body):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {"body": body}
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

def listReply_Message(number, options, body, footer, sedd, messageId):
    rows = []
    for i, opt in enumerate(options):
        title = opt if len(opt) <= 24 else opt[:24]
        desc  = ""  if len(opt) <= 24 else opt
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
            "body":    {"text": body},
            "footer":  {"text": footer},
            "action":  {
                "button": "Seleccionar",
                "sections": [{"title": footer, "rows": rows}]
            }
        }
    })

def markRead_Message(mid):
    return json.dumps({
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": mid
    })

def replyReaction_Message(number, mid, emoji):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "reaction",
        "reaction": {"message_id": mid, "emoji": emoji}
    })

# ----------------------------------------
# Dispatcher de flujos
# ----------------------------------------
def dispatch_flow(number, messageId, text, topic):
    cfg = session_states.get(number)
    if not cfg:
        session_states[number] = {"topic": topic, "step": 0}
        cfg = session_states[number]

    step  = cfg["step"]
    steps = FLOWS[topic]["steps"]

    # Paso 0 → enviamos prompt libre
    if step == 0:
        cfg["step"] = 1
        return enviar_Mensaje_whatsapp(text_Message(number, steps[0]["prompt"]))

    # Paso 1 → contamos keywords y desplegamos Sí/No
    if step == 1:
        cfg["last_input"] = text.lower()
        cnt = sum(
            bool(re.search(rf"\b{re.escape(kw)}\b", cfg["last_input"], re.IGNORECASE))
            for kw in TOPIC_KEYWORDS[topic]
        )
        if cnt < 1:
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(
                number,
                "No detecté síntomas claros de ansiedad.\n"
                "Podés describir más o consultar un profesional."
            ))
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

    # Paso 2 → si “No”, terminamos; si “Sí”, desplegamos lista
    if step == 2:
        if text.endswith("_btn_2"):  # “No”
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(number, "¡Gracias por usar AMPARA!"))
        # “Sí”: avanzamos a lista de sensaciones
        cfg["step"] = 3
        return enviar_Mensaje_whatsapp(
            listReply_Message(
                number,
                steps[2]["options"],
                steps[2]["prompt"],
                topic.capitalize(),
                f"{topic}_sens",
                messageId
            )
        )

    # Paso 3 → recibimos selección y entregamos contenido + cierre
    if step == 3:
        # “ansiedad_sens_row_X”
        idx = int(text.split("_")[-1]) - 1
        sel = steps[2]["options"][idx]
        cont = steps[3]["content_fn"](sel)
        enviar_Mensaje_whatsapp(text_Message(number, cont))
        cierre = steps[4]["prompt"]
        session_states.pop(number)
        return enviar_Mensaje_whatsapp(text_Message(number, cierre))

# ----------------------------------------
# Dispatcher principal
# ----------------------------------------
def administrar_chatbot(text, number, messageId, name):
    enviar_Mensaje_whatsapp(markRead_Message(messageId))
    enviar_Mensaje_whatsapp(replyReaction_Message(number, messageId, "🧠"))
    time.sleep(random.uniform(0.3, 0.7))

    txt = text.strip().lower()
    # Saludo y menú inicial
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

    # Si el usuario pulsa “Psicoeducación Interactiva”
    if text == "main_menu_btn_1":
        return dispatch_flow(number, messageId, "", "ansiedad")

    # Si hay flujo en curso, delegamos
    if number in session_states:
        topic = session_states[number]["topic"]
        return dispatch_flow(number, messageId, text, topic)

    # Fallback genérico
    return enviar_Mensaje_whatsapp(
        text_Message(number, "No entendí. Escribí 'hola' para volver al menú.")
    )
