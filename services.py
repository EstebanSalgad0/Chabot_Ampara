import requests
import sett
import json
import time
import random

# Única definición de estado de sesión
global session_states
session_states = {}

global appointment_sessions
appointment_sessions = {}

# -----------------------------------------------------------
# Estado para recordatorio y monitoreo de medicamentos
# -----------------------------------------------------------
global medication_sessions
medication_sessions = {}

# -----------------------------------------------------------
# Ejemplos de síntomas personalizados por categoría
# -----------------------------------------------------------
EJEMPLOS_SINTOMAS = {
    "respiratorio":    "tos seca, fiebre alta, dificultad para respirar",
    "bucal":           "dolor punzante en muela, sensibilidad al frío, sangrado de encías",
    "infeccioso":      "ardor al orinar, fiebre, orina frecuente",
    "cardiovascular":  "dolor en el pecho al esfuerzo, palpitaciones, mareos",
    "metabolico":      "sed excesiva, orina frecuentemente, pérdida de peso",
    "neurologico":     "dolor de cabeza pulsátil, náuseas, fotofobia",
    "musculoesqueletico": "dolor en espalda baja al levantarte, rigidez",
    "saludmental":     "ansiedad constante, insomnio, aislamiento social",
    "dermatologico":   "granos en cara, picazón intensa, enrojecimiento",
    "otorrinolaringologico": "ojos rojos, picazón ocular, secreción",
    "ginecologico":    "dolor pélvico durante menstruación, flujo anormal",
    "digestivo":       "diarrea, dolor abdominal inferior, gases"
}

# -----------------------------------------------------------
# Recomendaciones generales adaptadas por categoría
# -----------------------------------------------------------
RECOMENDACIONES_GENERALES = {
    "respiratorio": (
        "• Mantén reposo y buena hidratación.\n"
        "• Humidifica el ambiente y ventílalo a diario.\n"
        "• Usa mascarilla si convives con personas de riesgo.\n"
        "• Evita irritantes como humo, polvo o polución.\n"
        "• Controla tu temperatura cada 6 h.\n"
        "Si empeoras o la fiebre supera 39 °C, consulta a un profesional."
    ),
    "bucal": (
        "• Cepíllate los dientes al menos dos veces al día.\n"
        "• Usa hilo dental y enjuagues antisépticos.\n"
        "• Evita alimentos muy ácidos, azúcares o demasiado fríos/calientes.\n"
        "• Controla sangrados o mal aliento persistente.\n"
        "• Programa limpieza dental profesional anualmente.\n"
        "Si el dolor o sangrado continúa, visita a tu odontólogo."
    ),
    "infeccioso": (
        "• Guarda reposo e hidrátate con frecuencia.\n"
        "• Lávate las manos y desinfecta superficies de alto contacto.\n"
        "• Aísla si tu patología puede contagiar (fiebre, erupciones).\n"
        "• Usa mascarilla para no infectar a otros.\n"
        "• Observa tu temperatura y forúnculos si los hubiera.\n"
        "Si persiste la fiebre o hay sangre en secreciones, acude al médico."
    ),
    "cardiovascular": (
        "• Controla tu presión arterial regularmente.\n"
        "• Sigue una dieta baja en sal y grasas saturadas.\n"
        "• Realiza ejercicio moderado (30 min diarios) si tu médico lo autoriza.\n"
        "• Evita tabaco y consumo excesivo de alcohol.\n"
        "• Vigila dolores torácicos, palpitaciones o hinchazón.\n"
        "Si aparece dolor en el pecho o disnea, busca ayuda inmediata."
    ),
    "metabolico": (
        "• Mantén dieta equilibrada y controla los carbohidratos.\n"
        "• Realiza actividad física regular (mín. 150 min/semana).\n"
        "• Mide glucosa/lípidos según pauta médica.\n"
        "• Toma la medicación tal como te la recetaron.\n"
        "• Evita azúcares refinados y grasas trans.\n"
        "Si notas hipoglucemia (sudor, temblores) o hiperglucemia grave, consulta hoy."
    ),
    "neurologico": (
        "• Descansa en ambientes oscuros y silenciosos.\n"
        "• Identifica desencadenantes (estrés, luces, ruido).\n"
        "• Practica técnicas de respiración o relajación.\n"
        "• Lleva un diario de frecuencia y severidad de tus síntomas.\n"
        "• Mantente bien hidratado.\n"
        "Si aparecen déficit neurológicos (desorientación, debilidad), acude al neurólogo."
    ),
    "musculoesqueletico": (
        "• Aplica frío o calor local según indicación.\n"
        "• Realiza estiramientos suaves y evita movimientos bruscos.\n"
        "• Mantén reposo relativo, sin inmovilizar en exceso.\n"
        "• Considera fisioterapia o kinesiterapia.\n"
        "• Analgésicos de venta libre según prospecto.\n"
        "Si el dolor impide tu marcha o persiste más de 72 h, consulta al traumatólogo."
    ),
    "saludmental": (
        "• Practica respiración diafragmática y mindfulness.\n"
        "• Mantén rutina de sueño regular.\n"
        "• Realiza actividad física o caminatas diarias.\n"
        "• Comparte con tu red de apoyo (familia/amigos).\n"
        "• Considera terapia psicológica si los síntomas persisten.\n"
        "Si hay riesgo de daño a ti o a otros, busca ayuda de urgencia."
    ),
    "dermatologico": (
        "• Hidrata la piel con emolientes adecuados.\n"
        "• Evita jabones o detergentes agresivos.\n"
        "• No rasques lesiones ni uses remedios caseros.\n"
        "• Protege tu piel del sol con FPS ≥ 30.\n"
        "• Identifica y evita alérgenos o irritantes.\n"
        "Si notas pus, fiebre o expansión de la lesión, consulta a dermatología."
    ),
    "otorrinolaringologico": (
        "• Realiza lavados nasales y oculares con solución salina.\n"
        "• Evita rascarte o hurgarte en oído y nariz.\n"
        "• Controla exposición a alérgenos (polvo, pólenes).\n"
        "• No automediques antibióticos; sigue prescripción.\n"
        "• Descansa la voz y evita ambientes ruidosos.\n"
        "Si hay dolor intenso, secreción purulenta o pérdida auditiva, acude al ORL."
    ),
    "ginecologico": (
        "• Mantén higiene íntima con productos suaves.\n"
        "• Usa ropa interior de algodón y cambia con frecuencia.\n"
        "• Controla cualquier flujo anormal o sangrado intenso.\n"
        "• Alivia dolor menstrual con calor local y analgésicos según prospecto.\n"
        "• Programa chequeos ginecológicos anuales.\n"
        "Si hay fiebre, dolor severo o sangrado fuera de ciclo, busca atención médica."
    ),
    "digestivo": (
        "• Sigue dieta rica en fibra (frutas, verduras, cereales integrales).\n"
        "• Hidrátate agua o soluciones de rehidratación oral.\n"
        "• Evita comidas muy grasas, picantes o irritantes.\n"
        "• Come despacio y mastica bien.\n"
        "• Controla gases con caminatas suaves.\n"
        "Si observas sangre en heces o dolor abdominal muy intenso, consulta urgente."
    ),
    "default": (
        "• Mantén reposo e hidratación.\n"
        "• Observa tus síntomas a diario.\n"
        "• Consulta a un profesional si empeoras."
    ),
}


# -----------------------------------------------------------
# Funciones de mensajería y parsing de WhatsApp
# -----------------------------------------------------------
def obtener_Mensaje_whatsapp(message):
    """Obtiene el texto o el ID de respuesta de un mensaje de WhatsApp."""
    if 'type' not in message:
        return 'mensaje no reconocido'
    t = message['type']
    if t == 'text':
        return message['text']['body']
    elif t == 'button':
        return message['button']['text']
    elif t == 'interactive':
        interactive = message['interactive']
        if interactive['type'] == 'list_reply':
            return interactive['list_reply']['id']
        elif interactive['type'] == 'button_reply':
            return interactive['button_reply']['id']
    return 'mensaje no procesado'


