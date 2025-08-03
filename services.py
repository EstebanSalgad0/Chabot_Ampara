import requests
import sett
import json
import time
import random
import unicodedata

# Estado de sesión por usuario
session_states = {}

# Mapear IDs de botón/lista a comandos textuales
UI_MAPPING = {
    # Menú principal interactivo
    "menu_principal_row_1": "consulta de calificaciones",
    "menu_principal_row_2": "seguimiento de asistencia",
    "menu_principal_row_3": "horarios académicos",
    "menu_principal_row_4": "progreso académico",
    # Botones de comparación de calificaciones
    "grades_compare_btn_1": "grades_compare_yes",
    "grades_compare_btn_2": "grades_compare_no",
    # Botones de reunión de progreso
    "progress_meeting_btn_1": "progress_meeting_yes",
    "progress_meeting_btn_2": "progress_meeting_no",
    # Botones de justificación de asistencia
    "attendance_justified_btn_1": "attendance_yes",
    "attendance_justified_btn_2": "attendance_no",
    # Botones de horario académico
    "schedule_next_week_btn_1": "schedule_next_week_yes",
    "schedule_next_week_btn_2": "schedule_next_week_no",
    "schedule_meeting_btn_1": "schedule_meeting_yes",
    "schedule_meeting_btn_2": "schedule_meeting_no",
}

# Datos de ejemplo
EXAMPLE_GRADES = {
    "sofia": {"promedio": 6.1, "max": ("Matemáticas", 6.7), "min": ("Historia", 5.5), "delta_mes": 0.3}
}

EXAMPLE_SCHEDULE = {
    "amanda": [
        ("Miércoles", "Ciencias Naturales", "10:30"),
        ("Viernes", "Lenguaje y Comunicación", "10:30")
    ]
}

# Ejemplo de evaluaciones próxima semana
EXAMPLE_SCHEDULE_NEXT = {
    "amanda": [
        ("Martes", "Ciencias Sociales", "09:00"),
        ("Jueves", "Biología", "11:00")
    ]
}

EXAMPLE_PROGRESS = {
    "matias": {
        "fortalezas": ["Matemáticas", "Educación Física"],
        "debilidades": ["Inglés", "Ciencias"],
        "recomendacion": "Reforzar comprensión lectora y vocabulario en inglés"
    }
}

# -----------------------------------------------------------
# Utilidades
# -----------------------------------------------------------
def normalize(text):
    """Minúsculas y sin tildes para comparaciones."""
    return unicodedata.normalize('NFKD', text.lower()).encode('ASCII', 'ignore').decode('ASCII')

# Formatea hora 24h a 12h con AM/PM
def format_ampm(hhmm):
    h, m = map(int, hhmm.split(':'))
    suffix = 'AM' if h < 12 else 'PM'
    h12 = h if 1 <= h <= 12 else abs(h-12)
    if h12 == 0:
        h12 = 12
    return f"{h12}:{m:02d} {suffix}"
# -----------------------------------------------------------
# Funciones de mensajería y parsing de WhatsApp
# -----------------------------------------------------------
def obtener_Mensaje_whatsapp(message):
    if 'type' not in message:
        return 'mensaje no reconocido'
    t = message['type']
    if t == 'text':
        return message['text']['body']
    if t == 'button':
        return message['button']['text']
    if t == 'interactive':
        ia = message['interactive']
        if ia['type'] == 'list_reply':
            return ia['list_reply']['id']
        if ia['type'] == 'button_reply':
            return ia['button_reply']['id']
    return 'mensaje no procesado'


