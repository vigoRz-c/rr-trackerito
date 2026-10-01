import discord
from discord import app_commands
import aiohttp
import os

HENRIK_API_KEY = os.getenv("HENRIK_API_KEY")

@app_commands.command(name="rr", description="Affiche le rang et les RR d'un joueur Valorant")
@app_commands.describe(nom="Ton pseudo Valorant", tag="Ton tag (sans le #)", region="Ta région (ex: eu, na, ap)")
async def rr(interaction: discord.Interaction, nom: str, tag: str, region: str = "eu"):
    await interaction.response.defer()

    if not HENRIK_API_KEY:
        await interaction.followup.send("❌ Le bot n'a pas été configuré avec une clé API HenrikDev (`HENRIK_API_KEY`).")
        return

    headers = {
        "Authorization": HENRIK_API_KEY
    }
    
    url = f"https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{nom}/{tag}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if "data" not in data or data["data"] is None:
                    await interaction.followup.send("❌ Aucune donnée MMR trouvée pour ce joueur (peut-être qu'il n'a pas fait ses parties de placement).")
                    return
                
                stats = data["data"]
                
                rang = stats.get("currenttierpatched", "Inconnu")
                rr_actuel = stats.get("ranking_in_tier", 0)
                changement_rr = stats.get("mmr_change_to_last_game", 0)
                
                embed = discord.Embed(
                    title=f"Statistiques de {nom}#{tag}",
                    color=discord.Color.red()
                )
                embed.add_field(name="Rang", value=rang, inline=True)
                embed.add_field(name="RR Actuel", value=f"{rr_actuel} RR", inline=True)
                
                symbole = "📈" if changement_rr > 0 else "📉" if changement_rr < 0 else "➖"
                embed.add_field(name="Dernière game", value=f"{symbole} {changement_rr} RR", inline=False)
                
                await interaction.followup.send(embed=embed)
            
            elif response.status == 404:
                await interaction.followup.send(f"❌ Joueur `{nom}#{tag}` introuvable sur la région `{region}`.")
            elif response.status == 429:
                await interaction.followup.send("❌ L'API est surchargée (Rate Limit). Attends un peu.")
            else:
                await interaction.followup.send(f"❌ Erreur API ({response.status}). Vérifie ta clé API ou réessaie plus tard.")
