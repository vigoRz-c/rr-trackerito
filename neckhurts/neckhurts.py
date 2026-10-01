import os
import sys

# Si l'application est compilée (PyInstaller), on se place dans le dossier de l'exécutable, sinon dans celui du script
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

import discord
from dotenv import load_dotenv
from discord import app_commands

# ========== CONFIGURATION & VARIABLES ==========
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

from cogs.commande_rr import rr
from cogs.tracker import link, unlink, TrackerTask, load_data, save_data
from cogs.classement import classement
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
client.tree.add_command(classement)

@app_commands.command(name="test_game", description="[Admin] Simule une fin de partie pour tester l'affichage")
async def test_game(interaction: discord.Interaction):
    await interaction.response.send_message("Simulation de fin de partie en cours...", ephemeral=True)
    # Triche: on change le last_match_id pour forcer la detection du dernier match joué
    tracker_data = load_data()
    for user_id in tracker_data:
        if user_id == "_meta": continue
        tracker_data[user_id]["last_match_id"] = "fake_id_for_test"
    save_data(tracker_data)
    await client.tracker_task.tracker_loop.coro(client.tracker_task)

@app_commands.command(name="test_recap", description="[Admin] Force l'affichage du recapitulatif de la veille")
async def test_recap(interaction: discord.Interaction):
    await interaction.response.send_message("Génération du récapitulatif en cours...", ephemeral=True)
    await client.tracker_task.execute_daily_recap()

client.tree.add_command(test_game)
client.tree.add_command(test_recap)

# ========== LANCEMENT ==========
client.run(TOKEN)