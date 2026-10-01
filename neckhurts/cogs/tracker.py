import discord
from discord import app_commands
from discord.ext import tasks
import aiohttp
import os
import json
import datetime

os.makedirs("data", exist_ok=True)
DATA_FILE = "data/tracker_data.json"
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
        self.daily_recap.start()

    def cog_unload(self):
        self.tracker_loop.cancel()
        self.daily_recap.cancel()

    @tasks.loop(minutes=2.0)
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
                                
                                # Fetch du dernier match pour récupérer Score, Agent et Map
                                match_url = f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{nom}/{tag}?size=1"
                                agent = "Inconnu"
                                kda = "0/0/0"
                                map_name = "Inconnue"
                                match_score = "0-0"
                                agent_image_url = None
                                is_win = (diff > 0)
                                result_text = "Victoire" if is_win else "Défaite" if diff < 0 else "Égalité"
                                color = discord.Color.green() if is_win else discord.Color.red() if diff < 0 else discord.Color.dark_gray()
                                
                                try:
                                    async with session.get(match_url, headers=headers) as match_resp:
                                        if match_resp.status == 200:
                                            match_data = await match_resp.json()
                                            if match_data.get("data") and len(match_data["data"]) > 0:
                                                match = match_data["data"][0]
                                                metadata = match.get("metadata") or {}
                                                map_name = metadata.get("map", "Inconnue")
                                                
                                                players_dict = match.get("players") or {}
                                                all_players = players_dict.get("all_players", [])
                                                player_team = None
                                                for p in all_players:
                                                    if p.get("name", "").lower() == nom.lower() and p.get("tag", "").lower() == tag.lower():
                                                        agent = p.get("character", "Inconnu")
                                                        stats = p.get("stats") or {}
                                                        kda = f"{stats.get('kills', 0)}/{stats.get('deaths', 0)}/{stats.get('assists', 0)}"
                                                        player_team = p.get("team")
                                                        p_assets = p.get("assets") or {}
                                                        p_agent_assets = p_assets.get("agent") or {}
                                                        agent_image_url = p_agent_assets.get("small")
                                                        break
                                                
                                                if player_team:
                                                    teams = match.get("teams") or {}
                                                    my_team = teams.get(player_team.lower()) or {}
                                                    enemy_team_key = "blue" if player_team.lower() == "red" else "red"
                                                    enemy_team = teams.get(enemy_team_key) or {}
                                                    my_rounds = my_team.get("rounds_won", 0)
                                                    enemy_rounds = enemy_team.get("rounds_won", 0)
                                                    match_score = f"{my_rounds}-{enemy_rounds}"
                                except Exception as e:
                                    print(f"Erreur lors de la récupération du match pour {nom}#{tag}: {e}")

                                action_rr = "gagner" if diff > 0 else "perdre" if diff < 0 else "gagner"
                                phrase_desc = f"{nom} vient de {action_rr} {abs(mmr_change)} RR ({rang} {rr_actuel} RR)"
                                
                                embed = discord.Embed(
                                    title=f"{result_text} ({match_score})",
                                    description=phrase_desc,
                                    color=color
                                )
                                embed.set_author(name="Résultat de la partie", icon_url="https://media.valorant-api.com/gamemodes/96bd3920-4f36-d026-2b28-c683eb0bcac5/displayicon.png")
                                
                                embed.add_field(name="Score", value=kda, inline=True)
                                embed.add_field(name="Agent", value=agent, inline=True)
                                embed.add_field(name="Map", value=map_name, inline=True)
                                
                                if agent_image_url:
                                    embed.set_thumbnail(url=agent_image_url)
                                
                                embed.timestamp = datetime.datetime.now()
                                
                                if channel:
                                    await channel.send(embed=embed)
                                else:
                                    # Si pas de salon defini, on essaie d'envoyer en MP
                                    user = self.client.get_user(int(discord_id))
                                    if user:
                                        try:
                                            await user.send(embed=embed)
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

    @tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=2))))
    async def daily_recap(self):
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
        
        if not channel:
            return
            
        headers = {"Authorization": HENRIK_API_KEY}
        
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))
        yesterday = now - datetime.timedelta(days=1)
        start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        start_ts = int(start_of_yesterday.timestamp())
        end_ts = int(end_of_yesterday.timestamp())
        
        embed = discord.Embed(title="", color=discord.Color.magenta())
        embed.set_author(name="Récapitulatif de la veille", icon_url="https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/24/largeicon.png")
        
        has_data = False
        
        async with aiohttp.ClientSession() as session:
            for discord_id, info in tracker_data.items():
                nom = info["nom"]
                tag = info["tag"]
                region = info["region"]
                
                url = f"https://api.henrikdev.xyz/valorant/v1/mmr-history/{region}/{nom}/{tag}"
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data_api = (await response.json()).get("data", [])
                            
                            yesterday_matches = [m for m in data_api if start_ts <= m.get("date_raw", 0) <= end_ts]
                            if not yesterday_matches:
                                continue
                                
                            yesterday_matches.sort(key=lambda x: x.get("date_raw", 0))
                            
                            wins = 0
                            losses = 0
                            draws = 0
                            total_rr = 0
                            
                            for m in yesterday_matches:
                                rr_change = m.get("mmr_change_to_last_game", 0)
                                total_rr += rr_change
                                if rr_change > 0:
                                    wins += 1
                                elif rr_change < 0:
                                    losses += 1
                                else:
                                    draws += 1
                                    
                            total_games = wins + losses + draws
                            winrate = round((wins / total_games) * 100, 1) if total_games > 0 else 0
                            
                            end_match = yesterday_matches[-1]
                            end_tier = end_match.get("currenttierpatched", "Inconnu")
                            end_rr = end_match.get("ranking_in_tier", 0)
                            end_str = f"{end_tier} {end_rr}rr"
                            
                            oldest_match_index = data_api.index(yesterday_matches[0])
                            if oldest_match_index + 1 < len(data_api):
                                before_match = data_api[oldest_match_index + 1]
                                start_tier = before_match.get("currenttierpatched", "Inconnu")
                                start_rr = before_match.get("ranking_in_tier", 0)
                            else:
                                start_tier = yesterday_matches[0].get("currenttierpatched", "Inconnu")
                                start_rr = yesterday_matches[0].get("ranking_in_tier", 0) - yesterday_matches[0].get("mmr_change_to_last_game", 0)
                                if start_rr < 0 or start_rr >= 100:
                                    start_tier = "Inconnu"
                                    start_rr = "?"
                            
                            start_str = f"{start_tier} {start_rr}rr" if start_tier != "Inconnu" else "Inconnu"
                            
                            title = f"{nom} : {'+' if total_rr > 0 else ''}{total_rr}"
                            stats_str = f"{wins}W {losses}L" + (f" {draws}D" if draws > 0 else "") + f" ({winrate}%)"
                            desc = f"{stats_str} | {start_str} -> {end_str}"
                            
                            embed.add_field(name=title, value=desc, inline=False)
                            has_data = True
                except Exception as e:
                    print(f"Erreur Recap pour {nom}#{tag} : {e}")
                    
        if has_data:
            embed.timestamp = datetime.datetime.now()
            await channel.send(embed=embed)
            
    @daily_recap.before_loop
    async def before_daily_recap(self):
        await self.client.wait_until_ready()
