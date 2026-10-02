import discord
from discord import app_commands
import aiohttp
import os
import datetime
import json
from cogs.tracker import load_data

HENRIK_API_KEY = os.getenv("HENRIK_API_KEY")

async def autocomplete_nom(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    tracker_data = load_data()
    choices = []
    vus = set()
    for user_id, info in tracker_data.items():
        if user_id == "_meta":
            continue
        nom = info["nom"]
        if current.lower() in nom.lower() and nom not in vus:
            vus.add(nom)
            choices.append(app_commands.Choice(name=f"{nom}#{info['tag']}", value=nom))
    return choices[:25]

@app_commands.command(name="rr", description="Affiche le rang et le détail de la dernière game d'un joueur Valorant")
@app_commands.describe(nom="Ton pseudo Valorant", tag="Ton tag (sans le #)", region="Ta région (ex: eu, na, ap)")
@app_commands.autocomplete(nom=autocomplete_nom)
async def rr(interaction: discord.Interaction, nom: str, tag: str = None, region: str = "eu"):
    
    if tag is None:
        tracker_data = load_data()
        for user_id, info in tracker_data.items():
            if user_id == "_meta":
                continue
            if info["nom"].lower() == nom.lower():
                tag = info["tag"]
                break
        
        if tag is None:
            await interaction.response.send_message("❌ Tu dois fournir un tag si le joueur n'est pas encore enregistré !", ephemeral=True)
            return

    await interaction.response.defer()

    if not HENRIK_API_KEY:
        await interaction.followup.send("❌ Le bot n'a pas été configuré avec une clé API HenrikDev (`HENRIK_API_KEY`).")
        return

    headers = {
        "Authorization": HENRIK_API_KEY
    }
    
    url_mmr = f"https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{nom}/{tag}"
    url_match = f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{nom}/{tag}?size=1"

    async with aiohttp.ClientSession() as session:
        try:
            # 1. Recuperation du MMR
            async with session.get(url_mmr, headers=headers) as resp_mmr:
                if resp_mmr.status == 404:
                    await interaction.followup.send(f"❌ Joueur `{nom}#{tag}` introuvable sur la région `{region}`.")
                    return
                if resp_mmr.status != 200:
                    await interaction.followup.send(f"❌ Erreur API MMR ({resp_mmr.status}).")
                    return
                    
                data_mmr = await resp_mmr.json()
                if "data" not in data_mmr or data_mmr["data"] is None:
                    await interaction.followup.send("❌ Aucune donnée MMR trouvée pour ce joueur.")
                    return
                    
                stats = data_mmr["data"] or {}
                rang = stats.get("currenttierpatched", "Inconnu")
                rr_actuel = stats.get("ranking_in_tier", 0)
                changement_rr = stats.get("mmr_change_to_last_game", 0)
                
            # 2. Recuperation des details du dernier match
            agent = "Inconnu"
            kda = "0/0/0"
            map_name = "Inconnue"
            match_score = "0-0"
            agent_image_url = None
            
            async with session.get(url_match, headers=headers) as resp_match:
                if resp_match.status == 200:
                    data_match = await resp_match.json()
                    if data_match.get("data") and len(data_match["data"]) > 0:
                        match = data_match["data"][0]
                        metadata = match.get("metadata") or {}
                        map_name = metadata.get("map", "Inconnue")
                        
                        players_dict = match.get("players") or {}
                        all_players = players_dict.get("all_players", [])
                        player_team = None
                        for p in all_players:
                            if p.get("name", "").lower() == nom.lower() and p.get("tag", "").lower() == tag.lower():
                                agent = p.get("character", "Inconnu")
                                p_stats = p.get("stats") or {}
                                kills = p_stats.get('kills', 0)
                                deaths = p_stats.get('deaths', 0)
                                assists = p_stats.get('assists', 0)
                                kda = f"{kills}/{deaths}/{assists}"
                                player_team = p.get("team")
                                p_assets = p.get("assets") or {}
                                p_agent_assets = p_assets.get("agent") or {}
                                agent_image_url = p_agent_assets.get("small")
                                
                                headshots = p_stats.get("headshots", 0)
                                bodyshots = p_stats.get("bodyshots", 0)
                                legshots = p_stats.get("legshots", 0)
                                total_shots = headshots + bodyshots + legshots
                                hs_pct = round((headshots / total_shots) * 100, 1) if total_shots > 0 else 0.0
                                
                                kd = round(kills / deaths, 2) if deaths > 0 else kills
                                score_raw = p_stats.get("score", 0)
                                damage_made = p.get("damage_made", 0)
                                break
                        
                        nb_rounds = 0
                        if player_team:
                            teams = match.get("teams") or {}
                            my_team = teams.get(player_team.lower()) or {}
                            enemy_team_key = "blue" if player_team.lower() == "red" else "red"
                            enemy_team = teams.get(enemy_team_key) or {}
                            match_score = f"{my_team.get('rounds_won', 0)}-{enemy_team.get('rounds_won', 0)}"
                            nb_rounds = my_team.get('rounds_won', 0) + enemy_team.get('rounds_won', 0)
                            
                        # Le Performance Score sur l'échelle 0-500 correspond à la moyenne du score par round (l'ancien ACS)
                        perf = round(score_raw / nb_rounds) if nb_rounds > 0 else 0
                        adr = round(damage_made / nb_rounds) if nb_rounds > 0 else 0
                        
                        stats_dict = {
                            "hs_pct": hs_pct,
                            "kd": kd,
                            "adr": adr,
                            "perf": perf
                        }

            # 3. Construction de l'Embed et de l'Image
            is_win = (changement_rr > 0)
            result_text = "Victoire" if is_win else "Défaite" if changement_rr < 0 else "Égalité"
            color = discord.Color.green() if is_win else discord.Color.red() if changement_rr < 0 else discord.Color.orange()
            
            action_rr = "gagner" if is_win else "perdre" if changement_rr < 0 else "gagner"
            phrase_desc = f"{nom} vient de {action_rr} {abs(changement_rr)} RR ({rang} {rr_actuel} RR)"

            from utils.image_generator import generate_match_image
            buffer = await generate_match_image(map_name, agent, kda, changement_rr, match_score, stats_dict)
            file = discord.File(fp=buffer, filename="recap.png")

            embed = discord.Embed(
                title=f"{result_text} ({match_score})",
                description=phrase_desc,
                color=color
            )
            embed.set_author(name=f"Statistiques de {nom}#{tag}", icon_url="https://media.valorant-api.com/gamemodes/96bd3920-4f36-d026-2b28-c683eb0bcac5/displayicon.png")
            embed.set_image(url="attachment://recap.png")
            embed.timestamp = datetime.datetime.now()
            
            print("=== COMMANDE RR ENVOYÉE SUR DISCORD ===")
            print(json.dumps(embed.to_dict(), indent=4, ensure_ascii=False))
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Une erreur inattendue est survenue: {e}")
