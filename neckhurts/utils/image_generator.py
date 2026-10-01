import io
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont

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

async def generate_match_image(map_name: str, agent_name: str, kda: str, rr_change: int) -> io.BytesIO:
    """Génère une image premium récapitulative de la partie avec les assets API."""
    width, height = 800, 400
    
    async with aiohttp.ClientSession() as session:
        map_task = asyncio.create_task(get_map_image(map_name, session))
        agent_task = asyncio.create_task(get_agent_image(agent_name, session))
        map_img, agent_img = await asyncio.gather(map_task, agent_task)

    # 1. Background
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
            
        bg = map_img.convert("RGBA")
    else:
        bg = Image.new("RGBA", (width, height), (30, 34, 42, 255))

    # Dark overlay
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 160))
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)
    
    # 2. Agent Image
    if agent_img:
        agent_img.thumbnail((380, 380), Image.Resampling.LANCZOS)
        paste_x = 20
        paste_y = height - agent_img.height
        bg.paste(agent_img, (paste_x, paste_y), agent_img)
    
    # 3. Typography
    try:
        try:
            font_title = ImageFont.truetype("arialbd.ttf", 65)
            font_kda = ImageFont.truetype("arialbd.ttf", 55)
            font_small = ImageFont.truetype("arial.ttf", 28)
        except:
            font_title = ImageFont.truetype("arial.ttf", 65)
            font_kda = ImageFont.truetype("arial.ttf", 55)
            font_small = ImageFont.truetype("arial.ttf", 28)
    except IOError:
        font_title = ImageFont.load_default()
        font_kda = ImageFont.load_default()
        font_small = ImageFont.load_default()
        
    text_x = 420
    info_text = f"{map_name.upper()} • {agent_name.upper()}"
    draw.text((text_x, 60), info_text, fill=(200, 200, 200, 255), font=font_small)
    
    draw.text((text_x, 110), f"KDA: {kda}", fill=(255, 255, 255, 255), font=font_kda)
    
    sign = "+" if rr_change > 0 else ""
    color = (80, 255, 120, 255) if rr_change > 0 else (255, 80, 80, 255) if rr_change < 0 else (200, 200, 200, 255)
    rr_text = f"{sign}{rr_change} RR"
    draw.text((text_x, 210), rr_text, fill=color, font=font_title)
    
    buffer = io.BytesIO()
    bg.convert("RGB").save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return buffer
