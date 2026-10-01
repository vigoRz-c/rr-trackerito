import discord
from discord import app_commands
import aiohttp
import os
from cogs.tracker import load_data

HENRIK_API_KEY = os.getenv("HENRIK_API_KEY")

# Poids ELO par tier pour le tri (identique à l'API : elo absolu)
# On utilise directement le champ "elo" de l'API HenrikDev.

MEDAL = {1: "🥇", 2: "🥈", 3: "🥉"}

VALORANT_ICON = "https://media.valorant-api.com/gamemodes/96bd3920-4f36-d026-2b28-c683eb0bcac5/displayicon.png"


@app_commands.command(name="classement", description="Affiche le classement ELO de tous les membres enregistrés.")
async def classement(interaction: discord.Interaction):
    await interaction.response.defer()

    if not HENRIK_API_KEY:
        await interaction.followup.send("❌ L'API Henrik n'est pas configurée.")
        return

    tracker_data = load_data()
    joueurs = {k: v for k, v in tracker_data.items() if k != "_meta"}

    if not joueurs:
        await interaction.followup.send("❌ Aucun membre enregistré. Utilise `/link` pour t'enregistrer.")
        return

    headers = {"Authorization": HENRIK_API_KEY}
    resultats = []

    async with aiohttp.ClientSession() as session:
        for discord_id, info in joueurs.items():
            nom = info["nom"]
            tag = info["tag"]
            region = info.get("region", "eu")
            url = f"https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{nom}/{tag}"
            try:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = (await resp.json()).get("data") or {}
                        elo = data.get("elo", 0)
                        rang = data.get("currenttierpatched", "Non classé")
                        rr = data.get("ranking_in_tier", 0)
                        resultats.append({
                            "nom": nom,
                            "tag": tag,
                            "elo": elo,
                            "rang": rang,
                            "rr": rr,
                        })
                    else:
                        # Si l'API échoue on affiche quand même le joueur sans données live
                        resultats.append({
                            "nom": nom,
                            "tag": tag,
                            "elo": 0,
                            "rang": "Indisponible",
                            "rr": 0,
                        })
            except Exception as e:
                print(f"Erreur classement pour {nom}#{tag}: {e}")
                resultats.append({
                    "nom": nom,
                    "tag": tag,
                    "elo": 0,
                    "rang": "Erreur",
                    "rr": 0,
                })

    # Tri décroissant par ELO
    resultats.sort(key=lambda x: x["elo"], reverse=True)

    embed = discord.Embed(
        title="Classement des membres",
        color=discord.Color.from_rgb(255, 180, 0)
    )
    embed.set_author(name="RR Trackerito", icon_url=VALORANT_ICON)

    lines = []
    for i, joueur in enumerate(resultats, 1):
        medal = MEDAL.get(i, f"**#{i}**")
        nom_display = f"{joueur['nom']}#{joueur['tag']}"
        rang_display = joueur["rang"]
        rr_display = f"{joueur['rr']} RR" if joueur["elo"] > 0 else "—"
        lines.append(f"{medal}  **{nom_display}**\n└ {rang_display}  •  {rr_display}")

    embed.description = "\n\n".join(lines) if lines else "Aucune donnée disponible."
    embed.set_footer(text=f"{len(resultats)} membre(s)  •  Données via HenrikDev")

    import datetime
    embed.timestamp = datetime.datetime.now()

    await interaction.followup.send(embed=embed)
