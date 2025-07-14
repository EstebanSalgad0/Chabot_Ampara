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
# Palabras clave para clasificación de riesgo
# ----------------------------------------
RISK_KEYWORDS = {
    "Riesgo alto (suicida)": [
        "quiero rendirme", "no soporto más", "me quiero matar", "terminar con todo",
        "no vale la pena vivir", "estoy harto de vivir"
    ],
    "Riesgo medio": [
        "no puedo más", "me siento atrapado", "todo sale mal",
        "no encuentro salida", "siento que me ahogo", "ansiedad insoportable"
    ],
    "Riesgo bajo": [
        "me siento triste", "estoy agotado", "bajo ánimo",
        "desmotivado", "cansado emocionalmente", "un poco deprimido"
    ]
}



# ----------------------------------------
# Keywords para cada flujo
# ----------------------------------------
TOPIC_KEYWORDS = {
    "ansiedad": [
        "preocupación", "anticipatoria", "excesiva",
        "taquicardia", "tensión", "opresión",
        "sueño", "evitación", "miedo", "agotamiento"
    ],
    "depresion": [
        "tristeza", "anhedonia", "desmotivación",
        "baja energía", "apatía", "irritabilidad",
        "llanto", "aislamiento", "fatiga", "sentirse inútil"
    ],
    "tea": [
        "rutina", "angustia", "cambios", "ecolalia",
        "repetitivo", "sensorial", "ruidos", "texturas",
        "interacción", "autista", "autismo"
    ],
    "tdah": [
        "distraigo", "distrae", "hiperactividad", "impulsividad",
        "olvido", "organización", "planificación", "movimiento",
        "concentrar", "terminar", "interrumpe"
    ],
    "tlp": [
        "abandono", "inestabilidad", "emocional", "identidad",
        "impulsividad", "rabia", "soledad", "cambio rápido",
        "intensidad", "angustia"
    ],
    "tept": [
        "flashbacks", "intrusivos", "pesadillas", "sobresalta",
        "evito", "culpa", "vergüenza", "confusión",
        "desconexión", "retraimiento", "trauma"
    ],
    "suenos": [
        "conciliar", "despertar", "insomnio", "pesadillas",
        "sobresalto", "fatiga", "ciclos", "rumiar",
        "dormir", "descanso", "rutina nocturna"
    ],
    "tca": [
        "miedo a engordar", "culpa", "atracón", "restricción",
        "purga", "imagen corporal", "espejo", "comparación",
        "suficiente", "control", "autocastigo"
    ],
    "toc": [
        "obsesión", "compulsión", "ritual", "reviso", "lavar manos",
        "pensamientos intrusivos", "miedo a contaminarme",
        "ciclo", "alivio", "culpa", "vergüenza", "rutina"
    ]
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
    },

    "depresion": {
        "steps": [
            {   # Paso 0: pedir descripción libre
                "prompt": (
                    "🟢 *Describí los síntomas o sensaciones* que estás experimentando.\n"
                    "(Por ejemplo: “No tengo ganas de nada”, “Me siento muy triste”, etc.)"
                )
            },
            {   # Paso 1: confirmación detección
                "prompt": (
                    "🌿 *Detección de depresión*\n\n"
                    "Lo que describiste coincide con patrones de *depresión*. "
                    "¿Querés revisar contenidos psicoeducativos sobre depresión?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: confirmar envío por correo y preguntar sensación
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Qué sensación se asemeja más a lo que describiste?"
                ),
                "options": [
                    "Pérdida de interés",
                    "Tristeza profunda",
                    "Fatiga constante",
                    "Pensamientos negativos",
                    "Aislamiento social"
                ]
            },
            {   # Paso 3: entregar contenido
                "content_fn": lambda choice: {
                    "Pérdida de interés": (
                        "📌 *Tipo de recurso:* Audio + Infografía\n"
                        "Actividad de planificación de placer.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Realizar pequeñas actividades agradables puede mejorar tu ánimo."
                    ),
                    "Tristeza profunda": (
                        "📌 *Tipo de recurso:* Ejercicio guiado + Cápsula\n"
                        "Técnicas de regulación emocional.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Practicarlo te ayudará a procesar emociones difíciles."
                    ),
                    "Fatiga constante": (
                        "📌 *Tipo de recurso:* Audio de relajación\n"
                        "Ejercicios de activación conductual.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Incorporar pequeñas pausas activas puede reducir la sensación de agotamiento."
                    ),
                    "Pensamientos negativos": (
                        "📌 *Tipo de recurso:* Guía descargable\n"
                        "Reestructuración cognitiva paso a paso.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Seguir esta guía te ayudará a desafiar pensamientos disfuncionales."
                    ),
                    "Aislamiento social": (
                        "📌 *Tipo de recurso:* Frases + Audio\n"
                        "Estrategias de conexión social.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Practicar estas frases y ejercicios te puede ayudar a abrirte con otros."
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
    },

    "tea": {
        "steps": [
            {   # Paso 0: pedir descripción libre
                "prompt": (
                    "🟢 *Describí los comportamientos o sensaciones* que observás "
                    "en quien tiene TEA.\n"
                    "(Por ejemplo: “Se angustia con los cambios de rutina”, "
                    "“Repite frases todo el tiempo”, etc.)"
                )
            },
            {   # Paso 1: confirmación detección
                "prompt": (
                    "🌿 *Detección de TEA*\n\n"
                    "Lo que describiste coincide con patrones dentro del *Espectro Autista*. "
                    "¿Querés revisar contenidos psicoeducativos sobre TEA?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: confirmar envío y elegir sensación/comportamiento
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Qué aspecto se asemeja más a lo que describiste?"
                ),
                "options": [
                    "Incomodidad con cambios de rutina",
                    "Repetición de frases (ecolalia)",
                    "Sensibilidad a ruidos o texturas",
                    "Dificultad en interacción social",
                    "Intereses o conductas repetitivas"
                ]
            },
            {   # Paso 3: entregar contenido según elección
                "content_fn": lambda choice: {
                    "Incomodidad con cambios de rutina": (
                        "📌 *Tipo de recurso:* Calendario pictográfico editable\n"
                        "Cómo usar apoyos visuales para anticipar y estructurar cambios.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Planificar por adelantado reduce la ansiedad."
                    ),
                    "Repetición de frases (ecolalia)": (
                        "📌 *Tipo de recurso:* Guía práctica + ejemplos\n"
                        "Estrategias para canalizar la ecolalia hacia la comunicación funcional.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Refuerzo positivo y modelado apoyan el lenguaje."
                    ),
                    "Sensibilidad a ruidos o texturas": (
                        "📌 *Tipo de recurso:* Infografía + checklist sensorial\n"
                        "Perfil de hipersensibilidad y adaptaciones ambientales.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Filtrar estímulos molestos mejora el confort."
                    ),
                    "Dificultad en interacción social": (
                        "📌 *Tipo de recurso:* Cápsula educativa + ejercicios\n"
                        "Técnicas paso a paso para iniciar y mantener interacciones.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Practicar turnos de habla facilita el juego compartido."
                    ),
                    "Intereses o conductas repetitivas": (
                        "📌 *Tipo de recurso:* Plan de actividades + audio\n"
                        "Cómo incorporar los intereses en actividades motivadoras.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Usar los intereses como base para aprender cosas nuevas."
                    )
                }.get(choice,
                    "Aquí tenés más información sobre ese tema.\n"
                    "🔔 Enviado a tu correo.\n\n"
                    "👉 Implementa estas recomendaciones con tu terapeuta."
                )
            },
            {   # Paso 4: ¿Necesitás más ayuda?
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {   # Paso 5: despedida
                "prompt": (
                    "❤️ *Despedida:*\n"
                    "Gracias por usar AMPARA IA. Aprender sobre la neurodiversidad es "
                    "un acto de cuidado profundo. Si necesitás más apoyo, tu terapeuta "
                    "está disponible. ¡Hasta la próxima!"
                )
            }
        ]
    },

    "tdah": {
        "steps": [
            {   # Paso 0: pedir descripción libre
                "prompt": (
                    "🟢 *Describí los comportamientos o sensaciones* "
                    "que experimentás o que observás en el contexto de TDAH.\n"
                    "(Por ejemplo: “Me distraigo con cualquier cosa”, "
                    "“No paro quieto en clase”, etc.)"
                )
            },
            {   # Paso 1: confirmación detección
                "prompt": (
                    "🌿 *Detección de TDAH*\n\n"
                    "Lo que describiste coincide con patrones de *TDAH*. "
                    "¿Querés revisar contenidos psicoeducativos sobre TDAH?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: confirmar envío y elegir síntoma
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Qué síntoma te describiría mejor?"
                ),
                "options": [
                    "Dificultad para concentrarse",
                    "Inquietud motora o verbal",
                    "Impulsividad al actuar",
                    "Olvidos frecuentes",
                    "Desorganización constante"
                ]
            },
            {   # Paso 3: entregar contenido según elección
                "content_fn": lambda choice: {
                    "Dificultad para concentrarse": (
                        "📌 *Tipo de recurso:* Video breve + infografía\n"
                        "Explicación del funcionamiento atencional en TDAH.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Técnicas de enfoque pueden mejorar la atención."
                    ),
                    "Inquietud motora o verbal": (
                        "📌 *Tipo de recurso:* Ficha de pausas activas\n"
                        "Ejercicios breves para canalizar la energía.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Programar descansos regulares aumenta la calma."
                    ),
                    "Impulsividad al actuar": (
                        "📌 *Tipo de recurso:* Guía de reflexión + audio\n"
                        "Estrategias de pausa antes de responder.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Practicar respiraciones profundas antes de actuar."
                    ),
                    "Olvidos frecuentes": (
                        "📌 *Tipo de recurso:* Calendario editable + recordatorio sonoro\n"
                        "Herramientas externas para gestionar tareas.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Recordatorios visuales y audibles refuerzan la memoria."
                    ),
                    "Desorganización constante": (
                        "📌 *Tipo de recurso:* Plantillas de planificación\n"
                        "Estructuras simples para organizar el día.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Seguir un esquema diario reduce la dispersión."
                    )
                }.get(choice,
                    "Aquí tenés más información sobre ese tema.\n"
                    "🔔 He enviado este recurso a tu correo.\n\n"
                    "👉 Implementa estas recomendaciones con tu terapeuta."
                )
            },
            {   # Paso 4: ¿Necesitás más ayuda?
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {   # Paso 5: despedida
                "prompt": (
                    "❤️ *Despedida TDAH:*\n"
                    "Recordá que cada paso para convivir con TDAH es valioso. "
                    "Si necesitás más, tu terapeuta está ahí. ¡Hasta pronto!"
                )
            }
        ]
    },

    "tlp": {
        "steps": [
            {   # Paso 0: pedir descripción libre
                "prompt": (
                    "🟢 *Describí tus sensaciones o pensamientos* "
                    "relacionados con TLP.\n"
                    "(Por ejemplo: “Me enojo muy rápido”, “Siento miedo al abandono”, etc.)"
                )
            },
            {   # Paso 1: confirmación detección
                "prompt": (
                    "🌿 *Detección de TLP*\n\n"
                    "Lo que describiste coincide con patrones de *Trastorno Límite de la Personalidad*. "
                    "¿Querés revisar contenidos psicoeducativos sobre TLP?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: confirmar envío y elegir experiencia
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Qué experiencia se asemeja más a lo que sentís?"
                ),
                "options": [
                    "Cambios de ánimo muy rápidos",
                    "Miedo intenso al abandono",
                    "Ira o enojo desproporcionado",
                    "Sensación crónica de vacío",
                    "Relaciones interpersonales inestables"
                ]
            },
            {   # Paso 3: entregar contenido según elección
                "content_fn": lambda choice: {
                    "Cambios de ánimo muy rápidos": (
                        "📌 *Tipo de recurso:* Infografía ciclo emocional\n"
                        "Cómo identificar y anticipar oscilaciones afectivas.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Registro diario ayuda a reconocer patrones."
                    ),
                    "Miedo intenso al abandono": (
                        "📌 *Tipo de recurso:* Cápsula validante + ejercicio de anclaje\n"
                        "Estrategias para generar seguridad interna.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Recordar recursos de apoyo disminuye la angustia."
                    ),
                    "Ira o enojo desproporcionado": (
                        "📌 *Tipo de recurso:* Ejercicio guiado + audio\n"
                        "Técnicas de pausa emocional y respiración.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Practicar la contención antes de reaccionar."
                    ),
                    "Sensación crónica de vacío": (
                        "📌 *Tipo de recurso:* Guía de reconexión interna\n"
                        "Ejercicios para encontrar sentido y propósito.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Actividades significativas rellenan el vacío."
                    ),
                    "Relaciones interpersonales inestables": (
                        "📌 *Tipo de recurso:* Estrategias DBT para vínculos\n"
                        "Herramientas de validación y comunicación.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Practicar límites y saber pedir apoyo."
                    )
                }.get(choice,
                    "Aquí tenés más información sobre ese tema.\n"
                    "🔔 He enviado este recurso a tu correo.\n\n"
                    "👉 Implementa estas recomendaciones con tu terapeuta."
                )
            },
            {   # Paso 4: ¿Necesitás más ayuda?
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {   # Paso 5: despedida
                "prompt": (
                    "❤️ *Despedida TLP:*\n"
                    "Aprender a regular emociones intensas es un acto de cuidado profundo. "
                    "Si necesitás más, tu terapeuta está disponible. ¡Hasta la próxima!"
                )
            }
        ]
    },

    "tept": {
        "steps": [
            {   # Paso 0: pedir descripción libre
                "prompt": (
                    "🟢 *Describí los recuerdos o sensaciones* relacionadas\n"
                    "con lo que viviste.\n"
                    "(Por ejemplo: “No puedo dejar de pensar en lo que pasó”,\n"
                    "“Tengo pesadillas”, etc.)"
                )
            },
            {   # Paso 1: confirmación detección
                "prompt": (
                    "🌿 *Detección de TEPT*\n\n"
                    "Lo que describiste coincide con patrones de *Estrés Postraumático*. "
                    "¿Querés revisar contenidos psicoeducativos sobre TEPT?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: confirmar envío y elegir síntoma
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Qué síntoma te está afectando más?"
                ),
                "options": [
                    "Recuerdos o flashbacks intrusivos",
                    "Sobresaltos o hipervigilancia",
                    "Evitación de lugares o personas",
                    "Pesadillas recurrentes",
                    "Sentimiento de culpa o vergüenza"
                ]
            },
            {   # Paso 3: entregar contenido según elección
                "content_fn": lambda choice: {
                    "Recuerdos o flashbacks intrusivos": (
                        "📌 *Tipo de recurso:* Video explicativo + resumen claro\n"
                        "Comprender flashbacks y técnicas de grounding.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Grounding con 5-4-3-2-1 ancla al presente."
                    ),
                    "Sobresaltos o hipervigilancia": (
                        "📌 *Tipo de recurso:* Infografía sistema de alarma\n"
                        "Cómo reducir la reactividad física.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Prácticas de respiración lenta calman el cuerpo."
                    ),
                    "Evitación de lugares o personas": (
                        "📌 *Tipo de recurso:* Texto validante + alternativas\n"
                        "Estrategias graduadas para reencontrarte con tus miedos.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Comenzar con exposiciones muy leves y seguras."
                    ),
                    "Pesadillas recurrentes": (
                        "📌 *Tipo de recurso:* Rutina nocturna + audio relajante\n"
                        "Preparar el entorno mental antes de dormir.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Visualizaciones seguras ayudan a calmar la mente."
                    ),
                    "Sentimiento de culpa o vergüenza": (
                        "📌 *Tipo de recurso:* Guía de autoaceptación\n"
                        "Ejercicios para soltar la culpa post-trauma.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Escribir una carta de compasión hacia ti mismo/a."
                    )
                }.get(choice,
                    "Aquí tenés más información sobre ese tema.\n"
                    "🔔 He enviado este recurso a tu correo.\n\n"
                    "👉 Implementa estas recomendaciones con tu terapeuta."
                )
            },
            {   # Paso 4: ¿Necesitás más ayuda?
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {   # Paso 5: despedida
                "prompt": (
                    "❤️ *Despedida TEPT:*\n"
                    "Sanar del trauma lleva tiempo y acompañamiento. "
                    "Si necesitás más, tu terapeuta está disponible. ¡Hasta luego!"
                )
            }
        ]
    },

    "suenos": {
        "steps": [
            {   # Paso 0: pedir descripción libre
                "prompt": (
                    "🟢 *Describí tus dificultades para dormir*.\n"
                    "(Por ejemplo: “No puedo conciliar el sueño”,\n"
                    "“Me despierto muchas veces”, etc.)"
                )
            },
            {   # Paso 1: confirmación detección
                "prompt": (
                    "🌿 *Detección de trastornos del sueño*\n\n"
                    "Lo que describiste coincide con patrones de *trastornos del sueño*. "
                    "¿Querés revisar contenidos psicoeducativos sobre el descanso?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: confirmar envío y elegir dificultad
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Cuál de estas dificultades describe mejor tu sueño?"
                ),
                "options": [
                    "No puedo conciliar el sueño",
                    "Me despierto muchas veces",
                    "Duermo pero no descanso",
                    "Pesadillas o sobresaltos nocturnos",
                    "Pensamientos intrusivos al acostarme"
                ]
            },
            {   # Paso 3: entregar contenido según elección
                "content_fn": lambda choice: {
                    "No puedo conciliar el sueño": (
                        "📌 *Tipo de recurso:* Infografía higiene del sueño\n"
                        "Factores clave antes de acostarte.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Evitar pantallas y cafeína mejora la conciliación."
                    ),
                    "Me despierto muchas veces": (
                        "📌 *Tipo de recurso:* Audio de reinducción\n"
                        "Ejercicios suaves para volver a dormir.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Respiraciones profundas y conteo regresivo."
                    ),
                    "Duermo pero no descanso": (
                        "📌 *Tipo de recurso:* Video fases del sueño\n"
                        "Comprender el ciclo circadiano.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Ajustar rutina de luz y oscuridad."
                    ),
                    "Pesadillas o sobresaltos nocturnos": (
                        "📌 *Tipo de recurso:* Ejercicio de contención nocturna\n"
                        "Técnicas de seguridad emocional para la noche.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Usar un objeto de seguridad (peluche, manta)."
                    ),
                    "Pensamientos intrusivos al acostarme": (
                        "📌 *Tipo de recurso:* Audio de atención plena\n"
                        "Ejercicios de mindfulness antes de dormir.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Centrarte en sensaciones físicas, no en ideas."
                    )
                }.get(choice,
                    "Aquí tenés más información sobre ese tema.\n"
                    "🔔 He enviado este recurso a tu correo.\n"
                    "👉 Implementa estas recomendaciones con tu terapeuta."
                )
            },
            {   # Paso 4: ¿Necesitás más ayuda?
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {   # Paso 5: despedida
                "prompt": (
                    "❤️ *Despedida Sueños:*\n"
                    "Dormir bien es fundamental para tu bienestar. "
                    "Si necesitás más, tu terapeuta puede orientarte. ¡Buenas noches!"
                )
            }
        ]
    },

    "tca": {
        "steps": [
            {   # Paso 0: pedir descripción libre
                "prompt": (
                    "🟢 *Describí tus pensamientos o comportamientos* "
                    "relacionados con la alimentación.\n"
                    "(Por ejemplo: “Tengo miedo a engordar”, "
                    "“Después de comer me siento culpable”, etc.)"
                )
            },
            {   # Paso 1: confirmación detección
                "prompt": (
                    "🌿 *Detección de TCA*\n\n"
                    "Lo que describiste coincide con patrones de "
                    "*Trastornos de la Conducta Alimentaria*. "
                    "¿Querés revisar contenidos psicoeducativos sobre TCA?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: confirmar envío y elegir sensación/conducta
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Qué sensación o conducta refleja mejor tu experiencia?"
                ),
                "options": [
                    "Miedo a engordar",
                    "Culpa después de comer",
                    "Atracones incontrolables",
                    "Insatisfacción con mi cuerpo",
                    "Conductas de compensación"
                ]
            },
            {   # Paso 3: entregar contenido según elección
                "content_fn": lambda choice: {
                    "Miedo a engordar": (
                        "📌 *Tipo de recurso:* Infografía ciclo culpa–compensación\n"
                        "Cómo interrumpir patrones restrictivos.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Reconocer la función de la emoción es clave."
                    ),
                    "Culpa después de comer": (
                        "📌 *Tipo de recurso:* Audio de contención emocional\n"
                        "Técnicas para soltar la culpa post-comida.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Practicar autocompasión tras la comida."
                    ),
                    "Atracones incontrolables": (
                        "📌 *Tipo de recurso:* Diario reflexivo + plan de acción\n"
                        "Registro de emociones previas al atracón.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Identificar desencadenantes y alternativas."
                    ),
                    "Insatisfacción con mi cuerpo": (
                        "📌 *Tipo de recurso:* Ejercicio espejo + frases respetuosas\n"
                        "Práctica diaria de apreciación corporal.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Reconocer cualidades más allá del físico."
                    ),
                    "Conductas de compensación": (
                        "📌 *Tipo de recurso:* Guía para familiares y cuidadores\n"
                        "Cómo apoyar sin promover purgas o ejercicios excesivos.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Establecer límites saludables y comprensión."
                    )
                }.get(choice,
                    "Aquí tenés más información sobre ese tema.\n"
                    "🔔 He enviado este recurso a tu correo.\n"
                    "👉 Implementa estas recomendaciones con tu terapeuta."
                )
            },
            {   # Paso 4: ¿Necesitás más ayuda?
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {   # Paso 5: despedida
                "prompt": (
                    "❤️ *Despedida TCA:*\n"
                    "Tu valor no está en tu cuerpo ni en lo que comes. "
                    "Si necesitás más, tu terapeuta está disponible. ¡Hasta luego!"
                )
            }
        ]
    },

    "toc": {
        "steps": [
            {   # Paso 0: pedir descripción libre
                "prompt": (
                    "🟢 *Describí tus pensamientos o rituales* relacionados con TOC.\n"
                    "(Por ejemplo: “Reviso todo muchas veces”, "
                    "“Me lavo las manos constantemente”, etc.)"
                )
            },
            {   # Paso 1: confirmación detección
                "prompt": (
                    "🌿 *Detección de TOC*\n\n"
                    "Lo que describiste coincide con patrones de "
                    "*Trastorno Obsesivo Compulsivo*. "
                    "¿Querés revisar contenidos psicoeducativos sobre TOC?"
                ),
                "options": ["Sí", "No"]
            },
            {   # Paso 2: confirmar envío y elegir síntoma
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Qué síntoma describe mejor tu experiencia?"
                ),
                "options": [
                    "Pensamientos intrusivos",
                    "Rituales repetitivos",
                    "Necesidad de orden",
                    "Lavado de manos excesivo",
                    "Revisión constante de objetos"
                ]
            },
            {   # Paso 3: entregar contenido según elección
                "content_fn": lambda choice: {
                    "Pensamientos intrusivos": (
                        "📌 *Tipo de recurso:* Cápsula explicativa + ejercicio de distanciamiento\n"
                        "Cómo reconocer y desapegarte de los pensamientos.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Técnica de “observador” para separar idea de yo."
                    ),
                    "Rituales repetitivos": (
                        "📌 *Tipo de recurso:* Infografía ciclo compulsión–alivio\n"
                        "Entender el ciclo y dónde intervenir.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Practicar exposición sin realizar ritual."
                    ),
                    "Necesidad de orden": (
                        "📌 *Tipo de recurso:* Analogía ilustrada + pauta\n"
                        "Cómo flexibilizar expectativas de perfección.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Introducir variaciones mínimas en rutina."
                    ),
                    "Lavado de manos excesivo": (
                        "📌 *Tipo de recurso:* Video + hoja de prevención consciente\n"
                        "Alternativas seguras para la higiene.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Reducir gradualmente la frecuencia."
                    ),
                    "Revisión constante de objetos": (
                        "📌 *Tipo de recurso:* Registro de autoobservación + pistas\n"
                        "Técnicas de anclaje para detener la comprobación.\n"
                        "🔔 He enviado este recurso a tu correo.\n\n"
                        "👉 Marcar límites temporales claros."
                    )
                }.get(choice,
                    "Aquí tenés más información sobre ese tema.\n"
                    "🔔 He enviado este recurso a tu correo.\n"
                    "👉 Implementa estas recomendaciones con tu terapeuta."
                )
            },
            {   # Paso 4: ¿Necesitás más ayuda?
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {   # Paso 5: despedida
                "prompt": (
                    "❤️ *Despedida TOC:*\n"
                    "Entender tu TOC es un paso hacia la libertad. "
                    "Si necesitás más, tu terapeuta está ahí. ¡Hasta pronto!"
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
# Función de detección de tópico (umbral = 2)
# ----------------------------------------
def detect_topic(text):
    scores = {}
    for topic, kws in TOPIC_KEYWORDS.items():
        scores[topic] = sum(
            bool(re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE))
            for kw in kws
        )
    topic, max_score = max(scores.items(), key=lambda x: x[1])
    return topic if max_score >= 2 else None

# ----------------------------------------
# Dispatcher de flujos de Psicoeducación
# ----------------------------------------
def dispatch_flow(number, messageId, text, topic):
    cfg = session_states.get(number)
    if not cfg:
        session_states[number] = {"topic": topic, "step": 0}
        cfg = session_states[number]

    step  = cfg["step"]
    topic = cfg["topic"]
    steps = FLOWS[topic]["steps"]

    # Paso 0 → prompt libre
    if step == 0:
        cfg["step"] = 1
        return enviar_Mensaje_whatsapp(text_Message(number, steps[0]["prompt"]))

    # Paso 1 → confirmación detección
    if step == 1:
        user_text = text.strip()
        detected = detect_topic(user_text)
        if not detected:
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(
                number,
                "No detecté síntomas claros de ningún flujo.\nPodés describir más o consultar un profesional."
            ))
        cfg["topic"] = detected
        cfg["step"]   = 2
        step1 = FLOWS[detected]["steps"][1]
        return enviar_Mensaje_whatsapp(
            buttonReply_Message(
                number,
                step1["options"],
                step1["prompt"],
                detected.capitalize(),
                f"{detected}_confirm",
                messageId
            )
        )

    # Paso 2 → “No” termina, “Sí” avanza
    if step == 2:
        if text.endswith("_btn_2"):
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(number, "¡Gracias por usar AMPARA!"))
        cfg["step"] = 3
        step2 = FLOWS[topic]["steps"][2]
        return enviar_Mensaje_whatsapp(
            listReply_Message(
                number,
                step2["options"],
                step2["prompt"],
                topic.capitalize(),
                f"{topic}_sens",
                messageId
            )
        )

    # Paso 3 → entrega contenido
    if step == 3:
        idx = int(text.split("_")[-1]) - 1
        sel = FLOWS[topic]["steps"][2]["options"][idx]
        cont = FLOWS[topic]["steps"][3]["content_fn"](sel)
        enviar_Mensaje_whatsapp(text_Message(number, cont))
        cfg["step"] = 4
        return enviar_Mensaje_whatsapp(
            buttonReply_Message(
                number, ["Sí","No"],
                "¿Necesitás más ayuda?", "AMPARA IA",
                f"{topic}_more", messageId
            )
        )

    # Paso 4 → volver al menú o despedida
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
        session_states.pop(number)
        despedida = FLOWS[topic]["steps"][-1]["prompt"]
        return enviar_Mensaje_whatsapp(text_Message(number, despedida))

# ----------------------------------------
# Dispatcher de Informe al Terapeuta (fragmento con la clasificación actualizada)
# ----------------------------------------
def dispatch_informe(number, messageId, text):
    cfg = session_states.get(number)
    if not cfg:
        session_states[number] = {"topic": "informe", "step": 0}
        cfg = session_states[number]

    step = cfg["step"]

    # Paso 0: pedir motivo de consulta
    if step == 0:
        cfg["step"] = 1
        prompt = (
            "📝 *Informe al Terapeuta*\n\n"
            "Por favor, describí el motivo de consulta principal."
        )
        return enviar_Mensaje_whatsapp(text_Message(number, prompt))

    # Paso 1: clasificar riesgo y preguntar recordatorio
    if step == 1:
        motivo = text.strip()
        cfg["motivo"] = motivo

        # clasificación por orden de mayor a menor
        risk = "Sin riesgo detectado"
        for nivel, kws in RISK_KEYWORDS.items():
            if any(re.search(rf"\b{re.escape(kw)}\b", motivo, re.IGNORECASE) for kw in kws):
                risk = nivel
                break
        # si no matchea con ninguno, consideramos riesgo bajo
        if risk == "Sin riesgo detectado":
            risk = "Riesgo bajo"

        cfg["risk"] = risk
        cfg["step"] = 2

        prompt = (
            f"⚠️ *Clasificación de riesgo:* {risk}\n\n"
            "¿Querés programar un recordatorio diario de ejercicios de respiración a las 09:00?"
        )
        return enviar_Mensaje_whatsapp(
            buttonReply_Message(
                number,
                ["Sí", "No"],
                prompt,
                "Informe al Terapeuta",
                "informe_reminder",
                messageId
            )
        )

    # Paso 2: guardar recordatorio y enviar informe final
    if step == 2:
        if text.endswith("_btn_1"):
            cfg["reminder"] = "Programado diario a las 09:00"
            # aquí podrías crear la automación con automations.create(...)
        else:
            cfg["reminder"] = "No programado"

        report = (
            "📝 *Informe al Terapeuta*\n\n"
            f"• *Motivo de consulta:* {cfg['motivo']}\n"
            f"• *Clasificación de riesgo:* {cfg['risk']}\n"
            f"• *Recordatorio respiración:* {cfg['reminder']}"
        )
        session_states.pop(number)
        return enviar_Mensaje_whatsapp(text_Message(number, report))

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

    # Inicia Psicoeducación Interactiva
    if text == "main_menu_btn_1":
        return dispatch_flow(number, messageId, "", "ansiedad")

    # Inicia Informe al Terapeuta
    if text == "main_menu_btn_2":
        return dispatch_informe(number, messageId, "")

    # Si ya estamos en un flujo de psicoeducación...
    if number in session_states and session_states[number].get("topic") != "informe":
        topic = session_states[number]["topic"]
        return dispatch_flow(number, messageId, text, topic)

    # Si estamos en informe
    if number in session_states and session_states[number].get("topic") == "informe":
        return dispatch_informe(number, messageId, text)

    # Cualquier otro input
    return enviar_Mensaje_whatsapp(
        text_Message(number, "No entendí. Escribí 'hola' para volver al menú.")
    )
