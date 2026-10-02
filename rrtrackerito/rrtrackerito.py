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

# -- IMPORTS DES NOUVEAUX MODULES --
from core.config import TOKEN
from core.logger import log
from database.data_manager import DataManager

from cogs.tracker import link, unlink, TrackerTask
from services.image_services import generate_match_image, generate_group_image, generate_daily_recap_image, generate_classement_image
from cogs.tracker import RANK_BANNER_URLS
from cogs.classement import classement


# ========== BOT DISCORD ==========
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Nécessaire pour guild.get_member() → avatars Discord

class MyClient(discord.Client):
    def __init__(self, *, intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        
        # INJECTION DE LA BDD DANS LE CLIENT
        os.makedirs("data", exist_ok=True)
        self.db = DataManager("data/tracker_data.json")

    async def setup_hook(self):
        self.tracker_task = TrackerTask(self)
        
        # -- GESTIONNAIRE D'ERREURS GLOBAL --
        async def on_tree_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            log.error(f"[Slash Command Error] {interaction.command.name if interaction.command else 'Unknown'} : {error}", exc_info=error)
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Une erreur interne est survenue.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Une erreur interne est survenue.", ephemeral=True)
            except Exception as fallback_err:
                log.error(f"Impossible d'envoyer le message d'erreur : {fallback_err}")
                
        self.tree.on_error = on_tree_error
        await self.tree.sync()

    async def on_ready(self):
        log.info(f"Connecté avec succès en tant que {self.user}")
client = MyClient(intents=intents)

# ========== COMMANDES SLASH ==========
client.tree.add_command(link)
client.tree.add_command(unlink)
client.tree.add_command(classement)

import random as _random
import datetime as _dt

# ── Données de base pour la génération aléatoire ──────────────────────────────
_MAPS    = ["Ascent", "Bind", "Haven", "Split", "Fracture", "Pearl", "Lotus", "Sunset", "Abyss", "Icebox"]
_AGENTS  = [
    ("Jett",     "eb93336a-449b-9c1b-0a54-a891f7921d69"),
    ("Reyna",    "a3bfb853-43b2-7238-a4f1-ad90e9e46bcc"),
    ("Sage",     "569fdd95-4d10-43ab-ca70-79becc718b46"),
    ("Sova",     "320b2a48-4d9b-a075-30f1-1f93a9b638fa"),
    ("Omen",     "8e253930-4c05-31dd-1b6c-968525494517"),
    ("Breach",   "5f8d3a7f-467b-97f3-062c-b92e22e965fc"),
    ("Phoenix",  "eb93336a-449b-9c1b-0a54-a891f7921d69"),
    ("Neon",     "bb2a4828-46eb-8cd1-e765-15848195d751"),
    ("Killjoy",  "1dbf2edd-4729-0984-3115-daa5eed44993"),
    ("Cypher",   "117ed9e3-49f3-6512-3ccf-0cada7e3823b"),
    ("Chamber",  "22697a3d-45bf-8dd7-4fec-84a9e28c69d7"),
    ("Vyse",     "efba5359-4016-a1e5-7626-b1ae1a10f85b"),
]
_RANKS = [
    "Iron 1", "Iron 2", "Iron 3",
    "Bronze 1", "Bronze 2", "Bronze 3",
    "Silver 1", "Silver 2", "Silver 3",
    "Gold 1", "Gold 2", "Gold 3",
    "Platinum 1", "Platinum 2", "Platinum 3",
    "Diamond 1", "Diamond 2", "Diamond 3",
    "Ascendant 1",
]
_PLAYERS = [
    {"nom": "Zaki",             "tag": "5764"},
    {"nom": "lyrix",            "tag": "657"},
    {"nom": "Toshiro",          "tag": "EUWGL"},
    {"nom": "EGirlFanBoyGoon",  "tag": "MOMMY"},
    {"nom": "PerrierGingembre", "tag": "1L5DO"},
    {"nom": "Tyo",              "tag": "4498"},
]

def _rand_kda():
    k = _random.randint(3, 30)
    d = _random.randint(2, 20)
    a = _random.randint(0, 15)
    return f"{k}/{d}/{a}", k, d, a

def _rand_score():
    a = _random.randint(7, 13)
    b = _random.randint(0, 13)
    if a == 13:
        return f"{a}-{b}", a, b
    return f"{b}-{a}", b, a

def _rand_stats(k, d, nb_rounds):
    kd     = round(k / d, 2) if d > 0 else float(k)
    hs_pct = round(_random.uniform(8, 40), 1)
    adr    = _random.randint(60, 220)
    perf   = _random.randint(80, 420)
    return {"hs_pct": hs_pct, "kd": kd, "adr": adr, "perf": perf}

def _rand_rr(win):
    if win:
        return _random.randint(10, 30)
    return -_random.randint(10, 25)

def _rand_player_entry(p, rang=None):
    rang = rang or _random.choice(_RANKS)
    agent_name, agent_uuid = _random.choice(_AGENTS)
    kda_str, k, d, a = _rand_kda()
    nb_rounds = _random.randint(16, 26)
    ps = _rand_stats(k, d, nb_rounds)
    win = _random.choice([True, False])
    rr  = _rand_rr(win)
    return {
        "name":      p["nom"],
        "tag":       p["tag"],
        "rang":      rang,
        "agent_url": f"https://media.valorant-api.com/agents/{agent_uuid}/displayicon.png",
        "rank_url":  RANK_BANNER_URLS.get(rang, ""),
        "perf":      ps["perf"],
        "kda":       kda_str,
        "rr_change": rr,
        "hs_pct":    ps["hs_pct"],
        "kd":        ps["kd"],
        "adr":       ps["adr"],
    }

@app_commands.command(name="test_affichage", description="[Admin] Envoie un exemple de chaque type d'affichage du bot (données aléatoires)")
async def test_affichage(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ Génération de tous les affichages de test...", ephemeral=True)
    channel = interaction.channel

    map_solo   = _random.choice(_MAPS)
    agent_name, agent_uuid = _random.choice(_AGENTS)
    kda_str, k, d, a = _rand_kda()
    score_str, my_r, en_r = _rand_score()
    nb_rounds  = my_r + en_r
    stats_solo = _rand_stats(k, d, nb_rounds)
    rr_solo    = _rand_rr(my_r > en_r)
    rang_solo  = _random.choice(_RANKS)
    elo_solo   = _random.randint(0, 99)
    p_solo     = _PLAYERS[0]

    # ── 1. Recap solo ────────────────────────────────────────────────────────
    try:
        buf = await generate_match_image(map_solo, agent_name, kda_str, rr_solo, score_str, stats_solo)
        file  = discord.File(fp=buf, filename="recap.png")
        is_win  = rr_solo > 0
        is_draw = rr_solo == 0
        result  = "VICTOIRE" if is_win else "DÉFAITE" if not is_draw else "ÉGALITÉ"
        color   = discord.Color.from_rgb(0, 200, 120) if is_win else discord.Color.from_rgb(255, 60, 80) if not is_draw else discord.Color.from_rgb(120, 120, 120)
        sign    = "+" if rr_solo > 0 else ""
        desc    = f"▶ {p_solo['nom']} {'a gagné' if is_win else 'a perdu'} {abs(rr_solo)} RR ({rang_solo} — {elo_solo} RR)"
        embed   = discord.Embed(title=result, description=desc, color=color)
        embed.set_author(name=f"{p_solo['nom']}#{p_solo['tag']} — {rang_solo}")
        embed.set_image(url="attachment://recap.png")
        embed.set_footer(text="Test Affichage • Solo")
        await channel.send(content=f"**Solo** — {result.lower()} sur {map_solo}", embed=embed, file=file)
    except Exception as e:
        await channel.send(f"❌ Erreur solo : {e}")

    # ── 2. Recap duo ─────────────────────────────────────────────────────────
    try:
        map_duo   = _random.choice(_MAPS)
        sc_str, my, en = _rand_score()
        win_duo   = my > en
        result_duo = "VICTOIRE" if win_duo else "DÉFAITE"
        duo_sample = _random.sample(_PLAYERS, 2)
        duo_players = [_rand_player_entry(p) for p in duo_sample]
        for p in duo_players:
            p["rr_change"] = _rand_rr(win_duo)
        buf  = await generate_group_image(duo_players, map_name=map_duo, match_score=sc_str, result_text=result_duo)
        file = discord.File(fp=buf, filename="recap_groupe.png")
        await channel.send(content=f"**Duo** — {result_duo.lower()} sur {map_duo}", file=file)
    except Exception as e:
        await channel.send(f"❌ Erreur duo : {e}")

    # ── 3. Recap trio ────────────────────────────────────────────────────────
    try:
        map_trio  = _random.choice(_MAPS)
        sc_str, my, en = _rand_score()
        win_trio  = my > en
        result_trio = "VICTOIRE" if win_trio else "DÉFAITE"
        trio_sample = _random.sample(_PLAYERS, 3)
        trio_players = [_rand_player_entry(p) for p in trio_sample]
        for p in trio_players:
            p["rr_change"] = _rand_rr(win_trio)
        buf  = await generate_group_image(trio_players, map_name=map_trio, match_score=sc_str, result_text=result_trio)
        file = discord.File(fp=buf, filename="recap_groupe.png")
        await channel.send(content=f"**Trio** — {result_trio.lower()} sur {map_trio}", file=file)
    except Exception as e:
        await channel.send(f"❌ Erreur trio : {e}")

    # ── 4. Recap 5-stack ─────────────────────────────────────────────────────
    try:
        map_5     = _random.choice(_MAPS)
        sc_str, my, en = _rand_score()
        win_5     = my > en
        result_5  = "VICTOIRE" if win_5 else "DÉFAITE"
        stack_players = [_rand_player_entry(p) for p in _PLAYERS[:5]]
        for p in stack_players:
            p["rr_change"] = _rand_rr(win_5)
        buf  = await generate_group_image(stack_players, map_name=map_5, match_score=sc_str, result_text=result_5)
        file = discord.File(fp=buf, filename="recap_groupe.png")
        await channel.send(content=f"**5-Stack** — {result_5.lower()} sur {map_5}", file=file)
    except Exception as e:
        await channel.send(f"❌ Erreur 5-stack : {e}")

    # ── 5. Recap journalier ───────────────────────────────────────────────────
    try:
        fake_daily = []
        for p in _PLAYERS:
            nb_games = _random.randint(1, 7)
            wins     = _random.randint(0, nb_games)
            losses   = nb_games - wins
            draws    = 0
            total_rr = sum(_rand_rr(True) for _ in range(wins)) + sum(_rand_rr(False) for _ in range(losses))
            winrate  = round(wins / nb_games * 100, 1) if nb_games > 0 else 0.0
            start_rang = _random.choice(_RANKS)
            end_rang   = _random.choice(_RANKS)
            start_rr   = _random.randint(0, 99)
            end_rr     = _random.randint(0, 99)
            fake_daily.append({
                "nom":       p["nom"],
                "tag":       p["tag"],
                "total_rr":  total_rr,
                "wins":      wins,
                "losses":    losses,
                "draws":     draws,
                "winrate":   winrate,
                "start_rang": start_rang,
                "start_rr":  start_rr,
                "end_rang":  end_rang,
                "end_rr":    end_rr,
            })
        date_label = _dt.datetime.now().strftime("%d/%m/%Y")
        buf  = await generate_daily_recap_image(date_label, fake_daily)
        file = discord.File(fp=buf, filename="recap_quotidien.png")
        await channel.send(content="**Recap journalier**", file=file)
    except Exception as e:
        await channel.send(f"❌ Erreur recap journalier : {e}")

    # ── 6. Classement ─────────────────────────────────────────────────────────
    try:
        fake_classement = []
        for p in _PLAYERS:
            rang = _random.choice(_RANKS)
            rr   = _random.randint(0, 99)
            tier = _RANKS.index(rang)
            elo  = tier * 100 + rr
            fake_classement.append({
                "nom":  p["nom"],
                "tag":  p["tag"],
                "elo":  elo,
                "rang": rang,
                "rr":   rr,
            })
        fake_classement.sort(key=lambda x: x["elo"], reverse=True)
        buf  = await generate_classement_image(fake_classement)
        file = discord.File(fp=buf, filename="classement.png")
        await channel.send(content="**Classement**", file=file)
    except Exception as e:
        await channel.send(f"❌ Erreur classement : {e}")

client.tree.add_command(test_affichage)

# ========== LANCEMENT ==========
client.run(TOKEN)