def enviar_Mensaje_whatsapp(data):
    """
    Envía un payload JSON a la API de WhatsApp.
    Usa las variables de entorno definidas en sett.py:
      - WHATSAPP_TOKEN
      - WHATSAPP_URL
    """
    try:
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
        resp = requests.post(sett.WHATSAPP_URL, headers=headers, data=data)
        if resp.status_code == 200:
            print("Mensaje enviado correctamente")
        else:
            print(f"Error {resp.status_code}: {resp.text}")
        return resp.text, resp.status_code
    except Exception as e:
        print(f"Excepción al enviar mensaje: {e}")
        return str(e), 403


def text_Message(number, text):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {"body": text}
    })


def buttonReply_Message(number, options, body, footer, sedd, messageId):
    buttons = [
        {"type": "reply", "reply": {"id": f"{sedd}_btn_{i+1}", "title": opt if len(opt) <= 20 else opt[:20]}}
        for i, opt in enumerate(options)
    ]
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

# -----------------------------------------------------------
# Funciones para determinar diagnóstico según cada categoría
# -----------------------------------------------------------
def diagnostico_respiratorio(respuestas):
    respuestas = respuestas.lower()
    if (
        "tos leve" in respuestas
        and "estornudos" in respuestas
        and "congestion nasal" in respuestas
    ):
        return (
            "Resfriado común",
            "Autocuidado en casa",
            "Mantén reposo e hidratación, aprovecha líquidos calientes y, si tienes congestión, usa solución salina nasal. Usa mascarilla si estás con personas de riesgo."
        )
    elif (
        "tos seca" in respuestas
        and "fiebre" in respuestas
        and "dolores musculares" in respuestas
    ):
        return (
            "Gripe (influenza)",
            "Autocuidado + control",
            "Reposa, mantén una buena hidratación y utiliza paracetamol o ibuprofeno según prospecto. Controla tu temperatura cada 6 h."
        )
    elif (
        "dolor al tragar" in respuestas
        and "fiebre" in respuestas
        and "garganta inflamada" in respuestas
    ):
        return (
            "Faringitis / Amigdalitis / Laringitis",
            "Requiere atención si persiste",
            "Haz gárgaras con agua tibia y sal, hidratación abundante. Si el dolor dura más de 48 h o hay placas en la garganta, consulta al médico para posible tratamiento antibiótico."
        )
    elif (
        "tos persistente" in respuestas
        and "flema" in respuestas
        and "pecho apretado" in respuestas
    ):
        return (
            "Bronquitis",
            "Medir gravedad",
            "Evita irritantes (humo, polvo), mantente hidratado y usa expectorantes de venta libre. Si empeora la dificultad para respirar o la fiebre persiste, acude al médico."
        )
    elif (
        "fiebre alta" in respuestas
        and "dificultad respiratoria" in respuestas
    ):
        return (
            "Neumonía",
            "Urgencia médica",
            "Esta combinación sugiere neumonía: acude de inmediato a un servicio de urgencias u hospital."
        )
    elif (
        "opresión torácica" in respuestas
        and "silbidos" in respuestas
    ):
        return (
            "Asma",
            "Evaluar crisis",
            "Si tienes salbutamol, úsalo según indicaciones. Si no mejora en 15 min o empeora la respiración, llama al 131 o acude a urgencias."
        )
    elif (
        "estornudos" in respuestas
        and "congestión nasal" in respuestas
        and "picazón" in respuestas
    ):
        return (
            "Rinitis alérgica",
            "Tratamiento ambulatorio",
            "Evita alérgenos (polvo, pólenes), antihistamínicos orales y lavados nasales con solución salina. Consulta a tu alergólogo si persiste."
        )
    elif (
        "tos seca" in respuestas
        and "fiebre" in respuestas
        and "pérdida de olfato" in respuestas
    ):
        return (
            "COVID-19",
            "Sospecha, test y aislamiento",
            "Aíslate y haz prueba PCR lo antes posible. Monitorea tus síntomas cada día y consulta si aparece dificultad respiratoria."
        )
    else:
        return None, None, None


def diagnostico_bucal(respuestas):
    respuestas = respuestas.lower()
    if (
        "dolor punzante" in respuestas
        and "sensibilidad" in respuestas
    ):
        return (
            "Caries",
            "Requiere atención odontológica",
            "Mantén una higiene bucal rigurosa (cepillado y uso de hilo dental), evita alimentos muy ácidos o muy fríos/calientes y consulta a un odontólogo para tratar la cavidad."
        )
    elif (
        "encías inflamadas" in respuestas
        and "sangrado" in respuestas
        and "mal aliento" in respuestas
    ):
        return (
            "Gingivitis",
            "Higiene mejorada + control",
            "Mejora tu higiene bucal con cepillado suave dos veces al día, uso de hilo dental y enjuagues antisépticos. Si los síntomas persisten tras una semana, visita a tu dentista."
        )
    elif (
        "encías retraídas" in respuestas
        and "dolor al masticar" in respuestas
        and "movilidad" in respuestas
    ):
        return (
            "Periodontitis",
            "Atención odontológica urgente",
            "Acude al odontólogo de inmediato; podrías necesitar raspado y alisado radicular para frenar la pérdida de tejido periodontal."
        )
    elif (
        "llagas" in respuestas
        and "pequeñas" in respuestas
        and "dolorosas" in respuestas
    ):
        return (
            "Aftas bucales",
            "Manejo local + observar",
            "Evita alimentos ácidos o picantes, enjuaga con agua tibia y sal, y utiliza gel o crema tópica para aliviar el dolor. Si duran más de 2 semanas, consulta a tu dentista."
        )
    elif (
        "dolor mandibular" in respuestas
        and "tensión" in respuestas
        and "rechinar" in respuestas
    ):
        return (
            "Bruxismo",
            "Uso de férula / evaluación",
            "Considera usar una férula de descarga nocturna, técnicas de relajación y fisioterapia mandibular. Evalúa con un odontólogo o especialista en ATM."
        )
    else:
        return None, None, None


def diagnostico_infeccioso(respuestas):
    respuestas = respuestas.lower()
    if (
        "ardor al orinar" in respuestas
        and "fiebre" in respuestas
        and "orina frecuente" in respuestas
    ):
        return (
            "Infección urinaria",
            "Atención médica no urgente",
            "Hidrátate abundantemente, evita irritantes (café, alcohol) y consulta al médico si persiste o hay sangre en la orina."
        )
    elif (
        "diarrea" in respuestas
        and "vómitos" in respuestas
        and "dolor abdominal" in respuestas
    ):
        return (
            "Gastroenteritis",
            "Hidratación + reposo",
            "Mantén reposo, usa soluciones de rehidratación oral y observa si hay signos de deshidratación. Acude al médico si empeora."
        )
    elif (
        "dolor estomacal persistente" in respuestas
        and "náuseas" in respuestas
    ):
        return (
            "Infección por Helicobacter pylori",
            "Evaluación médica necesaria",
            "Solicita pruebas de H. pylori y consulta con tu médico para iniciar tratamiento antibiótico y protector gástrico."
        )
    elif (
        "fiebre" in respuestas
        and "erupción" in respuestas
        and "ampollas" in respuestas
    ):
        return (
            "Varicela",
            "Reposo + aislamiento",
            "Mantén reposo, controla la fiebre con paracetamol y evita rascarte. Aísla hasta que todas las ampollas se sequen."
        )
    elif (
        "manchas rojas" in respuestas
        and "tos" in respuestas
        and "conjuntivitis" in respuestas
    ):
        return (
            "Sarampión",
            "Evaluación médica urgente",
            "Acude de inmediato al médico, confirma tu estado de vacunación y evita el contacto con personas susceptibles."
        )
    elif (
        "erupción leve" in respuestas
        and "inflamación ganglionar" in respuestas
    ):
        return (
            "Rubéola",
            "Observación + test",
            "Realiza prueba de rubéola y evita el contacto con embarazadas. Sigue las indicaciones de tu médico."
        )
    elif (
        "dolor en mejillas" in respuestas
        and "fiebre" in respuestas
    ):
        return (
            "Paperas",
            "Cuidado en casa + control",
            "Aplica calor suave en la zona, toma analgésicos según indicación y descansa. Consulta si hay complicaciones."
        )
    elif (
        "cansancio" in respuestas
        and "piel amarilla" in respuestas
        and "fiebre" in respuestas
    ):
        return (
            "Hepatitis A/B/C",
            "Evaluación inmediata y pruebas de laboratorio",
            "Solicita pruebas de función hepática y marcadores virales. Acude al médico cuanto antes."
        )
    else:
        return None, None, None


