import io
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageMath

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
        target_agent_h = int(height * 1.5)
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
        
        paste_x = -50
        paste_y = height - target_agent_h + 30
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
    cst_val = stats.get("acs", "N/A")  # ACS is now CSt
    
    hs_str = f"{hs_pct}%" if isinstance(hs_pct, (int, float)) else str(hs_pct)
    kd_str = f"{kd_val:.2f}" if isinstance(kd_val, (int, float)) else str(kd_val)
    adr_str = str(adr_val)
    cst_str = str(cst_val)

    # We can widen the column slightly to make sure it looks spaced out
    col_width = 85
    
    # Row 1 Labels
    draw.text((text_x, grid_y), "HS%", fill=(170, 170, 170, 255), font=font_stat_lbl)
    draw.text((text_x + col_width, grid_y), "K/D", fill=(170, 170, 170, 255), font=font_stat_lbl)
    draw.text((text_x + 2*col_width, grid_y), "ADR", fill=(170, 170, 170, 255), font=font_stat_lbl)
    draw.text((text_x + 3*col_width + 10, grid_y), "CSt", fill=(170, 170, 170, 255), font=font_stat_lbl)
    
    # Row 2 Values
    val_y = grid_y + 25
    draw.text((text_x, val_y), hs_str, fill=(255, 255, 255, 255), font=font_stat_val)
    draw.text((text_x + col_width, val_y), kd_str, fill=(255, 255, 255, 255), font=font_stat_val)
    draw.text((text_x + 2*col_width, val_y), adr_str, fill=(255, 255, 255, 255), font=font_stat_val)
    draw.text((text_x + 3*col_width + 10, val_y), cst_str, fill=(255, 255, 255, 255), font=font_stat_val)
    
    buffer = io.BytesIO()
    bg.convert("RGB").save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return buffer
