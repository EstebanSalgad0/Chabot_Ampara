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
            {   # Paso 2: envío y elección de tema
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Qué tema te gustaría explorar?"
                ),
                "options": [
                    "¿Qué es el espectro autista y por qué es tan diverso?",
                    "Procesamiento sensorial: luces, sonidos, texturas",
                    "Anticipación de rutinas y apoyos visuales",
                    "Comunicación respetuosa y sin presión",
                    "Cómo explicar el TEA a otros desde una mirada inclusiva"
                ]
            },
            {   # Paso 3: entregar contenido según elección
                "content_fn": lambda choice: {
                    "¿Qué es el espectro autista y por qué es tan diverso?": (
                        "📌 *Tipo de recurso:* Video corto + Documento explicativo\n"
                        "Explicación sobre neurodiversidad y diversidad dentro del TEA.\n"
                        "🔔 Recurso enviado a tu correo.\n"
                        "👉 Conocer esta base te ayudará a comprender mejor."
                    ),
                    "Procesamiento sensorial: luces, sonidos, texturas": (
                        "📌 *Tipo de recurso:* Infografía + Checklist sensorial\n"
                        "Perfil de hipersensibilidad/hiposensibilidad y cómo adaptar el entorno.\n"
                        "🔔 Recurso enviado a tu correo.\n"
                        "👉 Útil para ajustar estímulos en casa o en el colegio."
                    ),
                    "Anticipación de rutinas y apoyos visuales": (
                        "📌 *Tipo de recurso:* Calendario pictográfico editable\n"
                        "Cómo usar apoyos visuales para reducir la ansiedad por cambios.\n"
                        "🔔 Recurso enviado a tu correo.\n"
                        "👉 Planificar con anticipación genera seguridad."
                    ),
                    "Comunicación respetuosa y sin presión": (
                        "📌 *Tipo de recurso:* Guía básica + ejemplos\n"
                        "Estrategias de comunicación alternativa y escucha activa.\n"
                        "🔔 Recurso enviado a tu correo.\n"
                        "👉 Facilita la interacción sin forzar respuestas."
                    ),
                    "Cómo explicar el TEA a otros desde una mirada inclusiva": (
                        "📌 *Tipo de recurso:* Cuento ilustrado + ficha descargable\n"
                        "Material para sensibilizar a familiares y docentes.\n"
                        "🔔 Recurso enviado a tu correo.\n"
                        "👉 Promueve el respeto y la comprensión del TEA."
                    )
                }.get(choice,
                    "Aquí tenés más información sobre ese tema.\n"
                    "🔔 Recurso enviado a tu correo.\n"
                    "👉 Implementar estas recomendaciones puede ayudar."
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
            {
                "prompt": (
                    "🟢 *Describí los comportamientos o sensaciones* "
                    "que experimentás o que observás en el contexto de TDAH.\n"
                    "(Por ejemplo: “Me distraigo con cualquier cosa”, "
                    "“No paro quieto en clase”, etc.)"
                )
            },
            {
                "prompt": (
                    "🌿 *Detección de TDAH*\n\n"
                    "Lo que describiste coincide con patrones de *TDAH*. "
                    "¿Querés revisar contenidos psicoeducativos sobre TDAH?"
                ),
                "options": ["Sí", "No"]
            },
            {
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Sobre qué te gustaría aprender hoy?"
                ),
                "options": [
                    "¿Qué es el TDAH y cómo funciona el cerebro?",
                    "Estrategias para organizar tareas y enfocarse",
                    "Cómo manejar la impulsividad con menos culpa",
                    "Qué hacer en casa o escuela para ayudar",
                    "Recursos visuales y rutinas estructuradas"
                ]
            },
            {
                "content_fn": lambda choice: {
                    "¿Qué es el TDAH y cómo funciona el cerebro?": (
                        "📌 *Tipo de recurso:* Video breve + infografía\n"
                        "Explicación del funcionamiento atencional en TDAH.\n"
                        "🔔 Te lo envié al correo.\n"
                        "👉 Conocer tu cerebro es el primer paso para adaptarte."
                    ),
                    "Estrategias para organizar tareas y enfocarse": (
                        "📌 *Tipo de recurso:* Checklist + ejemplo diario\n"
                        "Técnicas de planificación simple y recordatorios visuales.\n"
                        "🔔 Te lo envié al correo.\n"
                        "👉 Facilita el seguimiento de tus tareas."
                    ),
                    "Cómo manejar la impulsividad con menos culpa": (
                        "📌 *Tipo de recurso:* Guía práctica + audio\n"
                        "Técnicas de pausa y reflexión antes de actuar.\n"
                        "🔔 Te lo envié al correo.\n"
                        "👉 Te ayudará a ganar control sobre impulsos."
                    ),
                    "Qué hacer en casa o escuela para ayudar": (
                        "📌 *Tipo de recurso:* Ficha de apoyo escolar\n"
                        "Sugerencias para docentes y familia.\n"
                        "🔔 Te lo envié al correo.\n"
                        "👉 Apoya un entorno más comprensible."
                    ),
                    "Recursos visuales y rutinas estructuradas": (
                        "📌 *Tipo de recurso:* Plantillas editables\n"
                        "Rutinas visuales y recordatorios sonoros.\n"
                        "🔔 Te lo envié al correo.\n"
                        "👉 Refuerza la organización diaria."
                    )
                }.get(choice,
                    "Aquí tenés más info sobre eso.\n"
                    "🔔 Te lo envié al correo.\n"
                    "👉 Implementa estas ideas paso a paso."
                )
            },
            {
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {
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
            {
                "prompt": (
                    "🟢 *Describí tus sensaciones o pensamientos* "
                    "relacionados con TLP.\n"
                    "(Por ejemplo: “Me enojo muy rápido”, “Siento miedo al abandono”, etc.)"
                )
            },
            {
                "prompt": (
                    "🌿 *Detección de TLP*\n\n"
                    "Lo que describiste coincide con patrones de *Trastorno Límite de la Personalidad*. "
                    "¿Querés revisar contenidos psicoeducativos sobre TLP?"
                ),
                "options": ["Sí", "No"]
            },
            {
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Sobre qué tema te gustaría aprender hoy?"
                ),
                "options": [
                    "¿Por qué mis emociones cambian tan rápido?",
                    "Técnicas para regular la angustia o el enojo",
                    "Qué hacer cuando temo al abandono",
                    "Cómo hablar de esto con alguien cercano",
                    "Estrategias DBT para el día a día"
                ]
            },
            {
                "content_fn": lambda choice: {
                    "¿Por qué mis emociones cambian tan rápido?": (
                        "📌 *Tipo de recurso:* Infografía + audio\n"
                        "Ciclo emocional y su función.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Comprender el ciclo es clave para regularlo."
                    ),
                    "Técnicas para regular la angustia o el enojo": (
                        "📌 *Tipo de recurso:* Ejercicio guiado + ficha\n"
                        "Prácticas de pausa emocional y respiración.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Útil para momentos de alta intensidad."
                    ),
                    "Qué hacer cuando temo al abandono": (
                        "📌 *Tipo de recurso:* Cápsula validante\n"
                        "Anclajes y ejercicios para el miedo al abandono.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Te ayudará a generar seguridad interna."
                    ),
                    "Cómo hablar de esto con alguien cercano": (
                        "📌 *Tipo de recurso:* Guía de comunicación\n"
                        "Estrategias para expresar necesidades sin conflicto.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Facilita el apoyo de tu entorno."
                    ),
                    "Estrategias DBT para el día a día": (
                        "📌 *Tipo de recurso:* Guía básica + ejemplos\n"
                        "Herramientas dialéctico-conductuales para regular emociones.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Refuerza tus recursos emocionales."
                    )
                }.get(choice,
                    "Aquí tenés más info sobre eso.\n"
                    "🔔 Enviado a tu correo.\n"
                    "👉 Implementa estas ideas gradualmente."
                )
            },
            {
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {
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
            {
                "prompt": (
                    "🟢 *Describí los recuerdos o sensaciones* relacionadas\n"
                    "con lo que viviste.\n"
                    "(Por ejemplo: “No puedo dejar de pensar en lo que pasó”,\n"
                    "“Tengo pesadillas”, etc.)"
                )
            },
            {
                "prompt": (
                    "🌿 *Detección de TEPT*\n\n"
                    "Lo que describiste coincide con patrones de *Estrés Postraumático*. "
                    "¿Querés revisar contenidos psicoeducativos sobre TEPT?"
                ),
                "options": ["Sí", "No"]
            },
            {
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Sobre qué tema te gustaría aprender?"
                ),
                "options": [
                    "¿Qué es el trauma y cómo lo vive el cuerpo?",
                    "¿Por qué tengo recuerdos o reacciones sin querer?",
                    "Técnicas para sentirme a salvo en el presente",
                    "Cómo explicarlo sin contar todo lo que pasó",
                    "Recursos para momentos de crisis o desregulación"
                ]
            },
            {
                "content_fn": lambda choice: {
                    "¿Qué es el trauma y cómo lo vive el cuerpo?": (
                        "📌 *Tipo de recurso:* Video + resumen en lenguaje claro\n"
                        "Explicación de flashbacks y respuesta fisiológica.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Comprender ayuda a desactivar el miedo."
                    ),
                    "¿Por qué tengo recuerdos o reacciones sin querer?": (
                        "📌 *Tipo de recurso:* Infografía + cápsula sobre anclaje físico\n"
                        "Mecanismos de recuerdos intrusivos y sobresaltos.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Técnicas de grounding para el aquí y ahora."
                    ),
                    "Técnicas para sentirme a salvo en el presente": (
                        "📌 *Tipo de recurso:* Guía práctica + audio de relajación\n"
                        "Estrategias de anclaje y respiración.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Útil para lidiar con hiperalerta."
                    ),
                    "Cómo explicarlo sin contar todo lo que pasó": (
                        "📌 *Tipo de recurso:* Frases modelo + guía de comunicación segura\n"
                        "Cómo compartir sin retraumatizar.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Facilita que otros entiendan sin detalles."
                    ),
                    "Recursos para momentos de crisis o desregulación": (
                        "📌 *Tipo de recurso:* Checklist de autocuidado\n"
                        "Rutinas de contención y redes de apoyo.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Para usar cuando te sientas activado/a."
                    )
                }.get(choice,
                    "Aquí tenés más información sobre el TEPT.\n"
                    "🔔 Enviado a tu correo.\n"
                    "👉 Implementa estas recomendaciones con tu terapeuta."
                )
            },
            {
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {
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
            {
                "prompt": (
                    "🟢 *Describí tus dificultades para dormir*.\n"
                    "(Por ejemplo: “No puedo conciliar el sueño”,\n"
                    "“Me despierto muchas veces”, etc.)"
                )
            },
            {
                "prompt": (
                    "🌿 *Detección de trastornos del sueño*\n\n"
                    "Lo que describiste coincide con patrones de *trastornos del sueño*. "
                    "¿Querés revisar contenidos psicoeducativos sobre el descanso?"
                ),
                "options": ["Sí", "No"]
            },
            {
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Qué tema te interesa hoy?"
                ),
                "options": [
                    "¿Cómo funciona el ciclo del sueño y por qué se altera?",
                    "Estrategias para conciliar el sueño sin frustración",
                    "Qué hacer cuando me despierto de madrugada",
                    "Cómo preparar un ambiente propicio para dormir",
                    "Audios y rutinas para ayudar al descanso"
                ]
            },
            {
                "content_fn": lambda choice: {
                    "¿Cómo funciona el ciclo del sueño y por qué se altera?": (
                        "📌 *Tipo de recurso:* Video + explicación sobre ciclo circadiano\n"
                        "Descripción de fases y su regulación.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Conocer el ciclo ayuda a identificar problemas."
                    ),
                    "Estrategias para conciliar el sueño sin frustración": (
                        "📌 *Tipo de recurso:* Infografía + checklist editable\n"
                        "Técnicas de higiene del sueño.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Útil para preparar la noche."
                    ),
                    "Qué hacer cuando me despierto de madrugada": (
                        "📌 *Tipo de recurso:* Audio de reinducción\n"
                        "Ejercicio de reinducción y relajación.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Practícalo para volver a dormir."
                    ),
                    "Cómo preparar un ambiente propicio para dormir": (
                        "📌 *Tipo de recurso:* Guía básica + ejemplos\n"
                        "Consejos de luz, sonido y temperatura.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Mejora tu entorno de descanso."
                    ),
                    "Audios y rutinas para ayudar al descanso": (
                        "📌 *Tipo de recurso:* Rutinas nocturnas + audios de relajación\n"
                        "Protocolos para antes de acostarse.\n"
                        "🔔 Enviado a tu correo.\n"
                        "👉 Crea un ritual de descanso efectivo."
                    )
                }.get(choice,
                    "Aquí tenés más información sobre el sueño.\n"
                    "🔔 Enviado a tu correo.\n"
                    "👉 Implementa estas ideas junto a tu terapeuta."
                )
            },
            {
                "prompt": "¿Necesitás más ayuda?",
                "options": ["Sí", "No"]
            },
            {
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
            {   # Paso 0: descripción libre
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
            {   # Paso 2: elección de tema
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Qué tema te interesa hoy?"
                ),
                "options": [
                    "¿Por qué la comida genera tanta culpa o ansiedad?",
                    "Imagen corporal y presión social",
                    "Cómo frenar pensamientos dañinos",
                    "Frases de autocuidado y validación",
                    "Guía para familiares y cuidadores"
                ]
            },
            {   # Paso 3: entregar contenido
                "content_fn": lambda choice: {
                    "¿Por qué la comida genera tanta culpa o ansiedad?": (
                        "📌 *Tipo de recurso:* Infografía + audio de contención\n"
                        "Ciclo culpa–compensación y cómo interrumpirlo.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Reconocer el ciclo es el primer paso para cambiarlo."
                    ),
                    "Imagen corporal y presión social": (
                        "📌 *Tipo de recurso:* Ejercicio espejo + frases respetuosas\n"
                        "Cómo aceptar el cuerpo y cuestionar estándares.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Practica la autocompasión diariamente."
                    ),
                    "Cómo frenar pensamientos dañinos": (
                        "📌 *Tipo de recurso:* Gráfico comparativo + diario reflexivo\n"
                        "Distinción entre hambre emocional y física.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Registra tus pensamientos antes de actuar."
                    ),
                    "Frases de autocuidado y validación": (
                        "📌 *Tipo de recurso:* Cápsula educativa + carta de autorreconocimiento\n"
                        "Afirmaciones para romper el silencio.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Úsalas cuando te sientas vulnerable."
                    ),
                    "Guía para familiares y cuidadores": (
                        "📌 *Tipo de recurso:* Ficha breve + decálogo para cuidadores\n"
                        "Cómo apoyar sin juzgar.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Comparte este material con tu red de apoyo."
                    )
                }.get(choice,
                    "Aquí tenés más info sobre TCA.\n"
                    "🔔 Enviado a tu correo.\n\n"
                    "👉 Implementa estas recomendaciones con tu terapeuta."
                )
            },
            {   # Paso 4: más ayuda
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
            {   # Paso 0: descripción libre
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
            {   # Paso 2: elección de tema
                "prompt": (
                    "Gracias. He enviado tu descripción al correo de tu terapeuta.\n\n"
                    "¿Qué tema te gustaría explorar?"
                ),
                "options": [
                    "¿Qué son obsesiones y compulsiones?",
                    "¿Por qué no puedo parar si es irracional?",
                    "Cómo funciona el ciclo obsesión–ritual",
                    "Frases para compartir sin vergüenza",
                    "Prácticas seguras para la ansiedad"
                ]
            },
            {   # Paso 3: entregar contenido
                "content_fn": lambda choice: {
                    "¿Qué son obsesiones y compulsiones?": (
                        "📌 *Tipo de recurso:* Cápsula explicativa + ejercicio de distanciamiento\n"
                        "Diferencia entre pensamiento y acto repetitivo.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Comprender la distinción es clave."
                    ),
                    "¿Por qué no puedo parar si es irracional?": (
                        "📌 *Tipo de recurso:* Infografía + analogía ilustrada\n"
                        "Mecanismos del alivio momentáneo y culpa subsecuente.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Reconocer el ciclo ayuda a romperlo."
                    ),
                    "Cómo funciona el ciclo obsesión–ritual": (
                        "📌 *Tipo de recurso:* Video + hoja de prevención consciente\n"
                        "Explicación del ciclo ansiedad–ritual–alivio.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Identifica puntos de intervención."
                    ),
                    "Frases para compartir sin vergüenza": (
                        "📌 *Tipo de recurso:* Audio validante + guía de comunicación\n"
                        "Cómo explicar tu experiencia sin culpa.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Facilita el apoyo de otros."
                    ),
                    "Prácticas seguras para la ansiedad": (
                        "📌 *Tipo de recurso:* Registro de autoobservación + frases clave\n"
                        "Técnicas de pausa y mindfulness breve.\n"
                        "🔔 Enviado a tu correo.\n\n"
                        "👉 Úsalas en momentos de urgencia."
                    )
                }.get(choice,
                    "Aquí tenés más info sobre TOC.\n"
                    "🔔 Enviado a tu correo.\n\n"
                    "👉 Implementa estas ideas con tu terapeuta."
                )
            },
            {   # Paso 4: más ayuda
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
    # selecciona el tópico con más coincidencias
    topic, max_score = max(scores.items(), key=lambda x: x[1])
    # sólo devuelve un tópico si hay al menos 2 matches
    return topic if max_score >= 2 else None


# ----------------------------------------
# Dispatcher de flujos
# ----------------------------------------
def dispatch_flow(number, messageId, text, topic):
    cfg = session_states.get(number)
    if not cfg:
        # iniciamos conversation con el tópico por defecto (se re-asignará si hay otro match)
        session_states[number] = {"topic": topic, "step": 0}
        cfg = session_states[number]

    step  = cfg["step"]
    topic = cfg["topic"]
    steps = FLOWS[topic]["steps"]

    # Paso 0 → enviamos prompt libre
    if step == 0:
        cfg["step"] = 1
        return enviar_Mensaje_whatsapp(text_Message(number, steps[0]["prompt"]))

    # Paso 1 → detección dinámica y confirmación Sí/No
    if step == 1:
        user_text = text.strip()
        detected = detect_topic(user_text)
        if not detected:
            session_states.pop(number)
            return enviar_Mensaje_whatsapp(text_Message(
                number,
                "No detecté síntomas claros de ningún flujo.\nPodés describir más o consultar un profesional."
            ))
        # reasignamos el flujo si cambió
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

    # Paso 2 → “No” termina, “Sí” avanza a lista de sensaciones
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

    # Paso 3 → entrega contenido y preguntamos más ayuda
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
        session_states.pop(number)
        despedida = FLOWS[topic]["steps"][-1]["prompt"]
        return enviar_Mensaje_whatsapp(text_Message(number, despedida))

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

    # Si ya estamos en un flujo, delegamos
    if number in session_states:
        topic = session_states[number]["topic"]
        return dispatch_flow(number, messageId, text, topic)

    # Cualquier otro input
    return enviar_Mensaje_whatsapp(
        text_Message(number, "No entendí. Escribí 'hola' para volver al menú.")
    )
