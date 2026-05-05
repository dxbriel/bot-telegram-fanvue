from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import os

TOKEN = os.environ.get("TOKEN")
FANVUE_LINK = "https://fanvue.com/camilasoto"
FOTO = "foto.jpg"
ARCHIVO_USUARIOS = "usuarios.json"

MENSAJE_BIENVENIDA = """
Hola 💕 gracias por iniciar mi bot.

Aquí te dejo mi Fanvue:
{link}
"""

MENSAJE_RECORDATORIO = """
Holaa 💕 paso a recordarte que puedes ver mi contenido aquí:

{link}
"""

def cargar_usuarios():
    if os.path.exists(ARCHIVO_USUARIOS):
        with open(ARCHIVO_USUARIOS, "r") as archivo:
            return set(json.load(archivo))
    return set()

def guardar_usuarios(usuarios):
    with open(ARCHIVO_USUARIOS, "w") as archivo:
        json.dump(list(usuarios), archivo)

usuarios = cargar_usuarios()

async def enviar_foto(chat_id, context, mensaje):
    with open(FOTO, "rb") as foto:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=foto,
            caption=mensaje.format(link=FANVUE_LINK)
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    usuarios.add(chat_id)
    guardar_usuarios(usuarios)

    await enviar_foto(chat_id, context, MENSAJE_BIENVENIDA)

    await update.message.reply_text(
        "Recibirás un recordatorio cada 3 días. Usa /stop si quieres dejar de recibirlos."
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    usuarios.discard(chat_id)
    guardar_usuarios(usuarios)

    await update.message.reply_text("Listo, ya no recibirás recordatorios.")

async def recordatorio(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in list(usuarios):
        try:
            await enviar_foto(chat_id, context, MENSAJE_RECORDATORIO)
        except Exception:
            usuarios.discard(chat_id)
            guardar_usuarios(usuarios)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    app.job_queue.run_repeating(
        recordatorio,
        interval=3 * 24 * 60 * 60,
        first=3 * 24 * 60 * 60
    )

    print("Bot encendido...")
    app.run_polling()

if __name__ == "__main__":
    main()