import aiohttp
import asyncio
from core.config import HENRIK_API_KEY
from core.logger import log

BASE_URL = "https://api.henrikdev.xyz/valorant"
HEADERS = {"Authorization": HENRIK_API_KEY} if HENRIK_API_KEY else {}
TIMEOUT = aiohttp.ClientTimeout(total=15)

async def _fetch(url: str) -> dict:
    """Fonction utilitaire privée pour faire les requêtes aiohttp et gérer les erreurs."""
    if not HENRIK_API_KEY:
        log.error("Clé API Henrik manquante dans le .env.")
        return None
        
    try:
        async with aiohttp.ClientSession(headers=HEADERS, timeout=TIMEOUT) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    log.warning(f"[API Henrik] Rate limit atteint (429) sur {url}.")
                elif response.status == 404:
                    log.warning(f"[API Henrik] Joueur/Donnée introuvable (404) sur {url}.")
                elif response.status >= 500:
                    log.warning(f"[API Henrik] Erreur serveur distante ({response.status}) sur {url}.")
                else:
                    log.error(f"[API Henrik] Erreur HTTP {response.status} sur {url}.")
                return None
    except asyncio.TimeoutError:
        log.error(f"[API Henrik] Timeout (15s dépassées) sur {url}.")
        return None
    except aiohttp.ClientError as e:
        log.error(f"[API Henrik] Erreur réseau lors de l'appel à {url}: {e}")
        return None
    except Exception as e:
        log.error(f"[API Henrik] Exception critique inattendue : {e}")
        return None

async def get_player_mmr(nom: str, tag: str, region: str = "eu") -> dict:
    """Retourne les infos MMR actuelles d'un joueur."""
    url = f"{BASE_URL}/v1/mmr/{region}/{nom}/{tag}"
    data = await _fetch(url)
    return data.get("data", {}) if data else None

async def get_latest_match(nom: str, tag: str, region: str = "eu") -> list:
    """Retourne le dernier match d'un joueur (utile pour checker le last_match_id)."""
    url = f"{BASE_URL}/v3/matches/{region}/{nom}/{tag}?size=1"
    data = await _fetch(url)
    return data.get("data", []) if data else None

async def get_mmr_history(nom: str, tag: str, region: str = "eu") -> list:
    """Retourne l'historique récent des gains/pertes de MMR d'un joueur."""
    url = f"{BASE_URL}/v1/mmr-history/{region}/{nom}/{tag}"
    data = await _fetch(url)
    return data.get("data", []) if data else None
