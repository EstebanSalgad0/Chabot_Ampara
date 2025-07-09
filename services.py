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
session_states = {}  # Cada sesión: topic, step, last_choice, last_input

# ----------------------------------------
# Lista de keywords asociadas a ansiedad
# ----------------------------------------
ANXIEDAD_KEYWORDS = [
    "preocupación", "anticipatoria", "excesiva",
    "taquicardia", "tensión", "opresión",
    "sueño", "evitación", "miedo", "agotamiento"
]

# ----------------------------------------
# Definición de flujos de psicoeducación
# ----------------------------------------
FLOWS = {
    "ansiedad": {
        "steps": [
            {   # Paso 0: Detectar síntomas
                "type": "detect"
            },
            {   # Paso 1: Confirmación
                "type": "confirm",
                "prompt": (
                    "🌿 *Detección de ansiedad*\n\n"
                    "Lo que describiste puede estar relacionado con *estados de ansiedad*. "
                    "¿Te gustaría que revisemos algunos contenidos que refuercen lo conversado en sesión?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: Entrada libre y guardado
                "type": "text",
                "prompt": (
                    "🟢 *Describe con tus propias palabras cómo te sentís ahora.*\n\n"
                    "(Tu descripción se guardará y luego podrás descargarla para compartirla con tu psicólogo.)"
                ),
                "save_to_file": True  # marca para guardar
            },
            {   # Paso 3: Selección de sensación
                "type": "button",
                "prompt": "¿Qué sensación o sentimiento se asimila más a lo que describiste?",
                "options": [
                    "Presión en el pecho",
                    "Pensamiento catastrófico",
                    "Alteraciones del sueño",
                    "Evitación por miedo",
                    "Agotamiento mental"
                ]
            },
            {   # Paso 4: Entrega de contenido según elección
                "type": "text",
                "content_fn": lambda choice: {
                    "Presión en el pecho":
                        "Respuesta fisiológica al estrés y cómo reducirla.\n[Audio respiración 4-7-8 + infografía]",
                    "Pensamiento catastrófico":
                        "Ejercicio guiado y rueda del control.\n[Cápsula educativa]",
                    "Alteraciones del sueño":
                        "Higiene del sueño y ejercicios para calmar la mente.\n[Audio relajación + rutina editable]",
                    "Evitación por miedo":
                        "Evita gradualmente la exposición a situaciones temidas.\n[Guía visual descargable]",
                    "Agotamiento mental":
                        "Técnicas de autocuidado y mindfulness.\n[Frases de autocompasión + audio validante]"
                }.get(choice, "Aquí tenés información sobre ese tema.")
            },
            {   # Paso 5: Cierre
                "type": "text",
                "prompt": (
                    "✅ *Cierre del flujo:*\n"
                    "Lo que estás sintiendo es señal de que tu cuerpo necesita sentirse seguro. "
                    "¿Querés que prepare una cápsula para repasar esta semana?"
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
    if 'type' not in message: return 'mensaje no reconocido'
    t = message['type']
    if t == 'text': return message['text']['body']
    if t == 'button': return message['button']['text']
    if t == 'interactive':
        ip = message['interactive']
        if ip['type']=='list_reply': return ip['list_reply']['id']
        if ip['type']=='button_reply': return ip['button_reply']['id']
    return 'mensaje no procesado'

def enviar_Mensaje_whatsapp(payload):
    headers = {
        'Content-Type':'application/json',
        'Authorization':f"Bearer {sett.WHATSAPP_TOKEN}"
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
        "messaging_product":"whatsapp","recipient_type":"individual",
        "to":number,"type":"text","text":{"body":text}
    })

def buttonReply_Message(number, options, body, footer, sedd, messageId):
    buttons=[]
    for i,opt in enumerate(options):
        title = opt if len(opt)<=20 else opt[:20]
        buttons.append({"type":"reply","reply":{"id":f"{sedd}_btn_{i+1}","title":title}})
    return json.dumps({
        "messaging_product":"whatsapp","recipient_type":"individual","to":number,
        "type":"interactive","interactive":{
            "type":"button","body":{"text":body},
            "footer":{"text":footer},"action":{"buttons":buttons}
        }
    })

def markRead_Message(messageId):
    return json.dumps({
        "messaging_product":"whatsapp","status":"read","message_id":messageId
    })

def replyReaction_Message(number, messageId, emoji):
    return json.dumps({
        "messaging_product":"whatsapp","recipient_type":"individual",
        "to":number,"type":"reaction","reaction":{"message_id":messageId,"emoji":emoji}
    })

# ----------------------------------------
# Manejador genérico de flujos con detect/confirm/save
# ----------------------------------------
def dispatch_flow(number, messageId, text, topic):
    cfg = session_states.get(number)
    if not cfg:
        session_states[number] = {"topic":topic,"step":0,"last_choice":None,"last_input":None}
        cfg = session_states[number]

    step = cfg["step"]
    steps = FLOWS[topic]["steps"]
    current = steps[step]

    # Detect
    if current["type"]=="detect":
        cfg["last_input"] = text.lower()
        count = sum(bool(re.search(rf"\b{kw}\b", cfg["last_input"])) for kw in ANXIEDAD_KEYWORDS)
        if count<2:
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(
                number,
                "No detecté síntomas característicos de ansiedad. Consultá con tu terapeuta."
            ))
        # avanza a confirm
        cfg["step"]+=1
        return enviar_Mensaje_whatsapp(buttonReply_Message(
            number,
            steps[cfg["step"]]["options"],
            steps[cfg["step"]]["prompt"],
            "Detección Ansiedad",
            f"{topic}_confirm", messageId
        ))

    # Confirm
    if current["type"]=="confirm":
        if text.lower()=="no":
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(number,"¡Muchas gracias por usar AMPARA!"))
        cfg["step"]+=1  # avanza

    # Texto con guardado
    current = steps[cfg["step"]]
    if current["type"]=="text" and current.get("save_to_file"):
        cfg["last_input"] = text
        # guardar a archivo
        filename = f"/mnt/data/{number}_ansiedad.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        enviar_Mensaje_whatsapp(text_Message(
            number,
            f"✅ Tu descripción ha sido guardada. Puedes descargarla aquí: {filename}"
        ))
        cfg["step"]+=1
        # luego desplegar botones de sensación
        nxt = steps[cfg["step"]]
        return enviar_Mensaje_whatsapp(buttonReply_Message(
            number, nxt["options"], nxt["prompt"],
            "Sensaciones", f"{topic}_sens", messageId
        ))

    # Botones de sensación
    if current["type"]=="button":
        cfg["last_choice"]=text
        enviar_Mensaje_whatsapp(text_Message(
            number,
            steps[cfg["step"]+1]["content_fn"](text)
        ))
        cfg["step"]+=2  # saltar entrega y cerrar
        # cerrar
        cierre = steps[-1]["prompt"]
        return enviar_Mensaje_whatsapp(text_Message(number, cierre))

# ----------------------------------------
# Dispatcher principal
# ----------------------------------------
def administrar_chatbot(text, number, messageId, name):
    # marca leído y reacción
    enviar_Mensaje_whatsapp(markRead_Message(messageId))
    enviar_Mensaje_whatsapp(replyReaction_Message(number, messageId, "🧠"))
    time.sleep(random.uniform(0.4,1.0))

    txt = text.strip().lower()
    # menú principal
    if txt in ['hola','buenos días','buenas tardes','buenas noches']:
        body = (f"¡Hola {name}! Soy *AMPARA IA*, tu asistente virtual.\n"
                "¿Qué deseas hacer?\n\n1. Psicoeducación Interactiva\n"
                "2. Informe al Terapeuta\n3. Recordatorios Terapéuticos")
        return enviar_Mensaje_whatsapp(buttonReply_Message(
            number,MICROSERVICES,body,"AMPARA IA","main_menu",messageId
        ))

    # selección de microservicio
    if text=="main_menu_btn_1":
        return dispatch_flow(number,messageId,text,"ansiedad")
    if text=="main_menu_btn_2":
        return enviar_Mensaje_whatsapp(text_Message(number,"Informe al Terapeuta iniciado."))
    if text=="main_menu_btn_3":
        return enviar_Mensaje_whatsapp(text_Message(number,"Recordatorios Terapéuticos iniciado."))

    # flujos activos
    if number in session_states:
        return dispatch_flow(number,messageId,text,session_states[number]["topic"])

    # fallback
    return enviar_Mensaje_whatsapp(text_Message(number,"No entendí. Escribe 'hola' para volver al menú."))
