import discord
from discord import app_commands
from discord.ext import tasks
import aiohttp
import os
import json
import datetime
from utils.image_generator import generate_match_image

os.makedirs("data", exist_ok=True)
DATA_FILE = "data/tracker_data.json"
HENRIK_API_KEY = os.getenv("HENRIK_API_KEY")

# ─── Rang → image bannière (HenrikDev asset) ──────────────────────────────────
RANK_BANNER_URLS = {
    "Iron 1":     "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/3/largeicon.png",
    "Iron 2":     "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/4/largeicon.png",
    "Iron 3":     "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/5/largeicon.png",
    "Bronze 1":   "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/6/largeicon.png",
    "Bronze 2":   "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/7/largeicon.png",
    "Bronze 3":   "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/8/largeicon.png",
    "Silver 1":   "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/9/largeicon.png",
    "Silver 2":   "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/10/largeicon.png",
    "Silver 3":   "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/11/largeicon.png",
    "Gold 1":     "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/12/largeicon.png",
    "Gold 2":     "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/13/largeicon.png",
    "Gold 3":     "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/14/largeicon.png",
    "Platinum 1": "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/15/largeicon.png",
    "Platinum 2": "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/16/largeicon.png",
    "Platinum 3": "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/17/largeicon.png",
    "Diamond 1":  "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/18/largeicon.png",
    "Diamond 2":  "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/19/largeicon.png",
    "Diamond 3":  "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/20/largeicon.png",
    "Ascendant 1":"https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/21/largeicon.png",
    "Ascendant 2":"https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/22/largeicon.png",
    "Ascendant 3":"https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/23/largeicon.png",
    "Immortal 1": "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/24/largeicon.png",
    "Immortal 2": "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/25/largeicon.png",
    "Immortal 3": "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/26/largeicon.png",
    "Radiant":    "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/27/largeicon.png",
}

VALORANT_ICON = "https://media.valorant-api.com/gamemodes/96bd3920-4f36-d026-2b28-c683eb0bcac5/displayicon.png"

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


# ─── Extraction des stats depuis un match player ─────────────────────────────
def extract_player_stats(all_players, nom, tag):
    """Retourne un dict de stats enrichies pour le joueur trouvé."""
    for p in all_players:
        if p.get("name", "").lower() == nom.lower() and p.get("tag", "").lower() == tag.lower():
            stats = p.get("stats") or {}
            p_assets = p.get("assets") or {}
            p_agent_assets = p_assets.get("agent") or {}

            kills = stats.get("kills", 0)
            deaths = stats.get("deaths", 0)
            assists = stats.get("assists", 0)
            score = stats.get("score", 0)

            headshots = stats.get("headshots", 0)
            bodyshots = stats.get("bodyshots", 0)
            legshots = stats.get("legshots", 0)
            total_shots = headshots + bodyshots + legshots
            hs_pct = round((headshots / total_shots) * 100, 1) if total_shots > 0 else 0.0

            damage_made = p.get("damage_made", 0)
            
            return {
                "agent": p.get("character", "Inconnu"),
                "kda": f"{kills}/{deaths}/{assists}",
                "score_raw": score,
                "hs_pct": hs_pct,
                "team": p.get("team"),
                "agent_image": p_agent_assets.get("small"),
                "kills": kills,
                "deaths": deaths,
                "assists": assists,
                "damage_made": damage_made,
            }
    return None


def compute_acs(score_raw, total_rounds):
    """Calcule l'ACS (Average Combat Score) à partir du score brut et du nombre de rounds."""
    if total_rounds > 0:
        return round(score_raw / total_rounds)
    return 0


def rank_emoji(rang: str) -> str:
    rang_lower = rang.lower() if rang else ""
    if "iron" in rang_lower:       return "🪨"
    if "bronze" in rang_lower:     return "🥉"
    if "silver" in rang_lower:     return "🥈"
    if "gold" in rang_lower:       return "🥇"
    if "platinum" in rang_lower:   return "💠"
    if "diamond" in rang_lower:    return "💎"
    if "ascendant" in rang_lower:  return "🌿"
    if "immortal" in rang_lower:   return "🔴"
    if "radiant" in rang_lower:    return "✨"
    return "🎮"


