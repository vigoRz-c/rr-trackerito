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
