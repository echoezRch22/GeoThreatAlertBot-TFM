import os
from pymisp import PyMISP
from geo_module import obtener_pais_ip
from dotenv import load_dotenv

load_dotenv()


class MispExtractor:
    def __init__(self):
        # RS1: Protección de credenciales [cite: 216, 217]
        self.url = os.getenv('MISP_URL')
        self.key = os.getenv('MISP_KEY')
        self.verify = False

        try:
            self.misp = PyMISP(self.url, self.key, self.verify)
        except Exception as e:
            print(f"Error conexión MISP: {e}")
            self.misp = None

    def extraer_ips(self, limite=10):
        """OE#1: Extrae atributos de red para geolocalización."""
        if not self.misp: return []
        return self.misp.search(
            controller='attributes',
            type_attribute=['ip-src', 'ip-dst'],
            limit=limite,
            pythonify=True
        )

    def obtener_detalles_evento(self, event_id):
        """Extrae metadatos avanzados: Info, TLP, Nivel, Actores y Fecha."""
        try:
            evento = self.misp.get_event(event_id, pythonify=True)

            # 1. Extraer TLP
            tlp = "No definido"
            if hasattr(evento, 'tags'):
                for tag in evento.tags:
                    if "tlp:" in tag.name.lower():
                        tlp = tag.name.split("=")[-1].strip('"').upper()

            # 2. Extraer Actor de Amenaza o Malware (Galaxias)
            atribucion = "Desconocida"
            if hasattr(evento, 'clusters'):
                for cluster in evento.clusters:
                    # Buscamos nombres de actores o herramientas
                    atribucion = cluster.value
                    break  # Tomamos el primer cluster relevante

            # 3. Mapeo de nivel de amenaza
            niveles = {"1": "🔴 ALTO", "2": "🟡 MEDIO", "3": "🟢 BAJO", "4": "⚪ INDEFINIDO"}
            amenaza = niveles.get(str(evento.threat_level_id), "⚪ INDEFINIDO")

            return {
                "info": evento.info,
                "tlp": tlp,
                "nivel": amenaza,
                "atribucion": atribucion,
                "fecha": evento.date.strftime('%d-%m-%Y') if hasattr(evento, 'date') else "N/A",
                "id": event_id
            }
        except Exception as e:
            print(f"Error enriqueciendo evento {event_id}: {e}")
            return None

    def obtener_lista_paises_disponibles(self, limite=100):
        """OE#1: Analiza los últimos IoCs para identificar países con actividad."""
        if not self.misp: return []

        atributos = self.extraer_ips(limite=limite)
        paises = set()

        for ioc in atributos:
            # OE#2: Usamos el módulo de geolocalización para clasificar el origen [cite: 151]
            pais = obtener_pais_ip(ioc.value)
            if pais and pais != "Desconocido":
                paises.add(pais)

        return sorted(list(paises))


    # def obtener_detalles_evento(self, event_id):
    #     """
    #     OE#5: Extrae metadatos enriquecidos (Info, TLP, Nivel) para dar contexto[cite: 154].
    #     """
    #     try:
    #         # Analizado en la Tabla 1: /events/get/<id>
    #         evento = self.misp.get_event(event_id, pythonify=True)
    #
    #         # Procesamiento de Taxonomía TLP [cite: 112]
    #         tlp = "No definido"
    #         if hasattr(evento, 'tags'):
    #             for tag in evento.tags:
    #                 if "tlp:" in tag.name.lower():
    #                     tlp = tag.name.split("=")[-1].strip('"').upper()
    #
    #         # Clasificación de nivel de amenaza [cite: 179]
    #         niveles = {"1": "🔴 ALTO", "2": "🟡 MEDIO", "3": "🟢 BAJO", "4": "⚪ INDEFINIDO"}
    #         amenaza = niveles.get(str(evento.threat_level_id), "⚪ INDEFINIDO")
    #
    #         return {
    #             "info": evento.info,
    #             "tlp": tlp,
    #             "nivel": amenaza,
    #             "id": event_id
    #         }
    #     except Exception as e:
    #         print(f"Error al obtener detalles del evento {event_id}: {e}")
    #         return None

    def obtener_detalles_evento(self, event_id):
        """Extrae metadatos avanzados: Info, TLP, Nivel, Actores y Fecha.
        Implementa el requisito de seguridad de discriminación estricta de TLP.
        """
        try:
            evento = self.misp.get_event(event_id, pythonify=True)

            # 1. Extraer TLP de las etiquetas del evento
            tlp = "NO DEFINIDO"
            if hasattr(evento, 'tags'):
                for tag in evento.tags:
                    if "tlp:" in tag.name.lower():
                        # Si la etiqueta es tlp:white, extraerá "WHITE"
                        tlp = tag.name.split(":")[-1].strip('"').upper()

            # --- CONTROL DE SEGURIDAD MIGRADO DE LA LÓGICA CONCEPTUAL ---
            # Si el evento NO es explícitamente público (TLP:WHITE), se bloquea su procesamiento
            if tlp != "WHITE":
                print(
                    f"[BLOQUEO TLP] Evento {event_id} descartado automáticamente. Razón: Restricción de confidencialidad (TLP={tlp})[cite: 1]")
                return None  # Al retornar None, el orquestador sabrá que no debe difundir este IoC[cite: 1]
            # ------------------------------------------------------------

            # 2. Extraer Actor de Amenaza o Malware (Galaxias)
            atribucion = "Desconocida"
            if hasattr(evento, 'clusters'):
                for cluster in evento.clusters:
                    atribucion = cluster.value
                    break

                    # 3. Mapeo de nivel de amenaza
            niveles = {"1": "🔴 ALTO", "2": "🟡 MEDIO", "3": "🟢 BAJO", "4": "⚪ INDEFINIDO"}
            amenaza = niveles.get(str(evento.threat_level_id), "⚪ INDEFINIDO")

            return {
                "info": evento.info,
                "tlp": f"TLP:{tlp}",  # Devolverá "TLP:WHITE" listo para el formateo del bot[cite: 1]
                "nivel": amenaza,
                "atribucion": atribucion,
                "fecha": evento.date.strftime('%d-%m-%Y') if hasattr(evento, 'date') else "N/A",
                "id": event_id
            }
        except Exception as e:
            print(f"Error enriqueciendo evento {event_id}: {e}")
            return None