def enviar_Mensaje_whatsapp(data):
    """
    Envía un payload JSON a la API de WhatsApp usando las variables de entorno de sett.py:
      - WHATSAPP_TOKEN
      - WHATSAPP_URL
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {sett.WHATSAPP_TOKEN}"
    }
    print("--- Enviando JSON ---")
    try:
        print(json.dumps(json.loads(data), indent=2, ensure_ascii=False))
    except:
        print(data)
    print("---------------------")
    # URL de la API obtenida de la variable de entorno
    resp = requests.post(sett.WHATSAPP_URL, headers=headers, data=data)
    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}")
    return resp.text, resp.status_codee


def text_Message(number, text):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {"body": text}
    })


def listReply_Message(number, options, body, footer, sedd, messageId):
    rows = []
    for i, opt in enumerate(options):
        title = opt if len(opt) <= 24 else opt[:24]
        desc = "" if len(opt) <= 24 else opt
        rows.append({"id": f"{sedd}_row_{i+1}", "title": title, "description": desc})
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body},
            "footer": {"text": footer},
            "action": {"button": "Ver Opciones", "sections": [{"title": "Menú", "rows": rows}]}
        }
    })


def buttonReply_Message(number, options, body, footer, sedd, messageId):
    buttons = []
    for i, opt in enumerate(options):
        buttons.append({
            "type": "reply",
            "reply": {"id": f"{sedd}_btn_{i+1}", "title": opt if len(opt) <= 20 else opt[:20]}
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

# -----------------------------------------------------------
# Función principal del chatbot
# -----------------------------------------------------------
def administrar_chatbot(text, number, messageId, name):
    text = normalize(text)
    text = UI_MAPPING.get(text, text)
    enviar_Mensaje_whatsapp(markRead_Message(messageId))
    enviar_Mensaje_whatsapp(replyReaction_Message(number, messageId, "🎓"))

    # 1) Saludo y menú principal
    if text in ["hola", "buenas", "saludos"]:
        opts = [
            "🎒 Consulta de Calificaciones",
            "🗓️ Seguimiento de Asistencia",
            "📅 Horarios Académicos",
            "📈 Progreso Académico"
        ]
        body = (
            f"¡Hola {name}! 👋\n"
            "Soy *Mateo*, tu asistente escolar.\n"
            "¿En qué puedo ayudarte hoy?"
        )
        footer = "Menú Principal"
        enviar_Mensaje_whatsapp(listReply_Message(number, opts, body, footer, "menu_principal", messageId))
        return

    # 2) Flujos según estado
    if number in session_states:
        flow = session_states[number]["flow"]
        step = session_states[number]["step"]

        # 2.1) Consulta de Calificaciones
        if flow == "grades":
            if step == "ask_student":
                session_states[number]["student"] = text
                session_states[number]["step"] = "show_average"
                student = normalize(text)
                info = EXAMPLE_GRADES.get(student)
                if info:
                    avg_msg = (
                        f"*{text.title()}* tiene promedio general de *{info['promedio']}*."
                        f"• Nota más alta: {info['max'][0]} ({info['max'][1]})\n"
                        f"• Nota más baja: {info['min'][0]} ({info['min'][1]})"
                    )
                else:
                    avg_msg = "Lo siento, no encontré registros de ese estudiante. 🤔"
                enviar_Mensaje_whatsapp(text_Message(number, avg_msg))
                opts_cmp = ["✅ Sí", "❌ No"]
                enviar_Mensaje_whatsapp(buttonReply_Message(
                    number, opts_cmp,
                    "¿Deseas saber cómo va respecto al mes anterior?",
                    "Comparar Promedio", "grades_compare", messageId
                ))
                return
            if step == "show_average":
                student = normalize(session_states[number]["student"])
                info = EXAMPLE_GRADES.get(student)
                # Ajuste: comprobar flags generados por UI_MAPPING
                if text == "grades_compare_yes" or text == "si":
                    resp = f"Comparado con el mes pasado, subió *{info['delta_mes']}* puntos. ¡Buen avance! 🎉"
                else:
                    resp = "Entendido, sin comparación adicional."
                session_states[number]["step"] = "ask_thanks"
                enviar_Mensaje_whatsapp(text_Message(number, resp))
                return
            if step == "ask_thanks" and "gracias" in text:
                student = session_states[number]["student"].title()
                resp = f"Siempre a tu disposición para apoyar el aprendizaje de {student}."
                session_states.pop(number)
                enviar_Mensaje_whatsapp(text_Message(number, resp))
                return

        # 2.2) Seguimiento de Asistencia
        if flow == "attendance":
            if step == "ask_student":
                session_states[number]["student"] = text
                session_states[number]["step"] = "ask_justified"
                enviar_Mensaje_whatsapp(text_Message(number, f"Hoy *{text.title()}* no asistió a clases. ¿Fue justificado?"))
                opts = ["✅ Sí", "❌ No"]
                enviar_Mensaje_whatsapp(buttonReply_Message(number, opts, "Selecciona una opción:", "Justificación", "attendance_justified", messageId))
                return
            if step == "ask_justified":
                justified = text in ["attendance_yes", "si", "sí"]
                student = session_states[number]["student"].title()
                if justified:
                    enviar_Mensaje_whatsapp(text_Message(number, "Perfecto ✅, lo registraré como *justificado*."))
                    enviar_Mensaje_whatsapp(text_Message(number, "Asistencia justificada registrada."))
                else:
                    enviar_Mensaje_whatsapp(text_Message(number, "Registrado como *inasistencia injustificada*."))
                    enviar_Mensaje_whatsapp(text_Message(number, f"Te avisaré si {student} llega más tarde."))
                session_states[number]["step"] = "ask_thanks_attendance"
                return
            if step == "ask_thanks_attendance" and "gracias" in text.lower():
                student = session_states[number]["student"].title()
                resp = f"¡De nada! Estoy aquí para apoyar la continuidad educativa de {student}."
                session_states.pop(number)
                enviar_Mensaje_whatsapp(text_Message(number, resp))
                return
            
        # 2.3) Horarios Académicos
        if flow == "schedule":
            if step == "ask_student":
                student = normalize(text)
                session_states[number]["student"] = student
                session_states[number]["step"] = "ask_next_week"
                nome = text.title()
                info = EXAMPLE_SCHEDULE.get(student, [])
                lines = [f"📌 *{d}*: {subj} a las *{format_ampm(hh)}*" for d, subj, hh in info]
                msg = f"Esta semana *{nome}* tiene las siguientes evaluaciones:\n" + "\n".join(lines)
                enviar_Mensaje_whatsapp(text_Message(number, msg))
                # Preguntar por próxima semana
                opts = ["✅ Sí", "❌ No"]
                enviar_Mensaje_whatsapp(buttonReply_Message(
                    number, opts,
                    "¿Deseas ver las evaluaciones de la próxima semana?",
                    "Próxima Semana", "schedule_next_week", messageId
                ))
                return
            if step == "ask_next_week":
                student = session_states[number]["student"]
                if text in ["schedule_next_week_yes", "si", "sí"]:
                    info = EXAMPLE_SCHEDULE_NEXT.get(student, [])
                    lines = [f"📌 *{d}*: {subj} a las *{format_ampm(hh)}*" for d, subj, hh in info]
                    enviar_Mensaje_whatsapp(text_Message(number, "Evaluaciones próxima semana:\n" + "\n".join(lines)))
                # Luego preguntar por reunión de apoderados tanto si dijo sí o no
                opts = ["✅ Sí", "❌ No"]
                enviar_Mensaje_whatsapp(buttonReply_Message(
                    number, opts,
                    "¿Deseas saber cuándo hay reunión de apoderados?",
                    "Reunión", "schedule_meeting", messageId
                ))
                session_states[number]["step"] = "ask_meeting_info"
                return
            if step == "ask_meeting_info":
                if text in ["schedule_meeting_yes", "si", "sí"]:
                    resp = "👥 La reunión de apoderados es el jueves a las 18:00 hrs en modalidad online. Te enviaré el enlace 30 minutos antes."
                else:
                    resp = "¡Que tengas un buen día!"
                session_states[number]["step"] = "ask_thanks_schedule"
                enviar_Mensaje_whatsapp(text_Message(number, resp))
                return
            if step == "ask_thanks_schedule" and "gracias" in text.lower():
                enviar_Mensaje_whatsapp(text_Message(number, "¡Con gusto! La organización es clave para una buena experiencia escolar."))
                session_states.pop(number)
                return

        # 2.4) Progreso Académico
        if flow == "progress":
            if step == "ask_student":
                student = normalize(text)
                info = EXAMPLE_PROGRESS.get(student)
                if info:
                    resp = (
                        "*Resumen de Progreso*:\n"
                        f"• *Fortalezas*: {', '.join(info['fortalezas'])}\n"
                        f"• *Debilidades*: {', '.join(info['debilidades'])}\n"
                        f"• *Recomendación*: {info['recomendacion']}"
                    )
                    enviar_Mensaje_whatsapp(text_Message(number, resp))
                    time.sleep(1)
                    opts = ["Sí, agendar reunión 🗓️", "No, gracias 😊"]
                    enviar_Mensaje_whatsapp(buttonReply_Message(
                        number, opts,
                        "¿Deseas agendar una reunión con el profesor jefe?",
                        "Progreso Académico", "progress_meeting", messageId
                    ))
                    session_states[number]["step"] = "ask_meeting"
                else:
                    enviar_Mensaje_whatsapp(text_Message(number, "No encontré datos de progreso para ese estudiante. 🤷"))
                    session_states.pop(number)
                return
            if step == "ask_meeting":
                if text in ["progress_meeting_yes", "si", "sí"]:
                    resp = "✅ Reunión agendada para el lunes a las *17:00 hrs*. Te enviaré un recordatorio el día anterior."
                else:
                    resp = "Entendido, no hay reunión agendada. 😊"
                session_states.pop(number)
                enviar_Mensaje_whatsapp(text_Message(number, resp))
                return


    # 3) Iniciar flujos desde menú o texto
    commands = {"consulta de calificaciones": "grades", "seguimiento de asistencia": "attendance", "horarios académicos": "schedule", "progreso académico": "progress"}
    if text in commands:
        session_states[number] = {"flow": commands[text], "step": "ask_student"}
        prompt = {
            "grades": "¿De qué estudiante quieres consultar calificaciones?",
            "attendance": "¿De qué estudiante deseas seguimiento de asistencia?",
            "schedule": "¿Para qué estudiante deseas ver el horario?",
            "progress": "¿De qué estudiante quieres un resumen de progreso?"
        }[commands[text]]
        enviar_Mensaje_whatsapp(text_Message(number, prompt))
        return

    # 4) Fallback: menú interactivo
    opts = ["🎒 Consulta de Calificaciones", "🗓️ Seguimiento de Asistencia", "📅 Horarios Académicos", "📈 Progreso Académico"]
    body = f"Lo siento, no entendí tu solicitud, {name}. 🤔\nElige una opción del menú interactivo:"
    enviar_Mensaje_whatsapp(listReply_Message(number, opts, body, "Menú Principal", "menu_principal", messageId))
