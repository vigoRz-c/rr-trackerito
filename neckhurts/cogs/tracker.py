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

            embed.set_footer(text="Neckhurts Tracker  •  Données via HenrikDev")
            embed.timestamp = datetime.datetime.now()
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : {e}", ephemeral=True)


# ─── Construction de l'embed premium après une partie ─────────────────────────
def build_match_embed(nom, tag, rang, rr_actuel, mmr_change, diff,
                      agent, kda, map_name, match_score, agent_image_url,
                      acs, hs_pct, nb_rounds):
    is_win = diff > 0
    is_draw = diff == 0
    result_text = "VICTOIRE" if is_win else "DÉFAITE" if not is_draw else "ÉGALITÉ"
    color = discord.Color.from_rgb(0, 200, 120) if is_win else discord.Color.from_rgb(255, 60, 80) if not is_draw else discord.Color.from_rgb(120, 120, 120)

    sign = "+" if mmr_change >= 0 else ""
    rr_display = f"{sign}{mmr_change} RR"

    embed = discord.Embed(
        title=f"{result_text}  •  {match_score}",
        color=color
    )
    embed.set_author(
        name=f"{nom}#{tag}  —  {rang}  {rr_actuel} RR",
        icon_url=VALORANT_ICON
    )

    # Icone du rang en miniature (petite, coin droit) + agent en image si dispo
    rank_banner = RANK_BANNER_URLS.get(rang)
    if agent_image_url:
        embed.set_thumbnail(url=agent_image_url)
    elif rank_banner:
        embed.set_thumbnail(url=rank_banner)

    # ─ Stats ligne 1 : KDA / ACS / HS% ─
    embed.add_field(name="KDA", value=f"**{kda}**", inline=True)
    embed.add_field(name="ACS", value=f"**{acs}**", inline=True)
    embed.add_field(name="HS%", value=f"**{hs_pct}%**", inline=True)

    # ─ Stats ligne 2 : Agent / Map / Rounds ─
    embed.add_field(name="Agent", value=agent, inline=True)
    embed.add_field(name="Map", value=map_name, inline=True)
    embed.add_field(name="Rounds", value=str(nb_rounds), inline=True)

    # ─ RR en grand ─
    rr_label = "RR Gagnés" if is_win else "RR Perdus" if not is_draw else "RR"
    embed.add_field(name=rr_label, value=f"```{rr_display}```", inline=False)

    embed.set_footer(text="Neckhurts Tracker  •  Données via HenrikDev")
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
            for discord_id, info in tracker_data.items():
                if discord_id == "_meta":
                    continue
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

                            if current_elo != last_elo and current_elo != 0 and last_elo != 0:
                                diff = current_elo - last_elo
                                mmr_change = data_api.get("mmr_change_to_last_game", diff)
                                rang = data_api.get("currenttierpatched", "Inconnu")
                                rr_actuel = data_api.get("ranking_in_tier", 0)

                                # ─ Données du dernier match ─
                                match_url = f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{nom}/{tag}?size=1"
                                agent = "Inconnu"
                                kda = "0/0/0"
                                map_name = "Inconnue"
                                match_score = "0-0"
                                agent_image_url = None
                                acs = 0
                                hs_pct = 0.0
                                nb_rounds = 0

                                try:
                                    async with session.get(match_url, headers=headers) as match_resp:
                                        if match_resp.status == 200:
                                            match_data = await match_resp.json()
                                            if match_data.get("data") and len(match_data["data"]) > 0:
                                                match = match_data["data"][0]
                                                metadata = match.get("metadata") or {}
                                                map_name = metadata.get("map", "Inconnue")
                                                nb_rounds = metadata.get("rounds_played") or 0

                                                players_dict = match.get("players") or {}
                                                all_players = players_dict.get("all_players", [])

                                                ps = extract_player_stats(all_players, nom, tag)
                                                if ps:
                                                    agent = ps["agent"]
                                                    kda = ps["kda"]
                                                    agent_image_url = ps["agent_image"]
                                                    hs_pct = ps["hs_pct"]
                                                    acs = compute_acs(ps["score_raw"], nb_rounds)
                                                    player_team = ps.get("team")

                                                    if player_team:
                                                        teams = match.get("teams") or {}
                                                        my_team = teams.get(player_team.lower()) or {}
                                                        enemy_key = "blue" if player_team.lower() == "red" else "red"
                                                        enemy_team = teams.get(enemy_key) or {}
                                                        match_score = f"{my_team.get('rounds_won', 0)}-{enemy_team.get('rounds_won', 0)}"

                                except Exception as e:
                                    print(f"Erreur récupération match pour {nom}#{tag}: {e}")

                                # ─ Embed premium ─
                                embed = build_match_embed(
                                    nom=nom, tag=tag, rang=rang, rr_actuel=rr_actuel,
                                    mmr_change=mmr_change, diff=diff,
                                    agent=agent, kda=kda, map_name=map_name,
                                    match_score=match_score, agent_image_url=agent_image_url,
                                    acs=acs, hs_pct=hs_pct, nb_rounds=nb_rounds
                                )

                                # ─ Bouton 5 dernières games ─
                                view = DernieresGamesView(nom=nom, tag=tag, region=region)

                                print("=== MESSAGE ENVOYÉ SUR DISCORD ===")
                                print(json.dumps(embed.to_dict(), indent=4, ensure_ascii=False))

                                if channel:
                                    await channel.send(embed=embed, view=view)
                                else:
                                    user = self.client.get_user(int(discord_id))
                                    if user:
                                        try:
                                            await user.send(embed=embed, view=view)
                                        except:
                                            pass

                                tracker_data[discord_id]["last_elo"] = current_elo
                                save_data(tracker_data)

                except Exception as e:
                    print(f"Erreur Tracker pour {nom}#{tag} : {e}")

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
            title=f"📊 Récapitulatif du {yesterday.strftime('%d/%m/%Y')}",
            color=discord.Color.from_rgb(160, 100, 255)
        )
        embed.set_author(
            name="Recap Quotidien — Neckhurts Tracker",
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
            embed.set_footer(text="Neckhurts Tracker  •  Données via HenrikDev")
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