def diagnostico_cardiovascular(respuestas):
    respuestas = respuestas.lower()
    if (("presion" in respuestas or "presión" in respuestas)
        and ("sin síntomas" in respuestas or "alta" in respuestas)):
        return (
            "Hipertensión arterial",
            "Control ambulatorio",
            "Controla tu presión arterial regularmente, lleva una dieta baja en sal, haz ejercicio moderado y sigue las indicaciones de tu médico."
        )
    elif ("cansancio" in respuestas
          and "falta de aire" in respuestas
          and "hinchaz" in respuestas):
        return (
            "Insuficiencia cardíaca",
            "Evaluación clínica pronta",
            "Monitorea tu peso y la hinchazón, reduce la ingesta de líquidos si está indicado y consulta a un cardiólogo lo antes posible."
        )
    elif "palpitaciones" in respuestas:
        return (
            "Arritmias",
            "Requiere electrocardiograma",
            "Agenda un electrocardiograma y consulta con un especialista en cardiología para evaluar tu ritmo cardíaco."
        )
    elif ("dolor en el pecho" in respuestas
          and "brazo izquierdo" in respuestas
          and ("sudor frio" in respuestas or "sudor frío" in respuestas)):
        return (
            "Infarto agudo al miocardio",
            "Urgencia médica inmediata",
            "Llama a emergencias (SAMU 131) de inmediato o acude al hospital más cercano. No esperes."
        )
    elif ("dolor al caminar" in respuestas
          and "desaparece" in respuestas):
        return (
            "Aterosclerosis (angina)",
            "Evaluación médica en menos de 24 hrs",
            "Evita esfuerzos intensos hasta la valoración, y consulta con un cardiólogo para pruebas de perfusión o angiografía."
        )
    else:
        return None, None, None


def diagnostico_metabolico(respuestas):
    respuestas = respuestas.lower()
    if ("sed excesiva" in respuestas
        and "orina frecuentemente" in respuestas
        and "pérdida de peso" in respuestas):
        return (
            "Diabetes tipo 1",
            "Evaluación médica urgente",
            "Acude a un centro de salud para medición de glucosa en sangre y valoración endocrinológica inmediata."
        )
    elif ("cansancio" in respuestas
          and "visión borrosa" in respuestas
          and "sobrepeso" in respuestas):
        return (
            "Diabetes tipo 2",
            "Control y exámenes de laboratorio",
            "Realiza un hemograma de glucosa y HbA1c, ajusta dieta y actividad física, y programa consulta con endocrinología."
        )
    elif ("piel seca" in respuestas
          and ("intolerancia al frio" in respuestas or "frío" in respuestas)):
        return (
            "Hipotiroidismo",
            "Control endocrinológico",
            "Solicita perfil de tiroides (TSH, T4) y ajusta tu tratamiento si ya estás en seguimiento."
        )
    elif (("nerviosismo" in respuestas
           and ("sudoracion" in respuestas or "sudoración" in respuestas))
          and "pérdida de peso" in respuestas):
        return (
            "Hipertiroidismo",
            "Evaluación clínica y TSH",
            "Pide análisis de tiroides y consulta con endocrinólogo para manejo con antitiroideos o terapia con yodo."
        )
    elif ("circunferencia abdominal" in respuestas
          and ("presion alta" in respuestas or "presión alta" in respuestas)):
        return (
            "Síndrome metabólico",
            "Evaluación de riesgo cardiovascular",
            "Controla tu peso, presión y lípidos. Programa un chequeo cardiovascular completo."
        )
    elif "colesterol" in respuestas and "antecedentes" in respuestas:
        return (
            "Colesterol alto",
            "Prevención + examen de perfil lipídico",
            "Realiza un perfil de lípidos, ajusta dieta baja en grasas saturadas y considera estatinas si lo indica tu médico."
        )
    elif "dolor en la articulación" in respuestas and "dedo gordo" in respuestas:
        return (
            "Gota",
            "Evaluación médica ambulatoria",
            "Confirma con ácido úrico en sangre, modera el consumo de purinas y consulta con reumatología."
        )
    else:
        return None, None, None


def diagnostico_neurologico(respuestas):
    respuestas = respuestas.lower()
    if ("dolor de cabeza" in respuestas
        and ("pulsatil" in respuestas or "pulsátil" in respuestas)
        and ("nauseas" in respuestas or "náuseas" in respuestas)
        and "fotofobia" in respuestas):
        return (
            "Migraña",
            "Manejo con analgésicos + control",
            "Descansa en ambiente oscuro, utiliza triptanes o analgésicos según prescripción y lleva un diario de desencadenantes."
        )
    elif ("dolor de cabeza" in respuestas
          and "estrés" in respuestas):
        return (
            "Cefalea tensional",
            "Autocuidado + relajación",
            "Aplica compresas frías o calientes, practica técnicas de relajación y corrige postura."
        )
    elif ("sacudidas" in respuestas
          and "desmayo" in respuestas
          and ("confusion" in respuestas or "confusión" in respuestas)):
        return (
            "Epilepsia",  
            "Evaluación neurológica urgente",
            "Registra los episodios y consulta con neurología para EEG y ajuste de medicación anticonvulsivante."
        )
    elif ("temblores" in respuestas
          and "lentitud" in respuestas
          and "rigidez" in respuestas):
        return (
            "Parkinson",
            "Evaluación neurológica",
            "Agrega fisioterapia y consulta con neurología para iniciar tratamiento con levodopa o agonistas."
        )
    elif (("perdida de memoria" in respuestas or "pérdida de memoria" in respuestas)
          and "desorientación" in respuestas):
        return (
            "Alzheimer",
            "Evaluación por especialista",
            "Realiza pruebas cognitivas y consulta con neurología o geriatría para manejo multidisciplinario."
        )
    elif ("fatiga" in respuestas
          and "hormigueos" in respuestas
          and ("vision borrosa" in respuestas or "visión borrosa" in respuestas)):
        return (
            "Esclerosis múltiple",
            "Derivación neurológica",
            "Consulta con neurología para RMN cerebral y lumbar y comenzar terapia modificadora de enfermedad."
        )
    elif ("dolor facial" in respuestas
          and "punzante" in respuestas):
        return (
            "Neuralgia del trigémino",
            "Tratamiento farmacológico",
            "Inicia carbamazepina o gabapentina según indicación médica y valora bloqueo del nervio si persiste."
        )
    else:
        return None, None, None

