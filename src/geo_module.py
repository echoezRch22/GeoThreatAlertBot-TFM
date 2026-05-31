import geoip2.database
import os

# Ruta relativa para asegurar portabilidad (RNF3)
DB_PATH = os.path.join('../data', 'GeoLite2-City.mmdb')

def obtener_pais_ip(ip):
    """
    Determina el país de una IP para la segmentación geográfica (OE#2).
    """
    if not os.path.exists(DB_PATH):
        return "Desconocido (DB no encontrada)"

    try:
        with geoip2.database.Reader(DB_PATH) as reader:
            response = reader.city(ip)
            # Retornamos el nombre del país (necesario para filtrar canales de Telegram)
            return response.country.name if response.country.name else "Desconocido"
    except Exception:
        return "Desconocido"

def obtener_geo_enriquecida(ip):
    """OE#2: Clasificación geográfica detallada (País, Ciudad, ISP)"""
    if not os.path.exists(DB_PATH):
        return {"pais": "Desconocido", "ciudad": "-", "isp": "-"}

    try:
        with geoip2.database.Reader(DB_PATH) as reader:
            res = reader.city(ip)
            return {
                "pais": res.country.name or "Desconocido",
                "ciudad": res.city.name or "Desconocida",
                # Nota: Para ISP se requiere GeoLite2-ASN. Si no la tienes, se omite.
                "isp": "Verificado por DB"
            }
    except:
        return {"pais": "Desconocido", "ciudad": "-", "isp": "-"}