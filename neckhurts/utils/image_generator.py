import os
import io
from PIL import Image, ImageDraw, ImageFont

def generate_match_image(map_name: str, agent_name: str, kda: str, rr_change: int) -> io.BytesIO:
    """Génère une image premium récapitulative de la partie."""
    width, height = 800, 400
    
    # Paths for assets
    map_path = f"assets/maps/{map_name.lower()}.png"
    agent_path = f"assets/agents/{agent_name.lower()}.png"
    
    # 1. Background
    if os.path.exists(map_path):
        try:
            bg = Image.open(map_path).convert("RGBA")
            bg = bg.resize((width, height))
        except Exception:
            bg = Image.new("RGBA", (width, height), (40, 44, 52, 255))
    else:
        bg = Image.new("RGBA", (width, height), (40, 44, 52, 255))

    # Dark overlay to make text pop
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 150))
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)
    
    # 2. Agent Image
    if os.path.exists(agent_path):
        try:
            agent_img = Image.open(agent_path).convert("RGBA")
            agent_img.thumbnail((350, 350))
            # Center the agent image on the left side
            bg.paste(agent_img, (20, height - agent_img.height), agent_img)
        except Exception:
            pass
    
    # 3. Typography
    try:
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_medium = ImageFont.truetype("arial.ttf", 40)
        font_small = ImageFont.truetype("arial.ttf", 25)
    except IOError:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        
    # Text Placement
    text_x = 400
    draw.text((text_x, 80), "KDA", fill=(200, 200, 200, 255), font=font_medium)
    draw.text((text_x, 130), kda, fill=(255, 255, 255, 255), font=font_large)
    
    sign = "+" if rr_change > 0 else ""
    color = (100, 255, 100, 255) if rr_change > 0 else (255, 100, 100, 255) if rr_change < 0 else (200, 200, 200, 255)
    rr_text = f"RR: {sign}{rr_change}"
    draw.text((text_x, 220), rr_text, fill=color, font=font_large)
    
    info_text = f"Map: {map_name}  |  Agent: {agent_name}"
    draw.text((text_x, 320), info_text, fill=(180, 180, 180, 255), font=font_small)
    
    # Export to bytes
    buffer = io.BytesIO()
    bg.convert("RGB").save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
