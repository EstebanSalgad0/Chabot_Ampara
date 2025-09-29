from flask import Flask, request
import sett
import services
import os

app = Flask(__name__)

@app.route('/bienvenido', methods=['GET'])
def bienvenido():
    return 'Hola, soy IAN, tu asistente virtual Educacional. ¿En qué puedo ayudarte?'

@app.route('/status', methods=['GET'])
def status():
    """Endpoint para verificar el estado de la aplicación"""
    try:
        config_status = {
            'WHATSAPP_TOKEN': 'Configurado' if sett.WHATSAPP_TOKEN else 'NO CONFIGURADO',
            'WHATSAPP_URL': 'Configurado' if sett.WHATSAPP_URL else 'NO CONFIGURADO', 
            'VERIFY_TOKEN': 'Configurado' if sett.VERIFY_TOKEN else 'NO CONFIGURADO',
            'EMAIL_USER': 'Configurado' if sett.EMAIL_USER else 'NO CONFIGURADO',
            'EMAIL_PASS': 'Configurado' if sett.EMAIL_PASS else 'NO CONFIGURADO'
        }
        return {
            'status': 'OK',
            'message': 'Chatbot Agente Educacional IAN funcionando correctamente',
            'config': config_status
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'message': f'Error en configuración: {str(e)}'
        }, 500

@app.route('/webhook', methods=['GET'])
def verificar_token():
    try:
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        print(f"Token recibido: {token}")
        print(f"Token esperado: {sett.VERIFY_TOKEN}")
        print(f"Challenge: {challenge}")
        
        if token == sett.VERIFY_TOKEN and challenge:
            print("Token verificado correctamente")
            return challenge
        else:
            print("Token inválido o challenge faltante")
            return 'Token inválido', 403
    except Exception as e:
        print(f"Error en verificación de token: {e}")
        return 'Error en verificación', 403

@app.route('/webhook', methods=['POST'])
def recibir_mensaje():
    try:
        body = request.get_json()
        print(f"Webhook recibido: {body}")
        
        if not body:
            print("No se recibió JSON válido")
            return 'No JSON', 400
            
        entry = body['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        
        # Si es status update, no hay "messages"
        if 'messages' not in value:
            print("Mensaje ignorado: no contiene 'messages'")
            return 'Ignorado', 200

        message = value['messages'][0]
        number = message['from']
        messageId = message['id']
        name = value['contacts'][0]['profile']['name']
        text = services.obtener_Mensaje_whatsapp(message)

        print(f"Procesando mensaje de {name} ({number}): {text}")
        services.administrar_chatbot(text, number, messageId, name)
        return 'enviado', 200

    except KeyError as e:
        print(f'KeyError: {e}')
        print(f'Body recibido: {body}')
        return f'KeyError: {e}', 200  # Cambio a 200 para evitar reenvíos
    except Exception as e:
        print(f'Error general: {e}')
        return 'Error procesado', 200  # Cambio a 200 para evitar reenvíos

if __name__ == '__main__':
    # Configurar el puerto para Railway
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
