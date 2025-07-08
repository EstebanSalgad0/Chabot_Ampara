# sett.py
import os

# Carga variables desde el entorno (Railway inyectará estas)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_URL   = os.getenv("WHATSAPP_URL")
VERIFY_TOKEN   = os.getenv("VERIFY_TOKEN")   # <— añadido

if not WHATSAPP_TOKEN or not WHATSAPP_URL or not VERIFY_TOKEN:
    raise RuntimeError(
        "Faltan las variables WHATSAPP_TOKEN, WHATSAPP_URL o VERIFY_TOKEN"
    )
