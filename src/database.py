import sqlite3
import os

# 1. Obtener la ruta absoluta del directorio donde se encuentra este archivo (src/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Obtener la ruta de la carpeta raíz del proyecto (TFM_MISP_Backend)
RAIZ_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

# 3. Asegurar la ruta absoluta hacia el directorio 'data'
DATA_DIR = os.path.join(RAIZ_DIR, "data")

# 4. Asegurar de forma estricta la existencia de la carpeta 'data/' antes de cualquier operación
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

# 5. Definir la ruta absoluta y definitiva al archivo de la base de datos
DB_NAME = os.path.join(DATA_DIR, "tfm_bot.db")

def inicializar_db():
    """Crea las tablas necesarias para usuarios y logs (OE#4)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Tabla para suscripciones (RF3)
    cursor.execute('''CREATE TABLE IF NOT EXISTS suscripciones 
                      (chat_id INTEGER, pais TEXT, PRIMARY KEY (chat_id, pais))''')
    # Tabla para logs de alertas enviadas (RS5)
    cursor.execute('''CREATE TABLE IF NOT EXISTS alertas_enviadas 
                      (id INTEGER PRIMARY KEY, chat_id INTEGER, ip TEXT, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Tabla para cumplir con RF4 completo log de sistema
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS logs_sistema
                   (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       nivel TEXT, -- INFO, ERROR, METRICA
                       mensaje TEXT, -- Descripción del log
                       tiempo_ms REAL, -- Para métricas de rendimiento (RNF1)
                       fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   ''')

    conn.commit()
    conn.close()


def guardar_suscripcion(chat_id, pais):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO suscripciones (chat_id, pais) VALUES (?, ?)", (chat_id, pais))
        conn.commit()
    finally:
        conn.close()


def obtener_suscriptores(pais):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM suscripciones WHERE pais = ?", (pais,))
    usuarios = [row[0] for row in cursor.fetchall()]
    conn.close()
    return usuarios


def eliminar_suscripcion(chat_id, pais):
    """
    Elimina una suscripción específica y garantiza el Derecho al Olvido (Art. 17 RGPD),
    purgando en cascada el historial de alertas asociadas para evitar retención residual.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # 1. Eliminar el registro de suscripción por país
        cursor.execute("DELETE FROM suscripciones WHERE chat_id = ? AND pais = ?", (chat_id, pais))
        suscripcion_eliminada = cursor.rowcount > 0

        # 2. Verificar si al usuario le quedan otras suscripciones activas
        cursor.execute("SELECT 1 FROM suscripciones WHERE chat_id = ?", (chat_id,))
        tiene_otras_suscripciones = cursor.fetchone() is not None

        # 3. Si el usuario ya no tiene ninguna suscripción activa, se purga todo su historial
        if not tiene_otras_suscripciones:
            cursor.execute("DELETE FROM alertas_enviadas WHERE chat_id = ?", (chat_id,))

        conn.commit()
        return suscripcion_eliminada
    except Exception as e:
        # Garantizar trazabilidad del fallo en la base de datos
        registrar_log("ERROR", f"Fallo en cascada al eliminar suscripción del chat_id {chat_id}: {str(e)}")
        return False
    finally:
        conn.close()


def alerta_ya_enviada(chat_id, ip):
    """Verifica si esta IP ya fue notificada a este usuario (Evita duplicidad)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM alertas_enviadas WHERE chat_id = ? AND ip = ?", (chat_id, ip))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe


def registrar_alerta_enviada(chat_id, ip):
    """Registra el envío exitoso para trazabilidad y métricas (OE#4)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO alertas_enviadas (chat_id, ip) VALUES (?, ?)", (chat_id, ip))
        conn.commit()
    finally:
        conn.close()


def registrar_log(nivel, mensaje, tiempo_ms=0):
    """Guarda logs y métricas directamente en la DB (OE#4)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs_sistema (nivel, mensaje, tiempo_ms) VALUES (?, ?, ?)",
                   (nivel, mensaje, tiempo_ms))
    conn.commit()
    conn.close()


def obtener_suscripciones_por_usuario(chat_id):
    """Consulta la DB para obtener los países de un usuario (OE#4)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT pais FROM suscripciones WHERE chat_id = ?", (chat_id,))
        paises = [row[0] for row in cursor.fetchall()]
        return paises
    except Exception as e:
        print(f"Error al consultar suscripciones: {e}")
        return []
    finally:
        conn.close()