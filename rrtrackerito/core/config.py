import os
from dotenv import load_dotenv

# Chargement explicite du .env
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
HENRIK_API_KEY = os.getenv("HENRIK_API_KEY")
TRACKER_CHANNEL_ID = os.getenv("TRACKER_CHANNEL_ID")

if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN introuvable dans le .env")
