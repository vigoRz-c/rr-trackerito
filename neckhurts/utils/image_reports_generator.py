"""
image_reports_generator.py
==========================
Générateur d'images premium style Valorant pour :
  - Le panneau de classement  (/classement)
  - Le récapitulatif quotidien (Recap Quotidien)

Dépendances : Pillow (PIL), aiohttp
"""

import io
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from typing import Optional

# ─── URLs officielles des icônes de rang Valorant ─────────────────────────────
RANK_ICON_URLS: dict = {
    "Iron 1":      "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/3/largeicon.png",
    "Iron 2":      "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/4/largeicon.png",
    "Iron 3":      "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/5/largeicon.png",
    "Bronze 1":    "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/6/largeicon.png",
    "Bronze 2":    "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/7/largeicon.png",
    "Bronze 3":    "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/8/largeicon.png",
    "Silver 1":    "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/9/largeicon.png",
    "Silver 2":    "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/10/largeicon.png",
    "Silver 3":    "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/11/largeicon.png",
    "Gold 1":      "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/12/largeicon.png",
    "Gold 2":      "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/13/largeicon.png",
    "Gold 3":      "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/14/largeicon.png",
    "Platinum 1":  "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/15/largeicon.png",
    "Platinum 2":  "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/16/largeicon.png",
    "Platinum 3":  "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/17/largeicon.png",
    "Diamond 1":   "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/18/largeicon.png",
    "Diamond 2":   "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/19/largeicon.png",
    "Diamond 3":   "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/20/largeicon.png",
    "Ascendant 1": "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/21/largeicon.png",
    "Ascendant 2": "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/22/largeicon.png",
    "Ascendant 3": "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/23/largeicon.png",
    "Immortal 1":  "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/24/largeicon.png",
    "Immortal 2":  "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/25/largeicon.png",
    "Immortal 3":  "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/26/largeicon.png",
    "Radiant":     "https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/27/largeicon.png",
}

# ─── Couleurs accent par rang ──────────────────────────────────────────────────
RANK_ACCENT: dict = {
    "iron":      (150, 150, 150),
    "bronze":    (205, 127, 50),
    "silver":    (192, 192, 192),
    "gold":      (255, 215, 0),
    "platinum":  (100, 220, 255),
    "diamond":   (180, 130, 255),
    "ascendant": (80, 255, 160),
    "immortal":  (255, 80, 80),
    "radiant":   (255, 240, 100),
}

# ─── Palette globale ───────────────────────────────────────────────────────────
BG_DARK   = (13, 14, 20)
BG_CARD   = (22, 24, 34)
BG_HEADER = (18, 19, 28)
ACCENT    = (255, 70, 85)
NEON_BLUE = (0, 212, 255)
TEXT_WH   = (255, 255, 255)
TEXT_GREY = (140, 145, 165)
SEP_LINE  = (35, 38, 55)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates_bold = ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"]
    candidates_reg  = ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]
    for name in (candidates_bold if bold else candidates_reg):
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


async def _fetch_img(url: str, session: aiohttp.ClientSession, size: Optional[tuple] = None) -> Optional[Image.Image]:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                raw = await resp.read()
                img = Image.open(io.BytesIO(raw)).convert("RGBA")
                if size:
                    img = img.resize(size, Image.Resampling.LANCZOS)
                return img
    except Exception as e:
        print(f"[ImageGen] fetch error {url}: {e}")
    return None


def _rank_accent(rang: str) -> tuple:
    r = rang.lower() if rang else ""
    for key, color in RANK_ACCENT.items():
        if key in r:
            return color
    return TEXT_GREY


def _draw_rounded_rect(draw: ImageDraw.Draw, xy: tuple, radius: int, fill: tuple, outline=None, outline_width: int = 1):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=outline_width)


def _paste_with_alpha(base: Image.Image, layer: Image.Image, pos: tuple):
    if layer.mode != "RGBA":
        layer = layer.convert("RGBA")
    base.paste(layer, pos, layer)


