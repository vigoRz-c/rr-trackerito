import discord
from discord import app_commands
from discord.ext import tasks
import aiohttp
import os
import json

DATA_FILE = "tracker_data.json"
HENRIK_API_KEY = os.getenv("HENRIK_API_KEY")

# Charger les donnees ou creer un dico vide
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

@app_commands.command(name="link", description="Associe ton compte Discord a un compte Valorant pour le tracker.")
@app_commands.describe(nom="Ton pseudo Valorant", tag="Ton tag (sans le #)", region="Ta region (eu, na...)")
async def link(interaction: discord.Interaction, nom: str, tag: str, region: str = "eu"):
    await interaction.response.defer()

    if not HENRIK_API_KEY:
        await interaction.followup.send("❌ L'API Henrik n'est pas configuree.")
        return

    headers = {"Authorization": HENRIK_API_KEY}
    url = f"https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{nom}/{tag}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                resp_json = await response.json()
                data_api = resp_json.get("data")
                if not data_api:
                    await interaction.followup.send("❌ Pas de donnees MMR trouvees (joue tes parties de placement).")
                    return
                
                elo = data_api.get("elo", 0)
                
                # Sauvegarder dans le json
                tracker_data = load_data()
                discord_id = str(interaction.user.id)
                
                tracker_data[discord_id] = {
                    "nom": nom,
                    "tag": tag,
                    "region": region,
                    "last_elo": elo
                }
                
                save_data(tracker_data)
                
                await interaction.followup.send(f"✅ Compte {nom}#{tag} lié avec succès ! Le bot t'annoncera tes futurs gains/pertes de RR.")
                
            elif response.status == 404:
                await interaction.followup.send("❌ Compte introuvable.")
            else:
                await interaction.followup.send(f"❌ Erreur API ({response.status}).")

@app_commands.command(name="unlink", description="Supprime l'association entre ton compte Discord et Valorant.")
async def unlink(interaction: discord.Interaction):
    tracker_data = load_data()
    discord_id = str(interaction.user.id)
    if discord_id in tracker_data:
        del tracker_data[discord_id]
        save_data(tracker_data)
        await interaction.response.send_message("✅ Ton compte Valorant n'est plus suivi.")
    else:
        await interaction.response.send_message("❌ Tu n'avais aucun compte enregistré.")

# La tâche d'arrière plan (tracker)
class TrackerTask:
    def __init__(self, client):
        self.client = client
        self.channel_id = os.getenv("TRACKER_CHANNEL_ID")
        self.tracker_loop.start()

    def cog_unload(self):
        self.tracker_loop.cancel()

    @tasks.loop(minutes=10.0)
    async def tracker_loop(self):
        if not HENRIK_API_KEY:
            return
            
        tracker_data = load_data()
        if not tracker_data:
            return
            
        channel = None
        if self.channel_id:
            try:
                channel = self.client.get_channel(int(self.channel_id))
            except:
                pass

        headers = {"Authorization": HENRIK_API_KEY}
        
        async with aiohttp.ClientSession() as session:
            for discord_id, info in tracker_data.items():
                nom = info["nom"]
                tag = info["tag"]
                region = info["region"]
                last_elo = info["last_elo"]
                
                url = f"https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{nom}/{tag}"
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data_api = (await response.json()).get("data", {})
                            current_elo = data_api.get("elo", 0)
                            
                            # Si le ELO a change, une partie a ete jouee
                            if current_elo != last_elo and current_elo != 0 and last_elo != 0:
                                diff = current_elo - last_elo
                                mmr_change = data_api.get("mmr_change_to_last_game", diff)
                                rang = data_api.get("currenttierpatched", "Inconnu")
                                rr_actuel = data_api.get("ranking_in_tier", 0)
                                
                                symbole = "📈" if diff > 0 else "📉" if diff < 0 else "➖"
                                message = f"<@{discord_id}> ({nom}#{tag}) vient de terminer une partie !\n"
                                message += f"> **Changement** : {symbole} {mmr_change} RR\n"
                                message += f"> **Rang actuel** : {rang} ({rr_actuel} RR)\n"
                                
                                if channel:
                                    await channel.send(message)
                                else:
                                    # Si pas de salon defini, on essaie d'envoyer en MP
                                    user = self.client.get_user(int(discord_id))
                                    if user:
                                        try:
                                            await user.send(message)
                                        except:
                                            pass
                                
                                # Mettre a jour le last_elo
                                tracker_data[discord_id]["last_elo"] = current_elo
                                save_data(tracker_data)
                                
                except Exception as e:
                    print(f"Erreur Tracker pour {nom}#{tag} : {e}")
                    
    @tracker_loop.before_loop
    async def before_tracker_loop(self):
        await self.client.wait_until_ready()
