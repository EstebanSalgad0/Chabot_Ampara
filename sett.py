# sett.py
import os

# Carga variables desde el entorno (Railway inyectará estas)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_URL   = os.getenv("WHATSAPP_URL")

if not WHATSAPP_TOKEN or not WHATSAPP_URL:
    raise RuntimeError("Faltan las variables WHATSAPP_TOKEN o WHATSAPP_URL")