def diagnostico_musculoesqueletico(respuestas):
    respuestas = respuestas.lower()
    if (
        "dolor en espalda baja" in respuestas
        and "sin golpe" in respuestas
    ):
        return (
            "Lumbalgia",
            "Reposo + fisioterapia",
            "Aplica calor local, evita levantar pesos y realiza estiramientos suaves con guía de kinesiología."
        )
    elif (
        "dolor articular" in respuestas
        and ("inflamacion" in respuestas or "inflamación" in respuestas)
        and "rigidez" in respuestas
    ):
        return (
            "Artritis",
            "Evaluación médica reumatológica",
            "Solicita marcadores inflamatorios (VSG, PCR) y consulta con reumatología para manejo con AINEs o DMARDs."
        )
    elif (
        "dolor articular" in respuestas
        and "uso" in respuestas
        and ("sin inflamacion" in respuestas or "sin inflamación" in respuestas)
    ):
        return (
            "Artrosis",
            "Ejercicio suave + control",
            "Refuerza musculatura con ejercicios de bajo impacto y considera condroprotectores si lo indica tu médico."
        )
    elif (
        "dolor muscular generalizado" in respuestas
        and "fatiga" in respuestas
    ):
        return (
            "Fibromialgia",
            "Manejo crónico integral",
            "Combina ejercicio aeróbico suave, terapia cognitivo‑conductual y manejo del dolor con tu médico."
        )
    elif (
        "dolor al mover" in respuestas
        and "sobreuso" in respuestas
    ):
        return (
            "Tendinitis",
            "Reposo local + analgésicos",
            "Aplica hielo, inmoviliza la zona en reposo y toma AINEs según indicación médica."
        )
    elif (
        "dolor localizado" in respuestas
        and "bursa" in respuestas
    ):
        return (
            "Bursitis",
            "Reposo + hielo + evaluación",
            "Aplica frío local y consulta con ortopedia o fisiatría si persiste para posible infiltración."
        )
    elif "torcedura" in respuestas:
        return (
            "Esguince",
            "Reposo, hielo, compresión, elevación (RICE)",
            "Sujeta con venda elástica, eleva la zona y reevalúa en 48 h con un profesional."
        )
    else:
        return None, None, None


def diagnostico_salud_mental(respuestas):
    respuestas = respuestas.lower()
    if (
        "ansiedad" in respuestas
        and "dificultad para relajarse" in respuestas
    ):
        return (
            "Ansiedad generalizada",
            "Apoyo psicoemocional + técnicas de autorregulación",
            "Práctica respiración diafragmática, mindfulness y considera terapia cognitivo‑conductual."
        )
    elif (
        "tristeza persistente" in respuestas
        and "pérdida de interés" in respuestas
        and "fatiga" in respuestas
    ):
        return (
            "Depresión",
            "Apoyo clínico + evaluación emocional",
            "Consulta con psiquiatría o psicología para evaluar terapia y, si es necesario, antidepresivos."
        )
    elif (
        "cambios extremos" in respuestas
        and "hiperactividad" in respuestas
    ):
        return (
            "Trastorno bipolar",
            "Evaluación profesional integral",
            "Valora estabilizadores del ánimo con psiquiatría y seguimiento estrecho."
        )
    elif (
        "ataques de pánico" in respuestas
        and "miedo a morir" in respuestas
    ):
        return (
            "Trastorno de pánico",
            "Manejo con técnicas de respiración + orientación",
            "Aprende respiración controlada y considera ISRS o benzodiacepinas en pauta corta."
        )
    elif (
        "flashbacks" in respuestas
        and "hipervigilancia" in respuestas
    ):
        return (
            "TEPT",
            "Acompañamiento psicológico",
            "Terapia de exposición y EMDR con psicólogo especializado."
        )
    elif (
        "compulsiones" in respuestas
        or "pensamientos repetitivos" in respuestas
    ):
        return (
            "TOC",
            "Detección temprana + derivación especializada",
            "Terapia cognitivo‑conductual con ERP y, si hace falta, ISRS a dosis altas."
        )
    else:
        return None, None, None


def diagnostico_dermatologico(respuestas):
    respuestas = respuestas.lower()
    if (
        "granos" in respuestas
        and ("cara" in respuestas or "pecho" in respuestas or "espalda" in respuestas)
    ):
        return (
            "Acné",
            "Manejo domiciliario + higiene",
            "Limpia con jabón suave, evita productos comedogénicos y consulta dermatología si persiste."
        )
    elif (
        "piel seca" in respuestas
        and "enrojecida" in respuestas
        and ("picazon" in respuestas or "picazón" in respuestas)
    ):
        return (
            "Dermatitis atópica",
            "Hidratación + evitar alérgenos",
            "Emuslivos frecuentes, evita jabones agresivos y considera corticoides tópicos si lo indica tu médico."
        )
    elif (
        "placas rojas" in respuestas
        and "escamas" in respuestas
        and "engrosadas" in respuestas
    ):
        return (
            "Psoriasis",
            "Evaluación dermatológica",
            "Consulta dermatológica para valorar calcipotriol o fototerapia."
        )
    elif (
        "ronchas" in respuestas
        and "aparecen" in respuestas
        and ("rapido" in respuestas or "rápido" in respuestas)
    ):
        return (
            "Urticaria",
            "Posible alergia / estrés",
            "Antihistamínicos orales y evita desencadenantes identificados."
        )
    elif (
        ("lesion redonda" in respuestas or "lesión redonda" in respuestas)
        and "borde rojo" in respuestas
    ):
        return (
            "Tiña",
            "Antimicótico tópico",
            "Aplica clotrimazol o terbinafina localmente durante 2 semanas."
        )
    elif (
        "ampolla" in respuestas
        and ("labio" in respuestas or "genitales" in respuestas)
    ):
        return (
            "Herpes simple",
            "Antiviral tópico u oral",
            "Inicia aciclovir tópico o valaciclovir oral según prescripción."
        )
    elif (
        "bultos" in respuestas
        and "duros" in respuestas
    ):
        return (
            "Verrugas",
            "Tratamiento tópico o crioterapia",
            "Aplica ácido salicílico o valora crioterapia con dermatólogo."
        )
    else:
        return None, None, None


def diagnostico_otorrinolaringologico(respuestas):
    respuestas = respuestas.lower()
    if (
        "ojos rojos" in respuestas
        and ("picazon" in respuestas or "picazón" in respuestas)
        and "secrecion" in respuestas
    ):
        return (
            "Conjuntivitis",
            "Higiene + evitar contacto",
            "Lava con soluciones salinas y evita frotar. Consulta si hay secreción purulenta."
        )
    elif (
        ("dolor de oido" in respuestas or "dolor de oído" in respuestas)
        and "fiebre" in respuestas
        and "tapado" in respuestas
    ):
        return (
            "Otitis",
            "Evaluación médica (especialmente en niños)",
            "Consulta pronto para antibióticos si está indicado y analgésicos para el dolor."
        )
    elif (
        "presion en cara" in respuestas
        and "secrecion nasal espesa" in respuestas
        and "dolor de cabeza" in respuestas
    ):
        return (
            "Sinusitis",
            "Tratamiento ambulatorio",
            "Descongestionantes y antibiótico si persiste más de 10 días."
        )
    elif (
        ("vision borrosa" in respuestas or "visión borrosa" in respuestas)
        and "halos" in respuestas
        and "dolor ocular" in respuestas
    ):
        return (
            "Glaucoma",
            "Evaluación urgente",
            "Agudeza visual y presión intraocular con oftalmólogo de inmediato."
        )
    elif (
        "dificultad para ver" in respuestas
        and ("vision nublada" in respuestas or "visión nublada" in respuestas)
    ):
        return (
            "Cataratas",
            "Derivación oftalmológica",
            "Consulta oftalmológica para valorar cirugía de cataratas."
        )
    elif (
        "zumbido" in respuestas
        or "disminucion auditiva" in respuestas
        or "disminución auditiva" in respuestas
    ):
        return (
            "Pérdida auditiva",
            "Evaluación ORL o audiometría",
            "Realiza audiometría y consulta con otorrinolaringólogo para rehabilitación auditiva."
        )
    else:
        return None, None, None