# ─── Vue "5 dernières games" ─────────────────────────────────────────────────
class DernieresGamesView(discord.ui.View):
    def __init__(self, nom: str, tag: str, region: str):
        super().__init__(timeout=120)
        self.nom = nom
        self.tag = tag
        self.region = region

    @discord.ui.button(label="🕹️ 5 dernières games", style=discord.ButtonStyle.secondary)
    async def show_last_games(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        button.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        headers = {"Authorization": HENRIK_API_KEY}
        url = f"https://api.henrikdev.xyz/valorant/v3/matches/{self.region}/{self.nom}/{self.tag}?size=5"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ Impossible de récupérer l'historique.", ephemeral=True)
                        return
                    data = await resp.json()
                    matches = data.get("data") or []

            if not matches:
                await interaction.followup.send("❌ Aucune partie trouvée.", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🕹️ 5 dernières parties de {self.nom}#{self.tag}",
                color=discord.Color.from_rgb(255, 70, 85)
            )

            for i, match in enumerate(matches, 1):
                meta = match.get("metadata") or {}
                map_name = meta.get("map", "?")
                total_rounds = meta.get("rounds_played") or 0

                players_dict = match.get("players") or {}
                all_players = players_dict.get("all_players", [])

                ps = extract_player_stats(all_players, self.nom, self.tag)
                if not ps:
                    continue

                acs = compute_acs(ps["score_raw"], total_rounds)

                teams = match.get("teams") or {}
                player_team = ps.get("team", "")
                my_team = teams.get(player_team.lower()) or {}
                enemy_key = "blue" if player_team.lower() == "red" else "red"
                enemy_team = teams.get(enemy_key) or {}
                my_r = my_team.get("rounds_won", 0)
                en_r = enemy_team.get("rounds_won", 0)
                score_str = f"{my_r}-{en_r}"

                won = my_team.get("has_won", False)
                result_label = "Victoire" if won else "Défaite"

                embed.add_field(
                    name=f"{result_label} {i} — {map_name}",
                    value=(
                        f"**Agent:** {ps['agent']}  |  **KDA:** {ps['kda']}  |  "
                        f"**ACS:** {acs}  |  **HS%:** {ps['hs_pct']}%  |  **Score:** {score_str}"
                    ),
                    inline=False
                )

            embed.set_footer(text="RR Trackerito  •  Données via HenrikDev")
            embed.timestamp = datetime.datetime.now()
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : {e}", ephemeral=True)


# ─── Barre de progression RR ─────────────────────────────────────────────────
def rr_progress_bar(rr: int, total: int = 100, length: int = 12) -> str:
    """Génère une barre de progression ASCII pour les RR."""
    rr = max(0, min(rr, total))
    filled = round((rr / total) * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"`{bar}` {rr}/{total}"


# ─── Construction de l'embed premium après une partie ─────────────────────────
def build_match_embed(nom, tag, rang, mmr_change, match_score):
    # On utilise mmr_change (changement RR de la dernière game) et non diff
    is_win = mmr_change > 1
    is_draw = mmr_change == 0   
    result_text = "VICTOIRE" if is_win else "DÉFAITE" if not is_draw else "ÉGALITÉ"
    color = discord.Color.from_rgb(0, 200, 120) if is_win else discord.Color.from_rgb(255, 60, 80) if not is_draw else discord.Color.from_rgb(120, 120, 120)

    embed = discord.Embed(
        title=f"{result_text}  ·  {match_score}",
        description=f"▸  **{nom}** vient de terminer une ranked",
        color=color
    )
    embed.set_author(
        name=f"{nom}#{tag}  —  {rang}",
        icon_url=VALORANT_ICON
    )

    embed.set_image(url="attachment://recap.png")
    embed.set_footer(text="RR Trackerito  ·  Données via HenrikDev")
    embed.timestamp = datetime.datetime.now()
    return embed



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

# ─── Tâche d'arrière-plan (tracker) ──────────────────────────────────────────
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
            new_matches_by_id = {}
            
            for discord_id, info in tracker_data.items():
                if discord_id == "_meta":
                    continue
                nom = info["nom"]
                tag = info["tag"]
                region = info["region"]
                last_match_id = info.get("last_match_id")
                last_elo = info.get("last_elo", 0)

                match_url = f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{nom}/{tag}?size=1"
                try:
                    async with session.get(match_url, headers=headers) as match_resp:
                        if match_resp.status == 200:
                            match_data = await match_resp.json()
                            if match_data.get("data") and len(match_data["data"]) > 0:
                                match = match_data["data"][0]
                                metadata = match.get("metadata") or {}
                                match_id = metadata.get("matchid")
                                
                                if match_id:
                                    if last_match_id is None:
                                        tracker_data[discord_id]["last_match_id"] = match_id
                                        save_data(tracker_data)
                                    elif match_id != last_match_id:
                                        mode = metadata.get("mode", "").lower()
                                        queue = metadata.get("queue", "").lower()
                                        if mode == "competitive" or queue == "competitive":
                                            mmr_url = f"https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{nom}/{tag}"
                                            mmr_change = 0
                                            rang = "Inconnu"
                                            current_elo = last_elo
                                            
                                            async with session.get(mmr_url, headers=headers) as mmr_resp:
                                                if mmr_resp.status == 200:
                                                    data_api = (await mmr_resp.json()).get("data", {})
                                                    mmr_change = data_api.get("mmr_change_to_last_game", 0)
                                                    rang = data_api.get("currenttierpatched", "Inconnu")
                                                    current_elo = data_api.get("elo", last_elo)
                                            
                                            if match_id not in new_matches_by_id:
                                                new_matches_by_id[match_id] = {
                                                    "match": match,
                                                    "players": []
                                                }
                                                
                                            new_matches_by_id[match_id]["players"].append({
                                                "discord_id": discord_id,
                                                "nom": nom,
                                                "tag": tag,
                                                "region": region,
                                                "mmr_change": mmr_change,
                                                "rang": rang,
                                                "current_elo": current_elo
                                            })
                                        else:
                                            tracker_data[discord_id]["last_match_id"] = match_id
                                            save_data(tracker_data)
                except Exception as e:
                    print(f"Erreur vérification match pour {nom}#{tag} : {e}")

            for match_id, match_info in new_matches_by_id.items():
                match = match_info["match"]
                involved_players = match_info["players"]
                
                metadata = match.get("metadata") or {}
                map_name = metadata.get("map", "Inconnue")
                
                players_dict = match.get("players") or {}
                all_players = players_dict.get("all_players", [])
                
                if len(involved_players) == 1:
                    player_data = involved_players[0]
                    nom, tag, discord_id = player_data["nom"], player_data["tag"], player_data["discord_id"]
                    region = player_data["region"]
                    
                    ps = extract_player_stats(all_players, nom, tag)
                    if ps:
                        agent = ps["agent"]
                        kda = ps["kda"]
                        player_team = ps.get("team")
                        
                        match_score = "0-0"
                        if player_team:
                            teams = match.get("teams") or {}
                            my_team = teams.get(player_team.lower()) or {}
                            enemy_key = "blue" if player_team.lower() == "red" else "red"
                            enemy_team = teams.get(enemy_key) or {}
                            match_score = f"{my_team.get('rounds_won', 0)}-{enemy_team.get('rounds_won', 0)}"
                        
                        kills = ps.get("kills", 0)
                        deaths = ps.get("deaths", 0)
                        kd = round(kills / deaths, 2) if deaths > 0 else kills
                        nb_rounds = sum(map(int, match_score.split('-'))) if '-' in match_score else 0
                        
                        # Le Performance Score sur l'échelle 0-500 correspond à la moyenne du score par round (l'ancien ACS)
                        perf = round(ps.get("score_raw", 0) / nb_rounds) if nb_rounds > 0 else 0
                        adr = round(ps.get("damage_made", 0) / nb_rounds) if nb_rounds > 0 else 0
                        
                        stats_dict = {
                            "hs_pct": ps.get("hs_pct", 0),
                            "kd": kd,
                            "adr": adr,
                            "perf": perf
                        }
                        
                        buffer = await generate_match_image(map_name, agent, kda, player_data["mmr_change"], match_score, stats_dict)
                        file = discord.File(fp=buffer, filename="recap.png")
                        
                        embed = build_match_embed(
                            nom=nom, tag=tag, rang=player_data["rang"],
                            mmr_change=player_data["mmr_change"], match_score=match_score
                        )
                        view = DernieresGamesView(nom=nom, tag=tag, region=region)
                        
                        if channel:
                            await channel.send(embed=embed, file=file, view=view)
                        else:
                            user = self.client.get_user(int(discord_id))
                            if user:
                                try: await user.send(embed=embed, file=file, view=view)
                                except: pass
                                
                    tracker_data[discord_id]["last_match_id"] = match_id
                    tracker_data[discord_id]["last_elo"] = player_data["current_elo"]
                    save_data(tracker_data)
                    
                else:
                    p1_stats = extract_player_stats(all_players, involved_players[0]["nom"], involved_players[0]["tag"])
                    match_score = "0-0"
                    if p1_stats and p1_stats.get("team"):
                        player_team = p1_stats.get("team")
                        teams = match.get("teams") or {}
                        my_team = teams.get(player_team.lower()) or {}
                        enemy_key = "blue" if player_team.lower() == "red" else "red"
                        enemy_team = teams.get(enemy_key) or {}
                        match_score = f"{my_team.get('rounds_won', 0)}-{enemy_team.get('rounds_won', 0)}"
                    
                    mmr_change_p1 = involved_players[0]["mmr_change"]
                    is_win = mmr_change_p1 > 0
                    is_draw = mmr_change_p1 == 0
                    result_text = "VICTOIRE" if is_win else "DÉFAITE" if not is_draw else "ÉGALITÉ"
                    color = discord.Color.from_rgb(0, 200, 120) if is_win else discord.Color.from_rgb(255, 60, 80) if not is_draw else discord.Color.from_rgb(120, 120, 120)
                    
                    embed = discord.Embed(
                        title=f"{result_text} de groupe  ·  {match_score}",
                        description=f"Une partie groupée ({len(involved_players)} joueurs) vient de se terminer sur **{map_name}**.",
                        color=color
                    )
                    
                    for p_data in involved_players:
                        nom, tag = p_data["nom"], p_data["tag"]
                        ps = extract_player_stats(all_players, nom, tag)
                        if ps:
                            agent = ps["agent"]
                            kda = ps["kda"]
                            sign = "+" if p_data["mmr_change"] > 0 else ""
                            rr_str = f"{sign}{p_data['mmr_change']} RR"
                            embed.add_field(
                                name=f"{nom}#{tag}  —  {p_data['rang']}",
                                value=f"**Agent**: {agent}  |  **KDA**: {kda}  |  **{rr_str}**",
                                inline=False
                            )
                        
                        tracker_data[p_data["discord_id"]]["last_match_id"] = match_id
                        tracker_data[p_data["discord_id"]]["last_elo"] = p_data["current_elo"]
                        
                    save_data(tracker_data)
                    
                    if channel:
                        await channel.send(embed=embed)
                    else:
                        for p_data in involved_players:
                            user = self.client.get_user(int(p_data["discord_id"]))
                            if user:
                                try: await user.send(embed=embed)
                                except: pass

        # Rattrapage du Daily Recap si on a dépassé 9h et qu'il n'a pas été envoyé aujourd'hui
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))
        if now.hour >= 9:
            today_str = now.strftime("%Y-%m-%d")
            meta = tracker_data.get("_meta", {})
            if meta.get("last_daily_recap") != today_str:
                await self.execute_daily_recap()
                meta["last_daily_recap"] = today_str
                tracker_data["_meta"] = meta
                save_data(tracker_data)

    @tracker_loop.before_loop
    async def before_tracker_loop(self):
        await self.client.wait_until_ready()

    @tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=2))))
    async def daily_recap(self):
        # Marquer comme envoye
        tracker_data = load_data()
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))
        meta = tracker_data.get("_meta", {})
        meta["last_daily_recap"] = now.strftime("%Y-%m-%d")
        tracker_data["_meta"] = meta
        save_data(tracker_data)
        
        await self.execute_daily_recap()
        
    async def execute_daily_recap(self):
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
        
        if not channel and not tracker_data:
            return
            
        headers = {"Authorization": HENRIK_API_KEY}
        
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))
        yesterday = now - datetime.timedelta(days=1)
        start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        start_ts = int(start_of_yesterday.timestamp())
        end_ts = int(end_of_yesterday.timestamp())
        
        embed = discord.Embed(
            title=f"Recap du {yesterday.strftime('%d/%m/%Y')}",
            color=discord.Color.from_rgb(160, 100, 255)
        )
        embed.set_author(
            name="Recap Quotidien — RR Trackerito",
            icon_url="https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/24/largeicon.png"
        )

        has_data = False

        async with aiohttp.ClientSession() as session:
            for discord_id, info in tracker_data.items():
                if discord_id == "_meta":
                    continue
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

                            sign = "+" if total_rr >= 0 else ""
                            wins_str = f"{wins}W" if wins > 0 else ""
                            losses_str = f"{losses}L" if losses > 0 else ""
                            draws_str = f"{draws}D" if draws > 0 else ""
                            result_parts = [p for p in [wins_str, losses_str, draws_str] if p]
                            stats_str = "  ".join(result_parts) + f"  ({winrate}%WR)"

                            title = f"{nom}#{tag}  •  {sign}{total_rr} RR"
                            desc = f"{stats_str}\n`{start_str}` → `{end_str}`"

                            embed.add_field(name=title, value=desc, inline=False)
                            has_data = True
                except Exception as e:
                    print(f"Erreur Recap pour {nom}#{tag} : {e}")
                    
        if has_data:
            embed.set_footer(text="RR Trackerito  •  Données via HenrikDev")
            embed.timestamp = datetime.datetime.now()

            print("=== RÉCAPITULATIF ENVOYÉ SUR DISCORD ===")
            print(json.dumps(embed.to_dict(), indent=4, ensure_ascii=False))

            if channel:
                await channel.send(embed=embed)
            else:
                for discord_id in tracker_data:
                    if discord_id == "_meta":
                        continue
                    user = self.client.get_user(int(discord_id))
                    if user:
                        try:
                            await user.send(embed=embed)
                        except:
                            pass
            
    @daily_recap.before_loop
    async def before_daily_recap(self):
        await self.client.wait_until_ready()