def _draw_gradient_bg(img: Image.Image, color1: tuple, color2: tuple):
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(color1[0] * (1 - t) + color2[0] * t)
        g = int(color1[1] * (1 - t) + color2[1] * t)
        b = int(color1[2] * (1 - t) + color2[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


# ══════════════════════════════════════════════════════════════════════════════
#  PANNEAU DE CLASSEMENT
# ══════════════════════════════════════════════════════════════════════════════

async def generate_classement_image(resultats: list) -> io.BytesIO:
    """
    Génère un panneau de classement style Valorant.

    resultats : liste de dicts triés par ELO décroissant :
        { nom, tag, elo, rang, rr }
    """
    W         = 860
    HEADER_H  = 110
    ROW_H     = 64
    PADDING   = 24
    FOOTER_H  = 42
    n         = max(len(resultats), 1)
    H         = HEADER_H + n * ROW_H + FOOTER_H + PADDING

    img = Image.new("RGB", (W, H), BG_DARK)
    _draw_gradient_bg(img, (13, 14, 22), (20, 18, 30))
    draw = ImageDraw.Draw(img, "RGBA")

    font_title    = _load_font(26, bold=True)
    font_subtitle = _load_font(13)
    font_col_hdr  = _load_font(12)
    font_pos      = _load_font(20, bold=True)
    font_player   = _load_font(16, bold=True)
    font_tag      = _load_font(13)
    font_rang     = _load_font(14, bold=True)
    font_rr       = _load_font(18, bold=True)
    font_footer   = _load_font(11)

    # En-tête
    draw.rectangle([(0, 0), (W, HEADER_H)], fill=BG_HEADER)
    draw.rectangle([(0, 0), (5, HEADER_H)], fill=ACCENT)
    draw.text((22, 18), "CLASSEMENT DES MEMBRES", font=font_title, fill=TEXT_WH)
    draw.text((22, 52), "VALORANT  ·  Classement ELO compétitif en temps réel", font=font_subtitle, fill=TEXT_GREY)

    badge_text = f"{len(resultats)} joueurs"
    badge_w = 90
    _draw_rounded_rect(draw, (W - badge_w - 20, 32, W - 20, 70), radius=8, fill=ACCENT)
    bw = draw.textbbox((0, 0), badge_text, font=font_subtitle)[2]
    bh = draw.textbbox((0, 0), badge_text, font=font_subtitle)[3]
    draw.text((W - badge_w - 20 + (badge_w - bw) // 2, 32 + (38 - bh) // 2), badge_text, font=font_subtitle, fill=TEXT_WH)

    draw.rectangle([(0, HEADER_H - 2), (W, HEADER_H)], fill=ACCENT)

    # En-têtes de colonnes
    col_hdr_y  = HEADER_H + 10
    COL_POS    = 30
    COL_PLAYER = 110
    COL_RANG   = 460
    COL_RR     = 690

    draw.text((COL_POS,    col_hdr_y), "POS",    font=font_col_hdr, fill=TEXT_GREY)
    draw.text((COL_PLAYER, col_hdr_y), "JOUEUR", font=font_col_hdr, fill=TEXT_GREY)
    draw.text((COL_RANG,   col_hdr_y), "RANG",   font=font_col_hdr, fill=TEXT_GREY)
    draw.text((COL_RR,     col_hdr_y), "RR",     font=font_col_hdr, fill=TEXT_GREY)

    # Téléchargement des icônes de rang en parallèle
    async with aiohttp.ClientSession() as session:
        rank_urls = [RANK_ICON_URLS.get(j["rang"]) for j in resultats]
        rank_tasks = [_fetch_img(u, session, (40, 40)) if u else asyncio.sleep(0) for u in rank_urls]
        rank_icons = list(await asyncio.gather(*rank_tasks))

    PODIUM_COLORS = {
        1: (255, 215,   0),
        2: (192, 192, 192),
        3: (205, 127,  50),
    }

    for i, joueur in enumerate(resultats):
        rank_pos = i + 1
        row_y    = HEADER_H + 32 + i * ROW_H
        row_y2   = row_y + ROW_H - 4

        row_bg = (26, 28, 40) if i % 2 == 0 else (22, 24, 34)
        draw.rectangle([(0, row_y - 4), (W, row_y2)], fill=row_bg)

        if rank_pos <= 3:
            accent_col = PODIUM_COLORS[rank_pos]
            draw.rectangle([(0, row_y - 4), (4, row_y2)], fill=accent_col)

        # Position
        pos_text  = f"#{rank_pos}"
        pos_color = PODIUM_COLORS.get(rank_pos, TEXT_GREY)
        pos_font  = font_pos if rank_pos <= 3 else font_rang
        draw.text((COL_POS, row_y + 14), pos_text, font=pos_font, fill=pos_color)

        # Avatar initiale dans un cercle
        avatar_size = 40
        avatar_x = COL_PLAYER - 4
        avatar_y = row_y + 8
        accent_col_rank = _rank_accent(joueur["rang"])
        draw.ellipse(
            [(avatar_x, avatar_y), (avatar_x + avatar_size, avatar_y + avatar_size)],
            fill=(*accent_col_rank, 40),
            outline=(*accent_col_rank, 180),
            width=2
        )
        initial = joueur["nom"][0].upper() if joueur["nom"] else "?"
        iw = draw.textbbox((0, 0), initial, font=font_rang)[2]
        ih = draw.textbbox((0, 0), initial, font=font_rang)[3]
        draw.text(
            (avatar_x + (avatar_size - iw) // 2, avatar_y + (avatar_size - ih) // 2),
            initial, font=font_rang, fill=accent_col_rank
        )

        # Nom + tag
        name_x = COL_PLAYER + avatar_size + 10
        draw.text((name_x, row_y + 8),  joueur["nom"][:18],    font=font_player, fill=TEXT_WH)
        draw.text((name_x, row_y + 30), f"#{joueur['tag']}",   font=font_tag,    fill=TEXT_GREY)

        # Icône de rang + texte
        icon = rank_icons[i]
        rang_text = joueur["rang"] if joueur["elo"] > 0 else "—"
        if isinstance(icon, Image.Image):
            _paste_with_alpha(img, icon, (COL_RANG - 2, row_y + 10))
            draw.text((COL_RANG + 46, row_y + 20), rang_text, font=font_rang, fill=accent_col_rank)
        else:
            draw.text((COL_RANG, row_y + 20), rang_text, font=font_rang, fill=accent_col_rank)

        # RR
        rr_text = str(joueur["rr"]) if joueur["elo"] > 0 else "—"
        draw.text((COL_RR, row_y + 14), rr_text, font=font_rr, fill=TEXT_WH)
        if joueur["elo"] > 0:
            draw.text((COL_RR + 34, row_y + 20), "RR", font=font_tag, fill=TEXT_GREY)

        # Ligne séparatrice
        draw.rectangle([(PADDING, row_y2), (W - PADDING, row_y2 + 1)], fill=SEP_LINE)

    # Pied de page
    footer_y = H - FOOTER_H + 10
    draw.rectangle([(0, H - FOOTER_H), (W, H)], fill=BG_HEADER)
    draw.rectangle([(0, H - FOOTER_H), (W, H - FOOTER_H + 1)], fill=SEP_LINE)
    draw.text((PADDING, footer_y), "RR Trackerito  •  Données en temps réel via HenrikDev API", font=font_footer, fill=TEXT_GREY)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════════════════════
#  RECAP QUOTIDIEN
# ══════════════════════════════════════════════════════════════════════════════

async def generate_daily_recap_image(date_label: str, players_data: list) -> io.BytesIO:
    """
    Génère un panneau de récapitulatif quotidien style Valorant.

    date_label   : ex. "01/10/2026"
    players_data : liste de dicts :
        { nom, tag, total_rr, wins, losses, draws, winrate,
          start_rang, start_rr, end_rang, end_rr }
    """
    W        = 900
    HEADER_H = 120
    CARD_H   = 130
    CARD_GAP = 14
    PADDING  = 22
    FOOTER_H = 44
    n        = max(len(players_data), 1)
    H        = HEADER_H + n * (CARD_H + CARD_GAP) + FOOTER_H + PADDING

    img = Image.new("RGB", (W, H), BG_DARK)
    _draw_gradient_bg(img, (10, 12, 20), (18, 15, 28))
    draw = ImageDraw.Draw(img, "RGBA")

    font_title   = _load_font(28, bold=True)
    font_subtitle = _load_font(13)
    font_date    = _load_font(14, bold=True)
    font_player  = _load_font(17, bold=True)
    font_tag_sm  = _load_font(12)
    font_rr_big  = _load_font(30, bold=True)
    font_label   = _load_font(11)
    font_stat    = _load_font(16, bold=True)
    font_rang_sm = _load_font(13, bold=True)
    font_footer  = _load_font(11)

    # En-tête
    draw.rectangle([(0, 0), (W, HEADER_H)], fill=BG_HEADER)
    draw.rectangle([(0, 0), (5, HEADER_H)], fill=ACCENT)
    draw.text((22, 18), "RECAP QUOTIDIEN", font=font_title, fill=TEXT_WH)
    draw.text((22, 60), "Résumé des performances compétitives de la journée", font=font_subtitle, fill=TEXT_GREY)

    # Date pill
    date_text = date_label
    dt_w = draw.textbbox((0, 0), date_text, font=font_date)[2]
    pill_x = W - dt_w - 56
    _draw_rounded_rect(draw, (pill_x - 10, 30, W - 20, 70), radius=10, fill=(30, 32, 48), outline=NEON_BLUE, outline_width=1)
    draw.text((pill_x, 40), date_text, font=font_date, fill=NEON_BLUE)

    draw.rectangle([(0, HEADER_H - 2), (W, HEADER_H)], fill=ACCENT)

    # Téléchargement des icônes de rang (start + end) pour chaque joueur
    all_rank_urls = []
    for pd in players_data:
        all_rank_urls.append(RANK_ICON_URLS.get(pd.get("end_rang", ""), None))
        all_rank_urls.append(RANK_ICON_URLS.get(pd.get("start_rang", ""), None))

    async with aiohttp.ClientSession() as session:
        tasks = [_fetch_img(u, session, (38, 38)) if u else asyncio.sleep(0) for u in all_rank_urls]
        rank_imgs_flat = list(await asyncio.gather(*tasks))

    # Cartes joueurs
    for i, pd in enumerate(players_data):
        card_y = HEADER_H + PADDING // 2 + i * (CARD_H + CARD_GAP)

        end_icon   = rank_imgs_flat[i * 2]     if isinstance(rank_imgs_flat[i * 2],     Image.Image) else None
        start_icon = rank_imgs_flat[i * 2 + 1] if isinstance(rank_imgs_flat[i * 2 + 1], Image.Image) else None

        nom        = pd.get("nom", "Inconnu")
        tag        = pd.get("tag", "???")
        total_rr   = pd.get("total_rr", 0)
        wins       = pd.get("wins", 0)
        losses     = pd.get("losses", 0)
        draws_     = pd.get("draws", 0)
        winrate    = pd.get("winrate", 0.0)
        start_rang = pd.get("start_rang", "?")
        start_rr_v = pd.get("start_rr", "?")
        end_rang   = pd.get("end_rang", "?")
        end_rr_v   = pd.get("end_rr", 0)

        is_positive   = total_rr >= 0
        rr_accent_c   = (80, 230, 140) if is_positive else (255, 80, 80)
        rank_accent_c = _rank_accent(end_rang)

        # Fond carte
        _draw_rounded_rect(draw, (PADDING, card_y, W - PADDING, card_y + CARD_H),
                           radius=12, fill=BG_CARD, outline=(*rank_accent_c, 60), outline_width=1)
        # Barre latérale colorée
        draw.rectangle([(PADDING, card_y + 6), (PADDING + 4, card_y + CARD_H - 6)], fill=rr_accent_c)

        # Avatar (initiale dans un cercle)
        AV_SIZE = 52
        av_x = PADDING + 18
        av_y = card_y + (CARD_H - AV_SIZE) // 2
        draw.ellipse([(av_x, av_y), (av_x + AV_SIZE, av_y + AV_SIZE)],
                     fill=(*rank_accent_c, 30), outline=(*rank_accent_c, 160), width=2)
        initial = nom[0].upper() if nom else "?"
        iw = draw.textbbox((0, 0), initial, font=font_player)[2]
        ih = draw.textbbox((0, 0), initial, font=font_player)[3]
        draw.text((av_x + (AV_SIZE - iw) // 2, av_y + (AV_SIZE - ih) // 2),
                  initial, font=font_player, fill=rank_accent_c)

        # Nom + Tag
        name_x = av_x + AV_SIZE + 14
        draw.text((name_x, card_y + 18), nom[:20], font=font_player, fill=TEXT_WH)
        draw.text((name_x, card_y + 42), f"#{tag}", font=font_tag_sm, fill=TEXT_GREY)

        # Bilan RR
        sign   = "+" if total_rr >= 0 else ""
        rr_str = f"{sign}{total_rr} RR"
        rr_x   = 310
        draw.text((rr_x, card_y + 20), rr_str, font=font_rr_big, fill=rr_accent_c)

        rr_w = draw.textbbox((0, 0), rr_str, font=font_rr_big)[2]
        arrow = "▲" if is_positive else "▼"
        draw.text((rr_x + rr_w + 8, card_y + 28), arrow, font=font_stat, fill=rr_accent_c)

        # Stats W / L / WR%
        wl_str = f"{wins}V  {losses}D"
        if draws_ > 0:
            wl_str += f"  {draws_}N"
        draw.text((rr_x, card_y + 68), wl_str, font=font_stat, fill=TEXT_WH)
        draw.text((rr_x, card_y + 94), f"Win rate : {winrate:.1f}%", font=font_label, fill=TEXT_GREY)

        # Progression de rang
        prog_x = 600
        prog_y = card_y + 20

        if start_icon:
            _paste_with_alpha(img, start_icon, (prog_x, prog_y))
            draw.text((prog_x + 42, prog_y + 4),  start_rang,        font=font_rang_sm, fill=TEXT_GREY)
            draw.text((prog_x + 42, prog_y + 20), f"{start_rr_v} RR", font=font_label,   fill=TEXT_GREY)
        else:
            draw.text((prog_x, prog_y + 8), start_rang, font=font_rang_sm, fill=TEXT_GREY)

        arr_x = prog_x + 140
        draw.text((arr_x, prog_y + 10), "→", font=font_stat, fill=TEXT_GREY)

        end_x = arr_x + 30
        if end_icon:
            _paste_with_alpha(img, end_icon, (end_x, prog_y))
            draw.text((end_x + 42, prog_y + 4),  end_rang,            font=font_rang_sm, fill=rank_accent_c)
            draw.text((end_x + 42, prog_y + 20), f"{end_rr_v} RR",    font=font_label,   fill=rank_accent_c)
        else:
            draw.text((end_x, prog_y + 8), end_rang, font=font_rang_sm, fill=rank_accent_c)

        # Barre de progression RR
        bar_x  = prog_x
        bar_y  = card_y + 80
        bar_w  = 240
        bar_h  = 8
        rr_fill = max(0, min(int(end_rr_v) if isinstance(end_rr_v, (int, float)) else 0, 100))
        _draw_rounded_rect(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=4, fill=(40, 42, 60))
        if rr_fill > 0:
            _draw_rounded_rect(draw, (bar_x, bar_y, bar_x + int(bar_w * rr_fill / 100), bar_y + bar_h),
                               radius=4, fill=rank_accent_c)
        draw.text((bar_x, bar_y + 12), f"{rr_fill}/100 RR", font=font_label, fill=TEXT_GREY)

    # Pied de page
    footer_y_top = H - FOOTER_H
    draw.rectangle([(0, footer_y_top), (W, H)], fill=BG_HEADER)
    draw.rectangle([(0, footer_y_top), (W, footer_y_top + 1)], fill=SEP_LINE)
    draw.text((PADDING, footer_y_top + 14), "RR Trackerito  •  Données via HenrikDev API", font=font_footer, fill=TEXT_GREY)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
