import os
import discord
from dotenv import load_dotenv
from discord import app_commands

from sous_fonctions.commande_rr import rr
from sous_fonctions.tracker import link, unlink, TrackerTask

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
        self.tracker_task = TrackerTask(self)
        await self.tree.sync()

    async def on_ready(self):
        print(f"[SUCCESS] Connecté en tant que {self.user}")




client = MyClient(intents=intents)

# ========== COMMANDES SLASH ==========
client.tree.add_command(rr)
client.tree.add_command(link)
client.tree.add_command(unlink)

# ========== LANCEMENT ==========
client.run(TOKEN)