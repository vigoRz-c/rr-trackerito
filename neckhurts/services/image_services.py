import io
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageMath, ImageFilter

async def fetch_image(url: str, session: aiohttp.ClientSession) -> Image.Image:
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.read()
                return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception as e:
        print(f"Erreur téléchargement image {url}: {e}")
    return None

async def get_map_image(map_name: str, session: aiohttp.ClientSession) -> Image.Image:
    try:
        url = "https://valorant-api.com/v1/maps"
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                for m in data.get("data", []):
                    if m.get("displayName", "").lower() == map_name.lower():
                        splash_url = m.get("splash")
                        if splash_url:
                            return await fetch_image(splash_url, session)
    except Exception as e:
        print(f"Erreur get_map_image: {e}")
    return None

async def get_agent_image(agent_name: str, session: aiohttp.ClientSession) -> Image.Image:
    try:
        url = "https://valorant-api.com/v1/agents?isPlayableCharacter=true"
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                for a in data.get("data", []):
                    if a.get("displayName", "").lower() == agent_name.lower():
                        display_url = a.get("displayIcon")
                        if display_url:
                            return await fetch_image(display_url, session)
    except Exception as e:
        print(f"Erreur get_agent_image: {e}")
    return None

async def generate_match_image(map_name: str, agent_name: str, kda: str, rr_change: int, match_score: str, stats: dict = None) -> io.BytesIO:
    """Génère une image premium récapitulative de la partie."""
    if stats is None:
        stats = {}
        
    width, height = 800, 400
    
    async with aiohttp.ClientSession() as session:
        map_task = asyncio.create_task(get_map_image(map_name, session))
        agent_task = asyncio.create_task(get_agent_image(agent_name, session))
        map_img, agent_img = await asyncio.gather(map_task, agent_task)

    # 1. Background
    bg = Image.new("RGBA", (width, height), (30, 34, 42, 255))
    if map_img:
        map_ratio = map_img.width / map_img.height
        target_ratio = width / height
        
        if map_ratio > target_ratio:
            new_height = height
            new_width = int(new_height * map_ratio)
            map_img = map_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            left = (new_width - width) / 2
            map_img = map_img.crop((left, 0, left + width, height))
        else:
            new_width = width
            new_height = int(new_width / map_ratio)
            map_img = map_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            top = (new_height - height) / 2
            map_img = map_img.crop((0, top, width, top + height))
            
        bg.paste(map_img.convert("RGBA"), (0,0))

    # Dark overlay gradient (darker on the right)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for x in range(width):
        alpha = int(80 + 140 * (x / width)) 
        draw_ov.line([(x, 0), (x, height)], fill=(15, 15, 20, alpha))
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)
    
    # 2. Agent Image (Left)
    if agent_img:
        target_agent_h = int(height * 1.35)
        agent_ratio = agent_img.width / agent_img.height
        target_agent_w = int(target_agent_h * agent_ratio)
        agent_img = agent_img.resize((target_agent_w, target_agent_h), Image.Resampling.LANCZOS)
        
        agent_mask = agent_img.split()[3]
        fade = Image.new('L', (target_agent_w, target_agent_h))
        draw_fade = ImageDraw.Draw(fade)
        fade_start = int(target_agent_w * 0.5)
        for x in range(target_agent_w):
            if x < fade_start:
                alpha = 255
            else:
                alpha = max(0, int(255 * (1 - (x - fade_start) / (target_agent_w - fade_start))))
            draw_fade.line([(x, 0), (x, target_agent_h)], fill=alpha)
        
        new_alpha = ImageMath.eval("convert(min(a, b), 'L')", a=agent_mask, b=fade)
        agent_img.putalpha(new_alpha)
        
        paste_x = -30
        paste_y = (height - target_agent_h) // 2
        bg.paste(agent_img, (paste_x, paste_y), agent_img)
    
    # 3. Typography
    try:
        try:
            font_rr = ImageFont.truetype("arialbd.ttf", 70)
            font_kda = ImageFont.truetype("arialbd.ttf", 60)
            font_title = ImageFont.truetype("arial.ttf", 24)
            font_score = ImageFont.truetype("arialbd.ttf", 36)
            font_stat_val = ImageFont.truetype("arialbd.ttf", 26)
            font_stat_lbl = ImageFont.truetype("arial.ttf", 18)
        except:
            font_rr = ImageFont.truetype("arial.ttf", 70)
            font_kda = ImageFont.truetype("arial.ttf", 60)
            font_title = ImageFont.truetype("arial.ttf", 24)
            font_score = ImageFont.truetype("arial.ttf", 36)
            font_stat_val = ImageFont.truetype("arial.ttf", 26)
            font_stat_lbl = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font_rr = ImageFont.load_default()
        font_kda = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_score = ImageFont.load_default()
        font_stat_val = ImageFont.load_default()
        font_stat_lbl = ImageFont.load_default()
        
    text_x = 420
    
    # Title
    info_text = f"{map_name.upper()} • {agent_name.upper()}"
    draw.text((text_x, 40), info_text, fill=(200, 200, 200, 255), font=font_title)
    
    # Match Score (Top Right)
    draw.text((760, 35), match_score, fill=(230, 230, 230, 255), font=font_score, anchor="rt")
    
    # KDA
    draw.text((text_x, 80), f"KDA: {kda}", fill=(255, 255, 255, 255), font=font_kda)
    
    # RR
    sign = "+" if rr_change > 0 else ""
    color = (100, 255, 120, 255) if rr_change > 0 else (255, 80, 80, 255) if rr_change < 0 else (200, 200, 200, 255)
    rr_text = f"{sign}{rr_change} RR"
    draw.text((text_x, 150), rr_text, fill=color, font=font_rr)
    
    # Grid for Advanced Stats
    grid_y = 280
    hs_pct = stats.get("hs_pct", "N/A")
    kd_val = stats.get("kd", "N/A")
    adr_val = stats.get("adr", "N/A")
    perf_val = stats.get("perf", "N/A")  
    
    hs_str = f"{hs_pct}%" if isinstance(hs_pct, (int, float)) else str(hs_pct)
    kd_str = f"{kd_val:.2f}" if isinstance(kd_val, (int, float)) else str(kd_val)
    adr_str = str(adr_val)
    perf_str = str(perf_val)

    # We can widen the column slightly to make sure it looks spaced out
    col_width = 85
    
    # Row 1 Labels
    draw.text((text_x, grid_y), "HS%", fill=(170, 170, 170, 255), font=font_stat_lbl)
    draw.text((text_x + col_width, grid_y), "K/D", fill=(170, 170, 170, 255), font=font_stat_lbl)
    draw.text((text_x + 2*col_width, grid_y), "ADR", fill=(170, 170, 170, 255), font=font_stat_lbl)
    draw.text((text_x + 3*col_width + 10, grid_y), "Perf", fill=(170, 170, 170, 255), font=font_stat_lbl)
    
    # Row 2 Values
    val_y = grid_y + 25
    draw.text((text_x, val_y), hs_str, fill=(255, 255, 255, 255), font=font_stat_val)
    draw.text((text_x + col_width, val_y), kd_str, fill=(255, 255, 255, 255), font=font_stat_val)
    draw.text((text_x + 2*col_width, val_y), adr_str, fill=(255, 255, 255, 255), font=font_stat_val)
    draw.text((text_x + 3*col_width + 10, val_y), perf_str, fill=(255, 255, 255, 255), font=font_stat_val)
    
    buffer = io.BytesIO()
    bg.convert("RGB").save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return buffer


