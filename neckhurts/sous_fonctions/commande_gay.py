import discord
from discord import app_commands
import random
import datetime

mon_id = 784106722615754772  # À synchroniser avec le fichier principal si besoin

@app_commands.command(name="gay", description="Renvoie à quel point un utilisateur est gay")
@app_commands.describe(user="L'utilisateur à tester (optionnel)")
async def gay(interaction: discord.Interaction, user: discord.User = None):
    target = user or interaction.user
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H")  # UTC hour
    seed = f"{target.id}-{now}"
    local_random = random.Random(seed)
    pourcentage = local_random.randint(0, 50) if target.id == mon_id else local_random.randint(0, 100)

    if pourcentage == 100:
        msg = f"{target.mention} est gay à {pourcentage}% 🌈 (full homo)"
    elif 10 < pourcentage < 100:
        msg = f"{target.mention} est gay à {pourcentage}% 🌈"
    else:
        msg = f"{target.mention} est un peu gay à {pourcentage}% 🌈"

    await interaction.response.send_message(msg)

# Export de la commande pour l'import dans le bot principal
gay = gay