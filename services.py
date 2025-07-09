# services_ampara.py

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
# Cada sesión: topic, step, last_choice, last_input
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
    # aquí podrías añadir otro tema:
    # "depresion": ["tristeza", "anhedonia", ...]
}

# ----------------------------------------
# Definición de flujos
# ----------------------------------------
FLOWS = {
    "ansiedad": {
        "steps": [
            {   # Paso 0: pedir descripción de síntomas
                "type": "text",
                "prompt": (
                    "🟢 *Describí los síntomas o sensaciones* que estás experimentando.\n"
                    "(Por ejemplo: “Me cuesta respirar”, “Siento mucha tensión”, etc.)"
                )
            },
            {   # Paso 1: Confirmación de detección
                "type": "confirm",
                "prompt": (
                    "🌿 *Detección de ansiedad*\n\n"
                    "Lo que describiste coincide con patrones de *ansiedad*. "
                    "¿Querés revisar contenidos psicoeducativos sobre ansiedad?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: Guardar descripción y ofrecer descarga
                "type": "text",
                "prompt": (
                    "Gracias. Guardaré tu descripción para que tu terapeuta la vea.\n"
                    "Después descarga el archivo y envíalo a tu psicólogo.\n\n"
                    "¿Qué sensación o sentimiento se asemeja más a lo que describiste?"
                ),
                "options": [
                    "Presión en el pecho",
                    "Pensamiento catastrófico",
                    "Alteraciones del sueño",
                    "Evitación por miedo",
                    "Agotamiento mental"
                ],
                "save_to_file": True
            },
            {   # Paso 3: Entrega de contenido según elección
                "type": "text",
                "content_fn": lambda choice: {
                    "Presión en el pecho":
                        "Respuesta fisiológica al estrés y cómo reducirla.\n[Audio 4-7-8 + infografía]",
                    "Pensamiento catastrófico":
                        "Ejercicio guiado y rueda del control.\n[Cápsula educativa]",
                    "Alteraciones del sueño":
                        "Higiene del sueño y ejercicios para calmar la mente.\n[Audio relajación]",
                    "Evitación por miedo":
                        "Exposición gradual a situaciones temidas.\n[Guía descargable]",
                    "Agotamiento mental":
                        "Mindfulness y autocuidado.\n[Frases de autocompasión + audio]"
                }.get(choice, "Aquí tenés información sobre ese tema.")
            },
            {   # Paso 4: Cierre
                "type": "text",
                "prompt": (
                    "✅ *Cierre:*\n"
                    "Estas herramientas pueden ayudarte a regular tu ansiedad día a día.\n"
                    "¿Querés que programe un recordatorio con esta cápsula?"
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
def enviar_Mensaje_whatsapp(payload):
    headers = {
        "Content-Type":"application/json",
        "Authorization":f"Bearer {sett.WHATSAPP_TOKEN}"
    }
    print("--- Enviando JSON ---")
    try: print(json.dumps(json.loads(payload), indent=2, ensure_ascii=False))
    except: print(payload)
    print("---------------------")
    resp = requests.post(sett.WHATSAPP_URL, headers=headers, data=payload)
    if resp.status_code==200: print("✅ Mensaje enviado correctamente")
    else: print(f"❌ Error {resp.status_code}: {resp.text}")
    return resp

def text_Message(number, text):
    return json.dumps({
        "messaging_product":"whatsapp",
        "recipient_type":"individual",
        "to":number,
        "type":"text",
        "text":{"body":text}
    })

def buttonReply_Message(number, options, body, footer, sedd, messageId):
    buttons = []
    for i,opt in enumerate(options):
        title = opt if len(opt)<=20 else opt[:20]
        buttons.append({"type":"reply","reply":{"id":f"{sedd}_btn_{i+1}","title":title}})
    return json.dumps({
        "messaging_product":"whatsapp",
        "recipient_type":"individual",
        "to":number,
        "type":"interactive",
        "interactive":{
            "type":"button",
            "body":{"text":body},
            "footer":{"text":footer},
            "action":{"buttons":buttons}
        }
    })

def markRead_Message(messageId):
    return json.dumps({
        "messaging_product":"whatsapp","status":"read","message_id":messageId
    })

def replyReaction_Message(number, messageId, emoji):
    return json.dumps({
        "messaging_product":"whatsapp",
        "recipient_type":"individual",
        "to":number,
        "type":"reaction",
        "reaction":{"message_id":messageId,"emoji":emoji}
    })

# ----------------------------------------
# Dispatcher de flujos
# ----------------------------------------
def dispatch_flow(number, messageId, text, topic):
    cfg = session_states.get(number)
    if not cfg:
        # iniciar paso 0
        session_states[number] = {"topic":topic,"step":0,"last_input":None,"last_choice":None}
        cfg = session_states[number]

    step = cfg["step"]
    steps = FLOWS[topic]["steps"]
    current = steps[step]

    # Paso 0: DETECTAR
    if step == 0:
        # guardo input
        cfg["last_input"] = text.lower()
        # cuento coincidencias
        keywords = TOPIC_KEYWORDS[topic]
        count = sum(bool(re.search(rf"\b{kw}\b", cfg["last_input"])) for kw in keywords)
        if count < 2:
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(
                number,
                "No detecté síntomas claros de ansiedad. "
                "Podés describirlo de otra forma o consultar a un profesional."
            ))
        # pasa a confirmación
        cfg["step"] += 1
        return enviar_Mensaje_whatsapp(buttonReply_Message(
            number,
            steps[1]["options"],
            steps[1]["prompt"],
            topic.capitalize(),
            f"{topic}_confirm",
            messageId
        ))

    # confirmación (Paso 1)
    if step == 1:
        if text.lower() == "no":
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(number,"¡Gracias por usar AMPARA!"))
        cfg["step"] += 1

    # Paso 2: saludo a guardar y preguntar sensación
    if step == 2:
        cfg["last_input"] = text
        # guardo a archivo
        fname = f"/mnt/data/{number}_{topic}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(text)
        # paso siguiente: mostrar botones
        cfg["step"] += 1
        return enviar_Mensaje_whatsapp(buttonReply_Message(
            number,
            steps[2]["options"],
            steps[2]["prompt"],
            topic.capitalize(),
            f"{topic}_sens",
            messageId
        ))

    # Paso 3: entrega de contenido y cierre
    if step == 3:
        cfg["last_choice"] = text
        # contenido
        cont = steps[3]["content_fn"](text)
        enviar_Mensaje_whatsapp(text_Message(number, cont))
        cfg["step"] += 1
        # paso final (4)
        cierre = steps[4]["prompt"]
        session_states.pop(number)
        return enviar_Mensaje_whatsapp(text_Message(number, cierre))

# ----------------------------------------
# Dispatcher principal
# ----------------------------------------
def administrar_chatbot(text, number, messageId, name):
    enviar_Mensaje_whatsapp(markRead_Message(messageId))
    enviar_Mensaje_whatsapp(replyReaction_Message(number, messageId, "🧠"))
    time.sleep(random.uniform(0.3,0.7))

    txt = text.strip().lower()
    if txt in ['hola','buenos días','buenas tardes','buenas noches']:
        body = (f"¡Hola {name}! Soy *AMPARA IA*, tu asistente virtual.\n"
                "¿Qué deseas hacer?\n\n"
                "1. Psicoeducación Interactiva\n"
                "2. Informe al Terapeuta\n"
                "3. Recordatorios Terapéuticos")
        return enviar_Mensaje_whatsapp(buttonReply_Message(
            number,MICROSERVICES,body,"AMPARA IA","main_menu",messageId
        ))

    if text=="main_menu_btn_1":
        # paso 0 pide descripción
        return enviar_Mensaje_whatsapp(text_Message(
            number,FLOWS["ansiedad"]["steps"][0]["prompt"]
        ))

    if number in session_states:
        # continuo flujo detect/confirm/...
        return dispatch_flow(number, messageId, text, session_states[number]["topic"])

    # fallback
    return enviar_Mensaje_whatsapp(text_Message(
        number,"No entendí. Escribí 'hola' para volver al menú."
    ))
