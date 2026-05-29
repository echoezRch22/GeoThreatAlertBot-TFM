import asyncio
import os
import warnings
import time
from src.extractor import MispExtractor
from src.geo_module import obtener_pais_ip, obtener_geo_enriquecida
from src.database import inicializar_db, obtener_suscriptores, registrar_log
from telegram import Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

# Carga de variables de entorno (RS1)
load_dotenv()

# RS2: Ocultar avisos de certificados no válidos en entorno de pruebas
warnings.filterwarnings("ignore")


async def difundir_alertas_pro(atributos, bot, misp_ext):
    """CU04: Difusión con enriquecimiento de Galaxias y Atribución."""
    from src.database import alerta_ya_enviada, registrar_alerta_enviada

    for ioc in atributos:
        geo = obtener_geo_enriquecida(ioc.value)
        usuarios = obtener_suscriptores(geo['pais'])

        for chat_id in usuarios:
            if not alerta_ya_enviada(chat_id, ioc.value):
                detalles = misp_ext.obtener_detalles_evento(ioc.event_id)
                if not detalles: continue

                # Diseño de mensaje
                mensaje = (
                    f"🛡️ *INTELIGENCIA DE AMENAZAS: {detalles['nivel']}*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌐 *IoC (IP):* `{ioc.value}`\n"
                    f"📍 *Ubicación:* {geo['pais']} ({geo['ciudad']})\n"
                    f"⚪ *TLP:* {detalles['tlp']}\n"
                    f"👤 *Atribución:* {detalles['atribucion']}\n"
                    f"📅 *Fecha Evento:* {detalles['fecha']}\n\n"
                    f"📝 *Descripción:* \n_{detalles['info']}_\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 *MISP ID:* {ioc.event_id}"
                )

                # Botones interactivos (Usabilidad RNF5)
                keyboard = [[
                    InlineKeyboardButton("🔍 VirusTotal", url=f"https://www.virustotal.com/gui/ip-address/{ioc.value}"),
                    InlineKeyboardButton("📂 Abrir MISP", url=f"{os.getenv('MISP_URL')}/events/view/{ioc.event_id}")
                ]]

                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=mensaje,
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    registrar_alerta_enviada(chat_id, ioc.value)
                except Exception as e:
                    print(f"Error envío: {e}")

# async def difundir_alertas_pro(atributos, bot, misp_ext):
#     """CU04: Difusión automatizada sin duplicados."""
#     from database import alerta_ya_enviada, registrar_alerta_enviada
#
#     for ioc in atributos:
#         geo = obtener_geo_enriquecida(ioc.value)
#         usuarios = obtener_suscriptores(geo['pais'])
#
#         for chat_id in usuarios:
#             # MEJORA: Solo enviamos si NO ha sido enviada previamente
#             if not alerta_ya_enviada(chat_id, ioc.value):
#                 detalles = misp_ext.obtener_detalles_evento(ioc.event_id)
#                 if not detalles: continue
#
#                 mensaje = (
#                     f"🛡️ *INTELIGENCIA DE AMENAZAS: {detalles['nivel']}*\n"
#                     f"━━━━━━━━━━━━━━━━━━━━\n"
#                     f"🌐 *IoC (IP):* `{ioc.value}`\n"
#                     f"📍 *Ubicación:* {geo['pais']} ({geo['ciudad']})\n"
#                     f"⚪ *TLP:* {detalles['tlp']}\n\n"
#                     f"📝 *Descripción:* \n_{detalles['info']}_\n"
#                     f"━━━━━━━━━━━━━━━━━━━━\n"
#                     f"🆔 *MISP ID:* {ioc.event_id}"
#                 )
#
#                 keyboard = [[
#                     InlineKeyboardButton("🔍 VirusTotal", url=f"https://www.virustotal.com/gui/ip-address/{ioc.value}"),
#                     InlineKeyboardButton("📂 Ver Evento", url=f"{os.getenv('MISP_URL')}/events/view/{ioc.event_id}")
#                 ]]
#
#                 try:
#                     await bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown',
#                                            reply_markup=InlineKeyboardMarkup(keyboard))
#                     # REGISTRO: Guardamos en la tabla alertas_enviadas tras el éxito
#                     registrar_alerta_enviada(chat_id, ioc.value)
#                     print(f"✅ Alerta nueva enviada y registrada: {ioc.value}")
#                 except Exception as e:
#                     print(f"❌ Error al enviar alerta: {e}")
#             else:
#                 # Opcional: Debug para confirmar que el filtro funciona
#                 print(f"⏭️ Saltando {ioc.value} (ya notificada anteriormente)")

