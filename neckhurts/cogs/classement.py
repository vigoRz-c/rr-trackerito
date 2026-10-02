import discord
from discord import app_commands
import aiohttp
import os
import io
from cogs.tracker import load_data
from utils.image_reports_generator import generate_classement_image

HENRIK_API_KEY = os.getenv("HENRIK_API_KEY")


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

            # Récupération de l'avatar Discord du membre
            avatar_url = None
            try:
                member = interaction.guild.get_member(int(discord_id)) if interaction.guild else None
                if member:
                    avatar_url = member.display_avatar.url
            except Exception:
                pass

            url = f"https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{nom}/{tag}"
            try:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = (await resp.json()).get("data") or {}
                        elo  = data.get("elo", 0)
                        rang = data.get("currenttierpatched", "Non classé")
                        rr   = data.get("ranking_in_tier", 0)
                        resultats.append({
                            "nom":               nom,
                            "tag":               tag,
                            "elo":               elo,
                            "rang":              rang,
                            "rr":                rr,
                            "discord_avatar_url": avatar_url,
                        })
                    else:
                        resultats.append({
                            "nom":               nom,
                            "tag":               tag,
                            "elo":               0,
                            "rang":              "Indisponible",
                            "rr":                0,
                            "discord_avatar_url": avatar_url,
                        })
            except Exception as e:
                print(f"Erreur classement pour {nom}#{tag}: {e}")
                resultats.append({
                    "nom":               nom,
                    "tag":               tag,
                    "elo":               0,
                    "rang":              "Erreur",
                    "rr":                0,
                    "discord_avatar_url": avatar_url,
                })

    # Tri décroissant par ELO
    resultats.sort(key=lambda x: x["elo"], reverse=True)

    try:
        buf = await generate_classement_image(resultats)
        file = discord.File(fp=buf, filename="classement.png")
        await interaction.followup.send(file=file)
    except Exception as e:
        print(f"Erreur génération image classement : {e}")
        # Fallback : embed texte si la génération d'image échoue
        view = ClassementPaginationView(resultats, interaction.user.id)
        embed = view.generate_embed()
        if view.total_pages <= 1:
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=embed, view=view)


import datetime
import math

VALORANT_ICON = "https://media.valorant-api.com/gamemodes/96bd3920-4f36-d026-2b28-c683eb0bcac5/displayicon.png"


class ClassementPaginationView(discord.ui.View):
    """Fallback texte si la génération d'image échoue."""

    def __init__(self, resultats, author_id, per_page=15):
        super().__init__(timeout=180)
        self.resultats    = resultats
        self.author_id    = author_id
        self.per_page     = per_page
        self.current_page = 1
        self.total_pages  = math.ceil(len(resultats) / per_page) if resultats else 1
        self.update_buttons()

    def update_buttons(self):
        self.btn_prev.disabled = (self.current_page == 1)
        self.btn_next.disabled = (self.current_page == self.total_pages)

    def generate_embed(self):
        start_idx    = (self.current_page - 1) * self.per_page
        end_idx      = start_idx + self.per_page
        page_results = self.resultats[start_idx:end_idx]

        PODIUM = {1: " #1 ", 2: " #2 ", 3: " #3 "}
        rows = []
        for index_in_page, j in enumerate(page_results):
            global_idx = start_idx + index_in_page + 1
            if global_idx <= 3:
                pos = f"{PODIUM.get(global_idx)} "
            else:
                pos = f" #{global_idx} ".ljust(5)
            nom_tag  = f"{j['nom']}#{j['tag']}"
            rang_str = j["rang"] if j["elo"] > 0 else "—"
            rr_str   = f"{j['rr']} RR" if j["elo"] > 0 else "—"
            nom_tag  = nom_tag[:22].ljust(22)
            rang_str = rang_str[:14].ljust(14)
            rows.append(f"{pos} {nom_tag}  {rang_str}  {rr_str}")

        header      = " Pos   Joueur                    Rang              RR"
        sep         = "─" * 52
        table       = "\n".join(rows) if rows else "Aucun joueur."
        table_block = f"```\n{header}\n{sep}\n{table}\n```"

        embed = discord.Embed(
            title="Classement des membres",
            description=table_block,
            color=discord.Color.from_rgb(255, 180, 0)
        )
        embed.set_author(name="RR Trackerito", icon_url=VALORANT_ICON)
        embed.set_footer(text=f"Page {self.current_page}/{self.total_pages}  ·  {len(self.resultats)} membre(s) total  ·  Données via HenrikDev")
        embed.timestamp = datetime.datetime.now()
        return embed

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary, custom_id="prev_page")
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Tu ne peux pas changer la page de ce classement.", ephemeral=True)
            return
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary, custom_id="next_page")
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Tu ne peux pas changer la page de ce classement.", ephemeral=True)
            return
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)