def diagnostico_ginecologico(respuestas):
    respuestas = respuestas.lower()
    if (
        "dolor al orinar" in respuestas
        and ("orina turbia" in respuestas or "turbia" in respuestas)
        and "fiebre" in respuestas
    ):
        return (
            "Cistitis",
            "Hidratación + atención médica si persiste",
            "Bebe abundante agua y consulta si hay sangre o dolor severo."
        )
    elif (
        "flujo anormal" in respuestas
        and ("picazon" in respuestas or "picazón" in respuestas or "ardor" in respuestas)
    ):
        return (
            "Vaginitis",
            "Evaluación ginecológica ambulatoria",
            "Toma muestra de flujo y pide tratamiento según cultivo."
        )
    elif (
        ("dolor pelvico" in respuestas or "dolor pélvico" in respuestas)
        and ("menstruacion dolorosa" in respuestas or "menstruación dolorosa" in respuestas)
    ):
        return (
            "Endometriosis",
            "Control ginecológico recomendado",
            "Ultrasonido pélvico y manejo hormonal con tu ginecólogo."
        )
    elif (
        "irritabilidad" in respuestas
        and "dolor mamario" in respuestas
        and "cambios premenstruales" in respuestas
    ):
        return (
            "Síndrome premenstrual (SPM)",
            "Manejo con hábitos y control hormonal",
            "Lleva registro de tu ciclo, dieta equilibrada y valora anticonceptivos hormonales."
        )
    elif (
        "dolor testicular" in respuestas
        or ("dolor" in respuestas and "perineal" in respuestas)
    ):
        return (
            "Prostatitis",
            "Evaluación médica inmediata (urología)",
            "Antibióticos según urocultivo y manejo del dolor con antiinflamatorios."
        )
    else:
        return None, None, None


def diagnostico_digestivo(respuestas):
    respuestas = respuestas.lower()
    if (
        "acidez" in respuestas
        and "ardor" in respuestas
        and ("comer" in respuestas or "aliment" in respuestas)
    ):
        return (
            "Reflujo gastroesofágico (ERGE)",
            "Control dietético + posible medicación",
            "Evita alimentos grasos, eleva la cabecera de la cama y considera IBP según médico."
        )
    elif (
        "diarrea" in respuestas
        and "dolor abdominal" in respuestas
    ):
        return (
            "Colitis",
            "Observación + evitar irritantes",
            "Hidratación con sales y dieta BRAT. Consulta si hay sangre o fiebre alta."
        )
    elif (
        ("evacuaciones dificiles" in respuestas or "evacuaciones difíciles" in respuestas)
        and "dolor abdominal" in respuestas
    ):
        return (
            "Estreñimiento",
            "Hidratación + fibra + hábitos",
            "Aumenta fibra y agua, realiza ejercicio y valora laxantes suaves."
        )
    elif (
        "dolor al evacuar" in respuestas
        and ("sangrado" in respuestas or "sangre" in respuestas)
        and ("picazon" in respuestas or "picazón" in respuestas)
    ):
        return (
            "Hemorroides",
            "Higiene + dieta + evaluación médica si persiste",
            "Baños de asiento, crema de hidrocortisona y dieta rica en fibra."
        )
    elif (
        "gases" in respuestas
        and ("hinchazon" in respuestas or "hinchazón" in respuestas)
        and "diarrea" in respuestas
        and ("lacteos" in respuestas or "lácteos" in respuestas)
    ):
        return (
            "Intolerancia a la lactosa",
            "Evitar lácteos + prueba de tolerancia",
            "Sustituye por leches sin lactosa y realiza test de hidrógeno espirado."
        )
    else:
        return None, None, None

diagnostico_saludmental = diagnostico_salud_mental

def handle_orientacion(text, number, messageId):
    parts = text.split(":", 1)
    if len(parts) < 2:
        return text_Message(
            number,
            "Por favor, proporciona la información en el formato:\n"
            "orientacion_<categoria>_<paso>:<tus síntomas>"
        )

    header, content = parts[0], parts[1].strip()
    hp = header.split("_")
    if len(hp) < 3 or hp[0] != "orientacion":
        return text_Message(number, "Formato incorrecto para orientación de síntomas.")
    categoria, paso = hp[1], hp[2]

    known = {
        "respiratorio": [
            "tos leve", "tos seca", "tos persistente", "tos",
            "fiebre", "fiebre alta", "estornudos", "congestion nasal", "congestión nasal",
            "dolor de garganta", "dolor al tragar", "garganta inflamada",
            "cansancio", "dolores musculares", "dolor en el pecho", "pecho apretado",
            "flema", "silbidos", "picazón", "picazon", "pérdida de olfato",
            "opresión torácica", "opresion toracica"
        ],
        "bucal": [
            "dolor punzante", "sensibilidad",
            "encías inflamadas", "encías retraídas",
            "sangrado", "mal aliento",
            "llagas", "pequeñas", "dolorosas",
            "dolor al masticar", "tensión mandibular",
            "movilidad", "dolor mandibular", "rechinar"
        ],
        "infeccioso": [
            "ardor al orinar", "fiebre", "orina frecuente",
            "diarrea", "vómitos", "dolor abdominal",
            "manchas", "picazón", "picazon", "ictericia"
        ],
        "cardiovascular": [
            "dolor en el pecho", "palpitaciones", "cansancio", "mareos",
            "falta de aire", "hinchazón", "hinchazon", "sudor frío", "sudor frio",
            "náuseas", "presión", "presion",
            "dolor al caminar", "desaparece", "brazo izquierdo"
        ],
        "metabolico": [
            "sed excesiva", "orina frecuentemente", "pérdida de peso", "aumento de peso",
            "cansancio", "visión borrosa", "vision borrosa", "colesterol", "antecedentes",
            "nerviosismo", "sudoración", "sudoracion", "circunferencia abdominal",
            "sobrepeso", "piel seca", "intolerancia al frio", "intolerancia al frío"
        ],
        "neurologico": [
            "dolor de cabeza", "pulsatil", "pulsátil", "náuseas", "nauseas",
            "fotofobia", "estrés", "estres", "tensión", "tension",
            "temblores", "lentitud", "rigidez", "sacudidas", "desmayo",
            "confusión", "confusion", "pérdida de memoria", "perdida de memoria",
            "desorientación", "desorientacion",
            "hormigueo", "fatiga", "dolor facial", "punzante"
        ],
        "musculoesqueletico": [
            "dolor en espalda baja", "dolor articular", "inflamación",
            "rigidez", "dolor muscular", "fatiga", "torcedura", "bursa"
        ],
        "saludmental": [
            "ansiedad", "dificultad para relajarse", "tristeza persistente",
            "pérdida de interés", "fatiga", "cambios extremos", "hiperactividad",
            "ataques de pánico", "miedo a morir", "flashbacks", "hipervigilancia",
            "compulsiones", "pensamientos repetitivos"
        ],
        "dermatologico": [
            "granos", "picazón", "picazon", "erupción", "erupcion",
            "escamas", "engrosadas", "ampolla", "ronchas", "aparecen",
            "lesión redonda", "lesion redonda", "borde rojo", "bultos", "duros"
        ],
        "otorrinolaringologico": [
            "ojos rojos", "picazón", "picazon", "secreción", "secrecion",
            "dolor de oído", "dolor de oido", "fiebre", "tapado",
            "presion en cara", "presión en cara", "secrecion nasal espesa",
            "zumbido", "visión borrosa", "vision borrosa", "halos",
            "dificultad para ver", "vision nublada", "visión nublada"
        ],
        "ginecologico": [
            "dolor al orinar", "orina turbia", "turbia", "fiebre",
            "flujo anormal", "picazón", "picazon", "ardor",
            "dolor pélvico", "dolor pelvico", "menstruación dolorosa",
            "menstruacion dolorosa", "sangrado menstrual",
            "irritabilidad", "dolor mamario", "cambios premenstruales",
            "dolor testicular", "perineal"
        ],
        "digestivo": [
            "acidez", "ardor", "comer", "aliment", "diarrea",
            "estreñimiento", "evacuaciones difíciles", "evacuaciones dificiles",
            "dolor abdominal", "dolor al evacuar", "gases", "hinchazón",
            "hinchazon", "sangrado", "lacteos", "lácteos"
        ],
    }



    # Paso 1: extracción → confirmación con botones
    if paso == "extraccion":
        sym_list = known.get(categoria, [])
        detectados = [s for s in sym_list if s in content.lower()]
        session_states[number]["texto_inicial"] = content

        body = (
            f"🩺 He detectado estos síntomas de *{categoria}*:\n"
            + "\n".join(f"- {d}" for d in (detectados or ["(ninguno)"]))
        )
        footer = "¿Es correcto?"
        buttons = ["Si ✅", "No ❌"]
        return buttonReply_Message(
            number,
            buttons,
            body,
            footer,
            f"orientacion_{categoria}_confirmacion",
            messageId
        )

    # Paso 2: confirmación y diagnóstico
    if paso == "confirmacion":
        # 1) si vino de un botón, content será algo_btn_1 o algo_btn_2
        if content.endswith("_btn_1"):
            respuesta = "si"
        elif content.endswith("_btn_2"):
            respuesta = "no"
        else:
            # 2) si no, quizá vino por texto libre
            respuesta = content.lower().split()[0]

        if respuesta == "si":
            original = session_states[number].get("texto_inicial", "")
            func = globals().get(f"diagnostico_{categoria}")
            if not func:
                cuerpo = "Categoría no reconocida para diagnóstico."
            else:
                salida = func(original)
                if len(salida) == 3:
                    diag, nivel, reco = salida
                else:
                    diag, nivel = salida
                    reco = ""
                if diag:
                    cierre_texto = RECOMENDACIONES_GENERALES.get(
                        categoria,
                        RECOMENDACIONES_GENERALES["default"]
                    )
                    cierre_general = f"\n\nRecomendaciones generales:\n{cierre_texto}"
                    cuerpo = (
                        f"Basado en tus síntomas, podrías tener: *{diag}*.\n"
                        f"Nivel de alerta: *{nivel}*.\n\n"
                        f"{reco}"
                        f"{cierre_general}"
                    )
                else:
                    cuerpo = (
                        "No se pudo determinar un diagnóstico con la información proporcionada. "
                        "Te recomiendo acudir a un profesional para una evaluación completa."
                    )
            session_states.pop(number, None)
            return text_Message(number, cuerpo)
        else:
            session_states[number]["paso"] = "extraccion"
            return text_Message(number, "Entendido. Por favor describe nuevamente tus síntomas.")



