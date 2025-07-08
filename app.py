# app.py
import os
from flask import Flask, request
import sett
import services

app = Flask(__name__)

@app.route('/bienvenido', methods=['GET'])
def bienvenido():
    return 'Hola, soy MedicAI, tu asistente virtual. ¿En qué puedo ayudarte?'

@app.route('/webhook', methods=['GET'])
def verificar_token():
    mode      = request.args.get('hub.mode')
    token     = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    # Usamos sett.VERIFY_TOKEN en lugar de sett.token
    if mode == 'subscribe' and token == sett.VERIFY_TOKEN and challenge:
        return challenge, 200
    return 'Token inválido', 403

@app.route('/webhook', methods=['POST'])
def recibir_mensaje():
    try:
        body    = request.get_json(force=True)
        entry   = body['entry'][0]
        changes = entry['changes'][0]
        value   = changes['value']
        # Si es status update, no hay "messages"
        if 'messages' not in value:
            return 'Ignorado', 200

        message   = value['messages'][0]
        number    = message['from']
        messageId = message['id']
        name      = value['contacts'][0]['profile']['name']
        text      = services.obtener_Mensaje_whatsapp(message)

        # Llamamos al dispatcher principal
        services.administrar_chatbot(text, number, messageId, name)
        return 'Enviado', 200

    except KeyError as e:
        return f'KeyError: {e}', 400
    except Exception as e:
        # Para debug puedes imprimir e en logs
        return str(e), 500

if __name__ == '__main__':
    # Usamos el puerto que nos da Railway o 5000 por defecto
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
