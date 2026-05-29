from telegram.ext import ApplicationBuilder, CommandHandler
from telegram_bot import ThreatBot
import os
from dotenv import load_dotenv

load_dotenv()

#if __name__ == "__main__":
#    app_telegram_bot = ThreatBot()
#   app = ApplicationBuilder().token(os.getenv('TELEGRAM_TOKEN')).build()
#    app.add_handler(CommandHandler('start', app_telegram_bot.start))
#    app.add_handler(CommandHandler('suscribir', app_telegram_bot.suscribir))
#    print("🤖 Bot activo. Ve a Telegram y escribe /suscribir China")
#   app.run_polling()

if __name__ == "__main__":
    # Simplemente instancia la clase y llama a su método run()
    # Este método ya tiene configurados todos los comandos y el manejador de texto
    bot = ThreatBot()
    bot.run()