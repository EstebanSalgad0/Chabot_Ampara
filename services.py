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
            {   # Paso 2: confirmar envío por correo y preguntar sensación
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
                    "Presión en el pecho": (
                        "📌 *Tipo de recurso:* Audio + Infografía\n"
                        "Respuesta fisiológica al estrés y cómo reducirla.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Basado en tu sensación, estos consejos pueden ayudarte "
                        "a reducir la tensión y fomentar la relajación."
                    ),
                    "Pensamiento catastrófico": (
                        "📌 *Tipo de recurso:* Ejercicio guiado + Cápsula\n"
                        "Ejercicio sobre rueda del control.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Practicarlo te ayudará a cuestionar y equilibrar tus pensamientos."
                    ),
                    "Alteraciones del sueño": (
                        "📌 *Tipo de recurso:* Audio de relajación\n"
                        "Higiene del sueño y ejercicios.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Usar este audio antes de dormir puede mejorar tu descanso."
                    ),
                    "Evitación por miedo": (
                        "📌 *Tipo de recurso:* Guía descargable\n"
                        "Exposición gradual.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Seguir esta guía te permitirá enfrentar tus miedos paso a paso."
                    ),
                    "Agotamiento mental": (
                        "📌 *Tipo de recurso:* Frases + Audio\n"
                        "Mindfulness y autocuidado.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Pequeñas pausas y prácticas de mindfulness pueden recargar tu energía."
                    )
                }.get(choice,
                    "Aquí tenés información sobre ese tema.\n"
                    "🔔 He enviado esto a tu correo.\n\n"
                    "👉 Implementar estas recomendaciones puede ayudarte."
                )
            },
            {   # Paso 4: ¿Necesitás más ayuda?
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {   # Paso 5: despedida extendida
                "prompt": (
                    "❤️ *Despedida:*\n"
                    "Gracias por usar AMPARA IA. Recuerda que lo que practiques aquí "
                    "puede acompañarte entre sesiones y fortalecer tu proceso terapéutico. "
                    "Si en algún momento necesitás más apoyo o tenés dudas, tu terapeuta "
                    "está disponible para ayudarte. ¡Cuídate y hasta la próxima!"
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
    buttons = [
        {"type":"reply","reply":{"id":f"{sedd}_btn_{i+1}","title":opt if len(opt)<=20 else opt[:20]}}
        for i,opt in enumerate(options)
    ]
    return json.dumps({
        "messaging_product":"whatsapp","recipient_type":"individual","to":number,
        "type":"interactive","interactive":{
            "type":"button","body":{"text":body},"footer":{"text":footer},
            "action":{"buttons":buttons}
        }
    })

def listReply_Message(number, options, body, footer, sedd, messageId):
    rows = [{"id":f"{sedd}_row_{i+1}","title":opt if len(opt)<=24 else opt[:24],"description":""}
            for i,opt in enumerate(options)]
    return json.dumps({
        "messaging_product":"whatsapp","recipient_type":"individual","to":number,
        "type":"interactive","interactive":{
            "type":"list","body":{"text":body},"footer":{"text":footer},
            "action":{"button":"Seleccionar","sections":[{"title":footer,"rows":rows}]}
        }
    })

def markRead_Message(mid):
    return json.dumps({"messaging_product":"whatsapp","status":"read","message_id":mid})

def replyReaction_Message(number, mid, emoji):
    return json.dumps({
        "messaging_product":"whatsapp","recipient_type":"individual",
        "to":number,"type":"reaction","reaction":{"message_id":mid,"emoji":emoji}
    })

# ----------------------------------------
# Dispatcher de flujos
# ----------------------------------------
def dispatch_flow(number, messageId, text, topic):
    cfg = session_states.get(number)
    if not cfg:
        session_states[number] = {"topic":topic,"step":0}
        cfg = session_states[number]

    step  = cfg["step"]
    steps = FLOWS[topic]["steps"]

    # Paso 0 → enviamos prompt libre
    if step == 0:
        cfg["step"] = 1
        return enviar_Mensaje_whatsapp(text_Message(number, steps[0]["prompt"]))

    # Paso 1 → keywords y Sí/No
    if step == 1:
        cfg["last_input"] = text.lower()
        cnt = sum(bool(re.search(rf"\b{re.escape(kw)}\b", cfg["last_input"], re.IGNORECASE))
                  for kw in TOPIC_KEYWORDS[topic])
        if cnt < 1:
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(
                number,
                "No detecté síntomas claros de ansiedad.\nPodés describir más o consultar un profesional."
            ))
        cfg["step"] = 2
        return enviar_Mensaje_whatsapp(
            buttonReply_Message(number, steps[1]["options"], steps[1]["prompt"],
                                topic.capitalize(), f"{topic}_confirm", messageId)
        )

    # Paso 2 → “No” termina, “Sí” avanza a lista
    if step == 2:
        if text.endswith("_btn_2"):
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(number, "¡Gracias por usar AMPARA!"))
        cfg["step"] = 3
        return enviar_Mensaje_whatsapp(
            listReply_Message(number, steps[2]["options"], steps[2]["prompt"],
                              topic.capitalize(), f"{topic}_sens", messageId)
        )

    # Paso 3 → entrega contenido y preguntamos más ayuda
    if step == 3:
        idx = int(text.split("_")[-1]) - 1
        sel = steps[2]["options"][idx]
        cont = steps[3]["content_fn"](sel)
        enviar_Mensaje_whatsapp(text_Message(number, cont))
        cfg["step"] = 4
        return enviar_Mensaje_whatsapp(
            buttonReply_Message(number, ["Sí","No"], "¿Necesitás más ayuda?", "AMPARA IA",
                                f"{topic}_more", messageId)
        )

    # Paso 4 → si “Sí”, al menú; si “No”, despedida
    if step == 4:
        if text.endswith("_btn_1"):
            session_states.pop(number)
            menu = (
                "¿Qué deseas hacer?\n"
                "1. Psicoeducación Interactiva\n"
                "2. Informe al Terapeuta\n"
                "3. Recordatorios Terapéuticos"
            )
            return enviar_Mensaje_whatsapp(
                buttonReply_Message(number, MICROSERVICES, menu, "AMPARA IA",
                                    "main_menu", messageId)
            )
        # “No”
        session_states.pop(number)
        return enviar_Mensaje_whatsapp(text_Message(number, steps[5]["prompt"]))

# ----------------------------------------
# Dispatcher principal
# ----------------------------------------
def administrar_chatbot(text, number, messageId, name):
    enviar_Mensaje_whatsapp(markRead_Message(messageId))
    enviar_Mensaje_whatsapp(replyReaction_Message(number, messageId, "🧠"))
    time.sleep(random.uniform(0.3, 0.7))

    txt = text.strip().lower()
    # Saludo y menú inicial
    if txt in ['hola','buenos días','buenas tardes','buenas noches']:
        body = (
            f"¡Hola {name}! Soy *AMPARA IA*, tu asistente virtual.\n"
            "¿Qué deseas hacer?\n"
            "1. Psicoeducación Interactiva\n"
            "2. Informe al Terapeuta\n"
            "3. Recordatorios Terapéuticos"
        )
        return enviar_Mensaje_whatsapp(
            buttonReply_Message(number, MICROSERVICES, body, "AMPARA IA",
                                "main_menu", messageId)
        )

    if text == "main_menu_btn_1":
        return dispatch_flow(number, messageId, "", "ansiedad")

    if number in session_states:
        topic = session_states[number]["topic"]
        return dispatch_flow(number, messageId, text, topic)

    return enviar_Mensaje_whatsapp(
        text_Message(number, "No entendí. Escribí 'hola' para volver al menú.")
    )
