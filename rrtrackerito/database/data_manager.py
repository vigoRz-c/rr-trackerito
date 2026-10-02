import json
import os
import asyncio
from core.logger import log

class DataManager:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._lock = asyncio.Lock()  # Verrou asynchrone

    async def load_data(self) -> dict:
        """Charge le JSON de manière sécurisée."""
        async with self._lock:
            if not os.path.exists(self.filepath):
                return {}
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                log.error("Fichier JSON corrompu ! Renvoi d'un dictionnaire vide.")
                return {}
            except Exception as e:
                log.error(f"[DB ERROR] Erreur lors de la lecture : {e}")
                return {}

    async def save_data(self, data: dict):
        """Sauvegarde le JSON avec verrou pour éviter l'écrasement simultané."""
        async with self._lock:
            try:
                temp_path = self.filepath + ".tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                os.replace(temp_path, self.filepath)
            except Exception as e:
                log.error(f"[DB ERROR] Erreur lors de la sauvegarde : {e}")