# -----------------------------------------------------------
# Función principal del chatbot
# -----------------------------------------------------------

def administrar_chatbot(text, number, messageId, name):
    text = text.lower()
    # 1) marcar leído y reacción inicial
    enviar_Mensaje_whatsapp(markRead_Message(messageId))
    enviar_Mensaje_whatsapp(replyReaction_Message(number, messageId, "🩺"))
    

# 2) Mapeo de IDs de botones (button_reply) y filas de lista (list_reply)
    ui_mapping = {
        # Menú principal
        "menu_principal_btn_1": "agendar cita",
        "menu_principal_btn_2": "recordatorio de medicamento",
        "menu_principal_btn_3": "orientación de síntomas",

        # Especialidades – página 1
        "cita_especialidad_row_1": "medicina general",
        "cita_especialidad_row_2": "pediatría",
        "cita_especialidad_row_3": "ginecología y obstetricia",
        "cita_especialidad_row_4": "salud mental",
        "cita_especialidad_row_5": "kinesiología",
        "cita_especialidad_row_6": "odontología",
        "cita_especialidad_row_7": "➡️ ver más especialidades",

        # Especialidades – página 2 (hasta 10 filas)
        "cita_especialidad2_row_1":  "oftalmología",
        "cita_especialidad2_row_2":  "dermatología",
        "cita_especialidad2_row_3":  "traumatología",
        "cita_especialidad2_row_4":  "cardiología",
        "cita_especialidad2_row_5":  "nutrición y dietética",
        "cita_especialidad2_row_6":  "fonoaudiología",
        "cita_especialidad2_row_7":  "medicina interna",
        "cita_especialidad2_row_8":  "reumatología",
        "cita_especialidad2_row_9":  "neurología",
        "cita_especialidad2_row_10": "➡️ mostrar más…",

        # Especialidades – página 3 (hasta 10 filas)
        "cita_especialidad3_row_1":  "gastroenterología",
        "cita_especialidad3_row_2":  "endocrinología",
        "cita_especialidad3_row_3":  "urología",
        "cita_especialidad3_row_4":  "infectología",
        "cita_especialidad3_row_5":  "terapias complementarias",
        "cita_especialidad3_row_6":  "toma de muestras",
        "cita_especialidad3_row_7":  "vacunación / niño sano",
        "cita_especialidad3_row_8":  "control crónico",
        "cita_especialidad3_row_9":  "atención domiciliaria",
        "cita_especialidad3_row_10": "otro",

        # Fecha y Hora (button_reply)
        "cita_fecha_btn_1": "elegir fecha y hora",
        "cita_fecha_btn_2": "lo antes posible",

        # Sede (button_reply)
        "cita_sede_btn_1": "sede talca",
        "cita_sede_btn_2": "no, cambiar de sede",

        # Cambio de sede (list_reply)
        "cita_nueva_sede_row_1": "sede talca",
        "cita_nueva_sede_row_2": "sede curicó",
        "cita_nueva_sede_row_3": "sede linares",

        # Confirmación final (button_reply)
        "cita_confirmacion_btn_1": "cita_confirmacion:si",
        "cita_confirmacion_btn_2": "cita_confirmacion:no",

        # Orientación de síntomas – página 1
        "orientacion_categorias_row_1":  "orientacion_respiratorio_extraccion",
        "orientacion_categorias_row_2":  "orientacion_bucal_extraccion",
        "orientacion_categorias_row_3":  "orientacion_infeccioso_extraccion",
        "orientacion_categorias_row_4":  "orientacion_cardiovascular_extraccion",
        "orientacion_categorias_row_5":  "orientacion_metabolico_extraccion",
        "orientacion_categorias_row_6":  "orientacion_neurologico_extraccion",
        "orientacion_categorias_row_7":  "orientacion_musculoesqueletico_extraccion",
        "orientacion_categorias_row_8":  "orientacion_saludmental_extraccion",
        "orientacion_categorias_row_9":  "orientacion_dermatologico_extraccion",
        "orientacion_categorias_row_10": "ver más ➡️",

        # Orientación de síntomas – página 2
        "orientacion_categorias2_row_1": "orientacion_ginecologico_extraccion",
        "orientacion_categorias2_row_2": "orientacion_digestivo_extraccion",
    }

    datetime_mapping = {
    "cita_datetime_row_1": "2025-04-18 10:00 AM",
    "cita_datetime_row_2": "2025-04-18 11:30 AM",
    "cita_datetime_row_3": "2025-04-18 02:00 PM",
    "cita_datetime_row_4": "2025-04-19 09:00 AM",
    "cita_datetime_row_5": "2025-04-19 03:00 PM",
    "cita_datetime_row_6": "2025-04-20 10:00 AM",
    "cita_datetime_row_7": "2025-04-20 01:00 PM",
    "cita_datetime_row_8": "2025-04-21 09:30 AM",
    "cita_datetime_row_9": "2025-04-21 11:00 AM",
    "cita_datetime_row_10":"2025-04-21 02:30 PM",
    }

    # Normalizar y mapear IDs de UI
    if text in ui_mapping:
        text = ui_mapping[text]




    # 4) flujo de orientación activo (solo orientación de síntomas)
    if number in session_states and 'categoria' in session_states[number]:
        state = session_states[number]
        hdr = f"orientacion_{state['categoria']}_{state['paso']}"
        payload = handle_orientacion(f"{hdr}:{text}", number, messageId)
        enviar_Mensaje_whatsapp(payload)
        if state['paso'] == 'extraccion':
            session_states[number]['paso'] = 'confirmacion'
        else:
            session_states.pop(number, None)
        return

    list_responses = []
    disclaimer = (
        "\n\n*IMPORTANTE: Soy un asistente virtual con información general. "
        "Esta información NO reemplaza el diagnóstico ni la consulta con un profesional de la salud.*"
    )

    # Simular lectura
    time.sleep(random.uniform(0.5, 1.5))

    reacciones_ack = ["👍", "👌", "✅", "🩺"]
    emojis_saludo   = ["👋", "😊", "🩺", "🧑‍⚕️"]
    despedidas     = [
        f"¡Cuídate mucho, {name}! Aquí estoy si necesitas más. 😊" + disclaimer,
        "Espero haberte ayudado. ¡Hasta pronto! 👋" + disclaimer,
        "¡Que tengas un buen día! Recuerda consultar a tu médico si persisten. 🙌" + disclaimer,
    ]
    agradecimientos = [
        "De nada. ¡Espero que te sirva!" + disclaimer,
        f"Un placer ayudarte, {name}. ¡Cuídate!" + disclaimer,
        "Estoy aquí para lo que necesites." + disclaimer,
    ]
    respuesta_no_entendido = (
        "Lo siento, no entendí tu consulta. Puedes elegir:\n"
        "• Agendar Cita Médica\n"
        "• Recordatorio de Medicamento\n"
        "• Orientación de Síntomas"
        + disclaimer
    )

    # --- Lógica principal ---

    # 1) Emergencias
    if any(w in text for w in ["ayuda urgente", "urgente", "accidente", "samu", "131"]):
        body = (
            "🚨 *Si estás en una emergencia médica, llama de inmediato:* 🚨\n"
            "• SAMU: 131\n"
            "• Bomberos: 132\n"
            "• Carabineros: 133\n\n"
            "*No esperes respuesta del chatbot.*"
        )
        list_responses.append(text_Message(number, body))
        list_responses.append(replyReaction_Message(number, messageId, "🚨"))

    # Saludo y menú principal
    elif any(w in text for w in ["hola", "buenas", "saludos"]):
        body = (
            f"👋 ¡Hola {name}! Soy *MedicAI*, tu asistente virtual.\n\n"
            "¿En qué puedo ayudarte?\n"
            "1️⃣ Agendar Cita Médica\n"
            "2️⃣ Recordatorio de Medicamento\n"
            "3️⃣ Orientación de Síntomas"
        )
        footer = "MedicAI"
        opts = [
            "🗓️ Cita Médica",
            "💊 Recordar Medic",
            "🩺 Orientar Sint"
        ]
        list_responses.append(
            buttonReply_Message(number, opts, body, footer, "menu_principal", messageId)
        )
        list_responses.append(
            replyReaction_Message(number, messageId, random.choice(emojis_saludo))
        )

     # -----------------------------------------------------------
     # 3) Flujo: Agendar Citas
     # -----------------------------------------------------------
    elif "agendar cita" in text or "cita médica" in text:
         appointment_sessions[number] = {}                       # ← MOD: inicializo estado de cita
         body = "🗓️ ¡Perfecto! Selecciona el tipo de atención que necesitas:"
         footer = "Agendamiento de Citas"
         opts = [
             "🩺 Medicina General",
             "👶 Pediatría",
             "🤰 Ginecología y Obstetricia",
             "🧠 Salud Mental",
             "🏋️‍♂️ Kinesiología",
             "🦷 Odontología",
             "➡️ Ver más Especialidades"
         ]
         list_responses.append(
             listReply_Message(number, opts, body, footer, "cita_especialidad", messageId)
         )

     # 3.1) Listado interactivo de especialidades (página 2)
    elif text == "➡️ ver más especialidades":
         body = "🔍 Otras especialidades – selecciona una opción:"
         footer = "Agendamiento – Especialidades"
         opts2 = [
             "👁️ Oftalmología", "🩸 Dermatología", "🦴 Traumatología",
             "❤️ Cardiología", "🥗 Nutrición y Dietética", "🗣️ Fonoaudiología",
             "🏥 Medicina Interna", "🔧 Reumatología", "🧠 Neurología",
             "➡️ mostrar más…"
         ]
         list_responses.append(
             listReply_Message(number, opts2, body, footer, "cita_especialidad2", messageId)
         )

     # 3.1.1) Paginación: tercera página de especialidades
    elif text == "➡️ mostrar más…":
         body = "🔍 Más especialidades – selecciona una opción:"
         footer = "Agendamiento – Especialidades"
         opts3 = [
             "🍽️ Gastroenterología", "🧬 Endocrinología", "🚻 Urología",
             "🦠 Infectología", "🌿 Terapias Complementarias", "🧪 Toma de Muestras",
             "👶 Vacunación / Niño Sano", "🏠 Atención Domiciliaria",
             "💻 Telemedicina", "❓ Otro / No sé"
         ]
         list_responses.append(
             listReply_Message(number, opts3, body, footer, "cita_especialidad3", messageId)
         )

     # 3.2) Tras elegir especialidad
    elif text in [
         "medicina general", "pediatría", "ginecología y obstetricia", "salud mental",
         "kinesiología", "odontología", "oftalmología", "dermatología",
         "traumatología", "cardiología", "nutrición y dietética", "fonoaudiología",
         "medicina interna", "reumatología", "neurología", "gastroenterología",
         "endocrinología", "urología", "infectología", "terapias complementarias",
         "toma de muestras", "vacunación / niño sano", "atención domiciliaria",
         "telemedicina", "otro", "no sé"
     ]:
         appointment_sessions[number]['especialidad'] = text       # ← MOD: guardo especialidad
         body = "⏰ ¿Tienes preferencia de día y hora para tu atención?"
         footer = "Agendamiento – Fecha y Hora"
         opts = ["📅 Elegir Fecha y Hora", "⚡ Lo antes posible"]
         list_responses.append(
             buttonReply_Message(number, opts, body, footer, "cita_fecha", messageId)
         )

     # 3.3a) Si elige “Elegir fecha y hora”
    elif text == "elegir fecha y hora":
         body   = "Por favor selecciona fecha y hora para tu cita:"
         footer = "Agendamiento – Fecha y Hora"
         opciones = list(datetime_mapping.values())
         list_responses.append(
             listReply_Message(number, opciones, body, footer, "cita_datetime", messageId)
         )

     # 3.3b) Si elige “Lo antes posible”
    elif text == "lo antes posible":
         appointment_sessions[number]['datetime'] = "Lo antes posible"  # ← MOD: guardo genérico
         body   = "¿Atenderás en la misma sede de siempre?"
         footer = "Agendamiento – Sede"
         opts   = ["Sí", "No, cambiar de sede"]
         list_responses.append(
             buttonReply_Message(number, opts, body, footer, "cita_sede", messageId)
         )

     # 3.4) Tras escoger fecha/hora de calendario
    elif text.startswith("cita_datetime_row_"):
         selected = datetime_mapping.get(text)
         appointment_sessions[number]['datetime'] = selected       # ← MOD: guardo fecha exacta
         body     = f"Has seleccionado *{selected}*. ¿Atenderás en la misma sede de siempre?"
         footer   = "Agendamiento – Sede"
         opts     = ["Sí", "No, cambiar de sede"]
         list_responses.append(
             buttonReply_Message(number, opts, body, footer, "cita_sede", messageId)
         )

     # 3.5) Cambio de sede
    elif text == "no, cambiar de sede":
         body   = "Selecciona tu nueva sede:\n• Sede Talca\n• Sede Curicó\n• Sede Linares"
         footer = "Agendamiento – Nueva Sede"
         opts   = ["Sede Talca", "Sede Curicó", "Sede Linares"]
         list_responses.append(
             listReply_Message(number, opts, body, footer, "cita_nueva_sede", messageId)
         )

     # 3.6) Confirmación final
    elif text in ["sede talca", "sede curicó", "sede linares"]:
         appointment_sessions[number]['sede'] = text             # ← MOD: guardo sede
         esp  = appointment_sessions[number]['especialidad'].capitalize()
         dt   = appointment_sessions[number].get('datetime', 'día y hora')
         sede = appointment_sessions[number]['sede'].capitalize()
         # formateo fecha y hora si vienen como "YYYY-MM-DD HH:MM"
         if " " in dt:
             fecha, hora = dt.split(" ", 1)
             horario = f"{fecha} a las {hora}"
         else:
             horario = dt
         body = (
             f"¡Listo! Tu cita ha sido agendada para el *{horario}*, "
             f"en *{esp}*, en la sede *{sede}*.\n\n"
             "¿Deseas que te envíe un recordatorio el día anterior?"
         )
         footer = "Agendamiento – Confirmación Final"
         opts   = ["Sí", "No"]
         list_responses.append(
             buttonReply_Message(number, opts, body, footer, "cita_confirmacion", messageId)
         )

     # 3.7) Respuesta al recordatorio y cierre
    elif text.startswith("cita_confirmacion"):
         body = "¡Todo listo! Gracias por confiar en MedicAI 🩺✨"
         list_responses.append(text_Message(number, body))
         appointment_sessions.pop(number, None)                  # ← MOD: limpio estado de cita


     # -----------------------------------------------------------
    # 4) Flujo de Recordatorio y Monitoreo de Medicamentos
    # -----------------------------------------------------------

    # 4.1) Inicio de nueva sesión de recordatorio
    elif "recordatorio de medicamento" in text:
        # Inicializar estado de recordatorio
        medication_sessions[number] = {}
        session_states[number]   = {"flow": "med", "step": "ask_name"}

        body = (
            "🌿 ¡Vamos a ayudarte a mantener tu tratamiento al día! 🕒\n"
            "¿Qué medicamento necesitas que te recuerde tomar?"
        )
        list_responses.append(text_Message(number, body))

    # 4.2) Continuar el flujo de recordatorio existente
    elif number in session_states and session_states[number].get("flow") == "med":
        flow = session_states[number]
        step = flow["step"]

        if step == "ask_name":
            # Guardar nombre del medicamento
            medication_sessions[number]["name"] = text
            flow["step"] = "ask_freq"

            body = "Perfecto. ¿Con qué frecuencia debes tomarlo?"
            opts = [
                "Una vez al día",
                "Dos veces al día",
                "Cada 8 horas",
                "Otro horario personalizado"
            ]
            # Usamos lista en lugar de botones para permitir 4 opciones
            list_responses.append(
                listReply_Message(
                    number,
                    opts,
                    body,
                    "Recordatorio Medicamentos",
                    "med_freq",
                    messageId
                )
            )

        elif step == "ask_freq":
            # Guardar frecuencia
            medication_sessions[number]["freq"] = text
            flow["step"] = "ask_times"

            body = (
                "Anotaré tus tomas. ¿A qué hora quieres que te lo recuerde? "
                "(por ejemplo: 08:00 y 20:00)"
            )
            list_responses.append(text_Message(number, body))

        elif step == "ask_times":
            # Guardar horarios y cerrar flujo
            medication_sessions[number]["times"] = text
            med   = medication_sessions[number]["name"]
            times = medication_sessions[number]["times"]

            body = (
                f"¡Listo! Desde mañana, te enviaré un recordatorio de tu {med} a las {times}.\n"
                "📌 Recuerda que tomar tus medicamentos es un paso hacia sentirte mejor 💊💙"
            )
            list_responses.append(text_Message(number, body))
            session_states.pop(number, None)

            
    # 5) Inicio de orientación de síntomas
    elif "orientación de síntomas" in text or "orientacion de sintomas" in text:
        body = "Selecciona categoría de Enfermedades:"
        footer = "Orient. Síntomas"
        opts = [
            "Respiratorias 🌬",
            "Bucales 🦷",
            "Infecciosas 🦠",
            "Cardio ❤️",
            "Metabólicas ⚖️",
            "Neurológicas 🧠",
            "Músculo 💪",
            "Salud Mental 🧘",
            "Dermatologicas 🩹",
            "Ver más ➡️",
        ]
        enviar_Mensaje_whatsapp(
            listReply_Message(number, opts, body, footer, "orientacion_categorias", messageId)
        )
        return

    # 5.1) Paginación: si el usuario elige "Ver más ➡️", mostramos las categorías adicionales
    elif text == "Ver más ➡️":
        opts2 = [
            "Ginecológicas 👩‍⚕️",
            "Digestivas 🍽️",
        ]
        footer2 = "Orient. Síntomas"
        enviar_Mensaje_whatsapp(
            listReply_Message(number, opts2, "Otras categorías:", footer2, "orientacion_categorias2", messageId)
        )
        return


    # 6) Usuario selecciona categoría: arrancamos orientación
    elif text.startswith("orientacion_") and text.endswith("_extraccion"):
        _, categoria, _ = text.split("_", 2)
        session_states[number] = {"categoria": categoria, "paso": "extraccion"}

        display = {
            "respiratorio": "Respiratorias",
            "bucal": "Bucales",
            "infeccioso": "Infecciosas",
            "cardiovascular": "Cardiovasculares",
            "metabolico": "Metabólicas/Endocrinas",
            "neurologico": "Neurológicas",
            "musculoesqueletico": "Musculoesqueléticas",
            "saludmental": "Salud Mental",
            "dermatologico": "Dermatológicas",
            "ginecologico": "Ginecológicas/Urológicas",
            "digestivo": "Digestivas"
        }.get(categoria, categoria)

        ejemplo = EJEMPLOS_SINTOMAS.get(
            categoria,
            "tos seca, fiebre alta, dificultad para respirar"
        )

        prompt = (
            f"Por favor describe tus síntomas para enfermedades {display}.\n"
            f"Ejemplo: '{ejemplo}'"
        )
        enviar_Mensaje_whatsapp(text_Message(number, prompt))
        return

    # 7) Agradecimientos y despedidas
    elif any(w in text for w in ["gracias", "muchas gracias"]):
        list_responses.append(text_Message(number, random.choice(agradecimientos)))
        list_responses.append(replyReaction_Message(number, messageId, random.choice(reacciones_ack)))

    elif any(w in text for w in ["adiós", "chao", "hasta luego"]):
        list_responses.append(text_Message(number, random.choice(despedidas)))
        list_responses.append(replyReaction_Message(number, messageId, "👋"))

    # 8) Default
    else:
        list_responses.append(text_Message(number, respuesta_no_entendido))
        list_responses.append(replyReaction_Message(number, messageId, "❓"))

    # Envío de respuestas acumuladas
    for i, payload in enumerate(list_responses):
        if payload and payload.strip():
            enviar_Mensaje_whatsapp(payload)
        if i < len(list_responses) - 1:
            time.sleep(1)
