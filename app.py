from flask import Flask, request
import sett
import services

app = Flask(__name__)

@app.route('/bienvenido', methods=['GET'])
def bienvenido():
    return 'Hola, soy Mateo, tu asistente virtual Educacional. ¿En qué puedo ayudarte?'

@app.route('/webhook', methods=['GET'])
def verificar_token():
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if token == sett.token and challenge:
        return challenge
    return 'Token inválido', 403

@app.route('/webhook', methods=['POST'])
def recibir_mensaje():
    try:
        body = request.get_json()
        entry = body['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        # Si es status update, no hay "messages"
        if 'messages' not in value:
            return 'Ignorado', 200

        message = value['messages'][0]
        number = message['from']
        messageId = message['id']
        name = value['contacts'][0]['profile']['name']
        text = services.obtener_Mensaje_whatsapp(message)

        services.administrar_chatbot(text, number, messageId, name)
        return 'enviado', 200

    except KeyError as e:
        return f'KeyError: {e}', 403
    except Exception as e:
        return str(e), 403

if __name__ == '__main__':
    app.run()
