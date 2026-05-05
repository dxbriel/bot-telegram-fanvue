from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
import threading
import json
import os
import random

TOKEN = os.environ.get("TOKEN")
FANVUE_LINK = "https://fanvue.com/camilasoto"

ARCHIVO_USUARIOS = "usuarios.json"
CARPETA_FOTOS = "fotos"

INTERVALO_RECORDATORIO = 3 * 24 * 60 * 60  # 3 días

MENSAJES_BIENVENIDA = [
    """Ey 💕 qué lindo verte por aquí…

Te dejo mi Fanvue, ahí estoy subiendo contenido nuevo:
{link}""",

    """Holaa 💕 me alegra que hayas llegado hasta aquí.

Pásate por mi Fanvue cuando quieras:
{link}""",

    """Ya estás por aquí 😏💕

Te dejo mi Fanvue para que veas lo nuevo:
{link}"""
]

MENSAJES_RECORDATORIO = [
    """Me pasé por aquí un segundo 💕
Subí cositas nuevas, te dejo el link:

{link}""",

    """Ey 😏 no quería que te perdieras lo nuevo…

{link}""",

    """Holaa 💕 acuérdate de darte una vuelta por mi Fanvue:

{link}""",

    """Tengo contenido nuevo por aquí 😘

{link}""",

    """Solo vengo a dejarte esto por si quieres verme un ratito 💕

{link}""",

    """Te dejo una fotito y mi Fanvue por si hoy te apetece pasar 😏

{link}"""
]


def cargar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS):
        return {}

    try:
        with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if isinstance(datos, list):
            return {str(chat_id): {"ultima_foto": None} for chat_id in datos}

        return datos

    except Exception:
        return {}


usuarios = cargar_usuarios()


def guardar_usuarios():
    with open(ARCHIVO_USUARIOS, "w", encoding="utf-8") as archivo:
        json.dump(usuarios, archivo, indent=2)


def obtener_fotos():
    if not os.path.exists(CARPETA_FOTOS):
        os.makedirs(CARPETA_FOTOS)

    return [
        archivo for archivo in os.listdir(CARPETA_FOTOS)
        if archivo.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ]


def elegir_foto(chat_id):
    fotos = obtener_fotos()

    if not fotos:
        return None

    chat_id = str(chat_id)
    ultima_foto = usuarios.get(chat_id, {}).get("ultima_foto")

    fotos_disponibles = [foto for foto in fotos if foto != ultima_foto]

    if not fotos_disponibles:
        fotos_disponibles = fotos

    foto_elegida = random.choice(fotos_disponibles)

    usuarios.setdefault(chat_id, {})
    usuarios[chat_id]["ultima_foto"] = foto_elegida
    guardar_usuarios()

    return os.path.join(CARPETA_FOTOS, foto_elegida)


async def enviar_contenido(chat_id, context, mensaje):
    texto = mensaje.format(link=FANVUE_LINK)
    ruta_foto = elegir_foto(chat_id)

    if ruta_foto and os.path.exists(ruta_foto):
        with open(ruta_foto, "rb") as foto:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=foto,
                caption=texto
            )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=texto
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    usuarios.setdefault(chat_id, {"ultima_foto": None})
    guardar_usuarios()

    mensaje = random.choice(MENSAJES_BIENVENIDA)
    await enviar_contenido(chat_id, context, mensaje)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    if chat_id in usuarios:
        del usuarios[chat_id]
        guardar_usuarios()

    await update.message.reply_text("Listo 💕 ya no te volveré a escribir por aquí.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandos disponibles:\n\n"
        "/start - Ver contenido\n"
        "/stop - Detener mensajes"
    )


async def recordatorio(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in list(usuarios.keys()):
        try:
            mensaje = random.choice(MENSAJES_RECORDATORIO)
            await enviar_contenido(chat_id, context, mensaje)
        except Exception as e:
            print(f"No se pudo enviar a {chat_id}: {e}")
            usuarios.pop(chat_id, None)
            guardar_usuarios()


# Mini web para que Render detecte puerto y UptimeRobot pueda mantenerlo despierto
app_web = Flask(__name__)


@app_web.route("/")
def home():
    return "Bot activo"


def iniciar_web():
    puerto = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=puerto)


def main():
    if not TOKEN:
        raise ValueError("Falta configurar TOKEN en Render > Environment.")

    threading.Thread(target=iniciar_web, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_command))

    app.job_queue.run_repeating(
        recordatorio,
        interval=INTERVALO_RECORDATORIO,
        first=INTERVALO_RECORDATORIO
    )

    print("Bot encendido...")
    app.run_polling()


if __name__ == "__main__":
    main()