# async def ejecutar_sistema():
#     """
#     Orquestador principal que integra la extracción, clasificación y difusión.
#     """
#     # OE#4: Asegurar que la base de datos esté lista para las métricas y suscripciones
#     inicio = time.time()
#     inicializar_db()
#
#     print("🚀 Iniciando sistema Geo-CTI (MISP + Telegram)...")
#
#     # 1. Conexión y Extracción (OE#1 / RF1)
#     misp_ext = MispExtractor()
#     atributos = misp_ext.extraer_ips(limite=10)
#
#     if not atributos:
#         print("⚠️ No se recuperaron atributos de MISP.")
#         return
#
#     # Instanciar el Bot de Telegram (RS1)
#     token = os.getenv('TELEGRAM_TOKEN')
#     bot = Bot(token=token)
#
#     # 2. Procesamiento, Clasificación y Visualización (OE#2)
#     print(f"\n{'IP':<18} | {'PAÍS':<20} | {'EVENTO ID':<10}")
#     print("-" * 55)
#
#     for ioc in atributos:
#         pais = obtener_pais_ip(ioc.value)
#         print(f"{ioc.value:<18} | {pais:<20} | {ioc.event_id:<10}")
#
#     # 3. Difusión automatizada segmentada (OE#3 / RF3)
#     await difundir_alertas_pro(atributos, bot, misp_ext)
#
#     print("\n✅ Ciclo de ejecución completado con éxito.")


async def ejecutar_sistema():
    """
    Orquestador principal con registro de logs y métricas para cumplimiento de RF4.
    """
    inicio = time.time()
    inicializar_db() # OE#4: Asegurar tablas de suscripciones, alertas y logs

    try:
        registrar_log("INFO", "🚀 Iniciando ciclo de ejecución del sistema")
        print("🚀 Iniciando sistema Geo-CTI (MISP + Telegram)...")

        # 1. Conexión y Extracción (OE#1 / RF1)
        misp_ext = MispExtractor()
        atributos = misp_ext.extraer_ips(limite=50) # Aumentado para mejor muestreo

        if not atributos:
            registrar_log("ADVERTENCIA", "No se recuperaron nuevos atributos de MISP")
            print("⚠️ No se recuperaron atributos de MISP.")
            return

        # Instanciar el Bot de Telegram (RS1)
        token = os.getenv('TELEGRAM_TOKEN')
        bot = Bot(token=token)

        # 2. Procesamiento y Clasificación (OE#2)
        # Aquí también podemos registrar eventos descartados si no tienen IP válida
        print(f"\n{'IP':<18} | {'PAÍS':<20} | {'EVENTO ID':<10}")
        print("-" * 55)

        for ioc in atributos:
            pais = obtener_pais_ip(ioc.value)
            print(f"{ioc.value:<18} | {pais:<20} | {ioc.event_id:<10}")

        # 3. Difusión automatizada segmentada (OE#3 / RF3)
        await difundir_alertas_pro(atributos, bot, misp_ext)

        # 4. Registro de Métricas de Rendimiento (RF4 / RNF1)
        fin = time.time()
        latencia_ms = (fin - inicio) * 1000
        registrar_log("METRICA", f"Ciclo completado con éxito. Atributos: {len(atributos)}", latencia_ms)
        print(f"\n✅ Ciclo completado en {latencia_ms:.2f}ms.")

    except Exception as e:
        # Registro de Errores (RF4)
        error_msg = f"Fallo crítico en el orquestador: {str(e)}"
        registrar_log("ERROR", error_msg)
        print(f"❌ {error_msg}")

if __name__ == "__main__":
    # RNF1: La ejecución asíncrona optimiza el rendimiento
    # asyncio.run(ejecutar_sistema())

    # RF5: El sistema debe ejecutar consultas de forma automática
    INTERVALO_MINUTOS = 10

    while True:
        asyncio.run(ejecutar_sistema())
        print(f"😴 Esperando {INTERVALO_MINUTOS} minutos para la próxima búsqueda...")
        time.sleep(INTERVALO_MINUTOS * 60)