# --- Generateur de leaderboard pour les parties de groupe (Duo/Trio+) -----------
async def generate_group_image(
    players_data: list,
    map_name: str = "",
    match_score: str = "",
    result_text: str = "",
) -> io.BytesIO:
    """
    Genere une image leaderboard style Valorant pour les parties de groupe.

    players_data : liste de dict :
        { name, tag, rang, agent_url, rank_url, perf, kda, rr_change,
          hs_pct, kd, adr }
    map_name    : nom de la map (splash art en fond)
    match_score : ex '13-8'
    result_text : 'VICTOIRE' | 'DEFAITE' | 'EGALITE'
    """
    WIDTH        = 1100
    HEADER_H     = 110
    COL_HEADER_H = 42
    ROW_H        = 72
    PADDING_BOT  = 18
    n_players    = max(len(players_data), 1)
    HEIGHT       = HEADER_H + COL_HEADER_H + ROW_H * n_players + PADDING_BOT

    BG_DARK       = (14,  17,  23,  255)
    BG_ROW_A      = (20,  24,  32,  200)
    BG_ROW_B      = (28,  33,  46,  200)
    ACCENT_WIN    = (0,   210, 130, 255)
    ACCENT_LOSS   = (255, 65,  85,  255)
    ACCENT_DRAW   = (160, 160, 160, 255)
    COL_HEADER_C  = (120, 130, 155, 255)
    COL_HEADER_BG = (12,  16,  26,  230)
    SEPARATOR     = (50,  58,  80,  180)
    WHITE         = (255, 255, 255, 255)
    SUBTEXT       = (170, 180, 200, 255)
    GREEN         = (100, 230, 140, 255)
    ORANGE        = (255, 200,  80, 255)
    RED           = (235,  80,  80, 255)
    BLUE          = (120, 180, 255, 255)

    accent = (
        ACCENT_WIN  if result_text.upper() == "VICTOIRE"
        else ACCENT_LOSS if "FAITE" in result_text.upper()
        else ACCENT_DRAW
    )

    def _font(name, size):
        for attempt in [name, "arial.ttf"]:
            try:
                return ImageFont.truetype(attempt, size)
            except IOError:
                pass
        return ImageFont.load_default()

    font_title    = _font("arialbd.ttf", 28)
    font_subtitle = _font("arial.ttf",   18)
    font_col_hdr  = _font("arialbd.ttf", 12)
    font_name_f   = _font("arialbd.ttf", 17)
    font_tag      = _font("arial.ttf",   13)
    font_perf     = _font("arialbd.ttf", 18)
    font_kda      = _font("arial.ttf",   14)
    font_stat     = _font("arialbd.ttf", 15)
    font_rr       = _font("arialbd.ttf", 14)
    font_rang     = _font("arial.ttf",   12)

    async def _fetch(url, session):
        if not url:
            return None
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    data = await r.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception as exc:
            print(f"[group_image] fetch error {url}: {exc}")
        return None

    async def _fetch_map(name, session):
        if not name:
            return None
        try:
            async with session.get("https://valorant-api.com/v1/maps",
                                   timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    for m in (await r.json()).get("data", []):
                        if m.get("displayName", "").lower() == name.lower():
                            url = m.get("splash")
                            if url:
                                return await _fetch(url, session)
        except Exception as exc:
            print(f"[group_image] map fetch error: {exc}")
        return None

    async with aiohttp.ClientSession() as session:
        tasks_icons = []
        for p in players_data:
            tasks_icons.append(_fetch(p.get("agent_url", ""), session))
            tasks_icons.append(_fetch(p.get("rank_url",  ""), session))
        map_task    = _fetch_map(map_name, session)
        all_results = await asyncio.gather(map_task, *tasks_icons)

    map_img   = all_results[0]
    icon_list = all_results[1:]

    # Couche 1 : splash map recadree (ou fond sombre si indisponible)
    if map_img:
        ratio   = map_img.width / map_img.height
        t_ratio = WIDTH / HEIGHT
        if ratio > t_ratio:
            new_h = HEIGHT;  new_w = int(new_h * ratio)
        else:
            new_w = WIDTH;   new_h = int(new_w / ratio)
        map_img = map_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left    = (new_w - WIDTH)  // 2
        top     = (new_h - HEIGHT) // 2
        canvas  = map_img.crop((left, top, left + WIDTH, top + HEIGHT)).convert("RGBA")
    else:
        canvas = Image.new("RGBA", (WIDTH, HEIGHT), BG_DARK)

    # Couche 2 : overlay sombre pour lisibilite
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 185))
    canvas  = Image.alpha_composite(canvas, overlay)
    draw    = ImageDraw.Draw(canvas)

    # Barre accent verticale gauche
    draw.rectangle([(0, 0), (5, HEIGHT)], fill=accent)

    # En-tete
    title_x = 22
    if result_text:
        draw.text((title_x, 18), result_text.upper(), fill=accent, font=font_title)
    h_parts = []
    if map_name:
        h_parts.append(map_name.upper())
    if match_score:
        h_parts.append(match_score)
    if h_parts:
        draw.text((title_x, 54), "  .  ".join(h_parts), fill=SUBTEXT, font=font_subtitle)
    suffix = "s" if n_players > 1 else ""
    draw.text((WIDTH - 20, 18), f"{n_players} joueur{suffix}",
              fill=SUBTEXT, font=font_subtitle, anchor="rt")

    # Positions colonnes
    X_AGENT = 14;   X_RANK = 68;   X_NAME = 122
    X_PERF  = 460;  X_KDA  = 578;  X_HS   = 730
    X_KD    = 830;  X_ADR  = 930;  X_RR   = WIDTH - 18

    # Ligne en-tete colonnes
    col_y = HEADER_H
    draw.rectangle([(0, col_y), (WIDTH, col_y + COL_HEADER_H)], fill=COL_HEADER_BG)
    cy_hdr = col_y + COL_HEADER_H // 2

    def _lbl(text, x, anchor="mm"):
        draw.text((x, cy_hdr), text.upper(), fill=COL_HEADER_C,
                  font=font_col_hdr, anchor=anchor)

    _lbl("JOUEUR", X_NAME, anchor="lm")
    _lbl("PERF",   X_PERF)
    _lbl("KDA",    X_KDA)
    _lbl("HS%",    X_HS)
    _lbl("K/D",    X_KD)
    _lbl("ADR",    X_ADR)
    _lbl("RR",     X_RR, anchor="rm")

    # Tri par perf decroissant
    paired = sorted(
        zip(players_data,
            [icon_list[i * 2]     for i in range(n_players)],
            [icon_list[i * 2 + 1] for i in range(n_players)]),
        key=lambda t: t[0].get("perf", 0),
        reverse=True,
    )
    sorted_players   = [t[0] for t in paired]
    sorted_agent_img = [t[1] for t in paired]
    sorted_rank_img  = [t[2] for t in paired]

    def _paste_icon(img, x, y, size):
        if img is None:
            return
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        canvas.paste(img, (x, y), img if img.mode == "RGBA" else None)

    for idx, p in enumerate(sorted_players):
        agent_img = sorted_agent_img[idx]
        rank_img  = sorted_rank_img[idx]
        row_y = HEADER_H + COL_HEADER_H + idx * ROW_H

        # Fond de ligne semi-transparent
        row_ovl = Image.new("RGBA", (WIDTH - 5, ROW_H - 1),
                            BG_ROW_A if idx % 2 == 0 else BG_ROW_B)
        canvas.paste(row_ovl, (5, row_y), row_ovl)
        draw = ImageDraw.Draw(canvas)

        # Separateur
        if idx < n_players - 1:
            draw.line([(X_NAME, row_y + ROW_H - 1), (WIDTH - 10, row_y + ROW_H - 1)],
                      fill=SEPARATOR, width=1)

        cy2      = row_y + ROW_H // 2
        icon_sz  = 46
        icon_pad = (ROW_H - icon_sz) // 2

        # Icone agent
        if agent_img:
            agent_bg = Image.new("RGBA", (icon_sz, icon_sz), (30, 35, 48, 220))
            ar = agent_img.resize((icon_sz, icon_sz), Image.Resampling.LANCZOS)
            agent_bg.paste(ar, (0, 0), ar)
            canvas.paste(agent_bg, (X_AGENT, row_y + icon_pad))
            draw = ImageDraw.Draw(canvas)

        # Icone rang
        _paste_icon(rank_img, X_RANK, row_y + (ROW_H - 38) // 2, 38)
        draw = ImageDraw.Draw(canvas)

        # Nom + tag + rang
        name_str = p.get("name", "Joueur")
        tag_str  = p.get("tag",  "")
        rang_str = p.get("rang", "")
        name_y   = cy2 - 14
        draw.text((X_NAME, name_y), name_str, fill=WHITE, font=font_name_f)
        if tag_str:
            nw = draw.textlength(name_str, font=font_name_f)
            draw.text((X_NAME + nw + 4, name_y + 2), "#" + tag_str, fill=SUBTEXT, font=font_tag)
        if rang_str:
            draw.text((X_NAME, cy2 + 4), rang_str, fill=SUBTEXT, font=font_rang)

        # PERF
        try:
            perf_f   = float(p.get("perf", 0))
            perf_txt = str(int(perf_f))
            perf_col = GREEN if perf_f >= 250 else ORANGE if perf_f >= 180 else WHITE
        except Exception:
            perf_txt = str(p.get("perf", 0)); perf_col = WHITE
        draw.text((X_PERF, cy2), perf_txt, fill=perf_col, font=font_perf, anchor="mm")

        # KDA
        kda_str   = p.get("kda", "0/0/0")
        kda_parts = kda_str.split("/")
        if len(kda_parts) == 3:
            k, d, a = kda_parts
            k_w  = draw.textlength(k,     font=font_kda)
            sl_w = draw.textlength(" / ", font=font_kda)
            d_w  = draw.textlength(d,     font=font_kda)
            tw   = k_w + sl_w + d_w + sl_w + draw.textlength(a, font=font_kda)
            kx   = X_KDA - tw / 2
            draw.text((kx, cy2), k,     fill=GREEN,   font=font_kda, anchor="lm"); kx += k_w
            draw.text((kx, cy2), " / ", fill=SUBTEXT, font=font_kda, anchor="lm"); kx += sl_w
            draw.text((kx, cy2), d,     fill=RED,     font=font_kda, anchor="lm"); kx += d_w
            draw.text((kx, cy2), " / ", fill=SUBTEXT, font=font_kda, anchor="lm"); kx += sl_w
            draw.text((kx, cy2), a,     fill=BLUE,    font=font_kda, anchor="lm")
        else:
            draw.text((X_KDA, cy2), kda_str, fill=WHITE, font=font_kda, anchor="mm")

        # HS%
        try:
            hs_f   = float(p.get("hs_pct", 0))
            hs_txt = f"{hs_f:.1f}%"
            hs_col = GREEN if hs_f >= 25 else ORANGE if hs_f >= 15 else SUBTEXT
        except Exception:
            hs_txt = str(p.get("hs_pct", 0)); hs_col = SUBTEXT
        draw.text((X_HS, cy2), hs_txt, fill=hs_col, font=font_stat, anchor="mm")

        # K/D ratio
        try:
            kd_f   = float(p.get("kd", 0))
            kd_txt = f"{kd_f:.2f}"
            kd_col = GREEN if kd_f >= 1.0 else RED
        except Exception:
            kd_txt = str(p.get("kd", 0)); kd_col = SUBTEXT
        draw.text((X_KD, cy2), kd_txt, fill=kd_col, font=font_stat, anchor="mm")

        # ADR
        try:
            adr_f   = float(p.get("adr", 0))
            adr_txt = str(int(adr_f))
            adr_col = GREEN if adr_f >= 150 else ORANGE if adr_f >= 100 else SUBTEXT
        except Exception:
            adr_txt = str(p.get("adr", 0)); adr_col = SUBTEXT
        draw.text((X_ADR, cy2), adr_txt, fill=adr_col, font=font_stat, anchor="mm")

        # RR
        rr_change = p.get("rr_change", 0)
        sign      = "+" if rr_change > 0 else ""
        rr_col    = ACCENT_WIN if rr_change > 0 else ACCENT_LOSS if rr_change < 0 else ACCENT_DRAW
        draw.text((X_RR, cy2), f"{sign}{rr_change} RR",
                  fill=rr_col, font=font_rr, anchor="rm")

    # Pied de page
    bottom    = HEADER_H + COL_HEADER_H + ROW_H * n_players
    footer_bg = Image.new("RGBA", (WIDTH, PADDING_BOT), (8, 10, 16, 220))
    canvas.paste(footer_bg, (0, bottom), footer_bg)
    draw = ImageDraw.Draw(canvas)
    draw.text((WIDTH // 2, bottom + PADDING_BOT // 2),
              "RR Trackerito  -  Donnees via HenrikDev",
              fill=(70, 80, 100, 255), font=font_rang, anchor="mm")

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return buf


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


def _make_avatar_circle(img: Image.Image, size: int, outline_color: tuple = None, outline_width: int = 2) -> Image.Image:
    """Recadre une image PIL en cercle parfait de taille size×size avec contour optionnel."""
    img = img.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([(0, 0), (size - 1, size - 1)], fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)
    if outline_color:
        draw_r = ImageDraw.Draw(result)
        draw_r.ellipse(
            [(0, 0), (size - 1, size - 1)],
            outline=(*outline_color[:3], 200),
            width=outline_width
        )
    return result


async def _fetch_avatar(url: str, session: aiohttp.ClientSession, size: int,
                        outline_color: tuple = None) -> Optional[Image.Image]:
    """Télécharge un avatar Discord et le retourne en cercle PIL. Retourne None si échec."""
    if not url:
        return None
    try:
        # Forcer la résolution 128px (plus léger, suffisant)
        base_url = url.split("?")[0]
        fetch_url = f"{base_url}?size=128"
        async with session.get(fetch_url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
            if resp.status == 200:
                raw = await resp.read()
                img = Image.open(io.BytesIO(raw)).convert("RGBA")
                return _make_avatar_circle(img, size, outline_color=outline_color)
    except Exception as e:
        print(f"[ImageGen] avatar fetch error {url}: {e}")
    return None


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

    # Téléchargement des icônes de rang + avatars Discord en parallèle
    async with aiohttp.ClientSession() as session:
        rank_urls   = [RANK_ICON_URLS.get(j["rang"]) for j in resultats]
        avatar_urls = [j.get("discord_avatar_url") for j in resultats]
        rank_tasks  = [_fetch_img(u, session, (40, 40)) if u else asyncio.sleep(0) for u in rank_urls]
        avatar_tasks = [
            _fetch_avatar(u, session, 40, outline_color=_rank_accent(resultats[i]["rang"]))
            for i, u in enumerate(avatar_urls)
        ]
        results_all  = list(await asyncio.gather(*rank_tasks, *avatar_tasks))
        rank_icons   = results_all[:len(resultats)]
        avatar_icons = results_all[len(resultats):]

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

        # Avatar : cercle Discord si dispo, sinon initiale
        avatar_size = 40
        avatar_x = COL_PLAYER - 4
        avatar_y = row_y + 8
        accent_col_rank = _rank_accent(joueur["rang"])

        av_img = avatar_icons[i] if i < len(avatar_icons) else None
        if isinstance(av_img, Image.Image):
            _paste_with_alpha(img, av_img, (avatar_x, avatar_y))
            draw = ImageDraw.Draw(img)
        else:
            # Fallback : cercle coloré avec initiale
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
    Genere un panneau de recapitulatif quotidien style Valorant.

    date_label   : ex. "01/10/2026"
    players_data : liste de dicts :
        { nom, tag, total_rr, wins, losses, draws, winrate,
          start_rang, start_rr, end_rang, end_rr,
          discord_avatar_url (optionnel) }
    """
    W        = 1600
    HEADER_H = 200
    CARD_H   = 200
    CARD_GAP = 20
    PADDING  = 36
    FOOTER_H = 64
    n        = max(len(players_data), 1)
    H        = HEADER_H + n * (CARD_H + CARD_GAP) + FOOTER_H + PADDING

    img  = Image.new("RGB", (W, H), BG_DARK)
    _draw_gradient_bg(img, (10, 12, 20), (18, 15, 28))
    draw = ImageDraw.Draw(img, "RGBA")

    font_title    = _load_font(48, bold=True)
    font_subtitle = _load_font(22)
    font_date     = _load_font(24, bold=True)
    font_player   = _load_font(28, bold=True)
    font_tag_sm   = _load_font(20)
    font_rr_big   = _load_font(52, bold=True)
    font_label    = _load_font(19)
    font_stat     = _load_font(26, bold=True)
    font_rang_sm  = _load_font(22, bold=True)
    font_footer   = _load_font(18)

    # ── En-tete ────────────────────────────────────────────────────────────────
    draw.rectangle([(0, 0), (W, HEADER_H)], fill=BG_HEADER)
    draw.rectangle([(0, 0), (8, HEADER_H)], fill=ACCENT)
    draw.text((36, 28),  "RECAP QUOTIDIEN",                                     font=font_title,    fill=TEXT_WH)
    draw.text((36, 100), "Resume des performances competitives de la journee",   font=font_subtitle, fill=TEXT_GREY)

    # Date pill
    date_text = date_label
    dt_w   = draw.textbbox((0, 0), date_text, font=font_date)[2]
    pill_x = W - dt_w - 80
    _draw_rounded_rect(draw, (pill_x - 16, 48, W - 32, 112), radius=14,
                       fill=(30, 32, 48), outline=NEON_BLUE, outline_width=2)
    draw.text((pill_x, 66), date_text, font=font_date, fill=NEON_BLUE)
    draw.rectangle([(0, HEADER_H - 3), (W, HEADER_H)], fill=ACCENT)

    # ── Telechargement icones rang + avatars Discord en parallele ──────────────
    all_rank_urls = []
    for pd in players_data:
        all_rank_urls.append(RANK_ICON_URLS.get(pd.get("end_rang",   ""), None))
        all_rank_urls.append(RANK_ICON_URLS.get(pd.get("start_rang", ""), None))

    avatar_urls = [pd.get("discord_avatar_url") for pd in players_data]

    ICON_SIZE   = 60
    AVATAR_SIZE = 84

    async with aiohttp.ClientSession() as session:
        rank_tasks   = [_fetch_img(u, session, (ICON_SIZE, ICON_SIZE)) if u else asyncio.sleep(0)
                        for u in all_rank_urls]
        avatar_tasks = [
            _fetch_avatar(u, session, AVATAR_SIZE,
                          outline_color=_rank_accent(players_data[i].get("end_rang", "")))
            for i, u in enumerate(avatar_urls)
        ]
        all_results    = list(await asyncio.gather(*rank_tasks, *avatar_tasks))
        rank_imgs_flat = all_results[:len(all_rank_urls)]
        avatar_imgs    = all_results[len(all_rank_urls):]

    # ── Cartes joueurs ─────────────────────────────────────────────────────────
    for i, pd in enumerate(players_data):
        card_y = HEADER_H + PADDING // 2 + i * (CARD_H + CARD_GAP)

        end_icon   = rank_imgs_flat[i * 2]     if isinstance(rank_imgs_flat[i * 2],     Image.Image) else None
        start_icon = rank_imgs_flat[i * 2 + 1] if isinstance(rank_imgs_flat[i * 2 + 1], Image.Image) else None

        nom        = pd.get("nom",        "Inconnu")
        tag        = pd.get("tag",        "???")
        total_rr   = pd.get("total_rr",   0)
        wins       = pd.get("wins",       0)
        losses     = pd.get("losses",     0)
        draws_     = pd.get("draws",      0)
        winrate    = pd.get("winrate",    0.0)
        start_rang = pd.get("start_rang", "?")
        start_rr_v = pd.get("start_rr",  "?")
        end_rang   = pd.get("end_rang",   "?")
        end_rr_v   = pd.get("end_rr",    0)

        is_positive   = total_rr >= 0
        rr_accent_c   = (80, 230, 140) if is_positive else (255, 80, 80)
        rank_accent_c = _rank_accent(end_rang)

        # Fond carte
        _draw_rounded_rect(draw, (PADDING, card_y, W - PADDING, card_y + CARD_H),
                           radius=16, fill=BG_CARD, outline=(*rank_accent_c, 60), outline_width=2)
        # Barre laterale coloree
        draw.rectangle([(PADDING, card_y + 10), (PADDING + 6, card_y + CARD_H - 10)], fill=rr_accent_c)

        # ── Avatar ────────────────────────────────────────────────────────────
        AV_SIZE = AVATAR_SIZE
        av_x    = PADDING + 28
        av_y    = card_y + (CARD_H - AV_SIZE) // 2

        av_img = avatar_imgs[i] if i < len(avatar_imgs) else None
        if isinstance(av_img, Image.Image):
            _paste_with_alpha(img, av_img, (av_x, av_y))
            draw = ImageDraw.Draw(img, "RGBA")
        else:
            draw.ellipse([(av_x, av_y), (av_x + AV_SIZE, av_y + AV_SIZE)],
                         fill=(*rank_accent_c, 30), outline=(*rank_accent_c, 160), width=3)
            initial = nom[0].upper() if nom else "?"
            iw = draw.textbbox((0, 0), initial, font=font_player)[2]
            ih = draw.textbbox((0, 0), initial, font=font_player)[3]
            draw.text((av_x + (AV_SIZE - iw) // 2, av_y + (AV_SIZE - ih) // 2),
                      initial, font=font_player, fill=rank_accent_c)

        # ── Nom + Tag ─────────────────────────────────────────────────────────
        name_x = av_x + AV_SIZE + 22
        draw.text((name_x, card_y + 30), nom[:20],  font=font_player, fill=TEXT_WH)
        draw.text((name_x, card_y + 72), "#" + tag, font=font_tag_sm, fill=TEXT_GREY)

        # ── Bilan RR ──────────────────────────────────────────────────────────
        rr_x   = 560
        sign   = "+" if total_rr >= 0 else ""
        rr_str = sign + str(total_rr) + " RR"
        draw.text((rr_x, card_y + 24), rr_str, font=font_rr_big, fill=rr_accent_c)

        rr_w  = draw.textbbox((0, 0), rr_str, font=font_rr_big)[2]
        arrow = "▲" if is_positive else "▼"
        draw.text((rr_x + rr_w + 12, card_y + 38), arrow, font=font_stat, fill=rr_accent_c)

        # Stats W / L / WR%
        wl_str = str(wins) + "V  " + str(losses) + "D"
        if draws_ > 0:
            wl_str += "  " + str(draws_) + "N"
        draw.text((rr_x, card_y + 106), wl_str,                                       font=font_stat,  fill=TEXT_WH)
        draw.text((rr_x, card_y + 148), "Win rate : " + str(round(winrate, 1)) + "%", font=font_label, fill=TEXT_GREY)

        # ── Progression de rang ───────────────────────────────────────────────
        prog_x = 1050
        prog_y = card_y + 28

        if start_icon:
            _paste_with_alpha(img, start_icon, (prog_x, prog_y))
            draw.text((prog_x + ICON_SIZE + 8, prog_y + 4),  start_rang,              font=font_rang_sm, fill=TEXT_GREY)
            draw.text((prog_x + ICON_SIZE + 8, prog_y + 32), str(start_rr_v) + " RR", font=font_label,   fill=TEXT_GREY)
        else:
            draw.text((prog_x, prog_y + 14), start_rang, font=font_rang_sm, fill=TEXT_GREY)

        arr_x = prog_x + ICON_SIZE + 160
        draw.text((arr_x, prog_y + 14), "→", font=font_stat, fill=TEXT_GREY)

        end_x = arr_x + 42
        if end_icon:
            _paste_with_alpha(img, end_icon, (end_x, prog_y))
            draw.text((end_x + ICON_SIZE + 8, prog_y + 4),  end_rang,           font=font_rang_sm, fill=rank_accent_c)
            draw.text((end_x + ICON_SIZE + 8, prog_y + 32), str(end_rr_v) + " RR", font=font_label, fill=rank_accent_c)
        else:
            draw.text((end_x, prog_y + 14), end_rang, font=font_rang_sm, fill=rank_accent_c)

        # Barre de progression RR
        bar_x   = prog_x
        bar_y   = card_y + 128
        bar_w   = 400
        bar_h   = 12
        rr_fill = max(0, min(int(end_rr_v) if isinstance(end_rr_v, (int, float)) else 0, 100))
        _draw_rounded_rect(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=6, fill=(40, 42, 60))
        if rr_fill > 0:
            _draw_rounded_rect(draw, (bar_x, bar_y, bar_x + int(bar_w * rr_fill / 100), bar_y + bar_h),
                               radius=6, fill=rank_accent_c)
        draw.text((bar_x, bar_y + 18), str(rr_fill) + "/100 RR", font=font_label, fill=TEXT_GREY)

    # ── Pied de page ───────────────────────────────────────────────────────────
    footer_y_top = H - FOOTER_H
    draw.rectangle([(0, footer_y_top), (W, H)], fill=BG_HEADER)
    draw.rectangle([(0, footer_y_top), (W, footer_y_top + 2)], fill=SEP_LINE)
    draw.text((PADDING, footer_y_top + 20), "RR Trackerito  -  Donnees via HenrikDev API",
              font=font_footer, fill=TEXT_GREY)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf

