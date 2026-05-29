import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from src.database import guardar_suscripcion
from src.extractor import MispExtractor

load_dotenv()


class ThreatBot:
    def __init__(self):
        # RS1: Token obtenido de variables de entorno [cite: 217]
        self.token = os.getenv('TELEGRAM_TOKEN')

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """CU01: Bienvenida con menú de botones físicos."""
        teclado = [
            ['🌍 Países Disponibles', '📋 Mis Suscripciones'],
            ['ℹ️ Ayuda']
        ]
        # resize_keyboard=True hace que los botones no ocupen toda la pantalla
        # one_time_keyboard=False permite que el menú siempre esté visible
        reply_markup = ReplyKeyboardMarkup(teclado, resize_keyboard=True, one_time_keyboard=False)

        await update.message.reply_text(
            "🛡️ *Geo-CTI Threat Bot*\n"
            "Bienvenido al sistema de difusión de inteligencia segmentada.\n\n"
            "Selecciona una opción del menú inferior:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def suscribir(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Permite al usuario elegir un país para recibir alertas segmentadas.
        Responde al Requisito Funcional RF3[cite: 186].
        """
        if not context.args:
            await update.message.reply_text(
                "❌ Uso: /suscribir [Nombre del Pais en Ingles]\nEjemplo: /suscribir Ecuador"
            )
            return

        # Normalizamos el nombre del país (China, United States, etc.)
        pais = " ".join(context.args).strip()
        chat_id = update.effective_chat.id

        # OE#4: Guardar en la base de datos interna [cite: 153, 191, 193]
        guardar_suscripcion(chat_id, pais)

        await update.message.reply_text(f"✅ Te has suscrito con éxito a las alertas de: {pais}")
        print(f"DEBUG: Usuario {chat_id} suscrito a {pais}")

    async def desuscribir(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Permite al usuario eliminar una suscripción activa (RF3)."""
        if not context.args:
            await update.message.reply_text("❌ Uso: /desuscribir [Pais]\nEjemplo: /desuscribir China")
            return

        pais = " ".join(context.args).strip()
        chat_id = update.effective_chat.id

        from src.database import eliminar_suscripcion
        exito = eliminar_suscripcion(chat_id, pais)

        if exito:
            await update.message.reply_text(f"🗑️ Se ha eliminado tu suscripción a: **{pais}**.")
            print(f"DEBUG: Usuario {chat_id} desuscrito de {pais}")
        else:
            await update.message.reply_text(f"⚠️ No tenías una suscripción activa para: {pais}")

    async def paises_disponibles(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra una lista de países que tienen alertas activas en el sistema."""
        await update.message.reply_text("🔍 Consultando países con actividad reciente en MISP...")

        misp_ext = MispExtractor()
        paises = misp_ext.obtener_lista_paises_disponibles(limite=150)

        if not paises:
            await update.message.reply_text("⚠️ No se detectaron países con IoCs geolocalizables en este momento.")
            return

        lista_texto = "\n".join([f"• {p}" for p in paises])
        mensaje = (
            "🌍 *Países con actividad detectada:*\n\n"
            f"{lista_texto}\n\n"
            "💡 Puedes suscribirte a cualquiera de ellos usando:\n"
            "`/suscribir NombreDelPais`"
        )

        await update.message.reply_text(mensaje, parse_mode='Markdown')

    async def manejador_mensajes_texto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mapea el texto de los botones a las funciones existentes (RNF5)."""
        texto_recibido = update.message.text

        if texto_recibido == '🌍 Países Disponibles':
            # Llamamos a la función que ya tienes (asegúrate que el nombre coincida)
            await self.paises_disponibles(update, context)

        elif texto_recibido == '📋 Mis Suscripciones':
            await self.mostrar_mis_suscripciones(update, context)

        elif texto_recibido == 'ℹ️ Ayuda':
            await update.message.reply_text(
                "📖 *Guía Rápida*\n\n"
                "1. Consulta `/paises_disponibles`.\n"
                "2. Suscríbete con `/suscribir NombrePais`.\n"
                "3. Recibirás alertas automáticas de MISP cada 10 min.",
                parse_mode='Markdown'
            )

    async def mostrar_mis_suscripciones(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra al usuario sus suscripciones actuales (RF3)."""
        chat_id = update.effective_chat.id
        from src.database import obtener_suscripciones_por_usuario

        paises = obtener_suscripciones_por_usuario(chat_id)

        if not paises:
            mensaje = "ℹ️ *Aún no tienes suscripciones activas.*\n\nUsa `/suscribir NombrePais` para empezar a recibir alertas."
        else:
            # Formateamos la lista con bullets para mejor lectura
            lista_formateada = "\n".join([f"• {p}" for p in paises])
            mensaje = (
                "📋 *Tus Suscripciones Activas:*\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"{lista_formateada}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💡 _Para eliminar una, usa: /desuscribir Pais_"
            )

        await update.message.reply_text(mensaje, parse_mode='Markdown')

    def run(self):
        """Inicia el bot y registra los comandos[cite: 190]."""
        if not self.token:
            print("❌ Error: No se encontró TELEGRAM_TOKEN en el entorno.")
            return

        application = ApplicationBuilder().token(self.token).build()

        # Registro de comandos según los casos de uso [cite: 265]
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('suscribir', self.suscribir))
        application.add_handler(CommandHandler('desuscribir', self.desuscribir))
        application.add_handler(CommandHandler('paises_disponibles', self.paises_disponibles))
        application.add_handler(CommandHandler('mis_suscripciones', self.mostrar_mis_suscripciones))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.manejador_mensajes_texto))

        print("🤖 Bot de Telegram en espera de comandos...")
        application.run_polling()



if __name__ == "__main__":
    bot = ThreatBot()
    bot.run()