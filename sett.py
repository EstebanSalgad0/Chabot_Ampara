import requests  # Importa requests para hacer solicitudes HTTP

# Token de acceso para verificar la suscripción
token = 'MedicAI'

# Token de acceso y URL de la API de WhatsApp
whatsapp_token = 'EAAGSmHLF8ecBOZCjwuPkZCVzrI6VGCsf8B8DlwsdV6f3ZC6ZBgdHbKnTE4ZBAZAEd1OKvaM9D8DqZCPOIVdmYJHjljFBCKJU5043tzLGVD6qnBZAZAkSOewgN2G5hav0VaxKEsz0HhN7Khv3wlbQ0cA4f7RKoau1UVzuKMwDFDSQiv07PB70cBiAQI8HQOa4WZA9SViHCKAG90JrstqX2LWa8ZD'
whatsapp_url = 'https://graph.facebook.com/v19.0/281033528433782/messages'

# Diccionario de stickers con IDs correspondientes
stickers = {
    "poyo_feliz": "984778742532668",
    "perro_traje": "1009219236749949",
    "perro_triste": "982264672785815",
    "pedro_pascal_love": "801721017874258",
    "pelfet": "3127736384038169",
    "anotado": "24039533498978939",
    "gato_festejando": "1736736493414401",
    "okis": "268811655677102",
    "cachetada": "275511571531644",
    "gato_juzgando": "107235069063072",
    "chicorita": "3431648470417135",
    "gato_triste": "210492141865964",
    "gato_cansado": "1021308728970759"
}

# Función para enviar un sticker a través de la API de WhatsApp
def enviar_sticker(sticker_name, recipient_phone_number):
    if sticker_name not in stickers:
        raise ValueError(f"Sticker '{sticker_name}' no encontrado en el diccionario.")
    
    sticker_id = stickers[sticker_name]
    
    headers = {
        'Authorization': f'Bearer {whatsapp_token}',
        'Content-Type': 'application/json'
    }

    data = {
        "messaging_product": "whatsapp",
        "to": recipient_phone_number,
        "type": "sticker",
        "sticker": {
            "id": sticker_id
        }
    }

    response = requests.post(whatsapp_url, headers=headers, json=data)
    
    if response.status_code == 200:
        print("Sticker enviado exitosamente")
    else:
        print(f"Error al enviar el sticker: {response.status_code} - {response.text}")

# Ejemplo de uso
recipient_phone_number = "1234567890"  # Reemplaza con el número de teléfono del destinatario
sticker_name = "poyo_feliz"  # Reemplaza con el nombre del sticker que deseas enviar

enviar_sticker(sticker_name, recipient_phone_number)  # Envía el sticker especificado al número de teléfono del destinatario
