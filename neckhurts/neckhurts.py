import os
import discord
from dotenv import load_dotenv
from discord import app_commands

from sous_fonctions.commande_gay import gay
from sous_fonctions.commande_infos import infos
from sous_fonctions.commande_mimic import mimic
from sous_fonctions.auto_reponse import on_message, repondre, ORTHOGRAPHE_NEZ

# ========== CONFIGURATION & VARIABLES ==========
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ Le token Discord n'a pas été trouvé dans la variable d'environnement DISCORD_TOKEN")


# ========== BOT DISCORD ==========
intents = discord.Intents.default()
intents.message_content = True

class MyClient(discord.Client):
    def __init__(self, *, intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Connecté en tant que {self.user}")

    # Import des méthodes auto-réponse
    on_message = on_message
    repondre = repondre


client = MyClient(intents=intents)

# ========== COMMANDES SLASH ==========
client.tree.add_command(infos)
client.tree.add_command(gay)
client.tree.add_command(mimic)

# ========== LANCEMENT ==========
client.run(TOKEN)